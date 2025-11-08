import customtkinter as ctk
from PIL import Image, ImageTk
import threading

# สีที่ใช้ในแอป
back_color = '#F5FAFF'
force_color = '#2F6AA3'
text_main = '#1E293B'

class LoadingScreen(ctk.CTkFrame):
    """หน้าดาวโหลดสำหรับแสดงระหว่างรอข้อมูล"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.is_loading = False
        self.animation_index = 0
        
        # พื้นหลัง
        self.configure(fg_color=back_color)
        
        # Container สำหรับเนื้อหา
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(expand=True, fill="both")
        
        # วงกลมสำหรับการหมุน (spinner)
        self.spinner_label = ctk.CTkLabel(
            content_frame,
            text="⏳",
            font=("Arial", 60),
            text_color=force_color
        )
        self.spinner_label.pack(pady=50)
        
        # ข้อความดาวโหลด
        self.loading_text = ctk.CTkLabel(
            content_frame,
            text="กำลังโหลดข้อมูล...",
            font=("Arial", 24, "bold"),
            text_color=text_main
        )
        self.loading_text.pack(pady=10)
        
        # ข้อความรายละเอียด (ถ้ามี)
        self.detail_text = ctk.CTkLabel(
            content_frame,
            text="",
            font=("Arial", 18),
            text_color="#666666"
        )
        self.detail_text.pack(pady=5)
    
    def set_message(self, message="กำลังโหลดข้อมูล...", detail=""):
        """ตั้งค่าข้อความแสดงบนหน้าดาวโหลด"""
        self.loading_text.configure(text=message)
        if detail:
            self.detail_text.configure(text=detail)
        else:
            self.detail_text.configure(text="")
    
    def animate_spinner(self):
        """ทำให้ spinner หมุน"""
        try:
            if self.is_loading and self.winfo_exists():
                spinner_chars = ["⏳", "⌛", "⏳", "⌛"]
                self.animation_index = (self.animation_index + 1) % len(spinner_chars)
                self.spinner_label.configure(text=spinner_chars[self.animation_index])
                self.after(300, self.animate_spinner)
        except:
            # หน้าต่างถูกทำลายแล้ว ไม่ต้องทำอะไร
            pass
    
    def show_loading(self, message="กำลังโหลดข้อมูล...", detail=""):
        """แสดงหน้าดาวโหลด"""
        self.is_loading = True
        self.set_message(message, detail)
        self.lift()
        self.update()
        self.animate_spinner()
    
    def hide_loading(self):
        """ซ่อนหน้าดาวโหลด"""
        self.is_loading = False
    
    def on_show(self):
        """เมื่อแสดงหน้า"""
        pass

