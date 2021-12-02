void loop() {



  sarj_port.PosCmd = PSARJ; // From RasPi telemetry stream
  sarj_stbd.PosCmd = SSARJ; // From RasPi telemetry stream


  if (NULLIFY == 1) {
    motorNULL(sarj_port); myEncPSARJ.write(0); PSARJ = 0;
    motorNULL(sarj_stbd); myEncSSARJ.write(0); SSARJ = 0;
    NULLIFY = 0;
  }

  // Can likely simplify this, but need to incorporate Adafruit motor shield library commands into my motor function/struct

  motorfnc(sarj_port); // this is where it's called
  if (sarj_port.tmpSpeed > 0) {
    myMotorPSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorPSARJ->run(BACKWARD);
  }
  myMotorPSARJ->setSpeed(sarj_port.CmdSpeed);// + 20);

  motorfnc(sarj_stbd); // this is where it's called
  if (sarj_stbd.tmpSpeed > 0) {
    myMotorSSARJ->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorSSARJ->run(BACKWARD);
  }
  myMotorSSARJ->setSpeed(sarj_stbd.CmdSpeed);// + 20);


  D0 = digitalRead(0);
  D1 = digitalRead(1);
  D2 = digitalRead(2);
  D3 = digitalRead(3);
  D4 = digitalRead(4);
  D5 = digitalRead(5);
  D6 = digitalRead(6);
  D7 = digitalRead(7);
  D8 = digitalRead(8);
  D9 = digitalRead(9);
  D10 = digitalRead(10);
  D11 = digitalRead(11);
  D12 = digitalRead(12);
  D13 = digitalRead(13);
  D14 = digitalRead(14);
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
  // For TRRJ's, it's most important to get cleanly to zero and be able to achieve 90 deg for storage. Have to make some minor code modifications since the physical tooth locations on the servos/horns may not line up with zero.

  // Saturating at 90 deg rather than scaling input, since TRRJ rarely moves past 90 deg anyway.
  PTRRJ = max(PTRRJ, -120); // saturate at -90 deg, but servo needs to be pushed a bit higher than that.
  PTRRJ = min(PTRRJ, 120); // saturate at 90 deg
  //servo_PTRRJ.write(-1*PTRRJ);
  servo_PTRRJ.write(map(-1 * (PTRRJ - 15), -90, 90, -10, 190)); // 90 deg cmd is a little short, so bumping to 95 deg


  STRRJ = max(STRRJ, -120); // saturate at -90 deg
  STRRJ = min(STRRJ, 120); // saturate at 90 deg
  //servo_STRRJ.write(-1*STRRJ);
  servo_STRRJ.write(map(-1 * (STRRJ - 12), -90, 90, -15, 195)); // 90 deg cmd is a little short, so bumping to 95 deg
  //servo_STRRJ.write(map(-1*(STRRJ), -90, 90, 0, 180)); // 90 deg cmd is a little short, so bumping to 95 deg

  delay(1);
  // ========= END Servo Stuff============================

  // ============== Time measures ===================================================
  LoopStartMillis = millis();
  delta_t_millis = max(LoopStartMillis - previousMillis, 1); // ensure always equal to at least one, for later inversion
  inverse_delta_t_millis = 1 / ((float) delta_t_millis); // BCM mod 10/28/2018: for some reason, was not inverted (just = value, rather than 1/value).
  millisChPt1 = millis() - LoopStartMillis;
  // ================================================================================


  sarj_port.Count = myEncPSARJ.read();
  sarj_stbd.Count = myEncSSARJ.read();

  //
  millisChPt2 = millis() - LoopStartMillis;


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
    Serial.print(sarj_port.Count);
    Serial.print(",Count_SSARJ: ");
    Serial.print(sarj_stbd.PosErr);

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
    Serial.print(",D5: ");
    Serial.print(D5);
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

    Serial.print(",D14: ");
    Serial.print(D14);
    Serial.print(",D15: ");
    Serial.print(D15);
    Serial.print(",D16: ");
    Serial.print(D16);
    Serial.print(",D17: ");
    Serial.print(D17);

    Serial.print("| PosErrs Prt;Stbd: ");

    Serial.print(sarj_port.PosErr);
    Serial.print(", ");
    Serial.print(sarj_stbd.PosErr);
    //    Serial.print(", ");
    Serial.print("| CmdSpd Prt;Stbd: ");
    Serial.print(sarj_port.CmdSpeed);
    Serial.print(", ");
    Serial.print(sarj_stbd.CmdSpeed);

    Serial.println("|  ");

  }

  previousMillis = LoopStartMillis;

  millisChPt6 = millis() - LoopStartMillis;

  delay(3);
}
