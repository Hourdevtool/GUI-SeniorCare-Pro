from server.Database import Database
from mysql.connector import Error

class manageMedicData:
    def __init__(self):
         self.Database = Database()

    #ฟังชั่นดึงข้อมูลยาออกมาตามผู้ใช้งานเเละเครื่อง
    def getMedicine(self,id,device_id):
         try:
               #sqlสำหรับดึงข้อมูลยาออกมา
              sql = ''' SELECT  medicine_id ,medicine_name FROM tb_medicine WHERE id = %s AND device_id = %s'''
              self.Database.cursor.execute(sql,(id,device_id))  
              Data =  self.Database.cursor.fetchall()   
 
              if len(Data) > 0:
                    return {'status':True,'Data':Data}
              else:
                   return {'status':False ,'message':'ไม่พบข้อมูลในขณะนี้'}         
         except Error as e:
              return {'status':False ,'message':{e}}  
    #ฟังชั่นเพิ่มข้อมูลยาใหม่
    def insertMedic(self,id,device_id,medicine):
           
           try:
                #sqlสำหรับเพิ่มข้อมูลยาใหม่พร้อมกันหลายตัว
                sql = 'INSERT INTO tb_medicine (id,device_id,medicine_name,medicine_detail,all_count) VALUES (%s,%s,%s,%s,%s)'
                self.Database.cursor.executemany(sql,[(id,device_id,med,'ก่อนอาหาร',0)for med in medicine]) #med คือการ lop ยาที่เข้าเป็น array ออกมาเพื่อinsert เข้าไปทีละตัว
                self.Database.conn.commit()

                return {'status':True ,'message':'เพิ่มข้อมูลสำเร็จ'}
           except Error as e:
                return {'status':False ,'message':{e}}  
    # ฟังชั่นลบข้อมูลยา   
    def DeleteMedic(self,medicine_id):
           try:
                #ลบข้อมูลยาตาม id
                sql = 'DELETE FROM tb_medicine WHERE medicine_id = %s'
                self.Database.cursor.execute(sql,(medicine_id,))
                self.Database.conn.commit()

                return {'status':True ,'message':'ลบข้อมูลสำเร็จ'}
           except Error as e:
                return {'status':False ,'message':{e}}