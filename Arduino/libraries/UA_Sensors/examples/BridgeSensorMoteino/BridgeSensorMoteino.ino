/*
  Bridge Sensor with Moteino (RFM69), SDCard, and RTC

  Simplified bridge sensor sketch testing the use of Moteino
  instead of RocketScream Arduino and LinkSprite Sim900 GSM
  Shield combo.

  Created 14 6 2014
  Modified 14 6 2014
*/

#include <LowPower.h>
#include <math.h>
#include <RFM69.h>

#include <UASensors_SDCard.h>
#include <UASensors_RTC.h>

// UASensors SDCard Dependency
#include <SdFat.h>
#include <String.h>

// UASensors RTC Dependency
#include <SPI.h>
#include <Time.h>


// Analog Pins
#define THERMISTOR_PIN 5
#define ULTRASONIC_PIN 6


// Digital Pins
#define MOSFET_RTC_PIN   3
#define MOSFET_SD_PIN    4
#define MOSFET_US_PIN    5
#define MOSFET_GSM_PIN   6
#define MOSFET_THERM_PIN 7
#define RTC_CS_PIN       8
#define GSM_PWRKEY       9
#define SD_CS_PIN        7


// Moteino Settings
#define NODEID      99
#define NETWORKID   100
#define GATEWAYID   1
#define FREQUENCY   RF69_433MHZ
#define KEY         "80272XG72IuaIV7w"


// Settings
// -------------------------------
#define SEND_DATA_AFTER_X_READINGS  4
#define SLEEP_CYCLES                2
#define NUM_THERM_READINGS          5
#define THERM_READING_DELAY         20
#define NUM_DISTANCE_READINGS       3
#define DISTANCE_READING_DELAY      200
#define DATA_DELIM                  ';'
#define BACKUP_FILENAME             "backup.txt"
#define UNSENT_FILENAME             "unsent.txt"


// Custom Datatypes
typedef struct {
  int distance;
  int temperature;
  time_t timestamp;
} SensorReading;



// Global Variables
int numCachedReadings = 0;
SensorReading sensorReadings[SEND_DATA_AFTER_X_READINGS];
RFM69 radio;
UASensors_RTC rtc(RTC_CS_PIN);
UASensors_SDCard sd(SD_CS_PIN);


void setup() {}


void loop()
{
  radio.sleep();

  for (int i = 0; i < SLEEP_CYCLES; ++i)
  {
    LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }

  int roundedDistance = random(140, 181);
  int roundedTemperature = random(10, 31);

  rtc.begin();
  time_t unixTime = rtc.readDateTime();

  String dataString = String(unixTime) + " " + String(roundedDistance) + " " + String(roundedTemperature);

  sd.begin();
  sd.writeFile(BACKUP_FILENAME, dataString);

  sensorReadings[numCachedReadings].distance = roundedDistance;
  sensorReadings[numCachedReadings].temperature = roundedTemperature;
  sensorReadings[numCachedReadings].timestamp = unixTime;
  numCachedReadings += 1;

  if (numCachedReadings == SEND_DATA_AFTER_X_READINGS)
  {
    String textMessage = String(sensorReadings[0].timestamp) + " " + String(sensorReadings[0].distance) + " " + String(sensorReadings[0].temperature);
    time_t startTime = sensorReadings[0].timestamp;
    int minutesElapsed = 0;

    for (int i = 1; i < numCachedReadings; ++i)
    {
      minutesElapsed = (sensorReadings[i].timestamp - startTime) / 60;
      textMessage += String(DATA_DELIM) + String(minutesElapsed) + " " + String(sensorReadings[i].distance) + " " + String(sensorReadings[i].temperature);
    }

    if (mote_sendTextMsg(textMessage) == false)
    {
      sd.begin();
      sd.writeFile(UNSENT_FILENAME, textMessage);
      delay(500);
    }
    numCachedReadings = 0;
  }
}


// Sends message to receiving moteino
boolean mote_sendTextMsg(String message)
{
  if (message.length() >= MAX_DATA_LEN)
  {
    return false;
  }

  char payload[MAX_DATA_LEN];
  message.toCharArray(payload, MAX_DATA_LEN);

  radio.initialize(FREQUENCY,NODEID,NETWORKID);
  radio.encrypt(KEY);
  radio.setHighPower();

  if (radio.sendWithRetry(GATEWAYID, (const void*)(&payload), sizeof(payload)))
  {
    return true;
  }
  else
  {
    return false;
  }
}