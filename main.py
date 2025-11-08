import customtkinter as ctk
from PIL import Image, ImageTk
import time
from tkinter import messagebox
import subprocess
import threading
import json
import os
import warnings
from tkcalendar import Calendar
from datetime import datetime, timedelta
from pywifi import PyWiFi
from babel.dates import format_date
# model format เวลา
from lib.set_time import default_serializer
from lib.sendTimeToPico import recivetime,start_serial_loop

# --ใหม่--
#import pywinstyles


# nodel การเเจ้งเตือน
from lib.alert import sendtoTelegram
from lib.loadenv import PATH

# model อ่านออกเสียง
from gtts import gTTS 
from pygame import mixer

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
auth = auth()
manageData = infoData()
manageMedic = manageMedicData()
set_dispensing_time = setting_eat_time()
ai = Gemini()
set_counter = SetCounter()
Heart_report = heart_report()
medicine_report = eat_medicine_report()
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

class login(ctk.CTkFrame):     
    def on_show(self):         
        print("login is now visible")     
        show_onboard() 
        # เพิ่มส่วนนี้
        def on_frame_click(event):
            widget = event.widget
            if not isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
                hide_onboard()
        
        self.bind('<Button-1>', on_frame_click)

    def __init__(self, parent, controller):         
        super().__init__(parent)         
        self.controller = controller          
        
        # พื้นหลังแบบรูปภาพ (1024x600)         
        bg_image = Image.open(f"{PATH}image/login.png").resize((1024, 800), Image.Resampling.LANCZOS)         
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))         
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")         
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)          
        
        # === กล่องล็อกอินหลัก (Main Login Container) ===
        frame = ctk.CTkFrame(             
            self,             
            width=410,             
            height=530,             
            corner_radius=0,             
            fg_color="white",             
            bg_color="#000001"         
        )         
        frame.place(relx=0.5, rely=0.54, anchor="center")
        #pywinstyles.set_opacity(frame, value=0.9,color="#000001")
        # pywinstyles.set_opacity(frame, value=0.9 ,color="#000001")   # ถ้าใช้ pywinstyles
        
        # === โลโก้ในกล่องสี่เหลียมขอบมน (Logo Container) ===
        logo_frame = ctk.CTkFrame(
            frame,
            width=60,
            height=60,
            corner_radius=15,
            fg_color="#F5F5F5",
            border_width=1,
            border_color="#E0E0E0"
        )
        logo_frame.grid(row=0, column=0, columnspan=2, pady=(40, 20))
        
        lang_button = ctk.CTkButton(
            frame,  # หรือ parent ที่คุณต้องการวางปุ่ม
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
        lang_button.place(x=300, y=40)  # ปรับตำแหน่งตามต้องการ

        
        # === ไอคอนโลโก้ (Logo Icon) ===
        try:
            logo_login_img = Image.open(f"{PATH}image/login-icon.png").resize((40, 40), Image.Resampling.LANCZOS)
            self.logo_ctk_image = ctk.CTkImage(light_image=logo_login_img, size=(40, 40))
            logo_label = ctk.CTkLabel(logo_frame, image=self.logo_ctk_image, text="")
        except:
            logo_label = ctk.CTkLabel(
                logo_frame,
                text="↗",
                font=("Arial", 24, "bold"),
                text_color="#666666"
            )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # === หัวข้อหลัก (Main Title) ===
        ctk.CTkLabel(             
            frame,             
            text="ลงชื่อเข้าใช้ด้วยอีเมล",             
            font=("Arial", 28, "bold"),             
            text_color="#1a1a1a",         
        ).grid(row=1, column=0, columnspan=2, pady=(20, 10))     
        
        # === คำอธิบาย (Description) ===
        ctk.CTkLabel(             
            frame,             
            text="สร้างเอกสารใหม่สำหรับใช้กับเครื่องจ่าย\nของคุณบนเว็บไซต์ของเรา",             
            font=("Arial", 14),             
            text_color="#666666",
            justify="center"         
        ).grid(row=2, column=0, columnspan=2, pady=(0, 30))
        
        # === ตัวแปรเก็บข้อมูล (Data Variables) ===
        self.username = ctk.StringVar()         
        self.password = ctk.StringVar()          
        
        # === ช่องกรอกอีเมล - แก้ไขส่วนนี้ ===
        email_frame = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=8, height=50)
        email_frame.grid(row=3, column=0, columnspan=2, padx=30, pady=(0, 15), sticky="ew")
        email_frame.grid_columnconfigure(1, weight=1)

        email_icon = Image.open(f"{PATH}image/email.png").resize((24, 24), Image.Resampling.LANCZOS)
        self.email_ctk_image = ctk.CTkImage(light_image=email_icon, size=(24, 24))
        ctk.CTkLabel(email_frame, image=self.email_ctk_image, text="").grid(
            row=0, column=0, padx=(15, 10), pady=12, sticky="w"
        )

        # ✅ ใช้ create_entry_with_keyboard แทน CTkEntry
        email_entry = create_entry_with_keyboard(
            email_frame,
            textvariable=self.username,
            placeholder_text="Email",
            font=("Arial", 16),
            fg_color="#F8F9FA",
            border_width=0,
            text_color="#1a1a1a"
        )
        email_entry.grid(row=0, column=1, padx=(0, 15), pady=12, sticky="ew")
        
        # === ช่องกรอกรหัสผ่าน - แก้ไขส่วนนี้ ===
        password_frame = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=8, height=50)
        password_frame.grid(row=4, column=0, columnspan=2, padx=30, pady=(0, 15), sticky="ew")
        password_frame.grid_columnconfigure(1, weight=1)

        padlock_icon = Image.open(f"{PATH}image/padlock.png").resize((24, 24), Image.Resampling.LANCZOS)
        self.padlock_ctk_image = ctk.CTkImage(light_image=padlock_icon, size=(24, 24))
        ctk.CTkLabel(password_frame, image=self.padlock_ctk_image, text="").grid(
            row=0, column=0, padx=(15, 10), pady=12, sticky="w"
        )

        # ✅ ใช้ create_entry_with_keyboard แทน CTkEntry
        self.password_entry = create_entry_with_keyboard(
            password_frame,
            textvariable=self.password,
            placeholder_text="Password",
            font=("Arial", 16),
            fg_color="#F8F9FA",
            border_width=0,
            text_color="#1a1a1a",
            show="*"
        )
        self.password_entry.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="ew")
      

        # ปุ่มแสดง/ซ่อนรหัสผ่าน
        eye_closed_icon = Image.open(f"{PATH}image/eye_closed.png").resize((24, 24), Image.Resampling.LANCZOS)
        eye_open_icon = Image.open(f"{PATH}image/eye_open.png").resize((24, 24), Image.Resampling.LANCZOS)
        self.eye_closed_ctk = ctk.CTkImage(light_image=eye_closed_icon, size=(24, 24))
        self.eye_open_ctk = ctk.CTkImage(light_image=eye_open_icon, size=(24, 24))

        def toggle_password():
            if self.password_entry.cget("show") == "":
                self.password_entry.configure(show="*")
                show_password_btn.configure(image=self.eye_closed_ctk)
            else:
                self.password_entry.configure(show="")
                show_password_btn.configure(image=self.eye_open_ctk)

        show_password_btn = ctk.CTkButton(
            password_frame,
            image=self.eye_closed_ctk,
            text="",
            width=30,
            height=30,
            fg_color="#F8F9FA",
            hover_color="#F0F0F0",
            command=toggle_password
        )
        show_password_btn.grid(row=0, column=2, padx=(0, 10), pady=12, sticky="e")
        
        # === ฟังก์ชันการเข้าสู่ระบบ (Login Function) ===
        def save_and_go_home():             
            if len(self.username.get().strip()) == 0 or len(self.password.get().strip()) == 0:                 
                print('กรุณากรอกข้อมูลให้ถูกต้องตามแบบฟอร์ม')                 
                return              
            
            # แสดงหน้าดาวโหลด
            controller.show_loading("กำลังเข้าสู่ระบบ...", "กรุณารอสักครู่")
            
            def login_thread():
                try:
                    result = auth.login(self.username.get(), self.password.get())             
                    print(result)             
                    if result['status']:                 
                        self.controller.user = result['user']                 
                        with open('user_data.json', 'w', encoding='utf-8') as f:                     
                            json.dump(result['user'], f, ensure_ascii=False, indent=4, default=default_serializer)                 
                        print(result['message'])                 
                        # เปลี่ยนจาก show_frame ระหว่างกำลังโหลด -> ให้ hide_loading พาไปยังหน้าเป้าหมาย
                        def go_wifi():
                            try:
                                controller._previous_frame_class = Wificonnect
                            except Exception:
                                pass
                            controller.hide_loading()
                        controller.after(0, go_wifi)
                    else:                 
                        print(result['message'])
                        controller.after(0, controller.hide_loading)
                except Exception as e:
                    print(f"เกิดข้อผิดพลาด: {e}")
                    controller.after(0, controller.hide_loading)
            
            threading.Thread(target=login_thread, daemon=True).start()          
        
        # === ปุ่มเข้าสู่ระบบ (Get Started Button) ===
        save_button = ctk.CTkButton(             
            frame,             
            text="เข้าสู่ระบบ",             
            width=350,             
            height=50,             
            fg_color="#2D3748",             
            hover_color="#1A202C",             
            text_color="white",             
            font=("Arial", 16, "bold"),             
            corner_radius=8,             
            command=save_and_go_home         
        )         
        save_button.grid(row=6, column=0, columnspan=2, padx=30, pady=(0, 40), sticky="ew")
        
        # === การตั้งค่า Grid Layout ===
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

class HomePage(ctk.CTkFrame):
    def on_show(self):
        print("HomePage is now visible")
        # อัพเดทข้อมูลการตั้งค่ายาเมื่อแสดงหน้า (เฉพาะครั้งแรก)
        if not hasattr(self, '_medication_info_loaded'):
            self.update_medication_info()
            self._medication_info_loaded = True
        # อัพเดทข้อมูลผู้ใช้เมื่อแสดงหน้า (เฉพาะครั้งแรก)
        if not hasattr(self, '_user_info_loaded'):
            self.update_user_info()
            self._user_info_loaded = True
        self.create_menu_buttons(self.controller)
        
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
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
        self.date_label.place(x=70, y=185)

        self.time_label = ctk.CTkLabel(self, text="", font=("TH Sarabun New", 40, "bold"),
                                       fg_color="#8acaef", text_color="white")
        self.time_label.place(x=360, y=185)

        # สร้างส่วนแสดงข้อมูลการตั้งค่ายา
        self.create_medication_display()

        # สร้างส่วนแสดงข้อมูลผู้ใช้
        self.create_user_info_display()
        
        # สร้างส่วนแสดงจำนวนยาคงเหลือ (เพิ่มบรรทัดนี้)
        self.create_counter_medicine_display()
     
        self.update_datetime()

    def add_status_icons(self):
        # ปรับขนาดไอคอนให้เล็กลง
        battery_image = Image.open(f"{PATH}imgNew/battery.png").resize((30, 30), Image.Resampling.LANCZOS)
        self.battery_photo = ImageTk.PhotoImage(battery_image)
        battery_label = ctk.CTkLabel(self, image=self.battery_photo, text="", bg_color="#8acaef")
        #pywinstyles.set_opacity(battery_label, value=1,color="#000001")
        battery_label.place(x=925, y=55)

        wifi_image = Image.open(f"{PATH}imgNew/wi-fi.png").resize((30, 30), Image.Resampling.LANCZOS)
        self.wifi_photo = ImageTk.PhotoImage(wifi_image)
        wifi_label = ctk.CTkLabel(self, image=self.wifi_photo, text="", bg_color="#8acaef")
        #s.set_opacity(wifi_label, value=1,color="#000001")
        wifi_label.place(x=845, y=55)

    def create_menu_buttons(self, controller):
        # ปรับขนาดปุ่มให้เล็กลง
        btn_size = (100, 100)
        btn_images = {}
        pressure = 0
        if hasattr(self.controller, 'user') and self.controller.user and 'pressure' in self.controller.user:
            pressure = self.controller.user['pressure']

        if pressure == 1:
            paths = [
                f"{PATH}imgNew/iconuser.png", f"{PATH}imgNew/icontime.png", f"{PATH}imgNew/iconheath.png",
                f"{PATH}imgNew/icondog.png", f"{PATH}imgNew/iconreport.png", f"{PATH}imgNew/iconout.png",
                f"{PATH}imgNew/icondow.png"
            ]
            btn_texts = [
                "ข้อมูลผู้ใช้", "ตั้งเวลา", "สุขภาพ",
                "ข้อมูลยา", "รายงาน", "ออกระบบ", "ปิดเครื่อง"
            ]
        else:
            paths = [
                f"{PATH}imgNew/iconuser.png", f"{PATH}imgNew/icontime.png",
                f"{PATH}imgNew/icondog.png", f"{PATH}imgNew/iconreport.png", f"{PATH}imgNew/iconout.png",
                f"{PATH}imgNew/icondow.png"
            ]
            btn_texts = [
                "ข้อมูลผู้ใช้", "ตั้งเวลา",
                "ข้อมูลยา", "รายงาน", "ออกระบบ", "ปิดเครื่อง"
            ]
        pages = [info, Frame3, Frame4, Frame2, ReportFrame, login]

        for i, path in enumerate(paths, start=1):
            try:
                img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)
                btn_images[i] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Error: {path} not found.")

        # จัดปุ่มเป็น 2 แถว
        buttons_per_row = 7
        btn_width = 100
        btn_height = 80
        start_x = 30
        start_y = 600

        for i in range(7):
            if i + 1 in btn_images:
                text = btn_texts[i]
                
                # คำนวณตำแหน่งแถวและคอลัมน์
                row = i // buttons_per_row
                col = i % buttons_per_row
                
                x_pos = start_x + col * (btn_width + 40)  # เว้นระยะแนวนอนมากขึ้น
                y_pos = start_y + row * (btn_height + 30) # เว้นระยะแนวตั้งมากขึ้น


                # คำสั่งของแต่ละปุ่ม
                if i == 5:
                    command = self.confirm_logout
                elif i == 6:
                    command = self.shutdown_system
                else:
                    command = lambda i=i: controller.show_frame(pages[i])

                # สร้างปุ่ม
                btn = ctk.CTkButton(
                    self,
                    image=btn_images[i + 1],
                    text=text,
                    compound="top",
                    font=("TH Sarabun New", 22, "bold"),
                    fg_color="#FFFFFF",
                    bg_color="#000001",   
                    hover_color="#E9ECEF",
                    text_color="#1D3557",
                    border_width=2,
                    border_color="#A8DADC",
                    width=100,
                    height=90,
                    corner_radius=0,
                    command=command
                )
                btn.place(x=x_pos, y=y_pos)
                #pywinstyles.set_opacity(btn, value=1,color="#000001")

    def confirm_logout(self):
        response = messagebox.askyesno("ยืนยันออกจากระบบ", "คุณต้องการออกจากระบบหรือไม่?")
        if response:
            try:
                if os.path.exists("user_data.json"):
                    os.remove("user_data.json")
            except Exception as e:
                print(f"เกิดข้อผิดพลาดขณะออกจากระบบ: {e}")
            self.controller.show_frame(login)

    def shutdown_system(self):
        response = messagebox.askyesno("ยืนยัน", "คุณต้องการปิดเครื่องหรือไม่?")
        if response:
            os.system("shutdown /s /t 1")

    def create_medication_display(self):
        # ปรับปรุงการแสดงข้อมูลยาให้สวยงาม
        self.medication_frame = ctk.CTkFrame(
            self,
            width=340,
            height=300,
            corner_radius=0,
            fg_color="#FFFFFF",
            bg_color="#000001",
            border_width=2,
            border_color="#E8F4FD"
        )
        self.medication_frame.place(x=340, y=280)
        #pywinstyles.set_opacity(self.medication_frame, value=1, color="#000001")

        # หัวข้อพร้อมไอคอน
        header_frame = ctk.CTkFrame(
            self.medication_frame,
            width=320,
            height=40,
            corner_radius=20,
            fg_color="#E8F4FD"
        )
        header_frame.place(x=10, y=10)

        medication_icon = ctk.CTkLabel(
            header_frame,
            text=" ",
            font=("TH Sarabun New", 24),
            fg_color="transparent"
        )
        medication_icon.place(x=10, y=8)

        self.medication_title = ctk.CTkLabel(
            header_frame,
            text="การตั้งค่ายา",
            font=("TH Sarabun New", 25, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.medication_title.place(x=30, y=10)

        # ปุ่มควบคุม
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

        # สร้างกรอบสำหรับแสดงรายการยา
        self.medication_list_frame = ctk.CTkScrollableFrame(
            self.medication_frame,
            width=310,
            height=150,
            fg_color="#F8F9FA",
            corner_radius=10,
            border_width=1,
            border_color="#DEE2E6"
        )
        self.medication_list_frame.place(x=10, y=60)

        self.medication_labels = []

    def create_user_info_display(self):
        # ปรับปรุงการแสดงข้อมูลผู้ใช้ให้สวยงาม
        self.user_info_frame = ctk.CTkFrame(
            self,
            width=300,
            height=300,
            corner_radius=0,
            fg_color="#FFFFFF",
            bg_color="#000001",
            border_width=2,
            border_color="#FFF2E8"
        )
        self.user_info_frame.place(x=700, y=280)
        #pywinstyles.set_opacity(self.user_info_frame, value=1, color="#000001")

        # หัวข้อพร้อมไอคอน
        header_frame = ctk.CTkFrame(
            self.user_info_frame,
            width=280,
            height=40,
            corner_radius=10,
            fg_color="#FFF2E8"
        )
        header_frame.place(x=10, y=10)

        user_icon = ctk.CTkLabel(
            header_frame,
            text=" ",
            font=("TH Sarabun New", 24),
            fg_color="transparent"
        )
        user_icon.place(x=10, y=8)

        self.user_info_title = ctk.CTkLabel(
            header_frame,
            text="ข้อมูลผู้ใช้",
            font=("TH Sarabun New", 25, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.user_info_title.place(x=50, y=10)

        # สร้างกรอบสำหรับแสดงข้อมูล
        self.user_info_content = ctk.CTkScrollableFrame(
            self.user_info_frame,
            width=280,
            height=230,
            fg_color="#F8F9FA",
            corner_radius=10,
            border_width=1,
            border_color="#DEE2E6"
        )
        self.user_info_content.place(x=10, y=60)

        self.user_info_labels = []

    def create_counter_medicine_display(self):
        self.medicine_frame = ctk.CTkFrame(
            self,
            width=300,
            height=300,
            corner_radius=0,
            fg_color="#FFFFFF",
            bg_color="#000001",
            border_width=2,
            border_color="#FFF2E8"
        )
        self.medicine_frame.place(x=20, y=280)
        #pywinstyles.set_opacity(self.medicine_frame, value=1, color="#000001")
    
        # หัวข้อพร้อมไอคอน
        header_frame = ctk.CTkFrame(
            self.medicine_frame,
            width=280,
            height=40,
            corner_radius=10,
            fg_color="#FFF2E8"
        )
        header_frame.place(x=10, y=10)
        
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
        self.reset_counter_button.place(x=200, y=8)

        self.medicine_title = ctk.CTkLabel(
            header_frame,
            text="จำนวนยาคงเหลือ",
            font=("TH Sarabun New", 25, "bold"),
            text_color="#000000",
            fg_color="transparent"
        )
        self.medicine_title.place(x=10, y=10)

        # เริ่มต้นค่าตัวแปรสำหรับเก็บจำนวนยา - แก้ไข typo 'uset' เป็น 'user'
        if hasattr(self.controller, 'user') and self.controller.user and 'count_medicine' in self.controller.user:
            self.medicine_count = self.controller.user['count_medicine']
        else:
            self.medicine_count = 28
        
        # สร้าง Label สำหรับแสดงจำนวนยา
        self.counter_medicine = ctk.CTkLabel(
            self.medicine_frame,
            text=str(self.medicine_count),
            width=250,
            height=150,
            fg_color="#F8F9FA",
            corner_radius=10,
            font=("TH Sarabun New", 48, "bold"),
            text_color="#2E7D32"
        )
        self.counter_medicine.place(x=25, y=60)
        
        print(f"สร้างส่วนแสดงจำนวนยาคงเหลือเสร็จสิ้น: {self.medicine_count} เม็ด")
    
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
        """ลดจำนวนยา"""
        new_count = max(0, self.medicine_count - amount)  # ไม่ให้ต่ำกว่า 0
        set_counter.update_counter(self.controller.user['device_id'],self.controller.user['id'],new_count)
        self.update_medicine_count(new_count)

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
            set_counter.update_counter(self.controller.user['device_id'],self.controller.user['id'],initial_count)
            self.update_medicine_count(initial_count)
            
            # แสดงข้อความยืนยัน
            messagebox.showinfo("สำเร็จ", f"รีเซ็ตจำนวนยาเป็น {initial_count} เม็ดเรียบร้อยแล้ว")
            print(f"รีเซ็ตจำนวนยาเป็น: {initial_count} เม็ด")

    def update_user_info(self):
        try:
            # ป้องกันการอัพเดทซ้ำถ้ากำลังโหลดอยู่
            if hasattr(self, '_updating_user_info') and self._updating_user_info:
                return
            
            self._updating_user_info = True
            print("กำลังอัพเดทข้อมูลผู้ใช้...")
            
            # ลบข้อมูลเก่า
            for label in self.user_info_labels:
                try:
                    label.destroy()
                except:
                    pass
            self.user_info_labels.clear()

            # แสดงข้อมูลผู้ใช้
            if hasattr(self.controller, 'user') and self.controller.user:
                user = self.controller.user
                print(f"พบข้อมูลผู้ใช้: {user.get('firstname_th', '')} {user.get('lastname_th', '')}")
                
                # ข้อมูลพื้นฐาน
                user_info = []
                user_info.append(f"ผู้ป่วย: {user.get('firstname_th', '')} {user.get('lastname_th', '')}")
                user_info.append(f"โทรศัพท์: {user.get('phone', '')}")
                
                if user.get('chronic_disease'):
                    user_info.append(f"โรค: {user.get('chronic_disease', '')}")
                
                if user.get('caretaker_name'):
                    user_info.append(f"ผู้ดูแล: {user.get('caretaker_name', '')}")

                # แสดงข้อมูลในรูปแบบการ์ด
                for i, info in enumerate(user_info):
                    info_card = ctk.CTkFrame(
                        self.user_info_content,
                        height=35,
                        corner_radius=8,
                        fg_color="#E8F4FD" if i % 2 == 0 else "#FFF2E8"
                    )
                    info_card.pack(pady=3, padx=5, fill="x")
                    
                    info_label = ctk.CTkLabel(
                        info_card,
                        text=info,
                        font=("TH Sarabun New", 16, "bold"),
                        text_color="#000000",
                        fg_color="transparent",
                        justify="left",
                        anchor="w"
                    )
                    info_label.pack(pady=5, padx=10, fill="x",anchor="w")
                    
                    self.user_info_labels.append(info_card)
                    self.user_info_labels.append(info_label)
                    
                # อัพเดทจำนวนยาด้วย
                self.update_medicine_count()
                    
            else:
                print("ไม่พบข้อมูลผู้ใช้")
                # แสดงข้อความเมื่อไม่มีข้อมูลผู้ใช้
                no_user_card = ctk.CTkFrame(
                    self.user_info_content,
                    height=80,
                    corner_radius=10,
                    fg_color="#FFF3CD",
                    border_width=1,
                    border_color="#FFE69C"
                )
                no_user_card.pack(pady=30, padx=10, fill="x")
                
                warning_label = ctk.CTkLabel(
                    no_user_card,
                    text="⚠️ ไม่พบข้อมูลผู้ใช้",
                    font=("TH Sarabun New", 18, "bold"),
                    text_color="#856404",
                    fg_color="transparent"
                )
                warning_label.pack(pady=20)
                
                self.user_info_labels.extend([no_user_card, warning_label])
                
            print("อัพเดทข้อมูลผู้ใช้เสร็จสิ้น")
            self._updating_user_info = False
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอัพเดทข้อมูลผู้ใช้: {e}")
            self._updating_user_info = False

    def update_medication_info(self):
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

            # ดึงข้อมูลการตั้งค่ายาจาก API
            if hasattr(self.controller, 'user') and self.controller.user:
                # แสดงหน้าดาวโหลด
                self.controller.show_loading("กำลังโหลดข้อมูลยา...", "กรุณารอสักครู่")
                
                def load_meal_data():
                    try:
                        meal_data = set_dispensing_time.get_meal(
                            self.controller.user['device_id'],
                            self.controller.user['id']
                        )
                        self.controller.after(0, lambda: self.process_meal_data(meal_data))
                    except Exception as e:
                        print(f"เกิดข้อผิดพลาด: {e}")
                        self.controller.after(0, self.controller.hide_loading)
                
                threading.Thread(target=load_meal_data, daemon=True).start()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอัพเดทข้อมูลยา: {e}")
            self.controller.hide_loading()
    
    def process_meal_data(self, meal_data):
        """ประมวลผลข้อมูล meal_data หลังจากโหลดเสร็จ"""
        try:
            # แสดงข้อมูลวันที่เริ่มและสิ้นสุด
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
                        
                        date_card = ctk.CTkFrame(
                            self.medication_list_frame,
                            height=40,
                            corner_radius=8,
                            fg_color="#D4EDDA",
                            border_width=1,
                            border_color="#C3E6CB"
                        )
                        date_card.pack(pady=2, padx=5, fill="x")
                        
                        date_label = ctk.CTkLabel(
                            date_card,
                            text=date_info,
                            font=("TH Sarabun New", 14, "bold"),
                            text_color="#155724",
                            fg_color="transparent"
                        )
                        date_label.place(x=10, y=6)
                        
                        self.medication_labels.extend([date_card, date_label])
                    except:
                        pass
            
            if meal_data and 'data' in meal_data:
                medications = meal_data['data']
                recivetime(medications)
                # ป้องกันการเรียก start_serial_loop ซ้ำ
                if not hasattr(self.controller, '_serial_thread_running'):
                    serial_thread = threading.Thread(target=start_serial_loop, daemon=True)
                    serial_thread.start()
                    self.controller._serial_thread_running = True
                if medications:
                    # แสดงข้อมูลยาในรูปแบบการ์ด
                    for i, med in enumerate(medications):
                        meal_names = {
                            'bb': ' ก่อนนอน',
                            'bf': ' เช้า',
                            'lunch': ' กลางวัน',
                            'dn': ' เย็น'
                        }
                        
                        meal_name = meal_names.get(med.get('source', ''), med.get('source', ''))
                        time_str = med.get('time', '')
                        
                        # นับจำนวนยา
                        med_count = 0
                        med_names = []
                        for j in range(1, 5):
                            med_name = med.get(f'medicine_{j}', '')
                            if med_name:
                                med_count += 1
                                med_names.append(med_name)
                        
                        if med_count > 0:
                            # สร้างการ์ดยา
                            med_card = ctk.CTkFrame(
                                self.medication_list_frame,
                                height=60,
                                corner_radius=10,
                                fg_color="#E8F6EF",
                                border_width=2,
                                border_color="#7EBCA2"
                            )
                            med_card.pack(pady=3, padx=5, fill="x")
                            
                            # เวลาและมื้อ
                            time_label = ctk.CTkLabel(
                                med_card,
                                text=f"{meal_name} - {time_str}",
                                font=("TH Sarabun New", 20, "bold"),
                                text_color="#2D6A4F",
                                fg_color="transparent"
                            )
                            time_label.place(x=10, y=5)
                            
                            # จำนวนยา
                            count_label = ctk.CTkLabel(
                                med_card,
                                text=f" {med_count} รายการ",
                                font=("TH Sarabun New", 20),
                                text_color="#495057",
                                fg_color="transparent"
                            )
                            count_label.place(x=10, y=28)
                            
                            # สถานะ
                            status_label = ctk.CTkLabel(
                                med_card,
                                text=" พร้อมใช้",
                                font=("TH Sarabun New", 20, "bold"),
                                text_color="#FF0000",
                                fg_color="transparent"
                            )
                            status_label.place(x=200, y=28)
                            
                            self.medication_labels.extend([med_card, time_label, count_label, status_label])
                else:
                    # แสดงข้อความเมื่อไม่มีข้อมูลยา
                    self.show_no_medication_message()
            else:
                # แสดงข้อความเมื่อไม่มีข้อมูลยา
                self.show_no_medication_message()
            
            # ซ่อนหน้าดาวโหลด
            self.controller.hide_loading()
            self._updating_medication_info = False
                    
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอัพเดทข้อมูลยา: {e}")
            try:
                self.show_medication_error()
            except:
                pass
            self.controller.hide_loading()
            self._updating_medication_info = False

    def update_datetime(self):
        """อัพเดทวันที่และเวลาพร้อมเอฟเฟ็กต์"""
        today = datetime.today()
        
        # จัดรูปแบบวันที่ให้สั้นและเข้าใจง่าย
        thai_months = [
            "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
            "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
        ]
        
        thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        
        day_name = thai_days[today.weekday()]
        day = today.day
        month = thai_months[today.month]
        year = today.year + 543  # แปลงเป็น พ.ศ.
        
        date_text = f"{day_name} {day} {month} {year}"
        self.date_label.configure(text=date_text)

        # จัดรูปแบบเวลาพร้อมวินาที
        current_time = time.strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        
        # เปลี่ยนสีของเวลาตามช่วงเวลา
        hour = today.hour
        if 6 <= hour < 12:
            time_color = "#E67E22"  # สีส้ม (เช้า)
        elif 12 <= hour < 18:
            time_color = "#F39C12"  # สีเหลือง (บ่าย)
        elif 18 <= hour < 22:
            time_color = "#8E44AD"  # สีม่วง (เย็น)
        else:
            time_color = "#2C3E50"  # สีเข้ม (กลางคืน)
            
        self.time_label.configure(text_color=time_color)
        
        # อัพเดทสถานะระบบ
        self.update_system_status()
        
        # เรียกฟังก์ชันนี้ใหม่ทุก 1 วินาที (ตรวจสอบว่าหน้าต่างยังอยู่)
        try:
            if self.winfo_exists():
                self.after(1000, self.update_datetime)
        except:
            # หน้าต่างถูกทำลายแล้ว ไม่ต้องทำอะไร
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
        no_med_card = ctk.CTkFrame(
            self.medication_list_frame,
            height=80,
            corner_radius=10,
            fg_color="#FFF3CD",
            border_width=1,
            border_color="#FFE69C"
        )
        no_med_card.pack(pady=30, padx=10, fill="x")
        
        warning_label = ctk.CTkLabel(
            no_med_card,
            text="⚠️ ไม่พบข้อมูลการตั้งค่ายา",
            font=("TH Sarabun New", 18, "bold"),
            text_color="#856404",
            fg_color="transparent"
        )
        warning_label.pack(pady=20)
        
        self.medication_labels.extend([no_med_card, warning_label])

    def show_medication_error(self):
        """แสดงข้อความผิดพลาดเมื่อโหลดข้อมูลยาไม่สำเร็จ"""
        error_card = ctk.CTkFrame(
            self.medication_list_frame,
            height=80,
            corner_radius=10,
            fg_color="#F8D7DA",
            border_width=1,
            border_color="#F5C6CB"
        )
        error_card.pack(pady=30, padx=10, fill="x")
        
        error_label = ctk.CTkLabel(
            error_card,
            text="❌ เกิดข้อผิดพลาดในการโหลดข้อมูลยา",
            font=("TH Sarabun New", 16, "bold"),
            text_color="#721C24",
            fg_color="transparent"
        )
        error_label.pack(pady=20)
        
        self.medication_labels.extend([error_card, error_label])
class Frame2(ctk.CTkFrame): 
    def on_show(self):
        print("Frame2 is now visible")
        self.load_medications()
        self.refresh_medications()

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.medications = []
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
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังโหลดข้อมูลยา...", "กรุณารอสักครู่")
        
        def load_medications_thread():
            try:
                medicine_data = manageMedic.getMedicine(
                    self.controller.user['id'], self.controller.user['device_id']
                )
                if medicine_data['status']:
                    self.medications = medicine_data['Data']
                    print(self.medications)
                else:
                    self.medications = []
                    print(medicine_data['message'])
                
                # อัปเดต UI และซ่อนหน้าดาวโหลด
                self.controller.after(0, self.refresh_medications)
                self.controller.after(0, self.controller.hide_loading)
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")
                self.controller.after(0, self.controller.hide_loading)
        
        threading.Thread(target=load_medications_thread, daemon=True).start()

    def delete_medication(self, medicine_id):
        print(medicine_id)
        confirm = messagebox.askyesno("ยืนยัน", "คุณต้องการลบยานี้หรือไม่?")
        if confirm:
            delete_medic = manageMedic.DeleteMedic(medicine_id)
            if delete_medic['status']:
                self.medications = [med for med in self.medications if med['medicine_id'] != medicine_id]
                messagebox.showinfo("สำเร็จ", delete_medic['message'])
            else:
                messagebox.showerror("ล้มเหลว", delete_medic['message'])
            self.refresh_medications()

    def refresh_medications(self):
        for widget in self.sub_frame.winfo_children():
            widget.destroy()

        if not self.medications:
            no_data_label = ctk.CTkLabel(
                self.sub_frame,
                text="ไม่มีข้อมูล",
                text_color="black",
                fg_color="transparent",
                font=("TH Sarabun New", 24, "bold")
            )
            no_data_label.pack(pady=10, fill="x")
            return

        for index, med in enumerate(self.medications):
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
                    ai_advice = ai.save_advice(self.controller.user['id'], self.systolic_var.get(), self.diastolic_var.get(), self.pulse_var.get())
                    if ai_advice['status']:
                        self.controller.advice = ai_advice['Advice']
                        sendtoTelegram(ai_advice['Advice'], self.controller.user['telegram_key'], self.controller.user['telegram_id'])
                        controller.after(0, lambda: controller.show_frame(AIgen))
                    else:
                        print(ai_advice['message'])
                        controller.after(0, controller.hide_loading)
                except Exception as e:
                    print(f"เกิดข้อผิดพลาด: {e}")
                    controller.after(0, controller.hide_loading)
            
            threading.Thread(target=save_advice_thread, daemon=True).start()
            
        save_button = ctk.CTkButton(frame, text="บันทึกและกลับสู่หน้าหลัก", width=300, height=70, fg_color=force_color, 
                                    text_color="white", font=("Arial", 24, "bold"), command=save_and_go_home)

        clear_button = ctk.CTkButton(frame, text="ล้างข้อมูล", width=200, height=70, fg_color=bottom_hover,
                                     text_color="white", font=("Arial", 24, "bold"), command=clear_data)

        save_button.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        clear_button.grid(row=7, column=1, padx=20, pady=10, sticky="ew")




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

            if not len(new_meds) == 0:
                insert_new_medic = manageMedic.insertMedic(
                    self.controller.user['id'],
                    self.controller.user['device_id'],
                    new_meds
                )
                print(insert_new_medic['message'])
            else:
                print('ไม่พบข้อมูลยาใหม่กรุณากรอกข้อมูลยาก่อนกดบันทึก')

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
            text="ย้อนกลับ",                      # ไม่ใส่ข้อความ
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
        self.back_button.pack(side="right", padx=10, pady=10)

        self.time_options = ["เช้า", "กลางวัน", "เย็น", "ก่อนนอน"]

        # === Parent Frame ===
        parent_frame = ctk.CTkFrame(
            self, width=750, height=450, corner_radius=0,
            fg_color="#FFFFFF", bg_color="#000001"
        )
        parent_frame.place(relx=0.5, rely=0.5, anchor="center")
        parent_frame.pack_propagate(False)  # กันไม่ให้ขนาดเปลี่ยนตามลูก
        #pywinstyles.set_opacity(parent_frame, value=0.9,color="#000001")
        
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
        self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}  # เก็บข้อมูลยาแต่ละมื้อ
        self.med_combos = {}      # เก็บ reference ของ combobox ยา
        self.entry_frames = {}

    def update_meal_config(self):
        # แสดงหน้าดาวโหลด
        self.controller.show_loading("กำลังโหลดข้อมูลยา...", "กรุณารอสักครู่")
        
        def update_meal_config_thread():
            try:
                #logic ฝั่ง server
                medicine_data = manageMedic.getMedicine(self.controller.user['id'],self.controller.user['device_id'])
                if medicine_data['status']: 
                    self.medicine_map = {
                                        med["medicine_name"]: med["medicine_id"]
                                        for med in medicine_data["Data"]
                                        }
                    with open("meal_config.json", "r") as f:
                        meal_config = json.load(f)
                        self.num_meals = int(meal_config["meals"].split()[0])
                    
                    # อัปเดต UI และซ่อนหน้าดาวโหลด
                    self.controller.after(0, self.process_meal_config_update)
                else :
                    print(medicine_data['message'])
                    self.controller.after(0, self.controller.hide_loading)
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")
                self.controller.after(0, self.controller.hide_loading)
        
        threading.Thread(target=update_meal_config_thread, daemon=True).start()
    
    def process_meal_config_update(self):
        """ประมวลผลการอัปเดต meal config หลังจากโหลดเสร็จ"""
        try:
            self.selected_time_periods = {}
            for i in range(len(self.pages)):
                self.selected_time_periods[i] = {}

            self.pages = []
            self.current_page = 0

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
        
        # ใช้ entry_frames เป็นหลักในการวนลูป
        for meal_name, entry_frame in self.entry_frames.items():
            # ตรวจสอบว่ามีข้อมูลเวลาหรือไม่
            if meal_name not in self.time_entries or meal_name not in self.time_selects:
                continue
                
            # ดึงค่าจริงจาก ComboBox ช่วงเวลา
            time_period = self.time_selects[meal_name].get()
            
            # ดึงค่าเวลาจริง
            time_value = self.time_entries[meal_name].get()
            
            # รวบรวม ID ยา
            med_ids = []
            if meal_name in self.med_combos:
                for med_combo in self.med_combos[meal_name]:
                    med_name = med_combo.get()
                    if med_name in self.medicine_map and med_name != "เลือกยา":
                        med_ids.append(self.medicine_map[med_name])
            
            # บันทึกข้อมูลโดยใช้ช่วงเวลาจริงที่ผู้ใช้เลือก
            meal_data[time_period] = {
                "time": time_value if time_value else "00:00",
                "medications": med_ids
            }
   
        print("บันทึกข้อมูลสำเร็จ! ข้อมูลที่บันทึก:", meal_data)
        all_selected_periods = []
        for page_idx, selections in self.selected_time_periods.items():
            all_selected_periods.extend(selections.values())
        
        # ตรวจสอบว่ามีค่าซ้ำกันหรือไม่ (ไม่นับค่าว่าง)
        selected_periods = [p for p in all_selected_periods if p and p != "เลือกช่วงเวลา"]
        if len(selected_periods) != len(set(selected_periods)):
            # มีการเลือกซ้ำกัน
            messagebox.showerror("ข้อผิดพลาด", "มีการเลือกช่วงเวลาซ้ำกัน กรุณาตรวจสอบอีกครั้ง")
            return
        insert_meal = set_dispensing_time.set_meal(self.controller.user['device_id'],self.controller.user['id'],meal_data)
        if( insert_meal['status']):
            print(insert_meal['message'])
            self.controller.show_frame(HomePage)
            meal_data.clear()
            self.med_combos.clear()
            self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}
        else:
            print(insert_meal['message'])
            meal_data.clear()
            self.med_combos.clear()
            self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}
        
    def on_show(self):
        print("MedicationApp is now visible")
        self.update_meal_config()

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

            self.entry_telegram_token.delete(0, 'end')
            self.entry_telegram_token.insert(0, str(data.get('telegram_key', '')))

            self.entry_telegram_id.delete(0, 'end')
            self.entry_telegram_id.insert(0, str(data.get('telegram_id', '')))

            self.entry_telegram_group.delete(0, 'end')
            self.entry_telegram_group.insert(0, str(data.get('url2', '')))
            
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
                                   width=750, height=440)
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
        entry_status = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        entry_status.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        entry_status.insert(0, "online")
        entry_status.bind("<Key>", disable_editing)

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
        ctk.CTkLabel(form_frame, text="หมายเลขโทเคน", text_color="black", font=("Arial", 18)).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.entry_telegram_token = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_telegram_token.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Row 6
        ctk.CTkLabel(form_frame, text="ไอดี เทเลแกรม", text_color="black", font=("Arial", 18)).grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.entry_telegram_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_telegram_id.grid(row=6, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="ลิงค์กลุ่ม", text_color="black", font=("Arial", 18)).grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.entry_telegram_group = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 18))
        self.entry_telegram_group.grid(row=7, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Save Button
        def save_data():
            success = manageData.updateData(
                self.userid,
                self.result['device_id'],
                self.entry_line_id.get(),
                self.entry_telegram_token.get(),
                self.entry_telegram_id.get(),
                self.entry_telegram_group.get()
            )
            if success['status']:
                print(success['message'])
                controller.show_frame(HomePage)
            else:
                print(success['message'])

        btn_save = ctk.CTkButton(form_frame, text="บันทึกข้อมูล", command=save_data,
                                 fg_color="green", text_color="white",
                                 font=("Arial", 20, "bold"), height=40, corner_radius=20)
        btn_save.grid(row=8, column=0, columnspan=4, pady=(10, 10))




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
            font=("TH Sarabun New", 15, "bold"), corner_radius=8,
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
            if(date_entry.get() == "" and end_entry.get() == ""):
                print('กรุณากำหนดวันที่เริ่มจ่ายยา')
                return

            setting_time = set_dispensing_time.set_time(
                self.controller.user['device_id'],
                date_entry.get(), end_entry.get()
            )
            if setting_time['status']:
                print(setting_time['message'])
                controller.show_frame(MedicationApp)
            else:
                print(setting_time['message'])
        
        # ปุ่มบันทึกแบบ Premium
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
                
                if result['status']:
                    self.data = result['data']
                    self.page = 1
                    # อัปเดต UI
                    self.controller.after(0, lambda: self.display_table())
                    self.controller.after(0, lambda: self.export_button.configure(command=lambda: generate_pdf_sync(self.userid,)))
                    self.controller.after(0, self.controller.hide_loading)
                else:
                    print(result['message'])
                    self.controller.after(0, self.controller.hide_loading)
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")
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
                month_th = thai_months[date_obj.month - 1]
                dt = f"{date_obj.day:02d} {month_th} {date_obj.year + 543} เวลา {date_obj.strftime('%H:%M')}"
            except Exception:
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
        try:
            result = heart_report().generate_advice(self.controller.user['id'])
            if result['status']:
                heart_info_json = json.dumps(result['data'], ensure_ascii=False)
                prompt = f"นี่คือรายงานค่าความดันสูง ความดันต่ำ และค่าชีพจรในแต่ละวัน มีข้อมูลตามนี้: {heart_info_json} ช่วยประเมินโรคที่อาจเกิดขึ้นและให้คำแนะนำในการดูแลตัวเองและการปรับพฤติกรรมที่เหมาะสม"

                gemini = Gemini()
                ai_text = gemini.Advice(prompt)

                # ✅ อัปเดต Textbox แสดง AI
                self.after(0, lambda: self.update_ui(result, ai_text))
            else:
                print("เกิดข้อผิดพลาด:", result['message'])
                self.controller.after(0, self.controller.hide_loading)
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
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
        # ปรับขนาดฟอนต์ของ header
        for col, header in enumerate(self.headers):
            label = ctk.CTkLabel(self.scroll_frame, text=header, font=("Arial", 20, "bold"),
                                 text_color="black", width=self.column_widths[col])
            label.grid(row=0, column=col, padx=3, pady=3)

        for i, row in enumerate(data):
            systolic = f"{row['systolic_pressure']} mmHg"
            diastolic = f"{row['diastolic_pressure']} mmHg"
            pulse = f"{row['pulse_rate']} bpm"
            try:
                date = datetime.strptime(str(row['date']), "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y เวลา %H:%M น.")
            except:
                date = str(row['date'])

            values = [str(i+1), systolic, diastolic, pulse, None, date]

            heart_id = row['heart_id']
            advice_text = heart_report().get_heart_advice(heart_id)

            for col, val in enumerate(values):
                if col == 4:
                    # ปรับขนาดปุ่มคำแนะนำ
                    advice_btn = ctk.CTkButton(self.scroll_frame, text="!", width=35, height=25,
                                               command=lambda a=advice_text: self.show_advice_popup(a),
                                               fg_color="#495057", hover_color="#FF0000", text_color="white")
                    advice_btn.grid(row=i+1, column=col, padx=3, pady=3)
                else:
                    # ปรับขนาดฟอนต์ของข้อมูล
                    label = ctk.CTkLabel(self.scroll_frame, text=val, font=("Arial", 18),
                                         text_color="black", width=self.column_widths[col])
                    label.grid(row=i+1, column=col, padx=3, pady=3)
                    
                    
                    
# class Report3(ctk.CTkFrame):
#     def __init__(self, parent, controller):
#         super().__init__(parent)
#         self.controller = controller

#         # พื้นหลัง
#         bg_image = Image.open("imgNew/pagereport1.png").resize((1920, 1080), Image.Resampling.LANCZOS)
#         bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
#         bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
#         bg_label.place(x=0, y=0, relwidth=1, relheight=1)

#         # กรอบข้อมูล
#         info_frame = ctk.CTkFrame(self, fg_color="#e0e0e0", corner_radius=20)
#         info_frame.place(relx=0.5, rely=0.3, anchor="center")

#         # หัวข้อ "ข้อมูลผู้ป่วย" อยู่ในกรอบและตรงกลางบนสุด
#         header = ctk.CTkLabel(info_frame, text="ข้อมูลผู้ป่วย", font=("TH Sarabun New", 36, "bold"), text_color="black")
#         header.grid(row=0, column=0, columnspan=4, pady=(20, 10), sticky="n")

#         # ข้อมูลฝั่งซ้าย
#         left_data = [
#             ("ชื่อจริง:", "-"),
#             ("วัน / เดือน / ปี:", "-"),
#             ("ที่อยู่:", "-"),
#             ("โรคประจำตัว:", "-")
#         ]

#         # ข้อมูลฝั่งขวา
#         right_data = [
#             ("นามสกุล:", "-"),
#             ("เพศ:", "-")
#         ]

#         # แสดงข้อมูลฝั่งซ้าย (เริ่ม row=1)
#         for i, (label, value) in enumerate(left_data):
#             ctk.CTkLabel(info_frame, text=label, font=("TH Sarabun New", 28, "bold"),
#                          text_color="black", anchor="w", width=200).grid(row=i+1, column=0, padx=20, pady=10, sticky="w")
#             ctk.CTkLabel(info_frame, text=value, font=("TH Sarabun New", 28),
#                          text_color="black", anchor="w", width=300).grid(row=i+1, column=1, padx=10, pady=10, sticky="w")

#         # แสดงข้อมูลฝั่งขวา (เริ่ม row=1 เช่นกัน เพื่อให้เทียบกับฝั่งซ้าย)
#         for i, (label, value) in enumerate(right_data):
#             ctk.CTkLabel(info_frame, text=label, font=("TH Sarabun New", 28, "bold"),
#                          text_color="black", anchor="w", width=200).grid(row=i+1, column=2, padx=40, pady=10, sticky="w")
#             ctk.CTkLabel(info_frame, text=value, font=("TH Sarabun New", 28),
#                          text_color="black", anchor="w", width=300).grid(row=i+1, column=3, padx=10, pady=10, sticky="w")

#         # Navbar ด้านล่าง
#         navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
#         navbar.pack(side="bottom", fill="x")

#         page_title = ctk.CTkLabel(
#             navbar,
#             text="ข้อมูลผู้ใช้งาน",
#             font=("Arial", 50, "bold"),
#             text_color="black"
#         )
#         page_title.pack(side="left", padx=20, pady=20)

#         back_button = ctk.CTkButton(
#             navbar,
#             text="←",
#             width=150,
#             height=100,
#             corner_radius=35,
#             fg_color=force_color,
#             hover_color="#FF0000",
#             text_color="white",
#             font=("Arial", 44, "bold"),
#             command=lambda: controller.show_frame(HomePage)
#         )
#         back_button.pack(side="right", padx=10, pady=20)


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

            

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user = None
        self.title("เครื่องโฮมแคร์อัจฉริยะควบคุมผ่านระบบ SeniorCare Pro")
        
        # ปรับขนาดหน้าจอเป็น 1024x600
        self.geometry("1024x800")
        
        # ปรับการตั้งค่าหน้าต่างสำหรับจอเล็ก
        self.resizable(False, False)  # ป้องกันการปรับขนาด
        
        # ตั้งค่าให้เป็น fullscreen หรือ center window (optional)
        # self.attributes("-fullscreen", True)  # uncomment สำหรับ fullscreen
        
        # Center window on screen
        self.update_idletasks()
        width = 1024
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.advice = ''
        
        # สร้าง container frame
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        # สร้างและจัดการ frames ต่างๆ
        self.frames = {}
        
        # รายการ frames ที่จะสร้าง
        frame_classes = (
            HomePage, Frame2, Frame3, Frame4, add_Frame, info, 
            MedicationApp, AIgen, MedicationScheduleFrame, 
            ReportFrame, Report1, Report2, login, Wificonnect, LoadingScreen
        )
        
        for F in frame_classes:
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)
        
        # เพิ่มบรรทัดนี้
        setup_global_click_handler(self)
        
        # โหลดข้อมูลผู้ใช้และแสดงหน้าที่เหมาะสม
        self.load_user_data()
    
    def load_user_data(self):
        """โหลดข้อมูลผู้ใช้จากไฟล์"""
        if os.path.exists("user_data.json"):
            try:
                with open("user_data.json", "r", encoding='utf-8') as f:
                    user_data = json.load(f)
                print(f"โหลดข้อมูลผู้ใช้: {user_data}")
                
                if user_data:
                    self.user = user_data
                    self.show_frame(HomePage)
                else:
                    self.show_frame(login)
            except Exception as e:
                print(f"เกิดข้อผิดพลาดขณะโหลด user_data.json: {e}")
                self.show_frame(login)
        else:
            print("ไม่พบไฟล์ user_data.json - แสดงหน้า login")
            self.show_frame(login)
    
    def _lift_frame(self, frame_class, call_on_show=True):
        """ยก frame ขึ้นมาแสดง โดยเลือกได้ว่าจะเรียก on_show หรือไม่"""
        try:
            frame = self.frames[frame_class]
            frame.lift()
            # จดจำ frame ปัจจุบันที่กำลังแสดง
            self._current_frame_class = frame_class
            
            # ซ่อน keyboard เมื่อเปลี่ยนหน้า
            if frame_class not in [login, Wificonnect, add_Frame, LoadingScreen]:
                hide_onboard()
            
            if call_on_show:
                if hasattr(frame, 'on_show'):
                    frame.on_show()
                else:
                    print(f"Frame {frame_class.__name__} ไม่มี method on_show")
        except KeyError:
            print(f"ไม่พบ frame: {frame_class}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการแสดง frame: {e}")

    def show_frame(self, frame_class):
        """แสดง frame ที่ระบุ และเรียก on_show"""
        self._lift_frame(frame_class, call_on_show=True)
    
    def show_loading(self, message="กำลังโหลดข้อมูล...", detail=""):
        """แสดงหน้าดาวโหลด"""
        loading_frame = self.frames[LoadingScreen]
        # เก็บหน้าก่อนหน้าเพื่อนำกลับหลังโหลดเสร็จ (ครั้งแรกเท่านั้นขณะกำลังโหลด)
        if not hasattr(self, "_loading_active") or not self._loading_active:
            self._previous_frame_class = getattr(self, "_current_frame_class", None)
        self._loading_active = True
        loading_frame.show_loading(message, detail)
        self._lift_frame(LoadingScreen, call_on_show=False)
    
    def hide_loading(self):
        """ซ่อนหน้าดาวโหลด"""
        loading_frame = self.frames[LoadingScreen]
        loading_frame.hide_loading()
        # กลับไปยังหน้าก่อนหน้าถ้ามี
        if getattr(self, "_loading_active", False):
            self._loading_active = False
            if hasattr(self, "_previous_frame_class") and self._previous_frame_class:
                # กลับหน้าเดิม โดยไม่เรียก on_show ซ้ำ
                self._lift_frame(self._previous_frame_class, call_on_show=False)
            self._previous_frame_class = None

    
    def set_fullscreen(self, enable=True):
        """ตั้งค่าโหมด fullscreen"""
        self.attributes("-fullscreen", enable)
    
    def toggle_fullscreen(self):
        """สลับโหมด fullscreen"""
        current = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current)
    
    def exit_fullscreen(self):
        """ออกจากโหมด fullscreen"""
        self.attributes("-fullscreen", False)
    
    def center_window(self):
        """จัดหน้าต่างให้อยู่กึ่งกลางจอ"""
        self.update_idletasks()
        width = 1024
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """จัดการเมื่อปิดแอปพลิเคชัน"""
        try:
            # บันทึกข้อมูลก่อนปิด (หากจำเป็น)
            print("กำลังปิดแอปพลิเคชัน...")
            self.destroy()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะปิดแอปพลิเคชัน: {e}")
            self.destroy()


def main():
    """ฟังก์ชันหลักสำหรับรันแอปพลิเคชัน"""
    try:
        # สร้างและรันแอปพลิเคชัน
        app = MainApp()
        
        # ตั้งค่า protocol สำหรับการปิดหน้าต่าง
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # เพิ่ม keyboard shortcuts (optional)
        app.bind('<F11>', lambda e: app.toggle_fullscreen())
        app.bind('<Escape>', lambda e: app.exit_fullscreen())
        
        print("เริ่มต้นแอปพลิเคชัน SeniorCare Pro")
        app.mainloop()
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะรันแอปพลิเคชัน: {e}")


if __name__ == "__main__":
    main()
