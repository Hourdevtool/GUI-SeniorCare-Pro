# from server.Database import Database
# from mysql.connector import Error
import requests

class infoData :
    # def __init__(self):
    #     self.Database = Database()

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
        
         
# ----------------  lib ตัวทดสอบ-----------------------------
        # try:      
        #     sql = '''SELECT user.firstname_th ,user.lastname_th , user.email ,user.password ,user.line_id 
        #             ,tb_device.device_id,tb_device.telegram_id,tb_device.telegram_key,tb_device.url2 
        #             FROM user 
        #             INNER JOIN tb_device ON user.id = tb_device.id
        #             WHERE user.id= %s'''
        #     self.Database.cursor.execute(sql,(id,))
        #     Data =  self.Database.cursor.fetchone()
        #     #ตรวจสอบว่ามีข้อมูลผู้ใช้งานคนนี้ในระบบหรือไม่
        #     if len(Data) > 0 :
        #         return Data;
        #     else:
        #         return {'status':False , 'message':'ไม่พบข้อมูลในระบบ'};
        # except Error as e :
        #     return {'status':False ,'message':{e}}
# ----------------  lib ตัวทดสอบ-----------------------------
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

         

# -------------------------- lib ตัวทดสอบ -----------------------------------
        # try:
        #     #ทำกาอัพเดตข้อมูล line_id ที่ตาราง  user ก่อน
        #     sql1 = '''UPDATE user SET line_id = %s WHERE id = %s'''
        #     self.Database.cursor.execute(sql1, (lineid, id))
        #     #จากนั้น อัพเดตข้อมูลลงในตาราง tb_device ตัวเครื่อง
        #     sql2 = '''UPDATE tb_device SET telegram_key = %s ,telegram_id= %s, url2 = %s WHERE id = %s AND device_id = %s'''
            
        #     self.Database.cursor.execute(sql2,(telegram_key, telegram_id, url2, id, device_id))    
        #     self.Database.conn.commit();

        #     return {'status':True ,'message':'อัพเดตข้อมูลสำเร็จ'}
        
        # except Error as e :
        #       return {'status':False ,'message':{e}}
# -------------------------- lib ตัวทดสอบ -----------------------------------