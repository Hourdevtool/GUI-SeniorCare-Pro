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

# Helper and View Imports
from utils.helpers import show_onboard, hide_onboard, create_entry_with_keyboard, toggle_language, get_role_theme
from views.home_view import HomePage
from models.voice_service import VoicePromptPlayer

class info(ctk.CTkFrame):
    def on_show(self):
        print("info is now visible")
        self.userid = self.controller.user['id']
        
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังโหลดข้อมูลผู้ใช้...", "กรุณารอสักครู่")
        
        def load_user_info_thread():
            try:
                self.result = manageData.get(self.userid)
                if self.result:
                    data = self.result
                    # อัปเดต UI
                    self.controller.after(0, lambda: self.populate_user_info(data))
                else:
                    self.controller.after(0, self.controller.hide_loading)
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")
                self.controller.after(0, self.controller.hide_loading)
        
        threading.Thread(target=load_user_info_thread, daemon=True).start()
    
    def populate_user_info(self, data):
        """กรอกข้อมูลผู้ใช้ลงในฟอร์ม"""
        print(f"populate_user_info:{data}")
        try:
            self.entry_owner.delete(0, 'end')
            self.entry_owner.insert(0, f"{data.get('firstname_th', '')} {data.get('lastname_th', '')}")

            self.entry_email.delete(0, 'end')
            self.entry_email.insert(0, str(data.get('email', '')))

            self.entry_password.delete(0, 'end')
            self.entry_password.insert(0, str(data.get('password', '')))

            self.entry_line_id.delete(0, 'end')
            self.entry_line_id.insert(0, str(data.get('line_id', '')))

            self.entry_device_id.delete(0, 'end')
            self.entry_device_id.insert(0, str(data.get('device_id', '')))

            self.entry_line_token.delete(0, 'end')
            self.entry_line_token.insert(0, str(data.get('token_line', '')))

            self.entry_line_group.delete(0, 'end')
            self.entry_line_group.insert(0, str(data.get('group_id', '')))

            self.entry_telegram_token.delete(0, 'end')
            self.entry_telegram_token.insert(0, str(data.get('telegram_key', '')))

            self.entry_telegram_id.delete(0, 'end')
            self.entry_telegram_id.insert(0, str(data.get('telegram_id', '')))
            
            # ซ่อนหน้าดาวโหลด
            self.controller.hide_loading()
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
            self.controller.hide_loading()

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.userid = None
        self.result = None

        # Background
        bg_image = Image.open(f"{PATH}image/info.png").resize((1024, 800), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x", pady=50)

        page_title = ctk.CTkLabel(
            navbar,
            text="ข้อมูลตัวเครื่อง",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)

        def go_back():
            controller.show_frame(HomePage)

        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )
        
        # สร้างปุ่มโดยใส่รูปภาพลงใน image= ไม่ใช่ text=
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
            command=go_back
        )
        
        back_button.pack(side="right", padx=10, pady=5)
        # Disable editing function
        def disable_editing(event):
            return "break"

        # Form Frame
        form_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#FFFFFF", bg_color="#000001" ,
                                   width=750, height=480)
        form_frame.place(relx=0.5, rely=0.5, anchor="center")
        #pywinstyles.set_opacity(form_frame, value=0.8,color="#000001")
        
        # ป้องกันไม่ให้ grid ขยายขนาดอัตโนมัติ
        form_frame.grid_propagate(False)
        

        form_frame.grid_columnconfigure(0, weight=1, minsize=100)
        form_frame.grid_columnconfigure(1, weight=1, minsize=200)
        form_frame.grid_columnconfigure(2, weight=1, minsize=100)
        form_frame.grid_columnconfigure(3, weight=1, minsize=200)

        # Title
        ctk.CTkLabel(form_frame, text="ข้อมูลตัวเครื่อง", text_color="#2D6A4F",
                     font=("Arial", 24, "bold")).grid(row=0, column=0, columnspan=4, pady=(20, 30))

        # Row 1
        ctk.CTkLabel(form_frame, text="เจ้าของผู้สมัคร", text_color="black", font=("Arial", 18)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_owner = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_owner.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_owner.bind("<Key>", disable_editing)

        ctk.CTkLabel(form_frame, text="สถานะเครื่อง", text_color="black", font=("Arial", 18)).grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.entry_status = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18), state='disabled') # เปลี่ยน state เป็น 'disabled' ตั้งแต่เริ่มต้น
        self.entry_status.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.entry_status.bind("<Key>", disable_editing)
        
        # Row 2
        ctk.CTkLabel(form_frame, text="อีเมล", text_color="black", font=("Arial", 18)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_email = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_email.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_email.bind("<Key>", disable_editing)

        ctk.CTkLabel(form_frame, text="รหัสผ่าน", text_color="black", font=("Arial", 18)).grid(row=2, column=2, sticky="w", padx=10, pady=5)
        self.entry_password = ctk.CTkEntry(form_frame, show="*", fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_password.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        self.entry_password.bind("<Key>", disable_editing)

        # Row 3
        ctk.CTkLabel(form_frame, text="ไอดีไลน์", text_color="black", font=("Arial", 18)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.entry_line_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_line_id.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="หมายเลขเครื่อง", text_color="black", font=("Arial", 18)).grid(row=3, column=2, sticky="w", padx=10, pady=5)
        self.entry_device_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_device_id.grid(row=3, column=3, padx=5, pady=5, sticky="ew")
        self.entry_device_id.bind("<Key>", disable_editing)

        # Section: การแจ้งเตือน
        ctk.CTkLabel(form_frame, text="การแจ้งเตือน", text_color="#2D6A4F", font=("Arial", 22, "bold")).grid(row=4, column=0, columnspan=4, pady=(20, 20))

        # Row 5
        ctk.CTkLabel(form_frame, text="หมายเลขโทเคนไลน์", text_color="black", font=("Arial", 18)).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.entry_line_token = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_line_token.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="ไอดี กลุ่มไลน์", text_color="black", font=("Arial", 18)).grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.entry_line_group = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_line_group.grid(row=6, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Row 6
        ctk.CTkLabel(form_frame, text="หมายเลขโทเคน เทเลแกรม", text_color="black", font=("Arial", 18)).grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.entry_telegram_token = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_telegram_token.grid(row=7, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="ไอดี เทเลแกรม", text_color="black", font=("Arial", 18)).grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.entry_telegram_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_telegram_id.grid(row=8, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Save Button
        def save_data():
            success = manageData.updateData(
                self.userid,
                self.result['device_id'],
                self.entry_line_id.get(),
                self.entry_line_token.get(),
                self.entry_telegram_token.get(),
                self.entry_telegram_id.get(),
                self.entry_line_group.get(),
            )

            if success['status']:
                self.controller.notifier.show_notification(success['message'], success=True)
                controller.show_frame(HomePage)
            else:
                self.controller.notifier.show_notification(success['message'], success=False)


        btn_save = ctk.CTkButton(form_frame, text="บันทึกข้อมูล", command=save_data,
                                 fg_color="green", text_color="white",
                                 font=("Arial", 20, "bold"), height=40, corner_radius=20)
        btn_save.grid(row=9, column=0, columnspan=4, pady=(10, 10))






class Wificonnect(ctk.CTkFrame):
    def on_show(self):
        print("Wificonnect is now visible")
        # โหลดรายการ WiFi ครั้งแรกอัตโนมัติ
        if not hasattr(self, '_wifi_loaded_once'):
            self._wifi_loaded_once = True
            self.update_wifi_list()
        show_onboard()
        # เพิ่มส่วนนี้
        def on_frame_click(event):
            widget = event.widget
            if not isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
                hide_onboard()

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # === การกำหนดสีและธีม (Color Theme) ===
        self.primary_color = "#2563EB"      # สีน้ำเงินหลัก
        self.secondary_color = "#F1F5F9"    # สีพื้นหลังอ่อน
        self.accent_color = "#10B981"       # สีเขียวสำหรับ success
        self.danger_color = "#EF4444"       # สีแดงสำหรับ danger
        self.text_dark = "#1E293B"          # ข้อความเข้ม
        self.text_light = "#64748B"         # ข้อความอ่อน

        # === โหลดภาพและสร้าง CTkImage ===
        self.bg_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/wifi.png").resize((1024, 800)), 
            size=(1024, 800)
        )
        self.internet_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/internet.png").resize((32, 32)), 
            size=(32, 32)
        )
        self.refresh_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/refresh.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.send_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/send.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.padlock_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/padlock.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.broken_link_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/broken-link.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.eye_open_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/eye_open.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.eye_closed_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/eye_closed.png").resize((24, 24)), 
            size=(24, 24)
        )
        self.no_signal_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/no-signal.png").resize((48, 48)), 
            size=(48, 48)
        )

        # === พื้นหลัง ===
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # === Main Frame ===
        main_frame = ctk.CTkFrame(
            self,
            width=700,
            height=380,
            corner_radius=0,
            fg_color="white",
            border_width=1,
            border_color="#E2E8F0",
            bg_color="#000001"
        )
        main_frame.place(relx=0.5, rely=0.48, anchor="center")
        main_frame.pack_propagate(False)
        #pywinstyles.set_opacity(main_frame, value=0.9, color="#000001")

        # === Header ===
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=80)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))

        wifi_icon_label = ctk.CTkLabel(header_frame, image=self.internet_ctk_image, text="")
        wifi_icon_label.pack(side="left")

        title_label = ctk.CTkLabel(
            header_frame, 
            text="เลือกเครือข่าย Wi-Fi", 
            font=("Arial", 28, "bold"), 
            text_color=self.text_dark
        )
        title_label.pack(side="left", padx=(15, 0))

        self.refresh_button = ctk.CTkButton(
            header_frame,
            image=self.refresh_ctk_image,
            text="รีเฟรช",
            width=120,
            height=40,
            fg_color=self.primary_color,
            hover_color="#1D4ED8",
            font=("Arial", 14, "bold"),
            command=self.update_wifi_list
        )
        self.refresh_button.pack(side="right")

        self.lang_button = ctk.CTkButton(
            header_frame,  # หรือ parent ที่คุณต้องการวางปุ่ม
            text="TH/EN",
            width=50,
            height=40,
            corner_radius=10,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            font=("Arial", 10, "bold"),
            command=toggle_language
            )
        self.lang_button.pack(side="right")


        # === WiFi List Container ===
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.wifi_scroll_frame = ctk.CTkScrollableFrame(
            content_frame, width=620, height=200,
            corner_radius=15, fg_color=self.secondary_color,
            scrollbar_fg_color=self.secondary_color
        )
        self.wifi_scroll_frame.pack(fill="both", expand=True)

        self.password_frame = ctk.CTkFrame(content_frame, corner_radius=15, fg_color=self.secondary_color)

        # === Bottom Navbar ===
        navbar = ctk.CTkFrame(self, height=120, fg_color="white", border_width=1, border_color="#E2E8F0")
        navbar.pack(side="bottom", fill="x", pady=40)

        button_container = ctk.CTkFrame(navbar, fg_color="transparent")
        button_container.pack(expand=True, fill="both", padx=20, pady=20)

        back_button = ctk.CTkButton(
            button_container,
            image=self.reply_ctk_image,
            text="ย้อนกลับ",
            width=180,
            height=60,
            corner_radius=15,
            fg_color="#6B7280",
            hover_color="#4B5563",
            text_color="white",
            font=("Arial", 18, "bold"),
            command=lambda: controller.show_frame(login)
        )
        back_button.pack(side="left")

        skip_button = ctk.CTkButton(
            button_container,
            image=self.send_ctk_image,
            compound="right",
            text="ข้าม",
            width=180,
            height=60,
            corner_radius=15,
            fg_color=self.accent_color,
            hover_color="#059669",
            text_color="white",
            font=("Arial", 18, "bold"),
            command=lambda: controller.show_frame(HomePage)
        )
        skip_button.pack(side="right")

        self.status_label = ctk.CTkLabel(
            button_container,
            text="ยังไม่ได้เชื่อมต่อ",
            font=("Arial", 16),
            text_color=self.text_light
        )
        self.status_label.pack(expand=True)

    # ================= ฟังก์ชัน WiFi =================
    def get_wifi_list(self):
        try:
            wifi = PyWiFi()
            iface = wifi.interfaces()[0]
            iface.scan()
            scan_results = iface.scan_results()
            ssids = [network.ssid.strip() for network in scan_results if network.ssid]
            unique_ssids = list(dict.fromkeys(ssids))
            return unique_ssids
        except Exception as e:
            print(f"Error getting WiFi list: {e}")
            return []

    def show_password_form(self, ssid):
        self.wifi_scroll_frame.pack_forget()
        for widget in self.password_frame.winfo_children():
            widget.destroy()

        header_frame = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text=f"เชื่อมต่อกับ: {ssid}",
            font=("Arial", 20, "bold"),
            text_color=self.text_dark
        )
        title_label.pack(side="left", padx=(10, 0))
        

        input_frame = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=10)

        password_label = ctk.CTkLabel(
            input_frame, text="รหัสผ่าน WiFi:", font=("Arial", 16, "bold"), text_color=self.text_dark
        )
        password_label.pack(anchor="w", pady=(0, 10))

        password_input_frame = ctk.CTkFrame(input_frame, fg_color="white", corner_radius=10, height=50)
        password_input_frame.pack(fill="x", pady=(0, 10))
        password_input_frame.pack_propagate(False)

        key_icon_label = ctk.CTkLabel(password_input_frame, image=self.internet_ctk_image, text="")
        key_icon_label.pack(side="left", padx=(15, 10), pady=12)

        self.password_entry = create_entry_with_keyboard(
            password_input_frame,
            show="*",
            placeholder_text="กรอกรหัสผ่าน...",
            font=("Arial", 16),
            fg_color="white",
            border_width=0,
            text_color=self.text_dark
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 50), pady=12)
        
        self.show_pass_var = ctk.BooleanVar(value=False)
        self.show_pass_btn = ctk.CTkButton(
            password_input_frame, image=self.eye_closed_ctk_image,text="",
            width=30, height=30, fg_color="white", hover_color="#F8FAFC",
            command=self.toggle_password_visibility
        )
        self.show_pass_btn.pack(side="right", padx=(0, 15), pady=12)

        button_frame = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=(20, 30))

        connect_button = ctk.CTkButton(
            button_frame,
            image=self.broken_link_ctk_image,
            text="เชื่อมต่อ",
            width=200, height=50, font=("Arial", 16, "bold"),
            fg_color=self.primary_color, hover_color="#1D4ED8", corner_radius=10,
            command=lambda: self.connect_wifi(ssid)
        )
        connect_button.pack(side="right", padx=(10, 0))

        cancel_button = ctk.CTkButton(
            button_frame,
            image=self.reply_ctk_image,
            text="ยกเลิก",
            width=150, height=50, font=("Arial", 16, "bold"),
            fg_color="#6B7280", hover_color="#4B5563", corner_radius=10,
            command=self.show_wifi_list
        )
        cancel_button.pack(side="right")

        self.password_frame.pack(fill="both", expand=True)
        self.password_entry.focus()

    def toggle_password_visibility(self):
        if self.show_pass_var.get():
            self.password_entry.configure(show="*")
            self.show_pass_btn.configure(image=self.eye_closed_ctk_image)
            self.show_pass_var.set(False)
        else:
            self.password_entry.configure(show="")
            self.show_pass_btn.configure(image=self.eye_open_ctk_image)
            self.show_pass_var.set(True)

    def connect_wifi(self, ssid):
        password = self.password_entry.get()
        if not password:
            self.status_label.configure(text="กรุณากรอกรหัสผ่าน", text_color=self.danger_color)
            return
        self.status_label.configure(text=f"กำลังเชื่อมต่อ {ssid}...", text_color=self.primary_color)
        self.controller.after(2000, lambda: self.connection_success(ssid))

    def connection_success(self, ssid):
        self.status_label.configure(text=f"เชื่อมต่อ {ssid} สำเร็จ", text_color=self.accent_color)
        self.controller.after(1000, lambda: self.controller.show_frame(HomePage))

    def show_wifi_list(self):
        self.password_frame.pack_forget()
        self.wifi_scroll_frame.pack(fill="both", expand=True)
        self.status_label.configure(text="เลือกเครือข่าย WiFi", text_color=self.text_light)

    def update_wifi_list(self):
        # กันกดซ้ำระหว่างกำลังโหลด
        if hasattr(self, '_wifi_loading') and self._wifi_loading:
            return
        self._wifi_loading = True
        self._wifi_scanned_once = False
        # ปิดปุ่มระหว่างโหลด
        try:
            self.refresh_button.configure(state="disabled")
        except Exception:
            pass
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังค้นหาเครือข่าย WiFi...", "กรุณารอสักครู่")
        
        self.status_label.configure(text="กำลังค้นหา WiFi...", text_color=self.primary_color)
        
        def load_wifi_thread():
            try:
                # รอสักครู่เพื่อให้เห็นหน้าดาวโหลด
                import time
                time.sleep(0.5)
                
                self.controller.after(0, self.load_wifi_networks)
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")
                self.controller.after(0, self.controller.hide_loading)
        
        threading.Thread(target=load_wifi_thread, daemon=True).start()

    def load_wifi_networks(self):
        for widget in self.wifi_scroll_frame.winfo_children():
            widget.destroy()

        wifi_list = self.get_wifi_list()

        if not wifi_list:
            # ลองสแกนซ้ำอัตโนมัติ 1 ครั้งในครั้งแรกที่เปิดหน้า
            if not getattr(self, '_wifi_scanned_once', False):
                self._wifi_scanned_once = True
                self.status_label.configure(text="กำลังค้นหาอีกครั้ง...", text_color=self.primary_color)
                self.controller.after(1200, self.load_wifi_networks)
                return
            no_wifi_frame = ctk.CTkFrame(self.wifi_scroll_frame, fg_color="transparent")
            no_wifi_frame.pack(pady=50)

            sad_icon_label = ctk.CTkLabel(no_wifi_frame, image=self.no_signal_ctk_image, text="")
            sad_icon_label.pack()

            no_wifi_label = ctk.CTkLabel(
                no_wifi_frame,
                text="ไม่พบเครือข่าย WiFi\nกรุณาตรวจสอบการเชื่อมต่อและลองใหม่",
                font=("Arial", 16),
                text_color=self.text_light,
                justify="center"
            )
            no_wifi_label.pack(pady=(10, 0))
            self.status_label.configure(text="ไม่พบเครือข่าย", text_color=self.danger_color)
            # ซ่อนหน้าดาวโหลด
            self.controller.hide_loading()
        else:
            for i, wifi in enumerate(wifi_list):
                wifi_item_frame = ctk.CTkFrame(
                    self.wifi_scroll_frame,
                    fg_color="white",
                    corner_radius=12,
                    height=60
                )
                wifi_item_frame.pack(fill="x", padx=10, pady=5)
                wifi_item_frame.pack_propagate(False)

                # ความแรงสัญญาณจำลอง
                signal_label = ctk.CTkLabel(wifi_item_frame, image=self.internet_ctk_image, text="")
                signal_label.pack(side="left", padx=(20, 10), pady=15)

                wifi_name_label = ctk.CTkLabel(
                    wifi_item_frame, text=wifi,
                    font=("Arial", 16, "bold"), text_color=self.text_dark
                )
                wifi_name_label.pack(side="left", pady=15)

                lock_label = ctk.CTkLabel(wifi_item_frame, image=self.padlock_ctk_image, text="")
                lock_label.pack(side="right", padx=(10, 20), pady=15)

                def on_wifi_click(w=wifi):
                    self.show_password_form(w)

                invisible_button = ctk.CTkButton(
                    wifi_item_frame, 
                    text=wifi, fg_color="transparent", hover_color="#F1F5F9", border_width=0, 
                    text_color=self.text_dark, font=("Arial", 16, "bold"), anchor="w", command=on_wifi_click
                )
                invisible_button.place(relx=0, rely=0, relwidth=1, relheight=1)

            self.status_label.configure(text=f"พบเครือข่าย {len(wifi_list)} เครือข่าย", text_color=self.accent_color)
        
        # ซ่อนหน้าดาวโหลดหลังจากโหลดเสร็จ
        self.controller.hide_loading()
        # เปิดปุ่มและรีเซ็ตสถานะโหลด
        try:
            self.refresh_button.configure(state="normal")
        except Exception:
            pass
        self._wifi_loading = False

            


