void loop() {
delay(1);
int  debug_mode=6;
  B2A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  B4A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  B2B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  B4B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  PTRRJ=104*sin(1*3.14159*0.01*millis()/1000.0); 


  // ========= Servo Stuff =============================
  //map(value, fromLow, fromHigh, toLow, toHigh)
     servo1.write(map(PTRRJ, -115,115, 0, 255)); // from +/- 115deg to servo command min and max.
     servo2.write(map(PTRRJ, -115,115, 0, 255)); // from +/- 115deg to servo command min and max.
  //servo1.write(PTRRJ+180);
  //servo2.write(PTRRJ+180);

  delay(1);
  //delay(10);
//  for (i = 255; i != 0; i--) {
//    servo1.write(map(i, 0, 255, 0, 180));
//    delay(1);
//  }
  //delay(10);
  // ==================================================

  // ============== Time measures ===================================================
  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = (float) delta_t_millis;
  millisChPt1 = millis() - LoopStartMillis;
  // ================================================================================

  Count_B2B = myEnc2B.read(); // Feb08
  Count_B4B = myEnc4B.read();
  Count_B2A = myEnc2A.read();
  Count_B4A = myEnc4A.read();
  //   Serial.println(currentPosition); //shows you the current position in the serial monitor  // Feb08

  // ============== BGA 2A ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B2A = float(Count_B2A) / 5;

  PosErr_B2A = B2A - Pos_B2A; // Compute Pos_B2Aition Error
  dPosErr_B2A = PosErr_B2A - PosErr_old_B2A;

  if (abs(PosErr_B2A) < 0.1) {
    PosErr_B2A = 0;
    dPosErr_B2A = 0;
    PosErr_old_B2A = 0;
    IntOld_B2A = 0;
    //Serial.println("Small2A Err");
  }

  dErrDt_B2A = dPosErr_B2A * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B2A = IntOld_B2A + PosErr_B2A * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_B2A = IntNow_B2A;

  // Integrator reset when error sign changes
  if (PosErr_old_B2A * PosErr_B2A <= 0) { // sign on error has changed or is zero
    IntNow_B2A = 0;
    IntOld_B2A = 0;
  }
  PosErr_old_B2A = PosErr_B2A; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B2A = Kp_B2A * PosErr_B2A + Kd_B2A * (dErrDt_B2A) + Ki_B2A * IntNow_B2A;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B2A = abs(tmpSpeed_B2A);
  if ((CmdSpeed_B2A < 40) && (CmdSpeed_B2A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B2A = 40;
  }

 CmdSpeed_B2A = max(min(CmdSpeed_B2A, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B2A > 0) {
    myMotorB2A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB2A->run(BACKWARD);
  }
  myMotorB2A->setSpeed(CmdSpeed_B2A);// + 20);
  //=====================================================================================

  // ============== BGA 2B ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B2B = float(Count_B2B) / 5;

  PosErr_B2B = B2B - Pos_B2B; // Compute Pos_B2Bition Error
  dPosErr_B2B = PosErr_B2B - PosErr_old_B2B;

  if (abs(PosErr_B2B) < 0.1) {
    PosErr_B2B = 0;
    dPosErr_B2B = 0;
    PosErr_old_B2B = 0;
    IntOld_B2B = 0;
    //Serial.println("Small2B Err");
  }

  dErrDt_B2B = dPosErr_B2B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B2B = IntOld_B2B + PosErr_B2B * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_B2B = IntNow_B2B;

  // Integrator reset when error sign changes
  if (PosErr_old_B2B * PosErr_B2B <= 0) { // sign on error has changed or is zero
    IntNow_B2B = 0;
    IntOld_B2B = 0;
  }
  PosErr_old_B2B = PosErr_B2B; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B2B = Kp_B2B * PosErr_B2B + Kd_B2B * (dErrDt_B2B) + Ki_B2B * IntNow_B2B;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B2B = abs(tmpSpeed_B2B);
  if ((CmdSpeed_B2B < 40) && (CmdSpeed_B2B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B2B = 40;
  }

  CmdSpeed_B2B = max(min(CmdSpeed_B2B, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B2B > 0) {
    myMotorB2B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB2B->run(BACKWARD);
  }
  myMotorB2B->setSpeed(CmdSpeed_B2B);// + 20);
  //=====================================================================================

  // ============== BGA 4A ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B4A = float(Count_B4A) / 5;

  PosErr_B4A = B4A - Pos_B4A; // Compute Pos_B4Aition Error
  dPosErr_B4A = PosErr_B4A - PosErr_old_B4A;

  if (abs(PosErr_B4A) < 0.1) {
    PosErr_B4A = 0;
    dPosErr_B4A = 0;
    PosErr_old_B4A = 0;
    IntOld_B4A = 0;
    //Serial.println("Small4A Err");
  }

  dErrDt_B4A = dPosErr_B4A * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B4A = IntOld_B4A + PosErr_B4A * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_B4A = IntNow_B4A;

  // Integrator reset when error sign changes
  if (PosErr_old_B4A * PosErr_B4A <= 0) { // sign on error has changed or is zero
    IntNow_B4A = 0;
    IntOld_B4A = 0;
  }
  PosErr_old_B4A = PosErr_B4A; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B4A = Kp_B4A * PosErr_B4A + Kd_B4A * (dErrDt_B4A) + Ki_B4A * IntNow_B4A;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B4A = abs(tmpSpeed_B4A);
  if ((CmdSpeed_B4A < 40) && (CmdSpeed_B4A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B4A = 40;
  }

  CmdSpeed_B4A = max(min(CmdSpeed_B4A, 250), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B4A > 0) {
    myMotorB4A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB4A->run(BACKWARD);
  }
  myMotorB4A->setSpeed(CmdSpeed_B4A);// + 20);
  //=====================================================================================


  // ============== BGA 4B ==========================================================

  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
  Pos_B4B = float(Count_B4B) / 5;

  PosErr_B4B = B4B - Pos_B4B; // Compute Pos_B4Bition Error
  dPosErr_B4B = PosErr_B4B - PosErr_old_B4B;

  if (abs(PosErr_B4B) < 0.1) {
    PosErr_B4B = 0;
    dPosErr_B4B = 0;
    PosErr_old_B4B = 0;
    IntOld_B4B = 0;
    //Serial.println("Small4B Err");
  }

  dErrDt_B4B = dPosErr_B4B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_B4B = IntOld_B4B + PosErr_B4B * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_B4B = IntNow_B4B;

  // Integrator reset when error sign changes
  if (PosErr_old_B4B * PosErr_B4B <= 0) { // sign on error has changed or is zero
    IntNow_B4B = 0;
    IntOld_B4B = 0;
  }
  PosErr_old_B4B = PosErr_B4B; // For use on the next iteration

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_B4B = Kp_B4B * PosErr_B4B + Kd_B4B * (dErrDt_B4B) + Ki_B4B * IntNow_B4B;
  // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_B4B = abs(tmpSpeed_B4B);
  if ((CmdSpeed_B4B < 40) && (CmdSpeed_B4B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
    CmdSpeed_B4B = 40;
  }

  CmdSpeed_B4B = max(min(CmdSpeed_B4B, 250), 0); // At least 0, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_B4B > 0) {
    myMotorB4B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB4B->run(BACKWARD);
  }
  myMotorB4B->setSpeed(CmdSpeed_B4B);// + 20);
  //=====================================================================================

  //  // ============== PSARJ    ============================================================
  //  Pos_PSARJ = float(Count_PSARJ) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;
  //
  //  PosErr_PSARJ = PSARJ - Pos_PSARJ; // Compute Pos_PSARJition Error
  //  dPosErr_PSARJ = PosErr_PSARJ - PosErr_old_PSARJ;
  //  dErrDt_PSARJ = dPosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  //  IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Integrator
  //  IntOld_PSARJ = IntNow_PSARJ;
  //  PosErr_old_PSARJ = PosErr_PSARJ; // For use on the next iteration
  //  // Integrator reset when error sign changes
  //  if (PosErr_old_PSARJ * PosErr_PSARJ < 0) { // sign on error has changed
  //    IntNow_PSARJ = 0;
  //    IntOld_PSARJ = 0;
  //  }
  //
  //  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  //  tmpSpeed_PSARJ = Kp_PSARJ * PosErr_PSARJ + Kd_PSARJ * (dErrDt_PSARJ) + Ki_PSARJ * IntNow_PSARJ;
  //  CmdSpeed_PSARJ = map(abs(tmpSpeed_PSARJ), 2, 250, 2, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  //  CmdSpeed_PSARJ = max(min(CmdSpeed_PSARJ, 150), 0); // At least 10, at most 250.  Update as needed per motor.
  //
  //  // Set motor speed
  //  if (tmpSpeed_PSARJ < 0) {
  //    myMotorPSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  //  }
  //  else {
  //    myMotorPSARJ->run(BACKWARD);
  //  }
  //  myMotorPSARJ->setSpeed(CmdSpeed_PSARJ);// + 20);
  //  //====================================================================================

  millisChPt2 = millis() - LoopStartMillis;

if (debug_mode==5){
Serial.print("[Joint]:Cmd,Act,Err|  ");
Serial.print("2A:c");
Serial.print(B2A);
Serial.print(",a");
Serial.print(Pos_B2A);
Serial.print(",e");
Serial.print(PosErr_B2A);

Serial.print("|,  ");
Serial.print("4A:c");
Serial.print(B4A);
Serial.print(",a");
Serial.print(Pos_B4A);
Serial.print(",e");
Serial.print(PosErr_B4A);

Serial.print("|,  ");
Serial.print("2B:c");
Serial.print(B2B);
Serial.print(",a");
Serial.print(Pos_B2B);
Serial.print(",e");
Serial.print(PosErr_B2B);

Serial.print("|,  ");
Serial.print("4B:c");
Serial.print(B4B);
Serial.print(",a");
Serial.print(Pos_B4B);
Serial.print(",e");
Serial.print(PosErr_B4B);
Serial.print("|,");
Serial.println("");
}
  


if (debug_mode==6){
Serial.print(PosErr_B2A);

Serial.print(", ");
Serial.print(PosErr_B4A);

Serial.print(", ");
Serial.print(PosErr_B2B);

Serial.print(", ");
Serial.print(PosErr_B4B);
Serial.println("");
}








  
  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;

  delay(3);
}
