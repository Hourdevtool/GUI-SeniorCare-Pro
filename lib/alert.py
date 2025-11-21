import requests
import json
import threading
import time
from threading import Lock

def _sendtoTelegram_blocking(MESSAGE, TOKEN, CHAT_ID):
    if not TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    body = {
        "chat_id": CHAT_ID,
        "text": MESSAGE,
        "parse_mode": 'HTML',
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=10) # เพิ่ม timeout
    except requests.exceptions.RequestException as e:
        print(f"[Telegram Thread] เกิดข้อผิดพลาด: {e}")

def sendtoTelegram(MESSAGE, TOKEN, CHAT_ID):

    
    thread = threading.Thread(
        target=_sendtoTelegram_blocking,
        args=(MESSAGE, TOKEN, CHAT_ID),
        daemon=True  
    )
    thread.start()


def _sendtoLine_blocking(token, group_id, message_data):
    """
    [ตัวทำงานเบื้องหลัง] ฟังก์ชันนี้จะตรวจสอบประเภทของ message_data 
    และสร้าง payload ที่ถูกต้องสำหรับส่ง LINE
    """
    
    if not token or not group_id:
        print("[LINE Thread] Error: ไม่มี Token หรือ Group ID")
        return False

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # ⭐️ [แก้ไข] สร้าง message object แบบไดนามิก ⭐️
    message_object = {}
    
    if isinstance(message_data, str):
        # 1. ถ้าส่งมาเป็น "String" ธรรมดา -> ส่งเป็น Text Message
        message_object = {
            'type': 'text', 
            'text': message_data
        }
    
    elif isinstance(message_data, dict):
        # 2. ถ้าส่งมาเป็น "Dictionary" -> ส่งเป็น Flex Message
        message_object = {
            'type': 'flex',
            'altText': 'มีข้อความแจ้งเตือนใหม่ (โปรดเปิดดูในมือถือ)', # ⭐️ ข้อความสำรอง
            'contents': message_data # ⭐️ message_data คือ JSON ของ Flex ที่คุณสร้าง
        }
    
    else:
        print(f"[LINE Thread] Error: ไม่รองรับประเภทข้อมูล {type(message_data)}")
        return False
    # -----------------------------------------------

    payload = {
        'to': group_id,
        'messages': [message_object] # ⭐️ ใช้ object ที่สร้างขึ้นใหม่
    }
    
    try:
        # (ใช้ json.dumps() เพื่อแปลง Python dict เป็น JSON string)
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10) 
        
        if response.status_code == 200:
            print("[LINE Thread] ส่งข้อความสำเร็จ")
            return True
        else:
            # ⭐️ แสดง Error ที่ LINE ตอบกลับมา (สำคัญมาก)
            print(f"[LINE Thread] LINE API Error: {response.status_code}")
            print(f"[LINE Thread] Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[LINE Thread] เกิดข้อผิดพลาด Requests: {e}")
        return False

def sendtoLine(token, group_id, message_data):
    """
    [ตัวเรียก] สั่งส่งข้อความ (Text หรือ Flex) ไปยัง LINE ใน Thread แยก
    """
    
    thread = threading.Thread(
        target=_sendtoLine_blocking,
        args=(token, group_id, message_data), # ⭐️ เปลี่ยนชื่อเป็น message_data
        daemon=True 
    )
    thread.start()


# ========== ระบบป้องกันการส่งซ้ำ ==========
_notification_cache = {}  # เก็บ key และ timestamp ของการแจ้งเตือนที่ส่งไปแล้ว
_notification_lock = Lock()  # Lock สำหรับ thread-safe
_DEDUPLICATION_WINDOW = 300  # 5 นาที (300 วินาที) - ไม่ส่งซ้ำภายในเวลานี้


def _generate_notification_key(notification_type, identifier=""):
    """
    สร้าง unique key สำหรับการแจ้งเตือน
    
    Args:
        notification_type: ประเภทการแจ้งเตือน (เช่น "cmd_success", "cmd_failed", "schedule_success")
        identifier: ตัวระบุเพิ่มเติม (เช่น schedule_time, command_id)
    
    Returns:
        str: unique key
    """
    return f"{notification_type}_{identifier}"


def _should_send_notification(key):
    """
    ตรวจสอบว่าควรส่งการแจ้งเตือนหรือไม่ (ป้องกันการส่งซ้ำ)
    
    Args:
        key: unique key ของการแจ้งเตือน
    
    Returns:
        bool: True ถ้าควรส่ง, False ถ้าไม่ควรส่ง (เพราะส่งไปแล้ว)
    """
    with _notification_lock:
        current_time = time.time()
        
        # ตรวจสอบว่ามี key นี้ใน cache หรือไม่
        if key in _notification_cache:
            last_sent_time = _notification_cache[key]
            time_diff = current_time - last_sent_time
            
            # ถ้ายังไม่ครบเวลาที่กำหนด ให้ข้าม
            if time_diff < _DEDUPLICATION_WINDOW:
                print(f"[Notification] ข้ามการส่งซ้ำ: {key} (ส่งไปแล้วเมื่อ {time_diff:.0f} วินาทีที่แล้ว)")
                return False
        
        # บันทึกเวลาที่ส่ง
        _notification_cache[key] = current_time
        
        # ลบ key เก่าที่หมดอายุแล้ว (เพื่อประหยัด memory)
        expired_keys = [
            k for k, v in _notification_cache.items()
            if current_time - v > _DEDUPLICATION_WINDOW * 2
        ]
        for k in expired_keys:
            del _notification_cache[k]
        
        return True


def sendtoLineWithDeduplication(token, group_id, message_data, notification_type, identifier=""):
    """
    ส่งข้อความ LINE พร้อมป้องกันการส่งซ้ำ
    
    Args:
        token: LINE Bot Token
        group_id: LINE Group ID
        message_data: ข้อความที่จะส่ง (str หรือ dict)
        notification_type: ประเภทการแจ้งเตือน (เช่น "cmd_success", "cmd_failed", "schedule_success")
        identifier: ตัวระบุเพิ่มเติม (เช่น schedule_time, command_id) - optional
    
    Returns:
        bool: True ถ้าส่งสำเร็จ, False ถ้าข้าม (เพราะส่งซ้ำ) หรือเกิด error
    """
    if not token or not group_id:
        print("[Notification] Error: ไม่มี Token หรือ Group ID")
        return False
    
    # สร้าง unique key
    key = _generate_notification_key(notification_type, identifier)
    
    # ตรวจสอบว่าควรส่งหรือไม่
    if not _should_send_notification(key):
        return False
    
    # ส่งข้อความ
    thread = threading.Thread(
        target=_sendtoLine_blocking,
        args=(token, group_id, message_data),
        daemon=True
    )
    thread.start()
    
    print(f"[Notification] ส่งการแจ้งเตือน: {notification_type} ({identifier})")
    return True


def clear_notification_cache():
    """ล้าง cache ของการแจ้งเตือน (ใช้สำหรับ testing หรือ reset)"""
    with _notification_lock:
        _notification_cache.clear()
        print("[Notification] ล้าง cache แล้ว")