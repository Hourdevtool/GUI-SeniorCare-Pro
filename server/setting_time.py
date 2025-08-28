
# from server.Database import Database
# from mysql.connector import Error
from datetime import datetime
from lib.set_time import format_timedelta 
from datetime import timedelta
import requests
class setting_eat_time:
    # def __init__(self):
    #     self.Database = Database()

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




        # --------------------------lib ทดสอบ ------------------------------------
        # try:
        #     #ตรวจสอบว่าเครื่องมีข้อมูลอยู่ในระบบหรือไม่
        #     check_device = 'SELECT device_id FROM tb_device WHERE device_id = %s'  
        #     self.Database.cursor.execute(check_device,(device_id,))
        #     check_device = self.Database.cursor.fetchone()

        
        #     if check_device is None:
        #        return {'status':False ,'message':'ไม่พบข้อมูลเครื่องในระบบ'}
             
        #     startDate = datetime.strptime(startDate, "%d/%m/%Y")
        #     endDate = datetime.strptime(endDate, "%d/%m/%Y")

            
        #     format_startDate = startDate.strftime("%Y-%m-%d %H:%M:%S")
        #     format_endDate = endDate.strftime("%Y-%m-%d %H:%M:%S")

        #     #ถ้ามีให้ทำการอัพเดตข้อมูลเข้าไป
        #     sql = '''UPDATE tb_device SET startDate = %s, endDate = %s WHERE device_id = %s'''
        #     self.Database.cursor.execute(sql,(format_startDate,format_endDate,device_id))
        #     self.Database.conn.commit()
            
        #     return {'status':True ,'message':'ตั้งค่าเวลาสำเร็จ'}
        # except Error as e:
        #     return {'status':False ,'message':{e}} 
        # --------------------------lib ทดสอบ ------------------------------------
        
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

         # --------------------------lib ทดสอบ ------------------------------------
        # try:
        #     #loop item ทั้งหมดที่ส่งเข้ามา
        #     for meal_name, info in meal.items():
        #         time_set = info['time']
        #         time_set += ':00' 
        #         medications = info['medications']

        #         # เตรียมยาไม่เกิน 4 ตัว
        #         meds = medications + [None] * (4 - len(medications))  # เติม None ถ้ายามีน้อยกว่า 4
        #         med1, med2, med3, med4 = meds[:4]

        #         # Mapping ชื่อตารางและคอลัมน์
        #         if meal_name == 'เช้า':
        #             table = 'tb_data_bf'
        #             id_col = 'bf_id'
        #             time = 'time_bf'
        #         elif meal_name == 'กลางวัน':
        #             table = 'tb_data_lunch'
        #             id_col = 'lunch_id'
        #             time = 'time_lunch'
        #         elif meal_name == 'เย็น':
        #             table = 'tb_data_dn'
        #             id_col = 'dn_id'
        #             time = 'time_dn'
        #         elif meal_name == 'ก่อนนอน':
        #             table = 'tb_data_bb'
        #             id_col = 'bb_id'
        #             time = 'time_bb'
        #         else:
        #             return {'status': False, 'message': f'ชื่อมื้อไม่ถูกต้อง: {meal_name}'}

        #         # เช็คว่ามี record นี้อยู่หรือไม่
        #         sql_check = f'''SELECT {id_col} FROM {table} WHERE device_id = %s AND id = %s'''
        #         self.Database.cursor.execute(sql_check, (device_id, id))
        #         result = self.Database.cursor.fetchone()
               
        #         if result:   
        #             sql_update = f'''
        #                 UPDATE {table}
        #                 SET {time} = %s,
        #                     medicine_id = %s,
        #                     medicine_id2 = %s,
        #                     medicine_id3 = %s,
        #                     medicine_id4 = %s,
        #                     status_alert = '',
        #                     meal_count = 0
        #                 WHERE {id_col} = %s
        #             '''
        #             self.Database.cursor.execute(sql_update, (time_set, med1, med2, med3, med4, result[id_col]))
        #         else:
        #             # ถ้ายังไม่มี → INSERT ใหม่
        #             sql_insert = f'''
        #                 INSERT INTO {table} (device_id,id,{time}, medicine_id, medicine_id2, medicine_id3, medicine_id4,status_alert,meal_count)
        #                 VALUES (%s,%s,%s, %s, %s, %s, %s,%s,%s)
        #             '''
        #             self.Database.cursor.execute(sql_insert,(device_id,id,time_set, med1, med2, med3, med4,'',0))

        #     self.Database.conn.commit()
        #     return {'status': True, 'message': 'บันทึกข้อมูลมื้ออาหารสำเร็จ'}
        # except Error as e:
        #     return {'status': False, 'message': str(e)}
          # --------------------------lib ทดสอบ ------------------------------------
    def get_meal(self,device_id,id):
            get_meal_url = 'http://medic.ctnphrae.com/php/api/getsetmidicine.php'

            payload = {
                'device_id': device_id,
                'id': id
            }

            response = requests.get(get_meal_url, json=payload)
            return response.json()

        # --------------------------lib ทดสอบ ------------------------------------
        # try:
        #     sql = ''' SELECT 
        #         d.time,
        #         m1.medicine_name AS medicine_1,
        #         m2.medicine_name AS medicine_2,
        #         m3.medicine_name AS medicine_3,
        #         m4.medicine_name AS medicine_4,
        #         d.source
        #     FROM (
        #         SELECT device_id, id, time_bb AS time, medicine_id, medicine_id2, medicine_id3, medicine_id4, 'bb' AS source FROM tb_data_bb
        #         UNION ALL
        #         SELECT device_id, id, time_bf AS time, medicine_id, medicine_id2, medicine_id3, medicine_id4, 'bf' AS source FROM tb_data_bf
        #         UNION ALL
        #         SELECT device_id, id, time_dn AS time, medicine_id, medicine_id2, medicine_id3, medicine_id4, 'dn' AS source FROM tb_data_dn
        #         UNION ALL
        #         SELECT device_id, id, time_lunch AS time, medicine_id, medicine_id2, medicine_id3, medicine_id4, 'lunch' AS source FROM tb_data_lunch
        #     ) AS d
        #     LEFT JOIN tb_medicine m1 ON d.medicine_id = m1.medicine_id
        #     LEFT JOIN tb_medicine m2 ON d.medicine_id2 = m2.medicine_id
        #     LEFT JOIN tb_medicine m3 ON d.medicine_id3 = m3.medicine_id
        #     LEFT JOIN tb_medicine m4 ON d.medicine_id4 = m4.medicine_id
        #     WHERE d.device_id = %s AND d.id = %s;'''
            
            
        #     self.Database.cursor.execute(sql,(device_id,id))
        #     result = self.Database.cursor.fetchall()
        #     for row in result:
        #         if isinstance(row['time'], timedelta):
        #             row['time'] = format_timedelta(row['time'])

        #     return{'status': True, 'data': result}
        # except Error as e:
        #      return {'status': False, 'message': str(e)}
        # --------------------------lib ทดสอบ ------------------------------------


    

