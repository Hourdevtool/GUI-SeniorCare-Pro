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


def _sendtoLine_blocking(token, group_id, message_text):
    
    if not token or not group_id:
        return False

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'to': group_id,
        'messages': [{'type': 'text', 'text': message_text}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10) # เพิ่ม timeout
        if response.status_code == 200:
            
            return True
        else:
            
            return False
    except requests.exceptions.RequestException as e:
        print(f"[LINE Thread] เกิดข้อผิดพลาด: {e}")
        return False

def sendtoLine(token, group_id, message_text):

    
    thread = threading.Thread(
        target=_sendtoLine_blocking,
        args=(token, group_id, message_text),
        daemon=True 
    )
    thread.start()  

