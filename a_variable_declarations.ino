// pins for the encoder inputs


int rightCount = 0;
float Pos=0;
//double targetCount = 1000;//-1000; // later overwritten by PSARJ value
float PosErr = 0;
unsigned long time;
float tmpSpeed = 0;
float tmpSpeed2 = 0;

// === for PID  ========
int Kp = 50; // Proportional Gain of PID
int Ki = 4; // Integral Gain of PID
int Kd = 0; // Derivative Gain of PID
unsigned long previousMillis = 0;
unsigned long LoopStartMillis = 0;
// For debugging
unsigned long millisChPt1 = 0;
unsigned long millisChPt2 = 0;
unsigned long millisChPt3 = 0;
unsigned long millisChPt4 = 0;
unsigned long millisChPt5 = 0;
unsigned long millisChPt6 = 0;
int LEDstatus=0; 
//
unsigned long  delta_t_millis = 1;
float inverse_delta_t_millis = 1;
float dErr_dt = 0;
float PosErr_old = 0;
float dPosErr=0;
float Int_Old=0;
float Int_Now=0;

uint8_t i;
int CmdSpeed;
int MyFlag;
String response="";

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



