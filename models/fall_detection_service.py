import cv2
import numpy as np
import joblib
import time
import os
import multiprocessing
import pygame
from ultralytics import YOLO
from lib.alert import sendtoLine
from flexmessage.fall_alert import generate_fall_alert_message
from config.constants import SONG_DIR, VOICE_PROMPTS

# --- Configuration ---
YOLO_PATH = os.path.join("Tools", "yolov8n-pose.pt")
RF_PATH = os.path.join("Tools", "fall_detect_model.pkl")
CONF_THRESHOLD = 0.7 
FALL_TIME_THRESHOLD = 3.0 # seconds
DEBUG_MODE = False # Hardcode to True/False as requested
AI_ENABLED = False # Hardcode to Enable/Disable the AI Service

def play_audio(filename):
    """Play audio carefully avoiding conflicts."""
    try:
        # Re-init mixer to be safe in this process
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        filepath = os.path.join(SONG_DIR, filename)
        if os.path.exists(filepath):
            if not pygame.mixer.music.get_busy():
                 pygame.mixer.music.load(filepath)
                 pygame.mixer.music.play()
    except Exception as e:
        print(f"[FallService-Audio] Error: {e}")

def stop_audio():
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass

def falldetection_worker(is_running_flag, user_line_token, user_line_group_id):
    """
    Worker process for Fall Detection.
    """
    print("[FallService] Worker Started.")
    
    # Load Models
    try:
        pose_model = YOLO(YOLO_PATH)
        fall_model = joblib.load(RF_PATH)
        print("[FallService] Models loaded successfully.")
    except Exception as e:
        print(f"[FallService] Error loading models: {e}")
        return

    # Open Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FallService] ❌ Cannot open camera.")
        return

    fall_start_time = None
    is_fall_active = False # State to track if we are currently in a "Fall" state
    line_notified = False # To ensure we notify LINE only once per fall event

    while is_running_flag.value:
        ret, frame = cap.read()
        if not ret:
            print("[FallService] Camera read failed. Retrying...")
            time.sleep(1)
            continue
            
        # Optimization: Resize for faster processing if needed, but YOLOv8 is usually fast enough on resize
        # frame = cv2.resize(frame, (640, 480))

        # Run Inference
        results = pose_model(frame, verbose=False, conf=CONF_THRESHOLD)
        
        current_is_falling = False
        debug_txt = "Normal"
        ai_confidence = 0.0

        if results[0].keypoints is not None and len(results[0].keypoints) > 0:
            # Draw Skeleton (only needed for Debug, but nice to have ready)
            if DEBUG_MODE:
                frame = results[0].plot()

            # Extract Keypoints
            kpts = results[0].keypoints.xyn[0].cpu().numpy()
            row = kpts.flatten().tolist()
            
            # Predict
            try:
                prediction = fall_model.predict([row])[0]
                prob = fall_model.predict_proba([row])[0]
                ai_confidence = prob[prediction]
            except Exception as e:
                print(f"[FallService] Prediction Error: {e}")
                prediction = 0
                ai_confidence = 0

            # --- Logic from ai.py ---
            box = results[0].boxes.xywh[0].cpu().numpy()
            w, h = box[2], box[3]
            aspect_ratio = w / h
            
            # Checking logic
            if aspect_ratio < 0.90:
                current_is_falling = False
                debug_txt = f"Geo: Force Normal (Standing {aspect_ratio:.2f})"
            else:
                 # Leaning or Lying down
                if prediction == 1: # Model says Fall
                    if ai_confidence > 0.6:
                         current_is_falling = True
                         debug_txt = f"AI: Fall ({ai_confidence*100:.0f}%)"
                    else:
                        if aspect_ratio > 1.5:
                            current_is_falling = True
                            debug_txt = "Geo: Fall (AI Low Conf)"
                        else:
                            current_is_falling = False
                            debug_txt = "AI: Unsure -> Normal"
                else: # Model says Normal
                    if aspect_ratio > 2.0:
                        current_is_falling = True
                        debug_txt = "Geo: Force Fall (Flat)"
                    else:
                        current_is_falling = False
                        debug_txt = f"AI: Normal ({ai_confidence*100:.0f}%)"
        else:
             debug_txt = "No Person"

        # --- Fall Duration Logic ---
        if current_is_falling:
            if fall_start_time is None:
                fall_start_time = time.time()
            
            duration = time.time() - fall_start_time
            if duration > FALL_TIME_THRESHOLD:
                is_fall_active = True
                debug_txt = "!!! FALL CONFIRMED !!!"
        else:
            fall_start_time = None
            is_fall_active = False
            line_notified = False # Reset notification flag when back to normal
            stop_audio() # Stop the alarm

        # --- Actions ---
        if is_fall_active:
            # 1. Voice Alert (Looping handled by play function checking busy)
            play_audio(VOICE_PROMPTS['fall_alert']['filename'])
            
            # 2. LINE Notification (Once)
            if not line_notified:
                print("[FallService] Sending LINE Alert...")
                # Flex Message
                msg = generate_fall_alert_message() 
                sendtoLine(user_line_token, user_line_group_id, msg)
                line_notified = True

        # --- Debug Display ---
        if DEBUG_MODE:
            color = (0, 0, 255) if is_fall_active else (0, 255, 0)
            cv2.putText(frame, f"Status: {debug_txt}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
            if fall_start_time:
                 cv2.putText(frame, f"Time: {time.time() - fall_start_time:.1f}s", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            cv2.imshow('Fall Detection Debug', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
             # Important: If not showing window, we should sleep briefly to reduce CPU usage if needed,
             # but cap.read() usually blocks for defined FPS (e.g. 30fps = 33ms).
             pass

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    stop_audio()
    print("[FallService] Worker Stopped.")
