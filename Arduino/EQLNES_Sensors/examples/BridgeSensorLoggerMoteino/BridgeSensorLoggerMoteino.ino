/*
  Logger for Bridge Sensor using Moteino (RFM69)

  Created 14 6 2014
  Modified 14 6 2014
*/

#include <RFM69.h>
#include <SPI.h>
#include <Time.h>


// Settings
#define SERIAL_BAUD 115200
#define SENDER_DELIM ":"


// Moteino Settings
#define NODEID      1
#define NETWORKID   100
#define GATEWAYID   1
#define FREQUENCY   RF69_433MHZ
#define KEY         "80272XG72IuaIV7w"


RFM69 radio;

char message[MAX_DATA_LEN];

void setup()
{
  Serial.begin(SERIAL_BAUD);
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
  radio.setHighPower();
  radio.encrypt(KEY);
}

void loop()
{
  if (radio.receiveDone())
  {
    for (int i = 0; i < radio.DATALEN; ++i)
    {
      message[i] = (char)radio.DATA[i];
    }

    Serial.print(radio.SENDERID, DEC);
    Serial.print(SENDER_DELIM);
    Serial.println(message);

    if (radio.ACK_REQUESTED)
    {
      byte theNodeID = radio.SENDERID;
      radio.sendACK();
    }
  }
}