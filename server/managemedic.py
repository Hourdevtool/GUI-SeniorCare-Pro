
import requests
class manageMedicData:


    #ฟังชั่นดึงข้อมูลยาออกมาตามผู้ใช้งานเเละเครื่อง
    def getMedicine(self,id,device_id):

         Medicine_url = 'http://medic.ctnphrae.com/php/api/getMedicine.php'

         payload = {
             'id': id,
             'device_id': device_id
         }

         response = requests.get(Medicine_url, json=payload)
         return response.json()

  
    #ฟังชั่นเพิ่มข้อมูลยาใหม่
    def insertMedic(self,id,device_id,medicine):
         

            insert_Medicine_url = 'http://medic.ctnphrae.com/php/api/insertMedicine.php'

            payload = {
                   'id': id,
                   'device_id': device_id,
                   'medicine': medicine
               }
            response = requests.post(insert_Medicine_url, json=payload)
            return response.json()

    # ฟังชั่นลบข้อมูลยา   
    def DeleteMedic(self,medicine_id):
          
          del_Medicine_url = 'http://medic.ctnphrae.com/php/api/deleteMedicine.php'

          payload = {
              'medicine_id': medicine_id
          }

          response = requests.post(del_Medicine_url, json=payload)
          return response.json()

        