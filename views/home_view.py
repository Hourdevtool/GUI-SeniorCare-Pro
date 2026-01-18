import customtkinter as ctk
from PIL import Image, ImageTk
import time
from tkinter import messagebox
import subprocess
import threading
import json
import os
import warnings
import re
from tkcalendar import Calendar
from datetime import datetime, timedelta
from pywifi import PyWiFi
from babel.dates import format_date
# model format เวลา
from lib.set_time import default_serializer
from lib.serial_handler import (
    recivetime,
    start_Serial_loop,
    request_reset_data_command,
    request_instant_dispense_command,
    get_dont_pick_threshold,
    set_dont_pick_threshold,
)
from notifier import Notifier
from network_monitor import NetworkMonitor
import serial
import requests
#

# nodel การเเจ้งเตือน
from lib.alert import sendtoTelegram, sendtoLine, sendtoLineWithDeduplication
from lib.loadenv import PATH
from lib.call import press_sos_automation

# model อ่านออกเสียง
from gtts import gTTS 
from pygame import mixer

SONG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "song")
VOICE_PROMPTS = {
    "complete": {"text": "จ่ายยาสำเร็จค่ะ", "filename": "complete.mp3"},
    "dontpick": {"text": "ผู้ป่วยกรุณารับยาด้วยค่ะ", "filename": "dontpick.mp3"},
    "fail": {"text": "ดันยาไม่สำเร็จค่ะ", "filename": "fail.mp3"},
}
STARTUP_GREETING = {
    "text": "สวัสดีค่ะ ซีเนียร์แคร์โปรพร้อมให้บริการค่ะ",
    "filename": "startup_greeting.mp3",
}
TEST_MODE_EMAIL = "siri@gmail.com"


# ------------------ ฝั่ง server------------------------
from server.auth import auth
from server.info import infoData
from server.managemedic import manageMedicData
from server.setting_time import setting_eat_time
from server.gemini import Gemini
from server.heart_report import heart_report
from server.eat_medicine_report import eat_medicine_report
from server.exportpdf import generate_pdf_sync
from server.setcounter import SetCounter
from server.device_status import Devicestatus
auth = auth()
manageData = infoData()
manageMedic = manageMedicData()
set_dispensing_time = setting_eat_time()
ai = Gemini()
set_counter = SetCounter()
Heart_report = heart_report()
medicine_report = eat_medicine_report()
device_status = Devicestatus()
# -----------------------------------------------------

# ------------------ Loading Screen------------------------
from loading_screen import LoadingScreen
# -----------------------------------------------------

# ===== Global Keyboard Functions (เพิ่มหลัง imports) =====
def show_onboard():
    """แสดงแป้นพิมพ์บนจอ (Windows ใช้ osk.exe, Linux ใช้ onboard)"""
    try:
        import sys
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
        import sys
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

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# suppress 3rd-party deprecation warnings (pygame/pkg_resources)
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")
# Hospital-friendly, simple, high-contrast palette
word_color = '#213547'        # Neutral dark for text
bottom_hover = "#E03131"      # Destructive hover (soft red)
ho_color = "#2FBF71"          # Secondary accent (soft green)
select_color = '#A7E3C6'      # Selection/confirm accents

back_color = '#F5FAFF'        # Very light blue background
force_color = '#2F6AA3'       # Primary action color (calm hospital blue)
text_main = '#1E293B'         # Main text color
hover_color = "#255A8A"       # Primary hover (slightly darker blue)
input_color = "#FFFFFF"       # Inputs: white for cleanliness
input_text = "#0B1220"       # Input text: near-black for readability

# Global UI style constants (scaled for 1024x600)
BUTTON_RADIUS = 15            # ปรับมุมโค้งให้เหมาะสม
TITLE_FONT_SIZE = 30          # ลดจาก 56
SECTION_TITLE_SIZE = 22
LABEL_FONT_FAMILY = "Arial"

# ===== Role-Based Theme System =====
# ระบบแต่งตกแยกตามระดับผู้ใช้ (Admin, User, Patient)
ROLE_THEMES = {
    'admin': {
        'name': 'ผู้ดูแลระบบ',
        'button': {
            'fg_color': '#F8FAFC',         # สีน้ำเงินจางลง - ดูนุ่มนวลขึ้น
            'hover_color': '#5A9BC4',      # สีน้ำเงินเข้มขึ้นเล็กน้อยเมื่อ hover
            'text_color': 'black',       # ข้อความสีขาว
            'border_color': '#5CA95C',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',          # พื้นหลังหลัก
            'border_color': '#E2E8F0',     # ขอบสีเทาอ่อน
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#F7FAFC',         # พื้นหลังกล่องข้อมูล
            'border_color': '#CBD5E0',     # ขอบกล่องข้อมูล
            'header_color': '#EDF2F7'      # สีหัวข้อ
        },
        'accent': '#2563EB',               # สีเน้น (น้ำเงิน)
        'layout': {
            'medicine_frame': {'x': 20, 'y': 280, 'width': 300, 'height': 300},
            'medication_frame': {'x': 340, 'y': 280, 'width': 340, 'height': 300},
            'user_info_frame': {'x': 700, 'y': 280, 'width': 300, 'height': 300},
            'menu_buttons': {'start_x': 30, 'start_y': 600, 'spacing': 40, 'btn_width': 100, 'btn_height': 90}
        }
    },
    'user': {
        'name': 'ผู้ใช้งาน',
        'button': {
            'fg_color': '#F8FAFC',         # สีน้ำเงินจางลง - ดูนุ่มนวลขึ้น
            'hover_color': '#5A9BC4',      # สีน้ำเงินเข้มขึ้นเล็กน้อยเมื่อ hover
            'text_color': 'black',       # ข้อความสีขาว
            'border_color': '#5CA95C',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',         # พื้นหลังหลัก
            'border_color': '#B8D4F0',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#E8F4FD',         # พื้นหลังกล่องข้อมูล (น้ำเงินอ่อน)
            'border_color': '#A8DADC',     # ขอบกล่องข้อมูล
            'header_color': '#D1ECF1'      # สีหัวข้อ
        },
        'accent': '#2F6AA3',               # สีเน้น (น้ำเงิน)
        'layout': {
            'medicine_frame': {'x': 20, 'y': 280, 'width': 300, 'height': 300},
            'medication_frame': {'x': 340, 'y': 280, 'width': 340, 'height': 300},
            'user_info_frame': {'x': 700, 'y': 280, 'width': 300, 'height': 300},
            'menu_buttons': {'start_x':60, 'start_y': 600, 'spacing': 100, 'btn_width': 100, 'btn_height': 90}
        }
    },
    'patient': {
        'name': 'ผู้ป่วย',
        'button': {
            'fg_color': '#FFFFFF',         # สีขาว - ดูสะอาด
            'hover_color': '#E9ECEF',      # สีเทาอ่อนเมื่อ hover
            'text_color': '#1D3557',       # ข้อความสีน้ำเงินเข้ม
            'border_color': '#A8DADC',     # ขอบสีฟ้าอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',         # พื้นหลังหลัก
            'border_color': '#E8F4FD',     # ขอบสีฟ้าอ่อนมาก
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#F8F9FA',         # พื้นหลังกล่องข้อมูล
            'border_color': '#DEE2E6',     # ขอบกล่องข้อมูล
            'header_color': '#E8F4FD'      # สีหัวข้อ
        },
        'accent': '#8acaef',               # สีเน้น (ฟ้าอ่อน)
        'layout': {
            # ปรับตำแหน่งและขนาดให้เหมาะสมกับหน้าจอ 1024x600
            # จำนวนยาคงเหลือ - ด้านซ้าย, ขนาดใหญ่ขึ้น
            'medicine_frame': {'x': 20, 'y': 280, 'width': 360, 'height': 280},
            # การตั้งค่ายา - ตรงกลาง, ขนาดใหญ่ขึ้น
            'medication_frame': {'x': 400, 'y': 280, 'width': 600, 'height': 280},
            # ข้อมูลผู้ใช้ - ด้านขวา, ขนาดใหญ่ขึ้น
            'user_info_frame': {'x': 20, 'y': 570, 'width': 850, 'height': 220},
            # ปุ่มเมนู - ปรับตำแหน่งให้อยู่ด้านล่าง
            'menu_buttons': {'start_x': 910, 'start_y': 570, 'btn_width': 100, 'btn_height': 90}
        }
    }
}

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

# login class moved to views/login_view.py

class HomePage(ctk.CTkFrame):
    def on_show(self):
        print("HomePage is now visible")
        self.update_test_mode_visibility()
        if (
            hasattr(self.controller, "voice_player")
            and not getattr(self.controller, "_startup_greeting_played", True)
        ):
            self.controller._startup_greeting_played = True
            self.controller.voice_player.play_startup_greeting()
        # Re-create UI elements to adapt to login mode changes
        self.create_medication_display()
        self.create_user_info_display()
        self.create_counter_medicine_display()

        # อัพเดทข้อมูลการตั้งค่ายาเมื่อแสดงหน้า
        self.update_medication_info()
        self.controller.start_background_polling()
        self.controller.fetch_medications(show_loading_screen=False, on_complete_callback=None)

        if self.controller.last_known_schedule_data:
            print("Data found in MainApp cache, rendering immediately.")
            # ถ้ามี, ใช้วาด UI ทันที
            self._render_medication_data(self.controller.last_known_schedule_data, None)
        else:
            # ถ้าไม่มี (เพิ่งเปิดเครื่อง), ให้เริ่มดึงข้อมูลแบบ non-blocking
            print("No cached data in MainApp, triggering new fetch.")
            self.update_medication_info()
        # อัพเดทข้อมูลผู้ใช้เมื่อแสดงหน้า
        self.update_user_info()
        self.create_menu_buttons(self.controller)

        self.check_network_and_update_buttons()
        
        # รีเซ็ตปุ่ม SOS เมื่อกลับมาที่หน้า HomePage เพื่อให้สามารถกดได้อีกครั้ง
        # และควบคุมการแสดงปุ่ม SOS ตาม role
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        
        # แสดงปุ่ม SOS สำหรับทุก role (Patient, User, และ Admin)
        # แสดงปุ่ม SOS เฉพาะ role 'patient'
        if hasattr(self, 'call_button') and self.call_button:
            if user_role == 'patient':
                # แสดงปุ่ม SOS สำหรับ patient
                try:
                    self.call_button.place_info()
                except:
                    self.call_button.place(x=550, y=35)
                    self.reset_sos_button()
            else:
                # ซ่อนปุ่ม SOS สำหรับ role อื่น
                self.call_button.place_forget()

        # 🟢 Restart Clock Loop to prevent frozen time
        self.update_datetime()
       
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.menu_buttons = {}
        self.button_original_styles = {}
        self.call_button_original_style = None
        self._last_checked_network_status = None
        self._battery_received = False  # Flag ว่าเคยได้รับค่าแบตเตอรี่จริงหรือยัง
        self.sos_button_clicked = False  # Flag สำหรับป้องกันการกดปุ่ม SOS ซ้ำ

        # พื้นหลัง (ปรับขนาดเป็น 1024x600)
        bg_image = Image.open(f"{PATH}image/home.png").resize((1024, 800), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ไอคอน battery และ wifi
        self.add_status_icons()
        # วันที่และเวลา
        self.date_label = ctk.CTkLabel(self, text="", font=("TH Sarabun New", 35, "bold"),
                                       fg_color="#8acaef", text_color="white")
        self.date_label.place(x=58, y=185)

        self.time_label = ctk.CTkLabel(self, text="", font=("TH Sarabun New", 40, "bold"),
                                       fg_color="#8acaef", text_color="white")
        self.time_label.place(x=365, y=182)

        # สร้างส่วนแสดงข้อมูลการตั้งค่ายา
        self.create_medication_display()

        # สร้างส่วนแสดงข้อมูลผู้ใช้
        self.create_user_info_display()
        
        # สร้างส่วนแสดงจำนวนยาคงเหลือ (เพิ่มบรรทัดนี้)
        self.create_counter_medicine_display()
     
        self.update_datetime()

    def add_status_icons(self):
        # โหลดรูปแบตเตอรี่ทั้งหมด
        battery_size = (60, 60)  # ขนาดรูปแบตเตอรี่
        self.battery_images = {}
        battery_levels = [100, 75, 50, 25]
        
        for level in battery_levels:
            try:
                battery_image = Image.open(f"{PATH}imgNew/battery-{level}.png").resize(battery_size, Image.Resampling.LANCZOS)
                self.battery_images[level] = ImageTk.PhotoImage(battery_image)
            except FileNotFoundError:
                print(f"Warning: battery-{level}.png not found")
        
        # ใช้รูป default ถ้าไม่มีรูป
        try:
            default_image = Image.open(f"{PATH}imgNew/battery.png").resize(battery_size, Image.Resampling.LANCZOS)
            self.battery_images['default'] = ImageTk.PhotoImage(default_image)
        except:
            pass
        
        # สร้าง label สำหรับแสดงรูปแบตเตอรี่
        self.battery_label = ctk.CTkLabel(
            self, 
            image=self.battery_images.get(100, self.battery_images.get('default')),
            text="", 
            bg_color="#8acaef",
            fg_color="transparent",
            corner_radius=0,  # มุมโค้งมน
        )
        self.battery_label.place(x=830, y=40)
        
        self.battery_percent_label = ctk.CTkLabel(
            self,
            text="0%",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black",
            bg_color="#8acaef",
            fg_color="transparent",
        )
        self.battery_percent_label.place(x=942, y=70, anchor="center")
        
        # เชื่อมต่อกับ battery_percent_var จาก controller
        if hasattr(self.controller, 'battery_percent_var'):
            self.controller.battery_percent_var.trace_add('write', self.update_battery_display)
            # อัพเดตครั้งแรก
            self.update_battery_display()
        
        # โหลดรูป SOS ทั้งสามแบบ (ออนไลน์, ออฟไลน์, และค้าง)
        call_button_online = Image.open(f"{PATH}imgNew/sos.png").resize((200, 200), Image.Resampling.LANCZOS)
        self.call_photo_online = ImageTk.PhotoImage(call_button_online)
        
        call_button_offline = Image.open(f"{PATH}imgNew/sos-offline.png").resize((200, 200), Image.Resampling.LANCZOS)
        self.call_photo_offline = ImageTk.PhotoImage(call_button_offline)
        
        call_button_clicked = Image.open(f"{PATH}imgNew/sos-ค้าง.png").resize((200, 200), Image.Resampling.LANCZOS)
        self.call_photo_clicked = ImageTk.PhotoImage(call_button_clicked)
        
         # --- AI Status Icon ---
        # User requested using emoji 📸 with green color
        self.ai_status_label = ctk.CTkLabel(
            self,
            text="📸",
            font=("Arial", 40), # Large font for icon size
            text_color="#32CD32", # Lime Green
            bg_color="#8acaef", # Match header background
            fg_color="transparent"
        )
        # Position it near battery or date/time
        # Battery is at 830, 40. Date/Time at 58, 185 and 365, 182.
        # Let's put it top left or near center top? 
        # User said "show icon camera at home page... when closed show nothing"
        # Let's put it on the header bar, maybe left of SOS button or similar.
        # SOS is at 550, 35 (if patient).
        # Let's try x=480, y=40.
        
        # We don't place it yet, we place it in update_ai_status_icon
        
        # Bind to controller variable
        if hasattr(self.controller, 'is_ai_running_var'):
            self.controller.is_ai_running_var.trace_add('write', self.update_ai_status_icon)
            self.update_ai_status_icon()

        
        # ใช้รูปออนไลน์เป็นค่าเริ่มต้น
        self.call_photo = self.call_photo_online
        
        # สีสำหรับปุ่ม SOS - ตกแต่งให้สวยงามขึ้น
        sos_fg_color = "#EF5350"  # สีแดงสดใสสำหรับปุ่ม SOS
        sos_hover_color = "#EF5350"  # สีแดงเข้มขึ้นเมื่อ hover
        sos_bg_color = "#EF5350"
        sos_border_color = "#EF5350"  # สีขอบแดงอ่อน
        
        self.call_button = ctk.CTkButton(
            self, 
            image=self.call_photo, 
            text="",
            bg_color=sos_bg_color,
            fg_color=sos_fg_color,
            hover_color=sos_hover_color,
            width=200,
            border_width=0,  # เพิ่มขอบให้ดูสวยงาม
            border_color=sos_border_color,
            corner_radius=0,  # มุมโค้งมน
            height=200,
            command=self.on_video_call_click
        )
        # อย่า place ทันที - รอให้ on_show() ตรวจสอบ role ก่อน
        # self.call_button.place(x=550, y=35)  # ย้ายไปที่ on_show()
        
        # บันทึกสไตล์เดิมของปุ่ม SOS
        self.call_button_original_style = {
            'fg_color': sos_fg_color,
            'hover_color': sos_hover_color,
            'bg_color': sos_bg_color,
            'border_color': sos_border_color,
            'border_width': 0,
            'corner_radius': 0,
            'state': 'normal'
        } 

    def reset_sos_button(self):
        """รีเซ็ตสถานะปุ่ม SOS ให้สามารถกดได้อีกครั้ง"""
        if not hasattr(self, 'call_button') or not self.call_button:
            return
        
        self.sos_button_clicked = False
        
        # ตรวจสอบสถานะเครือข่ายเพื่อเลือกรูปภาพที่เหมาะสม
        if hasattr(self.controller, 'network_status_var'):
            is_online = self.controller.network_status_var.get() == "online"
            photo = self.call_photo_online if is_online else self.call_photo_offline
        else:
            photo = self.call_photo_online
        
        # คืนค่าปุ่ม SOS เป็นสไตล์เดิม
        if self.call_button_original_style:
            style = self.call_button_original_style
            self.call_button.configure(
                state=style['state'],
                image=photo,
                fg_color=style['fg_color'],
                hover_color=style['hover_color'],
                bg_color=style['bg_color'],
                border_color=style['border_color'],
                border_width=style['border_width'],
                corner_radius=style.get('corner_radius', 0)
            )

    def update_ai_status_icon(self, *args):
        """Show/Hide AI Camera Icon based on service status."""
        try:
            if not hasattr(self, 'ai_status_label') or not self.ai_status_label:
                return

            is_running = False
            if hasattr(self.controller, 'is_ai_running_var'):
                is_running = self.controller.is_ai_running_var.get()
            
            if is_running:
                # self.ai_status_label.configure(image=self.ai_icon_photo) # No image needed
                self.ai_status_label.place(x=780, y=35) # Adjusted y slightly for text alignment
                print(f"AI Icon Updating: Visible at 780, 45")
            else:
                self.ai_status_label.place_forget()
                print(f"AI Icon Updating: Hidden (Running={is_running})")
        except Exception as e:
            print(f"Error updating AI icon: {e}")

    def update_battery_display(self, *args):
        """อัพเดตการแสดงผลแบตเตอรี่ตามค่า battery_percent_var"""
        try:
            if not hasattr(self.controller, 'battery_percent_var'):
                return
            
            battery_percent = self.controller.battery_percent_var.get()
            
            # ตรวจสอบสถานะการเชื่อมต่อ
            is_connected = True
            if hasattr(self.controller, 'device_status_var'):
                device_status = str(self.controller.device_status_var.get())
                # ตรวจสอบว่ามี error หรือไม่
                if device_status and ("Error" in device_status or "Disconnected" in device_status or "Waiting" in device_status):
                    is_connected = False
            
            # ตรวจสอบว่ายังไม่ได้รับค่าหรือขาดการเชื่อมต่อ
            if battery_percent is None:
                # แสดง "-- %" เมื่อยังไม่ได้รับค่า
                if hasattr(self, 'battery_percent_label'):
                    self.battery_percent_label.configure(text="-- %")
                if hasattr(self, 'battery_label'):
                    if 'default' in self.battery_images:
                        self.battery_label.configure(image=self.battery_images['default'])
                    elif 25 in self.battery_images:
                        self.battery_label.configure(image=self.battery_images[25])
                return
            
            # แปลงค่าเป็นเปอร์เซ็นต์ (0-100)
            battery_percent = float(battery_percent)
            
            # ถ้าค่าเป็น 0-1 (ทศนิยม) แปลงเป็น 0-100
            if battery_percent <= 1.0 and battery_percent > 0.0:
                battery_percent = battery_percent * 100
                # ตั้ง flag ว่าได้รับค่าจริงแล้ว
                self._battery_received = True
            elif battery_percent > 1.0:
                # ถ้าค่า > 1 แสดงว่าเป็นเปอร์เซ็นต์แล้ว (0-100)
                # ตั้ง flag ว่าได้รับค่าจริงแล้ว
                self._battery_received = True
            
            # ตรวจสอบว่าค่าเป็น 0.0 จริงๆ หรือยังไม่ได้รับค่า
            # ถ้าเป็น 0.0 และยังไม่เคยได้รับค่าจริง หรือขาดการเชื่อมต่อ ให้แสดง "-- %"
            if battery_percent == 0.0:
                if not self._battery_received or not is_connected:
                    # แสดง "-- %" เมื่อยังไม่ได้รับค่าหรือขาดการเชื่อมต่อ
                    if hasattr(self, 'battery_percent_label'):
                        self.battery_percent_label.configure(text="-- %")
                    if hasattr(self, 'battery_label'):
                        if 'default' in self.battery_images:
                            self.battery_label.configure(image=self.battery_images['default'])
                        elif 25 in self.battery_images:
                            self.battery_label.configure(image=self.battery_images[25])
                    return
            
            # จำกัดค่าให้อยู่ในช่วง 0-100
            battery_percent = max(0, min(100, battery_percent))
            
            # เลือกรูปแบตเตอรี่ตามเปอร์เซ็นต์
            if battery_percent >= 75:
                battery_image_key = 100
            elif battery_percent >= 50:
                battery_image_key = 75
            elif battery_percent >= 25:
                battery_image_key = 50
            else:
                battery_image_key = 25
            
            # อัพเดตรูปแบตเตอรี่
            if hasattr(self, 'battery_label') and battery_image_key in self.battery_images:
                self.battery_label.configure(image=self.battery_images[battery_image_key])
            elif hasattr(self, 'battery_images') and 'default' in self.battery_images:
                self.battery_label.configure(image=self.battery_images['default'])
            
            # อัพเดตเปอร์เซ็นต์ (แสดงเป็นจำนวนเต็ม)
            if hasattr(self, 'battery_percent_label'):
                self.battery_percent_label.configure(text=f"{int(battery_percent)}%")
                
        except Exception as e:
            print(f"Error updating battery display: {e}")
            # แสดง "-- %" เมื่อเกิด error
            if hasattr(self, 'battery_percent_label'):
                self.battery_percent_label.configure(text="-- %")

    def create_menu_buttons(self, controller):
        # Clear existing buttons
        if hasattr(self, 'menu_buttons'):
            for btn in self.menu_buttons.values():
                btn.destroy()
        self.menu_buttons = {}
        self.button_original_styles = {}
        
        # Get user role (urole field from user data)
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        
        # Get theme for current role
        theme = get_role_theme(user_role)
        
        # Level 3: Patient (ผู้ป่วย) - Show only SOS button (already visible) and Logout
        if user_role == 'patient':
            try:
                logout_icon_path = f"{PATH}imgNew/iconout.png"
                logout_img = Image.open(logout_icon_path).resize((100, 100), Image.Resampling.LANCZOS)
                logout_photo = ImageTk.PhotoImage(logout_img)
                
                # Place logout button at bottom right
                logout_btn = ctk.CTkButton(
                    self,
                    image=logout_photo,
                    text="ออกระบบ",
                    compound="top",
                    font=("TH Sarabun New", 24, "bold"),  # เพิ่มขนาดฟอนต์
                    fg_color="white",
                    bg_color="#8acaef",
                    hover_color="#FFCDC9",
                    text_color="black",
                    border_width=5,
                    border_color="#FFCDD2",
                    width=100,
                    height=220,
                    corner_radius=0,
                    command=self.confirm_logout
                )
                logout_btn.place(x=880, y=570)  # ปรับตำแหน่งให้เหมาะสมกับหน้าจอ 1024x600
                logout_btn.image = logout_photo  # Keep reference
                self.menu_buttons['logout'] = logout_btn
                
                # Ensure SOS button is visible for patients
                if hasattr(self, 'call_button') and self.call_button:
                    self.call_button.place(x=550, y=35)
            except Exception as e:
                print(f"Error creating patient logout button: {e}")
            return
        
        # Level 2: User (ผู้ใช้งาน) - Show only: ตั้งเวลา, สุขภาพ, รายงาน, ออกระบบ
        if user_role == 'user':
            btn_size = (100, 100)
            btn_images = {}
            
            # Show: ตั้งเวลา (Frame3), สุขภาพ (Frame4), รายงาน (ReportFrame), ออกระบบ (login), ปิดเครื่อง
            paths = [
                f"{PATH}imgNew/icontime.png",
                f"{PATH}imgNew/iconheath.png",
                f"{PATH}imgNew/iconreport.png",
                f"{PATH}imgNew/iconout.png",
                f"{PATH}imgNew/icondow.png"
            ]
            btn_texts = [
                "ตั้งเวลา",
                "สุขภาพ",
                "รายงาน",
                "ออกระบบ",
                "ปิดเครื่อง"
            ]
            # Local imports to avoid circular dependency
            from views.schedule_setup_view import Frame3
            from views.health_view import Frame4
            from views.report_view import ReportFrame
            from views.login_view import login
            
            pages = [Frame3, Frame4, ReportFrame, login, None]  # None สำหรับปุ่มปิดเครื่อง  
            
            for i, path in enumerate(paths, start=1):
                try:
                    img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)
                    btn_images[i] = ImageTk.PhotoImage(img)
                except FileNotFoundError:
                    print(f"Error: {path} not found.")
            
            # ซ่อนปุ่ม SOS สำหรับ User (เผื่อกรณีค้าง)
            if hasattr(self, 'call_button') and self.call_button:
                self.call_button.place_forget()
            
            # จัดปุ่มเป็น 1 แถว - ใช้ค่าจาก theme layout
            menu_layout = theme.get('layout', {}).get('menu_buttons', {})
            btn_width = menu_layout.get('btn_width', 100)
            btn_height = menu_layout.get('btn_height', 90)
            start_x = menu_layout.get('start_x', 30)
            start_y = menu_layout.get('start_y', 600)
            spacing = menu_layout.get('spacing', 40)
            
            for i in range(len(paths)):
                if i + 1 in btn_images:
                    text = btn_texts[i]
                    x_pos = start_x + i * (btn_width + spacing)
                    y_pos = start_y
                    
                    # คำสั่งของแต่ละปุ่ม
                    if i == 3:  # Logout button (index 3 = ออกระบบ)
                        command = self.confirm_logout
                    elif i == 4:  # Shutdown button (index 4 = ปิดเครื่อง)
                        command = self.shutdown_system
                    else:
                        command = lambda i=i: controller.show_frame(pages[i])
                    
                    # ใช้ theme ตาม role
                    btn_style = theme['button']
                    style = {
                        'fg_color': btn_style['fg_color'],
                        'hover_color': btn_style['hover_color'],
                        'text_color': btn_style['text_color'],
                        'border_color': btn_style['border_color']
                    }
                    
                    # สร้างปุ่ม
                    btn = ctk.CTkButton(
                        self,
                        image=btn_images[i + 1],
                        text=text,
                        compound="top",
                        font=("TH Sarabun New", 22, "bold"),
                        fg_color=btn_style['fg_color'],
                        bg_color="#000001",   
                        hover_color=btn_style['hover_color'],
                        text_color=btn_style['text_color'],
                        border_width=btn_style['border_width'],
                        border_color=btn_style['border_color'],
                        width=100,
                        height=90,
                        corner_radius=btn_style['corner_radius'],
                        command=command
                    )
                    btn.place(x=x_pos, y=y_pos)
                    self.menu_buttons[i] = btn
                    self.button_original_styles[i] = style
            return

        # Level 1: Admin (ผู้ดูแลระบบ) - Show restricted menu (User Info, Medication Info, Logout, Shutdown)
        btn_size = (100, 100)
        btn_images = {}
        
        # กำหนดปุ่มสำหรับ Admin ตามที่ต้องการ: ข้อมูลผู้ใช้, ข้อมูลยา, ออกระบบ, ปิดเครื่อง
        paths = [
            f"{PATH}imgNew/iconuser.png", 
            f"{PATH}imgNew/icondog.png", 
            f"{PATH}imgNew/iconout.png",
            f"{PATH}imgNew/icondow.png"
        ]
        btn_texts = [
            "ข้อมูลผู้ใช้", 
            "ข้อมูลยา", 
            "ออกระบบ", 
            "ปิดเครื่อง"
        ]
        # Local imports to avoid circular dependency
        from views.user_info_view import info
        from views.medication_stock_view import Frame2
        from views.login_view import login
        
        # Pages mapping: info -> ข้อมูลผู้ใช้, Frame2 -> ข้อมูลยา, login -> ออกระบบ, None -> ปิดเครื่อง
        pages = [info, Frame2, login, None]

        for i, path in enumerate(paths, start=1):
            try:
                img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)
                btn_images[i] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Error: {path} not found.")

        # ซ่อนปุ่ม SOS สำหรับ Admin
        if hasattr(self, 'call_button') and self.call_button:
            self.call_button.place_forget()

        # จัดปุ่มให้อยู่กึ่งกลางและกระจายตัวสวยงาม
        btn_width = 100
        spacing = 160 # เพิ่มระยะห่างให้ดูเต็ม
        screen_width = 1024
        total_buttons = len(paths)
        
        total_content_width = (total_buttons * btn_width) + ((total_buttons - 1) * spacing)
        start_x = (screen_width - total_content_width) // 2
        start_y = 600

        for i in range(len(paths)):
            if i + 1 in btn_images:
                text = btn_texts[i]
                
                # คำนวณตำแหน่ง (แถวเดียว)
                x_pos = start_x + i * (btn_width + spacing)
                y_pos = start_y


                # คำสั่งของแต่ละปุ่ม
                # index 0: ข้อมูลผู้ใช้ -> pages[0]
                # index 1: ข้อมูลยา -> pages[1]
                # index 2: ออกระบบ -> confirm_logout
                # index 3: ปิดเครื่อง -> shutdown_system
                
                if i == 2: # Logout
                    command = self.confirm_logout
                elif i == 3: # Shutdown
                    command = self.shutdown_system
                else:
                    command = lambda i=i: controller.show_frame(pages[i])
                
                # ใช้ theme ตาม role
                btn_style = theme['button']
                style = {
                    'fg_color': btn_style['fg_color'],
                    'hover_color': btn_style['hover_color'],
                    'text_color': btn_style['text_color'],
                    'border_color': btn_style['border_color']
                }

                # สร้างปุ่ม - เพิ่มขนาดฟอนต์สำหรับ admin mode
                is_admin_mode = (user_role == 'admin')
                btn_font_size = 26 if is_admin_mode else 22
                
                btn = ctk.CTkButton(
                    self,
                    image=btn_images[i + 1],
                    text=text,
                    compound="top",
                    font=("TH Sarabun New", btn_font_size, "bold"),
                    fg_color=btn_style['fg_color'],
                    bg_color="#000001",   
                    hover_color=btn_style['hover_color'],
                    text_color=btn_style['text_color'],
                    border_width=btn_style['border_width'],
                    border_color=btn_style['border_color'],
                    width=100,
                    height=90,
                    corner_radius=btn_style['corner_radius'],
                    command=command
                )
                btn.place(x=x_pos, y=y_pos)
                self.menu_buttons[i] = btn
                self.button_original_styles[i] = style

    def confirm_logout(self):
        response = messagebox.askyesno("ยืนยันออกจากระบบ", "คุณต้องการออกจากระบบหรือไม่?")
        if response:
            # Import login locally to avoid circular dependency
            from views.login_view import login
            
            # Switch to login screen IMMEDIATELY (don't wait for cleanup)
            self.controller.show_frame(login)
            
            # Do cleanup in background thread to avoid blocking UI
            def cleanup_thread():
                try:
                    self.controller.stop_background_polling()
                    self.controller.user = None
                    if os.path.exists("user_data.json"):
                        os.remove("user_data.json")
                except Exception as e:
                    print(f"เกิดข้อผิดพลาดขณะออกจากระบบ: {e}")
            
            threading.Thread(target=cleanup_thread, daemon=True).start()

    def shutdown_system(self):
        response = messagebox.askyesno("ยืนยัน", "คุณต้องการปิดเครื่องหรือไม่?")
        if response:
            import sys
            if sys.platform == 'win32':
                os.system("shutdown /s /t 1")
            else:
                # สำหรับ Raspberry Pi / Linux
                os.system("sudo shutdown -h now")

    def create_medication_display(self):
        # Always destroy existing frame first
        if hasattr(self, 'medication_frame') and self.medication_frame:
            self.medication_frame.destroy()
            self.medication_frame = None

        # Check User Role
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        
        # Show for all roles: Patient, User, and Admin
        is_patient_mode = (user_role == 'patient')
        height_box = 280 if is_patient_mode else 300
        # list_height = 400 if is_patient_mode else 150

        # ใช้ theme ตาม role
        theme = get_role_theme(user_role)
        frame_style = theme['frame']
        info_style = theme['info_box']
        layout = theme.get('layout', {})
        
        # ดึงค่าตำแหน่งและขนาดจาก theme layout
        med_layout = layout.get('medication_frame', {})
        med_x = med_layout.get('x', 340)
        med_y = med_layout.get('y', 280)
        med_width = med_layout.get('width', 340)
        med_height = med_layout.get('height', height_box)

        # ปรับปรุงการแสดงข้อมูลยาให้สวยงาม
        self.medication_frame = ctk.CTkFrame(
            self,
            width=med_width,
            height=med_height,
            corner_radius=0,
            fg_color=frame_style['fg_color'],
            bg_color=frame_style['bg_color'],
            border_width=frame_style['border_width'],
            border_color=frame_style['border_color']
        )
        self.medication_frame.place(x=med_x, y=med_y)
        #pywinstyles.set_opacity(self.medication_frame, value=1, color="#000001")

        # หัวข้อพร้อมไอคอน - ปรับขนาดตาม role
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        header_width = (med_width - 20) if is_patient_mode else 320
        header_font_size = 32 if is_patient_mode else (28 if is_user_mode else (27 if is_admin_mode else 25))
        title_font_size = 32 if is_patient_mode else (28 if is_user_mode else (27 if is_admin_mode else 25))
        
        header_frame = ctk.CTkFrame(
            self.medication_frame,
            width=header_width,
            height=50 if is_patient_mode else 45,
            corner_radius=20,
            fg_color=info_style['header_color']
        )
        header_frame.place(x=10, y=10)

        medication_icon = ctk.CTkLabel(
            header_frame,
            text=" ",
            font=("TH Sarabun New", 28 if is_patient_mode else (26 if is_user_mode else (25 if is_admin_mode else 24))),
            fg_color="transparent"
        )
        medication_icon.place(x=10, y=10 if is_patient_mode else 8)

        self.medication_title = ctk.CTkLabel(
            header_frame,
            text="การตั้งค่ายา",
            font=("TH Sarabun New", title_font_size, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.medication_title.place(x=30, y=12 if is_patient_mode else 10)

        # ปุ่มควบคุม (แสดงสำหรับ Admin และ User)
        is_admin_mode = (user_role == 'admin')
        is_user_mode = (user_role == 'user')
        if is_admin_mode or is_user_mode:
            self.refresh_button = ctk.CTkButton(
                header_frame,
                text="รีเซ็ต",
                font=("TH Sarabun New", 20, "bold"),
                fg_color="#f4b81a",
                hover_color="#2D6A4F",
                text_color="white",
                corner_radius=8,
                width=40,
                height=25,
                command=self.reset_and_update
            )
            self.refresh_button.place(x=250, y=8)
            
            # บันทึกสไตล์เดิมของปุ่มรีเซ็ต
            self.refresh_button_original_style = {
                'fg_color': "#f4b81a",
                'hover_color': "#2D6A4F",
                'text_color': "white",
                'state': 'normal'
            }

            self.setting_button = ctk.CTkButton(
                header_frame,
                text="รีเฟรช",
                font=("TH Sarabun New", 20, "bold"),
                fg_color="#007BFF",
                hover_color="#0056B3",
                text_color="white",
                corner_radius=8,
                width=40,
                height=25,
                command=lambda: self.update_medication_info()
            )
            self.setting_button.place(x=160, y=8)
            
            # บันทึกสไตล์เดิมของปุ่มรีเฟรช
            self.setting_button_original_style = {
                'fg_color': "#007BFF",
                'hover_color': "#0056B3",
                'text_color': "white",
                'state': 'normal'
            }

        # คำนวณความสูงของ list frame จากความสูงของ frame หลัก
        list_height = med_height - (75 if is_patient_mode else 110)
        # สำหรับ patient mode: ลด width เล็กน้อยเพื่อให้ scrollbar แสดงชัดเจน
        list_width = (med_width - 30) if is_patient_mode else 310
        
        # สร้างกรอบสำหรับแสดงรายการยา
        # สำหรับ patient mode: ตั้งค่า scrollbar ให้เห็นชัดเจน
        scrollbar_params = {}
        if is_patient_mode:
            scrollbar_params = {
                'scrollbar_button_color': '#8acaef',
                'scrollbar_button_hover_color': '#6BA8D1',
                'scrollbar_fg_color': '#E8F4FD'
            }
        
        self.medication_list_frame = ctk.CTkScrollableFrame(
            self.medication_frame,
            width=list_width,
            height=list_height,
            fg_color="#F8F9FA",
            corner_radius=10,
            border_width=1,
            border_color="#DEE2E6",
            **scrollbar_params
        )
        self.medication_list_frame.place(x=10, y=(70 if is_patient_mode else 65))

        self.medication_labels = []

    def create_user_info_display(self):
        # Always destroy existing frame first
        if hasattr(self, 'user_info_frame') and self.user_info_frame:
            self.user_info_frame.destroy()
            self.user_info_frame = None

        # Check User Role
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        
        # Show for all roles: Patient, User, and Admin
        is_patient_mode = (user_role == 'patient')
        height_box = 280 if is_patient_mode else 300
        # content_height = 430 if is_patient_mode else 230

        # ใช้ theme ตาม role
        theme = get_role_theme(user_role)
        frame_style = theme['frame']
        info_style = theme['info_box']
        layout = theme.get('layout', {})
        
        # ดึงค่าตำแหน่งและขนาดจาก theme layout
        user_layout = layout.get('user_info_frame', {})
        user_x = user_layout.get('x', 700)
        user_y = user_layout.get('y', 280)
        user_width = user_layout.get('width', 300)
        user_height = user_layout.get('height', height_box)

        # ปรับปรุงการแสดงข้อมูลผู้ใช้ให้สวยงาม
        self.user_info_frame = ctk.CTkFrame(
            self,
            width=user_width,
            height=user_height,
            corner_radius=0,
            fg_color=frame_style['fg_color'],
            bg_color=frame_style['bg_color'],
            border_width=frame_style['border_width'],
            border_color=frame_style['border_color']
        )
        self.user_info_frame.place(x=user_x, y=user_y)
        #pywinstyles.set_opacity(self.user_info_frame, value=1, color="#000001")

        # หัวข้อพร้อมไอคอน - ปรับขนาดตาม role
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        header_width = (user_width - 20) if is_patient_mode else 280
        title_font_size = 32 if is_patient_mode else (28 if is_user_mode else (27 if is_admin_mode else 25))
        
        header_frame = ctk.CTkFrame(
            self.user_info_frame,
            width=header_width,
            height=50 if is_patient_mode else 45,
            corner_radius=10,
            fg_color=info_style['header_color']
        )
        header_frame.place(x=10, y=10)

        user_icon = ctk.CTkLabel(
            header_frame,
            text=" ",
            font=("TH Sarabun New", 28 if is_patient_mode else (26 if is_user_mode else (25 if is_admin_mode else 24))),
            fg_color="transparent"
        )
        user_icon.place(x=10, y=10 if is_patient_mode else 8)

        # สร้าง mapping สำหรับแสดงชื่อระดับ
        role_display_names = {
            "patient": "ผู้ป่วย",
            "user": "ผู้ดูแลผู้ป่วย",
            "admin": "ผู้ดูแลระบบ"
        }
        
        # ดึงชื่อระดับตาม role
        role_display = role_display_names.get(user_role, "")
        title_text = f"ข้อมูลผู้ใช้ ({role_display})" if role_display else "ข้อมูลผู้ใช้"
        
        self.user_info_title = ctk.CTkLabel(
            header_frame,
            text= "ข้อมูลผู้ใช้ (" + role_display + ")",
            font=("TH Sarabun New", title_font_size, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.user_info_title.place(x=50, y=12 if is_patient_mode else 10)

        # คำนวณความสูงของ content จากความสูงของ frame หลัก
        content_height = user_height - (75 if is_patient_mode else 80)
        content_width = (user_width - 20) if is_patient_mode else 280

        # สร้างกรอบสำหรับแสดงข้อมูล
        self.user_info_content = ctk.CTkScrollableFrame(
            self.user_info_frame,
            width=content_width,
            height=content_height,
            fg_color="#F8F9FA",
            corner_radius=10,
            border_width=1,
            border_color="#DEE2E6"
        )
        self.user_info_content.place(x=10, y=65)

        self.user_info_labels = []

    def create_counter_medicine_display(self):
        # Always destroy existing frame first
        if hasattr(self, 'medicine_frame') and self.medicine_frame:
            self.medicine_frame.destroy()
            self.medicine_frame = None

        # Check User Role
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        
        # Show for all roles: Patient, User, and Admin
        is_patient_mode = (user_role == 'patient')
        height_box = 280 if is_patient_mode else 300
        # font_size จะถูกกำหนดใหม่ในส่วนที่สร้าง label

        # ใช้ theme ตาม role
        theme = get_role_theme(user_role)
        frame_style = theme['frame']
        info_style = theme['info_box']
        layout = theme.get('layout', {})
        
        # ดึงค่าตำแหน่งและขนาดจาก theme layout
        medicine_layout = layout.get('medicine_frame', {})
        medicine_x = medicine_layout.get('x', 20)
        medicine_y = medicine_layout.get('y', 280)
        medicine_width = medicine_layout.get('width', 300)
        medicine_height = medicine_layout.get('height', height_box)

        self.medicine_frame = ctk.CTkFrame(
            self,
            width=medicine_width,
            height=medicine_height,
            corner_radius=0,
            fg_color=frame_style['fg_color'],
            bg_color=frame_style['bg_color'],
            border_width=frame_style['border_width'],
            border_color=frame_style['border_color']
        )
        self.medicine_frame.place(x=medicine_x, y=medicine_y)
        #pywinstyles.set_opacity(self.medicine_frame, value=1, color="#000001")
        
        # Destroy previous test mode section if it exists
        if hasattr(self, 'test_mode_section') and self.test_mode_section:
            self.test_mode_section.destroy()
        self.test_mode_section = None
        
        # Destroy previous logout frame if it exists
        if hasattr(self, 'logout_frame') and self.logout_frame:
            self.logout_frame.destroy()
        self.logout_frame = None

        self.test_mode_slider = None
        self.test_mode_value_label = None
    
        # หัวข้อพร้อมไอคอน - ปรับขนาดตาม role
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        header_width = (medicine_width - 20) if is_patient_mode else 280
        title_font_size = 32 if is_patient_mode else (28 if is_user_mode else (27 if is_admin_mode else 25))
        
        header_frame = ctk.CTkFrame(
            self.medicine_frame,
            width=header_width,
            height=50 if is_patient_mode else 45,
            corner_radius=10,
            fg_color=info_style['header_color']
        )
        header_frame.place(x=10, y=10)
        
        # ปุ่มรีเซ็ตจำนวนยา (แสดงสำหรับ Admin และ User)
        is_admin_mode = (user_role == 'admin')
        is_user_mode = (user_role == 'user')
        if is_admin_mode or is_user_mode:
            self.reset_counter_button = ctk.CTkButton(
                header_frame,
                text="รีเซ็ต",
                font=("TH Sarabun New", 20, "bold"),
                fg_color="#f4b81a",
                hover_color="#2D6A4F",
                text_color="white",
                corner_radius=8,
                width=60,  # เพิ่มความกว้างให้ปุ่ม
                height=25,
                command=self.reset_medicine_count  # เอา lambda ออก
            )
            self.reset_counter_button.place(x=220, y=8)
            
            # บันทึกสไตล์เดิมของปุ่มรีเซ็ตจำนวนยา
            self.reset_counter_button_original_style = {
                'fg_color': "#f4b81a",
                'hover_color': "#2D6A4F",
                'text_color': "white",
                'state': 'normal'
            }

        self.medicine_title = ctk.CTkLabel(
            header_frame,
            text="จำนวนยาคงเหลือ",
            font=("TH Sarabun New", title_font_size, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.medicine_title.place(x=10, y=12 if is_patient_mode else 10)

        # เริ่มต้นค่าตัวแปรสำหรับเก็บจำนวนยา
        if hasattr(self.controller, 'user') and self.controller.user and 'count_medicine' in self.controller.user:
            self.medicine_count = self.controller.user['count_medicine']
        else:
            self.medicine_count = 28
        
        # สร้าง Label สำหรับแสดงจำนวนยา
        # ปรับขนาดและตำแหน่งสำหรับผู้ป่วย
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        if is_patient_mode:
            counter_width = medicine_width - 40  # ใช้ความกว้างเต็มของ frame ลบ padding
            counter_height = medicine_height - 80  # ใช้ความสูงเต็มของ frame ลบ header
            counter_x = 20
            counter_y = 70
            font_size = 140  # เพิ่มขนาดฟอนต์ให้ใหญ่ขึ้น
        else:
            counter_width = 250
            counter_height = 150
            counter_x = 25
            counter_y = 60
            font_size = 95 if is_user_mode else (90 if is_admin_mode else 80)  # เพิ่มขนาดฟอนต์สำหรับ user และ admin mode
            
        self.counter_medicine = ctk.CTkLabel(
            self.medicine_frame,
            text=str(self.medicine_count),
            width=counter_width,
            height=counter_height,
            fg_color="#F8F9FA",
            corner_radius=10,
            font=("TH Sarabun New", font_size, "bold"),
            text_color="#2E7D32"
        )
        self.counter_medicine.place(x=counter_x, y=counter_y)
        
        print(f"Medicine counter display created: {self.medicine_count} pills")
        
        # แสดง Test Mode สำหรับผู้ดูแล (Admin only)
        is_admin_mode = (user_role == 'admin')
        if is_admin_mode:
            self._build_test_mode_controls()

    def _build_test_mode_controls(self):
        if self.test_mode_section is not None:
            return

        self._test_mode_position = {"x": 780, "y": 120}
        self.test_mode_section = ctk.CTkFrame(
            self,
            width=230,
            height=120,
            corner_radius=0,
            fg_color="#E8F4FD",
        )
        self.test_mode_section.place(**self._test_mode_position)
        self.test_mode_section.place_forget()

        title_label = ctk.CTkLabel(
            self.test_mode_section,
            text="TEST MODE",
            font=("TH Sarabun New", 20, "bold"),
            text_color="#1D3557",
        )
        title_label.place(x=10, y=5)

        self.instant_dispense_button = ctk.CTkButton(
            self.test_mode_section,
            text="จ่ายยาทันที",
            font=("TH Sarabun New", 20, "bold"),
            fg_color="#FF7043",
            hover_color="#F4511E",
            text_color="white",
            corner_radius=8,
            height=50,
            width=110,
            command=self._trigger_test_mode_dispense,
        )
        self.instant_dispense_button.place(x=10, y=40)


        slider_label = ctk.CTkLabel(
            self.test_mode_section,
            text="รอบรับยา",
            font=("TH Sarabun New",20, "bold"),
            text_color="#1D3557",
        )
        slider_label.place(x=130, y=28)

        self.test_mode_value_label = ctk.CTkLabel(
            self.test_mode_section,
            text="0 ครั้ง",
            font=("TH Sarabun New", 20, "bold"),
            text_color="#1D3557",
        )
        self.test_mode_value_label.place(x=130, y=75)

        self.test_mode_slider = ctk.CTkSlider(
            self.test_mode_section,
            from_=1,
            to=6,
            number_of_steps=5,
            command=self._on_test_mode_slider_change,
            width=80,
        )
        self.test_mode_slider.place(x=130, y=50)
        self._sync_test_mode_slider()

    def _trigger_test_mode_dispense(self):
        try:
            request_instant_dispense_command()
            if hasattr(self.controller, "notifier") and self.controller.notifier:
                self.controller.notifier.show_notification(
                    "ส่งคำสั่งจ่ายยาทันที (Test Mode)", success=True
                )
            print("Triggered instant dispense via Test Mode")
        except Exception as e:
            print(f"Error triggering Test Mode dispense: {e}")
            if hasattr(self.controller, "notifier") and self.controller.notifier:
                self.controller.notifier.show_notification(
                    f"ส่งคำสั่ง Test Mode ไม่สำเร็จ: {e}", success=False
                )

    def _on_test_mode_slider_change(self, value):
        threshold = int(round(float(value)))
        set_dont_pick_threshold(threshold)
        self._update_test_mode_slider_label(threshold)

    def _update_test_mode_slider_label(self, threshold):
        if self.test_mode_value_label is not None:
            self.test_mode_value_label.configure(text=f"{threshold} ครั้ง")

    def _sync_test_mode_slider(self):
        if self.test_mode_slider is None:
            return
        current_threshold = get_dont_pick_threshold()
        self.test_mode_slider.set(current_threshold)
        self._update_test_mode_slider_label(current_threshold)

    def update_test_mode_visibility(self):
        if self.test_mode_section is None:
            return
        is_test_account = getattr(self.controller, "is_test_account", False)
        if is_test_account:
            self.test_mode_section.place(**self._test_mode_position)
            self._sync_test_mode_slider()
        else:
            self.test_mode_section.place_forget()

    def reset_and_update(self):
        response = messagebox.askyesno(
            "ยืนยันการรีเซ็ต", 
            "คุณต้องการลบข้อมูลการตั้งเวลาจ่ายยา หรือ ไม่?"
        )
        if response:
                try:
                    set_dispensing_time.delete_time(self.controller.user['id'])
                    self.update_medication_info()
                except Exception as e:
                    print("เกิดข้อผิดพลาด:", e)
    # ฟังก์ชันสำหรับอัพเดทจำนวนยา
    def update_medicine_count(self, new_count=None):
        """อัพเดทจำนวนยาคงเหลือ"""
        # ตรวจสอบว่ามี counter_medicine widget หรือไม่ (อาจไม่มีถ้า role เป็น user)
        if not hasattr(self, 'counter_medicine') or self.counter_medicine is None:
            return  # ไม่ต้องอัพเดทถ้าไม่มี widget
        
        if new_count is not None:
            self.medicine_count = new_count
            # อัพเดทค่าใน controller.user ด้วย
            if hasattr(self.controller, 'user') and self.controller.user:
                self.controller.user['count_medicine'] = self.medicine_count
        
        # ตรวจสอบว่ามี controller และ user หรือไม่
        elif hasattr(self.controller, 'user') and self.controller.user:
            user_count = self.controller.user.get('count_medicine')
            if user_count is not None:
                self.medicine_count = user_count
        
        # อัพเดท UI
        self.counter_medicine.configure(text=str(self.medicine_count))
        
        # เปลี่ยนสีตามจำนวนยา
        if self.medicine_count <= 5:
            self.counter_medicine.configure(text_color="#D32F2F")  # สีแดง - ยาใกล้หมด
        elif self.medicine_count <= 10:
            self.counter_medicine.configure(text_color="#F57C00")  # สีส้ม - ยาเหลือน้อย
        else:
            self.counter_medicine.configure(text_color="#2E7D32")  # สีเขียว - ยาเพียงพอ
        
        print(f"อัพเดทจำนวนยา: {self.medicine_count} เม็ด")

    # ฟังก์ชันลดยา
    def reduce_medicine(self, amount=1):
        current_status = self.controller.network_status_var.get()
        """ลดจำนวนยา"""
        new_count = max(0, self.medicine_count - amount)  # ไม่ให้ต่ำกว่า 0
        set_counter.update_counter(self.controller.user['device_id'],self.controller.user['id'],new_count,current_status)
        self.update_medicine_count(new_count)

        # ตรวจสอบว่ายาหมดรอบหรือไม่ (เหลือ 0)
        if new_count == 0:
            print("Medicine count reached 0. Triggering cycle complete notification.")
            try:
                # 1. ส่งคำสั่ง Reset ไปยังบอร์ด (ถ้าเชื่อมต่ออยู่)
                request_reset_data_command()
                
                # 2. แจ้งเตือน LINE
                if hasattr(self.controller, 'user') and self.controller.user:
                    line_token = self.controller.user.get('token_line')
                    line_group = self.controller.user.get('group_id')
                    
                    if line_token and line_group:
                        current_time = datetime.now().strftime('%H:%M')
                        message = (
                            "🔄 [SeniorCare Pro] แจ้งเตือน : จ่ายยาครบ 28 รอบ\n"
                            "━━━━━━━━━━━━━━━━━━\n\n"
                            "เครื่องได้ทำการรีเซ็ตตำแหน่งเริ่มต้นเรียบร้อยแล้ว\n\n"
                            "กรุณาเติมยาและตรวจสอบความเรียบร้อย"
                        )
                        # ใช้ sendtoLineWithDeduplication ผ่าน thread แยก (หรือเรียกผ่าน alert โดยตรง)
                        # แต่ในที่นี้เราจะใช้ sendtoLineWithDeduplication ที่ import มา
                        sendtoLineWithDeduplication(
                            token=line_token,
                            group_id=line_group,
                            message_data=message,
                            notification_type="cycle_complete",
                            identifier=f"cycle_reset_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        )
            except Exception as e:
                print(f"Error handling cycle complete: {e}")

    # ฟังก์ชันรีเซ็ตยา
    def reset_medicine_count(self):
        """รีเซ็ตจำนวนยากลับไปเป็นค่าเริ่มต้น"""
        # ใช้ messagebox เพื่อยืนยันการรีเซ็ต
        response = messagebox.askyesno(
            "ยืนยันการรีเซ็ต", 
            "คุณต้องการรีเซ็ตจำนวนยาเป็น 28 เม็ดหรือไม่?"
        )
        
        if response:
            initial_count = 28
            current_status = self.controller.network_status_var.get()
            set_counter.update_counter(self.controller.user['device_id'],self.controller.user['id'],initial_count,current_status)
            self.update_medicine_count(initial_count)
            try:
                request_reset_data_command()
                print("Triggered reset_data due to manual UI reset")
            except Exception as e:
                print(f"Warning: unable to trigger reset_data after manual reset: {e}")
            
            # แสดงข้อความยืนยัน
            messagebox.showinfo("สำเร็จ", f"รีเซ็ตจำนวนยาเป็น {initial_count} เม็ดเรียบร้อยแล้ว")
            print(f"รีเซ็ตจำนวนยาเป็น: {initial_count} เม็ด")

    def update_user_info(self):
        try:
            # ตรวจสอบว่ามี user_info_content หรือไม่ (อาจไม่มีถ้า role เป็น user)
            if not hasattr(self, 'user_info_content') or self.user_info_content is None:
                return  # ไม่ต้องอัพเดทถ้าไม่มี widget
            
            # ป้องกันการอัพเดทซ้ำถ้ากำลังโหลดอยู่
            if hasattr(self, '_updating_user_info') and self._updating_user_info:
                return
            
            self._updating_user_info = True
            print("กำลังอัพเดทข้อมูลผู้ใช้...")
            
            # ลบข้อมูลเก่า
            if hasattr(self, 'user_info_labels'):
                for label in self.user_info_labels:
                    try:
                        label.destroy()
                    except:
                        pass
                self.user_info_labels.clear()
            else:
                self.user_info_labels = []

            # แสดงข้อมูลผู้ใช้
            if hasattr(self.controller, 'user') and self.controller.user:
                user = self.controller.user
                print(f"พบข้อมูลผู้ใช้: {user.get('firstname_th', '')} {user.get('lastname_th', '')}")
                
                # ตรวจสอบ role เพื่อปรับขนาด
                user_role = None
                if hasattr(self.controller, 'user') and self.controller.user:
                    user_role = self.controller.user.get('urole', '').lower()
                is_patient_mode = (user_role == 'patient')
                is_user_mode = (user_role == 'user')
                is_admin_mode = (user_role == 'admin')
                
                # ข้อมูลพื้นฐาน
                patient_name = f"ผู้ป่วย: {user.get('firstname_th', '')} {user.get('lastname_th', '')}"
                phone = f"โทรศัพท์: {user.get('phone', '')}"
                disease = f"โรค: {user.get('chronic_disease', '')}" if user.get('chronic_disease') else None
                caretaker = f"ผู้ดูแล: {user.get('caretaker_name', '')}" if user.get('caretaker_name') else None

                # ปรับขนาดตาม role
                card_height = 50 if is_patient_mode else (42 if is_user_mode else (40 if is_admin_mode else 35))
                info_font_size = 26 if is_patient_mode else (22 if is_user_mode else (20 if is_admin_mode else 16))
                card_pady = 5 if is_patient_mode else (4 if is_user_mode else (3.5 if is_admin_mode else 3))

                # สำหรับ patient mode: แสดงเป็น 2 คอลัมน์
                if is_patient_mode:
                    # สร้าง container สำหรับ 2 คอลัมน์
                    row_frame = ctk.CTkFrame(
                        self.user_info_content,
                        fg_color="transparent"
                    )
                    row_frame.pack(pady=card_pady, padx=5, fill="x")
                    
                    # คอลัมน์แรก (ครึ่งซ้าย): ผู้ป่วย, โทรศัพท์
                    left_column = ctk.CTkFrame(
                        row_frame,
                        fg_color="transparent"
                    )
                    left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
                    
                    # ผู้ป่วย
                    patient_card = ctk.CTkFrame(
                        left_column,
                        height=card_height,
                        corner_radius=8,
                        fg_color="#E8F4FD"
                    )
                    patient_card.pack(pady=(0, card_pady), padx=0, fill="x")
                    patient_label = ctk.CTkLabel(
                        patient_card,
                        text=patient_name,
                        font=("TH Sarabun New", info_font_size, "bold"),
                        text_color="#000000",
                        fg_color="transparent",
                        justify="left",
                        anchor="w"
                    )
                    patient_label.pack(pady=10, padx=15, fill="x", anchor="w")
                    self.user_info_labels.extend([patient_card, patient_label])
                    
                    # โทรศัพท์
                    phone_card = ctk.CTkFrame(
                        left_column,
                        height=card_height,
                        corner_radius=8,
                        fg_color="#FFF2E8"
                    )
                    phone_card.pack(pady=0, padx=0, fill="x")
                    phone_label = ctk.CTkLabel(
                        phone_card,
                        text=phone,
                        font=("TH Sarabun New", info_font_size, "bold"),
                        text_color="#000000",
                        fg_color="transparent",
                        justify="left",
                        anchor="w"
                    )
                    phone_label.pack(pady=10, padx=15, fill="x", anchor="w")
                    self.user_info_labels.extend([phone_card, phone_label, row_frame, left_column])
                    
                    # คอลัมน์ที่สอง (ครึ่งขวา): โรค, ผู้ดูแล
                    right_column = ctk.CTkFrame(
                        row_frame,
                        fg_color="transparent"
                    )
                    right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))
                    
                    # โรค
                    if disease:
                        disease_card = ctk.CTkFrame(
                            right_column,
                            height=card_height,
                            corner_radius=8,
                            fg_color="#E8F4FD"
                        )
                        disease_card.pack(pady=(0, card_pady), padx=0, fill="x")
                        disease_label = ctk.CTkLabel(
                            disease_card,
                            text=disease,
                            font=("TH Sarabun New", info_font_size, "bold"),
                            text_color="#000000",
                            fg_color="transparent",
                            justify="left",
                            anchor="w"
                        )
                        disease_label.pack(pady=10, padx=15, fill="x", anchor="w")
                        self.user_info_labels.extend([disease_card, disease_label])
                    
                    # ผู้ดูแล
                    if caretaker:
                        caretaker_card = ctk.CTkFrame(
                            right_column,
                            height=card_height,
                            corner_radius=8,
                            fg_color="#FFF2E8"
                        )
                        caretaker_card.pack(pady=0, padx=0, fill="x")
                        caretaker_label = ctk.CTkLabel(
                            caretaker_card,
                            text=caretaker,
                            font=("TH Sarabun New", info_font_size, "bold"),
                            text_color="#000000",
                            fg_color="transparent",
                            justify="left",
                            anchor="w"
                        )
                        caretaker_label.pack(pady=10, padx=15, fill="x", anchor="w")
                        self.user_info_labels.extend([caretaker_card, caretaker_label, right_column])
                else:
                    # สำหรับ non-patient mode: แสดงแบบเดิม (เรียงต่อกัน)
                    user_info = []
                    user_info.append(patient_name)
                    user_info.append(phone)
                    if disease:
                        user_info.append(disease)
                    if caretaker:
                        user_info.append(caretaker)
                    
                    for i, info in enumerate(user_info):
                        info_card = ctk.CTkFrame(
                            self.user_info_content,
                            height=card_height,
                            corner_radius=8,
                            fg_color="#E8F4FD" if i % 2 == 0 else "#FFF2E8"
                        )
                        info_card.pack(pady=card_pady, padx=5, fill="x")
                        
                        info_label = ctk.CTkLabel(
                            info_card,
                            text=info,
                            font=("TH Sarabun New", info_font_size, "bold"),
                            text_color="#000000",
                            fg_color="transparent",
                            justify="left",
                            anchor="w"
                        )
                        info_label.pack(pady=6, padx=10, fill="x", anchor="w")
                        
                        self.user_info_labels.append(info_card)
                        self.user_info_labels.append(info_label)
                    
                # อัพเดทจำนวนยาด้วย
                self.update_medicine_count()
                    
            else:
                print("ไม่พบข้อมูลผู้ใช้")
                # ตรวจสอบ role เพื่อปรับขนาด
                user_role = None
                if hasattr(self.controller, 'user') and self.controller.user:
                    user_role = self.controller.user.get('urole', '').lower()
                is_patient_mode = (user_role == 'patient')
                
                # ปรับขนาดตาม role
                card_height = 90 if is_patient_mode else 80
                font_size = 22 if is_patient_mode else 18
                
                # แสดงข้อความเมื่อไม่มีข้อมูลผู้ใช้
                no_user_card = ctk.CTkFrame(
                    self.user_info_content,
                    height=card_height,
                    corner_radius=10,
                    fg_color="#FFF3CD",
                    border_width=1,
                    border_color="#FFE69C"
                )
                no_user_card.pack(pady=30, padx=10, fill="x")
                
                warning_label = ctk.CTkLabel(
                    no_user_card,
                    text="⚠️ ไม่พบข้อมูลผู้ใช้",
                    font=("TH Sarabun New", font_size, "bold"),
                    text_color="#856404",
                    fg_color="transparent"
                )
                warning_label.pack(pady=20)
                
                self.user_info_labels.extend([no_user_card, warning_label])
                
            print("อัพเดทข้อมูลผู้ใช้เสร็จสิ้น")
            self._updating_user_info = False
            self.update_test_mode_visibility()
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอัพเดทข้อมูลผู้ใช้: {e}")
            self._updating_user_info = False


    def show_medication_loading(self):
        """(ฟังก์ชันใหม่) แสดงสถานะกำลังโหลดในกรอบข้อมูลยา"""
        try:
            # ป้องกันการอัพเดทซ้ำถ้ากำลังโหลดอยู่
            if hasattr(self, '_updating_medication_info') and self._updating_medication_info:
                return
            
            self._updating_medication_info = True
            # ลบข้อมูลเก่า
            for label in self.medication_labels:
                try:
                    label.destroy()
                except:
                    pass
            self.medication_labels.clear()

            # ตรวจสอบ role เพื่อปรับขนาด
            user_role = None
            if hasattr(self.controller, 'user') and self.controller.user:
                user_role = self.controller.user.get('urole', '').lower()
            is_patient_mode = (user_role == 'patient')
            is_user_mode = (user_role == 'user')
            is_admin_mode = (user_role == 'admin')
            
            # ปรับขนาดตาม role
            card_height = 100 if is_patient_mode else (90 if is_user_mode else (85 if is_admin_mode else 80))
            font_size = 28 if is_patient_mode else (24 if is_user_mode else (23 if is_admin_mode else 18))
            
            # แสดงการ์ด "กำลังโหลด"
            loading_card = ctk.CTkFrame(
                self.medication_list_frame,
                height=card_height, corner_radius=10, fg_color="#FFF3CD",
                border_width=1, border_color="#FFE69C"
            )
            loading_card.pack(pady=30, padx=10, fill="x")
            
            loading_label = ctk.CTkLabel(
                loading_card, text="🔄 กำลังโหลดข้อมูลการตั้งค่ายา...",
                font=("TH Sarabun New", font_size, "bold"), text_color="#856404",
                fg_color="transparent"
            )
            loading_label.pack(pady=(25 if is_patient_mode else 20))
            
            self.medication_labels.extend([loading_card, loading_label])
        except Exception as e:
            print(f"Error in show_medication_loading: {e}")

    def update_medication_info(self):
      
        try:
            # 1. แสดง "กำลังโหลด..." บน UI ทันที
            self.show_medication_loading()
            
            # 2. สร้างและเริ่ม Thread ใหม่ให้ไปทำงานเบื้องหลัง
            threading.Thread(
                target=self._fetch_medication_data_in_background, 
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการเริ่ม update_medication_info: {e}")
            self.show_medication_error() # (ใช้ฟังก์ชันเดิมของคุณ)

    def _fetch_medication_data_in_background(self):
        
        CACHE_FILE = "time_data.json" # ⭐️ ชื่อไฟล์แคช
        meal_data = None
        error_message = None
        data_source = "" # สำหรับ Log

        try:
            # 0. ตรวจสอบว่าล็อกอินหรือยัง (สำคัญมาก)
            if not (hasattr(self.controller, 'user') and self.controller.user):
                print("Background Thread: ไม่พบข้อมูลผู้ใช้")
                self.after(0, self._render_medication_data, None, "No user data")
                return

            # ⭐️ [FIX] 1. "พยายาม" ดึงข้อมูลจากเซิร์ฟเวอร์ก่อนเสมอ ⭐️
            # (เราจะไม่ตรวจสอบ network_status_var ที่นี่แล้ว)
            print("Background Thread (HomePage): กำลังพยายามดึงข้อมูลจากเซิร์ฟเวอร์...")
            meal_api_result = set_dispensing_time.get_meal( 
                self.controller.user['device_id'],
                self.controller.user['id']
            )
            
            # --- 2. ถ้าดึงข้อมูลสำเร็จ (ONLINE) ---
            if meal_api_result and 'data' in meal_api_result:
                meal_data = meal_api_result # นี่คือโครงสร้าง {'data': [...]}
                data_to_cache = meal_api_result['data'] # นี่คือข้อมูล [...] ที่จะบันทึก
                data_source = "Server (Online)"
                
                # --- 2b. บันทึกข้อมูลใหม่ลงไฟล์แคช (time_data.json) ---
                try:
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data_to_cache, f, indent=4)
                    print(f"Background Thread (HomePage): บันทึกข้อมูลใหม่ลง {CACHE_FILE} สำเร็จ")
                except Exception as e:
                    print(f"Background Thread (HomePage): ไม่สามารถเขียนไฟล์แคช: {e}")
                        
            else:
                # เซิร์ฟเวอร์ตอบกลับมาแต่ข้อมูลผิดพลาด (เช่น 'status': false)
                print("Background Thread (HomePage): เซิร์ฟเวอร์ตอบกลับข้อมูลไม่ถูกต้อง")
                error_message = "ข้อมูลจากเซิร์ฟเวอร์ไม่ถูกต้อง" # จะไปบังคับให้โหลดแคชแทน

        except requests.exceptions.RequestException as e:
            # --- 3. ถ้าดึงข้อมูล "ล้มเหลว" (OFFLINE หรือ Server ล่ม) ---
            # (นี่คือจุดที่ดักจับ Error 'getaddrinfo failed' ที่คุณเห็น)
            print(f"Background Thread (HomePage): เกิดข้อผิดพลาด Network (Offline): {e}")
            error_message = str(e) # บังคับให้ไปโหลดแคช
            
        except Exception as e:
            # --- 4. ERROR อื่นๆ (เช่น โค้ดผิด) ---
            print(f"Background Thread (HomePage): เกิดข้อผิดพลาดร้ายแรง: {e}")
            self.after(0, self._render_medication_data, None, str(e))
            return

        # --- 5. สรุปผลและแสดงผล ---
        
        if meal_data:
            # --- A: ถ้าดึงข้อมูล Online สำเร็จ ---
            print(f"Background Thread (HomePage): ดึงข้อมูลสำเร็จจาก {data_source} กำลังแสดงผล...")
            if 'data' in meal_data:
                 recivetime(meal_data['data']) 
            self.after(0, self._render_medication_data, meal_data, None)
        
        elif error_message:
            # --- B: ถ้า Offline หรือ Online แต่ดึงล้มเหลว -> ให้โหลดจากแคช ---
            print(f"Background Thread (HomePage): ดึงข้อมูลล้มเหลว ({error_message}). กำลังโหลดจากแคช {CACHE_FILE}...")
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        cached_data_list = json.load(f) 
                    
                    # ⭐️ ห่อข้อมูลกลับในรูปแบบที่ _render_medication_data คาดหวัง
                    meal_data = {'data': cached_data_list} 
                    
                    print("Background Thread (HomePage): โหลดแคชสำเร็จ กำลังแสดงผล...")
                    if 'data' in meal_data: # ตรวจสอบอีกครั้งเพื่อความปลอดภัย
                        recivetime(meal_data['data']) 
                    self.after(0, self._render_medication_data, meal_data, None) # ส่งข้อมูลจากแคชไปแสดงผล
                except Exception as e:
                    print(f"Background Thread (HomePage): ไม่สามารถอ่านไฟล์แคช: {e}")
                    self.after(0, self._render_medication_data, None, f"Offline และอ่านไฟล์แคชไม่ได้: {e}")
            else:
                self.after(0, self._render_medication_data, None, "Offline และไม่พบข้อมูลที่บันทึกไว้")
    def _render_medication_data(self, meal_data, error_message):

        # print("Main Thread: กำลังอัปเดต UI ด้วยข้อมูลยา...")
        try:
            # 1. ลบ "กำลังโหลด..." หรือข้อมูลเก่าทิ้ง
            for label in self.medication_labels:
                label.destroy()
            self.medication_labels.clear()

            # 2. ตรวจสอบว่ามี Error มาจาก Thread หรือไม่
            if error_message:
                print(f"Error rendering data: {error_message}")
                self.show_medication_error() # (ใช้ฟังก์ชันเดิมของคุณ)
                return

            # --- (โค้ดส่วนที่เหลือคือโค้ด "วาด UI" เดิมของคุณทั้งหมด) ---
            
            # 3. แสดงข้อมูลวันที่เริ่มและสิ้นสุด
            # ตรวจสอบ role เพื่อปรับขนาด
            user_role = None
            if hasattr(self.controller, 'user') and self.controller.user:
                user_role = self.controller.user.get('urole', '').lower()
            is_patient_mode = (user_role == 'patient')
            is_user_mode = (user_role == 'user')
            is_admin_mode = (user_role == 'admin')
            
            # ดึงค่าความกว้างของ medication_frame จาก layout
            theme = get_role_theme(user_role)
            layout = theme.get('layout', {})
            med_layout = layout.get('medication_frame', {})
            med_width = med_layout.get('width', 340)
            
            if hasattr(self.controller, 'user') and self.controller.user:
                start_date = self.controller.user.get('startDate', '')
                end_date = self.controller.user.get('endDate', '')
                
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                        
                        start_str = start_dt.strftime("%d/%m/%Y")
                        end_str = end_dt.strftime("%d/%m/%Y")
                        
                        date_info = f"ระยะเวลา: {start_str} - {end_str}"
                        
                        # ปรับขนาดตาม role
                        date_card_height = 50 if is_patient_mode else (45 if is_user_mode else (43 if is_admin_mode else 40))
                        date_font_size = 24 if is_patient_mode else (22 if is_user_mode else (21 if is_admin_mode else 18))
                        
                        date_card = ctk.CTkFrame(
                            self.medication_list_frame,
                            height=date_card_height, corner_radius=8, fg_color="#D4EDDA",
                            border_width=1, border_color="#C3E6CB"
                        )
                        date_card.pack(pady=2, padx=5, fill="x")
                        
                        date_label = ctk.CTkLabel(
                            date_card, text=date_info,
                            font=("TH Sarabun New", date_font_size, "bold"), text_color="#155724",
                            fg_color="transparent"
                        )
                        date_label.place(x=15, y=12 if is_patient_mode else 8)
                        
                        self.medication_labels.extend([date_card, date_label])
                    except Exception as e_date:
                        print(f"Error formatting date: {e_date}")
                        pass # (ถ้า format วันที่ผิด ก็แค่ข้ามไป)

            # 4. แสดงข้อมูลยา (ที่ได้มาจาก meal_data)
            if meal_data and 'data' in meal_data:
                medications = meal_data['data']
                # recivetime(medications)  <--- (ย้ายไป Thread เบื้องหลังแล้ว)
                
                if medications:
                    # แสดงข้อมูลยาในรูปแบบการ์ด
                    for i, med in enumerate(medications):
                        meal_names = {
                            'bb': ' ก่อนนอน', 'bf': ' เช้า',
                            'lunch': ' กลางวัน', 'dn': ' เย็น'
                        }
                        meal_name = meal_names.get(med.get('source', ''), med.get('source', ''))
                        time_str = med.get('time', '')
                        
                        med_count = 0
                        med_names = []
                        for j in range(1, 5):
                            med_name_item = med.get(f'medicine_{j}', '')
                            if med_name_item:
                                med_count += 1
                                med_names.append(med_name_item)
                        
                        if med_count > 0:
                            # ตรวจสอบ role เพื่อปรับขนาดการ์ดและฟอนต์
                            user_role = None
                            if hasattr(self.controller, 'user') and self.controller.user:
                                user_role = self.controller.user.get('urole', '').lower()
                            is_patient_mode = (user_role == 'patient')
                            is_user_mode = (user_role == 'user')
                            is_admin_mode = (user_role == 'admin')
                            
                            # ปรับขนาดการ์ดและฟอนต์ตาม role
                            card_height = 85 if is_patient_mode else (70 if is_user_mode else (65 if is_admin_mode else 60))
                            time_font_size = 28 if is_patient_mode else (24 if is_user_mode else (23 if is_admin_mode else 20))
                            count_font_size = 26 if is_patient_mode else (22 if is_user_mode else (21 if is_admin_mode else 20))
                            status_font_size = 26 if is_patient_mode else (22 if is_user_mode else (21 if is_admin_mode else 20))
                            
                            # สร้างการ์ดยา
                            med_card = ctk.CTkFrame(
                                self.medication_list_frame, height=card_height, corner_radius=10,
                                fg_color="#E8F6EF", border_width=2, border_color="#7EBCA2"
                            )
                            med_card.pack(pady=4, padx=5, fill="x")
                            
                            time_label = ctk.CTkLabel(
                                med_card, text=f"{meal_name} - {time_str}",
                                font=("TH Sarabun New", time_font_size, "bold"), text_color="#2D6A4F",
                                fg_color="transparent"
                            )
                            time_label.place(x=15, y=10 if is_patient_mode else 8)
                            
                            count_label = ctk.CTkLabel(
                                med_card, text=f" {med_count} รายการ",
                                font=("TH Sarabun New", count_font_size), text_color="#495057",
                                fg_color="transparent"
                            )
                            count_label.place(x=15, y=42 if is_patient_mode else 35)

                            status_label = ctk.CTkLabel(
                                med_card, text=" พร้อมใช้",
                                font=("TH Sarabun New", status_font_size, "bold"), text_color="#FF0000",
                                fg_color="transparent"
                            )
                            # ปรับตำแหน่ง status label ให้เหมาะสมกับความกว้างของ frame
                            if is_patient_mode:
                                # สำหรับ patient mode ที่ frame กว้าง 600px (จาก layout)
                                status_x = 600 - 150  # ใช้ความกว้างของ frame จาก layout
                            else:
                                status_x = 200
                            status_label.place(x=status_x, y=42 if is_patient_mode else 35)
                            
                            self.medication_labels.extend([med_card, time_label, count_label, status_label])
                else:
                    self.show_no_medication_message()
            else:
                self.show_no_medication_message()
                
        except Exception as e_render:
            print(f"เกิดข้อผิดพลาดในการ *แสดงผล* ข้อมูลยา: {e_render}")
            self.show_medication_error()

                            
    def _get_board_time(self):
        """
        พยายามดึงเวลาจากบอร์ด (Raspberry Pi/External Board)
        หากไม่สำเร็จจะคืนค่า None เพื่อให้ระบบใช้เวลาจาก System Time แทน
        """
        try:
            # TODO: ใส่ Logic การดึงเวลาจาก Serial/RTC ของบอร์ดที่นี่ในอนาคต
            # ตอนนี้ให้ถือว่าดึงไม่ได้ (Return None) เพื่อให้ Fallback ไปใช้ System Time (datetime.now())
            # ซึ่งบน Raspberry Pi เวลา System Time ก็ควรจะเป็นเวลาที่ถูกต้องอยู่แล้ว
            return None 
        except Exception as e:
            print(f"Error fetching board time: {e}")
            return None

    def update_datetime(self):
        """อัพเดทวันที่และเวลาพร้อมเอฟเฟ็กต์ (Robust Version)"""
        try:
            # 1. พยายามดึงเวลาจากบอร์ดก่อน
            current_dt = self._get_board_time()
            
            # 2. ถ้าดึงไม่ได้ ให้ใช้เวลาจาก System (เครื่อง)
            if current_dt is None:
                current_dt = datetime.now()
                
            # *หมายเหตุ: บน Raspberry Pi, datetime.now() คือเวลาของบอร์ดอยู่แล้ว
            
            # จัดรูปแบบวันที่ให้สั้นและเข้าใจง่าย
            thai_months = [
                "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
            ]
            
            thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
            
            day_name = thai_days[current_dt.weekday()]
            day = current_dt.day
            month = thai_months[current_dt.month]
            year = current_dt.year + 543  # แปลงเป็น พ.ศ.
            
            date_text = f"{day_name} {day} {month} {year}"
            if self.date_label.cget("text") != date_text:
                 self.date_label.configure(text=date_text)

            # จัดรูปแบบเวลาพร้อมวินาที
            current_time_str = current_dt.strftime("%H:%M:%S")
            self.time_label.configure(text=current_time_str)
            
            # เปลี่ยนสีของเวลาตามช่วงเวลา
            hour = current_dt.hour
            if 6 <= hour < 12:
                time_color = "#DC0000"  # สีส้ม (เช้า)
            elif 12 <= hour < 18:
                time_color = "#F4B342"  # สีเหลือง (บ่าย)
            elif 18 <= hour < 22:
                time_color = "#C47BE4"  # สีม่วง (เย็น)
            else:
                time_color = "#301CA0"  # สีเข้ม (กลางคืน)
                
            self.time_label.configure(text_color=time_color)
            
            # อัพเดทสถานะระบบ (Safe call)
            self.update_system_status()
            
            # เช็ค Network แบบ Non-blocking
            self.check_network_and_update_buttons()
            
        except Exception as e:
            print(f"Error in update_datetime: {e}")
            
        finally:
            # สำคัญ: เรียกตัวเองซ้ำเสมอ ไม่ว่าจะเกิด error หรือไม่
            # เพื่อป้องกันนาฬิกาหยุดเดิน
            try:
                if self.winfo_exists():
                    self.after(1000, self.update_datetime)
            except:
                pass

    def update_system_status(self):
        """อัพเดทสถานะระบบ"""
        try:
            # เช็คสถานะการเชื่อมต่อ (จำลอง)
            import random
            connection_status = random.choice([True, True, True, False])  # 75% โอกาสเชื่อมต่อได้
            
            if connection_status:
                status_text = "🟢 ระบบพร้อมใช้งาน"
                status_color = "#2ECC71"
            else:
                status_text = "🟡 ตรวจสอบการเชื่อมต่อ"
                status_color = "#F39C12"
                
            if hasattr(self, 'system_status'):
                self.system_status.configure(text=status_text, text_color=status_color)
        except:
            pass

    def show_no_medication_message(self):
        """แสดงข้อความเมื่อไม่มีข้อมูลยา"""
        # ตรวจสอบ role เพื่อปรับขนาด
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        is_patient_mode = (user_role == 'patient')
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        
        # ปรับขนาดตาม role
        card_height = 100 if is_patient_mode else (90 if is_user_mode else (85 if is_admin_mode else 80))
        font_size = 28 if is_patient_mode else (24 if is_user_mode else (23 if is_admin_mode else 18))
        
        no_med_card = ctk.CTkFrame(
            self.medication_list_frame,
            height=card_height,
            corner_radius=10,
            fg_color="#FFF3CD",
            border_width=1,
            border_color="#FFE69C"
        )
        no_med_card.pack(pady=30, padx=10, fill="x")
        
        warning_label = ctk.CTkLabel(
            no_med_card,
            text="⚠️ ไม่พบข้อมูลการตั้งค่ายา",
            font=("TH Sarabun New", font_size, "bold"),
            text_color="#856404",
            fg_color="transparent"
        )
        warning_label.pack(pady=(25 if is_patient_mode else 20))
        
        self.medication_labels.extend([no_med_card, warning_label])

    def show_medication_error(self):
        """แสดงข้อความผิดพลาดเมื่อโหลดข้อมูลยาไม่สำเร็จ"""
        # ตรวจสอบ role เพื่อปรับขนาด
        user_role = None
        if hasattr(self.controller, 'user') and self.controller.user:
            user_role = self.controller.user.get('urole', '').lower()
        is_patient_mode = (user_role == 'patient')
        is_user_mode = (user_role == 'user')
        is_admin_mode = (user_role == 'admin')
        
        # ปรับขนาดตาม role
        card_height = 100 if is_patient_mode else (90 if is_user_mode else (85 if is_admin_mode else 80))
        font_size = 28 if is_patient_mode else (24 if is_user_mode else (23 if is_admin_mode else 16))
        
        error_card = ctk.CTkFrame(
            self.medication_list_frame,
            height=card_height,
            corner_radius=10,
            fg_color="#F8D7DA",
            border_width=1,
            border_color="#F5C6CB"
        )
        error_card.pack(pady=30, padx=10, fill="x")
        
        error_label = ctk.CTkLabel(
            error_card,
            text="❌ เกิดข้อผิดพลาดในการโหลดข้อมูลยา",
            font=("TH Sarabun New", font_size, "bold"),
            text_color="#721C24",
            fg_color="transparent"
        )
        error_label.pack(pady=(25 if is_patient_mode else 20))
        
        self.medication_labels.extend([error_card, error_label])
    def check_network_and_update_buttons(self):
        current_status = "online" # ค่าเริ่มต้น
        try:
            current_status = self.controller.network_status_var.get()
            

        except AttributeError:
            
            try:
                current_status = self.controller.network_status
            except AttributeError:     
                return 
        except Exception as e:
            # print(f"Error reading network status: {e}")
            return
        print(current_status)
        should_update = True
        if current_status == self._last_checked_network_status:
            # ถ้าสถานะเดิม แต่ปุ่มอาจถูก reset ไปแล้ว ให้อัปเดตใหม่
            should_update = True
        
        if should_update:
            self._last_checked_network_status = current_status

            if current_status == "offline":
                print("HomePage: Network is OFFLINE, disabling buttons.")
                # รายชื่อปุ่มที่อนุญาตให้ใช้ตอน Offline
                allowed_buttons = ["ตั้งเวลา", "ออกระบบ", "ปิดเครื่อง"]
                
                for i, btn in self.menu_buttons.items():
                    try:
                        btn_text = btn.cget("text")
                        if btn_text in allowed_buttons:
                            # เปิดใช้งานปุ่มที่อนุญาต
                            if i in self.button_original_styles:
                                style = self.button_original_styles[i]
                                btn.configure(
                                    state="normal",
                                    fg_color=style['fg_color'],
                                    hover_color=style['hover_color'],
                                    text_color=style['text_color'],
                                    border_color=style['border_color']
                                )
                        else:
                            # ปิดใช้งานปุ่มอื่นๆ
                            btn.configure(
                                state="disabled",
                                fg_color="#E0E0E0",
                                hover_color="#E0E0E0",
                                text_color="#9E9E9E",
                                border_color="#BDBDBD"
                            )
                    except Exception as e:
                        print(f"Error updating button {i}: {e}")
                # อัปเดตปุ่ม SOS ให้เป็นสีเทาและเปลี่ยนรูปเป็นออฟไลน์
                if hasattr(self, 'call_button') and self.call_button:
                    self.call_button.configure(
                        state="disabled",
                        image=self.call_photo_offline,  # เปลี่ยนรูปเป็นออฟไลน์
                        fg_color="#B0B0B0",  # สีเทาอ่อน
                        hover_color="#B0B0B0",  # สีเทาอ่อน
                        border_color="#9E9E9E",  # เส้นขอบเทา
                        bg_color="#8acaef"  # เก็บ bg_color เดิม
                    )
                
                # อัปเดตปุ่มรีเฟรชและรีเซ็ตให้เป็นสีเทาและกดไม่ได้
                if hasattr(self, 'setting_button') and self.setting_button:
                    # คืนค่าสไตล์เดิมถ้ามี
                    if hasattr(self, 'setting_button_original_style'):
                        style = self.setting_button_original_style
                        self.setting_button.configure(
                            state="normal",
                            fg_color=style['fg_color'],
                            hover_color=style['hover_color'],
                            text_color=style['text_color']
                        )
                    else:
                        self.setting_button.configure(state="normal")
                
                if hasattr(self, 'refresh_button') and self.refresh_button:
                    if hasattr(self, 'refresh_button_original_style'):
                        style = self.refresh_button_original_style
                        self.refresh_button.configure(
                            state="normal",
                            fg_color=style['fg_color'],
                            hover_color=style['hover_color'],
                            text_color=style['text_color']
                        )
                    else:
                        self.refresh_button.configure(state="normal")
                
                if hasattr(self, 'reset_counter_button') and self.reset_counter_button:
                    if hasattr(self, 'reset_counter_button_original_style'):
                        style = self.reset_counter_button_original_style
                        self.reset_counter_button.configure(
                            state="normal",
                            fg_color=style['fg_color'],
                            hover_color=style['hover_color'],
                            text_color=style['text_color']
                        )
                    else:
                        self.reset_counter_button.configure(state="normal")
            else:
                # --- เน็ตออนไลน์: คืนค่าปุ่มเป็นปกติ ---
                print("HomePage: Network is ONLINE, enabling buttons.")
                for i, btn in self.menu_buttons.items():
                    if i in self.button_original_styles:
                        style = self.button_original_styles[i]
                        btn.configure(
                            state="normal",
                            fg_color=style['fg_color'],
                            hover_color=style['hover_color'],
                            text_color=style['text_color'],
                            border_color=style['border_color']
                        )
                # คืนค่าปุ่ม SOS เป็นสไตล์เดิมและเปลี่ยนรูปกลับเป็นออนไลน์
                if hasattr(self, 'call_button') and self.call_button and self.call_button_original_style:
                    style = self.call_button_original_style
                    self.call_button.configure(
                        state=style['state'],
                        image=self.call_photo_online,  # เปลี่ยนรูปกลับเป็นออนไลน์
                        fg_color=style['fg_color'],
                        hover_color=style['hover_color'],
                        bg_color=style['bg_color'],
                        border_color=style['border_color'],
                        border_width=style['border_width'],
                        corner_radius=style.get('corner_radius', 0)
                    )
                
                # คืนค่าปุ่มรีเฟรชและรีเซ็ตเป็นสไตล์เดิม
                if hasattr(self, 'setting_button') and self.setting_button and hasattr(self, 'setting_button_original_style'):
                    style = self.setting_button_original_style
                    self.setting_button.configure(
                        state=style['state'],
                        fg_color=style['fg_color'],
                        hover_color=style['hover_color'],
                        text_color=style['text_color']
                    )
                
                if hasattr(self, 'refresh_button') and self.refresh_button and hasattr(self, 'refresh_button_original_style'):
                    style = self.refresh_button_original_style
                    self.refresh_button.configure(
                        state=style['state'],
                        fg_color=style['fg_color'],
                        hover_color=style['hover_color'],
                        text_color=style['text_color']
                    )
                
                if hasattr(self, 'reset_counter_button') and self.reset_counter_button and hasattr(self, 'reset_counter_button_original_style'):
                    style = self.reset_counter_button_original_style
                    self.reset_counter_button.configure(
                        state=style['state'],
                        fg_color=style['fg_color'],
                        hover_color=style['hover_color'],
                        text_color=style['text_color']
                    )

    def on_video_call_click(self):
        # ตรวจสอบว่าปุ่มถูกกดไปแล้วหรือไม่
        if self.sos_button_clicked:
            print("SOS button already clicked, ignoring duplicate click")
            return
        
        if self.controller.network_status_var.get() == "offline":
             return 

        # ป้องกันการกดซ้ำ - ตั้งค่าสถานะและเปลี่ยนรูปเป็น sos-ค้าง.png
        self.sos_button_clicked = True
        
        # เปลี่ยนรูปปุ่มเป็น sos-ค้าง.png และปิดการใช้งาน
        self.call_button.configure(
            image=self.call_photo_clicked,
            state="disabled",
            fg_color="#2ECC71"  # เปลี่ยนเป็นสีเขียวเมื่อกด
        )

        try:
            token = self.controller.user['token_line']
            group_id = self.controller.user['group_id']

           
            if not token or not group_id:
                print("Call Error: Missing Token or Group ID")
                self.controller.notifier.show_notification("ยังไม่ได้ตั้งค่า LINE Notify", success=False)
                return
                
            # 4. แสดง Loading (ถูกต้อง)
            self.controller.show_loading("กำลังเริ่มวิดีโอคอล...", "กรุณารอสักครู่")

            def call_thread():
                try:
                    send_status = press_sos_automation(token, group_id)
                    if send_status: 
                        self.controller.after(0, lambda: self.controller.notifier.show_notification("ส่งคำขอวิดีโอคอลแล้ว", success=True))
                    else:
                        self.controller.after(0, lambda: self.controller.notifier.show_notification("ส่งคำขอ LINE ล้มเหลว", success=False))
                except Exception as e:
                    print(f"Failed to run SOS automation thread: {e}")
                    self.controller.after(0, lambda: self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False))
                finally:
                    # ซ่อน loading screen
                    self.controller.after(0, self.controller.hide_loading)
                    # รีเซ็ตปุ่ม SOS หลังจากโทรเสร็จแล้ว (เมื่อปิด browser)
                    self.controller.after(0, self.reset_sos_button)
            

            threading.Thread(target=call_thread, daemon=True).start()
        
        except KeyError:
            print("Call Error: 'user', 'token_line', or 'group_id' not found in controller.")
            self.controller.notifier.show_notification("เกิดข้อผิดพลาด: ไม่พบข้อมูลผู้ใช้", success=False)
            self.controller.hide_loading() 
            
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
            self.controller.hide_loading() 

# Other frames moved to their respective view files
        page_title.pack(side="left", padx=20)
        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )

        back_button = ctk.CTkButton(
            navbar,
           image=self.reply_ctk_image,   # ใช้ image แทน text
            text="ย้อนกลับ",                      # ไม่ใส่ข้อความ
            width=100, 
            height=50, 
            corner_radius=25,
            fg_color="#2563EB", 
            hover_color="#1D3557", 
            text_color="white",
            font=("Arial", 24, "bold"), 
            command=lambda: controller.show_frame(HomePage)
        )
        back_button.pack(side="right", padx=10, pady=5)

        add_button = ctk.CTkButton(
            navbar,
            text="เพิ่มข้อมูล",
            width=120,
            height=50,
            corner_radius=20,
            fg_color="#2563EB",
            hover_color="#05C766",
            text_color="white",
            font=("Arial", 20, "bold"),
            command=lambda: controller.show_frame(add_Frame)
        )
        add_button.pack(side="right", padx=10, pady=10)

        # กรอบใหญ่
        self.outer_frame = ctk.CTkFrame(
            self,
            width=700,
            height=400,
            fg_color="#FFFFFF",
            corner_radius=0,
        )
        self.outer_frame.place(relx=0.5, rely=0.5, anchor="center")
        #pywinstyles.set_opacity(self.outer_frame, value=0.9,color="#000001")

        # Scrollable Frame ภายใน
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.outer_frame,
            width=650,
            height=350,
            fg_color="#FFFFFF",
            corner_radius=15
        )
        self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center")

        # ▶️ เพิ่มข้อความบนสุด
        self.title_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="ชนิดยา",
            font=("TH Sarabun New", 32, "bold"),
            text_color="black",
            fg_color="transparent"
        )
        self.title_label.pack(pady=(20, 10))  # ระยะห่างบน-ล่างของข้อความ

        # ▶️ ปรับ Scrollbar สี
        self.scrollable_frame._scrollbar.configure(
            fg_color="#ffffff",
            button_color="#2563EB",
            bg_color="#FFFFFF",
            button_hover_color="#05C766"
        )
        #pywinstyles.set_opacity(self.scrollable_frame._scrollbar, value=1, color="#FFFFFF")

        # Sub Frame สำหรับรายการยา
        self.sub_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="#FFFFFF",
            width=900,
            corner_radius=20,
            bg_color="transparent"
        )
        self.sub_frame.pack(padx=20, pady=10, expand=True, fill="both")

    def go_to_add(self):
        threading.Thread(target=lambda: subprocess.Popen(["python", "Frame2-add.py"])).start()
        print("การแจ้งเตือน กำลังสลับไปยังหน้า Frame2-add.py")

    def load_medications(self):

      self.controller.fetch_medications(
            show_loading_screen=True,
            on_complete_callback=self.refresh_medications
        )

    def delete_medication(self, medicine_id):
        confirm = messagebox.askyesno("ยืนยัน", "คุณต้องการลบยานี้หรือไม่?")
        if confirm:
            if self.controller.network_status_var.get() == "offline":
                self.controller.notifier.show_notification("ไม่สามารถลบขณะออฟไลน์", success=False)
                return
            
            try:
                delete_medic = manageMedic.DeleteMedic(medicine_id)
                if delete_medic['status']:
                    
                    with self.controller.medicine_data_lock:
                        self.controller.cached_medications = [
                            med for med in self.controller.cached_medications if med['medicine_id'] != medicine_id
                        ]
                    
                    try:
                        with open(self.controller.MEDICINE_CACHE_FILE, "w", encoding="utf-8") as f:
                            json.dump(self.controller.cached_medications, f, indent=4)
                    except Exception as e:
                        print(f"Failed to update cache file after delete: {e}")

                    self.controller.notifier.show_notification(delete_medic['message'], success=True)
                else:
                    self.controller.notifier.show_notification(delete_medic['message'], success=False)
            
            except Exception as e:
                 self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)

            self.refresh_medications()


    def refresh_medications(self):
        for widget in self.sub_frame.winfo_children():
            widget.destroy()

        meds_to_display = self.controller.cached_medications
        if not meds_to_display:
            no_data_label = ctk.CTkLabel(
                self.sub_frame,
                text="ไม่มีข้อมูล",
                text_color="black",
                fg_color="transparent",
                font=("TH Sarabun New", 24, "bold")
            )
            no_data_label.pack(pady=10, fill="x")
            return

        for index, med in enumerate(meds_to_display):
            medicine_id = med['medicine_id']
            medicine_name = med['medicine_name']

            med_frame = ctk.CTkFrame(self.sub_frame, fg_color="#F0F0F0", corner_radius=15)
            med_frame.pack(padx=10, pady=10, fill="x")

            med_label = ctk.CTkLabel(
                med_frame,
                text=medicine_name,
                text_color="black",
                fg_color="transparent",
                font=("TH Sarabun New", 24)
            )
            med_label.pack(side="left", padx=10, pady=10)

            delete_button = ctk.CTkButton(
                med_frame,
                text="ลบ",
                width=100,
                height=50,
                corner_radius=15,
                fg_color="#F03E3E",
                hover_color="#FF6666",
                text_color="white",
                font=("TH Sarabun New", 18),
                command=lambda medicine_id=medicine_id: self.delete_medication(medicine_id)
            )
            delete_button.pack(side="right", padx=10, pady=10)

