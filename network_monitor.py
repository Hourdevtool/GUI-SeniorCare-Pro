import threading
import time
# ลบ import warnings และ pywifi ออก เพราะไม่ได้ใช้แล้ว
import requests
import json

from server.device_status import Devicestatus

# class NetworkMonitor (คงโครงสร้างเดิม)
class NetworkMonitor(threading.Thread):
    """
    Class สำหรับมอนิเตอร์สถานะเครือข่าย (Internet) ใน Background Thread
    และอัปเดตสถานะไปยัง Database โดยตรง
    """
    def __init__(self, id: str, ui_callback, monitor_interval: int = 60):
        """
        :param id: ID ของอุปกรณ์
        :param ui_callback: ฟังก์ชัน callback ที่จะถูกเรียกใน MainApp เมื่อสถานะเปลี่ยน
        :param monitor_interval: ช่วงเวลาในการตรวจสอบ (วินาที)
        """
        super().__init__()
        self.id = id
        self.ui_callback = ui_callback # ฟังก์ชันสำหรับส่งค่ากลับไปยัง MainApp
        self.monitor_interval = monitor_interval
        self._stop_event = threading.Event()
        self.device_status_updater = Devicestatus()
        self.last_status = None # สถานะสุดท้ายที่ถูกส่งไป
        self.daemon = True 
        
        # กำหนดค่าสถานะที่ใช้ส่งไปยัง Database และ UI
        self.ONLINE_STATUS_VALUE = 'online'
        self.OFFLINE_STATUS_VALUE = 'offline'

    # ⭐️ [แก้ไข] - เปลี่ยน Logic ภายในฟังก์ชันนี้
    def is_wifi_connected(self) -> bool:
     
        try:
            response = requests.head("https://www.google.com", timeout=10)
            return response.status_code < 400
        except requests.RequestException:

            try:
                requests.head("https://1.1.1.1",timeout = 10)
                return True
            except requests.RequestException:
                return False
            

    def run(self):

        
        while not self._stop_event.is_set():
            # ใช้ฟังก์ชันเดิม แต่ตอนนี้มันเช็ก Internet (Wi-Fi หรือ LAN)
            is_connected = self.is_wifi_connected()
            
            # current_db_status คือค่า 'online' หรือ 'offline' ที่จะส่งไป DB
            current_db_status = self.ONLINE_STATUS_VALUE if is_connected else self.OFFLINE_STATUS_VALUE
            
                
                
               
            try:
                    # ใช้ Devicestatus.setstatus(id, status)
                    result = self.device_status_updater.setstatus(self.id, current_db_status)
                    self.ui_callback(is_connected) 
                    # ตรวจสอบว่าการอัปเดตสำเร็จหรือไม่ (ตรวจสอบจาก result ที่ไม่เป็น None)
                    if result is not None:
                        self.last_status = current_db_status
                        
                        # 3. ส่งค่ากลับไปยัง MainApp ผ่าน Callback Function

                    else:
                        print(f"❌ Status update failed (DB). Response: {result}")
                        # ไม่ต้องอัปเดต last_status เพื่อให้พยายามส่งใหม่ในรอบหน้า
                        
            except Exception as e:
                    print(f"❌ Error calling setstatus (HTTP): {e}")

            
            # รอตามช่วงเวลาที่กำหนด
            self._stop_event.wait(self.monitor_interval)
        


    def stop(self):
        """ส่งสัญญาณให้ thread หยุดการทำงาน"""
        self._stop_event.set()