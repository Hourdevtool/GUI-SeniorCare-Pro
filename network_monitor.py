import threading
import time
import warnings
from pywifi import PyWiFi, const
import requests
import json
# นำเข้า Devicestatus จากไฟล์ device_status.py
# อิงตามโครงสร้างใน main.py ที่มีการนำเข้าจาก server.device_status
try:
    from server.device_status import Devicestatus
except ImportError:
    # ใช้ import นี้หากไฟล์ device_status.py อยู่ในโฟลเดอร์เดียวกันกับ network_monitor.py
    from device_status import Devicestatus 

# ปิด Warning ของ pywifi 
warnings.filterwarnings("ignore", message=".*")

class NetworkMonitor(threading.Thread):
    """
    Class สำหรับมอนิเตอร์สถานะเครือข่าย Wi-Fi ใน Background Thread
    และอัปเดตสถานะไปยัง Database โดยตรง
    """
    def __init__(self, device_id: str, ui_callback, monitor_interval: int = 60):
        """
        :param device_id: ID ของอุปกรณ์
        :param ui_callback: ฟังก์ชัน callback ที่จะถูกเรียกใน MainApp เมื่อสถานะเปลี่ยน
        :param monitor_interval: ช่วงเวลาในการตรวจสอบ (วินาที)
        """
        super().__init__()
        self.device_id = device_id
        self.ui_callback = ui_callback # ฟังก์ชันสำหรับส่งค่ากลับไปยัง MainApp
        self.monitor_interval = monitor_interval
        self._stop_event = threading.Event()
        self.device_status_updater = Devicestatus()
        self.last_status = None # สถานะสุดท้ายที่ถูกส่งไป
        self.daemon = True 
        
        # กำหนดค่าสถานะที่ใช้ส่งไปยัง Database และ UI
        self.ONLINE_STATUS_VALUE = 'online'
        self.OFFLINE_STATUS_VALUE = 'offline'

    def is_wifi_connected(self) -> bool:
        """ตรวจสอบสถานะการเชื่อมต่อ Wi-Fi โดยใช้ pywifi"""
        try:
            wifi = PyWiFi()
            if not wifi.interfaces():
                return False
            
            iface = wifi.interfaces()[0]
            # const.IFACE_CONNECTED คือค่าสถานะเมื่อเชื่อมต่อแล้ว
            return iface.status() == const.IFACE_CONNECTED
        except Exception:
            # หากเกิดข้อผิดพลาดในการเรียกใช้ pywifi ให้ถือว่าไม่ได้เชื่อมต่อ
            return False

    def run(self):
        """เมธอดที่รันใน Background ลูป"""
        print(f"✅ Network Monitor Thread Started for Device ID: {self.device_id}")
        
        while not self._stop_event.is_set():
            is_connected = self.is_wifi_connected()
            # current_db_status คือค่า 'online' หรือ 'offline' ที่จะส่งไป DB
            current_db_status = self.ONLINE_STATUS_VALUE if is_connected else self.OFFLINE_STATUS_VALUE
            
            # 1. ตรวจสอบการเปลี่ยนแปลงสถานะ (หรือเป็นการรันครั้งแรก)
            if current_db_status != self.last_status or self.last_status is None:
                
                print(f"🌐 Wi-Fi status change detected: {'Online' if is_connected else 'Offline'} (DB Value: {current_db_status}).")
                
                # 2. อัปเดตสถานะไปยัง Database โดยตรง
                try:
                    # ใช้ Devicestatus.setstatus(device_id, status)
                    result = self.device_status_updater.setstatus(self.device_id, current_db_status)
                    
                    # ตรวจสอบว่าการอัปเดตสำเร็จหรือไม่ (ตรวจสอบจาก result ที่ไม่เป็น None)
                    if result is not None:
                        print(f"✅ Status updated successfully to DB ({current_db_status}).")
                        self.last_status = current_db_status
                        
                        # 3. ส่งค่ากลับไปยัง MainApp ผ่าน Callback Function
                        self.ui_callback(is_connected) 
                    else:
                        print(f"❌ Status update failed (DB). Response: {result}")
                        # ไม่ต้องอัปเดต last_status เพื่อให้พยายามส่งใหม่ในรอบหน้า
                        
                except Exception as e:
                    print(f"❌ Error calling setstatus (HTTP): {e}")
            else:
                # สถานะเดิม ไม่ต้องอัปเดต DB
                print(f"✅ Wi-Fi status is still {'Online' if is_connected else 'Offline'}. Skipping DB update.")
            
            # รอตามช่วงเวลาที่กำหนด
            self._stop_event.wait(self.monitor_interval)
        
        print("🛑 Network Monitor Thread Stopped.")

    def stop(self):
        """ส่งสัญญาณให้ thread หยุดการทำงาน"""
        self._stop_event.set()