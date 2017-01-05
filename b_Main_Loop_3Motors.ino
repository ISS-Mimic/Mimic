void loop() {

  if (Serial1.available())
  {
    checkSerial();
  }
  // === DELETE THIS!  JUST FOR TESTING!!! =====
  //PSARJ=millis()*.0005;
  //PSARJ = 90 * sin(0.0005 * millis() * 0.001 * 180 / 3.14159);
  // === DELETE THIS!  JUST FOR TESTING!!! =====

  // ============== Time measures ===================================================
  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = (float) delta_t_millis;
  millisChPt1 = millis() - LoopStartMillis;
  // ================================================================================


  // ============== BGA 2B ==========================================================
  Pos_Beta2B = float(Count_Beta2B) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;

  PosErr_Beta2B = Beta2B - Pos_Beta2B; // Compute Pos_Beta2Bition Error
  dPosErr_Beta2B = PosErr_Beta2B - PosErr_Beta2B_old;
  dErrDt_Beta2B = dPosErr_Beta2B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_Beta2B = IntOld_Beta2B + PosErr_Beta2B * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_Beta2B = IntNow_Beta2B;
  PosErr_Beta2B_old = PosErr_Beta2B; // For use on the next iteration
  // Integrator reset when error sign changes
  if (PosErr_Beta2B_old * PosErr_Beta2B < 0) { // sign on error has changed
    IntNow_Beta2B = 0;
    IntOld_Beta2B = 0;
  }
  
  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_Beta2B = Kp_Beta2B * PosErr_Beta2B + Kd_Beta2B * (dErrDt_Beta2B) + Ki_Beta2B * IntNow_Beta2B;
  CmdSpeed_Beta2B = map(abs(tmpSpeed_Beta2B), 2, 250, 40, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_Beta2B = max(min(CmdSpeed_Beta2B, 250), 10); // At least 10, at most 250.  Update as needed per motor.
  
  // Set motor speed
  if (tmpSpeed_Beta2B < 0) {    myMotorBeta2B->run(FORWARD);}   // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  else {    myMotorBeta2B->run(BACKWARD);}
  myMotorBeta2B->setSpeed(CmdSpeed_Beta2B);// + 20);
  //=====================================================================================

  // ============== BGA 4B ==========================================================
  Pos_Beta4B = float(Count_Beta4B) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;

  PosErr_Beta4B = Beta4B - Pos_Beta4B; // Compute Pos_Beta4Bition Error
  dPosErr_Beta4B = PosErr_Beta4B - PosErr_Beta4B_old;
  dErrDt_Beta4B = dPosErr_Beta4B * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_Beta4B = IntOld_Beta4B + PosErr_Beta4B * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_Beta4B = IntNow_Beta4B;
  PosErr_Beta4B_old = PosErr_Beta4B; // For use on the next iteration
  // Integrator reset when error sign changes
  if (PosErr_Beta4B_old * PosErr_Beta4B < 0) { // sign on error has changed
    IntNow_Beta4B = 0;
    IntOld_Beta4B = 0;
  }
  
  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_Beta4B = Kp_Beta4B * PosErr_Beta4B + Kd_Beta4B * (dErrDt_Beta4B) + Ki_Beta4B * IntNow_Beta4B;
  CmdSpeed_Beta4B = map(abs(tmpSpeed_Beta4B), 2, 250, 40, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_Beta4B = max(min(CmdSpeed_Beta4B, 250), 10); // At least 10, at most 250.  Update as needed per motor.
  
  // Set motor speed
  if (tmpSpeed_Beta4B < 0) {    myMotorBeta4B->run(FORWARD);}   // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  else {    myMotorBeta4B->run(BACKWARD);}
  myMotorBeta4B->setSpeed(CmdSpeed_Beta4B);// + 20);
  //=====================================================================================

  // ============== PSARJ    ============================================================
  Pos_PSARJ = float(Count_PSARJ) / 2.5; // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;

  PosErr_PSARJ = PSARJ - Pos_PSARJ; // Compute Pos_PSARJition Error
  dPosErr_PSARJ = PosErr_PSARJ - PosErr_PSARJ_old;
  dErrDt_PSARJ = dPosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Integrator
  IntOld_PSARJ = IntNow_PSARJ;
  PosErr_PSARJ_old = PosErr_PSARJ; // For use on the next iteration
  // Integrator reset when error sign changes
  if (PosErr_PSARJ_old * PosErr_PSARJ < 0) { // sign on error has changed
    IntNow_PSARJ = 0;
    IntOld_PSARJ = 0;
  }
  
  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
  tmpSpeed_PSARJ = Kp_PSARJ * PosErr_PSARJ + Kd_PSARJ * (dErrDt_PSARJ) + Ki_PSARJ * IntNow_PSARJ;
  CmdSpeed_PSARJ = map(abs(tmpSpeed_PSARJ), 2, 250, 40, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  CmdSpeed_PSARJ = max(min(CmdSpeed_PSARJ, 250), 10); // At least 10, at most 250.  Update as needed per motor.
  
  // Set motor speed
  if (tmpSpeed_PSARJ < 0) {    myMotorPSARJ->run(FORWARD);}   // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  else {    myMotorPSARJ->run(BACKWARD);}
  myMotorPSARJ->setSpeed(CmdSpeed_PSARJ);// + 20);
  //====================================================================================

  millisChPt2 = millis() - LoopStartMillis;

  delay(10);

// Legacy vals used just for debugging....
  if (1) {
    response = ""; // empty it
    response += " | rghtCnt ";
    response += Count_Beta2B;
    response += " | Pos_Beta2B ";
    response += Pos_Beta2B;
    response += " | PSARJ:";
    response += PSARJ;
    response += " | PsErr:";
    response += PosErr_Beta2B;
    response += " | MyFlag";
    response += MyFlag;
    response += " |||CmdSpd:";
    response += CmdSpeed_Beta2B;
    response += " |||PSARJ:";
    response += PSARJ;
    millisChPt3 = millis() - LoopStartMillis;
    response += " |||delta_t_millis:";
    response += delta_t_millis;
    //    response+= " |||inv_delta_t_mlis:";
    //response+= inverse_delta_t_millis;
    response += "|millis";
    response += LoopStartMillis;
    response += " ||**|IntNow_Beta2B:";

    response += "|C1:";
    response += millisChPt1;
    response += "|C2:";
    response += millisChPt2;
    response += "|C3:";
    response += millisChPt3;

    response += "|C4:";
    response += millisChPt4;
    response += "|C5:";
    response += millisChPt5;
    response += "|C6:";
    response += millisChPt6;
    response += "LED:";
    response += LEDstatus;
    millisChPt4 = millis() - LoopStartMillis;
    Serial.println(response);
    millisChPt5 = millis() - LoopStartMillis;
  }


  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;


}
