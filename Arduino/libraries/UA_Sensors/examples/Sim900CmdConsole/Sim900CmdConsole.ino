/*
  Send AT Commands to Sim900 via Serial

  Sketch can be used to configure Sim900 shield

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

// GSM Shield uses software serial on pins 7, 8. Need to
// switch jumpers and do some soldering to enable software serial.
//
// NOTE: Software serial does not seem to work with this shield using
// 8 Mhz Arduinos
//
SoftwareSerial Sim900(7, 8);

const int MAX_BUFFER_SIZE = 100;

void setup()
{
  Serial.begin(9600);
  Sim900.begin(4800);

  Serial.println("Sim900 Command Console");
  Serial.println("----------------------");
}


void loop()
{
  char buffer[MAX_BUFFER_SIZE];
  int inputLength = 0;

  Serial.println("Enter AT command: ");

  while (!Serial.available())
  {
    delay(100);
  }

  inputLength = Serial.readBytesUntil('\n', buffer, MAX_BUFFER_SIZE - 1);
  buffer[inputLength] = '\0';

  Sim900.println(buffer);
  delay(100);
}