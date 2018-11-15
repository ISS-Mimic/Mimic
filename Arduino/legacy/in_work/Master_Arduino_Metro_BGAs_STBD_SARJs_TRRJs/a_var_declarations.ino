// pins for the encoder inputs

String test;
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
uint8_t i;
unsigned long mytime;

// ======== B1B PID Vals=====================
//  PID Constants
float Kp_B1B = 40; // Proportional Gain of PID
float Ki_B1B = 5; // Integral Gain of PID
float Kd_B1B = 10*0; // Derivative Gain of PID

// B1B vars that change every iteration
int Count_B1B = 0;
float Pos_B1B=0;
float PosErr_B1B = 0;
float PosErr_old_B1B = 0;
float tmpSpeed_B1B = 0;
float dErrDt_B1B = 0;
float dPosErr_B1B=0;
float IntOld_B1B=0;
float IntNow_B1B=0;
int CmdSpeed_B1B=0;
// =============================================

// ======== B3B PID Vals=====================
//  PID Constants
float Kp_B3B = 20; // Proportional Gain of PID
float Ki_B3B = 5; // Integral Gain of PID
float Kd_B3B = 0; // Derivative Gain of PID

// B3B vars that change every iteration
int Count_B3B = 0;
float Pos_B3B=0;
float PosErr_B3B = 0;
float PosErr_old_B3B = 0;
float tmpSpeed_B3B = 0;
float dErrDt_B3B = 0;
float dPosErr_B3B=0;
float IntOld_B3B=0;
float IntNow_B3B=0;
int CmdSpeed_B3B=0;
// =============================================

// ======== B1A PID Vals=====================
//  PID Constants
float Kp_B1A = 20; // Proportional Gain of PID
float Ki_B1A = 0; // Integral Gain of PID
float Kd_B1A = 0; // Derivative Gain of PID

// B1A vars that change every iteration
int Count_B1A = 0;
float Pos_B1A=0;
float PosErr_B1A = 0;
float PosErr_old_B1A = 0;
float tmpSpeed_B1A = 0;
float dErrDt_B1A = 0;
float dPosErr_B1A=0;
float IntOld_B1A=0;
float IntNow_B1A=0;
int CmdSpeed_B1A=0;
// =============================================

// ======== B3A PID Vals=====================
//  PID Constants
float Kp_B3A = 20; // Proportional Gain of PID
float Ki_B3A = 0; // Integral Gain of PID
float Kd_B3A = 0; // Derivative Gain of PID

// B3A vars that change every iteration
int Count_B3A = 0;
float Pos_B3A=0;
float PosErr_B3A = 0;
float PosErr_old_B3A = 0;
float tmpSpeed_B3A = 0;
float dErrDt_B3A = 0;
float dPosErr_B3A=0;
float IntOld_B3A=0;
float IntNow_B3A=0;
int CmdSpeed_B3A=0;
// =============================================

//// ======== PSARJ PID Vals=====================
////  PID Constants
float Kp_PSARJ = 50; // Proportional Gain of PID
float Ki_PSARJ = 0; // Integral Gain of PID
float Kd_PSARJ = 0; // Derivative Gain of PID

// PSARJ vars that change every iteration
int Count_PSARJ = 0;
float Pos_PSARJ=0;
float PosErr_PSARJ = 0;
float PosErr_old_PSARJ = 0;
float tmpSpeed_PSARJ = 0;
float dErrDt_PSARJ = 0;
float dPosErr_PSARJ=0;
float IntOld_PSARJ=0;
float IntNow_PSARJ=0;
int CmdSpeed_PSARJ=0;
//// =============================================


//// ======== SSARJ PID Vals=====================
////  PID Constants
float Kp_SSARJ = 50; // Proportional Gain of PID
float Ki_SSARJ = 0; // Integral Gain of PID
float Kd_SSARJ = 0; // Derivative Gain of PID

// SSARJ vars that change every iteration
int Count_SSARJ = 0;
float Pos_SSARJ=0;
float PosErr_SSARJ = 0;
float PosErr_old_SSARJ = 0;
float tmpSpeed_SSARJ = 0;
float dErrDt_SSARJ = 0;
float dPosErr_SSARJ=0;
float IntOld_SSARJ=0;
float IntNow_SSARJ=0;
int CmdSpeed_SSARJ=0;
//// =============================================


// For debugging
int MyFlag;
String response="";
unsigned long millisChPt1 = 0;
unsigned long millisChPt2 = 0;
unsigned long millisChPt3 = 0;
unsigned long millisChPt4 = 0;
unsigned long millisChPt5 = 0;
unsigned long millisChPt6 = 0;
int LEDstatus=0; 
int ManualSpeed=90; // MANUAL OVERRIDE

// ===== Initializations ==========
//PSARJ

boolean PSARJstartup = true;
double PSARJdiff = 0.00;
double oldPSARJstep = 0.00;
double oldPSARJangle = 0.00;
double oldPSARJ = 0.00;
double PSARJcheck = 0.00;
double PSARJstep = 0.00;


//SSARJ

boolean SSARJstartup = true;
double SSARJdiff = 0.00;
double oldSSARJstep = 0.00;
double oldSSARJangle = 0.00;
double oldSSARJ = 0.00;
double SSARJcheck = 0.00;
double SSARJstep = 0.00;
double B1A = 30.0;
double B3A = 30.0;
double B1B = -180.0;
double B3B = 30.0;

double B2B = 30.0;
double B4B = 30.0;
double B2A = 30.0;
double B4A = 30.0;

double PSARJ = -10.0;
double SSARJ = 0.0;
double PTRRJ = -10.0;
double STRRJ = 0.0;
boolean AOS = false;
