import serial
import time
from datetime import datetime, timedelta
import json
import re
from threading import Lock, Event

# ค่าคงที่สำหรับ Serial port
DEFAULT_SERIAL_PORT = "/dev/serial0"
DEFAULT_BAUDRATE = 115200
DONT_PICK_THRESHOLD = 6
MIN_DONT_PICK_THRESHOLD = 1
MAX_DONT_PICK_THRESHOLD = 6

allTime = []
_receive_buffer = ""
LOG_INCOMPLETE_WARNING = False
_schedule_lock = Lock()
_triggered_schedule_keys = set()
_manual_reset_event = Event()
_instant_dispense_event = Event()
_current_dont_pick_threshold = DONT_PICK_THRESHOLD
def request_reset_data_command():
    """
    แจ้ง Serial loop ให้ส่งคำสั่ง reset_data (cmd=1) หนึ่งครั้ง
    ใช้เมื่อผู้ใช้กดรีเซ็ตจำนวนยาบน UI
    """
    _manual_reset_event.set()


def request_instant_dispense_command():
    """
    แจ้ง Serial loop ให้จ่ายยาทันที (cmd=1, message=init) โดยไม่รอ schedule
    """
    _instant_dispense_event.set()


def get_dont_pick_threshold():
    """คืนค่าจำนวนครั้ง dontpick ที่ต้องรอก่อนโทร SOS"""
    return _current_dont_pick_threshold


def set_dont_pick_threshold(value):
    """
    ปรับจำนวนครั้ง dontpick ที่ต้องรอก่อนโทร SOS (ช่วง 1-6)
    """
    global _current_dont_pick_threshold
    try:
        new_value = int(round(float(value)))
    except (TypeError, ValueError):
        print(f"Warning: Invalid dontpick threshold value: {value}")
        return _current_dont_pick_threshold

    new_value = max(MIN_DONT_PICK_THRESHOLD, min(MAX_DONT_PICK_THRESHOLD, new_value))
    if new_value != _current_dont_pick_threshold:
        _current_dont_pick_threshold = new_value
        print(f"Dontpick SOS threshold updated to {new_value}")
    return _current_dont_pick_threshold


def _get_effective_dont_pick_threshold():
    return max(MIN_DONT_PICK_THRESHOLD, min(MAX_DONT_PICK_THRESHOLD, _current_dont_pick_threshold))


def _send_reset_data_command(ser, cmd_value, reason=""):
    """
    ส่งคำสั่ง reset_data ไปยังบอร์ดด้วย cmd ที่ระบุ
    """
    try:
        command_data = {"cmd": cmd_value, "message": "reset_data"}
        command = json.dumps(command_data) + "\n"
        context = f" ({reason})" if reason else ""
        print(f"TX reset_data{context}: {command.strip()}")
        _clear_serial_buffers(ser)
        ser.write(command.encode("utf-8"))
        ser.flush()
        return True
    except Exception as e:
        print(f"Error sending reset_data command{context}: {e}")
        return False


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
    
def start_Serial_loop(
    port=None,
    baudrate=None,
    battery_var=None,
    status_var=None,
    request_interval=5.0,
    notification_callback=None,
    medicine_count_getter=None,
    sound_callback=None,
):
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
    dontpick_sos_triggered = False
    last_dontpick_count = -1  # เก็บ dontpick_count ล่าสุดเพื่อป้องกันการเล่นเสียงซ้ำ (-1 ให้ dontpick0 เล่นเสียงรอบแรก)
    last_threshold = _get_effective_dont_pick_threshold()  # เก็บ threshold ล่าสุดเพื่อตรวจสอบการเปลี่ยนแปลง
    command_tolerance_after_sec = 60  # ส่งคำสั่งภายใน 60 วินาทีหลังถึงเวลาที่ตั้งไว้
    command_tolerance_before_sec = 0   # ไม่ส่งก่อนเวลาที่ตั้งไว้
    zero_cycle_reset_sent = False  # ป้องกันการส่ง reset_data ซ้ำเมื่อ count = 0
    startup_full_check_pending = True  # ใช้ตรวจสอบเงื่อนไขหลังไฟดับ/รีสตาร์ท
    medicine_count_error_logged = False

    def _get_medicine_count():
        if not callable(medicine_count_getter):
            return None
        nonlocal medicine_count_error_logged
        try:
            value = medicine_count_getter()
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            if not medicine_count_error_logged:
                print(f"Warning: medicine_count_getter returned non-integer value: {value}")
                medicine_count_error_logged = True
            return None
        except Exception as e:
            if not medicine_count_error_logged:
                print(f"Warning: Cannot read medicine count: {e}")
                medicine_count_error_logged = True
            return None

    try:
        while True:
            # === ตรวจสอบเหตุการณ์ reset_data ก่อน ===
            current_count = _get_medicine_count()

            if _instant_dispense_event.is_set():
                _instant_dispense_event.clear()
                try:
                    command_data = {"cmd": 1, "message": "init"}
                    command = json.dumps(command_data) + "\n"
                    print("TX (instant dispense):", command.strip())
                    _clear_serial_buffers(ser)
                    ser.write(command.encode("utf-8"))
                    ser.flush()
                except Exception as e:
                    print(f"Error sending instant dispense command: {e}")

            if _manual_reset_event.is_set():
                _manual_reset_event.clear()
                if _send_reset_data_command(ser, 1, reason="ui_manual_reset"):
                    zero_cycle_reset_sent = False  # เริ่มรอบใหม่หลังรีเซ็ต

            if startup_full_check_pending and current_count is not None:
                startup_full_check_pending = False
                if current_count == 28:
                    _send_reset_data_command(ser, 1, reason="startup_full_tray")

            if current_count is not None:
                if current_count == 0:
                    if not zero_cycle_reset_sent:
                        if _send_reset_data_command(ser, 0, reason="cycle_complete"):
                            zero_cycle_reset_sent = True
                else:
                    zero_cycle_reset_sent = False

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
                            
                            # ✅ ตรวจสอบ dontpick pattern ใน JSON status field
                            status_str = str(new_status).strip().lower()
                            dontpick_match = re.match(r"dontpick(\d+)", status_str)
                            
                            if dontpick_match:
                                # พบ dontpick ใน JSON payload
                                try:
                                    dontpick_count = int(dontpick_match.group(1))
                                except (TypeError, ValueError):
                                    dontpick_count = 0

                                if dontpick_count == 1:
                                    dontpick_sos_triggered = False

                                print(f"🔍 JSON: Received dontpick count: {dontpick_count}")

                                # เล่นเสียง dontpick เมื่อพบ dontpick status (เล่นทุกครั้งที่ dontpick_count เปลี่ยน)
                                if dontpick_count >= 0 and dontpick_count != last_dontpick_count:
                                    if sound_callback:
                                        try:
                                            sound_callback("dontpick")
                                            print(f"🔊 Playing dontpick sound (count: {dontpick_count})")
                                        except Exception as e:
                                            print(f"Error playing dontpick sound: {e}")
                                    last_dontpick_count = dontpick_count

                                current_threshold = _get_effective_dont_pick_threshold()
                                
                                # รีเซ็ต dontpick_sos_triggered เมื่อ threshold เปลี่ยน (สำหรับ test mode)
                                if current_threshold != last_threshold:
                                    print(f"🔄 Threshold changed from {last_threshold} to {current_threshold}, resetting SOS trigger flag")
                                    dontpick_sos_triggered = False
                                    last_threshold = current_threshold
                                
                                print(f"🔍 DEBUG: dontpick_count={dontpick_count}, threshold={current_threshold}, sos_triggered={dontpick_sos_triggered}")
                                
                                if (
                                    dontpick_count >= current_threshold
                                    and not dontpick_sos_triggered
                                ):
                                    print(f"✅ Triggering SOS! (dontpick {dontpick_count} >= threshold {current_threshold})")
                                    dontpick_identifier = f"dontpick_{dontpick_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                    current_time = datetime.now().strftime('%H:%M')
                                    message = (
                                        "❗ [SeniorCare Pro] แจ้งเตือน : ผู้ป่วยไม่รับยา\n"
                                        "━━━━━━━━━━━━━━━━━━\n\n"
                                        f"⏰ เวลา: {current_time} น.\n\n"
                                        f"🩺  จำนวนรอบที่ไม่รับยา: {dontpick_count}/{current_threshold}\n\n"
                                        "🚑  ระบบจะเริ่มการโทร SOS อัตโนมัติ"
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
                                
                                # อัพเดต last_status_value
                                last_status_value = normalized_status
                                continue  # ข้ามส่วนอื่นๆ เพราะ handle dontpick แล้ว
                            
                            # ตรวจสอบสถานะ fail
                            if normalized_status == "fail":
                                # ถ้าสถานะเปลี่ยนเป็น fail ให้แจ้งเตือนทันทีและเล่นเสียง
                                if status_changed:
                                    print(f"Status changed to fail. Triggering alert and sound.")
                                    
                                    # 1. เล่นเสียง fail.mp3
                                    if sound_callback:
                                        try:
                                            sound_callback("fail")
                                        except Exception as e:
                                            print(f"Error playing fail sound: {e}")

                                    # 2. แจ้งเตือนทาง LINE
                                    if notification_callback:
                                        try:
                                            current_time = datetime.now().strftime('%H:%M')
                                            message = (
                                                "❌ [SeniorCare Pro] แจ้งเตือน : การดันยาไม่สำเร็จ\n"
                                                "━━━━━━━━━━━━━━━━━━\n\n"
                                                f"⏰ เวลา: {current_time} น.\n\n"
                                                "🔧 กรุณาตรวจสอบเครื่องจ่ายยา"
                                            )
                                            notification_callback(
                                                "cmd_failed",
                                                f"status_fail_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                                message
                                            )
                                            # บันทึกประวัติการจ่ายยาล้มเหลว
                                            notification_callback(
                                                "save_history_failed",
                                                f"status_fail_immediate",
                                                None
                                            )
                                        except Exception as e:
                                            print(f"Error sending notification: {e}")
                                    
                                    # ไม่มีการโทร SOS (ตาม requirement)
                            else:
                                # ถ้าสถานะไม่ใช่ fail
                                # แจ้งเตือนเมื่อสถานะ complete (จ่ายยาสำเร็จ)
                                if normalized_status == "complete" and status_changed:
                                    # รีเซ็ต last_dontpick_count เมื่อสถานะเปลี่ยนเป็น complete
                                    last_dontpick_count = -1
                                    if notification_callback:
                                        try:
                                            current_time = datetime.now().strftime('%H:%M')
                                            message = (
                                                "✅ [SeniorCare Pro] แจ้งเตือน : การจ่ายยาสำเร็จ\n"
                                                "━━━━━━━━━━━━━━━━━━\n\n"
                                                f"⏰ เวลา: {current_time} น.\n\n"
                                                "💊 ระบบจ่ายยาเรียบร้อยแล้ว"
                                            )
                                            notification_callback(
                                                "cmd_success",
                                                "status_complete",
                                                message
                                            )
                                        except Exception as e:
                                            print(f"Error sending success notification: {e}")
                                
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

                        # เล่นเสียง dontpick เมื่อพบ dontpick status (เล่นทุกครั้งที่ dontpick_count เปลี่ยน)
                        if dontpick_count >= 0 and dontpick_count != last_dontpick_count:
                            if sound_callback:
                                try:
                                    sound_callback("dontpick")
                                    print(f"🔊 Playing dontpick sound (count: {dontpick_count})")
                                except Exception as e:
                                    print(f"Error playing dontpick sound: {e}")
                            last_dontpick_count = dontpick_count

                        if status_var is not None:
                            try:
                                status_var.set(normalized_special)
                            except Exception as e:
                                print(f"Error setting status_var with dontpick: {e}")

                        current_threshold = _get_effective_dont_pick_threshold()
                        
                        # รีเซ็ต dontpick_sos_triggered เมื่อ threshold เปลี่ยน (สำหรับ test mode)
                        if current_threshold != last_threshold:
                            print(f"🔄 Threshold changed from {last_threshold} to {current_threshold}, resetting SOS trigger flag")
                            dontpick_sos_triggered = False
                            last_threshold = current_threshold
                        
                        if (
                            dontpick_count >= current_threshold
                            and not dontpick_sos_triggered
                        ):
                            dontpick_identifier = f"dontpick_{dontpick_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            current_time = datetime.now().strftime('%H:%M')
                            message = (
                                "❗ [SeniorCare Pro] แจ้งเตือน : ผู้ป่วยไม่รับยา\n"
                                "━━━━━━━━━━━━━━━━━━\n\n"
                                f"⏰ เวลา: {current_time} น.\n\n"
                                f"🩺  จำนวนรอบที่ไม่รับยา: {dontpick_count}/{current_threshold}\n\n"
                                "🚑  ระบบจะเริ่มการโทร SOS อัตโนมัติ"
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
                                current_time = datetime.now().strftime('%H:%M')
                                message = (
                                    "✅ [SeniorCare Pro] แจ้งเตือน : จ่ายยาตามเวลาสำเร็จ\n"
                                    "━━━━━━━━━━━━━━━━━━\n\n"
                                    f"⏰ เวลา: {current_time} น.\n\n"
                                    "💊 ระบบได้ส่งคำสั่งจ่ายยาตามเวลาที่กำหนดไว้"
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
                                current_time = datetime.now().strftime('%H:%M')
                                message = (
                                    "🚨 [SeniorCare Pro] แจ้งเตือน : จ่ายยาตามเวลาไม่สำเร็จ\n"
                                    "━━━━━━━━━━━━━━━━━━\n\n"
                                    f"⏰ เวลา: {current_time} น.\n\n"
                                    "🔧 ระบบไม่สามารถจ่ายยาตามเวลาที่กำหนดไว้"
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

