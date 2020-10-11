void loop() {


  bga_2B.PosCmd = B2B; // From RasPi telemetry stream
  bga_2A.PosCmd = B2A; // From RasPi telemetry stream
  bga_4B.PosCmd = B4B; // From RasPi telemetry stream
  bga_4A.PosCmd = B4A; // From RasPi telemetry stream

  if (NULLIFY == 1) {
    digitalWrite(13, LOW);
    delay(500);
    motorNULL(bga_2B);    myEnc2B.write(0); B2B=0;

    motorNULL(bga_2A);     myEnc2A.write(0);B2A=0;

    motorNULL(bga_4B);     myEnc4B.write(0); B4B=0;
    
    motorNULL(bga_4A);    myEnc4A.write(0); B4A=0;

    digitalWrite(13, HIGH);
    digitalWrite(6, LOW);
    delay(500);
    NULLIFY = 0;
    digitalWrite(6, HIGH);

  }

  // Can likely simplify this, but need to incorporate Adafruit motor shield library commands into my motor function/struct

  motorfnc(bga_2B); // this is where it's called
  if (bga_2B.tmpSpeed > 0) {
    myMotorB2B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB2B->run(BACKWARD);
  }
  myMotorB2B->setSpeed(bga_2B.CmdSpeed);// + 20);

  motorfnc(bga_4B); // this is where it's called
  if (bga_4B.tmpSpeed > 0) {
    myMotorB4B->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB4B->run(BACKWARD);
  }
  myMotorB4B->setSpeed(bga_4B.CmdSpeed);// + 20);


  motorfnc(bga_2A); // this is where it's called
  if (bga_2A.tmpSpeed > 0) {
    myMotorB2A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB2A->run(BACKWARD);
  }
  myMotorB2A->setSpeed(bga_2A.CmdSpeed);// + 20);


  motorfnc(bga_4A); // this is where it's called
  if (bga_4A.tmpSpeed > 0) {
    myMotorB4A->run(FORWARD); // This command is necessary for the AdaFruit boards, requiring conditionals (rather than signed speeds taking care of direction).
  }
  else {
    myMotorB4A->run(BACKWARD);
  }
  myMotorB4A->setSpeed(bga_4A.CmdSpeed);// + 20);



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

  bga_2B.Count = myEnc2B.read();
  bga_4B.Count = myEnc4B.read();
  bga_2A.Count = myEnc2A.read();
  bga_4A.Count = myEnc4A.read();

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

    Serial.print("Count_B2A: ");
    Serial.print(bga_2B.Count);
    Serial.print(",Count_B4A: ");
    Serial.print(bga_4A.Count);
    Serial.print("Count_B2B: ");
    Serial.print(bga_2B.Count);
    Serial.print(",Count_B4B: ");
    Serial.print(bga_4B.Count);
    Serial.print(",SmartRolloverBGA");
    Serial.print(SmartRolloverBGA);

    //    Serial.print(",Count_PSARJ: ");
    //    Serial.print(Count_PSARJ);
    //    Serial.print(",Count_SSARJ: ");
    //    Serial.print(Count_SSARJ);

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
    Serial.print(bga_2B.PosErr);
    Serial.print(", ");
    Serial.print(bga_4A.PosErr);
    Serial.print(", ");
    Serial.print(bga_2B.PosErr);
    Serial.print(", ");
    Serial.print(bga_4B.PosErr);
    //    Serial.print(", ");
    //    Serial.print(PosErr_PSARJ);
    //    Serial.print(", ");
    //    Serial.print(PosErr_SSARJ);
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
