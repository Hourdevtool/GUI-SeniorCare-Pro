
# server Documentation

เอกสารการปรับเเต่งใช้งาน module ฝั่งserver


## สิ่งที่จะต้องติดตั้งก่อนเริ่มใช้งาน✔

mysql-connector

```bash
 pip install mysql-connector-python
```

สำหรับ geminiai

```bash
  pip install -q -U google-genai
```

module สำหรับเเปลงข้อมความเป็นเสียง

```bash
  pip install gTTS
```

module สำหรับการเล่นเสียง(ติดตั้งเมื่อรันบน window)

```bash
  pip install pygame
```


## เริ่มต้นใช้งาน

ในfolder server จะมีไฟล์ที่ใช้งานได้ดังนี้:

- ``` Database.py ``` ใช้สำหรับจัดการฐานข้อมูล
- ``` auth.py ``` ใช้สำหรับการตรวจสอบการเข้าสู่ระบบ
- ``` gemini.py ``` เป็น module ที่ใช้ให้คำเเนะนำโดยai
- ``` setting_time.py ``` ใช้สำหรับการตั้งค่าเวลากำหนดเวลาจ่ายยาต่างๆ
- ``` managemedic.py ``` ใช้จัดการการเพิ่มชื่อยาลบข้อมูลยา
- ``` info.py ``` ใช้เเสดงผลข้อมูลผ้ใช้อัพเดตข้อมูลตผู้ใช้งานที่อนุญาติให้ผู้ใช้งานอัพเดตได้เอง




## Database.py
#### ไฟล์นี้ทำหน้าที่ในการเชื่อมต่อฐานข้อมูลเป็นหลักสามารถปรับเปลี่ยน ฐานข้อมูลไปเชื่อมตัวอื่นได้ตาม comment ดังภาพ🔴
![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358349153088045157/image.png?ex=67f384bb&is=67f2333b&hm=5bb1db7b1e372df319061f4b7c495c2642062d2cd1e704fc0180dbf16df22f5e&)

#### การเรียกใช้งาน

```
   from server.Database import Database

     def __init__(self):
        self.database = Database()
         
         บังคับเชื่อมต่อฐานข้อมูลเมื่อมีการโหลด class นั้นๆ
```





## auth.py

#### ไฟล์นี้ทำหน้าที่ตรวจสอบเเละดึงข้อมูลผู้ใช้จากฐานข้อมูลออกมาโดยจะมี logic สำคัญดังภาพในกรณีที่ต้องการปรับเปรี่ยนการดึงข้อมูลสามารถทำได้ในฟังชั่น checkuser🔴

#### 👇ปรับตรงนี้
``` 
sql = '''SELECT user.*,tb_device.device_id 
                 FROM user 
                 LEFT JOIN tb_device 
                 ON user.id = tb_device.id 
                 WHERE user.email = %s OR user.phone = %s ''' 
```
![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358353190843715624/image.png?ex=67f3887d&is=67f236fd&hm=b648ccada1cb40420be12a6cced4ae7fbf39089e514d24f8efd752e28707de65&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น save_and_go_home ของ  class login โดยเริ่มทำงานที่บรรทัด 75 ในไฟล์ main.py

```


  from server.auth import auth   #import เข้ามาทำงานก่อน

  auth = auth() #เรียกใช้งาน class

#calss นี้จะทำงานในฟังชั่น save_and_go_home ของ  class login ดังนี้ 
def save_and_go_home():
            # logic ฝั่ง server
            if len(self.username.get().strip()) == 0 and len(self.password.get().                  strip()== 0 :
                           print('กรุณากรอกข้อมูลให้ถูกต้องตามแบบฟอร์ม')
                           return
             
            result = auth.login(self.username.get(),self.password.get())
            if result['status'] :
               self.controller.user = result['user']
               with open('user_data.json','w',encoding='utf-8') as f:
                   json.dump(result['user'], f,ensure_ascii=False, indent=4,default=default_serializer)
               print(result['message'])
               controller.show_frame(Wificonnect)
            else:
                print(result['message'])
      
```

#### -สิ่งที่ต้องการ

```http
   auth.login(username,password)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `username` | `string` | **Required**. email  หรือ เบอร์โทรศัพท์ อย่างใดอย่างหนึ่ง |
| `password` | `string` | **Required**. รหัสผ่าน |








## info.py

#### ไฟล์นี้ทำหน้าที่ดึงข้อมูลของผู้ใช้งานออกมาเเละทำการอัพเดตข้อมูลที่มีการอนุญาติให้มีการอัพเดตข้อมูลได้🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358358395886764124/image.png?ex=67f38d56&is=67f23bd6&hm=22f055caef476039dfac5283ed2d066465af3bab1db7eac2687d3523813f9d19&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น on_show ของ  class info โดยเริ่มทำงานที่บรรทัด ``` 966 ``` ในไฟล์ main.py เเละในฟังชั่น save_data บรรทัดที่ ``` 1077 ```

```


  from server.info import infoData   #import เข้ามาทำงานก่อน

  manageData = infoData() #เรียกใช้งาน class

def on_show(self):
        print("info is now visible")
        self.userid = self.controller.user['id']
        self.result = manageData.get(self.userid)

 def save_data():
            success = manageData.updateData(self.userid,self.result['device_id'],self.entry_line_id.get(),self.entry_telegram_token.get(),self.entry_telegram_id.get(),self.entry_telegram_group.get())
            print(success)
            if success['status']:
                print(success['message'])
                controller.show_frame(HomePage)
            else:
                print(success['message'])
      
```

#### -สิ่งที่ต้องการ

```
    manageData.get(userid)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ผู้ใช้งาน |

ตัวอย่างข้อมูลที่ดึงออกมา
```
{'firstname_th': 'ทดสอบ', 
'lastname_th': 'ทดสอบ', 
'email': 'test@gmail.com', 
'password': 'pop', 
'line_id': None,
 'device_id': 3, 
 'telegram_id': '', 
 'telegram_key': '', 
 'url2': 'http://medic.ctnphrae.com/'
 }
```


#### -สิ่งที่ต้องการ

```
   manageData.updateData(userid,device_id,line_id,telegram_token,telegram_id,telegram_group)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ผู้ใช้งาน |
| `device_id` | `Int` | **Required** id เครื่อง |
| `line_id` | `string` |  id_line |
| `telegram_token` | `string` |telegram_token |
| `telegram_id` | `string` | telegram_id |
| `telegram_group` | `string` | telegram_group |








## managemedic.py

#### ไฟล์นี้ทำหน้าที่ดึงข้อมูลตัวยาออกมาเเละเพิ่มข้อมูลยาใหม่เข้าไปเเละลบข้อมูลยาตัวนั้นออก 🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358363603547459654/image.png?ex=67f39230&is=67f240b0&hm=b302c9423e0aa3b5fc7089565ca42aad1621e624339932c7bd392947890a8428&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น load_medications ของ  ``` class Frame2 ``` โดยเริ่มทำงานที่บรรทัด ``` 247 ``` ในไฟล์ main.py เเละในฟังชั่น save_medications บรรทัดที่ ``` 500 ``` ของ ``` class add_Frame ``` เเละในฟังชั่น delete_medication บรรทัดที่ ``` 256 ``` ของ ``` class Frame2 ```

```


 from server.managemedic import manageMedicData   #import เข้ามาทำงานก่อน

  manageMedic = manageMedicData() #เรียกใช้งาน class

def load_medications(self):
            # logic ฝั่ง server
            medicine_data = manageMedic.getMedicine(self.controller.user['id'],self.      controller.user['device_id'])
            if  medicine_data['status']:
                  self.medications =  medicine_data['Data']
            else:
                 self.medications = []
                 print(medicine_data['message'])

 def save_medications():
            new_meds = []
            first_med = med_frame.entry_med_name.get()
            if first_med:
                new_meds.append(first_med)
            for entry, _ in med_frame.med_entries:
                med_name = entry.get()
                if med_name and med_name != first_med:
                    new_meds.append(med_name)
            # logic ฝั่ง server
            if  not len(new_meds) == 0 :
                insert_new_medic = manageMedic.insertMedic(self.controller.user['id'],self.controller.user['device_id'],new_meds)
                if insert_new_medic['status']:
                    print(insert_new_medic['message'])
                else:      
                    print(insert_new_medic['message'])
            else:
                print('ไม่พบข้อมูลยาใหม่กรุณากรอกข้อมูลยาก่อนกดบันทึก')   


def delete_medication(self,medicine_id):
        print(medicine_id)
        confirm = messagebox.askyesno("ยืนยัน", "คุณต้องการลบยานี้หรือไม่?")
        if confirm:
            # logic ฝั่ง server
            delete_medic = manageMedic.DeleteMedic(medicine_id)
            if delete_medic['status']:
                self.medications = [med for med in self.medications if med['medicine_id'] != medicine_id]
                messagebox.showinfo("สำเร็จ",delete_medic['message'])
            else:
                messagebox.showerror("ล้มเหลว",delete_medic['message'])   
            self.refresh_medications()
      
```

#### -สิ่งที่ต้องการ

```
    manageMedic.getMedicine(userid,device_id)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ผู้ใช้งาน |
| `device_id` | `Int` | **Required** id ของตัวเครื่อง |

ตัวอย่างข้อมูลที่ดึงออกมา
```
[
   {'medicine_id': 86, 'medicine_name': 'ยาละลายลิ่มเลือด'}
]

```

#### -สิ่งที่ต้องการ

```
    manageMedic.insertMedic(userid,device_id,new_meds)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ของผู้ใช้งาน |
| `device_id` | `Int` | **Required** id ของตัวเครื่อง |
| `new_meds` | `Array` | **Required**  ยาใหม่ที่ผู้ช้งานมีการเพิ่ม |



#### -สิ่งที่ต้องการ

```
    manageMedic.DeleteMedic(medicine_id)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `medicine_id` | `Int` | **Required** id ของตัวยา |










## คำสังรันในการทดสอบ 


```bash
   python main.py
```



## gemini.py

#### ไฟล์นี้ทำหน้าที่ส่งข้อมูลที่ผู้ใข้งานมีการกรอกเข้ามาเพื่อทำไปเเสดงผลเป็นข้อมความ🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358455400013496513/image.png?ex=67f3e7ae&is=67f2962e&hm=8b3e88dccada09791b146fcf13694fa49fd1f1bd209375d09bbd1fd14cc29555&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น save_and_go_home ของ  class Frame4 โดยเริ่มทำงานที่บรรทัด ``` 412 ``` ในไฟล์ main.py 
```


  from server.gemini import Gemini   #import เข้ามาทำงานก่อน

 ai = Gemini()  #เรียกใช้งาน class

def save_and_go_home():
            print(f"Saved: Systolic={self.systolic_var.get()}, Diastolic={self.diastolic_var.get()}, Pulse={self.pulse_var.get()}")
            if len(self.systolic_var.get().strip())== 0 and len(self.diastolic_var.get().strip()) == 0 and len(self.pulse_var.get().strip()) == 0:
                print('กรุณากรอกข้อมูลให้ครบถ้วน')
                return
            ai_advice = ai.save_advice(self.controller.user['id'],self.systolic_var.get(),self.diastolic_var.get(),self.pulse_var.get())
            if ai_advice['status']:
                 self.controller.advice = ai_advice['Advice']
                 print(ai_advice['message'])
                 controller.show_frame(AIgen)
            else:
                print(ai_advice['message'])
      
```

#### -สิ่งที่ต้องการ

```
    ai.save_advice(userid,systolic,diastolic,pulse)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ผู้ใช้งาน |
| `systolic` | `Int` | **Required** ค่าความดันสูง |
| `diastolic` | `Int` | **Required** ค่าความดันต่ำ |
| `pulse` | `Int` | **Required** ค่าชีพจร |

ตัวอย่างข้อมูลที่ดึงออกมา
```
{'status': True, 
'Advice': 'ค่าความดันโลหิต 150/100 mmHg และชีพจร 120 ครั้งต่อนาที ถือว่าสูงกว่าปกติและควรได้รับการดูแล\n\n1. การประเมิน:\n\n   ความดันตัวบน (Systolic): 150 mmHg จัดอยู่ในระดับความดันโลหิตสูงระยะที่ 1 (Stage 1 Hypertension) ซึ่งสูงกว่าค่าปกติ (น้
อยกว่า 120 mmHg) บ่งชี้ว่าหัวใจต้องทำงานหนักขึ้นในการสูบฉีดเลือด\n   ความดันตัวล่าง (Diastolic): 100 mmHg จัดอยู่ในระดับความดันโลหิตสูงระยะที่ 2 (Stage 2 Hypertension) ซึ่งสูงกว่าค่าปกติ (น้อยกว่า 80 mmHg) แสดงถึงแรงดันในหลอดเลือดที่สูงเกินไปขณะหัวใจคลายตัว\n   
ชีพจร (Pulse): 120 ครั้งต่อนาที สูงกว่าค่าปกติ (60-100 ครั้งต่อนาที) บ่งชี้ว่าหัวใจเต้นเร็วกว่าปกติ ซึ่งอาจเกิดจากความเครียด, การออกกำลังกาย, หรือปัญหาสุขภาพอื่นๆ\n\n2. โดยรวม:\n\nค่าความดันโลหิตที่สูงทั้งค่าตัวบนและตัวล่าง ร่วมกับชีพจรที่เต้นเร็ว บ่งชี้ถึงภาวะท
ี่ควรได้รับการดูแลและปรับปรุงเพื่อลดความเสี่ยงต่อปัญหาสุขภาพในระยะยาว เช่น โรคหัวใจ, หลอดเลือดสมอง, และไต\n\n3. คำแนะนำ:\n\n   ปรึกษาแพทย์: ควรพบแพทย์เพื่อตรวจวินิจฉัยหาสาเหตุของความดันโลหิตสูงและชีพจรเต้นเร็ว รวมถึงรับคำแนะนำในการรักษาที่เหมาะสม\n   ปรับพฤติกรร
ม:\n       อาหาร: ลดการบริโภคโซเดียม (เกลือ), อาหารแปรรูป, และไขมันอิ่มตัว เพิ่มการบริโภคผัก, ผลไม้, และธัญพืชไม่ขัดสี\n       ออกกำลังกาย: ออกกำลังกายแบบแอโรบิกอย่างสม่ำเสมอ เช่น เดินเร็ว, วิ่ง, ว่ายน้ำ อย่างน้อย 150 นาทีต่อสัปดาห์\n       ลดน้ำหนัก: หากมีน้ำหน
ักเกิน ควรลดน้ำหนักให้อยู่ในเกณฑ์ที่เหมาะสม\n       จัดการความเครียด: ฝึกเทคนิคการผ่อนคลาย เช่น การทำสมาธิ, โยคะ, หรือการหายใจลึกๆ\n       งดสูบบุหรี่และจำกัดการดื่มแอลกอฮอล์: บุหรี่และแอลกอฮอล์สามารถเพิ่มความดันโลหิตและอัตราการเต้นของหัวใจได้\n   ติดตามความดันโ
ลหิตและชีพจร: วัดความดันโลหิตและชีพจรเป็นประจำเพื่อติดตามผลการรักษาและการปรับพฤติกรรม\n',
'message': ''
}
```

#### -สิ่งที่ต้องการ

```
    ai.advice(prompts)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `prompts` | `String` | **Required** คำถามที่ใช้ถาม ai |




 








## setting_time.py

#### ไฟล์นี้ทำหน้าที่จัดการการการตั่งค่ากำหนดเวลาจ่ายา🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358379548634386462/a.png?ex=67f3a109&is=67f24f89&hm=33f5d39724091fc4a98b663b41e01a5aeb90cca3f55e272e12a1926ea2aa5207&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น save_and_go_to_frame1 ของ  class MedicationApp โดยเริ่มทำงานที่บรรทัด ``` 922 ``` ในไฟล์ main.py  เเละเรียกใช้ที่ฟังชั่น save_and_go_to_frame1 ของ class  MedicationScheduleFrame โดยเริ่มทำงานที่บรรทัด ``` 1123 ```
```


  from server.setting_time import setting_eat_time   #import เข้ามาทำงานก่อน

set_dispensing_time = setting_eat_time() #เรียกใช้งาน class

def save_and_go_to_frame1(self):
        meal_data = {}
        
        # ใช้ entry_frames เป็นหลักในการวนลูป
        for meal_name, entry_frame in self.entry_frames.items():
            # ตรวจสอบว่ามีข้อมูลเวลาหรือไม่
            if meal_name not in self.time_entries or meal_name not in self.time_selects:
                continue
                
            # ดึงค่าจริงจาก ComboBox ช่วงเวลา
            time_period = self.time_selects[meal_name].get()
            
            # ดึงค่าเวลาจริง
            time_value = self.time_entries[meal_name].get()
            
            # รวบรวม ID ยา
            med_ids = []
            if meal_name in self.med_combos:
                for med_combo in self.med_combos[meal_name]:
                    med_name = med_combo.get()
                    if med_name in self.medicine_map and med_name != "เลือกยา":
                        med_ids.append(self.medicine_map[med_name])
            
            # บันทึกข้อมูลโดยใช้ช่วงเวลาจริงที่ผู้ใช้เลือก
            meal_data[time_period] = {
                "time": time_value if time_value else "00:00",
                "medications": med_ids
            }
   
        print("บันทึกข้อมูลสำเร็จ! ข้อมูลที่บันทึก:", meal_data)

        insert_meal = set_dispensing_time.set_meal(self.controller.user['device_id'],self.controller.user['id'],meal_data)
        if( insert_meal['status']):
            print(insert_meal['message'])
            self.controller.show_frame(HomePage)
        else:
            print(insert_meal['message'])


  def save_and_go_to_frame1():
                  if(date_entry.get() == "" and end_entry.get() == ""):
                      print('กรุณากำหนดวันที่เริ่มจ่ายยา')
                      return

                  setting_time = set_dispensing_time.set_time(self.controller.user['device_id'], date_entry.get(), end_entry.get())
                  if setting_time['status']:
                      print(setting_time['message'])
                      controller.show_frame(MedicationApp)
                  else:
                      print(setting_time['message'])
      
```

#### -สิ่งที่ต้องการ

```
    set_dispensing_time.set_time(device_id, start_date, end_date)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `device_id` | `Int` | **Required** id ของเครื่อง |
| `start_date` | `Date` | **Required** วันที่เริ่มจ่ายยา |
| `end_date` | `Date` | **Required** วันที่สิ้นสุดจ่ายยา |

#### -สิ่งที่ต้องการ

```
   set_dispensing_time.set_meal(device_id,userid,meal_data)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `device_id` | `Int` | **Required** id ของเครื่อง |
| `userid` | `Int` | **Required** id ของผู้ใช้งาน |
| `meal_data` | `Array` | **Required**  มื้อที่ผู้ใช้งานกำหนด |


#### -สิ่งที่ต้องการ ❌ ยังไม่มีการเรียกใช้งานเเต่ทำงานได้เเล้ว

```
   set_dispensing_time.get(device_id,userid)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `device_id` | `Int` | **Required** id ของเครื่อง |
| `userid` | `Int` | **Required** id ของผู้ใช้งาน |

ตัวอย่างข้อมูลที่ดึงออกมา
```
[
    {
        'time': '22:00:00', 
        'medicine_1': 'พาราเซตามอล', 
        'medicine_2': 'ยารักษาโรคความดันโลหิตสูง', 
        'medicine_3': 'ยารักษาโรคเบาหวาน', 
        'medicine_4': 'ยาลดไขมันในเลือด', 
        'source': 'bb'
    }, 
    {
        'time': '10:00:00', 
        'medicine_1': 'พาราเซตามอล', 
        'medicine_2': None, 'medicine_3': None, 'medicine_4': None, 'source': 'bf'
    }, 
    {
        'time': '18:00:00', 
        'medicine_1': 'พาราเซตามอล', 
        'medicine_2': 'ยารักษาโรคความดันโลหิตสูง', 
        'medicine_3': 'ยารักษาโรคเบาหวาน', 
        'medicine_4': None, 
        'source': 'dn'
    }, 
    {
        'time': '14:00:00', 
        'medicine_1': 'ยารักษาโรคเบาหวาน', 
        'medicine_2': 'ยาลดไขมันในเลือด', 
        'medicine_3': None, 
        'medicine_4': None, 
        'source': 'lunch'
    }
]


```


 








## heart_report.py

#### ไฟล์นี้ทำหน้าที่ในการส่งข้อมูลออกมาเเละมีคำเเนะนำจาก ai 🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358450631899218121/image.png?ex=67f3e33d&is=67f291bd&hm=08bf8bfa2fdbdc57595a10e52791aaebd03e66d04312ab2db19cec77bc26549b&)

#### การเรียกใช้งาน class นี้จะทำงานในฟังชั่น on_show ของ  class Report2 โดยเริ่มทำงานที่บรรทัด ``` 1334 ``` ในไฟล์ main.py 
```


  from server.heart_report import heart_report   #import เข้ามาทำงานก่อน

 Heart_report = heart_report()  #เรียกใช้งาน class

def on_show(self):
        print("Report2 is now visible")
        result = Heart_report.generate_advice(self.controller.user['id'])
        if result['status']:
            print(result)
        else:
            print("เกิดข้อผิดพลาด:", result['message'])
      
```

#### -สิ่งที่ต้องการ

```
    Heart_report.generate_advice(userid)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ผู้ใช้งาน |


ตัวอย่างข้อมูลที่ดึงออกมา
```
{
    'status': True, 
    'Advice': 'จากข้อมูลที่ให้มา สรุปภาพรวมสุขภาพและให้คำแนะนำในการดูแลตัวเองได้ดังนี้ครับ\n\nภาพรวมสุขภาพ:\n\n   ความดันโลหิตสูง: ค่าความดันโลหิตที่วัดได้ทั้ง 3 ครั้ง สูงกว่าค่าปกติ โดยเฉพาะอย่างยิ่งค่าที่วัดได้ในเวลา 07:02:21 ซึ่งสูงมาก (180/120 m
mHg) ถือเป็นภาวะวิกฤตความดันโลหิตสูงที่ต้องได้รับการดูแลจากแพทย์อย่างเร่งด่วน\n   ชีพจรค่อนข้างเร็ว: ชีพจรอยู่ในช่วง 100-120 bpm ซึ่งค่อนข้างเร็ว ค่าปกติของชีพจรขณะพักคือ 60-100 bpm\n   ความผันผวนของความดันโลหิต: ความดันโลหิตมีการเปลี่ยนแปลงอย่างมากในแต่ละช่วงเว
ลาของวัน ซึ่งอาจบ่งบอกถึงปัญหาในการควบคุมความดันโลหิต\n\nคำแนะนำในการดูแลตัวเอง:\n\nคำแนะนำที่สำคัญที่สุดคือ:\n\n1.  ปรึกษาแพทย์โดยด่วน: เนื่องจากค่าความดันโลหิตสูงมากและมีความผันผวน ควรปรึกษาแพทย์เพื่อวินิจฉัยหาสาเหตุและรับการรักษาที่เหมาะสมโดยเร็วที่สุด การปล่
อยทิ้งไว้อาจนำไปสู่ภาวะแทรกซ้อนที่รุนแรง เช่น โรคหัวใจและหลอดเลือดสมอง\n\nคำแนะนำเพิ่มเติม (หลังจากปรึกษาแพทย์และปฏิบัติตามคำแนะนำของแพทย์แล้ว):\n\n   ติดตามความดันโลหิตอย่างสม่ำเสมอ: วัดความดันโลหิตเป็นประจำตามคำแนะนำของแพทย์ และจดบันทึกผล เพื่อติดตามการเปลี่ยน
แปลงและประสิทธิภาพของการรักษา\n   ปรับเปลี่ยนพฤติกรรมการใช้ชีวิต:\n       ควบคุมอาหาร: ลดปริมาณโซเดียม (เกลือ) ในอาหาร หลีกเลี่ยงอาหารแปรรูป อาหารสำเร็จรูป และอาหารที่มีไขมันสูง เน้นการรับประทานผัก ผลไม้ ธัญพืชไม่ขัดสี และโปรตีนไม่ติดมัน\n       ออกกำลังกาย: ออก
กำลังกายแบบแอโรบิกอย่างสม่ำเสมอ เช่น เดินเร็ว วิ่งเหยาะๆ ว่ายน้ำ หรือปั่นจักรยาน อย่างน้อย 30 นาทีต่อวัน 5 วันต่อสัปดาห์ ปรึกษาแพทย์ก่อนเริ่มโปรแกรมการออกกำลังกาย\n       ควบคุมน้ำหนัก: หากมีน้ำหนักเกิน ควรลดน้ำหนักให้อยู่ในเกณฑ์ที่เหมาะสม\n       งดสูบบุหรี่และ
ลดการดื่มแอลกอฮอล์: การสูบบุหรี่และการดื่มแอลกอฮอล์เป็นปัจจัยเสี่ยงที่สำคัญของโรคความดันโลหิตสูง\n       จัดการความเครียด: หาทางผ่อนคลายความเครียด เช่น การทำสมาธิ โยคะ หรือการทำกิจกรรมที่ชอบ\n       พักผ่อนให้เพียงพอ: นอนหลับพักผ่อนอย่างน้อย 7-8 ชั่วโมงต่อคืน\n 
  รับประทานยาตามที่แพทย์สั่งอย่างเคร่งครัด: หากแพทย์สั่งจ่ายยาความดันโลหิต ควรรับประทานยาอย่างสม่ำเสมอตามขนาดและเวลาที่กำหนด ห้ามหยุดยาเองโดยเด็ดขาด\n   หลีกเลี่ยงเครื่องดื่มที่มีคาเฟอีน: คาเฟอีนอาจทำให้ความดันโลหิตสูงขึ้นได้\n   แจ้งให้แพทย์ทราบเกี่ยวกับยาหรืออ
าหารเสริมที่กำลังใช้อยู่: ยาหรืออาหารเสริมบางชนิดอาจมีผลต่อความดันโลหิต\n\nข้อควรระวัง:\n\n   ข้อมูลที่ให้มามีเพียงค่าความดันโลหิตและชีพจรเท่านั้น ไม่สามารถใช้ในการวินิจฉัยโรคได้ การวินิจฉัยโรคต้องอาศัยการตรวจร่างกายและการซักประวัติโดยละเอียดจากแพทย์\n   คำแนะนำ
ที่ให้มาเป็นเพียงคำแนะนำเบื้องต้น ไม่สามารถใช้ทดแทนคำแนะนำทางการแพทย์ได้ ควรปรึกษาแพทย์เพื่อรับคำแนะนำที่เหมาะสมกับสภาพร่างกายของแต่ละบุคคล\n\nสรุป:\n\nภาวะความดันโลหิตสูงที่พบในข้อมูลนี้เป็นเรื่องที่ต้องให้ความสำคัญอย่างยิ่ง ควรปรึกษาแพทย์โดยด่วนเพื่อวินิจฉัยแล
ะรับการรักษาที่เหมาะสม การปรับเปลี่ยนพฤติกรรมการใช้ชีวิตก็เป็นสิ่งสำคัญในการควบคุมความดันโลหิตและป้องกันภาวะแทรกซ้อน\n', 
'data': [
        {
            'heart_id': 209, 
            'systolic_pressure': 120, 
            'diastolic_pressure': 111, 
            'pulse_rate': 100, 
            'heart_report': 'ค่าความดันโลหิต 120/111 m
    mHg และชีพจร 100 ครั้งต่อนาที จำเป็นต้องพิจารณาอย่างรอบคอบเพื่อประเมินสุขภาพโดยรวม\n\nการประเมิน:\n\n   ความดันตัวบน (Systolic): 120 mmHg อยู่ในเกณฑ์ปกติค่อนไปทางสูงเล็กน้อย (Normal to Elevated). ค่าปกติคือ <120 mmHg.\n   ความดันตัวล่าง (Diastolic): 111 mmHg สูง
    กว่าปกติ (Stage 2 Hypertension). ค่าปกติคือ <80 mmHg. ความดันตัวล่างที่สูงกว่าปกติ บ่งบอกถึงความดันในหลอดเลือดขณะพักที่สูง ซึ่งอาจเพิ่มความเสี่ยงต่อโรคหัวใจและหลอดเลือด\n   ชีพจร (Pulse): 100 ครั้งต่อนาที อยู่ในเกณฑ์ปกติ (Normal). ค่าปกติคือ 60-100 ครั้งต่อนาที 
    แต่ควรสังเกตว่าอยู่ในช่วงขอบบน\n\nโดยรวม:\n\nความดันโลหิตโดยรวมสูงกว่าปกติ (Hypertension Stage 2) โดยเฉพาะความดันตัวล่างที่สูงอย่างชัดเจน แม้ว่าชีพจรจะอยู่ในเกณฑ์ปกติ แต่ความดันโลหิตที่สูงอาจส่งผลเสียต่อสุขภาพในระยะยาว\n\nคำแนะนำ:\n\n1.  ปรึกษาแพทย์: ควรพบแพทย์เ
    พื่อตรวจวินิจฉัยเพิ่มเติมและรับคำแนะนำในการรักษาที่เหมาะสม แพทย์อาจแนะนำให้ทำการตรวจเพิ่มเติม เช่น การตรวจเลือด หรือการตรวจคลื่นไฟฟ้าหัวใจ (EKG)\n2.  ปรับพฤติกรรม:\n       อาหาร: ลดการบริโภคโซเดียม (เกลือ), อาหารแปรรูป, และไขมันอิ่มตัว เน้นการรับประทานผัก ผลไม้ 
    และธัญพืชไม่ขัดสี\n       การออกกำลังกาย: ออกกำลังกายแบบแอโรบิกอย่างสม่ำเสมอ เช่น เดินเร็ว ว่ายน้ำ หรือปั่นจักรยาน อย่างน้อย 150 นาทีต่อสัปดาห์\n       ลดน้ำหนัก: หากมีน้ำหนักเกินหรือเป็นโรคอ้วน การลดน้ำหนักจะช่วยลดความดันโลหิตได้\n       งดสูบบุหรี่และจำกัดการด
    ื่มแอลกอฮอล์: การสูบบุหรี่และดื่มแอลกอฮอล์มากเกินไปเป็นปัจจัยเสี่ยงต่อความดันโลหิตสูง\n       จัดการความเครียด: หาทางผ่อนคลายความเครียด เช่น การทำสมาธิ โยคะ หรือการทำกิจกรรมที่ชอบ\n3.  ติดตามความดันโลหิต: วัดความดันโลหิตเป็นประจำที่บ้านและจดบันทึกเพื่อติดตามผลกา
    รรักษาและการปรับพฤติกรรม\n\nDisclaimer: ข้อมูลนี้มีวัตถุประสงค์เพื่อให้ข้อมูลเบื้องต้นเท่านั้น ไม่สามารถใช้ทดแทนคำแนะนำทางการแพทย์จากผู้เชี่ยวชาญได้', 
    'id': 5, 
    'date': datetime.datetime(2025, 4, 6, 14, 26, 1)
    }, 
    {'heart_id': 207, 
    'systolic_pressure': 150, 
    'diastolic_pressure': 100, 
    'pulse_rate': 120, 
    'heart_report': 'ค่าความดันโลหิต 150/100 mmHg และชีพจร 120 ครั้งต่อนาที ถือว่าสูงกว่าปกติและควรได้รับการดูแล\n\n1. การประเมิน:\n\n   ความดันตัวบน (Systolic): 150 mmHg จัดอยู่ในระดับความดันโลหิตสูงระยะที่ 1 (Stage 1 Hyperten
    sion) ซึ่งสูงกว่าค่าปกติ (น้อยกว่า 120 mmHg) บ่งชี้ว่าหัวใจต้องทำงานหนักขึ้นในการสูบฉีดเลือด\n   ความดันตัวล่าง (Diastolic): 100 mmHg จัดอยู่ในระดับความดันโลหิตสูงระยะที่ 2 (Stage 2 Hypertension) ซึ่งสูงกว่าค่าปกติ (น้อยกว่า 80 mmHg) แสดงถึงแรงดันในหลอดเลือดที่ส
    ูงเกินไปขณะหัวใจคลายตัว\n   ชีพจร (Pulse): 120 ครั้งต่อนาที สูงกว่าค่าปกติ (60-100 ครั้งต่อนาที) บ่งชี้ว่าหัวใจเต้นเร็วกว่าปกติ ซึ่งอาจเกิดจากความเครียด, การออกกำลังกาย, หรือปัญหาสุขภาพอื่นๆ\n\n2. โดยรวม:\n\nค่าความดันโลหิตที่สูงทั้งค่าตัวบนและตัวล่าง ร่วมกับชีพ
    จรที่เต้นเร็ว บ่งชี้ถึงภาวะที่ควรได้รับการดูแลและปรับปรุงเพื่อลดความเสี่ยงต่อปัญหาสุขภาพในระยะยาว เช่น โรคหัวใจ, หลอดเลือดสมอง, และไต\n\n3. คำแนะนำ:\n\n   ปรึกษาแพทย์: ควรพบแพทย์เพื่อตรวจวินิจฉัยหาสาเหตุของความดันโลหิตสูงและชีพจรเต้นเร็ว รวมถึงรับคำแนะนำในการรัก
    ษาที่เหมาะสม\n   ปรับพฤติกรรม:\n       อาหาร: ลดการบริโภคโซเดียม (เกลือ), อาหารแปรรูป, และไขมันอิ่มตัว เพิ่มการบริโภคผัก, ผลไม้, และธัญพืชไม่ขัดสี\n       ออกกำลังกาย: ออกกำลังกายแบบแอโรบิกอย่างสม่ำเสมอ เช่น เดินเร็ว, วิ่ง, ว่ายน้ำ อย่างน้อย 150 นาทีต่อสัปดาห์\n
        ลดน้ำหนัก: หากมีน้ำหนักเกิน ควรลดน้ำหนักให้อยู่ในเกณฑ์ที่เหมาะสม\n       จัดการความเครียด: ฝึกเทคนิคการผ่อนคลาย เช่น การทำสมาธิ, โยคะ, หรือการหายใจลึกๆ\n       งดสูบบุหรี่และจำกัดการดื่มแอลกอฮอล์: บุหรี่และแอลกอฮอล์สามารถเพิ่มความดันโลหิตและอัตราการเต้นขอ
    งหัวใจได้\n   ติดตามความดันโลหิตและชีพจร: วัดความดันโลหิตและชีพจรเป็นประจำเพื่อติดตามผลการรักษาและการปรับพฤติกรรม\n', 
    'id': 5, 
    'date': datetime.datetime(2025, 4, 6, 9, 17, 25)
    }, 
    {
        'heart_id': 206, 
            'systolic_pressure': 180, 
            'diastolic_pressure': 120, 
            'pulse_rate':120, 
            'heart_report': 'ค่าความดันโลหิต 180/120 mmHg และชีพจร 120 ครั้งต่อนาที ถือว่าสูงกว่าปกติและต้องได้รับการดูแลอย่างใกล้ชิด\n\n1. การประเมิน:\n\n   ความดันตัวบน (Systolic): 180 mmHg - สูงมาก (Hypertensive Crisis) เป็นภาวะฉุกเฉินที่ต้องได้รับการรักษาทันที เพร
        าะอาจนำไปสู่ความเสียหายของอวัยวะสำคัญ\n   ความดันตัวล่าง (Diastolic): 120 mmHg - สูงมาก (Hypertensive Crisis) เช่นเดียวกับความดันตัวบน เป็นภาวะที่อันตราย\n   ชีพจร (Pulse): 120 ครั้งต่อนาที - สูงกว่าปกติ (Tachycardia) ชีพจรปกติขณะพักคือ 60-100 ครั้งต่อนาที การที
        ่ชีพจรสูง อาจเกิดจากความเครียด, การออกกำลังกาย, หรือปัญหาสุขภาพ\n\n2. โดยรวม:\n\nค่าที่วัดได้บ่งชี้ถึงภาวะวิกฤตความดันโลหิตสูงร่วมกับชีพจรที่เต้นเร็ว ซึ่งเป็นสัญญาณอันตรายที่ต้องได้รับการประเมินและรักษาโดยแพทย์โดยด่วน ภาวะนี้อาจเพิ่มความเสี่ยงต่อโรคหัวใจและหลอดเ
        ลือด, โรคไต, และภาวะแทรกซ้อนอื่นๆ\n\n3. คำแนะนำ:\n\n   ปรึกษาแพทย์ทันที: ไปพบแพทย์หรือโรงพยาบาลใกล้บ้านโดยเร็วที่สุด เพื่อรับการวินิจฉัยและการรักษาที่เหมาะสม อย่ารอช้า\n   ควบคุมความเครียด: พยายามหากิจกรรมที่ช่วยลดความเครียด เช่น การทำสมาธิ, การฟังเพลง, หรือการพ
        ักผ่อน\n   ปรับพฤติกรรมการกิน: ลดการบริโภคอาหารที่มีโซเดียมสูง (เช่น อาหารแปรรูป, อาหารสำเร็จรูป), หลีกเลี่ยงอาหารที่มีไขมันอิ่มตัวและคอเลสเตอรอลสูง, และเพิ่มการบริโภคผักและผลไม้\n   ออกกำลังกาย: หากแพทย์อนุญาต ให้ออกกำลังกายแบบแอโรบิกอย่างสม่ำเสมอ เช่น การเดิน,
        การวิ่ง, หรือการว่ายน้ำ แต่ต้องอยู่ภายใต้คำแนะนำของแพทย์\n   ติดตามความดันโลหิตและชีพจร: วัดความดันโลหิตและชีพจรเป็นประจำ และบันทึกผลเพื่อนำไปปรึกษาแพทย์\n\nข้อควรระวัง:\n\n   อย่าปรับยาเองโดยไม่ปรึกษาแพทย์\n   หลีกเลี่ยงเครื่องดื่มที่มีคาเฟอีนและแอลกอฮอล์\n\nD
        isclaimer: ข้อมูลนี้มีวัตถุประสงค์เพื่อให้ข้อมูลเท่านั้น ไม่ถือเป็นคำแนะนำทางการแพทย์ หากมีข้อกังวลเรื่องสุขภาพ ควรปรึกษาแพทย์ผู้เชี่ยวชาญ\n', 
        'id': 5, 
        'date': datetime.datetime(2025, 4, 6, 7, 2, 21)
        }
]
}
```
## eat_medicine_report.py



#### ไฟล์นี้ทำหน้าที่เเสดงผลการจ่ายย่ามาเป็น ข้อมูล🔴

![App Screenshot](https://cdn.discordapp.com/attachments/1233105002898395137/1358456305425317929/image.png?ex=67f3e886&is=67f29706&hm=8b3ad512645b0bde12452c6bcec4f6b5098df13abe9dc1d215728611b524f848&)

#### การเรียกใช้งาน calss นี้จะทำงานในฟังชั่น on_show ของ  class Report1 โดยเริ่มทำงานที่บรรทัด ``` 1308 ``` ในไฟล์ main.py  
```


  from server.eat_medicine_report import eat_medicine_report   #import เข้ามาทำงานก่อน

medicine_report = eat_medicine_report() #เรียกใช้งาน class

 def on_show(self):
        print("Report1 is now visible")
        result = medicine_report.get_eatmedic(self.controller.user['id'])
        if result['status']:
            print(result)
        else:
            print(result['message'])
```

#### -สิ่งที่ต้องการ

```
   medicine_report.get_eatmedic(userid)
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `userid` | `Int` | **Required** id ของผู้ใช้งาน |


ตัวอย่างข้อมูลที่ดึงออกมา
```
{
    'status': True, 
    'data': 
    [
        {
            'time_get': datetime.datetime(2025, 1, 3, 7, 17, 36), 
            'medicine_get': 'success', 
            'medicine_1': 'พาราเซตามอล', 
            'medicine_2': None, 
            'medicine_3': None, 
            'medicine_4': None
        }, 
        {
            'time_get': datetime.datetime(2025, 1, 3, 7, 19, 38), 
            'medicine_get': 'success', 
            'medicine_1': 'พาราเซตามอล', 
            'medicine_2': None, 
            'medicine_3': None, 
            'medicine_4': None
        }, 
        {
            'time_get': datetime.datetime(2025, 1, 3, 7, 23, 2), 
            'medicine_get': 'success', 
            'medicine_1': 'พาราเซตามอล',
             'medicine_2': None, 
             'medicine_3': None,
              'medicine_4': None
        }
    ]
    
}


```


 






