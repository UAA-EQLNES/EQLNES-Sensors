/*
  Bridge Sensor with GSM, SDCard, and RTC

  Sketch used by UA Sensors platform.

  Notes:
  - Sketch handles specific case with current test sensor
    where SD Card does not write
  - Need to test if this version works on test sensor

  Created 14 6 2014
  Modified 1 7 2014
*/

#include <LowPower.h>
#include <math.h>

#include <UASensors_Sim900.h>
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
#define MOSFET_US_PIN    5
#define MOSFET_GSM_PIN   6
#define THERM_PIN        7
#define RTC_CS_PIN       8
#define GSM_PWRKEY       9
#define SD_CS_PIN        10


// Settings
// -------------------------------
#define SEND_DATA_AFTER_X_READINGS 4
#define SLEEP_CYCLES               4
#define NUM_THERM_READINGS         5
#define THERM_READING_DELAY        20
#define NUM_DISTANCE_READINGS      3
#define DISTANCE_READING_DELAY     200
#define DATA_DELIM                 ';'
#define BACKUP_FILENAME            "backup.txt"
#define UNSENT_FILENAME            "unsent.txt"
#define ERROR_FILENAME             "error.txt"
#define PHONE_NUMBER               "+12223334444"
#define ERROR_GSM                  "GSM Failed"
#define ERROR_SMS                  "SMS Failed"


// Custom Datatypes
typedef struct {
  int distance;
  int temperature;
  time_t timestamp;
} SensorReading;


// Global Variables
int numCachedReadings = 0;
SensorReading sensorReadings[SEND_DATA_AFTER_X_READINGS];
UASensors_Sim900 sim900;
UASensors_RTC rtc(RTC_CS_PIN);
UASensors_SDCard sd(SD_CS_PIN);


void setup()
{
  pinMode(SD_CS_PIN, OUTPUT);
  pinMode(THERM_PIN, OUTPUT);
  sim900.begin(&Serial);
}


void loop()
{

  // 1. Wake up.
  // -----------

  // Enter idle state for 8 s with the rest of peripherals turned off.
  // 98 sleep cycles will take a reading approximately every 13 minutes.
  for (int i = 0; i < SLEEP_CYCLES; ++i)
  {
    LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }


  // HACK: Turn on GSM MOSFET on wake up each time. Somehow
  //       fixes bug where RocketScream resets.
  digitalWrite(MOSFET_GSM_PIN, HIGH);
  delay(1000);


  // 2. Turn on thermistor.
  // ----------------------
  digitalWrite(THERM_PIN, HIGH);

  // 3. Take 5 thermistor readings. (one every 20ms)
  // -----------------------------------------------
  int thermReadings[NUM_THERM_READINGS];
  for (int i = 0; i < NUM_THERM_READINGS; ++i)
  {
    thermReadings[i] = analogRead(THERMISTOR_PIN);
    delay(THERM_READING_DELAY);
  }

  // 4. Turn off thermistor.
  // -----------------------
  digitalWrite(THERM_PIN, LOW);
  delay(500);

  // 5. Average 5 thermistor readings.
  // ---------------------------------
  double sumTherm = 0;
  for (int i = 0; i < NUM_THERM_READINGS; ++i)
  {
    sumTherm += thermReadings[i];
  }
  double avgTherm = sumTherm / NUM_THERM_READINGS;
  avgTherm = 1023 / avgTherm - 1;
  double R = 10000 / avgTherm;


  // 6. Convert average thermistor reading into temperature.
  // -------------------------------------------------------

  // Steinhart-Hart, modified:
  double avgTemperature = ( 3950.0 / (log( R / (10000.0 * exp( -3950.0 / 298.13 ) ) ) ) ) - 273.13;


  // 7. Turn on ultrasonic sensor (MOSFET).
  // --------------------------------------
  digitalWrite(MOSFET_US_PIN, HIGH);
  // Calibration time
  delay(3000);


  // 8. Take 3 distance readings. (One every 200ms)
  // ----------------------------------------------
  int distanceReadings[NUM_DISTANCE_READINGS];
  for (int i = 0; i < NUM_DISTANCE_READINGS; ++i)
  {
    distanceReadings[i] = analogRead(ULTRASONIC_PIN);
    delay(DISTANCE_READING_DELAY);
  }


  // 9. Turn off ultrasonic sensor (MOSFET).
  // ---------------------------------------
  digitalWrite(MOSFET_US_PIN, LOW);
  delay(500);


  // 10. Average 3 distance measurements.
  // ------------------------------------
  double sumDistance = 0.0;
  for (int i = 0; i < NUM_DISTANCE_READINGS; ++i)
  {
    sumDistance += distanceReadings[i];
  }
  double avgDistance = sumDistance / NUM_DISTANCE_READINGS;


  // 11. Use average temperature to calculate actual distance.
  // ---------------------------------------------------------
  double adjustedDistance = ( ( 331.1 + .6 * avgTemperature ) / 344.5 ) * avgDistance;

  int roundedDistance = round(adjustedDistance);
  int roundedTemperature = round(avgTemperature);


  // 12. Get time from RTC Shield.
  // -----------------------------
  rtc.begin();
  time_t unixTime = rtc.readDateTime();


  // 13. Combine time, distance, and temperature into a single string.
  // -----------------------------------------------------------------
  String dataString = String(unixTime) + " " + String(roundedDistance) + " " + String(roundedTemperature);

  // Cache distance and time in global array variable
  sensorReadings[numCachedReadings].distance = roundedDistance;
  sensorReadings[numCachedReadings].temperature = roundedTemperature;
  sensorReadings[numCachedReadings].timestamp = unixTime;
  numCachedReadings += 1;


  // 14. Turn on SD Card.
  // 15. Save data string to text file on SD card: "1399506809 1000 100" (roughly 20 characters)
  // -------------------------------------------------------------------------------------------

  // Try to turn on SD card. Should only need to be called once.
  sd.begin();
  sd.writeFile(BACKUP_FILENAME, dataString);
  delay(1000);


  // 16. Are there 4 unsent data strings?
  // 17. Yes. Send 4 unsent data strings in one SMS. Go to 18.
  // -------------------------------------
  if (numCachedReadings == SEND_DATA_AFTER_X_READINGS)
  {

    // 18. Prepare text message
    // ---------------------
    String textMessage = String(sensorReadings[0].timestamp) + " " + String(sensorReadings[0].distance) + " " + String(sensorReadings[0].temperature);
    time_t startTime = sensorReadings[0].timestamp;
    int minutesElapsed = 0;

    // Format data to send as text message
    for (int i = 1; i < numCachedReadings; ++i)
    {
      minutesElapsed = (sensorReadings[i].timestamp - startTime) / 60;
      textMessage += String(DATA_DELIM) + String(minutesElapsed) + " " + String(sensorReadings[i].distance) + " " + String(sensorReadings[i].temperature);
    }


    // GSM baud rate. Start communication link with GSM shield.
    Serial.begin(19200);
    delay(100);


    // 20. Send text message if GSM Ready
    if (sim900.ensureReady() == true)
    {
      sim900.sendTextMsg(textMessage, PHONE_NUMBER);
      if (sim900.isTextMsgDelivered() == false)
      {
        sd.begin();
        sd.writeFile(ERROR_FILENAME, String(unixTime) + ": " + ERROR_SMS);
        sd.writeFile(UNSENT_FILENAME, textMessage);
      }
    }
    else
    {
      sd.begin();
      sd.writeFile(ERROR_FILENAME, String(unixTime) + ": " + ERROR_GSM);
      sd.writeFile(UNSENT_FILENAME, textMessage);
    }

    // Reset number of cached readings
    numCachedReadings = 0;


    // 20. Turn off GSM.
    // -----------------

    // Turn off GSM power pin.
    if (sim900.ensureOffline() == false)
    {
      // TODO(richard-to): What would be best way to handle this issue?
      //                   Battery will die quickly if power cannot be turned off.
      //                   Send SOS SMS?
    }
  }

  // Turn off GSM MOSFET.
  digitalWrite(MOSFET_GSM_PIN, LOW);
  delay(1000);
}