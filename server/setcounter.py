import requests
import json
import os
from datetime import datetime
from lib.counter_medic import countermidecine
class SetCounter:

    def update_counter(self, device_id, id, count,status=None):
        print("Update counter called with count:", status)

        countermidecine(count)
        api_success = False
        if status == "online":
            url = f"http://medic.ctnphrae.com/php/api/updatecounter.php"
            payload = {
                'device_id': device_id,
                'id': id,
                'count': count
            }
            try:
                response = requests.post(url, json=payload, timeout=5) 
                if response.status_code == 200:
                    api_success = True
                else:
                    print(f"Server Error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f" Connection Error during update counter: {e}")
        if not api_success:
            print("⚠️ Offline or Failed. Saving counter update to queue...")
            self.save_counter_to_queue(device_id, id, count)
    def save_counter_to_queue(self,deivce_id,user_id,count):

        QUEUE_FILE = "offline_schedule_queue.json"

        new_task ={
            "type": "update_counter",
            "payload": {
                "device_id": deivce_id,
                "id": user_id,
                "count": count
            },
            "timestamp": datetime.now().isoformat()
        }

        queue = []

        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, 'r') as file:
                    queue = json.load(file)
            except json.JSONDecodeError:
                queue = []
            
        #ลบงานซ้ำ
        queue = [t for t in queue if t.get("type")!= "update_counter"]

        queue.append(new_task)
        try:
            with open(QUEUE_FILE, 'w') as f:
                json.dump(queue,f , indent=4)
        except Exception as e:
            print(f"Error writing to queue file: {e}")

        
