import flet as ft
import requests
import threading


def main(page: ft.Page):
    page.title = "Cane Toad Trap Control"
    page.theme_mode = ft.ThemeMode.DARK
    
    # State
    state = {"pi_ip": "192.168.1.100", "connected": False}
    
    # UI Controls
    status_dot = ft.Text("●", size=20, color="red")
    status_text = ft.Text("Disconnected", color="red", weight="bold")
    toad_count = ft.Text("0", size=48, weight="bold", color="cyan")
    ip_field = ft.TextField(label="Pi IP Address", value="192.168.1.100", width=250)
    
    def update_status(connected):
        state["connected"] = connected
        status_dot.color = "cyan" if connected else "red"
        status_text.value = "Connected" if connected else "Disconnected"
        status_text.color = "cyan" if connected else "red"
        page.update()
    
    def check_connection():
        try:
            resp = requests.get(f"http://{state['pi_ip']}:5000/api/stats", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                toad_count.value = str(data.get("caught", 0))
                update_status(True)
                return
        except:
            pass
        update_status(False)
    
    def on_connect(e):
        state["pi_ip"] = ip_field.value
        thread = threading.Thread(target=check_connection)
        thread.daemon = True
        thread.start()
    
    def make_action_handler(action):
        def handler(e):
            try:
                requests.post(f"http://{state['pi_ip']}:5000/api/trigger/{action}", timeout=3)
                dlg = ft.AlertDialog(
                    title=ft.Text("✓ Success"),
                    content=ft.Text(f"{action.title()} triggered!")
                )
                page.dialog = dlg
                dlg.open = True
                thread = threading.Thread(target=check_connection)
                thread.daemon = True
                thread.start()
            except Exception as ex:
                dlg = ft.AlertDialog(
                    title=ft.Text("✗ Error"),
                    content=ft.Text(f"Connection failed: {str(ex)}")
                )
                page.dialog = dlg
                dlg.open = True
            page.update()
        return handler
    
    # Build UI
    content = ft.Column(
        [
            ft.Row([status_dot, status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Container(
                ft.Column(
                    [ft.Text("Toads Captured", color="gray"), toad_count],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor="#1e1e1e",
                border_radius=12,
                padding=20,
            ),
            ft.Divider(),
            ft.Text("Controls", weight="bold", size=16),
            ft.Row(
                [
                    ft.Button("Front Gate", on_click=make_action_handler("front"), width=120),
                    ft.Button("Rear Gate", on_click=make_action_handler("rear"), width=120),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Button("Euthanasia Cycle", on_click=make_action_handler("euthanasia"), width=250),
            ft.Divider(),
            ft.Text("Settings", weight="bold", size=16),
            ip_field,
            ft.Button("Connect to Pi", on_click=on_connect, width=250),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    
    page.add(content)
    check_connection()


if __name__ == "__main__":
    ft.app(target=main)
