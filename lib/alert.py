import requests
import json
import threading

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