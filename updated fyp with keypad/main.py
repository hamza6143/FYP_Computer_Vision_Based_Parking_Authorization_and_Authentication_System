import serial
import cv2
import easyocr
import numpy as np
import re
import os
import ssl
import sqlite3
import time
from datetime import datetime

# --- 1. INITIALIZATION & SSL FIX ---
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

reader = easyocr.Reader(['en'], gpu=False)

# --- 2. CONFIGURATION ---
DB_NAME = r'C:\Users\User\Desktop\codes\fyp\parking_system.db' 
BLACKLIST = ["SINDH", "PAKISTAN", "GOVT", "PUNJAB"]
ZOOM_FACTOR = 1.5  # Locked at 1.5x zoom globally

# --- 3. DATABASE SETUP & AUTOMATIC MIGRATION ---
def init_db():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS authorized_users 
                      (uid TEXT PRIMARY KEY, plate_number TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS access_logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       uid TEXT, plate_text TEXT, timestamp TEXT, status TEXT)''')
    
    cursor.execute("PRAGMA table_info(authorized_users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "is_inside" not in columns:
        cursor.execute("ALTER TABLE authorized_users ADD COLUMN is_inside INTEGER DEFAULT 0")
        conn.commit()

    raw_records = [
        ('4C 3A 73 06', 'BVS 406'),
        ('22 D7 07 5B', 'AFR 024'),
        ('99 65 F5 04', 'ABC 1234'),
        ('D7 ED C5 01', 'LE 0161'),
        ('19 38 93 03', 'ABC 4321'),
        ('2A E8 15 C0', 'KLM 9876'),
        ('F5 A3 66 BB', 'A 500'),
        ('F5 ED 67 BB', 'B 888'),
        ('5A 34 66 C0', 'XYZ 6754'),
        ('CB 60 92 03', 'PQR 2024 55'),
        ('F5 84 6A BB', 'STU 2024 19'),
        ('F3 E8 90 03', 'VWX 2023 72'),
        ('79 77 92 03', 'YZA 2023 31'),
        ('25 DE 93 03', 'BCD 2024 90'),
        ('7E 4E 0F 06', 'EFG 2024 04'),
    ]
    cleaned_records = [(r[0].replace(" ", "").upper(), r[1]) for r in raw_records]
    cursor.executemany("INSERT OR IGNORE INTO authorized_users (uid, plate_number) VALUES (?, ?)", cleaned_records)
    conn.commit()
    conn.close()
    print("✅ Parking Database successfully synced.")

# --- 4. ZOOM HELPER ---
def apply_zoom(frame, zoom):
    """Crops the center of the frame and resizes it back to simulate a permanent digital zoom."""
    if zoom == 1.0:
        return frame
    h, w = frame.shape[:2]
    cw, ch = int(w / zoom), int(h / zoom)
    x1, y1 = int((w - cw) / 2), int((h - ch) / 2)
    cropped = frame[y1:y1+ch, x1:x1+cw]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

def clean_and_filter(text):
    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    if clean_text in BLACKLIST or len(clean_text) < 2:
        return None
    return clean_text

def log_to_db(uid, plate, status):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO access_logs (uid, plate_text, timestamp, status) VALUES (?, ?, ?, ?)",
                       (uid, plate, now, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Database Logging Error: {e}")

def perform_ajrak_ocr(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 71, 15)
    results = reader.readtext(thresh)
    detected_parts = []
    for (bbox, text, prob) in results:
        filtered = clean_and_filter(text)
        if filtered and prob > 0.30:
            detected_parts.append(filtered)
    return " ".join(detected_parts)

def verify_and_respond(uid, frame, location_label):
    try:
        uid_to_check = uid.replace(" ", "").upper()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT plate_number, is_inside FROM authorized_users WHERE uid=?", (uid_to_check,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ ACCESS DENIED ({location_label}): Unregistered Card")
            if arduino: arduino.write(b'D') 
            log_to_db(f"{uid_to_check}_{location_label}", "N/A", "DENIED_UNREGISTERED")
            conn.close()
            return

        expected_plate, is_inside = result
        ocr_text = perform_ajrak_ocr(frame)  # Processes the stable zoomed frame
        ocr_clean = ocr_text.replace(" ", "").upper()
        expected_clean = expected_plate.replace(" ", "").upper()
        
        print(f"\n📡 Reader: {location_label} | Registered Vehicle: {expected_plate}")

        # --- ANTI-PASSBACK RULE ENFORCEMENT ---
        if location_label == "OUTER" and is_inside == 1:
            print(f"❌ PASSBACK VIOLATION: {expected_plate} is already inside the lot.")
            if arduino: arduino.write(b'D')
            log_to_db(uid_to_check, ocr_text if ocr_text else "NO_READ", "DENIED_PASSBACK_ENTRY")
            conn.close()
            return
            
        elif location_label == "INNER" and is_inside == 0:
            print(f"❌ PASSBACK VIOLATION: {expected_plate} is already outside the lot.")
            if arduino: arduino.write(b'D')
            log_to_db(uid_to_check, ocr_text if ocr_text else "NO_READ", "DENIED_PASSBACK_EXIT")
            conn.close()
            return

        # --- VEHICLE LICENSE PLATE MATCHING ---
        if expected_clean in ocr_clean:
            print(f"✅ ACCESS GRANTED: Opening gate for {expected_plate}")
            if arduino: arduino.write(b'G') 
            
            new_inside_status = 1 if location_label == "OUTER" else 0
            cursor.execute("UPDATE authorized_users SET is_inside=? WHERE uid=?", (new_inside_status, uid_to_check))
            conn.commit()
            
            status = f"GRANTED_{location_label}"
        else:
            print(f"❌ ACCESS DENIED: Plate mismatch. Expected {expected_plate}, got '{ocr_clean}'")
            if arduino: arduino.write(b'D')
            status = f"DENIED_PLATE_MISMATCH_{location_label}"

        log_to_db(uid_to_check, ocr_text if ocr_text else "NO_READ", status)
        conn.close()
        
    except Exception as e:
        print(f"❌ Core System Error: {e}")

# --- 5. HARDWARE SETUP ---
init_db()
arduino = None
try:
    arduino = serial.Serial(port='COM5', baudrate=9600, timeout=.1)
    time.sleep(2)
    print("✅ Arduino Connected on COM5.")
except Exception as e:
    print(f"⚠️ Warning: Arduino Connection Failed: {e}")

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Critical Error: Could not open camera.")
    exit()

# --- 6. MAIN LOOP ---
print("\n--- PARKING SYSTEM ACTIVE (1.5x ALWAYS-ON ZOOM) ---")

while True:
    ret, raw_frame = cap.read()
    if not ret: break

    frame = apply_zoom(raw_frame, ZOOM_FACTOR)
    cv2.imshow('Live Feed (1.5x Zoom)', frame)
    key = cv2.waitKey(1) & 0xFF

    if arduino and arduino.in_waiting > 0:
        raw_data = arduino.readline().decode('utf-8', errors='ignore').strip()
        
        if raw_data == "EMERGENCY_OVERRIDE_ON":
            print("\n🚨 EMERGENCY BYPASS: Keypad turned ON. Gate Locked Open.")
            log_to_db("KEYPAD_BYPASS", "BYPASS_ON", "EMERGENCY_OPEN")
            arduino.reset_input_buffer()
            
        elif raw_data == "EMERGENCY_OVERRIDE_OFF":
            print("\n🔒 EMERGENCY BYPASS: Keypad turned OFF. System Scanning Restored.")
            log_to_db("KEYPAD_BYPASS", "BYPASS_OFF", "EMERGENCY_CLOSE")
            arduino.reset_input_buffer()
        
        elif raw_data.startswith("OUTER_") or raw_data.startswith("INNER_"):
            location = "OUTER" if raw_data.startswith("OUTER_") else "INNER"
            uid = raw_data.replace("OUTER_", "").replace("INNER_", "")
            
            print(f"\n⏳ Card detected on {location} reader. Waiting for camera to settle...")
            
            # 1. Wait for physical servo rotation to complete
            time.sleep(2) 
            
            # 2. Flush old buffered frames out of OpenCV's memory pipeline
            for _ in range(5):
                cap.read()
                
            # 3. Grab a perfectly still, updated frame
            ret, fresh_raw = cap.read()
            if ret:
                stable_frame = apply_zoom(fresh_raw, ZOOM_FACTOR)
                verify_and_respond(uid, stable_frame, location)
            else:
                # Fallback to loop's last frame if hardware read fails
                verify_and_respond(uid, frame, location)
                
            arduino.reset_input_buffer()

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()