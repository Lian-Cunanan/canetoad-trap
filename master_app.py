import paho.mqtt.client as mqtt
import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template, jsonify, request, send_file
from flask_cors import CORS
import time
import hardware 
import threading 
from picamera2 import Picamera2
import os                  # <--- NEW: For creating folders
from datetime import datetime # <--- NEW: For timestamping images
import urllib.request # <--- NEW: Lets the Pi download images from the ESP32

# ==========================================
# 1. AI VISION & FLASK WEB SERVER
# ==========================================
app = Flask(_name_)
CORS(app)  # Enable CORS for mobile app requests
print("Loading YOLOv8 AI Model...")
model = YOLO("/home/aldrich/Downloads/CaneToad_SmartTrap/models/best.pt") 

# --- NEW: Picamera2 Engine Setup ---
print("[SYSTEM] Booting hardware camera sensor...")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "BGR888"})
picam2.configure(config)
picam2.start()
time.sleep(2) # Crucial: Let the sensor warm up to adjust to the light
print("[SYSTEM] Camera active.")

toads_caught = 0
ai_annotated_frame = None
show_ai_timer = 0
latest_entrance_frame = None # <--- NEW: We will store the newest frame here safely

# --- NEW: Create a folder to store your custom dataset ---
if not os.path.exists("dataset_captures"):
    os.makedirs("dataset_captures")

def generate_entrance_frames():
    """Streams the Gatekeeper camera, flashes AI analysis on trigger."""
    global ai_annotated_frame, show_ai_timer, latest_entrance_frame
    while True:
        try:
            # NEW: Grab the frame directly from the sensor
            frame = picam2.capture_array() 
        except Exception as e:
            print(f"[ERROR] Dropped a frame: {e}")
            continue
            
        # Update the global frame so the AI can safely grab a copy when needed
        latest_entrance_frame = frame.copy() 
            
        if time.time() < show_ai_timer and ai_annotated_frame is not None:
            display_frame = ai_annotated_frame
        else:
            display_frame = frame 

        ret, buffer = cv2.imencode('.jpg', display_frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_entrance')
def video_entrance():
    return Response(generate_entrance_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



# --- THE NEW WEB APP INTERFACE ---
@app.route('/')
def index():
    """Serves your custom mobile app interface."""
    return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    """The app calls this every 2 seconds to get the live toad count."""
    return jsonify({"caught": toads_caught})

@app.route('/api/trigger/<action>', methods=['POST'])
def api_trigger(action):
    """The app sends commands here when you press a button."""
    if action == "front":
        print("[WEB APP] Command Received: Open Front Gate")
        threading.Thread(target=hardware.open_front_gate).start()
    elif action == "rear":
        print("[WEB APP] Command Received: Open Rear Gate")
        threading.Thread(target=hardware.open_rear_gate).start()
    elif action == "euthanasia":
        print("[WEB APP] Command Received: Trigger Euthanasia Cycle")
        threading.Thread(target=hardware.trigger_euthanasia_cycle).start()
    
    return jsonify({"status": "success"})

@app.route('/api/capture', methods=['POST'])
def api_capture():
    """Hidden Developer Endpoint: Saves the current frame for AI training."""
    global latest_entrance_frame
    
    if latest_entrance_frame is not None:
        # Create a unique filename using the exact date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_captures/canetoad_{timestamp}.jpg"
        
        # Save the image using OpenCV
        cv2.imwrite(filename, latest_entrance_frame)
        print(f"[DATASET] Image successfully captured and saved: {filename}")
        
        return jsonify({"status": "success", "message": "Picture saved!"})
    else:
        return jsonify({"status": "error", "message": "Camera not ready!"}), 500
    
@app.route('/api/capture_esp', methods=['POST'])
def api_capture_esp():
    """Hidden Developer Endpoint: Downloads a high-res JPEG from the ESP32."""
    try:
        # The secret 'single photo' URL built into the ESP32 Arduino code
        esp_capture_url = "http://10.42.0.145/capture"
        
        # Download the image data across the Wi-Fi
        response = urllib.request.urlopen(esp_capture_url, timeout=5)
        image_bytes = response.read()
        
        # Generate the timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_captures/esp32_inside_{timestamp}.jpg"
        
        # Save the raw image bytes to the folder
        with open(filename, 'wb') as f:
            f.write(image_bytes)
            
        print(f"[DATASET] ESP32 Image successfully captured: {filename}")
        return jsonify({"status": "success", "message": "ESP32 Picture saved!"})
        
    except Exception as e:
        print(f"[ERROR] Failed to capture from ESP32: {e}")
        return jsonify({"status": "error", "message": "ESP32 offline or busy"}), 500
    
@app.route('/api/esp_control', methods=['POST'])
def api_esp_control():
    """Proxies hardware tuning commands directly to the ESP32-CAM."""
    try:
        # Get the setting name and value from the web app
        data = request.json
        var = data.get('var')
        val = data.get('val')
        
        # Build the secret ESP32 control URL
        esp_url = f"http://10.42.0.145/control?var={var}&val={val}"
        
        # Send the command across the Wi-Fi
        urllib.request.urlopen(esp_url, timeout=2)
        print(f"[HARDWARE] Tuned ESP32 Camera: {var} = {val}")
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"[ERROR] Failed to tune ESP32: {e}")
        return jsonify({"status": "error", "message": "ESP32 offline or busy"}), 500

@app.route('/download')
def download_page():
    """Serves the APK download page for users connecting via local WiFi."""
    return render_template('download.html')

@app.route('/download/app.apk')
def download_apk():
    """Serves the compiled React Native APK file."""
    apk_path = os.path.join(os.path.dirname(__file__), 'static', 'app.apk')
    if os.path.exists(apk_path):
        return send_file(apk_path, as_attachment=True, mimetype='application/vnd.android.package-archive')
    else:
        return jsonify({"status": "error", "message": "APK not found. Build and place app.apk in /static folder."}), 404


# ==========================================
# 2. THE BACKGROUND AI WORKER (NEW)
# ==========================================
def run_ai_and_hardware(frame_to_analyze):
    """This runs completely in the background so the video NEVER lags."""
    global toads_caught, ai_annotated_frame, show_ai_timer
    
    # Run YOLOv8 on the captured frame
    results = model(frame_to_analyze, conf=0.80) 
    
    # Save the picture with the boxes so the video stream can flash it
    ai_annotated_frame = results[0].plot()
    show_ai_timer = time.time() + 5 
    
    detected_class = None
    confidence = 0.0
    object_found = False
    
    for result in results:
        for box in result.boxes:
            object_found = True
            detected_class = model.names[int(box.cls[0])]
            confidence = float(box.conf[0]) 
            break 
    
    if not object_found:
        print(">>> AI Analysis: NOTHING detected. False Alarm. <<<")
        
    elif detected_class == '0':
        print(f">>> POSITIVE ID: Cane Toad (Confidence: {confidence*100:.1f}%). Opening Gate! <<<")
        hardware.open_front_gate() # This 2-second servo delay won't lag the video anymore!
        toads_caught += 1
        client.publish("trap/stats", f"Total Caught: {toads_caught}", retain=True)
        
    else:
        print(f">>> NEGATIVE ID: Recognized as class '{detected_class}'. Keeping gate closed. <<<")


# ==========================================
# 3. MQTT COMMUNICATION LOGIC
# ==========================================
def on_connect(client, userdata, flags, rc):
    print("Connected to Mosquitto Broker. System Armed.")
    client.subscribe("trap/trigger")
    client.subscribe("manual/#")
    client.publish("trap/stats", f"Total Caught: {toads_caught}", retain=True)

def on_message(client, userdata, msg):
    global latest_entrance_frame
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    # --- AUTONOMOUS SENSOR TRIGGER ---
    if topic == "trap/trigger" and payload == "motion_detected":
        print("\n[TRIGGER] IR Beam Broken! Sending to background AI...")
        
        if latest_entrance_frame is not None:
            # We grab a safe copy of the picture and send it to the background worker!
            ai_thread = threading.Thread(target=run_ai_and_hardware, args=(latest_entrance_frame.copy(),))
            ai_thread.start()
        else:
            print("[WARNING] Camera is still warming up, frame not ready.")

    # --- MANUAL APP TRIGGERS ---
    # We put the manual hardware controls in background threads too, 
    # so pressing a button doesn't freeze the app!
    elif topic == "manual/front":
        print("[MANUAL] Opening Front Gate...")
        threading.Thread(target=hardware.open_front_gate).start()
    elif topic == "manual/rear":
        print("[MANUAL] Opening Rear Gate...")
        threading.Thread(target=hardware.open_rear_gate).start()
    elif topic == "manual/euthanasia":
        print("[MANUAL] Triggering Euthanasia Cycle...")
        threading.Thread(target=hardware.trigger_euthanasia_cycle).start()

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
if _name_ == "_main_":
    hardware.setup()
    
    # We must define the client globally so the background threads can use it
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_start() 
    
    try:
        print("Starting Smart Trap Server! Open your phone app.")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down system...")
    finally:
        picam2.stop()
        hardware.cleanup() 
        client.disconnect()