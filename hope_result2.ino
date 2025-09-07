//최종ver 

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include "HX711.h"

// LCD, HX711, Servo 정의
LiquidCrystal_I2C lcd(0x27, 20, 4);
HX711 scale;
Servo servo1, servo2, servo3, servo4;

// 핀 정의
#define DT 3
#define SCK 2
#define SERVO1_PIN 5
#define SERVO2_PIN 6
#define SERVO3_PIN 9
#define SERVO4_PIN 10

// 무게 임계값
const float WEIGHT_THRESHOLD = 5.0;

// 평균값 계산 함수
float getAverageWeight(int count = 10) {
  float sum = 0;
  for (int i = 0; i < count; i++) {
    sum += scale.get_units();
    delay(10);
  }
  return sum / count;
}

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("  Recycling Robot");
  lcd.setCursor(0, 1);
  lcd.print("   Ready to Sort");

  // 서보 초기화
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  servo3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  servo1.write(5);
  servo2.write(5);
  servo3.write(5);
  servo4.write(10);

  // 로드셀 초기화
  scale.begin(DT, SCK);
  scale.set_scale(437.7);  // ← 사용자 보정값
  scale.tare();
}

void loop() {
  float weight = getAverageWeight(10);

  if (weight >= WEIGHT_THRESHOLD) {
    Serial.println("ready");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Trash Detected!");
    lcd.setCursor(0, 1);
    lcd.print("Weight: ");
    lcd.print(weight, 1);
    lcd.print(" g");

    delay(1500);  // 쓰레기 정지 대기

    waitForClassAndSort();
  }

  delay(500);  // 측정 주기
}

void waitForClassAndSort() {
  long startTime = millis();
  while (millis() - startTime < 10000) {
    if (Serial.available()) {
      int category = Serial.parseInt();
      if (category >= 0 && category <= 3) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Class: ");
        lcd.print(category);
        doSort(category);
        return;
      }
    }
  }
  lcd.setCursor(0, 2);
  lcd.print("Timeout (10s)");
}

void doSort(int category) {
  lcd.setCursor(0, 1);
  lcd.print("Sorting...");
  servo4.write(85);
  lcd.setCursor(0, 2);
  lcd.print("Open!!");
  delay(2000);

  lcd.setCursor(0, 3);
  switch (category) {
    case 1:
      servo1.write(70); lcd.print("→ Metal sorted"); delay(10000); servo1.write(5); break;
    case 2:
      servo2.write(70); lcd.print("→ Paper sorted"); delay(10000); servo2.write(5); break;
    case 3:
      servo3.write(70); lcd.print("→ Plastic sorted"); delay(10000); servo3.write(5); break;
    default:
      lcd.print("→ Glass (skip)");
      break;
  }

  delay(1000);
  servo4.write(10);
  lcd.setCursor(0, 2);
  lcd.print("Closed!!       ");
  lcd.setCursor(0, 3);
  lcd.print("                "); // 이전 메시지 지움
  delay(1500);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  Recycling Robot");
  lcd.setCursor(0, 1);
  lcd.print("   Ready to Sort");
}
