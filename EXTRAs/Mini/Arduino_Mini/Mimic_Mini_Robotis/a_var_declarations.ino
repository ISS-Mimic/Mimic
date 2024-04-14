
// pins for the encoder inputs

String test;

// ===== Initializations ==========

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
double PTRRJ = -10.0; // TRRJ's expect +/- 180 deg commands (limited to +/- 135-ish on ISS).  Requires custom scaling later.
double STRRJ = 0.0;
boolean AOS = false;

int MiniAllServoVals=0;

int Mini_MinPosServos_Flag =0;
int Mini_MidPosServos_Flag =0; // This is used to center all 12 servos.  Helpful for initial setup.  Put this command into the Serial Monitor (no "'s, and no _Flag): Mini_MidPosServos=1
int Mini_MaxPosServos_Flag =0;
int Mini_ServosInstallPos_Flag =0; // This is to put servos in proper postion for initial installation.

int DXL_ID_B1A = 10;
int DXL_ID_B3A = 9;
int DXL_ID_B1B = 11;
int DXL_ID_B3B = 12;

int DXL_ID_B2B = 2;
int DXL_ID_B4B = 1;
int DXL_ID_B2A = 3;
int DXL_ID_B4A = 4;

int DXL_ID_PSARJ = 5;
int DXL_ID_SSARJ = 8;
int servonum_PTRRJ = 7;
int servonum_STRRJ = 6;




//int pulselen_B1A = 0;
//int pulselen_B3A = 0;
//int pulselen_B1B = 0; 
//int pulselen_B3B = 0;
//
//int pulselen_B2B = 0;
//int pulselen_B4B = 0;
//int pulselen_B2A = 0;
//int pulselen_B4A = 0;
//
//int pulselen_PSARJ = 0;
//int pulselen_SSARJ = 0;
int pulselen_PTRRJ = 0;
int pulselen_STRRJ = 0;
