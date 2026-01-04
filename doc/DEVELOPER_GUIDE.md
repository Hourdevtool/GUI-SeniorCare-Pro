# 📚 คู่มือการพัฒนา SeniorCare Pro

คู่มือนี้อธิบายวิธีการพัฒนาและขยายระบบ SeniorCare Pro ที่ใช้สถาปัตยกรรม MVC

---

## 🏗️ โครงสร้างโปรเจค

```
GUI-SeniorCare-Pro/
├── main.py                 # จุดเริ่มต้นโปรแกรม
├── controllers/            # ตัวควบคุมหลัก
│   └── app_controller.py   # AppController - จัดการ navigation และ state
├── views/                  # หน้าจอ UI ทั้งหมด
│   ├── login_view.py       # หน้า Login
│   ├── home_view.py        # หน้า Home
│   ├── medication_stock_view.py    # หน้าข้อมูลยา
│   ├── schedule_setup_view.py      # หน้าตั้งเวลาจ่ายยา
│   ├── health_view.py      # หน้าสุขภาพ
│   ├── report_view.py      # หน้ารายงาน
│   └── user_info_view.py   # หน้าข้อมูลผู้ใช้
├── models/                 # โมเดลและ Services
│   ├── voice_service.py    # บริการเสียง
│   └── app_services.py     # บริการต่างๆ (auth, etc.)
├── config/                 # การตั้งค่า
│   ├── styles.py           # สี, ธีม, สไตล์
│   └── constants.py        # ค่าคงที่
├── utils/                  # ฟังก์ชันช่วยเหลือ
│   └── helpers.py          # Helper functions
├── server/                 # API Services
│   ├── auth.py             # Authentication
│   ├── managemedic.py      # จัดการยา
│   ├── setting_time.py     # ตั้งเวลา
│   └── ...
└── lib/                    # ไลบรารีเสริม
    ├── serial_handler.py   # จัดการ Serial Port
    └── ...
```

---

## 📄 1. การสร้างหน้าใหม่ (New View)

### ขั้นตอนที่ 1: สร้างไฟล์ View

สร้างไฟล์ใหม่ใน `views/` เช่น `views/my_new_view.py`

```python
import customtkinter as ctk
from PIL import Image
from lib.loadenv import PATH
from config.styles import force_color, back_color, hover_color
from utils.helpers import show_onboard, hide_onboard

class MyNewView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # สร้าง UI ของคุณที่นี่
        self.create_ui()
    
    def create_ui(self):
        """สร้าง UI elements"""
        # พื้นหลัง
        bg_image = Image.open(f"{PATH}image/background.png").resize((1024, 800))
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # ปุ่มย้อนกลับ
        back_btn = ctk.CTkButton(
            self,
            text="← ย้อนกลับ",
            command=self.go_back,
            fg_color=force_color,
            hover_color=hover_color
        )
        back_btn.place(x=20, y=20)
    
    def go_back(self):
        """กลับไปหน้า Home"""
        from views.home_view import HomePage
        self.controller.show_frame(HomePage)
    
    def on_show(self):
        """เรียกเมื่อหน้านี้แสดงผล - ใช้สำหรับโหลดข้อมูล"""
        print("MyNewView is now visible")
        # โหลดข้อมูลหรือ refresh UI ที่นี่
```

### ขั้นตอนที่ 2: ลงทะเบียนใน AppController

แก้ไข `controllers/app_controller.py`:

```python
# 1. เพิ่ม import
from views.my_new_view import MyNewView

# 2. เพิ่มใน frame_classes (ประมาณบรรทัด 145)
frame_classes = (
    HomePage, Frame2, Frame3, Frame4, add_Frame, info, 
    MedicationApp, AIgen, MedicationScheduleFrame, 
    ReportFrame, Report1, Report2, login, Wificonnect, LoadingScreen,
    MyNewView  # เพิ่มตรงนี้
)
```

### ขั้นตอนที่ 3: เรียกใช้งาน

```python
# จากที่ไหนก็ได้ในโค้ด
self.controller.show_frame(MyNewView)
```

---

## 🔘 2. การเพิ่มปุ่มในหน้า Home

แก้ไข `views/home_view.py` ใน method `create_menu_buttons()`:

### สำหรับ Patient (ผู้ป่วย)
- แสดงเฉพาะปุ่ม SOS และ Logout

### สำหรับ User (ผู้ดูแล)
แก้ไขประมาณบรรทัด 680-766:

```python
if user_role == 'user':
    # เพิ่มรูปภาพปุ่มใหม่
    paths = [
        f"{PATH}imgNew/icontime.png",
        f"{PATH}imgNew/iconheath.png",
        f"{PATH}imgNew/iconreport.png",
        f"{PATH}imgNew/my_new_icon.png",  # ← เพิ่มไอคอนใหม่
        f"{PATH}imgNew/iconout.png",
        f"{PATH}imgNew/icondow.png"
    ]
    
    # เพิ่มข้อความปุ่ม
    btn_texts = [
        "ตั้งเวลา",
        "สุขภาพ",
        "รายงาน",
        "ฟีเจอร์ใหม่",  # ← เพิ่มข้อความ
        "ออกระบบ",
        "ปิดเครื่อง"
    ]
    
    # Import view ใหม่
    from views.my_new_view import MyNewView
    
    # เพิ่มใน pages array
    pages = [Frame3, Frame4, ReportFrame, MyNewView, login, None]
```

### สำหรับ Admin (ผู้ดูแลระบบ)
แก้ไขประมาณบรรทัด 768-863 (เหมือนกับ User)

---

## 🌐 3. การเรียกใช้ API

### 3.1 API ที่มีอยู่แล้ว

```python
# ใน view ของคุณ
from server.managemedic import manageMedicData
from server.setting_time import setting_eat_time
from server.info import infoData

manageMedic = manageMedicData()
set_dispensing_time = setting_eat_time()
manageData = infoData()

# ตัวอย่างการใช้งาน
def load_medicines(self):
    result = manageMedic.getMedicine(
        self.controller.user['id'], 
        self.controller.user['device_id']
    )
    
    if result['status']:
        medicines = result['Data']
        # ทำอะไรกับข้อมูล
    else:
        print(f"Error: {result['message']}")
```

### 3.2 การสร้าง API Service ใหม่

สร้างไฟล์ใน `server/my_service.py`:

```python
import requests
from lib.loadenv import API_URL

class MyService:
    def __init__(self):
        self.base_url = API_URL
    
    def get_data(self, user_id):
        """ดึงข้อมูล"""
        try:
            url = f"{self.base_url}/api/my_endpoint.php"
            payload = {"user_id": user_id}
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": False, "message": "Server error"}
                
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Network error: {e}"}
    
    def save_data(self, user_id, data):
        """บันทึกข้อมูล"""
        try:
            url = f"{self.base_url}/api/save_data.php"
            payload = {
                "user_id": user_id,
                "data": data
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
            
        except Exception as e:
            return {"status": False, "message": str(e)}
```

### 3.3 การใช้งาน API พร้อม Loading Screen

```python
def fetch_data_with_loading(self):
    """ดึงข้อมูลพร้อมแสดง Loading"""
    # แสดง Loading
    self.controller.show_loading("กำลังโหลดข้อมูล...", "กรุณารอสักครู่")
    
    # ทำงานใน Background Thread
    def worker():
        try:
            result = my_service.get_data(self.controller.user['id'])
            
            if result['status']:
                # อัพเดท UI ใน Main Thread
                self.controller.after(0, lambda: self.update_ui(result['data']))
                self.controller.after(0, lambda: self.controller.notifier.show_notification(
                    "โหลดข้อมูลสำเร็จ", success=True
                ))
            else:
                self.controller.after(0, lambda: self.controller.notifier.show_notification(
                    result['message'], success=False
                ))
        except Exception as e:
            self.controller.after(0, lambda: self.controller.notifier.show_notification(
                f"เกิดข้อผิดพลาด: {e}", success=False
            ))
        finally:
            # ซ่อน Loading
            self.controller.after(0, self.controller.hide_loading)
    
    threading.Thread(target=worker, daemon=True).start()
```

---

## 🎨 4. การใช้ Styles และ Colors

```python
from config.styles import (
    force_color,      # สีหลัก
    back_color,       # สีพื้นหลัง
    hover_color,      # สีเมื่อ hover
    word_color,       # สีข้อความ
    select_color,     # สีเมื่อเลือก
    BUTTON_RADIUS,    # มุมโค้งปุ่ม
    ROLE_THEMES       # ธีมตาม role
)

# ใช้งาน
button = ctk.CTkButton(
    self,
    text="บันทึก",
    fg_color=force_color,
    hover_color=hover_color,
    text_color="white",
    corner_radius=BUTTON_RADIUS
)
```

---

## 🔄 5. Navigation ระหว่างหน้า

```python
# ไปหน้าอื่น
from views.home_view import HomePage
self.controller.show_frame(HomePage)

# ไปหน้าอื่นพร้อมส่งข้อมูล (ใช้ controller.user หรือ global state)
self.controller.user['temp_data'] = {"key": "value"}
self.controller.show_frame(TargetView)
```

---

## 📱 6. การใช้ Notifier (แจ้งเตือน)

```python
# แจ้งเตือนสำเร็จ
self.controller.notifier.show_notification("บันทึกสำเร็จ", success=True)

# แจ้งเตือนล้มเหลว
self.controller.notifier.show_notification("เกิดข้อผิดพลาด", success=False)
```

---

## 🔐 7. การเข้าถึงข้อมูล User

```python
# ดึงข้อมูล user ปัจจุบัน
if self.controller.user:
    user_id = self.controller.user['id']
    user_name = self.controller.user.get('firstname_th', 'ผู้ใช้')
    user_role = self.controller.user.get('urole', '').lower()
    device_id = self.controller.user['device_id']
```

---

## 🧪 8. Best Practices

### ✅ DO (ควรทำ)
- ใช้ `on_show()` สำหรับโหลดข้อมูลเมื่อหน้าแสดงผล
- ใช้ Threading สำหรับ API calls ที่ใช้เวลานาน
- ใช้ `controller.after(0, callback)` เมื่ออัพเดท UI จาก Thread
- Import locally ใน method เพื่อหลีกเลี่ยง circular imports
- ใช้ try-except สำหรับ API calls
- แสดง Loading Screen เมื่อทำงานนาน

### ❌ DON'T (ไม่ควรทำ)
- ❌ ไม่ควร import views อื่นๆ ที่ top-level (ใช้ local import แทน)
- ❌ ไม่ควรเรียก API ใน Main Thread โดยตรง
- ❌ ไม่ควรอัพเดท UI จาก Background Thread
- ❌ ไม่ควร hardcode ค่าสี (ใช้จาก config.styles)
- ❌ ไม่ควรสร้าง global variables

---

## 🐛 9. Debugging Tips

```python
# พิมพ์ข้อมูล debug
print(f"[DEBUG] User ID: {self.controller.user['id']}")

# ตรวจสอบว่า frame แสดงผลหรือไม่
def on_show(self):
    print(f"{self.__class__.__name__} is now visible")

# ตรวจสอบ network status
network_status = self.controller.network_status_var.get()
print(f"Network: {network_status}")
```

---

## 📝 10. ตัวอย่างการสร้างหน้าใหม่แบบสมบูรณ์

```python
# views/example_view.py
import customtkinter as ctk
from PIL import Image
import threading
from lib.loadenv import PATH
from config.styles import force_color, back_color, hover_color
from server.managemedic import manageMedicData

manageMedic = manageMedicData()

class ExampleView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.data = []
        
        # Background
        bg_image = Image.open(f"{PATH}image/background.png").resize((1024, 800))
        self.bg_ctk_image = ctk.CTkImage(light_image=bg_image, size=(1024, 800))
        bg_label = ctk.CTkLabel(self, image=self.bg_ctk_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="ตัวอย่างหน้าใหม่",
            font=("TH Sarabun New", 36, "bold"),
            text_color=force_color
        )
        title.place(x=400, y=50)
        
        # Content Frame
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            width=800,
            height=400,
            fg_color="white"
        )
        self.content_frame.place(x=100, y=150)
        
        # Back Button
        back_btn = ctk.CTkButton(
            self,
            text="← ย้อนกลับ",
            command=self.go_back,
            fg_color=force_color,
            hover_color=hover_color,
            width=120,
            height=40
        )
        back_btn.place(x=20, y=20)
    
    def on_show(self):
        """เรียกเมื่อหน้าแสดงผล"""
        print("ExampleView is now visible")
        self.load_data()
    
    def load_data(self):
        """โหลดข้อมูล"""
        self.controller.show_loading("กำลังโหลด...", "กรุณารอสักครู่")
        
        def worker():
            try:
                result = manageMedic.getMedicine(
                    self.controller.user['id'],
                    self.controller.user['device_id']
                )
                
                if result['status']:
                    self.data = result['Data']
                    self.controller.after(0, self.display_data)
                    self.controller.after(0, lambda: self.controller.notifier.show_notification(
                        "โหลดข้อมูลสำเร็จ", success=True
                    ))
                else:
                    self.controller.after(0, lambda: self.controller.notifier.show_notification(
                        result['message'], success=False
                    ))
            except Exception as e:
                self.controller.after(0, lambda: self.controller.notifier.show_notification(
                    f"เกิดข้อผิดพลาด: {e}", success=False
                ))
            finally:
                self.controller.after(0, self.controller.hide_loading)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def display_data(self):
        """แสดงข้อมูล"""
        # ล้าง content เก่า
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # แสดงข้อมูลใหม่
        for item in self.data:
            label = ctk.CTkLabel(
                self.content_frame,
                text=item['medicine_name'],
                font=("TH Sarabun New", 24)
            )
            label.pack(pady=10)
    
    def go_back(self):
        """กลับหน้า Home"""
        from views.home_view import HomePage
        self.controller.show_frame(HomePage)
```

---

## 🚀 เริ่มต้นพัฒนา

1. สร้างไฟล์ view ใหม่ใน `views/`
2. ลงทะเบียนใน `app_controller.py`
3. เพิ่มปุ่มใน `home_view.py` (ถ้าต้องการ)
4. ทดสอบการทำงาน
5. Commit และ Push

---

**หมายเหตุ:** เอกสารนี้จะอัพเดทเมื่อมีการเปลี่ยนแปลงสถาปัตยกรรม
