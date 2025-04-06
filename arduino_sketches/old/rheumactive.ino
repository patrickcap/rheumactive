// Currently a copy of: Arduino_Sketch_Dual_MVP_01.ino

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h> // For trigonometric calculations

Adafruit_MPU6050 mpu1; // First MPU-6050 (0x68)
Adafruit_MPU6050 mpu2; // Second MPU-6050 (0x69)

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // Wait for Serial Monitor to connect
  }

  Wire.begin();

  // Initialize the first MPU-6050 (0x68)
  if (!mpu1.begin(0x68)) {
    Serial.println("Failed to find MPU6050 at address 0x68!");
    while (1) delay(10);
  }
  Serial.println("MPU6050 at 0x68 initialized.");

  // Initialize the second MPU-6050 (0x69)
  if (!mpu2.begin(0x69)) {
    Serial.println("Failed to find MPU6050 at address 0x69!");
    while (1) delay(10);
  }
  Serial.println("MPU6050 at 0x69 initialized.");
}

void loop() {
  sensors_event_t accel1, gyro1, temp1;
  sensors_event_t accel2, gyro2, temp2;

  // Read data from the first MPU-6050
  mpu1.getEvent(&accel1, &gyro1, &temp1);

  // Read data from the second MPU-6050
  mpu2.getEvent(&accel2, &gyro2, &temp2);

  // Calculate roll, pitch, and yaw for the first sensor
  float roll1 = atan2(accel1.acceleration.y, accel1.acceleration.z) * 180 / M_PI;
  float pitch1 = atan2(-accel1.acceleration.x, sqrt(accel1.acceleration.y * accel1.acceleration.y + accel1.acceleration.z * accel1.acceleration.z)) * 180 / M_PI;
  float yaw1 = gyro1.gyro.z * 180 / M_PI; // Simplistic yaw approximation

  // Calculate roll, pitch, and yaw for the second sensor
  float roll2 = atan2(accel2.acceleration.y, accel2.acceleration.z) * 180 / M_PI;
  float pitch2 = atan2(-accel2.acceleration.x, sqrt(accel2.acceleration.y * accel2.acceleration.y + accel2.acceleration.z * accel2.acceleration.z)) * 180 / M_PI;
  float yaw2 = gyro2.gyro.z * 180 / M_PI; // Simplistic yaw approximation

  // Print data in CSV format: roll1,pitch1,yaw1,roll2,pitch2,yaw2
  Serial.print(roll1, 2); Serial.print(",");
  Serial.print(pitch1, 2); Serial.print(",");
  Serial.print(yaw1, 2); Serial.print(",");
  Serial.print(roll2, 2); Serial.print(",");
  Serial.print(pitch2, 2); Serial.print(",");
  Serial.println(yaw2, 2);

  // Adjust loop speed if necessary
  delay(10); // 10ms delay gives ~100Hz output rate
}
