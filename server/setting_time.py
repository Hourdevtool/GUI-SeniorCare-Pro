
from datetime import datetime
from lib.set_time import format_timedelta 
from datetime import timedelta
import requests
class setting_eat_time:


    #ฟังชั่นบันทึกเวลาลงไปใน device
    def set_time(self,device_id,startDate,endDate):

        set_time_url = 'http://medic.ctnphrae.com/php/api/updateDateDevice.php'

        startDate = datetime.strptime(startDate, "%d/%m/%Y")
        endDate = datetime.strptime(endDate, "%d/%m/%Y")

        format_startDate = startDate.strftime("%Y-%m-%d %H:%M:%S")
        format_endDate = endDate.strftime("%Y-%m-%d %H:%M:%S")
        timepayload = {
            'device_id': device_id,
            'startDate': format_startDate,
            'endDate': format_endDate
        }

        response = requests.post(set_time_url, json=timepayload)
        formatres =  response.json()
        if formatres['status'] == 'success':
            return {'status':True ,'message':formatres['message']}
        else:
            return {'status':False ,'message':formatres['message']}


    def delete_time(self,id):
         delete_time_url = 'http://medic.ctnphrae.com/php/upd.php'

         payload = {
              "UserID": id
          }
         response = requests.post(delete_time_url, json=payload)
         print(response.json())


    #ฟังชั่นการกำหนดเวลาจ่ายยา
    def set_meal(self, device_id, id, meal):

        set_meal_url = 'http://medic.ctnphrae.com/php/api/set_meal.php'

        mealpayload = {
            'device_id': device_id,
            'id': id,
            'meal': meal
        }

        response = requests.post(set_meal_url,json =mealpayload)
        formatresmeal = response.json()

        if formatresmeal['status'] == 'success':
            return {'status': True,'message':formatresmeal['message']}
        else:
            return {'status': False,'message':formatresmeal['message']}

      
    def get_meal(self,device_id,id):
            get_meal_url = 'http://medic.ctnphrae.com/php/api/getsetmidicine.php'

            payload = {
                'device_id': device_id,
                'id': id
            }

            response = requests.get(get_meal_url, json=payload)
            return response.json()

        


    

