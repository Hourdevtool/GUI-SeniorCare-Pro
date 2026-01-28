import customtkinter as ctk
import requests
import random
import string
import time
import os
import platform
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

from lib.alert import sendtoLine
from flexmessage.sosalert import generateflexmessage

KIOSK_NAME = "เครื่องจ่ายยาอัตโนมัติ"


def find_firefox_binary():
    """
    หา Firefox binary path อัตโนมัติ
    รองรับทั้ง Windows และ Linux (Raspberry Pi)
    """
    possible_paths = []
    
    # สำหรับ Linux/Raspberry Pi
    if platform.system() != "Windows":
        possible_paths.extend([
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr",
            "/usr/local/bin/firefox",
            "/opt/firefox/firefox",
            os.path.expanduser("~/firefox/firefox"),
            shutil.which("firefox"),  # ตรวจสอบใน PATH
            shutil.which("firefox-esr"),
        ])
    else:
        # สำหรับ Windows
        possible_paths.extend([
            "firefox.exe",
            shutil.which("firefox.exe"),
            # Windows default locations
            os.path.join(os.environ.get("ProgramFiles", ""), "Mozilla Firefox", "firefox.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Mozilla Firefox", "firefox.exe"),
        ])
    
    # ลบ None ออกจาก list
    possible_paths = [p for p in possible_paths if p]
    
    # ตรวจสอบว่า path ไหนมีไฟล์อยู่จริง
    for path in possible_paths:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"พบ Firefox binary ที่: {path}")
            return path
    
    # ถ้าหาไม่เจอ
    print("ไม่พบ Firefox binary ใน path ที่กำหนด")
    return None


def find_geckodriver():
    """
    หา geckodriver path อัตโนมัติ
    รองรับทั้ง Windows และ Linux (Raspberry Pi)
    """
    # รายการ path ที่อาจมี geckodriver
    possible_paths = []
    
    # สำหรับ Linux/Raspberry Pi
    if platform.system() != "Windows":
        possible_paths.extend([
            "/usr/bin/geckodriver",
            "/usr/local/bin/geckodriver",
            "/opt/geckodriver/geckodriver",
            os.path.expanduser("~/geckodriver"),
            os.path.expanduser("~/.local/bin/geckodriver"),
            shutil.which("geckodriver"),  # ตรวจสอบใน PATH
        ])
    else:
        # สำหรับ Windows
        possible_paths.extend([
            "geckodriver.exe",
            os.path.join(os.getcwd(), "geckodriver.exe"),
            os.path.expanduser("~/geckodriver.exe"),
            shutil.which("geckodriver.exe"),
        ])
    
    # ลบ None ออกจาก list
    possible_paths = [p for p in possible_paths if p]
    
    # ตรวจสอบว่า path ไหนมีไฟล์อยู่จริง
    for path in possible_paths:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"พบ geckodriver ที่: {path}")
            return path
    
    # ถ้าหาไม่เจอ ให้ลองใช้ webdriver-manager หรือให้ Selenium หาเอง
    print("ไม่พบ geckodriver ใน path ที่กำหนด กำลังลองใช้ Selenium auto-detection...")
    return None  # ให้ Selenium หาเอง


def generate_random_room():
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"https://meet.jit.si/SOS-Call-{code}"


def press_sos_automation(token, group_id):
    driver = None
    call_url = generate_random_room()
    send_status = None

    try:
        # -------------------------
        # 📌 1) Firefox Options
        # -------------------------
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # ⭐ เปิด WebRTC & Camera แบบอัตโนมัติ ⭐
        options.set_preference("media.navigator.permission.disabled", True)
        options.set_preference("media.navigator.streams.fake", False)
        options.set_preference("permissions.default.microphone", 1)
        options.set_preference("permissions.default.camera", 1)
        options.set_preference("dom.disable_open_during_load", False)

        # หา Firefox binary path
        firefox_binary_path = find_firefox_binary()
        if firefox_binary_path:
            options.binary_location = firefox_binary_path
        else:
            print("คำเตือน: ไม่พบ Firefox binary จะลองใช้ default path")

        # -------------------------
        # 📌 2) Open Firefox
        # -------------------------
        geckodriver_path = find_geckodriver()
        
        if geckodriver_path:
            service = Service(geckodriver_path)
            driver = webdriver.Firefox(service=service, options=options)
        else:
            # ถ้าหา geckodriver ไม่เจอ ให้ Selenium หาเอง (ต้องติดตั้ง webdriver-manager)
            try:
                # ลองใช้ webdriver-manager ถ้ามี
                from webdriver_manager.firefox import GeckoDriverManager
                service = Service(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            except ImportError:
                # ถ้าไม่มี webdriver-manager ให้ลองใช้โดยไม่ระบุ path
                # Selenium จะพยายามหา geckodriver ใน PATH
                try:
                    driver = webdriver.Firefox(options=options)
                except WebDriverException as e:
                    error_msg = (
                        "ไม่พบ geckodriver หรือ Firefox!\n\n"
                        "วิธีแก้ไข:\n"
                        "1. ติดตั้ง Firefox:\n"
                        "   - Linux/Raspberry Pi: sudo apt-get install firefox-esr\n"
                        "2. ติดตั้ง geckodriver:\n"
                        "   - Linux/Raspberry Pi: sudo apt-get install firefox-geckodriver\n"
                        "   - หรือดาวน์โหลดจาก: https://github.com/mozilla/geckodriver/releases\n"
                        "3. หรือติดตั้ง webdriver-manager:\n"
                        "   pip install webdriver-manager\n"
                    )
                    raise WebDriverException(error_msg) from e

        # -------------------------
        # 📌 3) เปิดที่หน้าจอทันที (ไม่ซ่อน)
        # -------------------------
        driver.set_window_position(0, 0)
        driver.maximize_window()

        print("กำลังเปิดห้อง Jitsi...")
        driver.get(call_url)

        wait = WebDriverWait(driver, 20)

        # -------------------------
        # 📌 4) ใส่ชื่ออัตโนมัติ
        # -------------------------
        name_field = wait.until(EC.element_to_be_clickable((By.ID, "premeeting-name-input")))
        name_field.clear()
        name_field.send_keys(KIOSK_NAME)

        # -------------------------
        # 📌 5) เปิดกล้อง + ไมค์ อัตโนมัติ
        # -------------------------
        time.sleep(1)

        js_enable_media = """
        try {
            const micBtn = document.querySelector('[aria-label="Toggle microphone"]');
            if (micBtn && micBtn.getAttribute("aria-pressed") === "false") micBtn.click();

            const camBtn = document.querySelector('[aria-label="Toggle camera"]');
            if (camBtn && camBtn.getAttribute("aria-pressed") === "false") camBtn.click();
        } catch (e) {}
        """

        driver.execute_script(js_enable_media)

        # -------------------------
        # 📌 6) Join Meeting
        # -------------------------
        join_button = driver.find_element(By.CSS_SELECTOR, "div[data-testid='prejoin.joinMeeting']")
        join_button.click()
        print("เข้าร่วมวิดีโอคอลแล้ว!")

        # -------------------------
        # 📌 7) ส่งแจ้งเตือนไป LINE
        # -------------------------
        flex_msg = generateflexmessage(call_url)
        send_status = sendtoLine(token, group_id, flex_msg)

        # -------------------------
        # 📌 8) ใส่ KIOSK MODE (เต็มหน้าจอ + UI ลดลง)
        # -------------------------
        time.sleep(3)
        js_kiosk = """
        try {
            // Hide filmstrip (ซ่อนแถบวิดีโอข้างล่าง)
            document.querySelector(".filmstrip").style.display = "none";

            // เปิด Immersive Mode (เต็มจอ)
            const immersiveBtn = document.querySelector('[id="toolbar_button__immersive"]');
            if (immersiveBtn) immersiveBtn.click();

            // เปิด Focus Mode (โฟกัสคู่สนทนา)
            const focusBtn = document.querySelector('[id="toolbar_button__videobackgroundblur"]');
            if (focusBtn) focusBtn.click();
        } catch (e) {}
        """

        driver.execute_script(js_kiosk)
        print("เข้า KIOSK MODE เรียบร้อย")

        # -------------------------
        # 📌 9) Inactivity Timer
        # -------------------------
        timeout_seconds = 120
        is_alone = True
        alone_start = time.time()

        while True:
            try:
                if not driver.window_handles:
                    print("ผู้ใช้ปิดหน้าต่างด้วยตัวเอง")
                    break

                js_count = """
                 var videoElements = document.querySelectorAll('.filmstrip__videos .videocontainer');
                    if (videoElements.length === 0) {
                        videoElements = document.querySelectorAll('.tile-view-container .videocontainer');
                    }
                    return videoElements.length;
                """
                count = driver.execute_script(js_count)
                count = int(count) if isinstance(count, int) else 1

                print("จำนวนผู้เข้าร่วม:", count)

                if count <= 1:
                    elapsed = time.time() - alone_start
                    if elapsed >= timeout_seconds:
                        print("อยู่คนเดียวเกิน 2 นาที → ปิดห้อง")
                        break
                else:
                    is_alone = False
                    alone_start = time.time()

                time.sleep(10)

            except Exception as e:
                print("Error:", e)
                break

    except Exception as e:
        print(f"เกิดข้อผิดพลาด SOS: {e}")

    finally:
        print("กำลังปิดเบราว์เซอร์...")
        if driver:
            driver.quit()
        return send_status