// pins for the encoder inputs

String test;
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
uint8_t i;
unsigned long time;

// ======== Beta2B PID Vals=====================
//  PID Constants
int Kp_Beta2B = 50; // Proportional Gain of PID
int Ki_Beta2B = 4; // Integral Gain of PID
int Kd_Beta2B = 0; // Derivative Gain of PID

// Beta2B vars that change every iteration
int Count_Beta2B = 0;
float Pos_Beta2B=0;
float PosErr_Beta2B = 0;
float PosErr_Beta2B_old = 0;
float tmpSpeed_Beta2B = 0;
float dErrDt_Beta2B = 0;
float dPosErr_Beta2B=0;
float IntOld_Beta2B=0;
float IntNow_Beta2B=0;
int CmdSpeed_Beta2B=0;
// =============================================

// ======== Beta4B PID Vals=====================
//  PID Constants
int Kp_Beta4B = 50; // Proportional Gain of PID
int Ki_Beta4B = 4; // Integral Gain of PID
int Kd_Beta4B = 0; // Derivative Gain of PID

// Beta4B vars that change every iteration
int Count_Beta4B = 0;
float Pos_Beta4B=0;
float PosErr_Beta4B = 0;
float PosErr_Beta4B_old = 0;
float tmpSpeed_Beta4B = 0;
float dErrDt_Beta4B = 0;
float dPosErr_Beta4B=0;
float IntOld_Beta4B=0;
float IntNow_Beta4B=0;
int CmdSpeed_Beta4B=0;
// =============================================

// ======== PSARJ PID Vals=====================
//  PID Constants
int Kp_PSARJ = 50; // Proportional Gain of PID
int Ki_PSARJ = 4; // Integral Gain of PID
int Kd_PSARJ = 0; // Derivative Gain of PID

// PSARJ vars that change every iteration
int Count_PSARJ = 0;
float Pos_PSARJ=0;
float PosErr_PSARJ = 0;
float PosErr_PSARJ_old = 0;
float tmpSpeed_PSARJ = 0;
float dErrDt_PSARJ = 0;
float dPosErr_PSARJ=0;
float IntOld_PSARJ=0;
float IntNow_PSARJ=0;
int CmdSpeed_PSARJ=0;
// =============================================



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

double Beta1B = 0.0;
double Beta2B = 0.0;
double Beta3B = 0.0;
double Beta4B = 0.0;
double Beta1A = 0.0;
double Beta2A = 0.0;
double Beta3A = 0.0;
double Beta4A = 0.0;
double PSARJ = -1.0;
double SSARJ = 0.0;
double PTRRJ = 0.0;
double STRRJ = 0.0;
boolean AOS = false;



