
// Stepper library info: https://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html

/*
Spec sheet notes: 
Speed Variation Ratio: 1/64
Stride Angle:   5.625° /64
*/

/*
   AccelStepper (uint8_t interface=AccelStepper::FULL4WIRE, uint8_t pin1=2, uint8_t pin2=3, uint8_t pin3=4, uint8_t pin4=5, bool enable=true)

  AccelStepper (void(*forward)(), void(*backward)())
  void  moveTo (long absolute)
  void  move (long relative)
  boolean   run ()
  boolean   runSpeed ()
  void  setMaxSpeed (float speed)
  float   maxSpeed ()
  void  setAcceleration (float acceleration)
  void  setSpeed (float speed)
  float   speed ()
  long  distanceToGo ()
  long  targetPosition ()
  long  currentPosition ()
  void  setCurrentPosition (long position)
  void  runToPosition ()
  boolean   runSpeedToPosition ()
  void  runToNewPosition (long position)
  void  stop ()
  virtual void  disableOutputs ()
  virtual void  enableOutputs ()
  void  setMinPulseWidth (unsigned int minWidth)
  void  setEnablePin (uint8_t enablePin=0xff)
  void  setPinsInverted (bool directionInvert=false, bool stepInvert=false, bool enableInvert=false)
  void  setPinsInverted (bool pin1Invert, bool pin2Invert, bool pin3Invert, bool pin4Invert, bool enableInvert)
  bool  isRunning ()

*/

String test;
boolean AOS = false;

double deg2StepperCounts=64/5.6; // To move 1 deg on output shaft, command 64/5.6 stepper counts.

double SGANT_El_deg = -180; // SGANT antenna elevation angle, deg; From telemetry stream
double SGANT_xEl_deg = 180; // SGANT "cross elevation" angle, deg; From telemetry stream
double SGANT_Elev_PosCountsTarget =0;// -1*SGANT_El_deg*deg2StepperCounts;
double SGANT_xElev_PosCountsTarget = 0;//-1*SGANT_xEl_deg*deg2StepperCounts;

int PosErrCount1=0;
int PosErrCount2=0;

#include <AccelStepper.h>
#define HALFSTEP 8
#define FULLSTEP 4

// You need the AccelStepper library for this sketch to run.  You can get it from here: http://aka.ms/AccelStepper

#define StepA1 2 // connect to "INT 1" pin on Stepper driver board
#define StepB1 3 // connect to "INT 2" pin on Stepper driver board
#define StepC1 4 // connect to "INT 3" pin on Stepper driver board
#define StepD1 5 // connect to "INT 4" pin on Stepper driver board

#define StepA2 10
#define StepB2 11
#define StepC2 12
#define StepD2 13

// Notice, I'm passing them as StepA1, StepC1, StepB1, StepD1 (coil ends order) not
// StepA1, StepB1, StepC1, StepD1 (firing order).
AccelStepper stepper1(HALFSTEP, StepA1, StepC1, StepB1, StepD1);
AccelStepper stepper2(HALFSTEP, StepA2, StepC2, StepB2, StepD2);


void setup() {
  Serial.begin(115200);
  //Serial3.begin(115200);          //Serial1 is connected to the RasPi
  Serial.setTimeout(50);

//  //Set the initial speed (read the AccelStepper docs on what "speed" means
////  stepper1.setSpeed(100.0);
//  //Tell it how fast to accelerate
stepper1.setAcceleration(100.0);
//  //Set a maximum speed it should exceed
stepper1.setMaxSpeed(4000.0);
//  //Tell it to move to the target position
// 
//  
//// Now for stepper2, for CrossElevation stepper
stepper2.setAcceleration(100.0);
stepper2.setSpeed(100.0);
//  //Tell it how fast to accelerate
//  stepper2.setAcceleration(100.0);
//  //Set a maximum speed it should exceed
stepper2.setMaxSpeed(4000.0);
//  //Tell it to move to the target position

//setPinsInverted (bool directionInvert=false, bool stepInvert=false, bool enableInvert=false)
//stepper1.setPinsInverted(true,false,false); // Flips the sign, so our steppers move positive dir for pos cmd
//stepper2.setPinsInverted(true,false,false); // Flips the sign, so our steppers move positive dir for pos cmd

}

void loop() {

  SGANT_Elev_PosCountsTarget = -1*SGANT_El_deg*deg2StepperCounts;
  SGANT_xElev_PosCountsTarget = -1*SGANT_xEl_deg*deg2StepperCounts;
  stepper1.moveTo(SGANT_Elev_PosCountsTarget);
  stepper2.moveTo(SGANT_xElev_PosCountsTarget);

  stepper1.run();
  stepper2.run();

 //-------------------------------------------------------- 

  Serial.print(SGANT_El_deg );
  Serial.print(",");
  Serial.print(stepper1.targetPosition() );
  Serial.print(",");
  Serial.print(stepper1.currentPosition());
  Serial.print(",");
  Serial.print(stepper1.speed() );
  Serial.print("  |  ");
  
  Serial.print(SGANT_xEl_deg );
  Serial.print(",");
  Serial.print(stepper2.targetPosition() );
  Serial.print(",");
  Serial.print(stepper2.currentPosition());
  Serial.print(",");
  Serial.print(stepper2.speed() );
  
  Serial.println("");


}
