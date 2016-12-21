#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield(); 
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61); 

// Select which 'port' M1, M2, M3 or M4. In this case, M1
Adafruit_DCMotor *myMotor = AFMS.getMotor(1);
// You can also make another motor on port M2
//Adafruit_DCMotor *myOtherMotor = AFMS.getMotor(2);

// pins for the encoder inputs
#include <Wire.h>
#define RH_ENCODER_A 3  // BGA1 interrupt and 
#define RH_ENCODER_B 2  // BGA1 encoder

// for software I2C
#define SCL_PIN 4
#define SCL_PORT PORTD
#define SDA_PIN 5
#define SDA_PORT PORTD
#include <SoftI2CMaster.h>

#include <SoftWire.h>
SoftWire Wire2 = SoftWire();

void setup() {

AFMS.begin(200);  // create with the default frequency 1.6KHz
  //AFMS.begin(1000);  // OR with a different frequency, say 1KHz

  
  Wire2.begin();                // join i2c bus with address #4
  Wire2.onReceive(receiveEvent); // register event
  pinMode(RH_ENCODER_A, INPUT);
  pinMode(RH_ENCODER_B, INPUT);

  // initialize hardware interrupts
  attachInterrupt(digitalPinToInterrupt(3), rightEncoderEvent, CHANGE);   // BGA1

  Serial.begin(115200);           // set up Serial library at 9600 bps
  Serial.println("Motor test!");

  // turn on motor
  myMotor->setSpeed(150);
  myMotor->run(RELEASE);

  // For debugging
   pinMode(13, OUTPUT); //LED
}






