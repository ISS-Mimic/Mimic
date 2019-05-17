void loop() {


  D0 = digitalRead(0);
  D1 = digitalRead(1);
    D2 = digitalRead(2);
  D3 = digitalRead(3);
//  D4 = digitalRead(4);
//  D5 = digitalRead(5);
//  D6 = digitalRead(6);
  D7 = digitalRead(7);
    D8 = digitalRead(8);
//  D9= digitalRead(9);
//  D10= digitalRead(10);
  D11 = digitalRead(11);
  D12 = digitalRead(12);
  //D13 = digitalRead(13);
  ////D14 = digitalRead(14);
  D15 = digitalRead(15);
  D16 = digitalRead(16);
  D17 = digitalRead(17);



  delay(1);
  if (Serial.available())
  {
    checkSerial();
  }

  int  debug_mode = 8;
  //  B2A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B4A = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B2B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  B4B = 100 + 90.0* sin(2.0 * 3.14159 * 0.01 * millis() / 1000.0);
  //  PTRRJ=104*sin(1*3.14159*0.01*millis()/1000.0);


  // ========= Servo Stuff =============================
  //map(value, fromLow, fromHigh, toLow, toHigh)
  //  servo_PTRRJ.write(map(PTRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
  //  servo_STRRJ.write(map(STRRJ, -115, 115, 0, 180)); // from +/- 115deg to servo command min and max.
  //servo_PTRRJ.write(PTRRJ+180);
  //servo_STRRJ.write(PTRRJ+180);

  delay(1);
  //delay(10);
  //  for (i = 255; i != 0; i--) {
  //    servo_PTRRJ.write(map(i, 0, 255, 0, 180));
  //    delay(1);
  //  }
  //delay(10);
  // ==================================================

  // ============== Time measures ===================================================
  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = 1 / ((float) delta_t_millis); // BCM mod 10/28/2018: for some reason, was not inverted (just = value, rather than 1/value).
  millisChPt1 = millis() - LoopStartMillis;
  // ================================================================================

//  Count_B2B = myEnc2B.read(); // Feb08
//  Count_B4B = myEnc4B.read();
//  Count_B2A = myEnc2A.read();
//  Count_B4A = myEnc4A.read();
  Count_PSARJ = myEncPSARJ.read();
  Count_SSARJ = myEncSSARJ.read();
  //   Serial.println(currentPosition); //shows you the current position in the serial monitor  // Feb08

//  // ============== BGA 2A ==========================================================
//
//  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
//  Pos_B2A = float(Count_B2A) / 5;
//
//  PosErr_B2A = B2A - Pos_B2A; // Compute Pos_B2Aition Error
//  dPosErr_B2A = PosErr_B2A - PosErr_old_B2A;
//
//  if (abs(PosErr_B2A) < 0.1) {
//    PosErr_B2A = 0;
//    dPosErr_B2A = 0;
//    PosErr_old_B2A = 0;
//    IntOld_B2A = 0;
//    //Serial.println("Small2A Err");
//  }
//
//  dErrDt_B2A = dPosErr_B2A * inverse_delta_t_millis * 0.001; // For Derivative
//  //IntNow_B2A = IntOld_B2A + PosErr_B2A * inverse_delta_t_millis * 0.001; // For Integrator
//  IntNow_B2A = IntOld_B2A + PosErr_B2A * delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
//  IntOld_B2A = IntNow_B2A;
//
//  // Integrator reset when error sign changes
//  if (PosErr_old_B2A * PosErr_B2A <= 0) { // sign on error has changed or is zero
//    IntNow_B2A = 0;
//    IntOld_B2A = 0;
//  }
//  PosErr_old_B2A = PosErr_B2A; // For use on the next iteration
//
//  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
//  tmpSpeed_B2A = Kp_B2A * PosErr_B2A + Kd_B2A * (dErrDt_B2A) + Ki_B2A * IntNow_B2A;
//  // Deadband seems to be about 40 (for 5V input to motor board);
//  CmdSpeed_B2A = abs(tmpSpeed_B2A);
//  if ((CmdSpeed_B2A < 40) && (CmdSpeed_B2A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
//    CmdSpeed_B2A = 40;
//  }
//
//  CmdSpeed_B2A = max(min(CmdSpeed_B2A, 250), 0); // At least 10, at most 250.  Update as needed per motor.
//
//  // Set motor speed
//  if (tmpSpeed_B2A > 0) {
//    myMotorB2A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
//  }
//  else {
//    myMotorB2A->run(BACKWARD);
//  }
//  myMotorB2A->setSpeed(CmdSpeed_B2A);// + 20);
//  //=====================================================================================
//
//  // ============== BGA 2B ==========================================================
//
//  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
//  Pos_B2B = float(Count_B2B) / 5;
//
//  PosErr_B2B = B2B - Pos_B2B; // Compute Pos_B2Bition Error
//  dPosErr_B2B = PosErr_B2B - PosErr_old_B2B;
//
//  if (abs(PosErr_B2B) < 0.1) {
//    PosErr_B2B = 0;
//    dPosErr_B2B = 0;
//    PosErr_old_B2B = 0;
//    IntOld_B2B = 0;
//    //Serial.println("Small2B Err");
//  }
//
//  dErrDt_B2B = dPosErr_B2B * inverse_delta_t_millis * 0.001; // For Derivative
//  IntNow_B2B = IntOld_B2B + PosErr_B2B *  delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
//  IntOld_B2B = IntNow_B2B;
//
//  // Integrator reset when error sign changes
//  if (PosErr_old_B2B * PosErr_B2B <= 0) { // sign on error has changed or is zero
//    IntNow_B2B = 0;
//    IntOld_B2B = 0;
//  }
//  PosErr_old_B2B = PosErr_B2B; // For use on the next iteration
//
//  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
//  tmpSpeed_B2B = Kp_B2B * PosErr_B2B + Kd_B2B * (dErrDt_B2B) + Ki_B2B * IntNow_B2B;
//  // Deadband seems to be about 40 (for 5V input to motor board);
//  CmdSpeed_B2B = abs(tmpSpeed_B2B);
//  if ((CmdSpeed_B2B < 40) && (CmdSpeed_B2B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
//    CmdSpeed_B2B = 40;
//  }
//
//  CmdSpeed_B2B = max(min(CmdSpeed_B2B, 250), 0); // At least 10, at most 250.  Update as needed per motor.
//
//  // Set motor speed
//  if (tmpSpeed_B2B > 0) {
//    myMotorB2B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
//  }
//  else {
//    myMotorB2B->run(BACKWARD);
//  }
//  myMotorB2B->setSpeed(CmdSpeed_B2B);// + 20);6+9
//  //=====================================================================================
//
//  // ============== BGA 4A ==========================================================
//
//  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
//  Pos_B4A = float(Count_B4A) / 5;
//
//  PosErr_B4A = B4A - Pos_B4A; // Compute Pos_B4Aition Error
//  dPosErr_B4A = PosErr_B4A - PosErr_old_B4A;
//
//  if (abs(PosErr_B4A) < 0.1) {
//    PosErr_B4A = 0;
//    dPosErr_B4A = 0;
//    PosErr_old_B4A = 0;
//    IntOld_B4A = 0;
//    //Serial.println("Small4A Err");
//  }
//
//  dErrDt_B4A = dPosErr_B4A * inverse_delta_t_millis * 0.001; // For Derivative
//  IntNow_B4A = IntOld_B4A + PosErr_B4A *  delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
//  IntOld_B4A = IntNow_B4A;
//
//  // Integrator reset when error sign changes
//  if (PosErr_old_B4A * PosErr_B4A <= 0) { // sign on error has changed or is zero
//    IntNow_B4A = 0;
//    IntOld_B4A = 0;
//  }
//  PosErr_old_B4A = PosErr_B4A; // For use on the next iteration
//
//  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
//  tmpSpeed_B4A = Kp_B4A * PosErr_B4A + Kd_B4A * (dErrDt_B4A) + Ki_B4A * IntNow_B4A;
//  // Deadband seems to be about 40 (for 5V input to motor board);
//  CmdSpeed_B4A = abs(tmpSpeed_B4A);
//  if ((CmdSpeed_B4A < 40) && (CmdSpeed_B4A > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
//    CmdSpeed_B4A = 40;
//  }
//
//  CmdSpeed_B4A = max(min(CmdSpeed_B4A, 250), 0); // At least 10, at most 250.  Update as needed per motor.
//
//  // Set motor speed
//  if (tmpSpeed_B4A > 0) {
//    myMotorB4A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
//  }
//  else {
//    myMotorB4A->run(BACKWARD);
//  }
//  myMotorB4A->setSpeed(CmdSpeed_B4A);// + 20);
//  //=====================================================================================
//
//
//  //  // ============== BGA 4B ==========================================================
//
//  // 150 motor shaft rotations / gearbox output shaft rotation * 12 encoder counts / motor rotation  /(360 deg per /output rotation) = 150*12/360 = 5 encoder counts per output shaft degree
//  Pos_B4B = float(Count_B4B) / 5;
//
//  PosErr_B4B = B4B - Pos_B4B; // Compute Pos_B4Bition Error
//  dPosErr_B4B = PosErr_B4B - PosErr_old_B4B;
//
//  if (abs(PosErr_B4B) < 0.1) {
//    PosErr_B4B = 0;
//    dPosErr_B4B = 0;
//    PosErr_old_B4B = 0;
//    IntOld_B4B = 0;
//    //Serial.println("Small4B Err");
//  }
//
//  dErrDt_B4B = dPosErr_B4B * inverse_delta_t_millis * 0.001; // For Derivative
//  IntNow_B4B = IntOld_B4B + PosErr_B4B * delta_t_millis * 0.001; // BCM mod 10/28/2018 - shoudln't be be using inverse time, but may have been why that val was not inverted above (from prior debugging?)
//  IntOld_B4B = IntNow_B4B;
//
//  // Integrator reset when error sign changes
//  if (PosErr_old_B4B * PosErr_B4B <= 0) { // sign on error has changed or is zero
//    IntNow_B4B = 0;
//    IntOld_B4B = 0;
//  }
//  PosErr_old_B4B = PosErr_B4B; // For use on the next iteration
//
//  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.
//  tmpSpeed_B4B = Kp_B4B * PosErr_B4B + Kd_B4B * (dErrDt_B4B) + Ki_B4B * IntNow_B4B;
//  // Deadband seems to be about 40 (for 5V input to motor board);
//  CmdSpeed_B4B = abs(tmpSpeed_B4B);
//  if ((CmdSpeed_B4B < 40) && (CmdSpeed_B4B > 5)) { // We want a dead space at 5 counts, but want it to move for larger vals.
//    CmdSpeed_B4B = 40;
//  }
//
//  CmdSpeed_B4B = max(min(CmdSpeed_B4B, 250), 0); // At least 0, at most 250.  Update as needed per motor.
//
//  // Set motor speed
//  if (tmpSpeed_B4B > 0) {
//    myMotorB4B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
//  }
//  else {
//    myMotorB4B->run(BACKWARD);
//  }
//  myMotorB4B->setSpeed(CmdSpeed_B4B);// + 20);
//  //=====================================================================================

  //  // ============== PSARJ    ============================================================
  Pos_PSARJ = float(Count_PSARJ) / (5 * 40 / 12); // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;  42 teeth on bull gear. T12 pinion

  PosErr_PSARJ = PSARJ - Pos_PSARJ; // Compute Pos_PSARJition Error

  // Kill error if error within tolerance
  if (abs(PosErr_PSARJ) < 0.5) {
    PosErr_PSARJ = 0;
    IntOld_PSARJ = 0;
    PosErr_old_PSARJ = 0;
  }
  dPosErr_PSARJ = PosErr_PSARJ - PosErr_old_PSARJ;
  dErrDt_PSARJ = dPosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  // IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * inverse_delta_t_millis * 0.001; // For Integrator
  IntNow_PSARJ = IntOld_PSARJ + PosErr_PSARJ * delta_t_millis * 0.001; // For Integrator; BCM mod 10/28/2018

  int sign = 0;



  if (abs(PosErr_PSARJ) == PosErr_PSARJ) {
    sign = 1;
  }
  else {
    sign = -1;
  }

  IntNow_PSARJ = min(abs(IntNow_PSARJ), 70) * sign;

  IntOld_PSARJ = IntNow_PSARJ;
  PosErr_old_PSARJ = PosErr_PSARJ; // For use on the next iteration
  // Integrator reset when error sign changes
  if (PosErr_old_PSARJ * PosErr_PSARJ < 0) { // sign on error has changed
    IntNow_PSARJ = 0;
    IntOld_PSARJ = 0;
  }

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.

  //int sign=0;
  if (abs(PosErr_PSARJ) == PosErr_PSARJ) {
    sign = 1;
  }
  else {
    sign = -1;
  }

  int tmp_KP = sign * min(abs(PosErr_PSARJ), 100);

  tmpSpeed_PSARJ = Kp_PSARJ * tmp_KP + Kd_PSARJ * (dErrDt_PSARJ) + Ki_PSARJ * IntNow_PSARJ;

  CmdSpeed_PSARJ = min(abs(tmpSpeed_PSARJ), 255); // BCM added 10/28/2018 to limit value to 255, since expecting 8-bit integer (uint8_t).  May want to later update data type.
  //CmdSpeed_PSARJ = map(abs(tmpSpeed_PSARJ), 2, 250, 2, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  // CmdSpeed_PSARJ = max(min(CmdSpeed_PSARJ, 150), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_PSARJ < 0) {
    myMotorPSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorPSARJ->run(BACKWARD);
  }
  myMotorPSARJ->setSpeed(CmdSpeed_PSARJ);// + 20);
  //  //====================================================================================



  //  // ============== SSARJ    ============================================================
  Pos_SSARJ = float(Count_SSARJ) / (5 * 40 / 12); // / 25; // 150:1 gear ratio, 6 encoder counts per motor shaft rotation 150/6=25;  42 teeth on bull gear. T12 pinion

  PosErr_SSARJ = SSARJ - Pos_SSARJ; // Compute Pos_SSARJition Error

  // Kill error if error within tolerance
  if (abs(PosErr_SSARJ) < 0.5) {
    PosErr_SSARJ = 0;
    IntOld_SSARJ = 0;
    PosErr_old_SSARJ = 0;
  }
  dPosErr_SSARJ = PosErr_SSARJ - PosErr_old_SSARJ;
  dErrDt_SSARJ = dPosErr_SSARJ * inverse_delta_t_millis * 0.001; // For Derivative
  // IntNow_SSARJ = IntOld_SSARJ + PosErr_SSARJ * inverse_delta_t_millis * 0.001; // For Integrator
  IntNow_SSARJ = IntOld_SSARJ + PosErr_SSARJ * delta_t_millis * 0.001; // For Integrator; BCM mod 10/28/2018

  sign = 0;



  if (abs(PosErr_SSARJ) == PosErr_SSARJ) {
    sign = 1;
  }
  else {
    sign = -1;
  }

  IntNow_SSARJ = min(abs(IntNow_SSARJ), 70) * sign;

  IntOld_SSARJ = IntNow_SSARJ;
  PosErr_old_SSARJ = PosErr_SSARJ; // For use on the next iteration
  // Integrator reset when error sign changes
  if (PosErr_old_SSARJ * PosErr_SSARJ < 0) { // sign on error has changed
    IntNow_SSARJ = 0;
    IntOld_SSARJ = 0;
  }

  // Calculate motor speed setpoint based on PID constants and computed params for this iteration.

  //int sign=0;
  if (abs(PosErr_SSARJ) == PosErr_SSARJ) {
    sign = 1;
  }
  else {
    sign = -1;
  }

  tmp_KP = sign * min(abs(PosErr_SSARJ), 100);

  tmpSpeed_SSARJ = Kp_SSARJ * tmp_KP + Kd_SSARJ * (dErrDt_SSARJ) + Ki_SSARJ * IntNow_SSARJ;

  CmdSpeed_SSARJ = min(abs(tmpSpeed_SSARJ), 255); // BCM added 10/28/2018 to limit value to 255, since expecting 8-bit integer (uint8_t).  May want to later update data type.
  //CmdSpeed_SSARJ = map(abs(tmpSpeed_SSARJ), 2, 250, 2, 250); // Deadband seems to be about 40 (for 5V input to motor board);
  // CmdSpeed_SSARJ = max(min(CmdSpeed_SSARJ, 150), 0); // At least 10, at most 250.  Update as needed per motor.

  // Set motor speed
  if (tmpSpeed_SSARJ < 0) {
    myMotorSSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorSSARJ->run(BACKWARD);
  }
  myMotorSSARJ->setSpeed(CmdSpeed_SSARJ);// + 20);
  //  //====================================================================================

  millisChPt2 = millis() - LoopStartMillis;

  //if (debug_mode==5){
  //Serial1.print("[Joint]:Cmd,Act,Err|  ");
  //Serial1.print("2A:c");
  //Serial1.print(B2A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B2A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B2A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("4A:c");
  //Serial1.print(B4A);
  //Serial1.print(",a");
  //Serial1.print(Pos_B4A);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B4A);
  //
  //Serial1.print("|,  ");
  //Serial1.print("2B:c");
  //Serial1.print(B2B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B2B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B2B);
  //
  //Serial1.print("|,  ");
  //Serial1.print("4B:c");
  //Serial1.print(B4B);
  //Serial1.print(",a");
  //Serial1.print(Pos_B4B);
  //Serial1.print(",e");
  //Serial1.print(PosErr_B4B);
  //Serial1.print("|,");
  //Serial1.println("");
  //}
  //
  //
  //
  //if (debug_mode==6){
  //Serial1.print(PosErr_B2A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B4A);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B2B);
  //
  //Serial1.print(", ");
  //Serial1.print(PosErr_B4B);
  //Serial1.println("");
  //}

  if (debug_mode == 8) {
    Serial.print("|  ");
//
//    Serial.print("Count_B2A: ");
//    Serial.print(Count_B2A);
//    Serial.print(",Count_B4A: ");
//    Serial.print(Count_B4A);
//    Serial.print("Count_B2B: ");
//    Serial.print(Count_B2B);
//    Serial.print(",Count_B4B: ");
//    Serial.print(Count_B4B);

    Serial.print(",Count_PSARJ: ");
    Serial.print(Count_PSARJ);
    Serial.print(",Count_SSARJ: ");
    Serial.print(Count_SSARJ);

    Serial.print(",D0:");
    Serial.print(D0);
    Serial.print(",D1:");
    Serial.print(D1);
        Serial.print(",D2:");
        Serial.print(D2);
        Serial.print(",D3:");
        Serial.print(D3);
//    Serial.print(",D4:");
//    Serial.print(D4);
//    Serial.print(",D5: ");
//    Serial.print(D5);
//    Serial.print(",D6:");
//    Serial.print(D6);
    Serial.print(",D7: ");
    Serial.print(D7);
        Serial.print(",D8:");
        Serial.print(D8);

//    Serial.print(",D9: ");
//    Serial.print(D9);
//        Serial.print(",D10:");
//        Serial.print(D10);
        
    Serial.print(",D11: ");
    Serial.print(D11);
    Serial.print(",D12: ");
    Serial.print(D12);
    //    Serial.print(",D13: ");
    //  Serial.print(D13);
    Serial.print(",D14: ");
    Serial.print(D14);
    Serial.print(",D15: ");
    Serial.print(D15);
    Serial.print(",D16: ");
    Serial.print(D16);
    Serial.print(",D17: ");
    Serial.print(D17);

    Serial.print("| PosErrs ");
//    Serial.print(PosErr_B2A);
//    Serial.print(", ");
//    Serial.print(PosErr_B4A);
//    Serial.print(", ");
//    Serial.print(PosErr_B2B);
//    Serial.print(", ");
//    Serial.print(PosErr_B4B);
//    Serial.print(", ");
    Serial.print(PosErr_PSARJ);
    Serial.print(", ");
    Serial.print(PosErr_SSARJ);
    //
    //    Serial.print(", ");
    //    Serial.print("Integer Mtr Spd Cmd to Shield(PortSrj):");
    //    Serial.print(CmdSpeed_PSARJ);
    //Serial.print(PosErr_SSARJ);
    Serial.println("|  ");


    // LCD
    //
    //    //
    //      // LCD =======================================
    //      // text display tests
    //      display.setTextSize(1);
    //      display.setTextColor(WHITE);
    //      display.setCursor(0,0);
    //      display.setTextColor(BLACK, WHITE); // 'inverted' text
    //      display.println("Jnt|-ERR-|-CMD-|-ACT-");
    //
    //    //   display.println("3600.0|3600.0|3600.0");
    //    //     float d=12345.6789;
    //        //tostrf(floatVar, minStringWidthIncDecimalPoint, numVarsAfterDecimal, charBuf);
    //
    //
    //        //int sensorValue = analogRead(A0);
    //      //String stringThree = "I want " + sensorValue;
    //    //  String temp="2A:" + PosErr_B2A + "|" + Count_B4B;
    //    //
    //    //dtostrf(PosErr_B2A, 4, 1, dtostrfbuffer);
    //    //sendBuffer
    //    //  sprintf(sendBuffer, "X%dY%dT", first, second);
    //      //  display.print("2A:");
    //      //  dtostrf(PosErr_B2A, 4, 1, dtostrfbuffer);
    //
    //      //Goal is "2A:[PosErr]|[PosCmd]|[ActPos]
    //      display.setTextColor(WHITE, BLACK);
    //    display.print("2A:");
    //    dtostrf(PosErr_B2A, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B2A, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B2A, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //     display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("4A:");
    //    dtostrf(PosErr_B4A, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B4A, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B4A, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //    display.setTextColor(WHITE, BLACK);
    //    display.print("2B:");
    //    dtostrf(PosErr_B2B, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B2B, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B2B, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //     display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("4B:");
    //    dtostrf(PosErr_B4B, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(B4B, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_B4B, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    //    display.setTextColor(WHITE, BLACK);
    //    display.print("SS:");
    //    dtostrf(PosErr_SSARJ, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(SSARJ, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_SSARJ, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //
    ////
    //    display.setTextColor(BLACK, WHITE); // 'inverted' text
    //    display.print("PS:");
    //    dtostrf(PosErr_PSARJ, 5, 1, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(PSARJ, 5, 1, dtostrfbuffer); //Cmd Pos
    //    display.print( dtostrfbuffer);
    //    display.print("|");
    //    dtostrf(Pos_PSARJ, 5, 1, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    ////
    //// PID vals
    //    display.print("Kpid:");
    //    dtostrf(Kp_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",");
    //    dtostrf(Ki_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",");
    //   dtostrf(Kd_PSARJ, 3, 0, dtostrfbuffer);
    //    display.print( dtostrfbuffer);
    //    display.print(",Mtr:");
    //    dtostrf(CmdSpeed_PSARJ, 3, 0, dtostrfbuffer);
    //    display.println( dtostrfbuffer);
    //// end PID vals
    //    //float Kp_PSARJ = 10; // Proportional Gain of PID
    ////float Ki_PSARJ = 2; // Integral Gain of PID
    ////float Kd_PSARJ = 2; // Derivative Gain of PID
    //
    //
    ////    display.print(",PSMtrSpdU8bot:");
    ////    dtostrf(CmdSpeed_PSARJ, 5, 1, dtostrfbuffer);
    ////    display.println( dtostrfbuffer);
    //
    //
    //
    ////    display.setTextColor(WHITE, BLACK);
    ////    display.print("STJ:");
    ////    dtostrf(STRRJ, 6, 1, dtostrfbuffer);
    ////    display.print( dtostrfbuffer);
    ////
    ////
    ////    display.setTextColor(BLACK, WHITE); // 'inverted' text
    ////    display.print("|PTJ:");
    ////    dtostrf(PTRRJ, 6, 1, dtostrfbuffer);
    ////    display.println( dtostrfbuffer);
    //    //
    //    //
    //    ////
    //    ////   // display.print(",");
    //    ////
    //    ////     display.println("4. Hello, world!");
    //    ////      display.println("5. Hello, world!");
    //    ////       display.println("6. Hello, world!");
    //    ////        display.println("7. Hello, world!");
    //    ////              display.println("8. Hello, world!");
    //    ////       display.println("9. Hello, world!");
    //    ////        display.println("10. Hello, world!");
    //    //
    //    //
    //      display.display();
    //      //delay(10);
    //      display.clearDisplay();
    //    //
    //    //  // LCD =======================================
  }
  //
  //
  //
  //




  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;

  delay(3);
}
