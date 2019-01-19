
/// MIMIC!!! MIMIC!!!
//


#include <Encoder.h>

#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>
#include <Servo.h>
Servo servo1;
Servo servo2;

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);  //UPDATE THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11
Adafruit_MotorShield AFMS2 = Adafruit_MotorShield(0x60); //UPDATE THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
// Port BGAS
Adafruit_DCMotor *myMotorB2A = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorB4A = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorB2B = AFMS.getMotor(3);
Adafruit_DCMotor *myMotorB4B = AFMS.getMotor(4);
// SARJs
Adafruit_DCMotor *myMotorPSARJ = AFMS2.getMotor(1);
Adafruit_DCMotor *myMotorSSARJ = AFMS2.getMotor(2);



Encoder myEnc2A(0, 1);
Encoder myEnc4A(4, 5); //for some reason, these do not register blips if motor moves fast, within a few deg of desired position
// Pins 9, 10 are used by Servos.  Odd issues with Pins 2-4.
Encoder myEnc2B(6, 7);
Encoder myEnc4B(11, 12);

Encoder myEncPSARJ(14,15);
Encoder myEncSSARJ(16,17);


void setup() {

  // Set some pins to high, just for convenient connection to power Hall Effect Sensors
//pinMode(A0, OUTPUT);
//digitalWrite(A0, HIGH);
//pinMode(A1, OUTPUT);
//digitalWrite(A1, HIGH);
//pinMode(A2, OUTPUT);
//digitalWrite(A2, HIGH);

  // Attach a servo to pin #10
//  servo1.attach(10);
//  servo2.attach(9);
  AFMS.begin(200);  // I set this at 200 previously to reduce audible buzz.
 // Serial.begin(115200);
    Serial.begin(9600);
  //Serial3.begin(115200);          //Serial1 is connected to the RasPi
  Serial.setTimeout(50);
 // Serial1.begin(9600);

  //Serial.println("Motor test!");

  // turn on motor   NOTE: May be able to remove all of these setSpeed and run commands here, although they are fine.
  myMotorB2A->setSpeed(150);
  myMotorB2A->run(RELEASE); 

  myMotorB4A->setSpeed(150);
  myMotorB4A->run(RELEASE);

  myMotorB2B->setSpeed(150);
  myMotorB2B->run(RELEASE);

  myMotorB4B->setSpeed(150);
  myMotorB4B->run(RELEASE);


  myMotorPSARJ->setSpeed(150);
  myMotorPSARJ->run(RELEASE);

  myMotorSSARJ->setSpeed(150);
  myMotorSSARJ->run(RELEASE);
  

  // For debugging
  //  pinMode(13, OUTPUT); //LED
}
