from server.Database import Database

class auth :
    def __init__(self):
        self.database = Database()

    def checkuser(self,identifier):
        sql = '''SELECT user.*,tb_device.* 
                 FROM user 
                 LEFT JOIN tb_device 
                 ON user.id = tb_device.id 
                 WHERE user.email = %s OR user.phone = %s '''
        self.database.cursor.execute(sql,(identifier,identifier))
        return self.database.cursor.fetchone();

    def login(self,identifier,password):
        user = self.checkuser(identifier)

        if not user:
            return{'status':False,'message':'ขออภัยไม่พบผู้ใช้งานนี้ในระบบ'}
        
        if  not password == user['password']:
               return{'status':False,'message':'ขออภัยรหัสผ่านไม่ถูกต้อง'}
        
        return {"status": True, "message": "เข้าสู่ระบบสำเร็จ", "user": user}
        
     