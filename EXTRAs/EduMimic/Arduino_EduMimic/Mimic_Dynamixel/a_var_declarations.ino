
// pins for the encoder inputs

String test;

// ===== Initializations ==========

// These are some arbitrary starting positions to set the motors to. This is so they will move a little upon startup. 
double B1A = 330.0;
double B3A = 330.0;
double B1B = 330.0;
double B3B = 330.0;

double B2B = 330.0;
double B4B = 330.0; 
double B2A = 330.0;
double B4A = 330.0;

double PSARJ = 30.0;
double SSARJ = 0.0;

// These values will be read from the model to determine the actual angles in the model
double B1A_PosAct = 0;
double B3A_PosAct = 0;
double B1B_PosAct = 0;
double B3B_PosAct = 0;
double B2B_PosAct = 0;
double B4B_PosAct = 0; 
double B2A_PosAct = 0;
double B4A_PosAct = 0;
double PSARJ_PosAct = 0;
double SSARJ_PosAct = 0;

// These values will be read from the model to get current (milli-Amps). 
double B1A_Cur = 0;
double B3A_Cur = 0;
double B1B_Cur = 0;
double B3B_Cur = 0;
double B2B_Cur = 0;
double B4B_Cur = 0; 
double B2A_Cur = 0;
double B4A_Cur = 0;
double PSARJ_Cur = 0;
double SSARJ_Cur = 0;
// this is really a 1 or zero, indicating if the motor is set to receive tq
double   B1A_TqStat = 0;
double   B3A_TqStat = 0;
double   B1B_TqStat = 0;
double   B3B_TqStat = 0;
double   B2B_TqStat = 0;
double   B4B_TqStat = 0; 
double   B2A_TqStat = 0;
double   B4A_TqStat = 0;
double   PSARJ_TqStat = 0;
double   SSARJ_TqStat = 0;



double PTRRJ = -10.0; // TRRJ's expect +/- 180 deg commands (limited to +/- 135-ish on ISS).  Requires custom scaling later.
double STRRJ = 0.0;
boolean AOS = false;



unsigned int DXL_ID_B1A = 10;
unsigned int DXL_ID_B3A = 9;
unsigned int DXL_ID_B1B = 11;
unsigned int DXL_ID_B3B = 12;

unsigned int DXL_ID_B2B = 2;
unsigned int DXL_ID_B4B = 1;
unsigned int DXL_ID_B2A = 3;
unsigned int DXL_ID_B4A = 4;

unsigned int DXL_ID_PSARJ = 5;
unsigned int DXL_ID_SSARJ = 8;
unsigned int servonum_PTRRJ = 6;
unsigned int servonum_STRRJ = 7;


int pulselen_PTRRJ = 0;
int pulselen_STRRJ = 0;
