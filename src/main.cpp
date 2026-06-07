#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>
#define OLED_SDA  21
#define OLED_SCL  19

U8G2_SSD1306_128X64_NONAME_F_HW_I2C OLED(U8G2_R0, U8X8_PIN_NONE);

#include "1e78d601061d43d991db7adedbeba0b1.h"

void setup() {
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(800000);
  OLED.begin();
  OLED.setContrast(200);
}

void loop() {
  const uint16_t delays[] = FRAME_DELAYS_MS;

  for (int i = 0; i < FRAME_COUNT; i++) {
    unsigned long t_start = millis();
    OLED.drawXBMP(0, 0, 128, 64, frames[i]);
    OLED.sendBuffer();
    unsigned long elapsed = millis() - t_start;
    if (elapsed < delays[i]) {
      delay(delays[i] - elapsed);
    }
  }
}
