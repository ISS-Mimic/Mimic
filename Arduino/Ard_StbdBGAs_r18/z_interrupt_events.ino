void checkSerial() 
{
  String receivedData = Serial.readStringUntil('\n');

  char buffer[receivedData.length() + 1];
  strcpy(buffer, receivedData.c_str());

  char *token;
  char *remainder;
  token = strtok_r(buffer, " ", &remainder);

  while (token != NULL) 
  {
    String dataString(token);
    int delimiterIndex = dataString.indexOf('=');

    if (delimiterIndex != -1) 
    {
      String key = dataString.substring(0, delimiterIndex);
      String value = dataString.substring(delimiterIndex + 1);

      if (key == "PSARJ") 
      {
        PSARJ = value.toFloat();
      } 
      else if (key == "SmartRolloverBGA") 
      {
        SmartRolloverBGA = int(value.toFloat());
      } 
      else if (key == "SmartRolloverSARJ") 
      {
        SmartRolloverSARJ = int(value.toFloat());
      } 
      else if (key == "NULLIFY") 
      {
        NULLIFY = int(value.toFloat());
      } 
      else if (key == "SSARJ") 
      {
        SSARJ = value.toFloat();
      } 
      else if (key == "PTRRJ") 
      {
        PTRRJ = value.toFloat();
      } 
      else if (key == "STRRJ") 
      {
        STRRJ = value.toFloat();
      } 
      else if (key == "B1B") 
      {
        B1B = value.toFloat();
      } 
      else if (key == "B1A") 
      {
        B1A = value.toFloat();
      } 
      else if (key == "B2B") 
      {
        B2B = value.toFloat();
      } 
      else if (key == "B2A") 
      {
        B2A = value.toFloat();
      } 
      else if (key == "B3B") 
      {
        B3B = value.toFloat();
      } 
      else if (key == "B3A") 
      {
        B3A = value.toFloat();
      } 
      else if (key == "B4B") 
      {
        B4B = value.toFloat();
      } 
      else if (key == "B4A") 
      {
        B4A = value.toFloat();
      } 
      else if (key == "AOS") 
      {
        AOS = value.toFloat();
        if (AOS == 1.00)
        {
          //digitalWrite(ledGreenPin, HIGH);
        }
        else
        {
          //digitalWrite(ledRedPin, HIGH);
        }
      }
    }
    token = strtok_r(NULL, " ", &remainder);
  }
}
