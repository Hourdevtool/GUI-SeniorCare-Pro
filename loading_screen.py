import customtkinter as ctk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import threading
import math

# สีที่ใช้ในแอป
back_color = '#F5FAFF'
force_color = '#2F6AA3'
text_main = '#1E293B'
hover_color = "#255A8A"
input_color = "#FFFFFF"
secondary_color = "#E8F4FD"

class LoadingScreen(ctk.CTkFrame):
    """หน้าดาวโหลดสำหรับแสดงระหว่างรอข้อมูล"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.is_loading = False
        self.animation_index = 0
        self.rotation_angle = 0
        
        # พื้นหลัง
        self.configure(fg_color=back_color)
        
        # Container หลักสำหรับเนื้อหา
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Card container สำหรับเนื้อหาหลัก (มีเงาและมุมโค้ง)
        card_frame = ctk.CTkFrame(
            main_container,
            fg_color=input_color,
            corner_radius=25,
            border_width=0
        )
        card_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Container สำหรับเนื้อหาใน card
        content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Canvas สำหรับ spinner แบบหมุน
        self.spinner_canvas = Canvas(
            content_frame,
            width=120,
            height=120,
            bg=input_color,
            highlightthickness=0,
            relief="flat",
            borderwidth=0
        )
        self.spinner_canvas.pack(pady=(20, 30))
        
        # วาด spinner เริ่มต้น
        self.draw_spinner()
        
        # ข้อความดาวโหลดหลัก
        self.loading_text = ctk.CTkLabel(
            content_frame,
            text="กำลังโหลดข้อมูล...",
            font=("Arial", 28, "bold"),
            text_color=text_main
        )
        self.loading_text.pack(pady=(0, 10))
        
        # ข้อความรายละเอียด (ถ้ามี)
        self.detail_text = ctk.CTkLabel(
            content_frame,
            text="",
            font=("Arial", 18),
            text_color="#666666"
        )
        self.detail_text.pack(pady=5)
        
        # Progress dots animation
        self.progress_dots = ctk.CTkLabel(
            content_frame,
            text="",
            font=("Arial", 20),
            text_color=force_color
        )
        self.progress_dots.pack(pady=10)
        
        # ปุ่มย้อนกลับ
        button_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_container.pack(pady=(30, 0))
        
        self.back_button = ctk.CTkButton(
            button_container,
            text="← ย้อนกลับ",
            font=("Arial", 18, "bold"),
            fg_color=secondary_color,
            hover_color="#D0E8F9",
            text_color=force_color,
            corner_radius=15,
            height=45,
            width=180,
            command=self.go_back,
            border_width=2,
            border_color=force_color
        )
        self.back_button.pack()
    
    def draw_spinner(self):
        """วาด spinner แบบหมุน"""
        self.spinner_canvas.delete("all")
        center_x, center_y = 60, 60
        radius = 45
        
        # วาดวงกลมหลัก
        self.spinner_canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline=secondary_color,
            width=8,
            fill=input_color
        )
        
        # วาดส่วนโค้งที่หมุน
        start_angle = self.rotation_angle
        extent = 60  # ความยาวของส่วนโค้ง
        
        # แปลงมุมเป็นพิกัด
        for i in range(3):
            angle = (start_angle + i * 120) % 360
            start_rad = math.radians(angle)
            end_rad = math.radians(angle + extent)
            
            # คำนวณจุดเริ่มต้นและสิ้นสุด
            x1 = center_x + radius * math.cos(start_rad)
            y1 = center_y + radius * math.sin(start_rad)
            x2 = center_x + radius * math.cos(end_rad)
            y2 = center_y + radius * math.sin(end_rad)
            
            # วาดส่วนโค้ง
            self.spinner_canvas.create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=angle,
                extent=extent,
                outline=force_color,
                width=8,
                style="arc"
            )
    
    def animate_spinner(self):
        """ทำให้ spinner หมุน"""
        try:
            if self.is_loading and self.winfo_exists():
                self.rotation_angle = (self.rotation_angle + 5) % 360
                self.draw_spinner()
                self.after(20, self.animate_spinner)  # หมุนเร็วขึ้น
        except:
            # หน้าต่างถูกทำลายแล้ว ไม่ต้องทำอะไร
            pass
    
    def animate_dots(self):
        """ทำให้จุด loading กระพริบ"""
        try:
            if self.is_loading and self.winfo_exists():
                dots = ["", ".", "..", "..."]
                self.animation_index = (self.animation_index + 1) % len(dots)
                self.progress_dots.configure(text=dots[self.animation_index])
                self.after(500, self.animate_dots)
        except:
            pass
    
    def set_message(self, message="กำลังโหลดข้อมูล...", detail=""):
        """ตั้งค่าข้อความแสดงบนหน้าดาวโหลด"""
        self.loading_text.configure(text=message)
        if detail:
            self.detail_text.configure(text=detail)
        else:
            self.detail_text.configure(text="")
    
    def show_loading(self, message="กำลังโหลดข้อมูล...", detail=""):
        """แสดงหน้าดาวโหลด"""
        self.is_loading = True
        self.set_message(message, detail)
        self.rotation_angle = 0
        self.animation_index = 0
        self.draw_spinner()
        self.lift()
        self.update()
        self.animate_spinner()
        self.animate_dots()
    
    def hide_loading(self):
        """ซ่อนหน้าดาวโหลด"""
        self.is_loading = False
    
    def go_back(self):
        """ย้อนกลับไปหน้าก่อนหน้า"""
        if self.controller:
            self.controller.hide_loading()
    
    def on_show(self):
        """เมื่อแสดงหน้า"""
        pass
