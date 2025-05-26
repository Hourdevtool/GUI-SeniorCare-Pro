import requests
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
    

