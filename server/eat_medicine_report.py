
import requests

class eat_medicine_report:

    
    def get_eatmedic(self,id):

        getmedicine_url = 'http://medic.ctnphrae.com/php/api/get_medicinereport.php';

        id_data = {
            'id': id
        }

        response = requests.get(getmedicine_url, json=id_data)

        return response.json()

    def save_history_eat(self,device_id,medicines,id,medicine_get):
        save_url = 'http://medic.ctnphrae.com/php/api/save_historyeat.php'
        
        payload={
            'device_id' : device_id,
            'medicines': medicines,
            'id' :id,
            'medicine_get': medicine_get
        }

        response = requests.post(save_url, json=payload)

        return response.json()