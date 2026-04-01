import cv2
import time

print("[TEST] Booting OpenCV GStreamer Diagnostic...")

# The GStreamer Pipeline: Bypasses V4L2 and grabs frames directly from the new libcamera system
pipeline = "libcamerasrc ! video/x-raw, width=640, height=480, framerate=30/1 ! videoconvert ! appsink"

# We pass cv2.CAP_GSTREAMER to tell OpenCV how to read the pipeline
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

time.sleep(1) # Warmup time

if not cap.isOpened():
    print("[RESULT] ERROR: OpenCV could not open the GStreamer pipeline.")
    print("This usually means OpenCV wasn't compiled with GStreamer support.")
else:
    print("[TEST] Pipeline opened. Attempting to grab a frame...")
    success, frame = cap.read()
    
    if success:
        print(f"[RESULT] MASSIVE SUCCESS! We bypassed the OS and grabbed a frame! Size: {frame.shape}")
    else:
        print("[RESULT] SILENT FAILURE STILL ACTIVE: The pipeline opened but no frames arrived.")

cap.release()
print("[TEST] Diagnostic complete.")