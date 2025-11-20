
import requests
class auth :

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


    def login(self,identifier,password):
        user = self.checkuser(identifier)
        if not user:
            return{'status':False,'message':'ขออภัยไม่พบผู้ใช้งานนี้ในระบบ'}
        
        if  not password == user['password']:
               return{'status':False,'message':'ขออภัยรหัสผ่านหรือชื่ผู้ใช้งานไม่ถูกต้อง'}
        
        return {"status": True, "message": "เข้าสู่ระบบสำเร็จ", "user": user}
        
     