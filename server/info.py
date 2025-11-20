
import requests

class infoData :


    #ฟังชั่นการดึงข้อมูลผู้ใช้งานออกมาตาม id
    def get(self,id):
         url = 'http://medic.ctnphrae.com/php/api/info.php'

         payload = {
              "id": id
         }

         response = requests.get(url, json=payload)
         infoFormat = response.json()

         if infoFormat['status'] == 'success':
              return infoFormat['data']
         else:
               errormsg = infoFormat['message']
               print(errormsg)
               return False
        
         

    #ฟังชั่นในการอัพเดตข้อมูลผู้ใช้งาน
    def updateData(self,id,device_id,lineid,telegram_key,telegram_id,line_token,group_id):
         
         update_url = 'http://medic.ctnphrae.com/php/api/updateinfo.php'

         newdata = {
              "id": id,
              "device_id": device_id,
              "line_id": lineid,
              "telegram_key": telegram_key,
              "telegram_id": telegram_id,
              "line_token": line_token,
              "group_id": group_id
         }

         response = requests.post(update_url, json=newdata)
         return response.json()

         

