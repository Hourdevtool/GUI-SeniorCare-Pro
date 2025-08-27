# from server.Database import Database
import requests
class auth :
    # def __init__(self):
    #     self.database = Database()

    def checkuser(self,identifier): 
        url = 'http://medic.ctnphrae.com/php/api/auth.php'

        user = {
              "identifier": identifier
        }
        responseUser = requests.post(url, json=user)
        jsonformat = responseUser.json()
        if jsonformat['status'] == 'success':
             return jsonformat['data']
        else:
             errormsg = jsonformat['message']
             print(errormsg)
             return False

# ----------------  lib ตัวทดสอบ-----------------------------
        # sql = '''SELECT user.*,tb_device.* 
        #          FROM user 
        #          LEFT JOIN tb_device 
        #          ON user.id = tb_device.id 
        #          WHERE user.email = %s OR user.phone = %s '''
        # self.database.cursor.execute(sql,(identifier,identifier))
        # return self.database.cursor.fetchone();
# ----------------  lib ตัวทดสอบ-----------------------------
    def login(self,identifier,password):
        user = self.checkuser(identifier)
        if not user:
            return{'status':False,'message':'ขออภัยไม่พบผู้ใช้งานนี้ในระบบ'}
        
        if  not password == user['password']:
               return{'status':False,'message':'ขออภัยรหัสผ่านหรือชื่ผู้ใช้งานไม่ถูกต้อง'}
        
        return {"status": True, "message": "เข้าสู่ระบบสำเร็จ", "user": user}
        
     