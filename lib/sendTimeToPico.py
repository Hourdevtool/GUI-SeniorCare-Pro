# sendTimeToPico.py

try:
    # ใช้ชื่อเต็มเพื่อหลีกเลี่ยงปัญหา conflict กับ standard library
    import serial as pyserial
    # ตรวจสอบว่าเป็น pyserial จริงๆ (มี Serial class)
    if hasattr(pyserial, 'Serial'):
        SERIAL_AVAILABLE = True
        serial = pyserial
        # optional: list_ports สำหรับ auto-detect
        try:
            from serial.tools import list_ports
        except Exception:
            list_ports = None
    else:
        SERIAL_AVAILABLE = False
        print("Warning: serial module found but Serial class is not available.")
        print("This might be a conflict with Python's standard library serial module.")
        print("Please install pyserial: pip install pyserial")
except ImportError:
    SERIAL_AVAILABLE = False
    list_ports = None
    print("Warning: pyserial library is not installed. Serial communication will be disabled.")
    print("Install it with: pip install pyserial")
except AttributeError:
    SERIAL_AVAILABLE = False
    list_ports = None
    print("Warning: serial module conflict detected. Serial communication will be disabled.")
    print("Please ensure pyserial is installed: pip install pyserial")

import time
from datetime import datetime

allTime = []

def recivetime(Times):
    global allTime
    allTime = [time['time'] for time in Times]
    print("Times updated:", allTime)

def pySerialSendData(ser):
    if not SERIAL_AVAILABLE:
        return False
    try:
        ser.write(b'1\n')
        print("SendData: 1")

        response = ser.readline().decode().strip()
        if response:
            print("ESP32:", response)
            return True
        else:
            print("No response")
            return False
    except Exception as e:
        print("Serial error:", e)
        return False

def _auto_detect_port() -> str | None:
    """ค้นหาพอร์ต serial อัตโนมัติ (Windows/Unix)."""
    if not SERIAL_AVAILABLE or not list_ports:
        return None
    ports = list(list_ports.comports())
    if not ports:
        return None
    # เลือกพอร์ตแรกที่พบ
    return ports[0].device


def start_serial_loop(port="/dev/ttyUSB0", baudrate=115200):
    if not SERIAL_AVAILABLE:
        # ไม่พร้อมใช้งานก็เงียบๆ ออกไป
        return
    
    ser = None
    try:
        # ถ้าพอร์ต default ใช้ไม่ได้ ให้ลอง auto-detect
        import sys
        selected_port = port
        if sys.platform == 'win32' and selected_port.startswith('/'):
            # Windows ไม่ใช้ path แบบ /dev/... ให้ลอง auto detect
            selected_port = _auto_detect_port() or 'COM3'
        if sys.platform != 'win32' and not selected_port.startswith('/'):
            # Unix-based ควรเป็น /dev/tty*
            selected_port = _auto_detect_port() or '/dev/ttyUSB0'

        ser = serial.Serial(selected_port, baudrate, timeout=1)
        time.sleep(2)
    except Exception:
        # ไม่มีอุปกรณ์/พอร์ตไม่พบ: ออกเงียบๆ
        return

    sent_times = set()
    try:
        while True:
            currentTime = datetime.now().strftime("%H:%M:%S")
            if currentTime in allTime and currentTime not in sent_times:
                success = pySerialSendData(ser)
                if success:
                    sent_times.add(currentTime)
                else:
                    pass

            if currentTime not in allTime and sent_times:
                sent_times.clear()

            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        if ser and hasattr(ser, 'close'):
            try:
                ser.close()
            except:
                pass
