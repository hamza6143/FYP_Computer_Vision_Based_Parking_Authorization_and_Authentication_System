# FYP_Computer_Vision_Based_Parking_Authorization_and_Authentication_System

An automated parking management system combining **RFID access control**, **Automatic Number Plate Recognition (ANPR)** via EasyOCR/OpenCV, and an **anti-passback algorithm** to monitor vehicle entry and exit. 

The system runs on a Python backend managing an SQLite database and a computer vision pipeline, communicating via serial with an Arduino microcontroller handling sensors, a motorized gate servo, an operational camera positioning servo, an LCD status display, and an emergency keypad override.

---

## Features

* **Dual-Authentication Layer:** Combines physical RFID card/tag validation with computer vision license plate matching.
* **Anti-Passback Tracking:** Tracks vehicle state (`is_inside` flag) to prevent duplicate entries or exits using the same credentials.
* **Computer Vision & Digital Zoom:** Integrates OpenCV and EasyOCR with an always-on digital zoom and adaptive thresholding pipeline for clearer plate captures.
* **Mechanical Camera Swiveling:** Automatically adjusts the camera angle depending on whether a vehicle is triggering the outer (entry) or inner (exit) reader.
* **Emergency Keypad Bypass:** Allows administrators to manually lock the gate open via an Arduino-connected matrix keypad using a secure code.
* **Persistent Local Logging:** Stores all access attempts, timestamps, and passback or mismatch violations in a local SQLite database.

---

## Hardware Architecture

* **Microcontroller:** Arduino (connected via Serial on `COM5`)
* **RFID Readers:** 2x MFRC522 modules (Outer entry reader on pin 10, Inner exit reader on pin 2, shared reset on pin 9)
* **Actuators & Servos:** 
  * Gate Control Servo (Pin `A0`)
  * Camera Positioning Servo (Pin `A3`)
* **User Interface:** 
  * 16x2 I2C LCD Display (`0x27`)
  * 4x4 Matrix Keypad (Rows: pins 8, 7, 6, 5; Cols: pins 4, 3, `A1`, `A2`)

---

## Software Stack

* **Python 3**
  * `opencv-python` (Frame capture, digital zoom, preprocessing)
  * `easyocr` (Text extraction from license plates)
  * `pyserial` (Serial communication with Arduino)
  * `sqlite3` (Local database storage and tracking)
* **Arduino IDE / C++**
  * `MFRC522`
  * `LiquidCrystal_I2C`
  * `Servo`
  * `Keypad`

---

## Project Structure

```text
├── parking_system.py       # Python backend, DB initialization, and OCR pipeline
├── parking_system.ino      # Arduino firmware for RFID, Servos, LCD, and Keypad
└── parking_system.db       # Local SQLite database (auto-generated on first run)
