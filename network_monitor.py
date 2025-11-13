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
        """
        ตรวจสอบสถานะการเชื่อมต่อ Internet (ทั้ง Wi-Fi และ LAN)
        (หมายเหตุ: ชื่อฟังก์ชันคงเดิมตามที่ร้องขอ แต่ logic ถูกเปลี่ยนเป็นการเช็กเน็ต)
        """
        try:
            # ใช้ HEAD request เพื่อความรวดเร็ว (ไม่ดึงเนื้อหา)
            # ใช้ timeout เพื่อป้องกันการค้างนานหากเน็ตช้า
            response = requests.head("https://www.google.com", timeout=5)
            # ถ้า status code อยู่ในกลุ่ม 2xx หรือ 3xx ถือว่าเชื่อมต่อได้
            return response.status_code < 400
        except requests.RequestException:
            # ไม่ว่าจะเป็น ConnectionError, Timeout, ฯลฯ
            # ถ้าเกิด Exception แสดงว่าเชื่อมต่อไม่ได้
            return False

    def run(self):
        """เมธอดที่รันใน Background ลูป"""
        print(f"✅ Network Monitor Thread Started for Device ID: {self.id}")
        
        while not self._stop_event.is_set():
            # ใช้ฟังก์ชันเดิม แต่ตอนนี้มันเช็ก Internet (Wi-Fi หรือ LAN)
            is_connected = self.is_wifi_connected()
            
            # current_db_status คือค่า 'online' หรือ 'offline' ที่จะส่งไป DB
            current_db_status = self.ONLINE_STATUS_VALUE if is_connected else self.OFFLINE_STATUS_VALUE
            
                
                
               
            try:
                    # ใช้ Devicestatus.setstatus(id, status)
                    result = self.device_status_updater.setstatus(self.id, current_db_status)
                    self.ui_callback(is_connected) 
                    print(result)
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
        
        print("🛑 Network Monitor Thread Stopped.")

    def stop(self):
        """ส่งสัญญาณให้ thread หยุดการทำงาน"""
        self._stop_event.set()