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

class Frame2(ctk.CTkFrame): 
    def on_show(self):
        print("Frame2 is now visible")
        self.load_medications()

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(bg_color="#8dc5fc")

        # Background
        bg_image = Image.open(f"{PATH}image/drugs.png").resize((1024, 800), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)


        page_title = ctk.CTkLabel(
            navbar,
            text="ตารางแสดงข้อมูลยา",
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


class add_Frame(ctk.CTkFrame):
    def on_show(self):
        print("add_Frame is now visible")
        show_onboard()
        # เพิ่มส่วนนี้
        def on_frame_click(event):
            widget = event.widget
            if not isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
                hide_onboard()

    def __init__(self, parent, controller):
        super().__init__(parent, width=1024, height=600)
        self.controller = controller
        self.configure(fg_color="#FFFFFF")

        # === Background ===
        bg_image = Image.open(f"{PATH}image/drugs.png").resize((1024, 800), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)

        page_title = ctk.CTkLabel(
            navbar,
            text="เพิ่มข้อมูลยา",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )  
        page_title.pack(side="left", padx=20)
        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )
        

        def go_back():
            controller.show_frame(Frame2)

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

        # === Enhanced Parent Frame ===
        parent_frame = ctk.CTkFrame(
            self, width=650, height=400, corner_radius=0,
            fg_color="#FFFFFF"
        )
        parent_frame.place(relx=0.5, rely=0.5, anchor="center")
        #pywinstyles.set_opacity(parent_frame, value=0.95, color="#000001")
        parent_frame.pack_propagate(False)
        
        # === Enhanced Scrollable Frame ===
        frame = ctk.CTkScrollableFrame(
            parent_frame, width=600, height=350, corner_radius=20,
            fg_color="#F8F9FA",
            scrollbar_button_color="#E76F51",
            scrollbar_button_hover_color="#D64933"
        )
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)
        
        #pywinstyles.set_opacity(frame, value=1, color="#000001")

        # ----------- Enhanced MedicationApp ----------
        class MedicationApp(ctk.CTkFrame):
            def __init__(self, master=None):
                super().__init__(master, fg_color="transparent")
                self.med_entries = []
                self.create_widgets()
                self.med_entries.append((self.entry_med_name, None))

            def create_widgets(self):
                # Enhanced Title with Icon
                self.label_title = ctk.CTkLabel(
                    self, text="เพิ่มข้อมูลยา", 
                    font=("TH Sarabun New", 40, "bold"), 
                    text_color="#1D3557"
                )
                self.label_title.grid(row=0, column=0, columnspan=2, pady=(15, 25), sticky="w", padx=(220, 20))

                self.lang_button = ctk.CTkButton(
                    self,  # หรือ parent ที่คุณต้องการวางปุ่ม
                    text="TH/EN",
                    width=50,
                    height=50,
                    corner_radius=10,
                    fg_color="#2563EB",
                    hover_color="#1D4ED8",
                    text_color="white",
                    font=("Arial", 10, "bold"),
                    command=toggle_language
                )
                self.lang_button.place(x=500, y=20)  # ปรับตำแหน่งตามต้องการ

                # Subtitle
                self.label_subtitle = ctk.CTkLabel(
                    self, text="กรอกชื่อยาที่ต้องการเพิ่มในระบบ", 
                    font=("TH Sarabun New", 16), 
                    text_color="#6C757D"
                )
                self.label_subtitle.grid(row=0, column=0, columnspan=2, pady=(50, 10), sticky="w", padx=(220, 0))

                # Enhanced Entry Field
                self.entry_med_name = create_entry_with_keyboard(
                    self,
                    placeholder_text="ป้อนชื่อยา...",
                    width=450,
                    height=50,
                    fg_color="#FFFFFF",
                    text_color="#1D3557",
                    font=("TH Sarabun New", 18),
                    corner_radius=15
                )
                self.entry_med_name.grid(row=1, column=0, padx=(0, 10), pady=(0, 15), sticky="w")

                # Enhanced Add Button
                self.add_button = ctk.CTkButton(
                    self, text="+ เพิ่มช่อง", 
                    height=50, width=120, 
                    font=("TH Sarabun New", 16, "bold"),
                    fg_color="#28A745", 
                    hover_color="#218838", 
                    text_color="white",
                    corner_radius=15,
                    command=self.add_medication_entry
                )
                self.add_button.grid(row=1, column=1, padx=(0, 30), pady=(0, 15), sticky="w")

            def add_medication_entry(self):
                row_index = len(self.med_entries) + 2
                
                # ✅ ใช้ create_entry_with_keyboard แทน CTkEntry
                entry = create_entry_with_keyboard(
                    self,
                    placeholder_text="ป้อนชื่อยา...",
                    width=450,
                    height=50,
                    fg_color="#FFFFFF",
                    text_color="#1D3557",
                    font=("TH Sarabun New", 18),
                    corner_radius=15
                )
                entry.grid(row=row_index, column=0, padx=(0, 10), pady=(0, 15), sticky="w")

                # Enhanced delete button
                delete_button = ctk.CTkButton(
                    self, text="ลบ", 
                    height=50, width=120, 
                    fg_color="#DC3545",
                    hover_color="#C82333", 
                    font=("TH Sarabun New", 16, "bold"), 
                    text_color="white",
                    corner_radius=15,
                    command=lambda e=entry: self.remove_medication_entry(e)
                )
                delete_button.grid(row=row_index, column=1, padx=(0, 30), pady=(0, 15), sticky="w")

                self.med_entries.append((entry, delete_button))

                # Add smooth animation effect
                entry.configure(fg_color="#E8F5E8")
                self.after(200, lambda: entry.configure(fg_color="#FFFFFF"))

            def remove_medication_entry(self, entry):
                for i, (e, b) in enumerate(self.med_entries):
                    if e == entry:
                        # Smooth removal animation
                        e.configure(fg_color="#FFE6E6")
                        self.after(150, lambda: self._complete_removal(e, b, i))
                        break

            def _complete_removal(self, entry, button, index):
                entry.grid_remove()
                if button:
                    button.grid_remove()
                self.med_entries.pop(index)

        # เพิ่ม MedicationApp ลงใน Scrollable Frame
        self.med_frame = MedicationApp(master=frame)
        self.med_frame.grid(row=0, column=0, columnspan=2, pady=(20, 0), padx=10)

        # ----------- Enhanced Save Button ----------
        def save_medications():
            new_meds = []
            first_med = self.med_frame.entry_med_name.get()
            if first_med:
                new_meds.append(first_med)
            for entry, _ in self.med_frame.med_entries:
                med_name = entry.get()
                if med_name and med_name != first_med:
                    new_meds.append(med_name)

            if len(new_meds) != 0:
                insert_new_medic = manageMedic.insertMedic(
                    self.controller.user['id'],
                    self.controller.user['device_id'],
                    new_meds
                )
                self.controller.notifier.show_notification(insert_new_medic['message'], success=insert_new_medic['status'])
            else:
                self.controller.notifier.show_notification("กรุณากรอกชื่อยาก่อนบันทึก", success=False)

            go_back()

        # Enhanced Save Button
        add_med_button = ctk.CTkButton(
            frame, 
            text="ยืนยันการเพิ่มยาใหม่และกลับสู่หน้าตาราง",
            fg_color="#007BFF", 
            hover_color="#0056B3", 
            text_color="white",
            width=550, height=60, 
            font=("TH Sarabun New", 20, "bold"),
            corner_radius=20,
            border_width=2,
            border_color="#0056B3",
            command=save_medications
        )
        add_med_button.grid(row=1, column=0, pady=25, padx=0)

        # Add hover animation
        def on_enter(event):
            add_med_button.configure(fg_color="#0056B3", border_color="#004085")
        
        def on_leave(event):
            add_med_button.configure(fg_color="#007BFF", border_color="#0056B3")
            
        add_med_button.bind("<Enter>", on_enter)
        add_med_button.bind("<Leave>", on_leave)










class MedicationApp(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.selected_time_periods = {} 
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        bg_image = Image.open(f"{PATH}image/time.png").resize((1024, 800), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        self.navbar.pack(side="bottom", fill="x",pady=50)


        self.page_title = ctk.CTkLabel(
            self.navbar,
            text="กำหนดช่วงเวลาและยา",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black"
        )   
        
        self.page_title.pack(side="left", padx=20)
        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )
        
        self.back_button = ctk.CTkButton(
            self.navbar,
           image=self.reply_ctk_image,   # ใช้ image แทน text
            text="ย้อนกลับ",                # ไม่ใส่ข้อความ
            width=100, 
            height=50, 
            corner_radius=25,
            fg_color="#2563EB", 
            hover_color="#1D3557", 
            text_color="white",
            font=("Arial", 24, "bold"), 
            command=self.go_back
        )
        self.back_button.pack(side="right", padx=10, pady=10)



        self.save_button = ctk.CTkButton(self.navbar, text="บันทึก", corner_radius=20, width=100, height=50, 
            fg_color="#2D6A4F", text_color="white", hover_color="#1B4332",
            font=("Arial", 24, "bold"), 
            border_width=2, border_color="#1B4332", command=self.save_and_go_to_frame1)
        
        # ⭐️ [แก้ไข] ปุ่ม save_button ควร pack หลังจาก back_button
        # (โค้ดเดิมของคุณ pack back_button สองครั้ง)
        self.save_button.pack(side="right", padx=10, pady=10) 

        self.time_options = ["เช้า", "กลางวัน", "เย็น", "ก่อนนอน"]

        # === Parent Frame ===
        parent_frame = ctk.CTkFrame(
            self, width=750, height=450, corner_radius=0,
            fg_color="#FFFFFF", bg_color="#000001"
        )
        parent_frame.place(relx=0.5, rely=0.5, anchor="center")
        parent_frame.pack_propagate(False)  # กันไม่ให้ขนาดเปลี่ยนตามลูก
        
        # === Scrollable Frame ข้างใน ===
        self.frame_container = ctk.CTkScrollableFrame(
            parent_frame, width=750, height=400, corner_radius=20,
            fg_color="#FFFFFF"
        )
        self.frame_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.current_page = 0
        self.pages = []
        self.time_entries = {}    # เก็บเวลาของแต่ละมื้อ
        self.time_selects = {}    # เก็บช่วงเวลาของแต่ละมื้อ
        self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}   # เก็บข้อมูลยาแต่ละมื้อ
        self.med_combos = {}      # เก็บ reference ของ combobox ยา
        self.entry_frames = {}

    def on_show(self):
        """Called when the frame is displayed"""
        print("MedicationApp is now visible")
        self.update_meal_config()
    
    # ⭐️ [FIX 1] เพิ่มฟังก์ชันนี้ที่ขาดไป (ที่ on_show เรียก) ⭐️
    def update_meal_config(self):
        """
        ฟังก์ชันนี้ถูกเรียกโดย on_show เพื่อเริ่มโหลดข้อมูลยา
        """
        # (เราจำเป็นต้องแสดง Loading ที่นี่)
        self.controller.show_loading("กำลังโหลดข้อมูลยา...", "กรุณารอสักครู่")
        
        # เริ่ม Thread (ที่คุณสร้างไว้แล้ว)
        threading.Thread(target=self.update_meal_config_thread, daemon=True).start()

        
    def update_meal_config_thread(self):
        try:
            # 1. ตรวจสอบสถานะเน็ต
            network_status = self.controller.network_status_var.get()
            medicine_data = None
            
            if network_status == "online":
                # 2a. ถ้าออนไลน์: ดึงข้อมูลใหม่จาก Server
                print("Meds (App): Online - Fetching from server...")
                api_result = manageMedic.getMedicine(
                    self.controller.user['id'], self.controller.user['device_id']
                )
                if api_result['status']:
                    medicine_data = api_result['Data']
                    # บันทึกข้อมูลใหม่ลงแคช
                    with open(self.controller.MEDICINE_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(medicine_data, f, indent=4)
                else:
                    self.controller.notifier.show_notification(api_result['message'], success=False)

            else:
                # 2b. ถ้าออฟไลน์: โหลดจากไฟล์แคช
                print(f"Meds (App): Offline - Loading from {self.controller.MEDICINE_CACHE_FILE}")
                if os.path.exists(self.controller.MEDICINE_CACHE_FILE):
                    try:
                        with open(self.controller.MEDICINE_CACHE_FILE, "r", encoding="utf-8") as f:
                            medicine_data = json.load(f)
                    except Exception as e:
                        print(f"Meds (App): Error reading cache file: {e}")
                        self.controller.notifier.show_notification("Offline: ไม่สามารถอ่านไฟล์แคชยา", success=False)
                else:
                    self.controller.notifier.show_notification("Offline: ไม่พบข้อมูลยาที่บันทึกไว้", success=False)

            # 3. ประมวลผลข้อมูล (ไม่ว่าจะมาจาก online หรือ offline)
            if medicine_data is not None:
                self.medicine_map = {
                    med["medicine_name"]: med["medicine_id"]
                    for med in medicine_data
                }
                with open("meal_config.json", "r") as f:
                    meal_config = json.load(f)
                    self.num_meals = int(meal_config["meals"].split()[0])
                
                self.controller.notifier.show_notification("โหลดข้อมูลยาสำเร็จ", success=True)
                self.controller.after(0, self.process_meal_config_update)
            else:
                # ถ้าไม่สำเร็จ (เช่น offline + ไม่มีแคช)
                self.controller.notifier.show_notification("ไม่สามารถโหลดข้อมูลยาได้", success=False)
                self.controller.after(0, self.controller.hide_loading)

        except Exception as e:
            self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
            self.controller.after(0, self.controller.hide_loading)

    
    # ⭐️ [FIX 2 & 3] แก้ไขฟังก์ชันนี้ (ล้าง UI) และจัดย่อหน้า ⭐️
    def process_meal_config_update(self):
        """ประมวลผลการอัปเดต meal config หลังจากโหลดเสร็จ"""
        try:
            # 1. ทำลาย Widgets เก่าทั้งหมดใน frame_container ⭐️
            for widget in self.frame_container.winfo_children():
                widget.destroy()

            # 2. ล้างค่าทั้งหมด และรีเซ็ต Page ⭐️
            self.pages.clear()
            self.current_page = 0
            
            self.selected_time_periods = {}
            self.time_entries = {}
            self.time_selects = {}
            self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}
            self.med_combos = {}
            self.entry_frames = {}
            # ----------------------------------------------------

            for i in range(0, self.num_meals, 2):
                page = ctk.CTkFrame(self.frame_container, fg_color=back_color, bg_color=back_color)
                self.pages.append(page)

            self.show_page(self.current_page)

            if self.num_meals > 2:
                if not hasattr(self, 'next_button'):
                    self.next_button = ctk.CTkButton(self.navbar, text="ถัดไป", corner_radius=20, width=100, height=50, 
                                                     fg_color=force_color, text_color="white", hover_color="#002299",
                                                     font=("Arial", 24, "bold"),  command=self.next_page)
                self.next_button.pack(side="right", padx=10, pady=10)
            else:
                if hasattr(self, 'next_button'):
                    self.next_button.pack_forget()
            
            # ซ่อนหน้าดาวโหลด
            self.controller.hide_loading()
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
            self.controller.hide_loading()

        if not hasattr(self, 'back_button'):
            self.back_button2 = ctk.CTkButton(self.navbar, text="ย้อนกลับ",  corner_radius=20, width=100, height=50, 
                                               fg_color=force_color, text_color="white", hover_color="#002299",
                                               font=("Arial", 24, "bold"),  command=lambda: self.controller.show_frame(MedicationApp))
            self.back_button2.pack(side="right", padx=10, pady=10)

    def show_page(self, page_index):
        for widget in self.frame_container.winfo_children():
            widget.pack_forget()

        self.pages[page_index].pack(fill="both", expand=True)
    
        if page_index == 1 and hasattr(self, 'next_button'):
            self.next_button.pack_forget()
        elif page_index == 0 and hasattr(self, 'next_button'):
            self.next_button.pack(side="right", padx=5, pady=5)

        if page_index == 1:
            if not hasattr(self, 'back_button2'):
                self.back_button2 = ctk.CTkButton(
                    self.navbar, text="ย้อนกลับ",  corner_radius=20, width=100, height=50, 
                    fg_color=force_color, text_color="white", hover_color="#002299",
                    font=("Arial", 24, "bold"), command=lambda: self.controller.show_frame(MedicationApp)
                )
            self.back_button2.pack(side="right", padx=5, pady=5)
        elif hasattr(self, 'back_button2'):
            self.back_button2.pack_forget()

        if (page_index == len(self.pages) - 1) or self.num_meals <= 2:
            self.save_button.pack(side="right", padx=5, pady=5)
        else:
            self.save_button.pack_forget()

        self.pages[page_index].pack(fill="both", expand=True)

        for i in range(page_index * 2, min((page_index + 1) * 2, self.num_meals)):      
            meal_name = self.time_options[i]

            meal_label = ctk.CTkLabel(
                self.pages[page_index], text=f"มื้อที่ {i + 1}",
                font=("Arial", 32, "bold"), bg_color=back_color,  
                fg_color="white", text_color="black", width=250, height=50, corner_radius=8
            )
            meal_label.grid(row=0, column=i % 2, padx=40, pady=(15, 8), sticky="w")

            time_var = ctk.StringVar()
            time_var.trace_add("write", lambda *args, var=time_var: self.format_time(var))

            time_entry = ctk.CTkEntry(
                self.pages[page_index], width=250, height=50,
                font=("Arial", 28), fg_color="white", text_color="black",
                placeholder_text="เวลา (HH:MM)", validate="key", textvariable=time_var
            )
            time_entry.grid(row=1, column=i % 2, padx=40, pady=(0, 8), sticky="w")
            time_entry.bind("<Button-1>", lambda event, e=time_entry: self.open_numpad(e)) 
            self.time_entries[meal_name] = time_entry

            time_select = ctk.CTkComboBox(
                self.pages[page_index], values=self.time_options, width=250, height=50,
                font=("Arial", 24), fg_color="white", text_color=word_color, 
                dropdown_font=("Arial", 24)
            )
            time_select.grid(row=3, column=i % 2, padx=40, pady=(0, 0), sticky="w")
            time_select.set("เลือกช่วงเวลา")

            time_select.configure(command=lambda value, meal=meal_name, col=i%2:self.on_time_period_select(page_index, col, value, meal))

            self.time_selects[meal_name] = time_select

            self.entry_frames[meal_name] = ctk.CTkFrame(self.pages[page_index], fg_color=back_color)
            self.entry_frames[meal_name].grid(row=4, column=i % 2, padx=0, pady=8, sticky="n")

            add_button = ctk.CTkButton(
                self.entry_frames[meal_name], text="+ เพิ่มยา", width=250, height=50,
                fg_color=force_color, text_color='white', font=("Arial", 24), 
                command=lambda m=meal_name: self.add_medication_entry(m)
            )
            add_button.pack(pady=8)
        self.update_time_periods_availability(page_index)

    def open_numpad(self, entry):
        # Local import to avoid circular dependency
        from views.schedule_setup_view import TimeNumpad
        TimeNumpad(self, entry)

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.show_page(self.current_page)


    def add_medication_entry(self, meal):
        entry_frame = self.entry_frames[meal]

        row = ctk.CTkFrame(entry_frame, fg_color=back_color)
        row.pack(pady=5)


        combo_values = list(self.medicine_map.keys())

        med_combo = ctk.CTkComboBox(
            row,
            values=combo_values,
            width=240,
            height=45,
            fg_color="white",
            text_color="black",
            font=("Arial", 20),
            dropdown_font=("Arial", 20)
        )
        med_combo.grid(row=0, column=0, padx=(0, 8), sticky="w")

        med_combo.set("เลือกยา")

        if meal not in self.med_combos:
            self.med_combos[meal] = []
        self.med_combos[meal].append(med_combo)

        delete_button = ctk.CTkButton(
            row,
            text="ลบ",
            width=60,
            height=45,
            fg_color="red",
            text_color="white",
            font=("Arial", 18),
            hover_color="#990000",
            command=lambda: self.remove_medication_entry(meal, row,med_combo)
        )
        delete_button.grid(row=0, column=1, sticky="w")

        self.med_entries[meal].append((row, med_combo, delete_button))
        
    def on_time_period_select(self, page_index, column_index, selected_value, meal_name):
        """เมื่อผู้ใช้เลือกช่วงเวลา"""
        # บันทึกค่าที่เลือก
        self.selected_time_periods[page_index][column_index] = selected_value
        
        # อัปเดตสถานะ dropdown ทั้งหมด
        self.update_time_periods_availability(page_index)
        
        # อัปเดต dropdown ในหน้าอื่นด้วย (ถ้ามี)
        for page_idx in self.selected_time_periods:
            if page_idx != page_index:
                self.update_time_periods_availability(page_idx)
    
    def update_time_periods_availability(self, page_index):
        """อัปเดตสถานะของ dropdown ช่วงเวลาในหน้าเฉพาะ"""
        # รวบรวมช่วงเวลาที่ถูกเลือกแล้วในทุกหน้า
        all_selected_periods = []
        for page_idx, selections in self.selected_time_periods.items():
            all_selected_periods.extend(selections.values())
        
        # สำหรับแต่ละ dropdown ในหน้านี้
        for i in range(page_index * 2, min((page_index + 1) * 2, self.num_meals)):
            meal_name = self.time_options[i]
            time_select = self.time_selects[meal_name]
            current_value = time_select.get()
            column_index = i % 2
            
            # สร้างรายการตัวเลือกใหม่ (ปิดการใช้งานตัวเลือกที่ถูกเลือกไปแล้ว)
            new_values = []
            for period in self.time_options:
                # ถ้าช่วงเวลานี้ถูกเลือกในที่อื่น และไม่ใช่ค่าปัจจุบันของ dropdown นี้
                if period in all_selected_periods and period != current_value:
                    new_values.append(f"║ {period} ║")  # แสดงว่าไม่สามารถเลือกได้
                else:
                    new_values.append(period)
            
            # อัปเดตค่าที่แสดงใน dropdown
            time_select.configure(values=new_values)
            
            # ตั้งค่าปัจจุบันใหม่ (เพื่อให้แสดงถูกต้อง)
            if current_value in new_values:
                time_select.set(current_value)
            else:
                # ถ้าค่าปัจจุบันไม่สามารถเลือกได้ (ถูกเลือกในที่อื่น) ให้รีเซ็ต
                if current_value != "เลือกช่วงเวลา" and current_value not in [f"║ {p} ║" for p in self.time_options]:
                    time_select.set("เลือกช่วงเวลา")
                    # ลบออกจาก selected_time_periods
                    if page_index in self.selected_time_periods and column_index in self.selected_time_periods[page_index]:
                        del self.selected_time_periods[page_index][column_index]

    def remove_medication_entry(self, meal, row, med_combo):
        for entry in self.med_entries[meal]:
            if entry[0] == row:
                self.med_entries[meal].remove(entry)
                break
            
        if meal in self.med_combos and med_combo in self.med_combos[meal]:
                    self.med_combos[meal].remove(med_combo)
        row.destroy()     

    def format_time(self, time_var):
        text = time_var.get().replace(":", "")
        if len(text) > 4:
            text = text[:4]
        formatted = ""

        if len(text) == 2:
            formatted = text[:2] + ":" + text[2:]
        else:
            formatted = text

        if len(text) == 4:
            h, m = int(text[:2]), int(text[2:])
            if h > 23:
                h = 23
            if m > 59:
                m = 59
            formatted = f"{h:02}:{m:02}"

        time_var.set(formatted)

    def validate_input(self, text):
        return text.isdigit() or text == ""

    def go_back(self):
        self.controller.show_frame(MedicationScheduleFrame)

    def save_and_go_to_frame1(self):
       
        meal_data = {}
        for meal_name, entry_frame in self.entry_frames.items():
            if meal_name not in self.time_entries or meal_name not in self.time_selects:
                continue
            
            time_period = self.time_selects[meal_name].get()
            time_value = self.time_entries[meal_name].get()
            
          
            if time_period == "เลือกช่วงเวลา" and (time_value or (meal_name in self.med_combos and self.med_combos[meal_name])):
                 self.controller.notifier.show_notification(f"กรุณาเลือกช่วงเวลาสำหรับ {meal_name}", success=False)
                 return


            if time_period == "เลือกช่วงเวลา":
                continue

            med_ids = []
            if meal_name in self.med_combos:
                for med_combo in self.med_combos[meal_name]:
                    med_name = med_combo.get()
                    if med_name in self.medicine_map and med_name != "เลือกยา":
                        med_ids.append(self.medicine_map[med_name])
            
            meal_data[time_period] = {
                "time": time_value if time_value else "00:00",
                "medications": med_ids
            }
        
        all_selected_periods = []
        for page_idx, selections in self.selected_time_periods.items():
            all_selected_periods.extend(selections.values())

        selected_periods = [p for p in all_selected_periods if p and p != "เลือกช่วงเวลา"]
        if len(selected_periods) != len(set(selected_periods)):
            self.controller.notifier.show_notification("มีช่วงเวลาซ้ำกัน กรุณาตรวจสอบอีกครั้ง", success=False)
            return
       
        network_status = self.controller.network_status_var.get()
        QUEUE_FILE = "offline_schedule_queue.json" 

        if network_status == "online":

            print("Meds (App): Online - Sending meal data to server...")
            try:
                insert_meal = set_dispensing_time.set_meal(
                    self.controller.user['device_id'],
                    self.controller.user['id'],
                    meal_data
                )
                
                if insert_meal['status']:
                    self.controller.notifier.show_notification(insert_meal['message'], success=True)
                    self.update_local_time_data_cache(meal_data)
                    self.controller.show_frame(HomePage)
                else:
                    self.controller.notifier.show_notification(insert_meal['message'], success=False)
            
            except requests.exceptions.RequestException as e:
                print(f"Meds (App): Failed to send data (Server Error/Timeout): {e}")
                self.save_meal_to_queue_and_cache(QUEUE_FILE, meal_data)
                self.controller.notifier.show_notification("เซิร์ฟเวอร์ขัดข้อง: บันทึกข้อมูลไว้ในเครื่อง", success=False)
                self.controller.show_frame(HomePage) 

        else:
            print("Meds (App): Offline - Saving meal data to local queue and cache...")
            try:
                self.save_meal_to_queue_and_cache(QUEUE_FILE, meal_data)
                self.controller.notifier.show_notification("Offline: บันทึกข้อมูลตั้งค่าเวลาไว้ในเครื่อง", success=True)
                self.controller.show_frame(HomePage)
            except Exception as e:
                self.controller.notifier.show_notification(f"ผิดพลาด: บันทึกไฟล์ไม่สำเร็จ: {e}", success=False)



    def save_meal_to_queue_and_cache(self, queue_file, meal_data):

        new_task = {
            "type": "set_meal", 
            "payload": {
                "device_id": self.controller.user['device_id'],
                "user_id": self.controller.user['id'],
                "meal_data": meal_data 
            },
            "timestamp": datetime.now().isoformat()
        }

        queue = []
        if os.path.exists(queue_file):
            try:
                with open(queue_file, "r", encoding="utf-8") as f:
                    queue = json.load(f)
                if not isinstance(queue, list): queue = []
            except json.JSONDecodeError:
                queue = []
        
        queue.append(new_task)
        try:
            with open(queue_file, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4)
            print(f"Task 'set_meal' successfully added to {queue_file}")
        except Exception as e:
            print(f"Error writing to {queue_file}: {e}")
            raise 
        self.update_local_time_data_cache(meal_data)

    def update_local_time_data_cache(self, meal_data):
        """
        แปลงข้อมูล meal_data (dict) ให้อยู่ในรูปแบบ list (ที่ HomePage ใช้อ่าน)
        แล้วบันทึกลง "time_data.json"
        """
        CACHE_FILE = "time_data.json"
        
        # Maps (จำเป็นสำหรับการแปลง)
        meal_key_map = {
            'เช้า': 'bf',
            'กลางวัน': 'lunch',
            'เย็น': 'dn',
            'ก่อนนอน': 'bb'
        }
        # สร้าง map กลับด้าน (ID -> Name) จาก self.medicine_map ที่โหลดมาตอน on_show
        if not hasattr(self, 'medicine_map'):
             print("Error: medicine_map is missing. Cannot update cache.")
             return

        reverse_medicine_map = {v: k for k, v in self.medicine_map.items()}

        new_cache_data = [] # นี่คือ list ที่จะบันทึกลง time_data.json
        
        for meal_name_th, data in meal_data.items():
            if meal_name_th not in meal_key_map:
                continue # ข้ามถ้าเป็น "เลือกช่วงเวลา"
            
            # สร้าง object meal
            meal_entry = {
                "source": meal_key_map.get(meal_name_th), # "เช้า" -> "bf"
                "time": data.get("time", "00:00"),
                "medicine_1": None,
                "medicine_2": None,
                "medicine_3": None,
                "medicine_4": None
            }
            
            # แปลง med_ids กลับเป็นชื่อ
            med_ids = data.get("medications", [])
            for i, med_id in enumerate(med_ids):
                if i < 4: # รองรับสูงสุด 4 ยา
                    med_name = reverse_medicine_map.get(med_id, "Unknown")
                    meal_entry[f"medicine_{i+1}"] = med_name
            
            new_cache_data.append(meal_entry)
        
        # 3. เขียนทับไฟล์ time_data.json
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(new_cache_data, f, indent=4)
            print(f"Meds (App): Updated {CACHE_FILE} cache successfully.")
            
            # 4. อัพเดท last_known_schedule_data ใน controller เพื่อให้การบันทึกประวัติทำงานได้ทันที
            if hasattr(self.controller, 'last_known_schedule_data'):
                self.controller.last_known_schedule_data = {'data': new_cache_data}
                print(f"Meds (App): Updated controller.last_known_schedule_data")
        except Exception as e:
            print(f"Meds (App): Failed to write {CACHE_FILE}: {e}")        
    def on_show(self):
        print("MedicationApp is now visible")
        self.update_meal_config()

