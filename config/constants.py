import os

# Base paths
# Assuming this file is in d:\test\GUI-SeniorCare-Pro\config\constants.py
# and we want to reference the project root or relative paths.
# In main.py: SONG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "song")
# Since we are moving this to config/, we need to adjust or keep it relative to project root.
# Let's define PROJECT_ROOT relative to this file.
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CONFIG_DIR)

SONG_DIR = os.path.join(PROJECT_ROOT, "song")

VOICE_PROMPTS = {
    "complete": {"text": "จ่ายยาสำเร็จค่ะ", "filename": "complete.mp3"},
    "dontpick": {"text": "ผู้ป่วยกรุณารับยาด้วยค่ะ", "filename": "dontpick.mp3"},
    "fail": {"text": "ดันยาไม่สำเร็จค่ะ", "filename": "fail.mp3"},
    "fall_alert": {"text": "พบคนล้มค่ะ", "filename": "fall.mp3"},
}

STARTUP_GREETING = {
    "text": "สวัสดีค่ะ ซีเนียร์แคร์โปรพร้อมให้บริการค่ะ",
    "filename": "startup_greeting.mp3",
}

TEST_MODE_EMAIL = "siri@gmail.com"
