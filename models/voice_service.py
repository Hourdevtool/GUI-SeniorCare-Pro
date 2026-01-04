import os
import threading
from gtts import gTTS
from pygame import mixer
from config.constants import SONG_DIR, VOICE_PROMPTS, STARTUP_GREETING

class VoicePromptPlayer:
    def __init__(self, song_dir=SONG_DIR):
        self.song_dir = song_dir
        os.makedirs(self.song_dir, exist_ok=True)
        self._lock = threading.Lock()

    def ensure_startup_greeting(self):
        """สร้างไฟล์เสียงต้อนรับเมื่อเปิดระบบครั้งแรก"""
        file_path = os.path.join(self.song_dir, STARTUP_GREETING["filename"])
        if os.path.exists(file_path):
            return file_path
        try:
            print("[VoicePrompt] Creating startup greeting audio")
            tts = gTTS(text=STARTUP_GREETING["text"], lang='th')
            tts.save(file_path)
        except Exception as e:
            print(f"[VoicePrompt] Failed to create startup greeting: {e}")
        return file_path

    def _ensure_file(self, key):
        data = VOICE_PROMPTS[key]
        file_path = os.path.join(self.song_dir, data["filename"])
        if not os.path.exists(file_path):
            try:
                print(f"[VoicePrompt] Creating audio for '{data['text']}'")
                tts = gTTS(text=data["text"], lang='th')
                tts.save(file_path)
            except Exception as e:
                print(f"[VoicePrompt] Failed to create '{key}': {e}")
                raise
        return file_path

    def _play_file(self, file_path):
        try:
            if not mixer.get_init():
                mixer.init()
        except Exception as e:
            print(f"[VoicePrompt] Cannot init mixer: {e}")
            return

        try:
            mixer.music.stop()
        except Exception:
            pass

        try:
            mixer.music.load(file_path)
            mixer.music.play()
            print(f"[VoicePrompt] Playing {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[VoicePrompt] Cannot play '{file_path}': {e}")

    def play(self, key):
        if key not in VOICE_PROMPTS:
            print(f"[VoicePrompt] Unknown key: {key}")
            return

        def worker():
            try:
                with self._lock:
                    file_path = self._ensure_file(key)
                    self._play_file(file_path)
            except Exception as e:
                print(f"[VoicePrompt] Error while handling '{key}': {e}")

        threading.Thread(target=worker, daemon=True).start()

    def play_startup_greeting(self):
        """เล่นเสียงต้อนรับเมื่อเริ่มระบบ (วันละครั้งต่อการรันแอป)"""

        def worker():
            try:
                with self._lock:
                    file_path = self.ensure_startup_greeting()
                    self._play_file(file_path)
            except Exception as e:
                print(f"[VoicePrompt] Error while playing startup greeting: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def preload_all_prompts(self):
        """สร้างไฟล์เสียงสำหรับทุกสถานะตั้งแต่เริ่มระบบ"""
        try:
            with self._lock:
                for key in VOICE_PROMPTS:
                    try:
                        self._ensure_file(key)
                    except Exception as e:
                        print(f"[VoicePrompt] Failed to preload '{key}': {e}")
        except Exception as e:
            print(f"[VoicePrompt] Error while preloading prompts: {e}")
