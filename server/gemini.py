from google import genai
from lib.loadenv import API_AI_KEY
import re
import requests

class Gemini:
    def __init__(self):
         #กำหนด apikey
         self.client = genai.Client(api_key=API_AI_KEY)
    #ฟังชั่นคำเเนะนำ
    def save_advice(self,id,Systolic,Diastolic,Pulse):
        
        #ตรวจสอบว่ามีข้อมูลส่งมาหรือไม่
        if not id or not Systolic or not Diastolic or not Pulse:
            return {'status':False,'message':'กรุณากรอกข้อมูลให้ครบถ้วน'}
        
        try:
             systolic = Systolic.strip()
             diastolic = Diastolic.strip()
             pulse = Pulse.strip()
             #ข้อมูลที่จะส่งไปให้ai ตอบคำถาม
             prompt = f"""
                    จากค่าความดันโลหิตและชีพจรต่อไปนี้:
                    - ความดันตัวบน (Systolic): {systolic} mmHg
                    - ความดันตัวล่าง (Diastolic): {diastolic} mmHg
                    - ชีพจร (Pulse): {pulse} ครั้งต่อนาที

                    กรุณาช่วยประเมินสุขภาพโดยแยกเป็นหัวข้อดังนี้:
                    1. การประเมิน: วิเคราะห์แต่ละค่าพร้อมคำอธิบายว่าค่าอยู่ในช่วงปกติหรือไม่
                    2. โดยรวม: วิเคราะห์ภาพรวมของสุขภาพจากค่าที่ได้รับ
                    3. คำแนะนำ: ให้คำแนะนำที่เหมาะสมต่อสุขภาพ เช่น การปรึกษาแพทย์, ปรับพฤติกรรม, การออกกำลังกาย และอาหาร เป็นต้น

                    ตอบกลับด้วยข้อความภาษาไทยแบบเป็นมิตรแต่มีข้อมูลชัดเจนไม่ต้องมีการทักทายเเละข้อความต้องกระชับอ่านง่ายสรุปคำแนะนำอย่างชัดเจน
                    ตัวอย่างข้อความที่ควรจะตอบกลับควรเป็นประมาณนี้
                    ค่าความดันโลหิต 222/222 mmHg และชีพจร 222 ครั้งต่อนาที 
                    ถือว่าอันตรายอย่างยิ่งและต้องได้รับการดูแลทางการแพทย์ฉุกเฉินทันที 
                    ค่าเหล่านี้บ่งชี้ถึงภาวะวิกฤตที่อาจนำไปสู่ภาวะแทรกซ้อนร้ายแรงถึงชีวิตได้การประเมินเบื้องต้น:   
                    ความดันโลหิตสูงมาก: ค่าความดันโลหิตที่สูงเกิน 180/120 mmHg 
                    ถือเป็นภาวะวิกฤตความดันโลหิตสูง (Hypertensive Crisis) 
                    ซึ่งอาจทำให้เกิดความเสียหายต่ออวัยวะสำคัญ เช่น สมอง หัวใจ ไต และหลอดเลือด   
                    ชีพจรเต้นเร็วมาก: อัตราชีพจรปกติขณะพักอยู่ที่ 60-100 ครั้งต่อนาที การที่ชีพจรสูงถึง 222 ครั้งต่อนาที 
                    แสดงว่าหัวใจทำงานหนักเกินไปอย่างมาก ซึ่งอาจเกิดจากภาวะหัวใจเต้นผิดจังหวะ (Arrhythmia) 
                    หรือภาวะอื่น ๆ ที่เป็นอันตรายคำแนะนำ:1.  เ
                    รียกรถพยาบาลทันที: อย่าพยายามแก้ไขสถานการณ์นี้ด้วยตนเอง โทร 1669 หรือเบอร์ฉุกเฉินในพื้นที่ของคุณทันที
                    2.  รอความช่วยเหลืออย่างสงบ: พยายามอยู่ในที่ที่อากาศถ่ายเทสะดวก และรอทีมแพทย์มาช่วยเหลือ
                    3.  ให้ข้อมูลที่ถูกต้อง: เมื่อทีมแพทย์มาถึง ให้แจ้งประวัติทางการแพทย์ ยาที่กำลังรับประทาน 
                    และอาการที่เกิดขึ้นข้อควรระวัง:   
                    อย่ากินยาเอง: อย่าพยายามลดความดันโลหิตหรือลดชีพจรด้วยยาที่คุณมีอยู่ 
                    เพราะอาจทำให้สถานการณ์แย่ลง   
                    อย่าประวิงเวลา: การรักษาที่รวดเร็วเป็นสิ่งสำคัญมากในกรณีฉุกเฉินเช่นนี้ 
                    Disclaimer: ข้อมูลที่ให้ไว้ ณ ที่นี้มีวัตถุประสงค์เพื่อให้ข้อมูลเท่านั้น 
                    และไม่ถือเป็นคำแนะนำทางการแพทย์ หากคุณมีข้อกังวลใดๆ เกี่ยวกับสุขภาพของคุณ โปรดปรึกษาผู้เชี่ยวชาญด้านสุขภาพที่ผ่านการรับรอง
                    """
            #ส่งข้อมูล
             response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents= prompt
            )
            
              #ตัดคำเอาเครื่องหมาย * ออก
             Adivce = re.sub(r'\*+', '',response.text) 
            
             #sql สำหรับบันทึกคำเเนะนำลงไปในฐานข้อมูล

             saveadvice_url = 'http://medic.ctnphrae.com/php/api/saveadvice.php'

             payload = {
                    'systolic_pressure': Systolic,
                    'diastolic_pressure': Diastolic,
                    'pulse_rate': Pulse,
                    'Adivce': Adivce,
                    'id': id
             }

             response = requests.post(saveadvice_url, json=payload)
             responseformat = response.json()

             if responseformat['status']:
               return  {'status':True,'Advice':Adivce,'message':responseformat['message']} 
             else:
                return  {'status':False,'message':responseformat['message']}

        except:
            return {'status':False,'message':'เกิดข้อผิดพลาดในการประมวลผลคำ'}    

    def Advice(self,prompts):
        try:
        
            #ส่งข้อมูล
             response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents= prompts
            )
            
              #ตัดคำเอาเครื่องหมาย * ออก
             Advice = re.sub(r'\*+', '',response.text) 


             return Advice

        except:
            return {'status':False,'message':'เกิดข้อผิดพลาดในการประมวลผลคำ'}    