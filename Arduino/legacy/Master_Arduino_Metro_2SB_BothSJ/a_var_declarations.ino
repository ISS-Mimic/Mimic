// pins for the encoder inputs
int run_internal_pos_command_flag=1;
String test;
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
uint8_t i;
unsigned long mytime;

// ======== B2B PID Vals=====================
//  PID Constants
float Kp_B2B = 20; // Proportional Gain of PID
float Ki_B2B = 5*0; // Integral Gain of PID
float Kd_B2B = 10*0; // Derivative Gain of PID

// B2B vars that change every iteration
int Count_B2B = 0;
float Pos_B2B=0;
float PosErr_B2B = 0;
float PosErr_old_B2B = 0;
float tmpSpeed_B2B = 0;
float dErrDt_B2B = 0;
float dPosErr_B2B=0;
float IntOld_B2B=0;
float IntNow_B2B=0;
int CmdSpeed_B2B=0;
// =============================================

// ======== B4B PID Vals=====================
//  PID Constants
float Kp_B4B = 20; // Proportional Gain of PID
float Ki_B4B = 5; // Integral Gain of PID
float Kd_B4B = 0; // Derivative Gain of PID

// B4B vars that change every iteration
int Count_B4B = 0;
float Pos_B4B=0;
float PosErr_B4B = 0;
float PosErr_old_B4B = 0;
float tmpSpeed_B4B = 0;
float dErrDt_B4B = 0;
float dPosErr_B4B=0;
float IntOld_B4B=0;
float IntNow_B4B=0;
int CmdSpeed_B4B=0;
// =============================================

// ======== B2A PID Vals=====================
//  PID Constants
float Kp_B2A = 20; // Proportional Gain of PID
float Ki_B2A = 0; // Integral Gain of PID
float Kd_B2A = 0; // Derivative Gain of PID

// B2A vars that change every iteration
int Count_B2A = 0;
float Pos_B2A=0;
float PosErr_B2A = 0;
float PosErr_old_B2A = 0;
float tmpSpeed_B2A = 0;
float dErrDt_B2A = 0;
float dPosErr_B2A=0;
float IntOld_B2A=0;
float IntNow_B2A=0;
int CmdSpeed_B2A=0;
// =============================================

// ======== B4A PID Vals=====================
//  PID Constants
float Kp_B4A = 20; // Proportional Gain of PID
float Ki_B4A = 0; // Integral Gain of PID
float Kd_B4A = 0; // Derivative Gain of PID

// B4A vars that change every iteration
int Count_B4A = 0;
float Pos_B4A=0;
float PosErr_B4A = 0;
float PosErr_old_B4A = 0;
float tmpSpeed_B4A = 0;
float dErrDt_B4A = 0;
float dPosErr_B4A=0;
float IntOld_B4A=0;
float IntNow_B4A=0;
int CmdSpeed_B4A=0;
// =============================================

//// ======== PSARJ PID Vals=====================
////  PID Constants
float Kp_PSARJ = 20; // Proportional Gain of PID
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

double B1B = 30.0;
double B2B = 30.0;
double B3B = 30.0;
double B4B = 30.0;
double B1A = 30.0;
double B2A = 30.0;
double B3A = 30.0;
double B4A = 30.0;
double PSARJ = -10.0;
double SSARJ = 0.0;
double PTRRJ = -10.0;
double STRRJ = 0.0;
boolean AOS = false;


