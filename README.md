# FYP: Computer Vision Based Parking Authorization and Authentication System

An automated parking management system combining **RFID access control**, **Automatic Number Plate Recognition (ANPR)** using EasyOCR and OpenCV, and an **anti-passback algorithm** to monitor and secure vehicle entry and exit.

The system uses a Python backend with an SQLite database and a computer vision pipeline. It communicates through serial communication with an Arduino microcontroller, which controls RFID readers, a motorized gate servo, a camera positioning servo, an LCD status display, and an emergency keypad override.

---

## Features

- **Dual Authentication:** Combines RFID card/tag validation with computer vision-based license plate recognition to verify both the user and the vehicle.
- **Anti-Passback Tracking:** Uses an `is_inside` status flag to prevent repeated entries or exits using the same credentials without following the correct entry/exit sequence.
- **Computer Vision and Digital Zoom:** Uses OpenCV and EasyOCR with digital zoom and adaptive thresholding to improve license plate image quality and text recognition.
- **Automatic Camera Positioning:** A servo-driven camera bracket changes the camera direction depending on whether the entry or exit RFID reader is triggered.
- **Emergency Keypad Override:** Allows administrators to activate an emergency gate override using a secure code entered through an Arduino-connected matrix keypad.
- **Local Database and Access Logging:** Stores RFID credentials, vehicle registration numbers, timestamps, access attempts, and authentication violations in a local SQLite database.

---

## System Architecture

The system consists of two main parts:

1. **Python Backend:** Handles RFID event processing, camera capture, image preprocessing, license plate recognition, authentication, and database operations.
2. **Arduino Microcontroller:** Manages RFID readers, servo motors, LCD messages, and keypad input.

The Python backend and Arduino communicate through a USB serial connection.

---

## Hardware Components

| Component | Description |
|---|---|
| Arduino | Main microcontroller |
| 2 × MFRC522 RFID Readers | Outer entry and inner exit authentication |
| RFID Cards/Tags | User identification |
| Camera | Vehicle number plate capture |
| Gate Control Servo | Controls the parking barrier |
| Camera Positioning Servo | Changes camera viewing direction |
| 16 × 2 I2C LCD | Displays system status and authentication messages |
| 4 × 4 Matrix Keypad | Emergency override code input |

### Arduino Pin Configuration

| Component | Arduino Pin / Configuration |
|---|---|
| Outer Entry RFID Reader | SS/SDA: Pin 10 |
| Inner Exit RFID Reader | SS/SDA: Pin 2 |
| RFID Shared Reset | Pin 9 |
| Gate Control Servo | A0 |
| Camera Positioning Servo | A3 |
| LCD | I2C Address: `0x27` |
| Keypad Rows | 8, 7, 6, 5 |
| Keypad Columns | 4, 3, A1, A2 |

---

## Software Stack

### Python Backend

| Library / Module | Purpose |
|---|---|
| Python 3 | Main backend programming language |
| OpenCV (`opencv-python`) | Camera capture, digital zoom, and image preprocessing |
| EasyOCR | License plate text extraction |
| NumPy | Numerical operations and image-array handling |
| PySerial (`pyserial`) | Serial communication between Python and Arduino |
| SQLite3 | Local database storage and access tracking |
| `re` | Text cleaning and processing |
| `os` | Operating-system and file operations |
| `ssl` | Security-related functions |
| `time` | Timing and performance measurements |
| `datetime` | Date and timestamp management |

### Arduino Software

**Programming Language:** C++

**Development Environment:** Arduino IDE

| Library | Purpose |
|---|---|
| MFRC522 | RFID reader communication |
| LiquidCrystal_I2C | LCD display control |
| Servo | Servo motor control |
| Keypad | Matrix keypad input handling |

---

## Computer Vision Pipeline

The system uses OpenCV and EasyOCR to identify vehicle registration numbers.

The image processing workflow includes:

1. Camera positioning based on the triggered RFID reader.
2. Waiting for the camera to settle and clearing old video frames.
3. Digital zoom to improve the license plate view.
4. Conversion of the captured image to grayscale.
5. Noise reduction using a bilateral filter.
6. Adaptive thresholding to improve character visibility.
7. License plate text detection and recognition using EasyOCR.
8. Cleaning and validation of OCR output before database comparison.

---

## Authentication Workflow

1. A user scans an RFID card at the entry or exit reader.
2. Arduino sends the RFID ID and gate direction to the Python backend.
3. The camera positioning servo adjusts the camera toward the relevant lane.
4. The camera captures the vehicle's license plate.
5. OpenCV preprocesses the image, and EasyOCR extracts the registration number.
6. Python compares the recognized plate with the registered vehicle number in SQLite.
7. The backend checks the user's current parking status using the anti-passback algorithm.
8. If authentication succeeds, the Arduino receives the command to operate the gate servo.
9. The database records the access event and updates the vehicle's inside/outside status.

If authentication fails, access is denied and the attempt is recorded.

---

## Database and Security

The system uses a local SQLite database to maintain:

- Registered RFID card IDs.
- Associated vehicle registration numbers.
- Current parking status (`is_inside`).
- Successful entry and exit records.
- RFID and number plate mismatches.
- Anti-passback violations.
- Emergency override events.
- Date and time of access attempts.

The anti-passback mechanism ensures that a registered vehicle cannot enter again before its previous exit has been recorded.

---

## Emergency Override

An Arduino-connected 4 × 4 matrix keypad provides an emergency override mechanism. Administrators can enter a configured security code to activate the gate override. The event is also recorded in the database for later review.

---

## Project Objectives

- Improve parking security through two-factor vehicle and user authentication.
- Reduce unauthorised vehicle entry through RFID and number plate matching.
- Prevent repeated or invalid entry/exit operations using anti-passback logic.
- Automate camera positioning and parking barrier operation.
- Maintain a local record of parking activities and authentication events.
- Develop a practical, low-cost parking authorization solution.

---

## Technologies Used

**Languages:** Python, C++

**Computer Vision:** OpenCV, EasyOCR

**Database:** SQLite

**Embedded Systems:** Arduino

**Communication:** USB Serial Communication

**Hardware Interfaces:** SPI, I2C, PWM

---

## Future Improvements

- Introduce a shared database for managing multiple parking gates.
- Add traffic-pattern analysis using historical access logs.
- Deploy the Python backend on a compact edge computing device.
- Integrate vehicle detection to trigger OCR only when a vehicle is present.

---

## Project Information

**Project Title:** Computer Vision Based Parking Authorization and Authentication System

**Project Type:** Bachelor of Engineering in Computer Systems Engineering – Final Year Project


├── parking_system.py       # Python backend, DB initialization, and OCR pipeline
├── parking_system.ino      # Arduino firmware for RFID, Servos, LCD, and Keypad
└── parking_system.db       # Local SQLite database (auto-generated on first run)


## Team Members Contributions & Technical Breakdown 
👨‍💻 Member 1: Hamza Aijaz

Primary AI Focus: Generative AI, Retrieval-Augmented Generation (RAG) Architecture, Vector Embeddings
Core Infrastructure Focus: Embedded Hardware Systems, Relational Database Architecture, Firmware Integration

1. Technical Contributions (AI & Infrastructure)

Generative AI & RAG Orchestration: Architected and developed the RAG chatbot backend utilizing Google Gemini 2.5 Flash as the primary LLM framework (Settings.llm) integrated seamlessly via LlamaIndex.

Vector Embeddings & Hybrid Storage: Implemented localized vector embedding generation using HuggingFace (BAAI/bge-small-en-v1.5) mapped to a serverless Pinecone vector database index (fyp-index) with hybrid sparse-dense retrieval across dynamic client namespaces.

Cloud Document Parsing: Integrated LlamaCloud asynchronous parsing pipelines (AsyncLlamaCloud) to transform multi-format project documents (.pdf, .docx, .txt) into structured Markdown strings optimized for vector indexing.

Embedded Hardware & State Management: Designed the dual MFRC522 RFID subsystem operating over a shared SPI bus and engineered the localized SQLite relational database (parking_system.db), including the authorized_users schema with dynamic is_inside binary spatial flags.

2. Methodological Contributions

Vector Pipeline Optimization: Configured cached resource engines (@st.cache_resource) in Streamlit to optimize Pinecone database connections and prevent redundant API handshakes during user queries.

Asynchronous Concurrency: Programmed non-blocking C++ Arduino firmware using millis() timing loops and established a robust RS-232 serial communication protocol operating at 115,200 baud with deterministic payload structuring (OUTER_, INNER_).

Database Integrity: Enforced strict ACID atomic transactions for SQLite database updates, ensuring spatial state synchronization and chronological audit logging (access_logs) occur seamlessly without data corruption.

3. Research Aspects

RAG & Enterprise Intelligence: Investigated the integration of Large Language Models with vector databases for localized enterprise document intelligence and automated information retrieval.

Decentralized Edge Computing: Researched edge computing paradigms and serverless relational architectures to eliminate external cloud latency and network dependency during real-time security authentication.


👨‍💻 Member 2: Mahmood Badar 

Primary AI Focus: Computer Vision, Deep Learning Neural Networks, OCR Pipelines
Core Infrastructure Focus: Electromechanical Sensor Optimization, Optical Stabilization1. 

1. Technical Contributions (AI & Infrastructure)
   
Deep Learning OCR Pipeline: Spearheaded the integration of the EasyOCR text extraction engine powered by Convolutional Recurrent Neural Networks (CRNN) for high-accuracy alphanumeric character recognition.

Neural Text Detection: Deployed the CRAFT (Character Region Awareness for Text Detection) deep learning model to automatically locate precise spatial bounding boxes around characters on physical license plates.

Advanced Computer Vision Pre-Processing: Engineered an OpenCV processing pipeline implementing single-channel grayscale conversions, bilateral filtering for edge-preserving noise reduction, and localized Adaptive Gaussian Thresholding.

Electromechanical Vision Actuation: Designed the dynamic camera bracket driven by micro-servo Pulse Width Modulation (PWM) signals to mechanically reposition a single optical sensor between 0 degree (outer lane) and 180 degree (inner lane).

2. Methodological Contributions
   
Optical Stabilization Protocol: Developed a synchronized frame-purging sequence combining a 500ms hardware settling delay with an OpenCV memory buffer-flushing loop (cap.read()) to eliminate motion blur caused by servo rotation.

Digital Zoom Optimization: Implemented a permanent 1.5x localized digital zoom (apply_zoom) to mathematically crop, center, and isolate the vehicle license plate region of interest.

Heuristic String Sanitization: Programmed regex-based data cleaning filters paired with a regional identifier blacklist ("SINDH", "PUNJAB", "PAKISTAN", "GOVT") to sanitize raw OCR outputs prior to relational database validation.

3. Research Aspects:
   
Hardware CapEx Optimization: Researched hardware resource optimization and cost reduction strategies (CapEx minimization) in multi-lane access control by replacing redundant multi-camera arrays with a single dynamic servo-actuated optical sensor.

Optical Noise Evaluation: Investigated the impact of environmental optical noise (headlight glare, shadows, and weather occlusions) on deep learning neural network confidence intervals.
