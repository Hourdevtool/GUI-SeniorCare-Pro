import serial
import time
from datetime import datetime
import json


allTime = []


def recivetime(Times):
    allTime = [time["time"] for time in Times]
    print("Times updated:", allTime)


def pySerialSendData(ser):
    try:
        data = {
            "cmd": 1,
        }
        command = json.dumps(data) + "\n"
        ser.write(command)
        return True
    except serial.SerialException as e:
        print("Serial error (send):", e)
        return False
    

def pySerialReceiveData(ser):
    try:
        line= ser.readline().decode('uft-8').strip()
        if line:
            try:
                data = json.loads(line)
                return data
            except json.JSONDecodeError:
                print(f"Received non-JSON data: {line}")
                return None
    except Exception as e:
        print(f"Receive error: {e}")
        return None
    
def start_Serial_loop(port, baudrate,battery_var,status_var):

    try:
        ser = serial.Serial(port,baudrate, timeout = 1)
        time.sleep(2)
    except serial.SerialException as e:
        print("Serial error at open:", e) 
        return
    
    sent_times = set()

    try:
        while True:
            if ser.in_waiting > 0:
                received_data = pySerialReceiveData(ser)

                if received_data:
                    print(f"Received data: {received_data}")
                    battery_level = received_data.get("battery")
                    new_status = received_data.get("status")

                    if battery_level is not None:
                        battery_var.set(battery_level)
                    
                    if new_status is not None:
                        status_var.set(str(new_status))
            
            currentTime = datetime.now().strftime("%H:%M:%S")
            if currentTime in allTime and currentTime not in sent_times:
                success = pySerialSendData(ser)
                if success :
                    sent_times.add(currentTime)
                else:
                    print("Failed to send data")
            
            if currentTime not in allTime and sent_times:
                sent_times.clear()
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("Serial loop stopped by user")
    except Exception as e:
        print(f"Unhandled error in serial loop: {e}")
    finally:
        ser.close()
        print("Serial port closed")



