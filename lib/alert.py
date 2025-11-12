import requests
import json
def sendtoTelegram(MESSAGE,TOKEN,CHAT_ID):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    body = {
        "chat_id":CHAT_ID,
        "text":MESSAGE,
        "parse_mode":'HTML',
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=body, headers=headers)

    print("HTTP Status Code:", response.status_code)
    print("Response Body:", response.text)


def sendtoLine(token, group_id, message_text):

    url = 'https://api.line.me/v2/bot/message/push'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        'to': group_id,
        'messages': [
            {
                'type': 'text',
                'text': message_text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            print(f"ส่ง Push Message สำเร็จ: '{message_text}'")
            return True
        else:
            print(f"ส่งข้อความไม่สำเร็จ: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ API: {e}")
        return False
    

