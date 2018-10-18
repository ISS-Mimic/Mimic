
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
Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x68);
Adafruit_MotorShield AFMS2 = Adafruit_MotorShield(0x78);

// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Select which 'port' M1, M2, M3 or M4. In this case, M1,2,4
Adafruit_DCMotor *myMotorB1A = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorB3A = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorB1B = AFMS.getMotor(3);
Adafruit_DCMotor *myMotorB3B = AFMS.getMotor(4);

Adafruit_DCMotor *myMotorPSARJ = AFMS2.getMotor(1);
Adafruit_DCMotor *myMotorSSARJ = AFMS2.getMotor(2);




Encoder myEnc1A(0, 1);
Encoder myEnc3A(5, 6); //for some reason, these do not register blips if motor moves fast, within a few deg of desired position
// Pins 9, 10 are used by Servos.  Odd issues with Pins 2-4.
Encoder myEnc1B(7, 8);
Encoder myEnc3B(11, 12);

// Per here, Analog pins on Metro M0 are also digtial IO. https://learn.adafruit.com/adafruit-metro-m0-express-designed-for-circuitpython/pinouts
// From here, A1 is digital 15, A2 is 16, A3 is 17, A4 is 18, A5 is 19. http://www.pighixxx.net/portfolio_tags/pinout-2/#prettyPhoto[gallery1368]/0/

Encoder myEncPSARJ(15, 16); // 15,16 is A2, A3
Encoder myEncSSARJ(17, 18); // 17,18 is A4 ,A5


void setup() {

  // Set some pins to high, just for convenient connection to power Hall Effect Sensors
pinMode(A0, OUTPUT);
digitalWrite(A0, HIGH);
pinMode(A1, OUTPUT);
digitalWrite(A1, HIGH);
pinMode(A2, OUTPUT);
digitalWrite(A2, HIGH);

  // Attach a servo to pin #10
  servo1.attach(10);
  servo2.attach(9);
  AFMS.begin(200);  // I set this at 200 previously to reduce audible buzz.
  Serial.begin(115200);
  //Serial3.begin(115200);          //Serial1 is connected to the RasPi
  Serial.setTimeout(50);
 // Serial1.begin(9600);

  //Serial.println("Motor test!");

  // turn on motor   NOTE: May be able to remove all of these setSpeed and run commands here, although they are fine.
  myMotorB1A->setSpeed(150);
  myMotorB1A->run(RELEASE); 

  myMotorB3A->setSpeed(150);
  myMotorB3A->run(RELEASE);

  myMotorB1B->setSpeed(150);
  myMotorB1B->run(RELEASE);

  myMotorB3B->setSpeed(150);
  myMotorB3B->run(RELEASE);

  // For debugging
  //  pinMode(13, OUTPUT); //LED
}
