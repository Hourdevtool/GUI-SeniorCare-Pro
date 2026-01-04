import subprocess
import customtkinter as ctk
import sys

# ===== Global Keyboard Functions =====
def show_onboard():
    """แสดงแป้นพิมพ์บนจอ (Windows ใช้ osk.exe, Linux ใช้ onboard)"""
    try:
        if sys.platform == 'win32':
            # Windows: ใช้ On-Screen Keyboard
            subprocess.Popen(['osk.exe'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        else:
            # Linux: ใช้ onboard
            subprocess.Popen(['onboard'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Cannot show keyboard: {e}")

def hide_onboard():
    """ซ่อนแป้นพิมพ์บนจอ (Windows: osk.exe, Linux: onboard)"""
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'osk.exe'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=False)
        else:
            subprocess.run(['killall', 'onboard'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=False)
    except FileNotFoundError:
        pass
    except Exception:
        pass

def create_entry_with_keyboard(parent, **kwargs):
    """สร้าง Entry ที่เรียก keyboard อัตโนมัติ"""
    entry = ctk.CTkEntry(parent, **kwargs)
    entry.bind('<Button-1>', lambda e: show_onboard())
    entry.bind('<FocusIn>', lambda e: show_onboard())
    entry.bind('<FocusOut>', lambda e: hide_onboard())
    return entry

def setup_global_click_handler(window):
    """ตั้งค่า handler สำหรับคลิกที่พื้นที่ว่าง"""
    def on_global_click(event):
        widget = event.widget
        
        # ตรวจสอบว่า widget หรือ parent ของมันเป็น Entry/Textbox หรือไม่
        current = widget
        is_input_widget = False
        
        # ตรวจสอบ widget และ parent ย้อนขึ้นไป 5 ระดับ
        for _ in range(5):
            if isinstance(current, (ctk.CTkEntry, ctk.CTkTextbox)):
                is_input_widget = True
                break
            if hasattr(current, 'master'):
                current = current.master
            else:
                break
        
        # ถ้าไม่ได้คลิกที่ input ให้ซ่อน keyboard
        if not is_input_widget:
            hide_onboard()
    
    window.bind_all('<Button-1>', on_global_click)

def toggle_language():
    """สลับภาษาไทย ↔ อังกฤษ"""
    try:
        # ตรวจสอบ layout ปัจจุบัน
        result = subprocess.run(["setxkbmap", "-query"], capture_output=True, text=True)
        if "th" in result.stdout:
            # ถ้าเป็นไทย ให้สลับเป็นอังกฤษ
            subprocess.run(["setxkbmap", "us"])
            print("Switched to English")
        else:
            # ถ้าเป็นอังกฤษ ให้สลับเป็นไทย
            subprocess.run(["setxkbmap", "th"])
            print("เปลี่ยนเป็นภาษาไทยแล้ว")
    except Exception as e:
        print(f"Error switching language: {e}")

from config.styles import ROLE_THEMES

def get_role_theme(role=None):
    """
    ดึง theme ตาม role ที่กำหนด
    ถ้าไม่ระบุ role จะใช้ role จาก controller.user
    """
    if role is None:
        # พยายามดึง role จาก controller ถ้ามี
        try:
            import inspect
            frame = inspect.currentframe()
            # หา controller จาก frame
            for frame_info in inspect.stack():
                local_vars = frame_info.frame.f_locals
                if 'self' in local_vars and hasattr(local_vars['self'], 'controller'):
                    controller = local_vars['self'].controller
                    if hasattr(controller, 'user') and controller.user:
                        role = controller.user.get('urole', '').lower()
                        break
        except:
            pass
    
    if role is None:
        role = 'patient'  # default
    
    role = role.lower()
    if role not in ROLE_THEMES:
        role = 'patient'  # fallback to patient
    
    return ROLE_THEMES[role]

def get_user_role_from_controller(controller):
    """ดึง role จาก controller"""
    if hasattr(controller, 'user') and controller.user:
        return controller.user.get('urole', '').lower()
    return 'patient'  # default

