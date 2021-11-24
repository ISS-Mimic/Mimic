
/// MIMIC!!! MIMIC!!!
//
// This version is for the Port BGA Arduino.  Other than naming (4B vs 3B), it's functionally identical to the Stbd BGA code.
// 4A is Motor 1, Encoder pins 0,1
// 2A is Motor 2, Encoder pins 2,3
// 4B is Motor 3, Encoder pins 7,8
// 2B is Motor 4, Encoder pins 11,12


int SpeedLimit= 125; // integer from 0 to 255.  0 means 0% speed, 255 is 100% speed.  

// Some constants to keep track of time and do some math operations later
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
uint8_t i;
unsigned long mytime;

// "Smart Rollover" means it takes the shortest path when crossing 0 deg.  For instance, if at 350 deg and commanded to 20 deg, rather than moving backward 330 deg (350-20), it will move forward 30 deg.
int SmartRolloverBGA = 1;
int SmartRolloverSARJ = 1;

// Defining some variables that will be used for each DC motor commanded.  Using a struct is a bit more tidy than creating unique variables for each motor.
struct joints
{
  float Kp;
  float Ki;
  float Kd;
  long Count;
  float PosCmd;
  float PosAct;
  float PosErr;
  float PosErr_old;
  float tmpSpeed;
  float dErrDt;
  float dPosErr;
  float IntOld;
  float IntNow;
  int CmdSpeed;
};

// This assigns values to each of the above variables in the struct (Kp, Ki, ...) for each "joint" struct created.
joints bga_4A = {5, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
joints bga_2A = {5, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
joints bga_4B = {5, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
joints bga_2B = {5, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};


void motorfnc(struct joints &myJoint) {
  
  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  myJoint.PosAct = float(myJoint.Count) / 5;

  // Added Aug 18, 2019 by BCM for "Smart Rollover"
  if (SmartRolloverBGA == 1) {
    if (abs(myJoint.PosAct) > 360) {
      float tmp_raw_div = myJoint.PosAct / 360.0; // result will be 0.xx, 1.xx, 2.xx, etc.  Solve for the Y in Y.xx, then subtract from the whole.
      // we want (for example) -900.1 degrees to become something in 0..360 range.
      //(double(tmp_raw_div)-double(floor(tmp_raw_div)))*360 - from Octave check
      float tmp_pos = (float(tmp_raw_div) - float(floor(tmp_raw_div))) * 360;
      myJoint.PosAct = tmp_pos;
    }
  }  // end Added Aug 18, 2019

  myJoint.PosErr = myJoint.PosCmd - myJoint.PosAct; // raw position error  
  myJoint.dPosErr = myJoint.PosErr - myJoint.PosErr_old;
  
// Added Aug 18, 2019 by BCM for "Smart Rollover"
  if (SmartRolloverBGA == 1) {
    if (myJoint.PosErr > 180) {
      myJoint.PosErr =myJoint.PosErr-360;
    }
    if (myJoint.PosErr <-180) {
      myJoint.PosErr = myJoint.PosErr+360;
    }
  }  // end Added Aug 18, 2019  

  if (abs(myJoint.PosErr) < 0.1) {
    myJoint.PosErr = 0;
    myJoint.dPosErr = 0;
    myJoint.PosErr_old = 0;
    myJoint.IntOld = 0;
  }

  myJoint.dErrDt = myJoint.dPosErr * inverse_delta_t_millis * 0.001; // For Derivative
  //IntNow = IntOld + PosErr * inverse_delta_t_millis * 0.001; // For Integrator
  myJoint.IntNow = myJoint.IntOld + myJoint.PosErr * delta_t_millis * 0.001; 
  myJoint.IntOld = myJoint.IntNow;

  // Integrator reset when error sign changes
  if (myJoint.PosErr_old * myJoint.PosErr <= 0) { // sign on error has changed or is zero
    myJoint.IntNow = 0;
    myJoint.IntOld = 0;
  }
  myJoint.PosErr_old = myJoint.PosErr; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  myJoint.tmpSpeed = myJoint.Kp * myJoint.PosErr + myJoint.Kd * (myJoint.dErrDt) + myJoint.Ki * myJoint.IntNow;
  // Deadband seems to be about 40 (for 5V input to motor board);
  myJoint.CmdSpeed = abs(myJoint.tmpSpeed);
  if ((myJoint.CmdSpeed < 40) && (myJoint.CmdSpeed > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    myJoint.CmdSpeed = 40;
  }
 //  myJoint.CmdSpeed = max(min(myJoint.CmdSpeed, 240), 0); //  Update as needed per motor.
  myJoint.CmdSpeed = max(min(myJoint.CmdSpeed, SpeedLimit), 0); //  Update as needed per motor.
}
void motorNULL(struct joints &myJoint) {
    myJoint.PosErr = 0;
    myJoint.dPosErr = 0;
    myJoint.dErrDt=0;
    myJoint.PosErr_old = 0;
    myJoint.IntOld = 0;
    myJoint.IntNow = 0;
    myJoint.Count=0;
    myJoint.PosCmd=0;
    myJoint.PosAct=0;
    myJoint.CmdSpeed=0;
    myJoint.tmpSpeed=0;
}

#include <Encoder.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <string.h>

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x60);  

// Select which 'port'  on the motor shield for each BGA entity: M1, M2, M3 or M4. 
Adafruit_DCMotor *myMotorB4A = AFMS.getMotor(1);
Adafruit_DCMotor *myMotorB2A = AFMS.getMotor(2);
Adafruit_DCMotor *myMotorB4B = AFMS.getMotor(3);
Adafruit_DCMotor *myMotorB2B = AFMS.getMotor(4);

// Define the pins used as encoder signals for each motor.  These are read via "hardware interrupts" to ensure the Ard sees every blip.
Encoder myEnc4A(0, 1);
Encoder myEnc2A(2, 3); 
Encoder myEnc4B(7, 8); 
Encoder myEnc2B(11, 12);

// Per here, Analog pins on Metro M0 are also digtial IO. https://learn.adafruit.com/adafruit-metro-m0-express-designed-for-circuitpython/pinouts
// From here, A1 is digital 15, A2 is 16, A3 is 17, A4 is 18, A5 is 19. http://www.pighixxx.net/portfolio_tags/pinout-2/#prettyPhoto[gallery1368]/0/


int D0 = 0;
int D1 = 0;
int D2 =0;
int D3 =0;
//int D4 = 0;
//int D5 = 0;
//int D6 = 0;
int D7 = 0;
int D8 =0;
//int D9 =0;
//int D10=0;
int D11 = 0;
int D12 = 0;
//int D13=0;
int D14 = 0;
int D15 = 0;
int D16 = 0;
int D17 = 0;


void setup() {

  // Set some pins to high, just for convenient connection to power Hall Effect Sensors
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
    pinMode(5, OUTPUT);
  digitalWrite(5, LOW); // always low, for convenient ground
  pinMode(6, OUTPUT);
  digitalWrite(6, HIGH);

// This sets the AdaFruit Motor Shield frequency to command the motors.  Mostly changed to reduce audible buzz.
  AFMS.begin(200);  // I set this at 200 previously to reduce audible buzz.

  Serial.begin(9600);
  Serial.setTimeout(50);

}
