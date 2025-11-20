
from server.gemini import Gemini
from datetime import datetime
import requests
class heart_report:
    def __init__(self):

        self.gemini = Gemini()

    def get_heart_data(self, id):

        heart_report_url = 'http://medic.ctnphrae.com/php/api/heart_report.php'

        payload_id = {
            'id': id
        }

        response = requests.get(heart_report_url, json=payload_id)

        return response.json()
    
    def get_heart_advice(self,heart_id):

        heart_advice_url = 'http://medic.ctnphrae.com/php/api/get_advice.php'

        payload_heard_id = {
            'heart_id': heart_id
        }

        response = requests.get(heart_advice_url, json=payload_heard_id)

        result = response.json()
        if result['status']:
            return result['message']
        else:
            return result['message']
        
    def format_heart_data_for_ai(self, data):
        lines = []
        for row in data:
            systolic = row['systolic_pressure']
            diastolic = row['diastolic_pressure']
            pulse = row['pulse_rate']
            try:
                date = row['date'].strftime("%Y-%m-%d เวลา %H:%M:%S")
            except Exception:
                date = str(row['date'])
            lines.append(f"วันที่ {date} : ความดันโลหิต {systolic}/{diastolic} mmHg, ชีพจร {pulse} bpm")
        return "\n".join(lines)

    def generate_advice(self, id):
        result = self.get_heart_data(id)
        if not result['status']:
            return result

        data = result['data']
        formatted_data = self.format_heart_data_for_ai(data)

         # สร้าง prompt ให้ AI วิเคราะห์ข้อมูลภาพรวม
        prompt = (
                   f"นี่คือข้อมูลค่าความดันโลหิตและชีพจรของคุณ:\n\n{formatted_data}\n\n"
                    "กรุณาสรุปภาพรวมสุขภาพจากข้อมูลทั้งหมด และให้คำแนะนำในการดูแลตัวเอง "
                    "เช่น การพบแพทย์ การปรับเปลี่ยนพฤติกรรมการใช้ชีวิต และการติดตามผล"
         )

        # เรียกใช้ AI ให้วิเคราะห์ภาพรวม
        advice = self.gemini.Advice(prompt)

        return {
        'status': True,
        'advices': advice,  # สรุปภาพรวมเพียงชุดเดียว
        'data': data
    }
