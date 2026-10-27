#include <Arduino.h>

#if !defined(ARDUINO_ELEGOO_ESP32S3_BOT_CAM)
#error Select ELEGOO ESP32-S3 BOT CAM before compiling CameraCheck.
#else
#include "esp_camera.h"

// J1 Y2..Y9 map to camera D0..D7, not GPIO order.
static_assert(CAM_PIN_D0 == 11 && CAM_PIN_D1 == 9 && CAM_PIN_D2 == 8 && CAM_PIN_D3 == 10 &&
              CAM_PIN_D4 == 12 && CAM_PIN_D5 == 18 && CAM_PIN_D6 == 17 && CAM_PIN_D7 == 16,
              "Incorrect camera data pins");
static_assert(CAM_PIN_XCLK == 15 && CAM_PIN_PCLK == 13 && CAM_PIN_VSYNC == 6 && CAM_PIN_HREF == 7,
              "Incorrect camera clock/sync pins");
static_assert(CAM_PIN_SIOD == 4 && CAM_PIN_SIOC == 5 && CAM_PIN_PWDN == -1 && CAM_PIN_RESET == -1,
              "Incorrect camera control pins");

static bool cameraReady = false;

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("ELEGOO ESP32-S3 BOT CAM camera check");
  Serial.printf("Flash: %u bytes; PSRAM: %u bytes\n", ESP.getFlashChipSize(), ESP.getPsramSize());
  if (!psramFound()) {
    Serial.println("PSRAM missing. Select Tools > PSRAM > OPI PSRAM and upload again.");
    return;
  }

  // Use a compatible JPEG DVP sensor, e.g. OV2640. Do not call Wire.begin():
  // esp_camera_init() owns the shared GPIO4/5 SCCB bus in this example.
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = CAM_PIN_D0;
  config.pin_d1 = CAM_PIN_D1;
  config.pin_d2 = CAM_PIN_D2;
  config.pin_d3 = CAM_PIN_D3;
  config.pin_d4 = CAM_PIN_D4;
  config.pin_d5 = CAM_PIN_D5;
  config.pin_d6 = CAM_PIN_D6;
  config.pin_d7 = CAM_PIN_D7;
  config.pin_xclk = CAM_PIN_XCLK;
  config.pin_pclk = CAM_PIN_PCLK;
  config.pin_vsync = CAM_PIN_VSYNC;
  config.pin_href = CAM_PIN_HREF;
  config.pin_sccb_sda = CAM_PIN_SIOD;
  config.pin_sccb_scl = CAM_PIN_SIOC;
  config.pin_pwdn = CAM_PIN_PWDN;
  config.pin_reset = CAM_PIN_RESET;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x. Check the sensor and ribbon cable with power off.\n", err);
    return;
  }
  cameraReady = true;
}

void loop() {
  if (cameraReady) {
    camera_fb_t *frame = esp_camera_fb_get();
    if (frame) {
      Serial.printf("JPEG frame: %ux%u, %u bytes\n", (unsigned)frame->width,
                    (unsigned)frame->height, (unsigned)frame->len);
      esp_camera_fb_return(frame);
    } else {
      Serial.println("Frame capture failed.");
    }
  }
  delay(1000);
}
#endif
