
import requests
import json
import os
from datetime import datetime
class eat_medicine_report:

    
    def get_eatmedic(self,id):

        getmedicine_url = 'http://medic.ctnphrae.com/php/api/get_medicinereport.php';

        id_data = {
            'id': id
        }

        response = requests.get(getmedicine_url, json=id_data)

        return response.json()

    def save_history_eat(self,device_id,medicines,id,medicine_get, status=None):
        save_url = 'http://medic.ctnphrae.com/php/api/save_historyeat.php'
        
        payload={
            'device_id' : device_id,
            'medicines': medicines,
            'id' :id,
            'medicine_get': medicine_get
        }

        if status == "online":
            try:
                response = requests.post(save_url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ Server Error: {response.status_code}")   
            except requests.exceptions.RequestException as e:
                print(f"❌ Connection Error (Save History): {e}")
        
        
        self._save_to_queue(payload)

        return {'status': True, 'message': 'Offline: Saved to queue'}
    
    def _save_to_queue(self, payload):
        QUEUE_FILE = "offline_schedule_queue.json"
        
        new_task = {
            "type": "save_history_eat", 
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }

        queue = []
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    queue = json.load(f)
                if not isinstance(queue, list): queue = []
            except json.JSONDecodeError:
                queue = []
        
        queue.append(new_task)

        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4)
            print(f"Task 'save_history_eat' saved to queue.")
        except Exception as e:
            print(f"Error writing to queue file: {e}")