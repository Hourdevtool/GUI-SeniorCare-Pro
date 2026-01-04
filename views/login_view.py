import customtkinter as ctk
from PIL import Image
import threading
import json
import os
from lib.loadenv import PATH
from lib.set_time import default_serializer
from utils.helpers import show_onboard, hide_onboard, create_entry_with_keyboard, toggle_language
from models.app_services import auth_service as auth
# We will import HomePage later in the controller or lazily to avoid circular imports.
# Ideally, the controller switches view, so View shouldn't import other Views. 
# But the original code calls controller.show_frame(HomePage).
# We will use string "HomePage" or pass it via controller if possible, 
# or just assume HomePage is registered in controller.

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
        
        # === เลือกระดับผู้ใช้ (User Role Selection) - ตกแต่งให้สวยงาม ===
        # (จะย้ายไปไว้หลังคำอธิบาย)
        self.user_role_var = ctk.StringVar(value="patient")
        
        # === ตัวแปรเก็บข้อมูล (Data Variables) ===
        self.username = ctk.StringVar()         
        self.password = ctk.StringVar()          
        
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
        logo_frame.grid(row=1, column=0, columnspan=2, pady=(20, 20))
        
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

        # === ปุ่มเปลี่ยนภาษา (Language Toggle) ===
        lang_button = ctk.CTkButton(
            frame,
            text="TH/EN",
            width=50,
            height=30,
            corner_radius=10,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            font=("Arial", 10, "bold"),
            command=toggle_language
        )
        lang_button.place(relx=0.95, rely=0.05, anchor="ne")
        
        # === หัวข้อหลัก (Main Title) ===
        ctk.CTkLabel(             
            frame,             
            text="ลงชื่อเข้าใช้ด้วยอีเมล",             
            font=("Arial", 28, "bold"),             
            text_color="#1a1a1a",         
        ).grid(row=2, column=0, columnspan=2, pady=(20, 10))     
        
        # === คำอธิบาย (Description) ===
        ctk.CTkLabel(             
            frame,             
            text="สร้างเอกสารใหม่สำหรับใช้กับเครื่องจ่าย\nของคุณบนเว็บไซต์ของเรา",             
            font=("Arial", 14),             
            text_color="#666666",
            justify="center"         
        ).grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # === เลือกระดับผู้ใช้ (User Role Selection) แบบภาพตัวอย่าง ===
        role_container = ctk.CTkFrame(
            frame,
            fg_color="#E7F5FF",        # พื้นหลังฟ้าอ่อน
            corner_radius=15,
            border_width=1,
            border_color="#8acbff"
        )
        role_container.grid(row=4, column=0, columnspan=2, pady=(0, 20), padx=30, sticky="ew")
        role_container.grid_columnconfigure(0, weight=1)


        # === Header ข้างบนเหมือนภาพ ===
        header_frame = ctk.CTkFrame(
            role_container,
            fg_color="#D9F0FF",        # สีหัวข้อฟ้าอ่อนกว่า
            corner_radius=10,
            height=48
        )
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # ไอคอน + ข้อความ
        icon_label = ctk.CTkLabel(
            header_frame,
            text="👤",
            font=("Arial", 20),
            text_color="#1D3557"
        )
        icon_label.pack(side="left", padx=(15, 8), pady=10)

        title_label = ctk.CTkLabel(
            header_frame,
            text="เลือกระดับผู้ใช้",
            font=("TH Sarabun New", 20, "bold"),
            text_color="#1D3557"
        )
        title_label.pack(side="left", pady=10)
        
        # === กรอบสำหรับ Combobox สไตล์เหมือนภาพ ===
        cb_frame = ctk.CTkFrame(
            role_container,
            fg_color="#BEE3FF",    # สีพื้นหลังฟ้าใส
            corner_radius=12
        )
        cb_frame.pack(fill="x", padx=10, pady=(5, 15))
        
        # Mapping ระหว่างชื่อภาษาไทยกับค่า urole
        self.role_mapping = {
            "ผู้ป่วย": "patient",
            "ผู้ดูแลผู้ป่วย": "user",
            "ผู้ดูแลระบบ": "admin"
        }
        
        # ==== Combobox ====
        self.role_combobox = ctk.CTkComboBox(
            cb_frame,
            values=["ผู้ป่วย", "ผู้ดูแลผู้ป่วย", "ผู้ดูแลระบบ"],
            variable=self.user_role_var,
            font=("TH Sarabun New", 20, "bold"),
            height=40,
            dropdown_font=("TH Sarabun New", 25),

            fg_color="#FFFFFF",
            button_color="#8acbff",
            button_hover_color="#6fb3e8",

            border_color="#8acbff",
            border_width=1,
            corner_radius=10,

            text_color="#1D3557",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#1D3557",
            dropdown_hover_color="#E5F4FF"
        )
        self.role_combobox.pack(fill="x", padx=15, pady=10)
        self.role_combobox.set("ผู้ป่วย")
        
        # === ช่องกรอกอีเมล - แก้ไขส่วนนี้ ===
        email_frame = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=8, height=50)
        email_frame.grid(row=5, column=0, columnspan=2, padx=30, pady=(0, 15), sticky="ew")
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
        email_entry.insert(0, 'siri@gmail.com')
        # === ช่องกรอกรหัสผ่าน - แก้ไขส่วนนี้ ===
        password_frame = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=8, height=50)
        password_frame.grid(row=6, column=0, columnspan=2, padx=30, pady=(0, 15), sticky="ew")
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
        self.password.set('test')

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
                print('Please fill in the information correctly.')                 
                return              
            
            # แสดงหน้าดาวโหลด
            controller.show_loading("กำลังเข้าสู่ระบบ...", "กรุณารอสักครู่")
            
            def login_thread():
                try:
                    result = auth.login(self.username.get(), self.password.get())
                    
                    if result['status']:
                        self.controller.user = result['user']
                        self.controller.login_mode() # Update test mode status

                        self.controller.network_status_var.set("online")

                        self.controller.start_network_monitor_service()
                        
                        # Save selected user role (override server role if needed)
                        selected_role_thai = self.user_role_var.get()
                        selected_role = self.role_mapping.get(selected_role_thai, "patient")
                        result['user']['urole'] = selected_role
                        result['user']['login_mode'] = selected_role  # Keep for backward compatibility
                        

                        with open('user_data.json', 'w', encoding='utf-8') as f:
                            json.dump(result['user'], f, ensure_ascii=False, indent=4, default=default_serializer)

                        self.controller.notifier.show_notification(result['message'], success=True)

                        def go_home():
                            # Import HomePage locally to avoid circular dependency
                            from views.home_view import HomePage
                            controller._previous_frame_class = None 
                            controller.hide_loading()
                            controller.show_frame(HomePage)

                        controller.after(0, go_home)
                    else:
                        self.controller.notifier.show_notification(result['message'], success=False)
                        controller.after(0, controller.hide_loading)
                except Exception as e:
                    self.controller.notifier.show_notification(f"เกิดข้อผิดพลาด: {e}", success=False)
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
        save_button.grid(row=7, column=0, columnspan=2, padx=30, pady=(0, 40), sticky="ew")
        
        # === การตั้งค่า Grid Layout ===
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
