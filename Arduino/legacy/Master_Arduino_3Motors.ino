
// This version is built to turn 3 motors, PSARJ, BGA 2B & BGA 4B using the Driver Board Ports 1, 2, and 4 respectively.

// =========== Primary ToDo's ===========
// 1) Connect extra motors to ensure this version (3 motors) works
// 2) Change secondary encoder pin for each motor to be non-interrrupt pin
// 3) Debug all my errors....
//
// Eventually....
// 1) Set I2C address for 2nd and 3rd motor driver boards, as each board can drive only 4 motors.
//




#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
Adafruit_DCMotor *myMotorPSARJ = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorBeta2B = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorBeta4B = AFMS.getMotor(4);


// pins for the encoder inputs
#include <Wire.h>

// Hardware interrupt pins on the Arduino Mega: 2, 3, 18, 19, 20, 21; 
// NOTE: Will eventually use only 1 interrupt pin per motor, which will support up to six motors.  Will try software interrupts for the rest, if possible.  Otherwise will need a second Ard, or one with more HW interrupts.

#define ENCODER_Beta2B_A 3  // Beta2B interrupt and 
#define ENCODER_Beta2B_B 2  // Beta2B encoder

#define ENCODER_Beta4B_A 18  // Beta4B interrupt and 
#define ENCODER_Beta4B_B 19  // Beta4B encoder

#define ENCODER_PSARJ_A 20  // PSARJ interrupt and 
#define ENCODER_PSARJ_B 21  // PSARJ encoder



void setup() {

  AFMS.begin(200);  // I sest this at 200 to reduce audible buzz.
  //AFMS.begin(1000);  // OR with a different frequency, say 1KHz

  pinMode(ENCODER_Beta2B_A, INPUT);
  pinMode(ENCODER_Beta2B_B, INPUT);
  pinMode(ENCODER_Beta4B_A, INPUT);
  pinMode(ENCODER_Beta4B_B, INPUT);
  pinMode(ENCODER_PSARJ_A, INPUT);
  pinMode(ENCODER_PSARJ_B, INPUT);

  // initialize hardware interrupts  NOTE: Per above, will eventually use non-interrupt pins for secondary Encoder counters (the "_B" ones)
  attachInterrupt(digitalPinToInterrupt(3), EncoderEvent_Beta2B, CHANGE);   // Beta2B
  attachInterrupt(digitalPinToInterrupt(18), EncoderEvent_Beta4B, CHANGE);   // Beta4B
  attachInterrupt(digitalPinToInterrupt(20), EncoderEvent_PSARJ, CHANGE);  // PSARJ

  Serial.begin(9600);
  Serial1.begin(115200);          //Serial1 is connected to the RasPi
  Serial1.setTimeout(50);

  Serial.println("Motor test!");

  // turn on motor   NOTE: May be able to remove all of these setSpeed and run commands here, although they are fine.
  myMotorBeta2B->setSpeed(150);
  myMotorBeta2B->run(RELEASE);

  myMotorBeta4B->setSpeed(150);
  myMotorBeta4B->run(RELEASE);

  myMotorPSARJ->setSpeed(150);
  myMotorPSARJ->run(RELEASE);

  // For debugging
  pinMode(13, OUTPUT); //LED
}






