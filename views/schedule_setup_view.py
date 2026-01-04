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
from config.styles import force_color, bottom_hover, BUTTON_RADIUS, hover_color, back_color, word_color, select_color
from views.medication_stock_view import MedicationApp

class Frame3(ctk.CTkFrame):
    def on_show(self):
        print("Frame3 is now visible")
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.selected_meal = ctk.StringVar(value="1 มื้อ")
        options = ["1 มื้อ", "2 มื้อ", "3 มื้อ", "4 มื้อ"]
        
        # พื้นหลัง
        bg_image = Image.open(f"{PATH}image/time.png").resize((1024, 800), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        content_frame = ctk.CTkFrame(
            self, width=700, height=400,
            corner_radius=0, fg_color="#FFFFFF", bg_color="#000001",
            border_width=2, border_color="#E8E8E8"
        )
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        #pywinstyles.set_opacity(content_frame, value=0.9,color="#000001")
        
        content_frame.grid_columnconfigure((0, 1), weight=1)
        
        # เส้นแต่งด้านบน
        top_accent = ctk.CTkFrame(
            content_frame, height=8, corner_radius=4,
            fg_color="#34C759"
        )
        top_accent.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(20, 0))
        
        # หัวข้อพร้อมไอคอน
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.grid(row=1, column=0, columnspan=2, pady=(5, 5))
    
        ctk.CTkLabel(
            title_frame, text="เลือกจำนวนมื้อจ่ายยา",
            text_color="#2D6A4F", font=("TH Sarabun New", 38, "bold")
        ).pack(side="top")
        
        # คำอธิบาย
        ctk.CTkLabel(
            content_frame, text="กรุณาเลือกจำนวนมื้อที่ต้องการจ่ายยาต่อวัน",
            text_color="#666666", font=("TH Sarabun New", 18)
        ).grid(row=2, column=0, columnspan=2, pady=(0, 5))
        
        # กรอบสำหรับปุ่มเลือกมื้อ
        buttons_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_container.grid(row=3, column=0, columnspan=2, pady=(5, 5))
        
        # ปุ่มเลือกมื้อแบบ Grid สวยงาม
        self.buttons = []
        for i, option in enumerate(options):
            btn = ctk.CTkButton(
                buttons_container, text=option, corner_radius=18,
                width=280, height=75,
                fg_color=("#34C759" if option == self.selected_meal.get() else "#F8F9FA"),
                text_color=("white" if option == self.selected_meal.get() else "#34C759"),
                hover_color="#A8DADC",
                font=("TH Sarabun New", 30, "bold"),
                border_width=2,
                border_color=("#34C759" if option == self.selected_meal.get() else "#E0E0E0"),
                command=lambda opt=option: self.select_meal(opt)
            )
            btn.grid(row=i // 2, column=i % 2, padx=25, pady=10)
            self.buttons.append(btn)
        
        # เส้นแบ่ง
        separator = ctk.CTkFrame(
            content_frame, height=2, corner_radius=1,
            fg_color="#E8E8E8"
        )
        separator.grid(row=4, column=0, columnspan=2, sticky="ew", padx=50, pady=(5, 5))
        
        # ปุ่มบันทึกแบบ Gradient Effect
        save_button = ctk.CTkButton(
            content_frame, text="บันทึกและไปต่อ",
            corner_radius=25, width=520, height=70,
            fg_color="#2D6A4F", text_color="white",
            hover_color="#1B4332",
            font=("TH Sarabun New", 34, "bold"),
            border_width=2, border_color="#1B4332",
            command=self.save_and_change_page
        )
        save_button.grid(row=5, column=0, columnspan=2, pady=(10,25))
        
        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)


        page_title = ctk.CTkLabel(
            navbar,
            text="ตั้งค่าจำนวนมื้อจ่ายยา",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)
        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )
        # ปุ่มย้อนกลับแบบ Rounded
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
        back_button.pack(side="right", padx=10, pady=10)
    
    def select_meal(self, option):
        self.selected_meal.set(option)
        # อัพเดทสไตล์ปุ่มพร้อมเอฟเฟ็กต์
        for btn in self.buttons:
            if btn.cget("text") == option:
                btn.configure(
                    fg_color="#34C759", 
                    text_color="white",
                    border_color="#2D6A4F",
                    border_width=3
                )
            else:
                btn.configure(
                    fg_color="#FFFFFF", 
                    text_color="#34C759",
                    border_color="#E0E0E0",
                    border_width=2
                )
    
    def save_and_change_page(self):
        print(f"บันทึกการตั้งค่าจำนวนมื้อ: {self.selected_meal.get()}")
        with open("meal_config.json", "w", encoding="utf-8") as f:
            json.dump({"meals": self.selected_meal.get()}, f, ensure_ascii=False, indent=4)
        self.controller.show_frame(MedicationScheduleFrame)


# เพิ่ม class HealthNumpad ในไฟล์ main.py


class TimeNumpad(ctk.CTkToplevel):
    def __init__(self, parent, entry):
        super().__init__(parent)
        self.title("Numpad เวลา")
        self.geometry("600x700")
        self.entry = entry
        self.attributes("-topmost", True)
        self.time_var = ctk.StringVar(value=self.entry.get())
        self.time_var.trace_add("write", lambda *args: self.format_time(self.time_var))
        self.entry.configure(textvariable=self.time_var)  
        self.configure(bg="white")


        frame = ctk.CTkFrame(self)
        frame.pack(pady=10)

        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 1), ("⌫", 3, 2)
        ]

        for text, row, col in buttons:
            ctk.CTkButton(frame, text=text, font=("Arial", 30), width=120, height=120, 
                          command=lambda x=text: self.on_button_click(x)).grid(row=row, column=col, padx=5, pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="ล้าง", fg_color="red", font=("Arial", 28), width=160, height=60,
                      command=self.clear_entry).pack(side="left", padx=20)

        ctk.CTkButton(btn_frame, text="OK", fg_color="green", font=("Arial", 28), width=160, height=60,
                      command=self.close_numpad).pack(side="left", padx=20)
    def format_time(self, time_var):
        text = time_var.get().replace(":", "")
        if len(text) > 4:
            text = text[:4]

        formatted = text
        if len(text) >= 2:
            formatted = text[:2] + ":" + text[2:]

        if len(text) == 4:
            h, m = int(text[:2]), int(text[2:])
            h = min(h, 23)
            m = min(m, 59)
            formatted = f"{h:02}:{m:02}"

        time_var.set(formatted)

    def on_button_click(self, value):
        current_text = self.entry.get()

        if value == "⌫":
            self.entry.delete(len(current_text) - 1, "end")
        elif len(current_text) < 5:
            if len(current_text) == 2 and ":" not in current_text:
                self.entry.insert("end", ":")  
            self.entry.insert("end", value)

    def clear_entry(self):
        self.entry.delete(0, "end") 

    def close_numpad(self):
        text = self.entry.get()
        if len(text) == 4: 
            self.entry.insert(2, ":")
        elif len(text) != 5: 
            self.entry.delete(0, "end")
        self.destroy()



# ⭐️ [แทนที่] คลาส MedicationApp ทั้งหมดด้วยโค้ดนี้ ⭐️


class MedicationScheduleFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, width=1024, height=600, corner_radius=0, fg_color="#1d567b")
        self.controller = controller
        self.interval_label = None
        self.interval_days = None
        self.pack_propagate(False)  # ✅ กันไม่ให้ย่อ/ขยายเอง

        # === พื้นหลัง ===
        bg_image = Image.open(f"{PATH}image/time.png").resize((1024, 800), Image.Resampling.LANCZOS) 
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # === กรอบหลัก ===
        content_frame = ctk.CTkFrame(
            self, width=800, height=400,
            corner_radius=0, fg_color="#ffffff", bg_color="#000001",
            border_width=3, border_color="#E8E8E8"
        )
        content_frame.place(relx=0.5, rely=0.47, anchor="center")
        content_frame.pack_propagate(False)
        #pywinstyles.set_opacity(content_frame, value=0.9,color="#000001")

        # === หัวข้อหลักพร้อมไอคอน ===
        title_container = ctk.CTkFrame(content_frame, fg_color="transparent", height=60)
        title_container.pack(fill="x", padx=30, pady=(10, 5))
    
        
        ctk.CTkLabel(
            title_container, text="กำหนดระยะเวลาการใช้ยา",
            font=("TH Sarabun New", 34, "bold"), 
            text_color="#0077b6"
        ).pack(side="left")

        # === Scrollable Frame สำหรับเนื้อหา ===
        frame = ctk.CTkScrollableFrame(content_frame, width=850, height=320,
                                       corner_radius=15, fg_color="#f8f9fa",
                                       border_width=2, border_color="#e9ecef")
        frame.pack(expand=True, fill="both", padx=20, pady=(5, 10))
        self.frame = frame

        # โหลดการตั้งค่ามื้ออาหาร
        self.load_meal_config()

        # === การ์ดสำหรับวันที่เริ่ม ===
        start_card = ctk.CTkFrame(frame, fg_color="#ffffff", corner_radius=15,
                                  border_width=2, border_color="#0077b6")
        start_card.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="ew")

        # ไอคอนและหัวข้อ
        start_header = ctk.CTkFrame(start_card, fg_color="transparent")
        start_header.pack(fill="x", padx=15, pady=(15, 5))
        
        frame_text = ctk.CTkLabel(
            start_header, text="เลือกวันที่เริ่มจ่ายยา",
            font=("TH Sarabun New", 26, "bold"), text_color="#0077b6"
        )
        frame_text.pack(side="left")

        # Input container
        frame_date = ctk.CTkFrame(start_card, fg_color="#f0f8ff", corner_radius=12,
                                  border_width=1, border_color="#b8daff")
        frame_date.pack(fill="x", padx=15, pady=(5, 10))

        date_entry = ctk.CTkEntry(frame_date, width=250, height=55,
                                  font=("TH Sarabun New", 24,"bold"),text_color="#000000", 
                                  corner_radius=8, border_width=2,
                                  border_color="#0077b6", fg_color="white")  
        date_entry.pack(side="left", padx=15, pady=10)

        # ปุ่มเปิดปฏิทินแบบสวย
        pick_date_btn = ctk.CTkButton(
            frame_date, text="เลือกวัน", width=140, height=55,
            font=("TH Sarabun New", 20, "bold"), corner_radius=8,
            fg_color="#0077b6", hover_color="#023e8a",
            border_width=2, border_color="#023e8a"
        )
        pick_date_btn.pack(side="right", padx=15, pady=10)

        # === การ์ดสำหรับวันที่สิ้นสุด ===
        end_card = ctk.CTkFrame(frame, fg_color="#ffffff", corner_radius=15,
                                border_width=2, border_color="#e63946")
        end_card.grid(row=1, column=1, padx=20, pady=(5, 5), sticky="ew")

        # ไอคอนและหัวข้อ
        end_header = ctk.CTkFrame(end_card, fg_color="transparent")
        end_header.pack(fill="x", padx=15, pady=(15, 5))
        

        frame_text2 = ctk.CTkLabel(
            end_header, text="สิ้นสุดการจ่ายยา",
            font=("TH Sarabun New", 26, "bold"), text_color="#e63946"
        )  
        frame_text2.pack(side="left")

        # Input container
        frame_date2 = ctk.CTkFrame(end_card, fg_color="#fff5f5", corner_radius=12,
                                   border_width=1, border_color="#fecaca")
        frame_date2.pack(fill="x", padx=15, pady=(5, 15))

        end_entry = ctk.CTkEntry(frame_date2, width=250, height=55,
                                 font=("TH Sarabun New", 24,"bold"),text_color="#000000",
                                 corner_radius=8, border_width=2,
                                 border_color="#e63946", fg_color="white")
        end_entry.pack(side="left", padx=15, pady=10)

        # === เส้นแบ่งตกแต่ง ===
        separator = ctk.CTkFrame(
            frame, height=3, corner_radius=2,
            fg_color="#dee2e6"
        )
        separator.grid(row=2, column=0, columnspan=2, sticky="ew", 
                       padx=40, pady=20)
        



        # === Navbar แบบ Gradient ===
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)


        # Title container พร้อมไอคอน
        title_nav_container = ctk.CTkFrame(navbar, fg_color="transparent")
        
        page_title = ctk.CTkLabel(
            navbar,
            text="กำหนดวันที่เริ่มจ่ายยา",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)

        def go_back():
            controller.show_frame(Frame3)

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
            command=go_back
        )
        back_button.pack(side="right", padx=10, pady=10)
        
        def save_and_go_to_frame1():
            
            # --- (1) Get data from entries ---
            start_date = date_entry.get()
            end_date = end_entry.get()
            device_id = self.controller.user['device_id']

            # --- (2) Validation (same as before) ---
            if start_date == "" and end_date == "":
                self.controller.notifier.show_notification("กรุณากำหนดวันที่เริ่มจ่ายยา", success=False)
                return

            # --- (3) Get Network Status ---
            network_status = "offline" # ค่าเริ่มต้น
            try:
                # พยายามอ่านจาก ctk.StringVar (วิธีที่แนะนำ)
                network_status = self.controller.network_status_var.get()
            except AttributeError:
                try:
                    # ถ้าไม่สำเร็จ ลองอ่านจากตัวแปรธรรมดา
                    network_status = self.controller.network_status
                except AttributeError:
                    print("Warning: ไม่สามารถอ่านสถานะเน็ตจาก controller ได้")

            # ⭐️ ชื่อไฟล์สำหรับเก็บคิวงานออฟไลน์
            QUEUE_FILE = "offline_schedule_queue.json"

            if network_status == "online":
                # --- 4a. ONLINE: พยายามส่งข้อมูลไปเซิร์ฟเวอร์ ---
                print("Network is Online. Sending data to server...")
                try:
                    setting_time = set_dispensing_time.set_time(
                        device_id,
                        start_date, 
                        end_date
                    )
                    
                    if setting_time['status']:
                        self.controller.notifier.show_notification(setting_time['message'], success=True)
                        controller.show_frame(MedicationApp) # ไปหน้าถัดไป
                    else:
                        self.controller.notifier.show_notification(setting_time['message'], success=False)
                        # ไม่ต้องไปหน้าถัดไปถ้าเซิร์ฟเวอร์ปฏิเสธ

                except requests.exceptions.RequestException as e: 
                    # ⭐️ ถ้า "ออนไลน์" แต่เซิร์ฟเวอร์ล่ม (เช่น 500 error หรือ ConnectTimeout)
                    print(f"Failed to send data (Server Error/Timeout): {e}")
                    # ให้บันทึกลงคิวออฟไลน์แทน
                    self.save_schedule_to_queue(QUEUE_FILE, device_id, start_date, end_date)
                    self.controller.notifier.show_notification("เซิร์ฟเวอร์ขัดข้อง: บันทึกข้อมูลไว้ในเครื่อง", success=False)
                    controller.show_frame(MedicationApp) # ยังคงไปหน้าถัดไป

            else:
                # --- 4b. OFFLINE: บันทึกลงไฟล์ JSON Queue ---
                print("Network is Offline. Saving data to local queue...")
                try:
                    self.save_schedule_to_queue(QUEUE_FILE, device_id, start_date, end_date)
                    
                    # แจ้งเตือนผู้ใช้และไปหน้าถัดไป
                    self.controller.notifier.show_notification("Offline: บันทึกข้อมูลไว้ในเครื่อง", success=True)
                    controller.show_frame(MedicationApp)
                    
                except Exception as e:
                    self.controller.notifier.show_notification(f"ผิดพลาด: บันทึกไฟล์ไม่สำเร็จ: {e}", success=False)
                    print(f"Failed to save offline data: {e}")
        
        save_button = ctk.CTkButton(
            navbar, text="บันทึก", corner_radius=20, width=100, height=50, 
            fg_color="#2D6A4F", text_color="white", hover_color="#1B4332",
            font=("Arial", 24, "bold"), 
            border_width=2, border_color="#1B4332",
            command=save_and_go_to_frame1
        )
        save_button.pack(side="right", padx=10, pady=10)


       
        date_picker_open = [False]
        def open_date_picker():
            if not date_picker_open[0]:
                date_entry.configure(state="normal")
                DatePicker(self, date_entry, end_entry, date_picker_open).place(
                    in_=frame_date, relx=0.9, rely=-0.5, anchor="center"
                )
                date_picker_open[0] = True

        # เชื่อมโยงฟังก์ชันกับปุ่ม
        pick_date_btn.configure(command=open_date_picker)

        # Configure grid weights
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def load_meal_config(self):
        try:
            with open("meal_config.json", "r") as f:
                meal_config = json.load(f)
                num_meals = int(meal_config["meals"].split()[0])
                self.interval_days = 28 // num_meals

            if self.interval_label:
                self.interval_label.configure(text=f"ระยะเวลาในการจ่ายยา {self.interval_days} วัน")
            else:
                # การ์ดแสดงข้อมูลระยะเวลา
                info_card = ctk.CTkFrame(self.frame, fg_color="#e8f5e8", corner_radius=15,
                                         border_width=2, border_color="#34C759")
                info_card.grid(row=0, column=0, columnspan=2,
                               padx=30, pady=(15, 20), sticky="ew")

                # ไอคอนและข้อมูล
                info_container = ctk.CTkFrame(info_card, fg_color="transparent")
                info_container.pack(expand=True, fill="both", padx=20, pady=15)
                
                ctk.CTkLabel(
                    info_container, text="!",
                    font=("Arial", 32),text_color="#F8BF04"
                ).pack(side="left", padx=(0, 15))

                self.interval_label = ctk.CTkLabel(
                    info_container, text=f"ระยะเวลาในการจ่ายยา {self.interval_days} วัน",
                    font=("TH Sarabun New", 26, "bold"),
                    text_color="#2D6A4F"
                )
                self.interval_label.pack(side="left")

        except Exception as e:
            print(f"Error loading meal_config.json: {e}")
    def save_schedule_to_queue(self, queue_file, device_id, start_date, end_date):
            new_task = {
                "type": "set_time", # ระบุประเภทของงาน
                "payload": {
                    "device_id": device_id,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "timestamp": datetime.now().isoformat() # เก็บเวลาที่บันทึก
            }

           
            queue = []
            if os.path.exists(queue_file):
                try:
                    with open(queue_file, "r", encoding="utf-8") as f:
                        queue = json.load(f)
                        if not isinstance(queue, list): # กันไฟล์เสีย
                            queue = []
                except json.JSONDecodeError:
                    queue = [] 
            
           
            queue.append(new_task)
            
            try:
                with open(queue_file, "w", encoding="utf-8") as f:
                    json.dump(queue, f, indent=4)
                print(f"Task successfully added to {queue_file}")
            except Exception as e:
                print(f"Error writing to {queue_file}: {e}")
                raise # ส่ง exception กลับไปให้ฟังก์ชันหลัก
        
    def on_show(self):
        print("MedicationScheduleFrame is now visible")
        self.load_meal_config()



class DatePicker(ctk.CTkFrame):
    def __init__(self, master, entry, end_entry, open_flag):
        print("DatePicker initialized") 
        super().__init__(master)
        self.entry = entry
        self.end_entry = end_entry 
        self.open_flag = open_flag
        self.configure(fg_color="white", bg_color=back_color, corner_radius=15)

        self.cal = Calendar(
            self, selectmode="day", year=datetime.now().year, month=datetime.now().month, day=datetime.now().day,
            background="white", foreground="black", headersbackground="#87CEFA",
            normalbackground="white", weekendbackground="#E0F7FF", 
            selectbackground="#0094FF", selectforeground="white", 
            bordercolor="#0094FF", disabledbackground="#F0F0F0",
            font=("Arial", 30),locale="th_TH"
        )
        self.cal.pack(pady=20)

        select_btn = ctk.CTkButton(self, text="เลือก", fg_color=force_color   , text_color="white", font=("Arial", 30, "bold"), command=self.set_date)
        select_btn.pack(side="left", padx=10, pady=10)

        close_btn = ctk.CTkButton(self, text="ปิด", fg_color="#FF3B3B", text_color="white", font=("Arial", 30, "bold"), command=self.close_date_picker)  
        close_btn.pack(side="right", padx=10, pady=10)

    def set_date(self):
        try:
            with open("meal_config.json", "r") as f:
                meal_config = json.load(f)
                num_meals = int(meal_config["meals"].split()[0])
                self.interval_days = 28 // num_meals

            selected_date = self.cal.get_date()
            formatted_date = datetime.strptime(selected_date, "%d/%m/%y").strftime("%d/%m/%Y")
            self.entry.configure(state="normal")
            self.entry.delete(0, "end")
            self.entry.insert(0, formatted_date)
            self.entry.configure(state="readonly")
            
            end_date = datetime.strptime(formatted_date, "%d/%m/%Y") + timedelta(days=self.interval_days)
            formatted_end_date = end_date.strftime("%d/%m/%Y")
            self.end_entry.configure(state="normal")
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, formatted_end_date)
            self.end_entry.configure(state="readonly")
        except Exception as e:
            print(f"Error loading meal_config.json: {e}")
        self.close_date_picker()

    def close_date_picker(self):
        self.open_flag[0] = False
        self.destroy()


