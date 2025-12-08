# รายงานการตรวจสอบความเข้ากันได้กับ Raspberry Pi 5

## 📋 สรุปผลการตรวจสอบ

ระบบ **GUI-SeniorCare-Pro** สามารถทำงานบน Raspberry Pi 5 ได้ แต่มีข้อควรระวังและสิ่งที่ต้องเตรียมดังนี้:

---

## ✅ ส่วนที่ทำงานได้ปกติ

### 1. **Serial Communication**
- ✅ ใช้ `/dev/serial0` ซึ่งถูกต้องสำหรับ Raspberry Pi 5
- ✅ Baudrate 115200 ใช้งานได้
- ✅ UART pins (GPIO14 TXD0, GPIO15 RXD0) ถูกต้องสำหรับ Pi 5
- ✅ ใช้ library `pyserial` ซึ่งรองรับ Linux

**หมายเหตุ**: ต้องเปิดใช้งาน UART ใน Raspberry Pi OS:
```bash
sudo raspi-config
# Interface Options → Serial Port → Enable
```

### 2. **Python Dependencies**
ส่วนใหญ่รองรับ Raspberry Pi 5:
- ✅ `customtkinter` - ทำงานได้ (ต้องมี X11 display)
- ✅ `pygame` - ทำงานได้ (ต้องตั้งค่า audio)
- ✅ `serial` (pyserial) - ทำงานได้
- ✅ `requests`, `PIL`, `gTTS` - ทำงานได้
- ✅ `pywifi` - ทำงานได้บน Linux
- ✅ `mysql-connector-python` - ทำงานได้
- ✅ `google-genai` - ทำงานได้

### 3. **Platform Detection**
- ✅ มีการตรวจสอบ `os.name` และ `sys.platform` เพื่อรองรับทั้ง Windows และ Linux
- ✅ มี fallback สำหรับ Linux ในส่วนต่างๆ

---

## ⚠️ ส่วนที่ต้องเตรียม/แก้ไข

### 1. **Display และ GUI**
**ปัญหา**: CustomTkinter ต้องการ X11 display server

**วิธีแก้**:
```bash
# ตรวจสอบว่ามี display หรือไม่
echo $DISPLAY

# ถ้าไม่มี ให้ตั้งค่า (สำหรับ headless หรือ SSH)
export DISPLAY=:0

# หรือใช้ VNC/Remote Desktop
```

**แนะนำ**: ใช้ Raspberry Pi OS Desktop หรือติดตั้ง X11 server

### 2. **Audio System**
**ปัญหา**: pygame ต้องการ audio system

**วิธีแก้**:
```bash
# ติดตั้ง audio drivers
sudo apt-get update
sudo apt-get install -y alsa-utils pulseaudio

# ตรวจสอบ audio device
aplay -l

# ตั้งค่า default audio device
sudo raspi-config
# Advanced Options → Audio → เลือก output device
```

### 3. **PDF Generation (Playwright)**
**ปัญหา**: `playwright` ต้องการ Chromium browser

**วิธีแก้**:
```bash
# ติดตั้ง dependencies สำหรับ playwright
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

# ติดตั้ง playwright browsers
pip install playwright
playwright install chromium
```

### 4. **On-Screen Keyboard**
**ปัญหา**: ใช้ `onboard` ซึ่งอาจไม่ได้ติดตั้งมา

**วิธีแก้**:
```bash
# ติดตั้ง onboard keyboard
sudo apt-get install -y onboard
```

### 5. **Environment Variables**
**ปัญหา**: ต้องตั้งค่า environment variables

**วิธีแก้**: สร้างไฟล์ `.env`:
```env
API_AI_KEY=your_api_key_here
DEBIAN_PATH=/path/to/debian/path
```

### 6. **Serial Port Permissions**
**ปัญหา**: ผู้ใช้ต้องมีสิทธิ์เข้าถึง serial port

**วิธีแก้**:
```bash
# เพิ่มผู้ใช้เข้า group dialout
sudo usermod -a -G dialout $USER

# หรือใช้ sudo (ไม่แนะนำ)
# ต้อง logout และ login ใหม่เพื่อให้การเปลี่ยนแปลงมีผล
```

### 7. **WiFi Management (pywifi)**
**ปัญหา**: `pywifi` อาจต้องการสิทธิ์พิเศษ

**วิธีแก้**:
```bash
# ติดตั้ง dependencies
sudo apt-get install -y \
    libnl-3-dev \
    libnl-genl-3-dev

# หรือใช้ sudo สำหรับการจัดการ WiFi
```

---

## 🔧 ขั้นตอนการติดตั้งบน Raspberry Pi 5

### 1. **เตรียมระบบ**
```bash
# อัพเดตระบบ
sudo apt-get update && sudo apt-get upgrade -y

# ติดตั้ง Python และ pip (ถ้ายังไม่มี)
sudo apt-get install -y python3 python3-pip python3-venv
```

### 2. **เปิดใช้งาน UART**
```bash
# แก้ไข config.txt
sudo nano /boot/firmware/config.txt

# เพิ่มหรือแก้ไข:
enable_uart=1

# แก้ไข cmdline.txt (ถ้ามี)
sudo nano /boot/firmware/cmdline.txt
# ลบ console=serial0,115200 ออก (ถ้ามี)

# Reboot
sudo reboot
```

### 3. **ติดตั้ง Dependencies**
```bash
# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate

# ติดตั้ง Python packages
pip install -r requirements.txt

# หรือติดตั้งทีละตัวตาม lib.txt
pip install customtkinter pillow pygame gTTS serial requests \
    mysql-connector-python google-genai pywifi tkcalendar \
    babel python-dotenv playwright
```

### 4. **ตั้งค่า Audio**
```bash
# ตรวจสอบ audio
aplay /usr/share/sounds/alsa/Front_Left.wav

# ถ้าไม่ได้ยินเสียง ให้ตั้งค่า
sudo raspi-config
# Advanced Options → Audio → เลือก output
```

### 5. **ตั้งค่า Display (ถ้าใช้ headless)**
```bash
# สำหรับ VNC
sudo apt-get install -y realvnc-vnc-server

# หรือใช้ X11 forwarding สำหรับ SSH
# ใช้ -X flag เมื่อ SSH
ssh -X pi@raspberrypi
```

---

## 🧪 การทดสอบ

### 1. **ทดสอบ Serial Port**
```python
import serial
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
print(f"Serial port opened: {ser.is_open}")
ser.close()
```

### 2. **ทดสอบ Audio**
```python
from pygame import mixer
mixer.init()
mixer.music.load("song/startup_greeting.mp3")
mixer.music.play()
```

### 3. **ทดสอบ Display**
```python
import customtkinter as ctk
root = ctk.CTk()
root.title("Test")
root.geometry("400x300")
root.mainloop()
```

---

## 📝 ไฟล์ที่ต้องตรวจสอบ/แก้ไข

### 1. **lib/loadenv.py**
- ✅ ตรวจสอบแล้ว - มีการตรวจสอบ `os.name` เพื่อใช้ path ที่ถูกต้อง

### 2. **lib/serial_handler.py**
- ✅ ตรวจสอบแล้ว - ใช้ `/dev/serial0` ซึ่งถูกต้อง

### 3. **main.py**
- ✅ ตรวจสอบแล้ว - มี platform detection สำหรับ keyboard
- ⚠️ ต้องตรวจสอบว่า onboard keyboard ติดตั้งแล้ว

### 4. **server/exportpdf.py**
- ✅ ตรวจสอบแล้ว - มี fallback สำหรับ Linux (ใช้ firefox)

---

## ⚡ Performance Considerations

### Raspberry Pi 5 Specifications:
- CPU: Quad-core Cortex-A76 @ 2.4GHz
- RAM: 4GB/8GB options
- GPU: VideoCore VII

**คำแนะนำ**:
1. ใช้ Raspberry Pi 5 รุ่น 8GB RAM สำหรับประสิทธิภาพที่ดีกว่า
2. ใช้ microSD card Class 10 หรือเร็วกว่า
3. พิจารณาใช้ SSD ผ่าน USB 3.0 สำหรับประสิทธิภาพที่ดีกว่า
4. ปิด visual effects ที่ไม่จำเป็น

---

## 🐛 ปัญหาที่อาจพบ

### 1. **Serial Port ไม่ทำงาน**
**อาการ**: `SerialException: [Errno 2] No such file or directory: '/dev/serial0'`

**แก้ไข**:
```bash
# ตรวจสอบว่า UART เปิดใช้งานแล้ว
sudo raspi-config
# Interface Options → Serial Port → Enable

# ตรวจสอบว่า serial port มีอยู่
ls -l /dev/serial*
```

### 2. **Audio ไม่ทำงาน**
**อาการ**: pygame ไม่สามารถเล่นเสียงได้

**แก้ไข**:
```bash
# ตรวจสอบ audio device
aplay -l

# ตั้งค่า default audio
sudo raspi-config
# Advanced Options → Audio → เลือก output
```

### 3. **Display Error**
**อาการ**: `_tkinter.TclError: no display name and no $DISPLAY environment variable`

**แก้ไข**:
```bash
export DISPLAY=:0
# หรือใช้ VNC/Remote Desktop
```

### 4. **Permission Denied (Serial)**
**อาการ**: `PermissionError: [Errno 13] Permission denied: '/dev/serial0'`

**แก้ไข**:
```bash
sudo usermod -a -G dialout $USER
# logout และ login ใหม่
```

---

## ✅ Checklist ก่อนใช้งาน

- [ ] Raspberry Pi OS ติดตั้งแล้ว
- [ ] Python 3.8+ ติดตั้งแล้ว
- [ ] UART เปิดใช้งานแล้ว (`/dev/serial0`)
- [ ] ผู้ใช้อยู่ใน group `dialout`
- [ ] Audio system ทำงานได้
- [ ] Display/X11 พร้อมใช้งาน
- [ ] Dependencies ทั้งหมดติดตั้งแล้ว
- [ ] Environment variables ตั้งค่าแล้ว (`.env`)
- [ ] Playwright Chromium ติดตั้งแล้ว
- [ ] Onboard keyboard ติดตั้งแล้ว (ถ้าต้องการ)
- [ ] Network connection พร้อมใช้งาน
- [ ] Database connection ตั้งค่าแล้ว

---

## 📚 เอกสารอ้างอิง

- [Raspberry Pi 5 Documentation](https://www.raspberrypi.com/documentation/)
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [PySerial Documentation](https://pyserial.readthedocs.io/)
- [Playwright Documentation](https://playwright.dev/python/)

---

## 🎯 สรุป

**ระบบสามารถทำงานบน Raspberry Pi 5 ได้** แต่ต้อง:
1. ✅ เตรียมระบบให้พร้อม (UART, Audio, Display)
2. ✅ ติดตั้ง dependencies ทั้งหมด
3. ✅ ตั้งค่า permissions และ environment variables
4. ✅ ทดสอบแต่ละส่วนก่อนใช้งานจริง

**เวลาที่ใช้ในการเตรียม**: ประมาณ 30-60 นาที

**ระดับความยาก**: ปานกลาง (ต้องมีความรู้พื้นฐาน Linux)

---

*รายงานนี้สร้างเมื่อ: 2025-01-XX*
*เวอร์ชันระบบ: GUI-SeniorCare-Pro*

