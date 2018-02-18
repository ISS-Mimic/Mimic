
// MIMIC!!! MIMIC!!!
//
//

// Prior problems with Mega interrupt limitations led to use of Arduino Due instead.  This board can
// support hardware interrupts on any digital pin, although pin 13 is avoided since connects to LED.
// This means we can (theoretically) use an interrupt pin for each encoder signal on each motor.
// That's two per motor, times ten (8 BGA and 2 SARJ) motors = 20 interrupts. A minor issue discovered
// with the Due is that it's pull-up resistors have a large value (100 Kohms), which made for problems
// with counting encoder pulses.  Web search indicated that using a 2.2K resistor on each utilized pin
// to 3.3v is the solution, which seems to work well.
// Subsequently, discovered Due is problematic with I2C, so moved to Metro M0

// To Do's
// 1) Test with four motors -- DONE 1/20/2018 with Metro M0
// 2) Set I2C address for 2nd and 3rd motor driver boards, as each board can drive only 4 DC motors.
// 3) Try 20 interrupts (driven by encoders) at once to ensure no loss of counts  --  DONE 1/20/2018 with Metro M0
// 4) Rewrite Motor algorithms as re-usable class, rather than explicit for each one.
// 5) Add capability for servos, to drive the TRRJs. DONE 1/0?/2018 with Metro M0
// 6) De-ugli-fication of the code.

#include <Encoder.h>

#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>
#include <Servo.h>
Servo servo1;
Servo servo2;

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
Adafruit_DCMotor *myMotorB2A = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorB4A = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorB2B = AFMS.getMotor(3);
Adafruit_DCMotor *myMotorB4B = AFMS.getMotor(4);


Encoder myEnc2A(2, 3);
Encoder myEnc4A(6, 7); //for some reason, these do not register blips if motor moves fast, within a few deg of desired position
//Encoder myEnc4A(A1,A2);// was 0,1
Encoder myEnc2B(5, 8);
Encoder myEnc4B(11, 12);

void setup() {

  // Attach a servo to pin #10
  servo1.attach(10);
  servo2.attach(9);
  AFMS.begin(200);  // I set this at 200 previously to reduce audible buzz.
  Serial.begin(115200);
  //Serial3.begin(115200);          //Serial1 is connected to the RasPi
  Serial.setTimeout(50);
  Serial1.begin(9600);

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

  // For debugging
  //  pinMode(13, OUTPUT); //LED
}


