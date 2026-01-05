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
import multiprocessing
#
from models.fall_detection_service import falldetection_worker, AI_ENABLED

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

# View Imports
from views.login_view import login
from views.home_view import HomePage
from views.medication_stock_view import Frame2, add_Frame, MedicationApp
from views.schedule_setup_view import Frame3, MedicationScheduleFrame, TimeNumpad, DatePicker
from views.health_view import Frame4, HealthNumpad, AIgen
from views.report_view import ReportFrame, Report1, Report2
from views.user_info_view import info, Wificonnect
from models.voice_service import VoicePromptPlayer
import utils.helpers as helpers
from utils.helpers import *
class AppController(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user = None
        self.is_test_account = False
        
        # AI Service Variables
        self.ai_running_flag = None
        self.ai_process = None
        self.is_ai_running_var = ctk.BooleanVar(value=False)

        self.title("เครื่องโฮมแคร์อัจฉริยะควบคุมผ่านระบบ SeniorCare Pro")
        #  loop Data api
        self.polling_thread_active = False
        self.polling_thread_handle = None
        self.data_lock = threading.Lock()
        self.last_known_schedule_data = None 
        self.data_lock = threading.Lock()

        self.has_sent_online_notification = False

        # ปรับขนาดหน้าจอเป็น 1024x600
        self.geometry("1024x800")
        self.notifier = Notifier(self)
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
        self.voice_player = VoicePromptPlayer()
        self.voice_player.ensure_startup_greeting()
        self.voice_player.preload_all_prompts()
        self._startup_greeting_played = False
        self.battery_percent_var = ctk.DoubleVar(value=0.0)
        self.device_status_var = ctk.StringVar(value="0")

        self.device_status_var.trace_add('write', self.status_callback)
        self.status_timestamps = {}

        # สร้าง container frame
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.network_status_var = ctk.StringVar(value="offline")
        # สร้างและจัดการ frames ต่างๆ
        self.frames = {}

        self.cached_medications = [] 
        self.medicine_data_lock = threading.Lock() 
        self.MEDICINE_CACHE_FILE = "offline_medicineData.json"
        self._is_med_cache_loading = False
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
        
        # Ensure AI service is started if user is loaded
        if self.user:
            self.start_ai_service()
            
        self.start_serial_thread()

        if hasattr(self, 'user') and isinstance(self.user, dict) and 'id' in self.user:
            id_to_monitor = self.user.get('id')
            
            if id_to_monitor:
                self.network_monitor = NetworkMonitor(
                    id=id_to_monitor, 
                    ui_callback=self._async_update_wifi_status, # ใช้ฟังก์ชันที่เราเพิ่งสร้าง
                    monitor_interval=10
                )
                self.network_monitor.start()
                print(f"Started Network Monitor for Device ID: {id_to_monitor}")
            else:
                 print("Cannot start Network Monitor: 'id' not found in self.user.")
        else:
            print("self.user not defined or loaded yet. Network Monitor not started.")


    
    def start_ai_service(self):
        """Start the Fall Detection AI Service in a separate process."""
        if not AI_ENABLED:
            print("[AppController] AI Service is DISABLED via hardcode.")
            return

        if self.ai_process and self.ai_process.is_alive():
            print("[AppController] AI Service is already running.")
            return

        if not self.user:
            print("[AppController] Cannot start AI: No user loaded.")
            return

        print("[AppController] Starting AI Service...")
        
        # Prepare arguments
        user_line_token = self.user.get('token_line', '')
        user_line_group_id = self.user.get('group_id', '')
        
        # Create synchronization flag
        self.ai_running_flag = multiprocessing.Value('b', True)
        
        # Spawn Process
        self.ai_process = multiprocessing.Process(
            target=falldetection_worker,
            args=(self.ai_running_flag, user_line_token, user_line_group_id),
            daemon=True
        )
        self.ai_process.start()
        self.is_ai_running_var.set(True)
        print(f"[AppController] AI Service started (PID: {self.ai_process.pid})")

    def stop_ai_service(self):
        """Stop the Fall Detection AI Service."""
        if self.ai_running_flag:
            self.ai_running_flag.value = False
        
        if self.ai_process and self.ai_process.is_alive():
            print("[AppController] Stopping AI Service...")
            self.ai_process.join(timeout=2)
            if self.ai_process.is_alive():
                print("[AppController] AI Service did not stop gracefully, terminating...")
                self.ai_process.terminate()
        
        self.ai_process = None
        self.ai_running_flag = None
        self.is_ai_running_var.set(False)
        print("[AppController] AI Service stopped.")

    def login_mode(self):
        if self.user and self.user.get('email') == TEST_MODE_EMAIL:
            self.is_test_account = True
            print("Test Mode Activate")
        else:
            self.is_test_account = False
            print("User Mode Activate")
    def fetch_medications(self, show_loading_screen=True, on_complete_callback=None):
       
        
        # ⭐️⭐️ นี่คือส่วนที่ "กัน error" ที่คุณต้องการ ⭐️⭐️
        if not self.user:
            print("Meds: ไม่สามารถโหลดได้, ยังไม่ได้ล็อกอิน")
            # (ถ้า Frame2 เรียกตอนยังไม่ล็อกอิน) ให้ซ่อน loading และแสดงผลว่า "ไม่มีข้อมูล"
            if show_loading_screen:
                self.hide_loading()
            if on_complete_callback:
                self.after(0, on_complete_callback) 
            return # ⭐️ หยุดการทำงานทันที ⭐️
        # ----------------------------------------------------

        # ⭐️ ป้องกันการโหลดซ้ำซ้อน ถ้ากำลังโหลดอยู่
        if self._is_med_cache_loading:
            print("Meds: กำลังโหลดข้อมูลยาอยู่แล้ว, ข้ามคำสั่งนี้")
            return
            
        self._is_med_cache_loading = True
        
        if show_loading_screen:
            self.show_loading("กำลังโหลดข้อมูลยา...", "กรุณารอสักครู่")
        
        # เริ่ม Thread ใหม่เพื่อโหลดข้อมูล
        threading.Thread(
            target=self._medications_worker_thread, 
            args=(show_loading_screen, on_complete_callback,), 
            daemon=True
        ).start()

  
    def _medications_worker_thread(self, show_loading_screen, on_complete_callback):
        """Worker ที่รันใน Background Thread สำหรับ fetch_medications"""
        
        # ⭐️ [แก้ไข] เราจะไม่เช็ก network_status_var ที่นี่ ⭐️
        new_data = []
        error_message = None
        data_source = ""

        try:
            # ⭐️ [FIX] 1. "พยายาม" ดึงข้อมูลจากเซิร์ฟเวอร์ก่อนเสมอ ⭐️
            print("Meds: กำลังพยายามดึงข้อมูลจากเซิร์ฟเวอร์...")
            medicine_data = manageMedic.getMedicine(
                self.user['id'], self.user['device_id']
            )
            
            # --- 2. ถ้าดึงข้อมูลสำเร็จ (ONLINE) ---
            if medicine_data['status']:
                new_data = medicine_data['Data']
                data_source = "Server (Online)"
                
                # 2a. บันทึกข้อมูลใหม่ลงไฟล์แคช (JSON)
                try:
                    with open(self.MEDICINE_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(new_data, f, indent=4)
                    print(f"Meds: บันทึกข้อมูลใหม่ลง {self.MEDICINE_CACHE_FILE} สำเร็จ")
                except Exception as e:
                    print(f"Meds: ไม่สามารถเขียนไฟล์แคช: {e}")
                
                # 2b. แจ้งเตือน (ถ้าจำเป็น)
                if show_loading_screen:
                    self.after(0, lambda: self.notifier.show_notification("โหลดข้อมูลยาสำเร็จ", success=True))
            
            else:
                # 2c. เซิร์ฟเวอร์ตอบกลับมาแต่ข้อมูลผิดพลาด (เช่น 'status': false)
                error_message = medicine_data.get('message', 'เซิร์ฟเวอร์ปฏิเสธการร้องขอ')

        except requests.exceptions.RequestException as e:
            # --- 3. ถ้าดึงข้อมูล "ล้มเหลว" (OFFLINE หรือ Server ล่ม) ---
            print(f"Meds: เกิดข้อผิดพลาด Network (Offline): {e}")
            error_message = f"ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์: {e}" # ⭐️ บังคับให้ไปโหลดแคช
            
        except Exception as e:
            # --- 4. ERROR อื่นๆ (เช่น โค้ดผิด) ---
            error_message = f"เกิดข้อผิดพลาด: {e}"
            print(f"Error in _medications_worker_thread: {e}")

        
        # --- 5. สรุปผลและแสดงผล ---
        
        # ⭐️ [FIX] อัปเดตแคช global *ก่อน* ที่จะไปโหลดจากแคช
        with self.medicine_data_lock:
             self.cached_medications = new_data
        
        if error_message:
            # --- 5a. ถ้าเกิด Error (Onlineล่ม หรือ Offline) -> ให้โหลดจากแคช ---
            print(f"Meds: ดึงข้อมูลล้มเหลว ({error_message}). กำลังโหลดจากแคช...")
            if os.path.exists(self.MEDICINE_CACHE_FILE):
                try:
                    with open(self.MEDICINE_CACHE_FILE, "r", encoding="utf-8") as f:
                        new_data_from_cache = json.load(f)
                    
                    # ⭐️ อัปเดต cache global อีกครั้งด้วยข้อมูลจากไฟล์
                    with self.medicine_data_lock:
                        self.cached_medications = new_data_from_cache
                        
                    if show_loading_screen:
                        self.after(0, lambda: self.notifier.show_notification("โหลดข้อมูลจากแคช (Offline)", success=True))
                except Exception as e:
                    print(f"Meds: ไม่สามารถอ่านไฟล์แคช: {e}")
                    self.after(0, lambda: self.notifier.show_notification(f"Offline และอ่านไฟล์แคชไม่ได้: {e}", success=False))
            else:
                # --- 5b. Offline และไม่มีไฟล์แคช ---
                print(f"Meds: ไม่พบไฟล์แคช {self.MEDICINE_CACHE_FILE}")
                self.after(0, lambda: self.notifier.show_notification("Offline และไม่พบไฟล์แคชข้อมูลยา", success=False))
        
        # 6. เรียก Callback (เช่น Frame2.refresh_medications)
        if on_complete_callback:
            self.after(0, on_complete_callback)
            
        # 7. ซ่อนหน้า Loading (ถ้าถูกเรียกให้แสดง)
        if show_loading_screen:
            self.after(0, self.hide_loading)
            
        # 8. ปลดล็อกสถานะ "กำลังโหลด"
        self._is_med_cache_loading = False
    def _async_update_wifi_status(self, is_connected: bool):
        """
        ฟังก์ชันนี้ถูกเรียกโดย Background Thread เพื่อส่งค่ากลับมายัง Main Thread
        """
        # ใช้ self.after() เพื่อให้โค้ดรันใน Main Thread อย่างปลอดภัย (UI Thread)
        self.after(0, lambda: self._update_wifi_status_gui(is_connected))
        
    def _update_wifi_status_gui(self, is_connected: bool):
        old_status = self.network_status_var.get()
        
        new_status = "online" if is_connected else "offline"
        self.network_status_var.set(new_status)
        
        # ⭐ อัปเดต UI ทันทีเมื่อสถานะเครือข่ายเปลี่ยน
        print(f"🔄 Network status changed: {old_status} -> {new_status}")
        
        # อัปเดต HomePage UI ทันที
        if hasattr(self, 'frames') and HomePage in self.frames:
            home_page = self.frames[HomePage]
            if hasattr(home_page, 'check_network_and_update_buttons'):
                try:
                    home_page.check_network_and_update_buttons()
                    print(f"✅ Updated HomePage UI for network status: {new_status}")
                except Exception as e:
                    print(f"❌ Error updating HomePage UI: {e}")
        
        # info_frame = None
        # for frame_instance in self.frames.values():
        #     if hasattr(frame_instance, 'entry_status'):
        #         info_frame = frame_instance
        #         break
        
        # if info_frame:
        #     entry = info_frame.entry_status
        #     new_color = "#2E7D32" if is_connected else "#D32F2F"
        #     try:
        #         entry.configure(state='normal')
        #         entry.delete(0, ctk.END)
        #         entry.insert(0, new_status) 
        #         entry.configure(state='disabled', text_color=new_color)
        #     except Exception as e:
        #         print(f"❌ Error updating entry_status in GUI: {e}")


        if new_status == "online" and not self.has_sent_online_notification:
            
            self.has_sent_online_notification = True
            
            if self.user: 
                try:
                    user_name = self.user.get('firstname_th', 'ผู้ใช้')
                    device_id = self.user.get('device_id', 'N/A')
                    line_token = self.user.get('token_line')
                    line_group = self.user.get('group_id')
                    tg_token = self.user.get('telegram_key')
                    tg_id = self.user.get('telegram_id')

                    line_message = (
                        f"[SeniorCare Pro]\\n"
                        f"เครื่องจ่ายยา (ID: {device_id})\\n"
                        f"สำหรับคุณ: {user_name}\\n"
                        f"ได้เชื่อมต่ออินเทอร์เน็ตและพร้อมใช้งานแล้ว"
                    )


                    # sendtoLine(line_token, line_group, line_message)
                
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดขณะเตรียมส่งแจ้งเตือนออนไลน์: {e}")
            else: 
                print("⚠️ ไม่สามารถส่งแจ้งเตือนออนไลน์ได้, self.user ยังไม่ถูกโหลด")
        
        # --- END: โค้ดใหม่ ---


        # 6. ตรวจสอบเพื่อ Sync ข้อมูล (โค้ดเดิมของคุณ)
        if old_status == "offline" and new_status == "online":
            print("✅ Network is BACK ONLINE. Checking for offline tasks to sync...")
            # เริ่มการซิงค์ใน Thread แยก เพื่อไม่ให้ UI ค้าง
            threading.Thread(target=self.sync_offline_tasks, daemon=True).start()
    def sync_offline_tasks(self):
        QUEUE_FILE = "offline_schedule_queue.json"
        
        if not os.path.exists(QUEUE_FILE):
            return




        # 1. อ่านคิว
        tasks = []
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            if not tasks or not isinstance(tasks, list):
                print("Sync: ไฟล์คิวว่างเปล่า หรือรูปแบบผิด")
                os.remove(QUEUE_FILE) # ลบไฟล์ที่ไม่มีข้อมูล
                return
            
        except Exception as e:
            print(f"Sync: Error reading queue file: {e}")
            return
            
        
        remaining_tasks = [] # เก็บ task ที่ยังซิงค์ไม่สำเร็จ
        synced_count = 0

        for task in tasks:
            try:
                task_type = task.get("type")
                
                if task_type == "save_history_eat" and "payload" in task:
                    payload = task["payload"]
                    print(f"Sync: กำลังบันทึกประวัติการกินยา... ({payload['medicine_get']})")

                    url = 'http://medic.ctnphrae.com/php/api/save_historyeat.php'
                    try:
                        resp = requests.post(url, json=payload, timeout=10)
                        if resp.status_code == 200:
                            print(f"Sync: บันทึกประวัติสำเร็จ")
                            synced_count += 1
                        else:
                            print(f"Sync: Server ตอบกลับผิดพลาด ({resp.status_code})")
                            remaining_tasks.append(task)
                    except Exception as e:
                        print(f"Sync: เชื่อมต่อล้มเหลว ({e})")
                        remaining_tasks.append(task)

                if task_type == "update_counter" and "payload" in task:
                    payload = task["payload"]
                    print(f"Sync: กำลังอัปเดตจำนวนยา... ({payload['count']} เม็ด)")
                    
                    # ยิง API โดยตรง
                    url = "http://medic.ctnphrae.com/php/api/updatecounter.php"
                    try:
                        resp = requests.post(url, json=payload, timeout=10)
                        if resp.status_code == 200:
                            print(f"Sync: อัปเดตจำนวนยาสำเร็จ")
                            synced_count += 1
                        else:
                            print(f"Sync: Server ตอบกลับผิดพลาด ({resp.status_code})")
                            remaining_tasks.append(task)
                    except Exception as e:
                        print(f"Sync: เชื่อมต่อล้มเหลว ({e})")
                        remaining_tasks.append(task)
                if task_type == "set_time" and "payload" in task:
                    payload = task["payload"]
                    
                    result = set_dispensing_time.set_time(
                        payload['device_id'],
                        payload['start_date'],
                        payload['end_date']
                    )
                    
                    if result and result.get('status') == True:
                        print(f"Sync: ซิงค์ task 'set_time' {task['timestamp']} สำเร็จ")
                        synced_count += 1
                    else:
                        print(f"Sync: เซิร์ฟเวอร์ปฏิเสธ task 'set_time' {task['timestamp']}. จะลองใหม่รอบหน้า")
                        remaining_tasks.append(task)
                
                # --- ⭐️ [เพิ่ม] Task 2: ตั้งค่ามื้อยา (จาก JSON ที่คุณส่งมา) ⭐️ ---
                elif task_type == "set_meal" and "payload" in task:
                    payload = task["payload"]
                    
                    # เรียกใช้ set_meal จาก object ที่เป็น global
                    result = set_dispensing_time.set_meal(
                        payload['device_id'],
                        payload['user_id'],
                        payload['meal_data'] # ⭐️ ส่งข้อมูล meal_data ที่เราบันทึกไว้
                    )
                    
                    if result and result.get('status') == True:
                        print(f"Sync: ซิงค์ task 'set_meal' {task['timestamp']} สำเร็จ")
                        synced_count += 1
                    else:
                        print(f"Sync: เซิร์ฟเวอร์ปฏิเสธ task 'set_meal' {task['timestamp']}. จะลองใหม่รอบหน้า")
                        remaining_tasks.append(task)
                # -----------------------------------------------------------------

                else:
                    print(f"Sync: ข้าม task ประเภทที่ไม่รู้จัก: {task_type}")

            except Exception as e:
                print(f"Sync: เกิดข้อผิดพลาดขณะซิงค์ task {task['timestamp']}: {e}. จะลองใหม่รอบหน้า")
                remaining_tasks.append(task) # บันทึกกลับเข้าคิว
            
            # หน่วงเวลาเล็กน้อย
            time.sleep(1) 

        # 3. เขียน task ที่ยังทำไม่สำเร็จ กลับลงไฟล์
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(remaining_tasks, f, indent=4)
            
            # แจ้งเตือนใน UI (ต้องใช้ self.after เพื่อให้รันใน Main Thread)
            if synced_count > 0:
                print(f"Sync: ซิงค์สำเร็จ {synced_count} รายการ")
                self.after(0, lambda: self.notifier.show_notification(
                    f"ซิงค์ข้อมูล {synced_count} รายการสำเร็จ", success=True
                ))
            
            if len(remaining_tasks) > 0:
                print(f"Sync: {len(remaining_tasks)} task ยังคงค้างอยู่ในคิว")
                self.after(0, lambda: self.notifier.show_notification(
                    f"ซิงค์ข้อมูลไม่สำเร็จ {len(remaining_tasks)} รายการ", success=False
                ))
            
            if len(remaining_tasks) == 0 and synced_count > 0:
                 print("Sync: คิวว่างเปล่าแล้ว")
                 os.remove(QUEUE_FILE) # ลบไฟล์ทิ้งถ้าซิงค์หมดแล้ว

        except Exception as e:
            print(f"Sync: CRITICAL error writing back to queue file: {e}")
            
    def start_background_polling(self):
        if not self.polling_thread_active:
           print("--- [MainApp] Starting background polling thread... ---")
           self.polling_thread_active = True
           self.polling_thread_handle = threading.Thread(
                target=self._polling_loop, 
                daemon=True
            ) 
           self.polling_thread_handle.start()
        else:
            print("--- [MainApp] Polling thread is already running. ---")

    def stop_background_polling(self):
        print("--- [MainApp] Received stop signal. ---")
        self.polling_thread_active = False 
        self.user = None                  
        self.last_known_schedule_data = None 
        self.polling_thread_handle = None

    def _polling_loop(self):
        
        while self.polling_thread_active:

            if not self.user:
                print("ไม่พบข้อมูลผู้ใช้งาน")
                time.sleep(5)
                continue

            try:
                new_data = set_dispensing_time.get_meal(
                    self.user['device_id'],
                    self.user['id']
                )
                if new_data and 'data' in new_data:
                    recivetime(new_data['data'])
                data_changed = False

                with self.data_lock:
                    if new_data and new_data != self.last_known_schedule_data:
                        self.last_known_schedule_data = new_data
                        data_changed = True

                if data_changed:
                    current_frame = self.frames[HomePage]    
                    if current_frame.winfo_viewable():
                        self.after(0, current_frame._render_medication_data, new_data, None)
            except Exception as e:
                print(f"[Polling Thread] Error during API poll: {e}")

            time.sleep(30)


    def start_serial_thread(self):
        try:
            # กำหนด Port และ Baudrate สำหรับเชื่อม UART (TX/RX) กับ Raspberry Pi
            # /dev/serial0 จะชี้ไปยัง UART หลัก (GPIO14 TXD0, GPIO15 RXD0) บน Pi 5
            PORT = "/dev/serial0"
            BAUDRATE = 115200

            # สร้าง callback function เพื่อตรวจสอบจำนวนยาคงเหลือ
            def get_medicine_count():
                """Callback function ที่คืนค่าจำนวนยาคงเหลือ"""
                try:
                    if hasattr(self, 'user') and self.user:
                        count = self.user.get('count_medicine')
                        if count is not None:
                            return int(count)
                except Exception as e:
                    print(f"Error getting medicine count: {e}")
                return None

            # สร้าง callback function สำหรับแจ้งเตือน LINE
            def notification_callback(notification_type, identifier, message):
                """
                Callback function สำหรับแจ้งเตือนผ่าน LINE และบันทึกประวัติการจ่ายยา
                
                Args:
                    notification_type: ประเภทการแจ้งเตือน (เช่น "cmd_success", "cmd_failed", "save_history_failed")
                    identifier: ตัวระบุเพิ่มเติม (เช่น schedule_time, command_id)
                    message: ข้อความที่จะส่ง (None ถ้าเป็น flag สำหรับบันทึกประวัติ)
                """
                try:
                    # ตรวจสอบว่าต้องบันทึกประวัติการจ่ายยาหรือไม่
                    if notification_type == "save_history_failed":
                        # บันทึกประวัติการจ่ายยาล้มเหลว
                        self._save_medicine_history("failed")
                        return
                    
                    if notification_type == "trigger_sos_call":
                        self._trigger_sos_call(identifier)
                        return
                    
                    if not hasattr(self, 'user') or not self.user:
                        print("[Notification] ไม่สามารถส่งแจ้งเตือน: ยังไม่มีข้อมูลผู้ใช้")
                        return
                    
                    line_token = self.user.get('token_line')
                    line_group = self.user.get('group_id')
                    
                    if not line_token or not line_group:
                        print("[Notification] ไม่สามารถส่งแจ้งเตือน: ไม่มี LINE Token หรือ Group ID")
                        return
                    
                    # ถ้า message เป็น None ให้ข้ามการส่ง LINE
                    if message is None:
                        return
                    
                    # ส่งข้อความผ่าน LINE พร้อมป้องกันการส่งซ้ำ
                    sendtoLineWithDeduplication(
                        token=line_token,
                        group_id=line_group,
                        message_data=message,
                        notification_type=notification_type,
                        identifier=identifier
                    )
                except Exception as e:
                    print(f"[Notification] เกิดข้อผิดพลาดขณะส่งแจ้งเตือน: {e}")

            serial_thread = threading.Thread(
                target=start_Serial_loop, 
                args=(
                    PORT, 
                    BAUDRATE, 
                    self.battery_percent_var, 
                    self.device_status_var,
                    5.0,  # request_interval
                    notification_callback,  # notification_callback
                    get_medicine_count,
                    self.voice_player.play,
                ),
                daemon=True 
            )
            serial_thread.start()
        except Exception as e:
            print(f"--- [MainApp] FAILED to start serial thread: {e} ---")
            self.device_status_var.set(f"Serial Error: {e}")

    def _trigger_sos_call(self, reason_identifier=None):
        """
        เริ่มการกดปุ่ม SOS อัตโนมัติ (ใช้เมื่อผู้ป่วยไม่มารับยาครบ 6 รอบ)
        """
        if getattr(self, "_auto_sos_in_progress", False):
            print("[Auto SOS] กำลังโทรอยู่แล้ว ข้ามการเรียกซ้ำ")
            return

        if not hasattr(self, 'user') or not self.user:
            print("[Auto SOS] ไม่มีข้อมูลผู้ใช้ ไม่สามารถโทร SOS ได้")
            return

        line_token = self.user.get('token_line')
        line_group = self.user.get('group_id')

        if not line_token or not line_group:
            print("[Auto SOS] ไม่มี Token หรือ Group ID สำหรับ SOS")
            return

        if getattr(self, "network_status_var", None) and self.network_status_var.get() == "offline":
            print("[Auto SOS] เครือข่ายออฟไลน์ ไม่สามารถโทร SOS ได้")
            return

        self._auto_sos_in_progress = True

        def _auto_sos_thread():
            try:
                print(f"[Auto SOS] เริ่มโทร SOS อัตโนมัติ (reason={reason_identifier})")
                send_status = press_sos_automation(line_token, line_group)

                if hasattr(self, 'notifier') and self.notifier:
                    if send_status:
                        self.after(
                            0,
                            lambda: self.notifier.show_notification(
                                "ระบบโทร SOS อัตโนมัติแล้ว", success=True
                            )
                        )
                    else:
                        self.after(
                            0,
                            lambda: self.notifier.show_notification(
                                "ส่งคำขอ SOS อัตโนมัติไม่สำเร็จ", success=False
                            )
                        )
            except Exception as e:
                print(f"[Auto SOS] เกิดข้อผิดพลาด: {e}")
                if hasattr(self, 'notifier') and self.notifier:
                    self.after(
                        0,
                        lambda: self.notifier.show_notification(
                            f"SOS อัตโนมัติผิดพลาด: {e}", success=False
                        )
                    )
            finally:
                self._auto_sos_in_progress = False

        threading.Thread(target=_auto_sos_thread, daemon=True).start()
    def _get_medicines_for_current_time(self):
        """
        ดึง medicine_id จาก schedule ที่ตรงกับเวลาปัจจุบัน
        
        Returns:
            list: array ของ medicine_id (สูงสุด 4 ตัว) หรือ [] ถ้าไม่พบ
        """
        try:
            # ตรวจสอบว่ามีข้อมูล schedule หรือไม่
            if not hasattr(self, 'last_known_schedule_data') or not self.last_known_schedule_data:
                # ลองโหลดจาก cache
                CACHE_FILE = "time_data.json"
                if os.path.exists(CACHE_FILE):
                    try:
                        with open(CACHE_FILE, "r", encoding="utf-8") as f:
                            schedule_data = json.load(f)
                            if schedule_data:
                                self.last_known_schedule_data = {'data': schedule_data}
                    except Exception as e:
                        print(f"Error loading schedule cache: {e}")
                        return []
                else:
                    return []
            
            # ดึงข้อมูล schedule
            meal_data = self.last_known_schedule_data
            if not meal_data or 'data' not in meal_data:
                return []
            
            # สร้าง reverse map จากชื่อยาไป medicine_id
            medicine_name_to_id = {}
            if hasattr(self, 'cached_medications') and self.cached_medications:
                with self.medicine_data_lock:
                    for med in self.cached_medications:
                        if 'medicine_name' in med and 'medicine_id' in med:
                            medicine_name_to_id[med['medicine_name']] = med['medicine_id']
            
            if not medicine_name_to_id:
                print("[Save History] ไม่พบข้อมูลยาใน cached_medications")
                return []
            
            # หา schedule ที่ตรงกับเวลาปัจจุบัน
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            
            medications = meal_data['data']
            medicine_ids = []
            
            for med in medications:
                schedule_time = med.get('time', '')
                if not schedule_time:
                    continue
                
                # เปรียบเทียบเวลา (รองรับรูปแบบ HH:MM และ HH:MM:SS)
                schedule_time_clean = schedule_time.split(':')[:2]  # เอาแค่ HH:MM
                current_time_clean = current_time_str.split(':')[:2]
                
                if schedule_time_clean == current_time_clean:
                    # พบ schedule ที่ตรงกับเวลาปัจจุบัน
                    # ดึง medicine_id จาก medicine_1 ถึง medicine_4
                    for i in range(1, 5):
                        med_name = med.get(f'medicine_{i}', '')
                        if med_name and med_name in medicine_name_to_id:
                            medicine_ids.append(medicine_name_to_id[med_name])
                    
                    # หาเจอแล้ว ให้ return
                    break
            
            return medicine_ids[:4]  # จำกัดสูงสุด 4 ตัว
            
        except Exception as e:
            print(f"[Save History] Error getting medicines for current time: {e}")
            return []
    
    def _save_medicine_history(self, medicine_get):
        """
        บันทึกประวัติการจ่ายยาลงฐานข้อมูล
        
        Args:
            medicine_get: "success" หรือ "failed"
        """
        try:
            if not hasattr(self, 'user') or not self.user:
                print("[Save History] ไม่พบข้อมูลผู้ใช้")
                return
            
            # ดึงข้อมูลที่จำเป็น
            device_id = self.user.get('device_id')
            user_id = self.user.get('id')
            
            if not device_id or not user_id:
                print("[Save History] ไม่พบ device_id หรือ id")
                return
            
            # ดึง medicine_id จาก schedule ที่ตรงกับเวลาปัจจุบัน
            medicines = self._get_medicines_for_current_time()
            
            if not medicines:
                print("[Save History] ไม่พบข้อมูลยาสำหรับเวลาปัจจุบัน")
                return
            
            # ตรวจสอบ network status
            network_status = self.network_status_var.get()
            status_param = "online" if network_status == "online" else None
            
            # เรียกใช้ save_history_eat
            result = medicine_report.save_history_eat(
                device_id=device_id,
                medicines=medicines,
                id=user_id,
                medicine_get=medicine_get,
                status=status_param
            )
            
            if result and result.get('status'):
                print(f"[Save History] บันทึกประวัติการจ่ายยา ({medicine_get}) สำเร็จ")
            else:
                message = result.get('message', 'Unknown error') if result else 'No result'
                print(f"[Save History] บันทึกประวัติการจ่ายยา ({medicine_get}) ล้มเหลว: {message}")
                
        except Exception as e:
            print(f"[Save History] เกิดข้อผิดพลาดขณะบันทึกประวัติ: {e}")

    # อัพเดตสถานะการจ่ายยา
    def status_callback(self,*args):
        new_status = str(self.device_status_var.get())
        normalized_status = self._normalize_status_value(new_status)
        current_time = time.time()

        if normalized_status == "complete":
            fail_start = self.status_timestamps.get("fail")
            duration = None
            if fail_start:
                duration = current_time - fail_start
                duration_minutes = duration / 60
                alert_delay = self.user.get('alert_delay', 0) if self.user else 0
                if duration_minutes > alert_delay:
                    print(f"!!! test !!! (Duration {duration:.0f}s > {alert_delay}m)")
                else:
                    print(f"--- ทดสอบ --- (Duration {duration:.0f}s <= {alert_delay}m)")
            else:
                print("Status: complete (จ่ายยาสำเร็จค่ะ)")

            if getattr(self, 'voice_player', None):
                self.voice_player.play("complete")

            homePage = self.frames[HomePage]
            homePage.reduce_medicine()
            self._save_medicine_history("success")

        elif normalized_status == "fail":
            print("Status: fail (จ่ายยาล้มเหลวค่ะ)")
            if getattr(self, 'voice_player', None):
                self.voice_player.play("fail")

        elif normalized_status == "nopush":
            print("Status: nopush (ยังไม่มีการดันยาค่ะ)")

        elif normalized_status:
            print(f"Status update: {normalized_status}")
        else:
            print(f"Status update: {new_status}")

    @staticmethod
    def _normalize_status_value(status):
        if status is None:
            return None
        status_str = str(status).strip().lower()
        if status_str in {"fail", "complete", "nopush"}:
            return status_str
        if status_str == "0":
            return "fail"
        if status_str == "1":
            return "complete"
        return status_str

    def load_user_data(self):

        """โหลดข้อมูลผู้ใช้จากไฟล์"""

        if os.path.exists("user_data.json"):
            try:
                with open("user_data.json", "r", encoding='utf-8') as f:
                    user_data = json.load(f)
                print(f"โหลดข้อมูลผู้ใช้: {user_data}")
                
                if user_data:
                    self.user = user_data
                    self.is_test_account = self.user.get("email") == TEST_MODE_EMAIL
                    self.network_status_var.set("online")
                    self.show_frame(HomePage)
                    home_frame = self.frames.get(HomePage)
                    if home_frame:
                        home_frame.update_test_mode_visibility()

                else:
                    self.is_test_account = False
                    home_frame = self.frames.get(HomePage)
                    if home_frame:
                        home_frame.update_test_mode_visibility()
                    
                    # Start AI Service automatically
                    self.start_ai_service()
                    
                    self.show_frame(login)
            except Exception as e:
                print(f"Error loading user_data.json: {e}")
                self.is_test_account = False
                home_frame = self.frames.get(HomePage)
                if home_frame:
                    home_frame.update_test_mode_visibility()
                self.show_frame(login)
        else:
            print("user_data.json not found - showing login page")
            self.is_test_account = False
            home_frame = self.frames.get(HomePage)
            if home_frame:
                home_frame.update_test_mode_visibility()
            self.show_frame(login)
    

    def start_network_monitor_service(self):
        if not self.user or 'id' not in self.user:
            print("Cannot start Network Monitor: No user ID.")
            return

        if hasattr(self, 'network_monitor') and self.network_monitor.is_alive():
            print("Network Monitor is already running.")
            return

        try:
            print(f"Starting Network Monitor for Device ID: {self.user['id']}")
            self.network_monitor = NetworkMonitor(
                id=self.user['id'], 
                ui_callback=self._async_update_wifi_status,
                monitor_interval=10
            )
            self.network_monitor.start()
        except Exception as e:
            print(f"Failed to start Network Monitor: {e}")
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
            # --- หยุด Network Monitor Thread ก่อนปิด ---
            if hasattr(self, 'network_monitor') and self.network_monitor.is_alive():
                print("Stopping Network Monitor...")
                self.network_monitor.stop()
                self.network_monitor.stop()
                self.network_monitor.join() 
            
            # --- หยุด AI Service ก่อนปิด ---
            self.stop_ai_service()
            # ------------------------------- 
            # ------------------------------------------
            
            print("Closing application...")
            self.destroy()
        except Exception as e:
            print(f"Error closing application: {e}")
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
        
        print("Starting SeniorCare Pro application")
        app.mainloop()
        
    except Exception as e:
        print(f"Error running application: {ascii(e)}")


if __name__ == "__main__":
    main()
