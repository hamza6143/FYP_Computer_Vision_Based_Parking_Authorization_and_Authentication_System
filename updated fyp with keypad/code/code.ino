#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <Keypad.h>

#define SS_1_PIN 10    // Outer RFID SS Pin
#define SS_2_PIN 2     // Inner RFID SS Pin (Safe available pin)
#define RST_PIN 9      // Shared Reset Pin

MFRC522 rfid1(SS_1_PIN, RST_PIN); // Outer Reader
MFRC522 rfid2(SS_2_PIN, RST_PIN); // Inner Reader

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo gateServo;
Servo camServo;        // Camera bracket positioning servo

const byte ROWS = 4;
const byte COLS = 4; 
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {8, 7, 6, 5};   // Digital Pins 5-8
byte colPins[COLS] = {4, 3, A1, A2}; // Digital Pins 3-4, and Analog Pins A1-A2

Keypad myKeypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

int closeAngle = 0;
int openAngle = 110;     
unsigned long stayOpenTime = 8000; 

int camOuterAngle = 0;   // Facing outwards for entry scans
int camInnerAngle = 180; // Facing inwards for exit scans

const String EMERGENCY_CODE = "2327"; 
String inputCode = "";
bool isGateOpen = false; 
bool isKeypadBypassActive = false; 
unsigned long gateOpenStartTime = 0; 

void setup() {
  Serial.begin(9600);
  SPI.begin();
  
  // Staggered boot delays clear buffer issues on the SPI bus line
  rfid1.PCD_Init(); 
  delay(100);       
  rfid2.PCD_Init(); 
  delay(100);       
  
  gateServo.attach(A0); 
  gateServo.write(closeAngle); 
  
  camServo.attach(A3);             
  camServo.write(camOuterAngle);   
  
  lcd.init();
  lcd.backlight();
  displayReadyMessage();
}

void loop() {
  // 1. AUTOMATIC TIMER CONTROL
  if (isGateOpen && !isKeypadBypassActive && (millis() - gateOpenStartTime >= stayOpenTime)) {
    closeGate(); 
  }

  // 2. KEYPAD PROCESSING
  char key = myKeypad.getKey(); 
  if (key) { 
    if (key == '#') { 
      if (inputCode == EMERGENCY_CODE) {
        handleKeypadBypassToggle(); 
      } else {
        lcd.clear();
        lcd.print("INVALID CODE");
        delay(1500);
        if (isKeypadBypassActive) displayBypassActiveMessage(); else displayReadyMessage(); 
      }
      inputCode = ""; 
    } 
    else if (key == '*') { 
      inputCode = "";
      lcd.clear(); 
      lcd.print("ENTRY CLEARED");
      delay(1000);
      if (isKeypadBypassActive) displayBypassActiveMessage(); else displayReadyMessage();
    } 
    else {
      inputCode += key;
      lcd.clear(); 
      lcd.print("ENTER CODE:");
      lcd.setCursor(0, 1);
      for(int i=0; i<inputCode.length(); i++) lcd.print("*"); 
    }
  }

  // 3. CHECK FOR RFID CARD SCANS (Decoupled execution blocks)
  if (!isGateOpen && !isKeypadBypassActive) {
    // Check Outer RFID
    if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {
      camServo.write(camOuterAngle); // Shift camera outward
      delay(500);                     // Wait for mechanical shift
      processRFID("OUTER_", rfid1);
    }
    
    // Check Inner RFID
    if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {
      camServo.write(camInnerAngle); // Shift camera inward
      delay(500);                     // Wait for mechanical shift
      processRFID("INNER_", rfid2);
    }
  }

  // 4. LISTEN FOR PYTHON'S RESPONSE
  if (!isGateOpen && !isKeypadBypassActive && Serial.available() > 0) {
    char result = Serial.read(); 
    if (result == 'G') { 
      openGate("ACCESS GRANTED", "PASS THROUGH", false); 
    } 
    else if (result == 'D') {
      lcd.clear();
      lcd.print("ACCESS DENIED");
      lcd.setCursor(0, 1); 
      lcd.print("CHECK PLATE/UID");
      delay(3000);
      displayReadyMessage();
    }
  }
}

void processRFID(String prefix, MFRC522 &reader) {
  lcd.clear();
  lcd.print("SCANNING...");
  
  Serial.print(prefix); 
  for (byte i = 0; i < reader.uid.size; i++) {
    Serial.print(reader.uid.uidByte[i] < 0x10 ? "0" : ""); 
    Serial.print(reader.uid.uidByte[i], HEX); 
  }
  Serial.println();
  
  reader.PICC_HaltA();
  reader.PCD_StopCrypto1();
  delay(200); 
}

void openGate(String msg1, String msg2, bool isBypass) {
  lcd.clear();
  lcd.print(msg1);
  lcd.setCursor(0, 1); 
  lcd.print(msg2);
  
  gateServo.write(openAngle); 
  isGateOpen = true;
  isKeypadBypassActive = isBypass;
  gateOpenStartTime = millis(); 
}

void closeGate() {
  gateServo.write(closeAngle);
  delay(200);
  isGateOpen = false; 
  isKeypadBypassActive = false;
  displayReadyMessage();
}

void handleKeypadBypassToggle() {
  while(Serial.available() > 0) Serial.read();
  if (!isKeypadBypassActive) { 
    Serial.println("EMERGENCY_OVERRIDE_ON"); 
    openGate("EMERGENCY MODE", "BYPASS ACTIVE", true);
  } else {
    Serial.println("EMERGENCY_OVERRIDE_OFF"); 
    lcd.clear();
    lcd.print("BYPASS DEACTIVATED"); 
    lcd.setCursor(0, 1);
    lcd.print("CLOSING GATE...");
    delay(1500);
    closeGate();
  }
}

void displayReadyMessage() {
  lcd.clear();
  lcd.print(" PARKING SYSTEM ");
  lcd.setCursor(0, 1);
  lcd.print("    READY...    "); 
}

void displayBypassActiveMessage() {
  lcd.clear();
  lcd.print("EMERGENCY MODE");
  lcd.setCursor(0, 1);
  lcd.print("BYPASS ACTIVE");
}