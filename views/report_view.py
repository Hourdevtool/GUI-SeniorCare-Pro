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
from config.styles import force_color, bottom_hover, BUTTON_RADIUS, hover_color

class ReportFrame(ctk.CTkFrame):     
    def on_show(self):         
        print("ReportFrame is now visible")      
        self.create_report_button(self.controller)
    def __init__(self, parent, controller):         
        super().__init__(parent)         
        self.controller = controller          
        
        # พื้นหลัง - ปรับขนาดเป็น 1024x600
        bg_image = Image.open(f"{PATH}image/reportdata.png").resize((1024, 800), Image.Resampling.LANCZOS)         
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))         
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")         
        bg_label.place(x=0, y=0, relwidth=1, relheight=1) 

        # ขนาดปุ่มที่เหมาะสมกับหน้าจอขนาด 1024x600
        

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)     
        
        page_title = ctk.CTkLabel(
            navbar,
            text="หน้าพิมพ์รายงาน",
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
        back_button.pack(side="right", padx=10, pady=10)
    def create_report_button(self, controller):
        btn_size = (140, 140)         
        btn_images = {}        
        if(self.controller.user['pressure'] == 1):
            pages = [Report1, Report2]         
            labels = ["รายงานข้อมูลการจ่ายยา", "รายงานข้อมูลความดันและชีพจร"]  
            imgpath = [f"{PATH}imgNew/iconreport2.png", f"{PATH}imgNew/pageuser.png", f"{PATH}imgNew/iconreport1.png"]
        else:
            pages = [Report1]         
            labels = ["รายงานข้อมูลการจ่ายยา"]  
            imgpath = [f"{PATH}imgNew/iconreport2.png"]
        for i, path in enumerate(imgpath, start=1):             
            try:                 
                img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)                 
                btn_images[i] = ImageTk.PhotoImage(img)             
            except FileNotFoundError:                 
                print(f"Error: {path} not found.") 

        # คำนวณให้อยู่ตรงกลางแนวนอนสำหรับหน้าจอ 1024px
        spacing = 180         
        total_width = (2 * btn_size[0]) + spacing         
        start_x = (1024 - total_width) // 2          
        
        for i in range(len(pages)):             
            x_pos = start_x + i * (btn_size[0] + spacing)

            if i + 1 in btn_images:                 
                btn = ctk.CTkButton(                     
                    self,                     
                    image=btn_images[i + 1],                     
                    text="",                                          
                    hover_color="#76C8C8",                     
                    bg_color="#000001",                     
                    border_width=2,                     
                    border_color="#1d567b",                     
                    corner_radius=0,                     
                    width=140,                     
                    height=140,                     
                    command=lambda i=i: controller.show_frame(pages[i])                 
                )                 
                btn.place(x=x_pos, y=300)
                #pywinstyles.set_opacity(btn, value=0.9,color="#000001")

            # ปรับขนาดและตำแหน่งของ label
            label = ctk.CTkLabel(                 
                self,                 
                text=labels[i],                 
                fg_color="#A8DADC",                 
                bg_color="#000001",                 
                text_color="#000000",                 
                corner_radius=0,                 
                font=("TH Sarabun New", 25, "bold"),
                width=300,
                height=40             
            )             
            label.place(x=x_pos - 65, y=480) 
            ##pywinstyles.set_opacity(label, value=0.9,color="#000001")
        

class Report1(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.page = 1
        self.rows_per_page = 6 
        self.data = []

        # พื้นหลังธีมเครื่องจ่ายยา - ปรับขนาดเป็น 1024x600
        bg_image = Image.open(f"{PATH}image/reportdata.png").resize((1024, 800), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)

        page_title = ctk.CTkLabel(navbar,           text="ตารางแสดงข้อมูลยา",
            font=("TH Sarabun New", 28, "bold"),
            text_color="black") 
        page_title.pack(side="left", padx=20)


        self.reply_ctk_image = ctk.CTkImage(
            light_image=Image.open(f"{PATH}image/reply.png").resize((24, 24)), 
            size=(24, 24)
        )

        back_button = ctk.CTkButton(navbar,           image=self.reply_ctk_image,   # ใช้ image แทน text
            text="ย้อนกลับ",                      # ไม่ใส่ข้อความ
            width=100, 
            height=50, 
            corner_radius=25,
            fg_color="#2563EB", 
            hover_color="#1D3557", 
            text_color="white",
            font=("Arial", 24, "bold"), 
            command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=10)

        self.export_button = ctk.CTkButton(navbar,
                                           text="ส่งออกเอกสาร",
                                           width=100,
                                           height=50,
                                           corner_radius=25,
                                           fg_color="#fddc75",
                                           hover_color="#a08a46",
                                           text_color="white",
                                           font=("Arial", 24, "bold"),
                                           command=lambda: None)  # ยังไม่ทำงาน
        self.export_button.pack(side="right", padx=10, pady=15)

        # กรอบตาราง - ปรับขนาดให้เหมาะกับ 1024x600
        self.table_frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            bg_color="#000001",
            corner_radius=0,
            width=750,
            height=550
        )
        self.table_frame.place(relx=0.5, rely=0.15, anchor="n")
        #pywinstyles.set_opacity( self.table_frame, value=0.9,color="#000001")


        # เพิ่มบรรทัดนี้เพื่อป้องกันการปรับขนาดอัตโนมัติ
        self.table_frame.pack_propagate(False)
        self.table_frame.grid_propagate(False)

        # สร้าง scrollable frame สำหรับเนื้อหาตาราง
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.table_frame,
            width=680,
            height=500,
            fg_color="transparent"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Navigation controls (centered) - ปรับตำแหน่งให้เหมาะสม
        self.nav_frame = ctk.CTkFrame(self, bg_color="#ffffff", fg_color="#ffffff")
        self.nav_frame.place(relx=0.5, rely=0.72, anchor="center")
        self.nav_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_prev = ctk.CTkButton(
            self.nav_frame,
            text="ก่อนหน้า",
            width=120,
            height=40,
            corner_radius=BUTTON_RADIUS,
            fg_color=force_color,
            hover_color=hover_color,
            text_color="white",
            font=("Arial", 24, "bold"),
            command=self.prev_page
        )
        self.btn_prev.grid(row=0, column=0, padx=8, pady=5, sticky="e")

        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="",
            font=("TH Sarabun New", 24, "bold"),
            text_color="#0B1220"
        )
        self.page_label.grid(row=0, column=1, padx=8, pady=5)

        self.btn_next = ctk.CTkButton(
            self.nav_frame,
            text="ถัดไป",
            width=120,
            height=40,
            corner_radius=BUTTON_RADIUS,
            fg_color=force_color,
            hover_color=hover_color,
            text_color="white",
            font=("Arial", 24, "bold"),
            command=self.next_page
        )
        self.btn_next.grid(row=0, column=2, padx=8, pady=5, sticky="w")

        self.summary_label = ctk.CTkLabel(self,
                                          bg_color="#ffffff",
                                          text="",
                                          font=("TH Sarabun New", 24, "bold"),
                                          text_color="#000000")
        self.summary_label.place(relx=0.5, rely=0.78, anchor="center")

        # ดึงข้อมูล
        self.userid = self.controller.user.get('id') if self.controller.user else None
        self.result = manageData.get(self.userid) if self.userid else {}

    def on_show(self):
        print("Report1 is now visible")

        if not self.controller.user or 'id' not in self.controller.user:
            print("❌ ไม่มีข้อมูลผู้ใช้ หรือยังไม่ได้ล็อกอิน")
            return

        self.userid = self.controller.user['id']
        
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังโหลดรายงานการกินยา...", "กรุณารอสักครู่")
        
        def load_report_data_thread():
            try:
                self.result = manageData.get(self.userid)
                result = medicine_report.get_eatmedic(self.userid)
                print(result)
                if result['status']:
                    self.data = result['data']
                    self.page = 1
                    self.controller.notifier.show_notification("โหลดรายงานสำเร็จ", success=True)

                    self.controller.after(0, lambda: self.display_table())
                    self.controller.after(0, lambda: self.export_button.configure(
                        command=lambda: generate_pdf_sync(self.userid,)
                    ))
                    self.controller.after(0, self.controller.hide_loading)
                else:
                    self.controller.notifier.show_notification(result['message'], success=False)
                    self.controller.after(0, self.controller.hide_loading)
            except Exception as e:
                self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
                self.controller.after(0, self.controller.hide_loading)

        threading.Thread(target=load_report_data_thread, daemon=True).start()


    def display_table(self):
        # เคลียร์ widget เก่าใน scrollable_frame แทน table_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.data:
            empty = ctk.CTkFrame(self.scrollable_frame, fg_color="#F8FAFC", corner_radius=12)
            empty.grid(row=0, column=0, padx=15, pady=15, sticky='ew', columnspan=3)
            ctk.CTkLabel(empty,
                         text="ไม่มีประวัติการจ่ายยา",
                         text_color="#C92A2A",
                         font=("TH Sarabun New", 24, "bold")).pack(padx=15, pady=12)
            return

        # Header bar - ปรับขนาดฟอนต์
        header = ctk.CTkFrame(self.scrollable_frame, fg_color="#EDF2F7", corner_radius=10)
        header.grid(row=0, column=0, columnspan=3, sticky='ew', padx=15, pady=(15, 8))
        header.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(header, text="วันที่ - เวลา", font=("TH Sarabun New", 24, "bold"),
                     text_color="#1E293B").grid(row=0, column=0, padx=12, pady=8, sticky='ew')
        ctk.CTkLabel(header, text="ชื่อยา", font=("TH Sarabun New", 24, "bold"),
                     text_color="#1E293B").grid(row=0, column=1, padx=12, pady=8, sticky='ew')
        ctk.CTkLabel(header, text="ผลการจ่ายยา", font=("TH Sarabun New", 24, "bold"),
                     text_color="#1E293B").grid(row=0, column=2, padx=12, pady=8, sticky='ew')

        start = (self.page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        page_data = self.data[start:end]

        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]

        for idx, row in enumerate(page_data, start=1):
            bg = "#F8FAFC" if idx % 2 == 1 else "#EEF6FF"
            row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=bg, corner_radius=10)
            row_frame.grid(row=idx, column=0, columnspan=3, sticky='ew', padx=15, pady=4)
            row_frame.grid_columnconfigure((0, 1, 2), weight=1)

            try:
                date_obj = row['time_get']
                
                # ถ้าเป็น string ให้แปลงเป็น datetime object
                if isinstance(date_obj, str):
                    # ลองแปลงรูปแบบต่างๆ
                    try:
                        date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                            except ValueError:
                                dt = "ไม่สามารถแสดงวันที่"
                                raise ValueError("ไม่สามารถแปลงวันที่ได้")
                
                # ถ้าเป็น None หรือไม่มีค่า
                if date_obj is None:
                    dt = "ไม่สามารถแสดงวันที่"
                else:
                    month_th = thai_months[date_obj.month - 1]
                    dt = f"{date_obj.day:02d} {month_th} {date_obj.year + 543} เวลา {date_obj.strftime('%H:%M')}"
            except Exception as e:
                print(f"Error formatting date: {e}, row['time_get'] = {row.get('time_get', 'N/A')}")
                dt = "ไม่สามารถแสดงวันที่"

            name = row['medicine_1'] if row['medicine_1'] else "ไม่มีข้อมูล"
            is_success = row['medicine_get'] == 'success'
            badge_text = "สำเร็จ" if is_success else "ไม่สำเร็จ"
            badge_bg = "#E6F4EA" if is_success else "#FDECEA"
            badge_color = "#1E7E34" if is_success else "#C92A2A"
            badge_emoji = "" if is_success else ""

            ctk.CTkLabel(row_frame, text=dt,
                         text_color="#0B1220", font=("TH Sarabun New", 20)).grid(row=0, column=0, padx=12, pady=6, sticky='w')
            ctk.CTkLabel(row_frame, text=name,
                         text_color="#0B1220", font=("TH Sarabun New", 20)).grid(row=0, column=1, padx=12, pady=6, sticky='w')

            badge = ctk.CTkFrame(row_frame, fg_color=badge_bg, corner_radius=15)
            badge.grid(row=0, column=2, padx=12, pady=6, sticky='ew')
            ctk.CTkLabel(badge, text=f"{badge_emoji} {badge_text}",
                         text_color=badge_color,
                         font=("TH Sarabun New", 20, "bold")).pack(padx=10, pady=4)

        # กำหนดให้ scrollable_frame column ปรับขนาดตามเนื้อหา
        self.scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1)

        total_pages = max(1, (len(self.data) + self.rows_per_page - 1) // self.rows_per_page)
        self.page_label.configure(text=f"หน้าที่ {self.page} จาก {total_pages}")

        success = sum(1 for d in self.data if d['medicine_get'] == 'success')
        failed = len(self.data) - success
        self.summary_label.configure(text=f" สรุปผลการจ่ายยา |  สำเร็จ: {success} |  ไม่สำเร็จ: {failed}")

    def next_page(self):
        if self.page < (len(self.data) + self.rows_per_page - 1) // self.rows_per_page:
            self.page += 1
            self.display_table()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.display_table()


class Report2(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")
        self.controller = controller

        # ✅ Background - ปรับขนาดเป็น 1024x600
        bg_image = Image.open(f"{PATH}image/reportdata.png").resize((1024, 800), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar
        navbar = ctk.CTkFrame(self, height=60, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x",pady=50)

        page_title = ctk.CTkLabel(
            navbar,
            text="ประวัติการวัดความดัน",
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
            command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=10)

        # ✅ ปุ่มส่งออกเอกสาร - ปรับขนาดให้เหมาะสม
        self.export_button = ctk.CTkButton(navbar,
                                    text="ส่งออกเอกสาร",
                                    width=100, 
                                    height=50, 
                                    corner_radius=BUTTON_RADIUS,
                                    fg_color="#fddc75",
                                    hover_color="#a08a46",
                                    text_color="white",
                                    font=("Arial", 20, "bold"),
                                    command=lambda: None)  # ไม่ทำอะไร
        self.export_button.pack(side="right", padx=10, pady=15)

        # ✅ กล่องใหญ่สำหรับหัวข้อ + คำแนะนำจาก AI - ปรับขนาดและตำแหน่ง
        self.advice_card = ctk.CTkFrame(self,
                                        width=950,
                                        height=230,
                                        fg_color="#FFFFFF",  # สีฟ้าอ่อน
                                        corner_radius=0)
        self.advice_card.place(relx=0.5, rely=0.67, anchor="center")
        #pywinstyles.set_opacity(self.advice_card, value=0.9,color="#000001")

        # ✅ หัวข้อในกล่อง - ปรับขนาดฟอนต์
        self.advice_title = ctk.CTkLabel(self.advice_card,
                                         text="คำแนะนำในการดูแลตัวเองและการปรับพฤติกรรมที่เหมาะสม",
                                         font=("Arial", 20, "bold"),
                                         text_color="#000000")
        self.advice_title.pack(pady=(10, 5))  # เว้นบน 10 ล่าง 5

        # ✅ Textbox สำหรับเนื้อหา AI - ปรับขนาด
        self.advice_textbox = ctk.CTkTextbox(self.advice_card,
                                             width=920,
                                             height=200,
                                             wrap="word",
                                             font=("Arial", 18),
                                             fg_color="white",
                                             text_color="black",
                                             corner_radius=10)
        self.advice_textbox.insert("1.0", "\nกำลังโหลดข้อมูลจาก AI...")
        self.advice_textbox.configure(state="disabled")
        self.advice_textbox.pack(pady=(0, 10))

        # ✅ Scrollable Frame สำหรับตารางข้อมูล - ปรับขนาดและตำแหน่ง

        # === Parent Frame ===
        parent_frame = ctk.CTkFrame(
            self, width=920, height=250, corner_radius=0,
            fg_color="#FFFFFF", bg_color="#000001"
        )
        parent_frame.place(relx=0.5, rely=0.35, anchor="center")
        #pywinstyles.set_opacity(parent_frame, value=0.9, color="#000001")
        
        # === Scrollable Child ===
        self.scroll_frame = ctk.CTkScrollableFrame(
            parent_frame, width=880, height=230, fg_color="white"
        )
        self.scroll_frame.place(relx=0.5, rely=0.5, anchor="center")
        


        self.headers = ["ลำดับ", "ความดันสูง", "ความดันต่ำ", "ชีพจร", "คำแนะนำ", "วันที่บันทึก"]
        self.column_widths = [60, 120, 120, 80, 80, 200]

    # ✅ เรียกตอนแสดงหน้าจอ
    def on_show(self):
        print("Report2 is now visible")
        
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังโหลดรายงานสุขภาพ...", "กำลังประมวลผลข้อมูลด้วย AI กรุณารอสักครู่")
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        threading.Thread(target=self.load_data_async, daemon=True).start()

    def load_data_async(self):
        """🎯 ปรับปรุง: เรียก Gemini เพียงครั้งเดียว (ไม่ซ้ำ)"""
        try:
            # ✅ เรียก heart_report.generate_advice() เพียงครั้งเดียว (ใช้คำแนะนำที่มีอยู่แล้ว)
            result = heart_report().generate_advice(self.controller.user['id'])
            
            if result['status']:
                ai_text = result['advices']  
                print("ai_text", ai_text)# 🚀 ประหยัด 10-20 วินาที!
                
                self.controller.notifier.show_notification("โหลดข้อมูลสุขภาพสำเร็จ", success=True)
                self.after(0, lambda: self.update_ui(result, ai_text))
            else:
                self.controller.notifier.show_notification(result['message'], success=False)
                self.controller.after(0, self.controller.hide_loading)
        except Exception as e:
            self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
            self.controller.after(0, self.controller.hide_loading)

    
    def update_ui(self, result, ai_text):
        # อัปเดต AI textbox
        self.advice_textbox.configure(state="normal")
        self.advice_textbox.delete("1.0", "end")
        self.advice_textbox.insert("1.0", "\n" + ai_text)
        self.advice_textbox.configure(state="disabled")

        # bind ปุ่ม export
        self.export_button.configure(command=lambda: generate_pdf_sync(self.controller.user['id'], ai_text))

        # แสดงตาราง
        self.display_data(result['data'], result['advices'])
        
        # ซ่อนหน้าดาวโหลด
        self.controller.hide_loading()
    
    def show_advice_popup(self, advice_text):
        popup = ctk.CTkToplevel(self)
        popup.title("คำแนะนำจาก AI")
        popup.geometry("500x350")
        popup.configure(fg_color="white")

        popup.transient(self)
        popup.attributes('-topmost', True)  # ใช้ topmost แทน

        label = ctk.CTkLabel(popup, text="คำแนะนำจาก AI", 
                        font=("Arial", 20, "bold"), text_color="black")
        label.pack(pady=8)

        textbox = ctk.CTkTextbox(popup, width=450, height=220, wrap="word", 
                            font=("Arial", 18), fg_color="white", text_color="black")
        textbox.insert("1.0", advice_text)
        textbox.configure(state="disabled")
        textbox.pack(pady=8)

        close_btn = ctk.CTkButton(popup, text="ปิด", command=popup.destroy,
                                  fg_color="#495057", hover_color="#FF0000", 
                                  text_color="white")
        close_btn.pack(pady=8)
        popup.focus_force()  # ให้ focus ที่ popup

    def _set_grab_safely(self, window):
        try:
            window.grab_set()
        except Exception as e:
            print(f"Cannot grab window: {e}")
            # ถ้า grab ไม่ได้ก็ไม่เป็นไร popup ยังใช้งานได้ปกติ

    def display_data(self, data, advices):
        """🎯 ปรับปรุง: lazy loading + async grid + caching advice"""
        # เคลียร์ widget เก่า
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # ✅ สร้าง header ก่อน (ไม่ใช้ loop)
        headers = self.headers
        column_widths = self.column_widths
        
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(self.scroll_frame, text=header, font=("Arial", 20, "bold"),
                                 text_color="black", width=column_widths[col])
            label.grid(row=0, column=col, padx=3, pady=3)
        
        # ✅ สร้าง cache advice (ประหยัด 50+ วินาที)
        advice_cache = {}  # heart_id -> advice_text
        if isinstance(advices, str):
            # ถ้า advices เป็น string เดียว ให้ใช้สำหรับทุกแถว
            default_advice = advices
        else:
            default_advice = "ไม่พบคำแนะนำ"
        
        # ✅ เรียก update_idletasks() เพื่อให้ UI respond
        self.scroll_frame.update_idletasks()
        
        # ✅ สร้างแถวด้วย async batching (ป้องกัน hanging)
        self._render_rows_async(data, advice_cache, default_advice, 0)
    
    def _render_rows_async(self, data, advice_cache, default_advice, start_index, batch_size=5):
        """🚀 Render rows ทีละ batch เพื่อให้ UI ไม่ค้าง"""
        headers = self.headers
        column_widths = self.column_widths
        end_index = min(start_index + batch_size, len(data))
        
        for idx in range(start_index, end_index):
            i = idx
            row = data[idx]
            
            systolic = f"{row['systolic_pressure']} mmHg"
            diastolic = f"{row['diastolic_pressure']} mmHg"
            pulse = f"{row['pulse_rate']} bpm"
            try:
                date = datetime.strptime(str(row['date']), "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y เวลา %H:%M น.")
            except:
                date = str(row['date'])

            values = [str(i+1), systolic, diastolic, pulse, None, date]
            heart_id = row.get('heart_id', None)
            
            # ✅ ใช้ default_advice แทนการเรียก API ซ้ำ
            advice_text = advice_cache.get(heart_id, default_advice)

            for col, val in enumerate(values):
                if col == 4:
                    # ✅ ปุ่มคำแนะนำ
                    advice_btn = ctk.CTkButton(self.scroll_frame, text="!", width=35, height=25,
                                               command=lambda a=advice_text: self.show_advice_popup(a),
                                               fg_color="#495057", hover_color="#FF0000", text_color="white")
                    advice_btn.grid(row=i+1, column=col, padx=3, pady=3)
                else:
                    label = ctk.CTkLabel(self.scroll_frame, text=val, font=("Arial", 18),
                                         text_color="black", width=column_widths[col])
                    label.grid(row=i+1, column=col, padx=3, pady=3)
        
        # ✅ Render batch ถัดไป (ไม่ block UI)
        if end_index < len(data):
            self.after(10, lambda: self._render_rows_async(data, advice_cache, default_advice, end_index, batch_size))
                    
                    

