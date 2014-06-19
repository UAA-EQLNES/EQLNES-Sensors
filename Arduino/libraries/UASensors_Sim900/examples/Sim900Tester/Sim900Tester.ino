/*
  Test Sim900 GSM Shield

  Test functionality needed for UA sensors platform, mainly,
  sending text messages and power toggle.

  Notes:
  - Currently we do not check if the GSM powered off successfully. Only power
    on is checked. This is possible but not implemented.

  Created 14 6 2014
  Modified 14 6 2014
*/
#include <SoftwareSerial.h>
#include <UASensors_Sim900.h>

// UA Sensors Sim900 - Dependencies
#include <String.h>

// A test message for testing SMS functionality.
#define TEST_MSG "This is a test message from Sim900 GSM shield."

// Recipient phone number
#define PHONE_NUMBER "+12223334444"

// Time to wait for GSM to power on.
const int GSM_TIMEOUT = 250;

// Time to wait for SMS to be sent
const int SMS_TIMEOUT = 100;


// Starting power state of GSM.
bool isOn = false;

// Instantiate Sim900 object. Need to call begin before using.
UASensors_Sim900 sim900;

// GSM Shield uses software serial on pins 7, 8. Need to
// switch jumpers and do some soldering to enable software serial.
//
// NOTE: Software serial does not seem to work with this shield using
// 8 Mhz Arduinos
//
SoftwareSerial Sim900Serial(7, 8);


// Menu options recognized from Serial input
const char SEND_TEXT_MSG = 's';
const char TOGGLE_POWER = 'p';


void setup()
{
  Serial.begin(9600);
  Sim900Serial.begin(9600);

  Serial.println("Sim900 Tester commands");
  Serial.println("-----------------------");
  Serial.println("s: Send text message");
  Serial.println("p: Toggle power on shield");

  sim900.begin(Sim900Serial);
}


void loop()
{
  // Listen for user input. Perform action
  // if valid command specified from Serial.
  if (Serial.available())
  {
    switch (Serial.read())
    {
      case TOGGLE_POWER:
        doTogglePower();
        break;
      case SEND_TEXT_MSG:
        doSendTextMsg();
        break;
    }
  }

  // Listen for input from GSM shield.
  if (sim900.available())
  {
    Serial.write(sim900.read());
  }
}


void doTogglePower()
{
  if (isOn)
  {
    Serial.println("Powering down GSM shield...");
    sim900.togglePower();
    isOn = false;
  }
  else
  {
    Serial.println("Powering up GSM shield...");
    sim900.togglePower();
    isOn = true;

    if (sim900.isReady(GSM_TIMEOUT) == true)
    {
      Serial.println("GSM shield powered on and ready.");
    }
    else
    {
      Serial.println("Error: Failed to power up GSM shield.");
    }
  }

}


void doSendTextMsg()
{
  Serial.println("Sending a test message via SMS...");
  sim900.sendTextMsg(TEST_MSG, PHONE_NUMBER);
  if (sim900.isTextMsgDelivered(SMS_TIMEOUT) == true)
  {
    Serial.println("SMS text message sent successfully!");
  }
  else
  {
    Serial.println("Error: Could not send text message!");
  }
}
