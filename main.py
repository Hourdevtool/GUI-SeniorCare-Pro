import customtkinter as ctk
from PIL import Image, ImageTk
import time
from tkinter import messagebox
import subprocess
import threading
import json
import os
from tkcalendar import Calendar
from datetime import datetime, timedelta
from pywifi import PyWiFi
from babel.dates import format_date
# model format เวลา
from lib.set_time import default_serializer

# nodel การเเจ้งเตือน
from lib.alert import sendtoTelegram

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
auth = auth()
manageData = infoData()
manageMedic = manageMedicData()
set_dispensing_time = setting_eat_time()
ai = Gemini()
Heart_report = heart_report()
medicine_report = eat_medicine_report()
# -----------------------------------------------------


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
word_color = '#1D3557'
bottom_hover = "#FF0000"
ho_color = "#5EBA91"
select_color ='#5FDF9F'

back_color = '#E8F6EF'
force_color = '#2D6A4F'
text_main = '#1D3557'
hover_color = "#40916C"
input_color = "white"
input_text = "black"


class login(ctk.CTkFrame):
    def on_show(self):
        print("login is now visible")

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # พื้นหลังแบบรูปภาพ
        bg_image = Image.open("imgNew/Wellcome.png").resize((1920, 1080), Image.Resampling.LANCZOS) 
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # กล่องล็อกอิน
        frame = ctk.CTkFrame(
            self,
            width=900,
            height=700,
            corner_radius=30,
            fg_color=back_color,
            bg_color="#1d567b"
        )
        frame.place(relx=0.76, rely=0.5, anchor="center")

        # หัวข้อ "เข้าสู่ระบบ"
        ctk.CTkLabel(
            frame,
            text="เข้าสู่ระบบ",
            font=("Arial", 50, "bold"),
            text_color=input_text,
            fg_color=back_color,
            bg_color=back_color
        ).grid(row=0, column=0, columnspan=2, pady=(30, 10))

        self.username = ctk.StringVar()
        self.password = ctk.StringVar()

        # ฟังก์ชันสร้างกล่องกรอกข้อมูล
        def create_input(label_text, var, row, show=None):
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 36), text_color=text_main, bg_color=back_color)
            entry = ctk.CTkEntry(
                frame,
                textvariable=var,
                width=800,
                height=70,
                font=("Arial", 36),
                fg_color=input_color,
                text_color=input_text,
                corner_radius=15,
                show=show
            )
            label.grid(row=row, column=0, padx=40, pady=(30, 0), sticky="w")
            entry.grid(row=row + 1, column=0, columnspan=2, padx=40, pady=(0, 10), sticky="ew")

        # กรอกเบอร์หรืออีเมล / รหัสผ่าน
        create_input("เบอร์โทรหรืออีเมล", self.username, 1)
        create_input("รหัสผ่าน", self.password, 3, show="*")

        # ปุ่มตกลง
        def save_and_go_home():
            if len(self.username.get().strip()) == 0 and len(self.password.get().strip()) == 0:
                print('กรุณากรอกข้อมูลให้ถูกต้องตามแบบฟอร์ม')
                return

            result = auth.login(self.username.get(), self.password.get())
            print(result)
            if result['status']:
                self.controller.user = result['user']
                with open('user_data.json', 'w', encoding='utf-8') as f:
                    json.dump(result['user'], f, ensure_ascii=False, indent=4, default=default_serializer)
                print(result['message'])
                controller.show_frame(Wificonnect)
            else:
                print(result['message'])

        save_button = ctk.CTkButton(
            frame,
            text="ตกลง",
            width=800,
            height=70,
            fg_color=force_color,
            hover_color=hover_color,
            text_color="white",
            font=("Arial", 42, "bold"),
            corner_radius=20,
            command=save_and_go_home
        )
        save_button.grid(row=6, column=0, padx=40, pady=(40, 30), sticky="ew")
        

class HomePage(ctk.CTkFrame):
    def on_show(self):
        print("HomePage is now visible")

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # พื้นหลัง
        bg_image = Image.open("imgNew/Home.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ไอคอน battery และ wifi
        self.add_status_icons()

        # ปุ่ม
        self.create_menu_buttons(controller)

        # วันที่และเวลา
        self.date_label = ctk.CTkLabel(self, text="", font=("TH Sarabun New", 48, "bold"), fg_color="#d8eeeb", text_color="black")
        self.date_label.place(x=50, y=420)

        self.time_label = ctk.CTkLabel(self, text="", font=("TH Sarabun New", 90, "bold"), fg_color="#d8eeeb", text_color="black")
        self.time_label.place(x=50, y=500)

        self.update_datetime()

    def add_status_icons(self):
        battery_image = Image.open("imgNew/battery.png").resize((64, 64), Image.Resampling.LANCZOS)
        self.battery_photo = ImageTk.PhotoImage(battery_image)
        battery_label = ctk.CTkLabel(self, image=self.battery_photo, text="", bg_color="#1d567b")
        battery_label.place(x=1800, y=40)

        wifi_image = Image.open("imgNew/wi-fi.png").resize((64, 64), Image.Resampling.LANCZOS)
        self.wifi_photo = ImageTk.PhotoImage(wifi_image)
        wifi_label = ctk.CTkLabel(self, image=self.wifi_photo, text="", bg_color="#1d567b")
        wifi_label.place(x=1700, y=40)

    def create_menu_buttons(self, controller):
        btn_size = (180, 180)
        btn_images = {}

        paths = [
            "imgNew/iconuser.png", "imgNew/icontime.png", "imgNew/iconheath.png",
            "imgNew/icondog.png", "imgNew/iconreport.png", "imgNew/iconout.png",
            "imgNew/icondow.png"
        ]
        btn_texts = [
            "ข้อมูลผู้ใช้", "ตั้งเวลา", "สุขภาพ",
            "ข้อมูลยา", "รายงาน", "ออกระบบ", "ปิดเครื่อง"
        ]
        pages = [info, Frame3, Frame4, Frame2, ReportFrame, login]

        for i, path in enumerate(paths, start=1):
            try:
                img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)
                btn_images[i] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Error: {path} not found.")

        total_width = 7 * 200 + 6 * 20
        start_x = (1920 - total_width) // 2

        for i in range(7):
            if i + 1 in btn_images:
                text = btn_texts[i]

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
                    font=("TH Sarabun New", 36, "bold"),
                    fg_color="#BBEDD4",
                    hover_color="#A3D7C6",
                    text_color="black",
                    border_width=3,
                    border_color="#7EBCA2",
                    # corner_radius=25,
                    width=200,
                    height=220,
                    command=command
                )
                btn.place(x=start_x  - 100 + i * (200 + 50), y=700)

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

    def update_datetime(self):
        today = datetime.today()
        formatted_date = format_date(today, format="full", locale="th_TH")
        self.date_label.configure(text=formatted_date)

        current_time = time.strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.time_label.after(1000, self.update_datetime)


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

        bg_image = Image.open("imgNew/pullrepore.png").resize((1920, 1080), Image.Resampling.LANCZOS) 
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        

        navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="ตารางแสดงข้อมูลยา", font=("Arial", 50, "bold"), text_color="black")  
        page_title.pack(side="left", padx=20)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=20)

        add_button = ctk.CTkButton(navbar, text="เพิ่มข้อมูล", width=150, height=100, corner_radius=35, 
                                   fg_color=force_color, hover_color=select_color, text_color="white",
                                   font=("Arial", 44, "bold"),
                                   command=lambda: controller.show_frame(add_Frame))
        add_button.pack(side="right", padx=10, pady=20)

        self.frame = ctk.CTkScrollableFrame(self, width=1000, height=620, corner_radius=30, fg_color="#FFFFFF", bg_color="#1d567b") 
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        # ▶️ เพิ่มข้อความบนสุด
        title_label = ctk.CTkLabel(self.frame, text="ชนิดยา", font=("TH Sarabun New", 48, "bold"), text_color="black", fg_color="transparent")
        title_label.pack(pady=(20, 10))  # ระยะห่างบน-ล่างของข้อความ
        # ▶️ ปรับ Scrollbar สี
        self.frame._scrollbar.configure(fg_color="#bddeff", button_color=back_color, button_hover_color="#05C766")
        self.sub_frame = ctk.CTkFrame(self.frame, fg_color="#FFFFFF", width=400, height=100, corner_radius=30, bg_color=back_color)  
        self.sub_frame.pack(padx=20, pady=10, expand=True, fill="both")


    def go_to_add(self):
        threading.Thread(target=lambda: subprocess.Popen(["python", "Frame2-add.py"])).start()
        print("การแจ้งเตือน กำลังสลับไปยังหน้า Frame2-add.py")

    def load_medications(self):
            # logic ฝั่ง server
            medicine_data = manageMedic.getMedicine(self.controller.user['id'],self.controller.user['device_id'])
            if  medicine_data['status']:
                  self.medications =  medicine_data['Data']
                  print(self.medications)
            else:
                 self.medications = []
                 print(medicine_data['message'])

    def delete_medication(self,medicine_id):
        print(medicine_id)
        confirm = messagebox.askyesno("ยืนยัน", "คุณต้องการลบยานี้หรือไม่?")
        if confirm:
            # logic ฝั่ง server
            delete_medic = manageMedic.DeleteMedic(medicine_id)
            if delete_medic['status']:
                self.medications = [med for med in self.medications if med['medicine_id'] != medicine_id]
                messagebox.showinfo("สำเร็จ",delete_medic['message'])
            else:
                messagebox.showerror("ล้มเหลว",delete_medic['message'])   
            self.refresh_medications()


    def refresh_medications(self):
        for widget in self.sub_frame.winfo_children():
            widget.destroy()
        
        num_columns = 1
        for index, med in enumerate(self.medications):
            row = index // num_columns
            col = index % num_columns
            
            medicine_id = med['medicine_id']
            medicine_name = med['medicine_name']
            
            med_frame = ctk.CTkFrame(self.sub_frame, fg_color="#FFFFFF", corner_radius=10)
            med_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            med_label = ctk.CTkLabel(med_frame, text=medicine_name, text_color="black", fg_color="#FFFFFF", bg_color="#FFFFFF",font=("Arial", 24))
            med_label.pack(side="left", padx=10, pady=5)
            
            delete_button = ctk.CTkButton(med_frame, text="ลบ", width=100, height=70, corner_radius=15, 
                                          fg_color="#FF0000", hover_color="#CC0000", text_color="white",font=("Arial", 24),
                                          command=lambda medicine_id=medicine_id: self.delete_medication(medicine_id))
            delete_button.pack(side="right", padx=10, pady=5)
        
        for i in range(num_columns):
            self.sub_frame.grid_columnconfigure(i, weight=1)

        if not self.medications:
            no_data_label = ctk.CTkLabel(self.sub_frame, text="ไม่มีข้อมูล", text_color="black", fg_color="#FFFFFF", bg_color="#FFFFFF", width=400, height=100)  
            no_data_label.pack(pady=5, fill="x")



class Frame3(ctk.CTkFrame):
    def on_show(self):
        print("Frame3 is now visible")

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.selected_meal = ctk.StringVar(value="1 มื้อ")
        options = ["1 มื้อ", "2 มื้อ", "3 มื้อ", "4 มื้อ"]

        bg_image = Image.open("imgNew/pagetime.png").resize((1920, 1080), Image.Resampling.LANCZOS) 
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        content_frame = ctk.CTkFrame(self, width=1200, height=800, corner_radius=30, fg_color="#FFFFFF", bg_color="#1d567b")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        content_frame.grid_columnconfigure((0, 1), weight=1)

        # Title
        ctk.CTkLabel(content_frame, text="เลือกจำนวนมื้อจ่ายยา", text_color="#000000",
                     font=("Arial", 48, "bold")).grid(row=0, column=0, columnspan=2, pady=(60, 40))

        # Meal buttons
        self.buttons = []
        for i, option in enumerate(options):
            btn = ctk.CTkButton(content_frame, text=option, corner_radius=20, width=350, height=100,
                                fg_color=("#34C759" if option == self.selected_meal.get() else "#FFF3FF"),
                                text_color=("white" if option == self.selected_meal.get() else "#34C759"),
                                hover_color="#A8DADC", font=("Arial", 32, "bold"),
                                command=lambda opt=option: self.select_meal(opt))
            btn.grid(row=1 + i // 2, column=i % 2, padx=40, pady=20)
            self.buttons.append(btn)

        # Save button
        save_button = ctk.CTkButton(content_frame, text="✅ บันทึกและไปต่อ", corner_radius=20, width=600, height=100,
                                    fg_color="#2D6A4F", text_color="white", hover_color="#1B4332",
                                    font=("Arial", 36, "bold"), command=self.save_and_change_page)
        save_button.grid(row=3, column=0, columnspan=2, pady=(60, 20))

        # Bottom Navbar
        navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")

        page_title = ctk.CTkLabel(navbar, text="ตั้งค่าจำนวนมื้อจ่ายยา", font=("Arial", 50, "bold"), text_color="black")
        page_title.pack(side="left", padx=40, pady=20)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"), command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=20, pady=20)

    def select_meal(self, option):
        self.selected_meal.set(option)
        for i, btn in enumerate(self.buttons):
            if btn.cget("text") == option:
                btn.configure(fg_color="#34C759", text_color="white")
            else:
                btn.configure(fg_color="#FFFFFF", text_color="#34C759")

    def save_and_change_page(self):
        print(f"บันทึกการตั้งค่าจำนวนมื้อ: {self.selected_meal.get()}")
        with open("meal_config.json", "w") as f:
            json.dump({"meals": self.selected_meal.get()}, f)
        self.controller.show_frame(MedicationScheduleFrame)




class Frame4(ctk.CTkFrame):
    def on_show(self):
        print("Frame4 is now visible")

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
     
        bg_image = Image.open("imgNew/pageheath.png").resize((1920, 1080), Image.Resampling.LANCZOS) 
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = ctk.CTkFrame(self, width=1200, height=800, corner_radius=30, fg_color="#FFFFFF", bg_color="#1d567b") 
        frame.place(relx=0.5, rely=0.5, anchor="center")


        navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="วัดความดันและชีพจร", font=("Arial", 50, "bold"), text_color="black") 
        page_title.pack(side="left", padx=20, pady=20)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=5)

        self.systolic_var = ctk.StringVar()
        self.diastolic_var = ctk.StringVar()
        self.pulse_var = ctk.StringVar()

        def create_input(label_text, var, row):
            label = ctk.CTkLabel(frame, text=label_text, font=("Arial", 34), text_color="black") 
            entry = ctk.CTkEntry(frame, textvariable=var, width=1000, height=100, font=("Arial", 34), fg_color="white", text_color="black") 
            label.grid(row=row, column=0, padx=30, pady=(30, 0), sticky="w")
            entry.grid(row=row+1, column=0, columnspan=2, padx=30, pady=(0, 5), sticky="ew")

        create_input("ความดันสูงสุด (Systolic)", self.systolic_var, 0)
        create_input("ความดันต่ำสุด (Diastolic)", self.diastolic_var, 2)
        create_input("ชีพจร (Pulse)", self.pulse_var, 4)

        def clear_data():
            self.systolic_var.set("")
            self.diastolic_var.set("")
            self.pulse_var.set("")
            print("ข้อมูลถูกล้างเรียบร้อยแล้ว")

        def save_and_go_home():
            message = f'''
            📊 รายงานสุขภาพ\n
            👤 ชื่อผู้ใช้งาน: {self.controller.user['firstname_th']} - {self.controller.user['lastname_th']}\n
            💓 ความดันสูง: {self.systolic_var.get()} mmHg\n
            💓 ความดันต่ำ: {self.diastolic_var.get()} mmHg\n
            💓 ชีพจร: {self.pulse_var.get()} bpm
            '''
            sendtoTelegram(message, self.controller.user['telegram_key'], self.controller.user['telegram_id'])
            if len(self.systolic_var.get().strip())== 0 and len(self.diastolic_var.get().strip()) == 0 and len(self.pulse_var.get().strip()) == 0:
                print('กรุณากรอกข้อมูลให้ครบถ้วน')
                return
            ai_advice = ai.save_advice(self.controller.user['id'],self.systolic_var.get(),self.diastolic_var.get(),self.pulse_var.get())
            if ai_advice['status']:
                 self.controller.advice = ai_advice['Advice']
                 sendtoTelegram(ai_advice['Advice'], self.controller.user['telegram_key'], self.controller.user['telegram_id'])
                 controller.show_frame(AIgen)
            else:
                print(ai_advice['message'])
            
          
           

        save_button = ctk.CTkButton(frame, text="บันทึกและกลับสู่หน้าหลัก", width=400, height=100, fg_color=force_color, 
                                    text_color="white", font=("Arial", 34, "bold"), command=save_and_go_home)

        clear_button = ctk.CTkButton(frame, text="ล้างข้อมูล", width=400, height=100, fg_color=bottom_hover,
                                     text_color="white", font=("Arial", 34, "bold"), command=clear_data)

        save_button.grid(row=6, column=0, padx=30, pady=30, sticky="ew")
        clear_button.grid(row=6, column=1, padx=30, pady=30, sticky="ew")



class add_Frame(ctk.CTkFrame):
    def on_show(self):
        print("add_Frame is now visible")

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # พื้นหลัง
        bg_image = Image.open("imgNew/pagedog.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar ด้านล่าง
        navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")

        page_title = ctk.CTkLabel(navbar, text="เพิ่มข้อมูลยา", font=("Arial", 50, "bold"), text_color="black")
        page_title.pack(side="left", padx=20, pady=20)

        def go_back():
            controller.show_frame(Frame2)

        back_button = ctk.CTkButton(
            navbar, text="←", width=150, height=100, corner_radius=35,
            fg_color=force_color, hover_color=bottom_hover, text_color="white",
            font=("Arial", 44, "bold"), command=go_back
        )
        back_button.pack(side="right", padx=10, pady=20)

        # Scrollable Frame สำหรับเนื้อหา
        frame = ctk.CTkScrollableFrame(self, width=1100, height=620, corner_radius=30, fg_color=back_color, bg_color="#1d567b")
        frame.pack(padx=50, pady=160, expand=True)
        frame.pack_propagate(False)

        # ----------- MedicationApp ----------
        class MedicationApp(ctk.CTkFrame):
            def __init__(self, master=None):
                super().__init__(master, fg_color=back_color)
                self.med_entries = []
                self.create_widgets()
                self.med_entries.append((self.entry_med_name, None))

            def create_widgets(self):
                self.label_title = ctk.CTkLabel(self, text="เพิ่มข้อมูลยา", font=("Arial", 48, "bold"), text_color="black")
                self.label_title.grid(row=0, column=0, columnspan=2, pady=(10, 20))

                self.entry_med_name = ctk.CTkEntry(
                    self, placeholder_text="ชื่อยา", width=800, height=60,
                    fg_color="#FFFFFF", text_color="black", font=("Arial", 24)
                )
                self.entry_med_name.grid(row=1, column=0, padx=(50, 10), pady=(0, 10), sticky="w")

                self.add_button = ctk.CTkButton(
                    self, text="เพิ่มช่อง", height=60, width=200, font=("Arial", 24),
                    fg_color="#4CAF50", hover_color="#45A049", text_color="white",
                    command=self.add_medication_entry
                )
                self.add_button.grid(row=1, column=1, padx=(0, 50), pady=(0, 10), sticky="w")

            def add_medication_entry(self):
                row_index = len(self.med_entries) + 2
                entry = ctk.CTkEntry(
                    self, placeholder_text="ชื่อยา", width=800, height=60,
                    fg_color="#FFFFFF", text_color="black", font=("Arial", 24)
                )
                entry.grid(row=row_index, column=0, padx=(50, 10), pady=(0, 10), sticky="w")

                delete_button = ctk.CTkButton(
                    self, text="ลบ", height=60, width=200, fg_color="red",
                    hover_color="#cc0000", font=("Arial", 24),
                    command=lambda e=entry: self.remove_medication_entry(e)
                )
                delete_button.grid(row=row_index, column=1, padx=(0, 50), pady=(0, 10), sticky="w")

                self.med_entries.append((entry, delete_button))

            def remove_medication_entry(self, entry):
                for i, (e, b) in enumerate(self.med_entries):
                    if e == entry:
                        e.grid_remove()
                        b.grid_remove()
                        self.med_entries.pop(i)
                        break

        # เพิ่ม MedicationApp ลงใน Scrollable Frame
        self.med_frame = MedicationApp(master=frame)
        self.med_frame.grid(row=0, column=0, columnspan=2, pady=(20, 0))

        # ----------- ปุ่มยืนยันเพิ่มยาใหม่ ----------
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

        add_med_button = ctk.CTkButton(
            frame, text="ยืนยันการเพิ่มยาใหม่และกลับสู่หน้าตาราง",
            fg_color=force_color, hover_color="#0055A4", text_color="white",
            width=1000, height=70, font=("Arial", 24), command=save_medications
        )
        add_med_button.grid(row=1, column=0, columnspan=2, pady=30)










class AIgen(ctk.CTkFrame):
    def on_show(self):
      
        # modelการพูด
        print("AIgen is now visible")
        self.label.configure(text=self.controller.advice)

        tts = gTTS(text=self.controller.advice,lang='th')
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
        except Exception as e :
            print(f"เกิดข้อผิดพลาดขณะลบไฟล์: {e}")
        
        self.controller.show_frame(HomePage)


    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        bg_image = Image.open("imgNew/pageai.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = ctk.CTkScrollableFrame(self, width=1400, height=600, corner_radius=30, fg_color="#FFFFFF", bg_color="#1d567b")
        frame.place(relx=0.5, rely=0.51, anchor="center")

        navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="คำแนะนำจาก AI", font=("Arial", 50, "bold"), text_color="black")
        page_title.pack(side="left", padx=20, pady=20)

        back_button = ctk.CTkButton(navbar, text="ยืนยัน", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color=bottom_hover, text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=self.stop_and_go_home)
        back_button.pack(side="right", padx=10, pady=20)

        self.systolic_var = ctk.StringVar()
        self.diastolic_var = ctk.StringVar()
        self.pulse_var = ctk.StringVar()

        self.label = ctk.CTkLabel(frame, text='', font=("Arial", 30), text_color="black", wraplength=1400, justify="left") 
        self.label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")




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

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        bg_image = Image.open("imgNew/pagetime.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        

        self.navbar = ctk.CTkFrame(self, height=160, fg_color="#A8DADC", corner_radius=0)
        self.navbar.pack(side="bottom", fill="x")

        self.page_title = ctk.CTkLabel(self.navbar, text="ตารางแสดงข้อมูลยา", font=("Arial", 50, "bold"), text_color="black")  
        self.page_title.pack(side="left", padx=20)
        
        self.back_button = ctk.CTkButton(self.navbar, text="←", width=150, height=100, corner_radius=35, 
                                    fg_color=force_color, hover_color=bottom_hover, text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=self.go_back)
        self.back_button.pack(side="right", padx=10, pady=20)

        self.save_button = ctk.CTkButton(self.navbar, text="บันทึกและกลับหน้าหลัก", width=500, height=100,
                                         fg_color=force_color, text_color="white", hover_color="#002299",
                                         font=("Arial", 44, "bold"), command=self.save_and_go_to_frame1)
        self.save_button.pack(side="right", padx=20, pady=20)    

        self.time_options = ["เช้า", "กลางวัน", "เย็น", "ก่อนนอน"]

        self.frame_container = ctk.CTkScrollableFrame(self, width=1700, height=550, corner_radius=30, fg_color="#FFFFFF", bg_color="#1d567b")
        self.frame_container.place(relx=0.5, rely=0.5, anchor="center")


        self.current_page = 0
        self.pages = []
        self.time_entries = {}    # เก็บเวลาของแต่ละมื้อ
        self.time_selects = {}    # เก็บช่วงเวลาของแต่ละมื้อ
        self.med_entries = {"เช้า": [], "กลางวัน": [], "เย็น": [], "ก่อนนอน": []}  # เก็บข้อมูลยาแต่ละมื้อ
        self.med_combos = {}      # เก็บ reference ของ combobox ยา
        self.entry_frames = {}

      

    def update_meal_config(self):
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
        else :
                print(medicine_data['message'])
                return 

        # for widget in self.frame_container.winfo_children():
        #     widget.destroy()

        self.pages = []
        self.current_page = 0

        for i in range(0, self.num_meals, 2):
            page = ctk.CTkFrame(self.frame_container, fg_color=back_color, bg_color=back_color)
            self.pages.append(page)

        self.show_page(self.current_page)

        if self.num_meals > 2:
            if not hasattr(self, 'next_button'):
                self.next_button = ctk.CTkButton(self.navbar, text="ถัดไป", width=150, height=100,
                                                fg_color=force_color, text_color="white", hover_color="#002299",
                                                font=("Arial", 44, "bold"), command=self.next_page)
            self.next_button.pack(side="right", padx=10, pady=20)
        else:
            if hasattr(self, 'next_button'):
                self.next_button.pack_forget()


        if not hasattr(self, 'back_button'):
            self.back_button2 = ctk.CTkButton(self.navbar, text="ย้อนกลับ", width=200, height=100,
                                            fg_color=force_color, text_color="white", hover_color="#002299",
                                            font=("Arial", 44, "bold"), command=lambda: self.controller.show_frame(MedicationApp))
            self.back_button2.pack(side="right", padx=10, pady=20)

    def show_page(self, page_index):
        for widget in self.frame_container.winfo_children():
            widget.pack_forget()

        self.pages[page_index].pack(fill="both", expand=True)

        if page_index == 1 and hasattr(self, 'next_button'):
            self.next_button.pack_forget()
        elif page_index == 0 and hasattr(self, 'next_button'):
            self.next_button.pack(side="right", padx=10, pady=20)

        if page_index == 1:
            if not hasattr(self, 'back_button2'):
                self.back_button2 = ctk.CTkButton(
                    self.navbar, text="ย้อนกลับ", width=200, height=100,
                    fg_color=force_color, text_color="white", hover_color="#002299",
                    font=("Arial", 44, "bold"), command=lambda: self.controller.show_frame(MedicationApp)
                )
            self.back_button2.pack(side="right", padx=10, pady=20)
        elif hasattr(self, 'back_button2'):
            self.back_button2.pack_forget()

    
        if (page_index == len(self.pages) - 1) or self.num_meals <= 2:
            self.save_button.pack(side="right", padx=20, pady=20)
        else:
            self.save_button.pack_forget()

        self.pages[page_index].pack(fill="both", expand=True)

        for i in range(page_index * 2, min((page_index + 1) * 2, self.num_meals)):
            meal_name = self.time_options[i]

            meal_label = ctk.CTkLabel(
                self.pages[page_index], text=f"มื้อที่ {i + 1}",
                font=("Arial", 70, "bold"), bg_color=back_color,  
                fg_color="white", text_color="black", width=600, height=120, corner_radius=10
            )
            meal_label.grid(row=0, column=i % 2, padx=100, pady=(20, 10), sticky="w")

            time_var = ctk.StringVar()
            time_var.trace_add("write", lambda *args, var=time_var: self.format_time(var))

            time_entry = ctk.CTkEntry(
                self.pages[page_index], width=600, height=120,
                font=("Arial", 70), fg_color="white", text_color="black",
                placeholder_text="เวลา (HH:MM)", validate="key", textvariable=time_var
            )
            time_entry.grid(row=1, column=i % 2, padx=100, pady=(0, 10), sticky="w")
            time_entry.bind("<Button-1>", lambda event, e=time_entry: self.open_numpad(e)) 
            self.time_entries[meal_name] = time_entry

            time_select = ctk.CTkComboBox(
                self.pages[page_index], values=self.time_options, width=600, height=120,
                font=("Arial", 70), fg_color="white", text_color=word_color, 
                dropdown_font=("Arial", 70)
            )
            time_select.grid(row=3, column=i % 2, padx=100, pady=(0, 0), sticky="w")
            time_select.set("เลือกช่วงเวลา")
            self.time_selects[meal_name] = time_select

            self.entry_frames[meal_name] = ctk.CTkFrame(self.pages[page_index], fg_color=back_color)
            self.entry_frames[meal_name].grid(row=4, column=i % 2, padx=0, pady=10, sticky="n")

            add_button = ctk.CTkButton(
                self.entry_frames[meal_name], text="+ เพิ่มยา", width=600, height=120,
                fg_color=force_color, text_color='white', font=("Arial", 70), 
                command=lambda m=meal_name: self.add_medication_entry(m)
            )
            add_button.pack(pady=10)

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
            width=500,
            height=120,
            fg_color="white",
            text_color="black",
            font=("Arial", 70),
            dropdown_font=("Arial", 70)
        )
        med_combo.grid(row=0, column=0, padx=(0, 10), sticky="w")

        med_combo.set("เลือกยา")

        if meal not in self.med_combos:
            self.med_combos[meal] = []
        self.med_combos[meal].append(med_combo)

        delete_button = ctk.CTkButton(
            row,
            text="ลบ",
            width=90,
            height=120,
            fg_color="red",
            text_color="black",
            font=("Arial", 70),
            hover_color="#990000",
            command=lambda: self.remove_medication_entry(meal, row,med_combo)
        )
        delete_button.grid(row=0, column=1, sticky="w")

        self.med_entries[meal].append((row, med_combo, delete_button))

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

        insert_meal = set_dispensing_time.set_meal(self.controller.user['device_id'],self.controller.user['id'],meal_data)
        if( insert_meal['status']):
            print(insert_meal['message'])
            self.controller.show_frame(HomePage)
        else:
            print(insert_meal['message'])
        

    def on_show(self):
        print("MedicationApp is now visible")
        self.update_meal_config()


class info(ctk.CTkFrame):
    def on_show(self):
        print("info is now visible")
        self.userid = self.controller.user['id']
        self.result = manageData.get(self.userid)
        print(self.result)
        if self.result:
            data = self.result

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

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.userid = None
        self.result = None

        bg_image = Image.open("imgNew/user.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        navbar = ctk.CTkFrame(self, height=100, fg_color="#A8DADC", corner_radius=0)
        navbar.pack(side="bottom", fill="x")

        def go_back():
            controller.show_frame(HomePage)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"), command=go_back)
        back_button.pack(side="right", padx=20, pady=10)

        def disable_editing(event):
            return "break"

        form_frame = ctk.CTkFrame(self, corner_radius=40, fg_color="#FFFFFF",bg_color="#1d567b", width=1350, height=800)
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        form_frame.grid_columnconfigure(0, weight=1, minsize=200)
        form_frame.grid_columnconfigure(1, weight=1, minsize=300)
        form_frame.grid_columnconfigure(2, weight=1, minsize=200)
        form_frame.grid_columnconfigure(3, weight=1, minsize=300)

        ctk.CTkLabel(form_frame, text="ข้อมูลตัวเครื่อง", text_color="#2D6A4F", font=("Arial", 36, "bold")).grid(row=0, column=0, columnspan=4, pady=(30, 40))

        # Row 1
        ctk.CTkLabel(form_frame, text="เจ้าของผู้สมัคร ใช้งานระบบ", text_color="black", font=("Arial", 28)).grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.entry_owner = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_owner.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.entry_owner.bind("<Key>", disable_editing)

        ctk.CTkLabel(form_frame, text="สถานะเครื่อง", text_color="black", font=("Arial", 28)).grid(row=1, column=2, sticky="w", padx=20, pady=10)
        entry_status = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        entry_status.grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        entry_status.insert(0, "online")
        entry_status.bind("<Key>", disable_editing)

        # Row 2
        ctk.CTkLabel(form_frame, text="อีเมล", text_color="black", font=("Arial", 28)).grid(row=2, column=0, sticky="w", padx=20, pady=10)
        self.entry_email = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_email.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.entry_email.bind("<Key>", disable_editing)

        ctk.CTkLabel(form_frame, text="รหัสผ่าน", text_color="black", font=("Arial", 28)).grid(row=2, column=2, sticky="w", padx=20, pady=10)
        self.entry_password = ctk.CTkEntry(form_frame, show="*", fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_password.grid(row=2, column=3, padx=10, pady=10, sticky="ew")
        self.entry_password.bind("<Key>", disable_editing)

        # Row 3
        ctk.CTkLabel(form_frame, text="ไอดีไลน์ผู้ใช้งาน", text_color="black", font=("Arial", 28)).grid(row=3, column=0, sticky="w", padx=20, pady=10)
        self.entry_line_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_line_id.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="หมายเลข เชื่อมต่อเครื่อง", text_color="black", font=("Arial", 28)).grid(row=3, column=2, sticky="w", padx=20, pady=10)
        self.entry_device_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_device_id.grid(row=3, column=3, padx=10, pady=10, sticky="ew")
        self.entry_device_id.bind("<Key>", disable_editing)

        # Section Heading
        ctk.CTkLabel(form_frame, text="การแจ้งเตือน", text_color="#2D6A4F", font=("Arial", 34, "bold")).grid(row=4, column=0, columnspan=4, pady=(30, 30))

        # Row 5
        ctk.CTkLabel(form_frame, text="หมายเลขโทเคน เทเลแกรม", text_color="black", font=("Arial", 28)).grid(row=5, column=0, sticky="w", padx=20, pady=10, columnspan=2)
        self.entry_telegram_token = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_telegram_token.grid(row=5, column=1, columnspan=3, padx=10, pady=10, sticky="ew")

        # Row 6
        ctk.CTkLabel(form_frame, text="ไอดี เทเลแกรม", text_color="black", font=("Arial", 28)).grid(row=6, column=0, sticky="w", padx=20, pady=10)
        self.entry_telegram_id = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_telegram_id.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="ลิงค์กลุ่ม เทเลแกรม", text_color="black", font=("Arial", 28)).grid(row=6, column=2, sticky="w", padx=20, pady=10)
        self.entry_telegram_group = ctk.CTkEntry(form_frame, fg_color="white", text_color="black", font=("Arial", 28))
        self.entry_telegram_group.grid(row=6, column=3, padx=10, pady=10, sticky="ew")

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
            print(success)
            if success['status']:
                print(success['message'])
                controller.show_frame(HomePage)
            else:
                print(success['message'])

        btn_save = ctk.CTkButton(form_frame, text="บันทึกข้อมูล", command=save_data,
                                 fg_color="green", text_color="white",
                                 font=("Arial", 34, "bold"), height=60, corner_radius=30)
        btn_save.grid(row=7, column=0, columnspan=4, pady=(40, 20))




class MedicationScheduleFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.interval_label = None
        self.interval_days = None

        # ตั้งค่าภาพพื้นหลัง
        bg_image = Image.open("imgNew/pageTime.png").resize((1920, 1080), Image.Resampling.LANCZOS) 
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ตั้งค่า frame ที่สามารถเลื่อน
        frame = ctk.CTkScrollableFrame(self, width=900, height=500, corner_radius=30, fg_color="#ffffff", bg_color="#1d567b") 
        frame.pack(padx=50, pady=50, expand=True)
        self.frame = frame

        # โหลดการตั้งค่ามื้ออาหาร
        self.load_meal_config()

        # Navbar
        navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
        navbar.pack(side="bottom", fill="x")

        # Title
        page_title = ctk.CTkLabel(navbar, text="กำหนดวันที่เริ่มจ่ายยา", font=("Arial", 50, "bold"), text_color="black") 
        page_title.pack(side="left", padx=20, pady=20)

        def go_back():
            controller.show_frame(Frame3)
        
        # ปุ่มกลับ
        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"), command=go_back)
        back_button.pack(side="right", padx=10, pady=20)
        
        def save_and_go_to_frame1():
            if(date_entry.get() == "" and end_entry.get() == ""):
                print('กรุณากำหนดวันที่เริ่มจ่ายยา')
                return

            setting_time = set_dispensing_time.set_time(self.controller.user['device_id'], date_entry.get(), end_entry.get())
            if setting_time['status']:
                print(setting_time['message'])
                controller.show_frame(MedicationApp)
            else:
                print(setting_time['message'])
        
        # ปุ่มบันทึก
        save_button = ctk.CTkButton(navbar, text="บันทึก", corner_radius=10, width=250, height=100, 
                                    fg_color="#2D6A4F", text_color="white", hover_color="#002299",
                                    font=("Arial", 44, "bold"), command=save_and_go_to_frame1)
        save_button.pack(side="right", padx=20, pady=20)

        # การตั้งค่าฟอร์มสำหรับวันที่เริ่มและวันที่สิ้นสุด
        frame_text = ctk.CTkLabel(frame, fg_color="white", text="เลือกวันที่เริ่มจ่ายยา", font=("Arial", 30, "bold"), text_color="black", corner_radius=10)
        frame_text.grid(row=1, column=0, padx=(50,0), pady=(20,10), sticky="w")

        frame_date = ctk.CTkFrame(frame, fg_color="#f0f8ff")
        frame_date.grid(row=2, column=0, padx=(50,0), pady=0, sticky="w")

        date_entry = ctk.CTkEntry(frame_date, width=200, height=60, font=("Arial", 30), state="normal")  
        date_entry.pack(side="left", padx=(20,0), pady=(0,10))

        frame_text2 = ctk.CTkLabel(frame, fg_color="white", text="สิ้นสุดการจ่ายยา", font=("Arial", 30, "bold"), text_color="black", corner_radius=10)  
        frame_text2.grid(row=1, column=1, padx=(220,0), pady=(20,10), sticky="w")

        frame_date2 = ctk.CTkFrame(frame, fg_color="#ffffff")
        frame_date2.grid(row=2, column=1, padx=40, pady=0, sticky="w")

        end_entry = ctk.CTkEntry(frame_date2, width=200, height=60, font=("Arial", 30), state="normal")
        end_entry.pack(side="left", padx=(200,0))
        
        date_picker_open = [False]
        def open_date_picker():
            print("open_date_picker() called")  
            if not date_picker_open[0]:
                print("Creating DatePicker...") 
                date_entry.configure(state="normal")
                DatePicker(self, date_entry, end_entry, date_picker_open).place(in_=frame_date, relx=0.18, rely=1, anchor="nw")
                date_picker_open[0] = True

        # ปุ่มเปิดปฏิทิน
        pick_date_btn = ctk.CTkButton(frame_date, text="เปิดปฏิทิน", width=50, height=60, font=("Arial", 30), command=open_date_picker)
        pick_date_btn.pack(side="left", padx=5)

    def load_meal_config(self):
        try:
            with open("meal_config.json", "r") as f:
                meal_config = json.load(f)
                num_meals = int(meal_config["meals"].split()[0])
                self.interval_days = 28 // num_meals

            if self.interval_label:
                self.interval_label.configure(text=f"ระยะเวลาในการจ่ายยา {self.interval_days} วัน")
            else:
                self.interval_label = ctk.CTkLabel(
                    self.frame, text=f"ระยะเวลาในการจ่ายยา {self.interval_days} วัน",
                    font=("Arial", 30 ,"bold"), fg_color="white", text_color="black",
                    corner_radius=10, bg_color="#8dc5fc"
                )
                self.interval_label.grid(row=0, column=0, columnspan=2, padx=(100,100), pady=(20, 0), sticky="we")

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

        select_btn = ctk.CTkButton(self, text="✔ เลือก", fg_color=force_color   , text_color="white", font=("Arial", 30, "bold"), command=self.set_date)
        select_btn.pack(side="left", padx=10, pady=10)

        close_btn = ctk.CTkButton(self, text="✖ ปิด", fg_color="#FF3B3B", text_color="white", font=("Arial", 30, "bold"), command=self.close_date_picker)  
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

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # พื้นหลัง
        bg_image = Image.open("imgNew/pagereport.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ขนาดปุ่มและโหลดภาพ
        btn_size = (200, 200)
        btn_images = {}
        for i, path in enumerate(["imgNew/iconreport2.png", "imgNew/pageuser.png", "imgNew/iconreport1.png"], start=1):
            try:
                img = Image.open(path).resize(btn_size, Image.Resampling.LANCZOS)
                btn_images[i] = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Error: {path} not found.")

        # หน้า report (Report1, Report3, Report2 ตามลำดับใหม่)
        pages = [Report1, Report3, Report2]
        labels = ["รายงานข้อมูลการจ่ายยา", "รายงานข้อมูลผู้ใช้งาน", "รายงานข้อมูลความดันและชีพจร"]

        # คำนวณให้อยู่ตรงกลางแนวนอน และห่างกัน 20px
        spacing = 250
        total_width = (3 * btn_size[0]) + (2 * spacing)
        start_x = (1920 - total_width) // 2

        for i in range(3):
            x_pos = start_x + i * (btn_size[0] + spacing)

            if i + 1 in btn_images:
                btn = ctk.CTkButton(
                    self,
                    image=btn_images[i + 1],
                    text="",
                    fg_color="#1d567b",
                    hover_color="#76C8C8",
                    bg_color="#1d567b",
                    border_width=3,
                    border_color="#1d567b",
                    corner_radius=20,
                    width=200,
                    height=200,
                    command=lambda i=i: controller.show_frame(pages[i])
                )
                btn.place(x=x_pos, y=250)

            label = ctk.CTkLabel(
                self,
                text=labels[i],
                fg_color="#A8DADC",
                bg_color="#1d567b",
                text_color="#000000",
                corner_radius=20,
                font=("TH Sarabun New", 30, "bold")
            )
            label.place(x=x_pos - 50, y=470)

        # Navbar ด้านล่าง
        navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="หน้าพิมพ์รายงาน", font=("Arial", 50, "bold"), text_color="black") 
        page_title.pack(side="left", padx=20, pady=20)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=20)





class Report1(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.page = 1
        self.rows_per_page = 10
        self.data = []

        # พื้นหลังธีมเครื่องจ่ายยา
        bg_image = Image.open("imgNew/pagereport1.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar ด้านล่าง
        navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="ประวัติการจ่ายยา", font=("Arial", 50, "bold"), text_color="black") 
        page_title.pack(side="left", padx=20, pady=20)
        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
            command=lambda: controller.show_frame(HomePage)
        )
        back_button.pack(side="right", padx=10, pady=20)

        # กรอบตาราง
        self.table_frame = ctk.CTkFrame(self, fg_color="white",bg_color="#1d567b", corner_radius=15)
        self.table_frame.place(relx=0.5, rely=0.15, anchor="n")

        self.page_label = ctk.CTkLabel(self, text="",bg_color="#ffffff", font=("TH Sarabun New", 20, "bold"), text_color="#000000")
        self.page_label.place(relx=0.5, rely=0.62, anchor="center")

        self.nav_frame = ctk.CTkFrame(self,bg_color="#1d567b",fg_color="transparent")
        self.nav_frame.place(relx=0.5, rely=0.67, anchor="center")

        self.btn_prev = ctk.CTkButton(
            self.nav_frame, text="ก่อนหน้า", width=120, height=45, fg_color="#aeb3f5",
            text_color="black", hover_color="#a1d6e2", font=("Arial", 20, "bold"), command=self.prev_page
        )
        self.btn_prev.grid(row=0, column=0, padx=10)

        self.btn_next = ctk.CTkButton(
            self.nav_frame, text="ถัดไป", width=120, height=45, fg_color="#aeb3f5",
            text_color="black", hover_color="#a1d6e2", font=("Arial", 20, "bold"), command=self.next_page
        )
        self.btn_next.grid(row=0, column=1, padx=10)

        self.summary_label = ctk.CTkLabel(self,bg_color="#ffffff", text="", font=("TH Sarabun New", 20, "bold"), text_color="#000000")
        self.summary_label.place(relx=0.5, rely=0.73, anchor="center")

        # ดึงข้อมูล
        self.userid = self.controller.user.get('id') if self.controller.user else None
        self.result = manageData.get(self.userid) if self.userid else {}
    def on_show(self):
        print("Report1 is now visible")

        if not self.controller.user or 'id' not in self.controller.user:
            print("❌ ไม่มีข้อมูลผู้ใช้ หรือยังไม่ได้ล็อกอิน")
            return

        self.userid = self.controller.user['id']
        self.result = manageData.get(self.userid)

        result = medicine_report.get_eatmedic(self.userid)
        if result['status']:
            self.data = result['data']
            self.page = 1
            self.display_table()
        else:
            print(result['message'])

    def display_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.data:
            no_data_label = ctk.CTkLabel(self.table_frame, text="ไม่มีประวัติการจ่ายยา", text_color="#fc4e4e", font=("TH Sarabun New", 22, "bold"))
            no_data_label.grid(row=0, column=0, columnspan=3, padx=15, pady=20)
            return

        headers = ["วันที่ - เวลา", "ชื่อยา", "ผลการจ่ายยา"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, text=header,
                font=("TH Sarabun New", 20, "bold"), text_color="#000000"
            )
            label.grid(row=0, column=i, padx=20, pady=12)

        start = (self.page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        page_data = self.data[start:end]

        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]

        for idx, row in enumerate(page_data, start=1):
            try:
                date_obj = row['time_get']
                month_th = thai_months[date_obj.month - 1]
                dt = f"{date_obj.day:02d} {month_th} {date_obj.year + 543} เวลา {date_obj.strftime('%H:%M')}"
            except Exception as e:
                dt = "ไม่สามารถแสดงวันที่"

            name = row['medicine_1'] if row['medicine_1'] else "ไม่มีข้อมูล"
            status = "✅ สำเร็จ" if row['medicine_get'] == 'success' else "❌ ไม่สำเร็จ"
            status_color = "#27ae60" if row['medicine_get'] == 'success' else "#c0392b"

            ctk.CTkLabel(self.table_frame,text_color="#000000", text=dt, font=("TH Sarabun New", 18)).grid(row=idx, column=0, padx=10, pady=6)
            ctk.CTkLabel(self.table_frame,text_color="#000000", text=name, font=("TH Sarabun New", 18)).grid(row=idx, column=1, padx=10, pady=6)
            ctk.CTkLabel(self.table_frame, text=status, font=("TH Sarabun New", 18, "bold"), text_color=status_color).grid(row=idx, column=2, padx=10, pady=6)

        total_pages = max(1, (len(self.data) + self.rows_per_page - 1) // self.rows_per_page)
        self.page_label.configure(text=f"หน้าที่ {self.page} จาก {total_pages}")

        success = sum(1 for d in self.data if d['medicine_get'] == 'success')
        failed = len(self.data) - success
        self.summary_label.configure(text=f"📋 สรุปผลการจ่ายยา | ✅ สำเร็จ: {success} | ❌ ไม่สำเร็จ: {failed}")

    def next_page(self):
        if self.page < (len(self.data) + self.rows_per_page - 1) // self.rows_per_page:
            self.page += 1
            self.display_table()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.display_table()

class Report2(ctk.CTkFrame):    
    def on_show(self):
        print("Report2 is now visible")
        result = heart_report().generate_advice(self.controller.user['id'])
        if result['status']:
            self.display_data(result['data'], result['advices'])  # Display the fetched data
        else:
            print("เกิดข้อผิดพลาด:", result['message'])

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Background
        bg_image = Image.open("imgNew/pagereport2.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Navbar                          
        navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
        navbar.pack(side="bottom", fill="x")
        page_title = ctk.CTkLabel(navbar, text="ประวัติการวัดความดัน", font=("Arial", 50, "bold"), text_color="black") 
        page_title.pack(side="left", padx=20, pady=20)
        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(HomePage))
        back_button.pack(side="right", padx=10, pady=5)

        # Scrollable Frame for the table
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=1200, height=700,bg_color="#ffffff", fg_color="#ffffff")
        self.scroll_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.headers = ["ลำดับ", "ความดันสูง", "ความดันต่ำ", "ชีพจร", "คำแนะนำประจำวัน", "วันที่บันทึก"]
        self.column_widths = [100, 200, 200, 150, 200, 300]

    def show_advice_popup(self, advice_text):
        popup = ctk.CTkToplevel(self)
        popup.title("คำแนะนำจาก AI")
        popup.geometry("600x420")
        popup.grab_set()

        label = ctk.CTkLabel(popup, text="คำแนะนำจาก AI", font=("Arial", 24, "bold"))
        label.pack(pady=10)

        textbox = ctk.CTkTextbox(popup, width=550, height=300, wrap="word", font=("Arial", 18))
        textbox.insert("1.0", advice_text)
        textbox.configure(state="disabled")
        textbox.pack(pady=10)

        close_btn = ctk.CTkButton(popup, text="ปิด", command=popup.destroy)
        close_btn.pack(pady=10)

    def display_data(self, data, advices):
        # Create table headers
        for col, header in enumerate(self.headers):
            label = ctk.CTkLabel(self.scroll_frame, text=header, font=("Arial", 20, "bold"), text_color="black", width=self.column_widths[col])
            label.grid(row=0, column=col, padx=5, pady=5)

        # Use heart_id to fetch corresponding advice for each record
        for i, row in enumerate(data):
            systolic = f"{row['systolic_pressure']} mmHg"  # High blood pressure
            diastolic = f"{row['diastolic_pressure']} mmHg"  # Low blood pressure
            pulse = f"{row['pulse_rate']} bpm"  # Pulse rate
            try:
                date = datetime.strptime(str(row['date']), "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y เวลา %H:%M น.")
            except:
                date = str(row['date'])

            values = [str(i+1), systolic, diastolic, pulse, None, date]

            # Get advice text for the corresponding heart_id
            heart_id = row['heart_id']

            # Find the corresponding advice for the heart_id from advices
            advice_text = next((a['advice'] for a in advices if a['heart_id'] == heart_id), "ไม่พบคำแนะนำ")

            # Create a button to show advice
            for col, val in enumerate(values):
                if col == 4:  # When we reach the "คำแนะนำประจำวัน" column
                    advice_btn = ctk.CTkButton(self.scroll_frame, text="🔍", width=50, height=35, 
                                            command=lambda a=advice_text: self.show_advice_popup(a))
                    advice_btn.grid(row=i+1, column=col, padx=5, pady=5)
                else:
                    label = ctk.CTkLabel(self.scroll_frame, text=val, font=("Arial", 18), text_color="black", width=self.column_widths[col])
                    label.grid(row=i+1, column=col, padx=5, pady=5)
                    
                    
                    
                    
                    
class Report3(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # พื้นหลัง
        bg_image = Image.open("imgNew/pagereport1.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # กรอบข้อมูล
        info_frame = ctk.CTkFrame(self, fg_color="#e0e0e0", corner_radius=20)
        info_frame.place(relx=0.5, rely=0.3, anchor="center")

        # หัวข้อ "ข้อมูลผู้ป่วย" อยู่ในกรอบและตรงกลางบนสุด
        header = ctk.CTkLabel(info_frame, text="ข้อมูลผู้ป่วย", font=("TH Sarabun New", 36, "bold"), text_color="black")
        header.grid(row=0, column=0, columnspan=4, pady=(20, 10), sticky="n")

        # ข้อมูลฝั่งซ้าย
        left_data = [
            ("ชื่อจริง:", "-"),
            ("วัน / เดือน / ปี:", "-"),
            ("ที่อยู่:", "-"),
            ("โรคประจำตัว:", "-")
        ]

        # ข้อมูลฝั่งขวา
        right_data = [
            ("นามสกุล:", "-"),
            ("เพศ:", "-")
        ]

        # แสดงข้อมูลฝั่งซ้าย (เริ่ม row=1)
        for i, (label, value) in enumerate(left_data):
            ctk.CTkLabel(info_frame, text=label, font=("TH Sarabun New", 28, "bold"),
                         text_color="black", anchor="w", width=200).grid(row=i+1, column=0, padx=20, pady=10, sticky="w")
            ctk.CTkLabel(info_frame, text=value, font=("TH Sarabun New", 28),
                         text_color="black", anchor="w", width=300).grid(row=i+1, column=1, padx=10, pady=10, sticky="w")

        # แสดงข้อมูลฝั่งขวา (เริ่ม row=1 เช่นกัน เพื่อให้เทียบกับฝั่งซ้าย)
        for i, (label, value) in enumerate(right_data):
            ctk.CTkLabel(info_frame, text=label, font=("TH Sarabun New", 28, "bold"),
                         text_color="black", anchor="w", width=200).grid(row=i+1, column=2, padx=40, pady=10, sticky="w")
            ctk.CTkLabel(info_frame, text=value, font=("TH Sarabun New", 28),
                         text_color="black", anchor="w", width=300).grid(row=i+1, column=3, padx=10, pady=10, sticky="w")

        # Navbar ด้านล่าง
        navbar = ctk.CTkFrame(self, height=200, fg_color="#A8DADC")
        navbar.pack(side="bottom", fill="x")

        page_title = ctk.CTkLabel(
            navbar,
            text="ข้อมูลผู้ใช้งาน",
            font=("Arial", 50, "bold"),
            text_color="black"
        )
        page_title.pack(side="left", padx=20, pady=20)

        back_button = ctk.CTkButton(
            navbar,
            text="←",
            width=150,
            height=100,
            corner_radius=35,
            fg_color=force_color,
            hover_color="#FF0000",
            text_color="white",
            font=("Arial", 44, "bold"),
            command=lambda: controller.show_frame(HomePage)
        )
        back_button.pack(side="right", padx=10, pady=20)




class Wificonnect(ctk.CTkFrame):
    def on_show(self):
        print("Wificonnect is now visible")
        self.update_wifi_list()

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        back_color = "#C1E0E2"
        force_color = "#007ACC"
        bottom_hover = "#FF5733"

        bg_image = Image.open("imgNew/wifi.png").resize((1920, 1080), Image.Resampling.LANCZOS)
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = ctk.CTkScrollableFrame(self, width=950, height=650, corner_radius=30, fg_color=back_color,bg_color="#1d567b")
        frame.place(relx=0.5, rely=0.52, anchor="center")

        navbar = ctk.CTkFrame(self, height=200, fg_color=back_color, corner_radius=0)
        navbar.pack(side="bottom", fill="x")

        page_title = ctk.CTkLabel(navbar, text="เชื่อมต่อ Wi-Fi", font=("Arial", 50, "bold"), text_color="black")
        page_title.pack(side="left", padx=20)

        back_button = ctk.CTkButton(navbar, text="←", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color="#FF0000", text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(login))
        back_button.pack(side="right", padx=10, pady=5)

        skip_button = ctk.CTkButton(navbar, text="ข้าม", width=150, height=100, corner_radius=35,
                                    fg_color=force_color, hover_color=bottom_hover, text_color="white",
                                    font=("Arial", 44, "bold"),
                                    command=lambda: controller.show_frame(HomePage))
        skip_button.pack(side="right", padx=10, pady=5)

        self.wifi_frame = ctk.CTkFrame(frame, fg_color="#C1E0E2")
        self.wifi_frame.pack(padx=50, pady=50, fill="both", expand=True)

        self.password_frame = ctk.CTkFrame(frame, fg_color="#C1E0E2")
        self.password_frame.pack_forget()

        self.refresh_button = ctk.CTkButton(frame, text="Refresh Wi-Fi List", command=self.update_wifi_list,
                                            fg_color=force_color, bg_color="#C1E0E2", text_color="white",
                                            hover=True, hover_color="green", font=("Arial", 34, "bold"))
        self.refresh_button.pack(pady=20, anchor="center")

    def get_wifi_list(self):
        wifi = PyWiFi()
        iface = wifi.interfaces()[0]
        iface.scan()
        scan_results = iface.scan_results()
        return [network.ssid for network in scan_results]

    def show_password_form(self, ssid):
        self.wifi_frame.pack_forget() 
        for widget in self.password_frame.winfo_children():
            widget.destroy()

        password_label = ctk.CTkLabel(self.password_frame, text=f"กรุณากรอกรหัสผ่านเพื่อใช้งาน {ssid}:",
                                      width=800, text_color="black", font=("Arial", 24))
        password_label.pack(pady=10)

        password_entry = ctk.CTkEntry(self.password_frame, show="*", width=800, height=60, font=("Arial", 24))
        password_entry.pack(pady=10)

        button_frame = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        connect_button = ctk.CTkButton(button_frame, text="เชื่อมต่อ", width=300, height=60, font=("Arial", 24),
                                       fg_color=force_color, hover_color="green",
                                       command=lambda: self.controller.show_frame(HomePage))
        connect_button.pack(side="left", padx=10)

        back_button = ctk.CTkButton(button_frame, text="ย้อนกลับ", width=300, height=60, font=("Arial", 24),
                                    fg_color="#FF5733", hover_color="#FF0000",
                                    command=self.show_wifi_list)
        back_button.pack(side="left", padx=10)

        self.password_frame.pack(padx=50, pady=50, fill="both", expand=True)

    def show_wifi_list(self):
        self.password_frame.pack_forget() 
        self.wifi_frame.pack(padx=50, pady=50, fill="both", expand=True) 

    def update_wifi_list(self):
        wifi_list = self.get_wifi_list()

        for widget in self.wifi_frame.winfo_children():
            widget.destroy()

        if not wifi_list:
            no_wifi_label = ctk.CTkLabel(self.wifi_frame, text="ไม่พบเครือข่าย Wi-Fi กรุณาลองใหม่อีกครั้ง",
                                         font=("Arial", 24), text_color="black")
            no_wifi_label.pack(pady=10, anchor="center")
        else:
            for wifi in wifi_list:
                wifi_button = ctk.CTkButton(self.wifi_frame, text=wifi, width=800, height=60,
                                            font=("Arial", 24), fg_color=force_color, hover_color="gray",
                                            command=lambda w=wifi: self.show_password_form(w))
                wifi_button.pack(pady=10, fill="x", anchor="center")



class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user = None
        self.title("เครื่องโฮมแคร์อัจฉริยะควบคุมผ่านระบบ SeniorCare Pro")
        self.geometry("1920x1080") 
        self.advice = ''
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (HomePage, Frame2, Frame3, Frame4, add_Frame, info, MedicationApp, AIgen, MedicationScheduleFrame, ReportFrame, Report1, Report2,Report3, login, Wificonnect):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)
        
        if os.path.exists("user_data.json"):
            try:
                with open("user_data.json","r",encoding='utf-8') as f:
                    user_data = json.load(f)
                print(user_data)
                if user_data:
                    self.user = user_data
                    self.show_frame(HomePage)
                else:
                     self.show_frame(login)   
            except Exception as e :
                  print(f"เกิดข้อผิดพลาดขณะโหลด user_data.json: {e}")
                  self.show_frame(login)
        else:
            self.show_frame(login)
    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.lift()
        frame.on_show() 



if __name__ == "__main__":
    app = MainApp()
    app.mainloop()