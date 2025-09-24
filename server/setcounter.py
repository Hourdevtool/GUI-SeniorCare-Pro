import requests
from lib.counter_medic import countermidecine
class SetCounter:

    def update_counter(self, device_id, id, count):
        url = f"http://medic.ctnphrae.com/php/api/updatecounter.php"
        payload = {
            'device_id': device_id,
            'id': id,
            'count': count
        }
        response = requests.post(url, json=payload)
        print(response.json())
        countermidecine(count)
