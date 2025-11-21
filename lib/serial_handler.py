import serial
import time
from datetime import datetime, timedelta
import json
import re
from threading import Lock

# ค่าคงที่สำหรับ Serial port
DEFAULT_SERIAL_PORT = "/dev/serial0"
DEFAULT_BAUDRATE = 115200
DONT_PICK_THRESHOLD = 5

allTime = []
_receive_buffer = ""
LOG_INCOMPLETE_WARNING = False
_schedule_lock = Lock()
_triggered_schedule_keys = set()


def _handle_special_message(data):
    """Map special message payloads to shorthand strings."""
    message = data.get("message")
    if message == "reset_data":
        return "rehome_sent"

    cmd = data.get("cmd")
    if cmd == 1:
        return "cmd_1_sent"

    return None


def _is_status_payload(data):
    """ตรวจสอบว่า payload เป็นข้อมูลสถานะแบต/สเตตัสตามที่คาดหวังหรือไม่"""
    if not isinstance(data, dict):
        return False

    has_battery = "battery" in data
    has_status = "status" in data

    return has_battery and has_status


def _normalize_status_value(status):
    """แปลงค่าที่ได้รับจากบอร์ดให้เป็นสถานะที่ระบบรู้จัก"""
    if status is None:
        return None

    status_str = str(status).strip().lower()

    if status_str in {"fail", "complete", "nopush"}:
        return status_str
    if status_str == "0":
        return "fail"
    if status_str == "1":
        return "complete"

    return status_str


def _parse_schedule_time(time_str):
    """แปลงสตริงเวลาให้เป็น datetime สำหรับตรวจสอบเวลาจ่ายยา"""
    if not time_str:
        return None

    formats = [
        "%H:%M",
        "%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]

    now = datetime.now()

    for fmt in formats:
        try:
            parsed = datetime.strptime(time_str, fmt)
            if "%Y" in fmt:
                return parsed
            return datetime.combine(now.date(), parsed.time())
        except ValueError:
            continue
    return None


def recivetime(Times):
    global allTime, _triggered_schedule_keys
    normalized_times = [
        time_entry.get("time")
        for time_entry in Times
        if isinstance(time_entry, dict) and time_entry.get("time")
    ]

    with _schedule_lock:
        if normalized_times == allTime:
            print("Times received (no change):", allTime)
            return

        allTime = normalized_times
        _triggered_schedule_keys = set()

    print("Times updated:", allTime)


def _clear_serial_buffers(ser):
    """ล้าง buffer ของ serial port ทั้ง input/output"""
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("🗑️  ล้าง buffer แล้ว")
    except AttributeError:
        pass
    except Exception as e:
        print(f"Warning: ไม่สามารถล้าง buffer ได้ - {e}")


def pySerialSendData(ser, reset=True):
    try:
        data = {
                "cmd": 0,
                # "message": "reset_data"
                "message": "init"
            }
        command = json.dumps(data) + "\n"
        # Debug: print transmitted JSON line
        try:
            print(f"TX: {command.strip()}")
        except Exception:
            pass
        _clear_serial_buffers(ser)
        ser.write(command.encode("utf-8"))
        return True
    except serial.SerialException as e:
        print("Serial error (send):", e)
        return False
    

def pySerialReceiveData(ser, timeout=5.0):
    """รับข้อมูลจาก ESP32 (boand) และรอจนกว่าจะได้ข้อมูลหรือ timeout
    
    Args:
        ser: Serial port object
        timeout: เวลารอสูงสุด (วินาที)
    
    Returns:
        dict: ข้อมูล JSON ที่ได้รับ (มี status และ battery)
        str: ข้อความพิเศษจาก ESP32 (เช่น "rehome_sent", "cmd_1_sent", "waiting")
        None: ถ้า timeout
    """
    start_time = time.time()
    MAX_BUFFER_SIZE = 4096
    global _receive_buffer
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            try:
                # อ่านทีละ byte เพื่อจัดการกับ buffer แบบเดียวกับ ESP32
                raw = ser.read(1)
                if not raw:
                    continue
                
                try:
                    char = raw.decode('utf-8', errors='ignore')
                except UnicodeError:
                    continue
                
                # ตรวจสอบว่าได้รับข้อมูลครบ (เจอ newline)
                if char == "\n":
                    line = _receive_buffer.strip()
                    _receive_buffer = ""  # เคลียร์ buffer
                    
                    if not line:
                        continue
                    
                    # Debug: print raw received line
                    try:
                        print(f"RX RAW: {line}")
                    except Exception:
                        pass
                    
                    # พยายาม parse JSON ก่อน
                    try: 
                        data = json.loads(line)
                        # Debug: print parsed JSON
                        try:
                            print(f"RX JSON: {data}")
                        except Exception:
                            pass

                        special = _handle_special_message(data)
                        if special is not None:
                            return special

                        if _is_status_payload(data):
                            return data

                        # ถ้า JSON ไม่ใช่ payload ที่เราสนใจ ให้ข้าม
                        print(f"Ignored JSON payload: {data}")
                        continue
                    except json.JSONDecodeError:
                        # ถ้าไม่ใช่ JSON อาจเป็นข้อความพิเศษจาก ESP32
                        # เช่น "rehome_sent", "cmd_1_sent", "waiting"
                        print(f"RX Text: {line}")
                        return line
                
                # เพิ่มข้อมูลใน buffer
                _receive_buffer += char
                
                # ตรวจสอบ buffer overflow
                if len(_receive_buffer) >= MAX_BUFFER_SIZE:
                    print(f"Error: Buffer overflow at {len(_receive_buffer)} bytes")
                    _receive_buffer = ""
                    return f"Error: Buffer overflow at {MAX_BUFFER_SIZE} bytes"
                    
            except Exception as e:  
                print(f"Receive error: {e}")
                _receive_buffer = ""
                continue
        
        time.sleep(0.01)  # รอสั้นๆ เพื่อไม่ให้ busy loop
    
    # Timeout
    if _receive_buffer and LOG_INCOMPLETE_WARNING:
        print(f"Warning: Timeout with incomplete data: {_receive_buffer[:50]}")
    return None

def send_and_receive(ser, command_data=None, timeout=5.0):
    """ส่งคำสั่งไปหา ESP32 (boand) แล้วรอรับข้อมูลตอบกลับ
    
    Args:
        ser: Serial port object
        command_data: dict ข้อมูลคำสั่งที่จะส่ง (ถ้า None จะใช้ init)
                     รองรับคำสั่ง:
                     - {"cmd": 1, "message": "init"} → ส่งคำสั่ง cmd=1
                     - {"cmd": 1, "message": "reset_data"} → ส่งคำสั่ง reset
                     - dict อื่นๆ → ส่ง JSON ตามที่กำหนด
        timeout: เวลารอสูงสุด (วินาที)
    
    Returns:
        dict: ข้อมูล JSON ที่ได้รับจาก ESP32 (มี status และ battery)
        str: ข้อความพิเศษจาก ESP32 (เช่น "rehome_sent", "cmd_1_sent", "waiting")
        None: ถ้า timeout
    """
    # ส่งคำสั่ง
    if command_data is None:
        command_data = {"cmd": 1, "message": "init"}
    
    try:
        command = json.dumps(command_data) + "\n"
        print(f"TX: {command.strip()}")
        _clear_serial_buffers(ser)
        ser.write(command.encode("utf-8"))
        ser.flush()  # ตรวจสอบให้ข้อมูลส่งออกไปทันที
        
        # รอรับข้อมูลตอบกลับ
        response = pySerialReceiveData(ser, timeout=timeout)
        return response
        
    except serial.SerialException as e:
        print(f"Serial error (send_and_receive): {e}")
        return None
    except Exception as e:
        print(f"Error in send_and_receive: {e}")
        return None


def send_rehome_command(ser, timeout=5.0):
    """ส่งคำสั่ง rehome ไปหา ESP32 (boand)
    
    Args:
        ser: Serial port object
        timeout: เวลารอสูงสุด (วินาที)
    
    Returns:
        str: "rehome_sent" ถ้าสำเร็จ หรือ None ถ้า timeout
    """
    command_data = {"cmd": 1, "message": "reset_data"}
    response = send_and_receive(ser, command_data, timeout=timeout)
    
    if isinstance(response, str) and response == "rehome_sent":
        return response
    return None


def send_cmd1_command(ser, timeout=5.0):
    """ส่งคำสั่ง cmd=1 ไปหา ESP32 (boand)
    
    Args:
        ser: Serial port object
        timeout: เวลารอสูงสุด (วินาที)
    
    Returns:
        str: "cmd_1_sent" ถ้าสำเร็จ หรือ None ถ้า timeout
    """
    command_data = {"cmd": 1, "message": "init"}
    response = send_and_receive(ser, command_data, timeout=timeout)
    
    if isinstance(response, str) and response == "cmd_1_sent":
        return response
    return None
    
def start_Serial_loop(port=None, baudrate=None, battery_var=None, status_var=None, request_interval=5.0, notification_callback=None):
    """Loop หลักที่ส่งคำสั่งไปหา ESP32 แล้วรอรับข้อมูลตอบกลับ
    
    Args:
        port: Serial port (default: "/dev/serial0")
        baudrate: Baud rate (default: 115200)
        battery_var: StringVar สำหรับเก็บค่าแบตเตอรี่
        status_var: StringVar สำหรับเก็บสถานะ
        request_interval: ช่วงเวลาระหว่างการส่งคำสั่ง (วินาที) - default 5 วินาที
        notification_callback: ฟังก์ชัน callback สำหรับแจ้งเตือน (token, group_id, message, type, identifier)
    """
    # ใช้ค่า default ถ้าไม่ได้ระบุ
    if port is None:
        port = DEFAULT_SERIAL_PORT
    if baudrate is None:
        baudrate = DEFAULT_BAUDRATE
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # รอให้ serial port พร้อม
        print(f"Serial port opened: {port} at {baudrate} baud")
    except serial.SerialException as e:
        print(f"Serial error at open: {e}") 
        return
    
    # ส่งคำสั่งเริ่มต้นหลังจากเปิด Serial 2 วินาที
    print("Sending initial command...")
    initial_command = {"cmd": 0, "message": "init"}
    command = json.dumps(initial_command) + "\n"
    print(f"TX: {command.strip()}")
    _clear_serial_buffers(ser)
    ser.write(command.encode("utf-8"))
    ser.flush()
    
    # รอรับ status แรก (ประมาณ 3 วินาทีหลังเริ่มต้น)
    print("Waiting for first status...")
    first_status = pySerialReceiveData(ser, timeout=5.0)
    if first_status:
        print(f"Received first status: {first_status}")
        if isinstance(first_status, dict):
            battery_level = first_status.get("battery")
            new_status = first_status.get("status")
            if battery_var is not None and battery_level is not None:
                try:
                    battery_var.set(battery_level)
                except Exception as e:
                    print(f"Error setting battery_var: {e}")
            if status_var is not None and new_status is not None:
                try:
                    status_var.set(str(new_status))
                except Exception as e:
                    print(f"Error setting status_var: {e}")
    
    last_payload = None
    last_special_message = None
    last_status_value = None
    status_fail_count = 0  # นับจำนวนครั้งที่ได้รับสถานะ fail ติดกัน
    STATUS_FAIL_THRESHOLD = 5  # จำนวนครั้งที่ต้องได้รับสถานะ fail ก่อนส่งคำสั่ง cmd=1
    dontpick_sos_triggered = False
    command_tolerance_after_sec = 60  # ส่งคำสั่งภายใน 60 วินาทีหลังถึงเวลาที่ตั้งไว้
    command_tolerance_before_sec = 0   # ไม่ส่งก่อนเวลาที่ตั้งไว้

    try:
        while True:
            # รับข้อมูลจาก ESP32 ตลอดเวลา (ESP32 ส่งสถานะกลับมาทุกวินาที)
            received_data = pySerialReceiveData(ser, timeout=5) 
            
            if received_data:
                print(f"Received data: {received_data}")
                
                # ตรวจสอบว่าเป็น JSON (dict) หรือข้อความ (str)
                if isinstance(received_data, dict):
                    # ข้อมูล JSON ที่มี status และ battery
                    battery_level = received_data.get("battery")
                    new_status = received_data.get("status")
                    normalized_status = _normalize_status_value(new_status)
                    
                    # ข้ามถ้าข้อมูลเหมือนเดิม (ยกเว้นเมื่อสถานะเป็น fail เพื่อให้นับได้)
                    if last_payload == received_data and normalized_status != "fail":
                        continue

                    last_payload = received_data.copy()

                    if battery_var is not None and battery_level is not None:
                        try:
                            battery_var.set(battery_level)
                        except Exception as e:
                            print(f"Error setting battery_var: {e}")
                    
                    if new_status is not None:
                        try:
                            display_status = str(new_status)
                            if status_var is not None:
                                status_var.set(display_status)

                            # ตรวจสอบว่า status เปลี่ยนหรือไม่
                            status_changed = (last_status_value != normalized_status)
                            
                            # ตรวจสอบและนับสถานะ fail
                            if normalized_status == "fail":
                                # ถ้าสถานะเปลี่ยนจากค่าอื่นเป็น fail ให้เริ่มนับใหม่
                                if status_changed:
                                    status_fail_count = 1
                                    print(f"Status changed to fail, starting count: {status_fail_count}/{STATUS_FAIL_THRESHOLD}")
                                else:
                                    # ถ้าสถานะยังเป็น fail อยู่ ให้เพิ่มตัวนับ
                                    status_fail_count += 1
                                    print(f"Status=fail detected (count: {status_fail_count}/{STATUS_FAIL_THRESHOLD})")
                                
                                # เมื่อครบ 5 ครั้งติดกัน ให้ส่งคำสั่ง cmd=1
                                if status_fail_count >= STATUS_FAIL_THRESHOLD:
                                    try:
                                        command_data = {"cmd": 1, "message": "init"}
                                        command = json.dumps(command_data) + "\n"
                                        print(f"TX (cmd=1 after {STATUS_FAIL_THRESHOLD} fail): {command.strip()}")
                                        _clear_serial_buffers(ser)
                                        ser.write(command.encode("utf-8"))
                                        ser.flush()
                                        
                                        # แจ้งเตือน: จ่ายยาไม่สำเร็จ (fail ติดกัน 5 ครั้ง)
                                        if notification_callback:
                                            try:
                                                message = (
                                                    "⚠️ [SeniorCare Pro] แจ้งเตือน\n\n"
                                                    f"❌ การจ่ายยาล้มเหลว\n"
                                                    f"สถานะ: ตรวจพบ fail ติดกัน {STATUS_FAIL_THRESHOLD} ครั้ง\n"
                                                    f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                                    f"ระบบได้ส่งคำสั่ง cmd=1 เพื่อลองจ่ายยาอีกครั้ง"
                                                )
                                                notification_callback(
                                                    "cmd_failed",
                                                    f"status_fail_{STATUS_FAIL_THRESHOLD}",
                                                    message
                                                )
                                                # บันทึกประวัติการจ่ายยาล้มเหลว
                                                notification_callback(
                                                    "save_history_failed",
                                                    f"status_fail_{STATUS_FAIL_THRESHOLD}",
                                                    None  # ส่ง None เพื่อบอกว่าเป็น flag สำหรับบันทึกประวัติ
                                                )
                                            except Exception as e:
                                                print(f"Error sending notification: {e}")
                                        
                                        status_fail_count = 0  # รีเซ็ตตัวนับหลังจากส่งคำสั่ง
                                    except Exception as e:
                                        print(f"Error sending cmd=1 command: {e}")
                            else:
                                # ถ้าสถานะไม่ใช่ fail
                                if status_changed and last_status_value == "fail":
                                    # ส่ง reset_data เมื่อสถานะเปลี่ยนจาก fail เป็นค่าอื่น
                                    try:
                                        command_data = {"cmd": 1, "message": "reset_data"}
                                        command = json.dumps(command_data) + "\n"
                                        print(f"TX (reset_data after fail): {command.strip()}")
                                        _clear_serial_buffers(ser)
                                        ser.write(command.encode("utf-8"))
                                        ser.flush()
                                    except Exception as e:
                                        print(f"Error sending reset_data command: {e}")
                                    
                                    # แจ้งเตือน: จ่ายยาสำเร็จหลังจากล้มเหลว
                                    if notification_callback:
                                        try:
                                            message = (
                                                "✅ [SeniorCare Pro] แจ้งเตือน\n\n"
                                                f"✅ การจ่ายยาสำเร็จ\n"
                                                f"สถานะ: เปลี่ยนจาก fail เป็น {display_status}\n"
                                                f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                                f"ระบบได้จ่ายยาสำเร็จหลังจากที่ล้มเหลวก่อนหน้านี้"
                                            )
                                            notification_callback(
                                                "cmd_success",
                                                f"status_recovered_{display_status}",
                                                message
                                            )
                                        except Exception as e:
                                            print(f"Error sending recovery notification: {e}")
                                
                                # แจ้งเตือนเมื่อสถานะ complete (จ่ายยาสำเร็จ)
                                if normalized_status == "complete" and status_changed:
                                    if notification_callback:
                                        try:
                                            message = (
                                                "✅ [SeniorCare Pro] แจ้งเตือน\n\n"
                                                f"✅ การจ่ายยาสำเร็จ\n"
                                                f"สถานะ: {display_status}\n"
                                                f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                                f"ระบบได้จ่ายยาสำเร็จตามปกติ"
                                            )
                                            notification_callback(
                                                "cmd_success",
                                                "status_complete",
                                                message
                                            )
                                        except Exception as e:
                                            print(f"Error sending success notification: {e}")
                                
                                # รีเซ็ตตัวนับเมื่อสถานะไม่ใช่ fail
                                if status_fail_count > 0:
                                    print(f"Status changed from fail to {display_status}, resetting count")
                                    status_fail_count = 0
                                
                                if normalized_status in {"complete", "fail", "nopush"}:
                                    dontpick_sos_triggered = False
                            
                            # อัพเดต last_status_value
                            last_status_value = normalized_status
                        except Exception as e:
                            print(f"Error setting status_var: {e}")
                elif isinstance(received_data, str):
                    normalized_special = received_data.strip()
                    lower_special = normalized_special.lower()

                    dontpick_match = re.match(r"dontpick(\d+)", lower_special)
                    if dontpick_match:
                        try:
                            dontpick_count = int(dontpick_match.group(1))
                        except (TypeError, ValueError):
                            dontpick_count = 0

                        if dontpick_count == 1:
                            dontpick_sos_triggered = False

                        print(f"Received dontpick count: {dontpick_count}")

                        if status_var is not None:
                            try:
                                status_var.set(normalized_special)
                            except Exception as e:
                                print(f"Error setting status_var with dontpick: {e}")

                        if (
                            dontpick_count >= DONT_PICK_THRESHOLD
                            and not dontpick_sos_triggered
                        ):
                            dontpick_identifier = f"dontpick_{dontpick_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            message = (
                                "🚨 [SeniorCare Pro] แจ้งเตือน\n\n"
                                "❗ ผู้ป่วยยังไม่มารับยา\n"
                                f"จำนวนรอบที่ไม่รับยา: {dontpick_count}/{DONT_PICK_THRESHOLD}\n"
                                f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                "ระบบจะเริ่มการโทร SOS อัตโนมัติ"
                            )
                            if notification_callback:
                                try:
                                    notification_callback(
                                        "dontpick_threshold",
                                        dontpick_identifier,
                                        message
                                    )
                                    notification_callback(
                                        "trigger_sos_call",
                                        dontpick_identifier,
                                        None
                                    )
                                except Exception as e:
                                    print(f"Error handling dontpick notification: {e}")
                            dontpick_sos_triggered = True

                        last_special_message = normalized_special
                        continue

                    if last_special_message == normalized_special:
                        continue

                    last_special_message = normalized_special
                    # ข้อความพิเศษจาก ESP32 (เช่น "rehome_sent", "cmd_1_sent", "waiting")
                    print(f"Received special message: {received_data}")
                    
                    if status_var is not None:
                        try:
                            # อัพเดต status_var ด้วยข้อความพิเศษ
                            status_var.set(received_data)
                        except Exception as e:
                            print(f"Error setting status_var with special message: {e}")

            # ตรวจสอบเวลาจ่ายยาและส่งคำสั่งเมื่อถึงเวลา
            with _schedule_lock:
                schedule_times = list(allTime)

            now_dt = datetime.now()

            for schedule_str in schedule_times:
                schedule_dt = _parse_schedule_time(schedule_str)
                if schedule_dt is None:
                    continue

                has_explicit_date = "-" in schedule_str

                if not has_explicit_date:
                    if schedule_dt + timedelta(seconds=command_tolerance_after_sec) < now_dt:
                        schedule_dt += timedelta(days=1)

                diff = (now_dt - schedule_dt).total_seconds()
                schedule_key = schedule_dt.strftime("%Y-%m-%d %H:%M:%S")

                if (
                    command_tolerance_before_sec <= diff <= command_tolerance_after_sec
                    and schedule_key not in _triggered_schedule_keys
                ):
                    try:
                        command_data = {"cmd": 1, "message": "init"}
                        command = json.dumps(command_data) + "\n"
                        print(f"TX (scheduled): {command.strip()} at {schedule_key}")
                        _clear_serial_buffers(ser)
                        ser.write(command.encode("utf-8"))
                        ser.flush()
                        
                        # แจ้งเตือน: ส่งคำสั่งตาม schedule
                        if notification_callback:
                            try:
                                message = (
                                    "⏰ [SeniorCare Pro] แจ้งเตือน\n\n"
                                    f"✅ ส่งคำสั่งจ่ายยาตามเวลา\n"
                                    f"เวลาที่กำหนด: {schedule_str}\n"
                                    f"เวลาที่ส่ง: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                    f"ระบบได้ส่งคำสั่งจ่ายยาตามเวลาที่กำหนดไว้"
                                )
                                notification_callback(
                                    "schedule_triggered",
                                    schedule_key,
                                    message
                                )
                            except Exception as e:
                                print(f"Error sending schedule notification: {e}")
                        
                        with _schedule_lock:
                            _triggered_schedule_keys.add(schedule_key)
                    except Exception as e:
                        print(f"Error sending scheduled command: {e}")
                        # แจ้งเตือน: ส่งคำสั่งตาม schedule ไม่สำเร็จ
                        if notification_callback:
                            try:
                                message = (
                                    "❌ [SeniorCare Pro] แจ้งเตือน\n\n"
                                    f"❌ ส่งคำสั่งจ่ายยาตามเวลาไม่สำเร็จ\n"
                                    f"เวลาที่กำหนด: {schedule_str}\n"
                                    f"เวลาเกิดข้อผิดพลาด: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                    f"ข้อผิดพลาด: {str(e)}"
                                )
                                notification_callback(
                                    "schedule_failed",
                                    schedule_key,
                                    message
                                )
                            except Exception as e2:
                                print(f"Error sending schedule error notification: {e2}")
                    break
            
            # รอสักครู่เพื่อไม่ให้ busy loop
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Serial loop stopped by user")
    except Exception as e:
        print(f"Unhandled error in serial loop: {e}")
    finally:
        ser.close()
        print("Serial port closed")


def open_serial_connection(port=None, baudrate=None):
    """เปิด Serial connection ไปหา ESP32 (boand)
    
    Args:
        port: Serial port (default: "/dev/serial0")
        baudrate: Baud rate (default: 115200)
    
    Returns:
        serial.Serial: Serial port object หรือ None ถ้าเกิดข้อผิดพลาด
    """
    if port is None:
        port = DEFAULT_SERIAL_PORT
    if baudrate is None:
        baudrate = DEFAULT_BAUDRATE
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # รอให้ serial port พร้อม
        print(f"Serial port opened: {port} at {baudrate} baud")
        return ser
    except serial.SerialException as e:
        print(f"Serial error at open: {e}")
        return None

