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
from config.styles import force_color, bottom_hover, BUTTON_RADIUS

class HealthNumpad(ctk.CTkToplevel):
    def __init__(self, parent, entry, max_length=3):
        super().__init__(parent)
        self.entry = entry
        self.max_length = max_length
        self.title("กรอกตัวเลข")
        self.configure(fg_color="#f0f0f0")
        
        self.update()
        self.geometry("450x600+300+50")
        self.update_idletasks()
        
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        self.protocol("WM_DELETE_WINDOW", self.close_numpad)
        
        # === Display ===
        display_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15, height=80)
        display_frame.pack(pady=20, padx=20, fill="x")
        
        self.display_label = ctk.CTkLabel(
            display_frame, 
            text=self.entry.get() or "0",
            font=("Arial", 48, "bold"),
            text_color="#2563EB"
        )
        self.display_label.pack(pady=15)
        
        # === ปุ่มตัวเลข ===
        frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=15)
        frame.pack(pady=10, padx=20)
        
        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 0,), ("⌫", 3, 1), ("ยืนยัน", 3, 2)
        ]
        
        for item in buttons:
            text = item[0]
            row = item[1]
            col = item[2]
            colspan = item[3] if len(item) > 3 else 1
            
            btn = ctk.CTkButton(
                frame, 
                text=text, 
                font=("Arial", 28, "bold"),
                width=100 if colspan == 1 else 220,
                height=85,
                corner_radius=15,
                fg_color="#e0e0e0",
                hover_color="#c0c0c0",
                text_color="black"
            )
            
            if text == "⌫":
                btn.configure(fg_color="#ff6b6b", hover_color="#ee5a52", text_color="white")
                btn.configure(command=lambda x=text: self.on_button_click(x))
            elif text == "ยืนยัน":
                btn.configure(fg_color="#2563EB", hover_color="#1D4ED8", text_color="white",
                              command=self.close_numpad)
            else:
                btn.configure(command=lambda x=text: self.on_button_click(x))
            
            btn.grid(row=row, column=col, columnspan=colspan, padx=8, pady=8)
    
    def update_display(self):
        value = self.entry.get() or "0"
        self.display_label.configure(text=value)
    
    def on_button_click(self, value):
        self.entry.configure(state="normal")
        current_text = self.entry.get()
        
        if value == "⌫":
            if len(current_text) > 0:
                self.entry.delete(len(current_text) - 1, "end")
                self.update_display()
        elif len(current_text) < self.max_length:
            if current_text == "0":
                self.entry.delete(0, "end")
            self.entry.insert("end", value)
            self.update_display()
        
        self.entry.configure(state="readonly")
    
    def clear_entry(self):
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.update_display()
        self.entry.configure(state="readonly")
    
    def close_numpad(self):
        self.entry.configure(state="normal")
        if len(self.entry.get().strip()) == 0:
            self.entry.insert(0, "0")
        self.entry.configure(state="readonly")
        self.destroy()


# แก้ไข Frame4 - เปลี่ยนฟังก์ชัน create_input

class Frame4(ctk.CTkFrame):
    # ... (ส่วนอื่นๆ ไม่ต้องแก้)
    
    def __init__(self, parent, controller):
        super().__init__(parent, width=1024, height=800)
        self.controller = controller
     
        bg_image = Image.open(f"{PATH}image/pageheath.png").resize((1024, 800), Image.Resampling.LANCZOS) 
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = ctk.CTkFrame(self, width=800, height=400, corner_radius=0, fg_color="#FFFFFF", bg_color="#000001") 
        frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(
            frame,
            text="วัดความดันและชีพจร",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)

        page_title = ctk.CTkLabel(
            navbar,
            text="วัดความดันและชีพจร",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)

        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )

        back_button = ctk.CTkButton(
            navbar,
            image=self.reply_ctk_image,
            text="ย้อนกลับ",
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

        # ====== Input ======
        self.systolic_var = ctk.StringVar()
        self.diastolic_var = ctk.StringVar()
        self.pulse_var = ctk.StringVar()

        # ⭐ แก้ไขฟังก์ชัน create_input ให้มี Numpad
        def create_input(label_text, var, row):
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 22), text_color="black")
            label.grid(row=row, column=0, padx=20, pady=(10, 0), sticky="w")
            
            # สร้าง frame สำหรับ entry + ปุ่ม numpad
            input_frame = ctk.CTkFrame(frame, fg_color="transparent")
            input_frame.grid(row=row+1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
            
            entry = ctk.CTkEntry(
                input_frame, 
                textvariable=var, 
                width=500, 
                height=60,
                font=("Arial", 22), 
                fg_color="white", 
                text_color="black",
                state="readonly"
            )
            entry.pack(side="left", padx=(0, 10))
            
            numpad_btn = ctk.CTkButton(
                input_frame,
                text="⌨",
                font=("Arial", 32),
                width=80,
                height=60,
                corner_radius=15,
                fg_color="#2563EB",
                hover_color="#1D4ED8",
                command=lambda: HealthNumpad(self, entry, max_length=3)
            )
            numpad_btn.pack(side="left")

        create_input("ความดันสูงสุด (Systolic)", self.systolic_var, 1)
        create_input("ความดันต่ำสุด (Diastolic)", self.diastolic_var, 3)
        create_input("ชีพจร (Pulse)", self.pulse_var, 5)

        # ====== ปุ่ม ======
        def clear_data():
            self.systolic_var.set("")
            self.diastolic_var.set("")
            self.pulse_var.set("")
            print("ข้อมูลถูกล้างเรียบร้อยแล้ว")

        def save_and_go_home():
            if len(self.systolic_var.get().strip()) == 0 and len(self.diastolic_var.get().strip()) == 0 and len(self.pulse_var.get().strip()) == 0:
                print('กรุณากรอกข้อมูลให้ครบถ้วน')
                return
            
            # แสดงหน้าดาวโหลด
            controller.show_loading("กำลังบันทึกข้อมูลและสร้างคำแนะนำ...", "กรุณารอสักครู่")
            
            def save_advice_thread():
                try:
                    ai_advice = ai.save_advice(
                        self.controller.user['id'],
                        self.systolic_var.get(),
                        self.diastolic_var.get(),
                        self.pulse_var.get()
                    )
                    if ai_advice['status']:
                        self.controller.advice = ai_advice['Advice']
                        user_report = (
                            f"📊 รายงานสุขภาพ\n"
                            f"👤 ชื่อผู้ใช้งาน: {self.controller.user['firstname_th']} - {self.controller.user['lastname_th']}\n"
                            f"💓 ความดันสูง: {self.systolic_var.get()}\n"
                            f"💓 ความดันต่ำ: {self.diastolic_var.get()}\n"
                            f"💓 ชีพจร: {self.pulse_var.get()}" 
                        )
                    
                        sendtoLine(self.controller.user['token_line'],self.controller.user['group_id'],user_report)
                        sendtoLine(self.controller.user['token_line'],self.controller.user['group_id'],ai_advice['Advice'])
                        self.controller.notifier.show_notification("บันทึกคำแนะนำสำเร็จ", success=True)
                        def show_ai_gen():
                            controller._previous_frame_class = None
                            controller.hide_loading()
                            controller.show_frame(AIgen)
                        controller.after(0, show_ai_gen)
                    else:
                        self.controller.notifier.show_notification(ai_advice['message'], success=False)
                        controller.after(0, controller.hide_loading)
                except Exception as e:
                    self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
                    controller.after(0, controller.hide_loading)

            threading.Thread(target=save_advice_thread, daemon=True).start()

            
        save_button = ctk.CTkButton(frame, text="บันทึกและกลับสู่หน้าหลัก", width=300, height=70, fg_color=force_color, 
                                    text_color="white", font=("Arial", 24, "bold"), command=save_and_go_home)

        clear_button = ctk.CTkButton(frame, text="ล้างข้อมูล", width=200, height=70, fg_color=bottom_hover,
                                     text_color="white", font=("Arial", 24, "bold"), command=clear_data)

        save_button.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        clear_button.grid(row=7, column=1, padx=20, pady=10, sticky="ew")





class AIgen(ctk.CTkFrame):
    def on_show(self):
        # modelการพูด
        print("AIgen is now visible")
        self.label.configure(text=self.controller.advice)

        tts = gTTS(text=self.controller.advice, lang='th')
        tts.save("thai_voice.mp3")

        if not mixer.get_init():
            mixer.init()

        if mixer.music.get_busy():
            mixer.music.stop()

        mixer.music.load("thai_voice.mp3")
        mixer.music.play()

        def delete_file():
            while mixer.music.get_busy():
                time.sleep(0.1) 
            mixer.quit()
            try:
                os.remove("thai_voice.mp3")
            except Exception as e:
                print("ลบไฟล์ไม่สำเร็จ:", e)

        threading.Thread(target=delete_file).start()    

    def stop_and_go_home(self):
        try:
            if mixer.get_init() and mixer.music.get_busy():
                mixer.music.stop()
            mixer.quit()
            if os.path.exists('thai_voice.mp3'):
                os.remove("thai_voice.mp3")  
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        
        self.controller.show_frame(HomePage)

    def __init__(self, parent, controller):
        super().__init__(parent, width=1024, height=800)
        self.controller = controller
        
        bg_image = Image.open(f"{PATH}image/report.png").resize((1024, 800), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # === Parent Frame ===
        parent_frame = ctk.CTkFrame(
            self, width=750, height=450, corner_radius=0,
            fg_color="#FFFFFF"
        )
        parent_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # === หัวข้อกล่อง ===
        title_label = ctk.CTkLabel(
            parent_frame,
            text="คำแนะนำจาก AI",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )
        title_label.pack(pady=(15, 5))   # เว้นระยะด้านบนเล็กน้อย

        # === Scrollable Child ===
        frame = ctk.CTkScrollableFrame(
            parent_frame, width=700, height=360, corner_radius=20, fg_color="#FFFFFF"
        )
        frame.pack(pady=(0, 10))  # ขยับลงเล็กน้อยให้สวยงาม

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)

        page_title = ctk.CTkLabel(
            navbar,
            text="คำแนะนำจาก AI",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)

        back_button = ctk.CTkButton(navbar, text="ยืนยัน", width=100, height=50, corner_radius=BUTTON_RADIUS,
                                    fg_color=force_color, hover_color=bottom_hover, text_color="white",
                                    font=("Arial", 26, "bold"),
                                    command=self.stop_and_go_home)
        back_button.pack(side="right", padx=10, pady=10)

        self.systolic_var = ctk.StringVar()
        self.diastolic_var = ctk.StringVar()
        self.pulse_var = ctk.StringVar()

        # === Label ด้านใน Scrollable Frame ===
        self.label = ctk.CTkLabel(
            frame,
            text='',
            font=("Arial", 20),
            text_color="#000000",
            justify="left",
            wraplength=680  
        )
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

         
        





