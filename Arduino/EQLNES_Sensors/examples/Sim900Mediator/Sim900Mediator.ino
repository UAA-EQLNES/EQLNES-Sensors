/*
  Sim900 Mediator

  This sketch makes Arduino act as a bridge between Sim900
  shield and device connected via Serial.

  Example of devices include laptop or Raspberry Pi.

  Main usage is for forwarding incoming SMS messages
  for processing.

  Another usage is for sending AT commands to configure
  the shield.

  Notes:
  - Notice that the baud rate for the shield connection is 4800. This
    is a workaround for SMS messages greater than 64 characters. Another
    option is to increase the buffer size defined in the Software Serial
    library.
  - The GSM shield will need to be set to listen at this baud rate. The
    AT command to use is "AT+IPR=4800"

  Created 14 6 2014
  Modified 14 6 2014
*/

#include <SoftwareSerial.h>
SoftwareSerial Sim900(7, 8);

char c = 0;

void setup()
{
  Serial.begin(9600);
  Sim900.begin(4800);
}

void loop()
{
  if (Serial.available() > 0)
  {
    c = Serial.read();
    Sim900.print(c);
  }

  if (Sim900.available() > 0)
  {
    c = Sim900.read();
    Serial.print(c);
  }
}