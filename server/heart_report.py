from server.Database import Database
from mysql.connector import Error
from server.gemini import Gemini
from datetime import datetime

class heart_report:
    def __init__(self):
        self.Database = Database()
        self.gemini = Gemini()

    def get_heart_data(self, id):
        try:
            sql = 'SELECT * FROM tb_heart WHERE id = %s ORDER BY date DESC'
            self.Database.cursor.execute(sql, (id,))
            Data = self.Database.cursor.fetchall()
            return {'status': True, 'Data': Data}
        except Error as e:
            return {'status': False, 'message': e}

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

        data = result['Data']
        advices = []

        # สร้างคำแนะนำแยกตามแต่ละ heart_id
        for row in data:
            heart_id = row['heart_id']
            prompt = (
                f"ข้อมูลนี้คือค่าความดันโลหิตและชีพจรของคุณในวันที่ {row['date']} : "
                f"ความดันโลหิต {row['systolic_pressure']}/{row['diastolic_pressure']} mmHg, "
                f"ชีพจร {row['pulse_rate']} bpm\n"
                "กรุณาสรุปภาพรวมสุขภาพและให้คำแนะนำในการดูแลตัวเอง"
            )
            advice = self.gemini.Advice(prompt)  # เรียกใช้ AI เพื่อให้คำแนะนำ
            advices.append({'heart_id': heart_id, 'advice': advice})

        return {'status': True, 'advices': advices, 'data': data}
