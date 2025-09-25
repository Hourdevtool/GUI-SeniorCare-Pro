# sendTimeToPico.py

import serial
import time
from datetime import datetime

allTime = []

def recivetime(Times):
    global allTime
    allTime = [time['time'] for time in Times]
    print("Times updated:", allTime)

def pySerialSendData(ser):
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
    except serial.SerialException as e:
        print("Serial error:", e)
        return False

def start_serial_loop(port="/dev/ttyUSB0", baudrate=115200):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
    except serial.SerialException as e:
        print("Serial error at open:", e)
        return

    sent_times = set()
    try:
        while True:
            currentTime = datetime.now().strftime("%H:%M:%S")
            if currentTime in allTime and currentTime not in sent_times:
                print(f"Time matched: {currentTime}, sending data...")
                success = pySerialSendData(ser)
                if success:
                    sent_times.add(currentTime)
                else:
                    print("Failed to send data")

            if currentTime not in allTime and sent_times:
                sent_times.clear()

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Serial loop stopped by user")
    finally:
        ser.close()
        print("Serial port closed")
