import customtkinter as ctk
import requests
import random
import string
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from lib.alert import sendtoLine
from flexmessage.sosalert import generateflexmessage

KIOSK_NAME = "เครื่องจ่ายยาอัตโนมัติ" 



driver = None 

def generate_random_room():
    rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"https://meet.jit.si/SOS-Call-{rand_str}"

def press_sos_automation(token, group_id): # (แก้ typo gruop_id -> group_id)
    global driver
    call_url = generate_random_room()
    send_status = None 
    driver = None # ⭐️ [แก้ไข] เริ่มต้น driver เป็น None ที่นี่

    try:
        # 1. ตั้งค่า Selenium (เหมือนเดิม)
        options = Options() 
        
        driver = webdriver.Firefox(options=options)
        
        # 2. ย้ายหน้าต่างไปซ่อนนอกจอระหว่างโหลด
        print("กำลังซ่อนหน้าต่างชั่วคราว...")
        driver.set_window_position(-3000, 0)
        
        # 3. เปิดหน้าเว็บ Jitsi (นอกจอ)
        driver.get(call_url)
        print("เบราว์เซอร์เปิดแล้ว (นอกจอ) กำลังเข้าร่วม...")

        # 4. รอ, พิมพ์ชื่อ, และกด Join (หน้า Pre-join)
        wait = WebDriverWait(driver, 15)
        
        print("กำลังค้นหาช่องใส่ชื่อ...")
        name_field = wait.until(
            EC.element_to_be_clickable((By.ID, "premeeting-name-input"))
        )
        name_field.send_keys(KIOSK_NAME)
        print("พิมพ์ชื่อสำเร็จ")
        
        print("กำลังค้นหาปุ่ม Join...")
        join_button = driver.find_element(By.CSS_SELECTOR, "div[data-testid='prejoin.joinMeeting']")
        join_button.click()
        print("เข้าร่วมคอลสำเร็จ (นอกจอ)!")

        # 5. ส่ง LINE (ทำทันที)
        message = generateflexmessage(call_url)

        print(call_url)
        # ⭐️ [แก้ไข] ใช้ค่าที่ถูกต้องจากตัวแปร
        
        send_status = sendtoLine(token, group_id, message)

        # 6. ย้ายหน้าต่างกลับมาที่หน้าจอ
        print("กำลังแสดงผลหน้าต่างวิดีโอคอล...")
        time.sleep(2) # รอ 2 วินาที ให้ UI นิ่ง
        driver.set_window_position(0, 0)
        driver.maximize_window()

        # 7. ตั้งค่าตัวแปรสำหรับเฝ้าระวัง
        timeout_seconds = 120 
        is_alone = True # ⭐️ เริ่มต้นด้วยสถานะ "อยู่คนเดียว" (เพราะเราเพิ่งเข้า)
        alone_start_time = time.time() # ⭐️ เริ่มจับเวลา 5 นาที "ทันที"

        print(f"Starting {timeout_seconds}-second inactivity monitor...")
        
        # 8. เริ่ม Loop เฝ้าระวัง
        while True:
            current_participant_count = 1 # ⭐️ ตั้งค่าเริ่มต้นใน Loop ว่า "อยู่คนเดียว"
            
            try:
                # 8a. ตรวจสอบว่าเบราว์เซอร์ยังเปิดอยู่หรือไม่
                if not driver.window_handles:
                    print("Browser was closed manually.")
                    break 

                js_code = """
                    var videoElements = document.querySelectorAll('.filmstrip__videos .videocontainer');
                    if (videoElements.length === 0) {
                        videoElements = document.querySelectorAll('.tile-view-container .videocontainer');
                    }
                    return videoElements.length;
                    """
                count = driver.execute_script(js_code)

                if isinstance(count, int) and count >= 1:
                 current_participant_count = count
                else:
                    current_participant_count = 1
            
                print(f"✅ จำนวนผู้เข้าร่วมที่หาเจอ (Via JS DOM Count): {current_participant_count}")
            except Exception as e:
                # 8e. ⭐️ [FIX] ถ้าหาปุ่มไม่เจอ (NoSuchElementException) = เรายังอยู่ใน Lobby
                print(f"❌ Error accessing Jitsi API: {e}. Assuming 1 participant.")
                current_participant_count = 1 # ⭐️ คงสถานะ "อยู่คนเดียว"
            
            # 9. ⭐️ [FIX] ย้าย Logic การจับเวลาและ sleep ให้ออกมาอยู่นอก try/except
            # (เพื่อให้มันทำงานทุกรอบ ไม่ว่าจะหาปุ่มเจอหรือไม่)
            
            if current_participant_count <= 1:
                # --- เราอยู่คนเดียว หรือยังอยู่ใน Lobby ---
                if not is_alone:
                    # (เพิ่งกลายเป็นอยู่คนเดียว)
                    print("Kiosk is now alone. Starting 5-minute timeout.")
                    is_alone = True
                    alone_start_time = time.time()
                else:
                    # (ยังคงอยู่คนเดียว/อยู่ใน Lobby)
                    elapsed = time.time() - alone_start_time
                    if elapsed > timeout_seconds:
                        print(f"Alone (or in lobby) for {timeout_seconds} seconds. Closing call.")
                        break 
                    else:
                        print(f"Still alone for {int(elapsed)} seconds... (Closing in {int(timeout_seconds - elapsed)}s)")
            else:
                # --- มีคนอื่นอยู่ด้วย (Count > 1) ---
                if is_alone:
                    print(f"Participant joined (Total: {current_participant_count}). Resetting timer.")
                is_alone = False
                alone_start_time = None # ⭐️ รีเซ็ต/หยุด ตัวจับเวลา

            time.sleep(15) # ⭐️ ตรวจสอบทุก 15 วินาที

    except Exception as e:
        print(f"เกิดข้อผิดพลาดร้ายแรงในกระบวนการ SOS: {e}")
        
    finally:
        print("Call finished or timed out. Closing browser.")
        if driver:
            driver.quit() 
        return send_status


