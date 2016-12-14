const int ledPin = 13;
String test = "";

void setup()
{
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  Serial1.begin(115200);
  Serial1.setTimeout(50);
}

void loop()
{
  digitalWrite(ledPin, LOW);
  if(Serial1.available())
  {
    checkSerial();
  }
}
void checkSerial()
{
  digitalWrite(ledPin, HIGH);
  test = "";
  while(Serial1.available())  
  {
     test = Serial1.readString();
  }
  Serial.println(test);
  Serial.println();
}
