
// This version is built to turn 3 motors, PSARJ, BGA 2B & BGA 4B using the Driver Board Ports 1, 2, and 4 respectively.

// =========== Primary ToDo's ===========
// 1) Connect extra motors to ensure this version (3 motors) works
// 2) Change secondary encoder pin for each motor to be non-interrrupt pin
// 3) Debug all my errors....
//
// Eventually....
// 1) Set I2C address for 2nd and 3rd motor driver boards, as each board can drive only 4 motors.
//


#include <Encoder.h>  // Feb08

#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
Adafruit_DCMotor *myMotorB2A = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorB4A = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorB2B = AFMS.getMotor(3);
Adafruit_DCMotor *myMotorB4B = AFMS.getMotor(4);


// pins for the encoder inputs
//#include <Wire.h>  // BCM - can prob remove this line.

// Hardware interrupt pins on the Arduino Mega: 2, 3, 18, 19, 20, 21; 
// NOTE: Will eventually use only 1 interrupt pin per motor, which will support up to six motors.  Will try software interrupts for the rest, if possible.  Otherwise will need a second Ard, or one with more HW interrupts.
//

  Encoder myEnc4B(12, 2); // Feb08  
  Encoder myEnc2B(14, 3); // Feb08

  Encoder myEnc4A(20, 8); // Feb08  
  Encoder myEnc2A(21, 9); // Feb08
  
  //long currentPosition = 0;  // Feb08

void setup() {

  AFMS.begin(500);  // I sest this at 200 to reduce audible buzz.

  Serial.begin(115200);
  Serial1.begin(115200);          //Serial1 is connected to the RasPi
  Serial1.setTimeout(50);

  Serial.println("Motor test!");

  // turn on motor   NOTE: May be able to remove all of these setSpeed and run commands here, although they are fine.
  myMotorB2A->setSpeed(150);
  myMotorB2A->run(RELEASE);

  myMotorB4A->setSpeed(150);
  myMotorB4A->run(RELEASE);
  
  myMotorB2B->setSpeed(150);
  myMotorB2B->run(RELEASE);

  myMotorB4B->setSpeed(150);
  myMotorB4B->run(RELEASE);

  // For debugging
  pinMode(13, OUTPUT); //LED
}






