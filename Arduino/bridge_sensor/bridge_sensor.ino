#include <LowPower.h>
#include <math.h>
#include <SdFat.h>
#include <SPI.h>
#include <String.h>
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
#define SD_CS_PIN        10


// Settings
// ----------------------------------
#define SEND_DATA_AFTER_X_READINGS 4
#define SLEEP_CYCLES 4
#define NUM_THERM_READINGS 5
#define THERM_READING_DELAY 20
#define NUM_DISTANCE_READINGS  3
#define DISTANCE_READING_DELAY 200
#define DATA_DELIM ';'
#define BACKUP_FILENAME "backup.txt"
#define UNSENT_FILENAME "unsent.txt"
#define ERROR_FILENAME "error.txt"
#define PHONE_NUMBER   "+16505033896"
#define GSM_TIMEOUT 250
#define SMS_TIMEOUT 100
#define ERROR_GSM "GSM Failed"
#define ERROR_SMS "SMS Failed"


// Custom Datatypes
// -------------------------------------
typedef struct {
  int distance;
  int temperature;
  time_t timestamp;
} SensorReading;


// Global Variables
// -------------------------------------
int numCachedReadings = 0;
SensorReading sensorReadings[SEND_DATA_AFTER_X_READINGS];
SdFat sd;
SdFile fh;

void setup() 
{
  pinMode(SD_CS_PIN, OUTPUT);
  pinMode(MOSFET_THERM_PIN, OUTPUT);
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

    
  // 2. Turn on thermistor.
  // ----------------------
  digitalWrite(MOSFET_THERM_PIN, HIGH);

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
  digitalWrite(MOSFET_THERM_PIN, LOW);
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
  digitalWrite(MOSFET_RTC_PIN, HIGH);
  delay(500);
  rtc_init();  
  time_t unixTime = rtc_readTimeDate();
  digitalWrite(MOSFET_RTC_PIN, LOW);
  delay(500);  
  
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
  
  //Turn on SD MOSFET.
  digitalWrite(MOSFET_SD_PIN, HIGH); 

  // Try to turn on SD card. Should only need to be called once.
  sd.begin(SD_CS_PIN, SPI_FULL_SPEED);  
  sd_writeToFile(BACKUP_FILENAME, dataString);
  delay(1000);
  
  // Turn off SD MOSFET.
  digitalWrite(MOSFET_SD_PIN, LOW); 
  delay(500);
  
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
  
  
    // 19. Turn on GSM Shied.
    // ---------------------

    //Turn on GSM MOSFET.
    digitalWrite(MOSFET_GSM_PIN, HIGH); 
    delay(1000);

    // GSM baud rate. Start communication link with GSM shield.  
    Serial.begin(19200);
    delay(100);
  
    // Turn on GSM power pin.
    digitalWrite(GSM_PWRKEY, HIGH); 
    delay(1000);

    // Turn off GSM power pin.
    digitalWrite(GSM_PWRKEY, LOW); 
    delay(1000);
    
    
    // 20. Send text message if GSM Ready
    if (gsm_ready(GSM_TIMEOUT) == true)
    {
      gsm_sendTextMessage(textMessage);
      if (gsm_smsSent(SMS_TIMEOUT) == false)
      {
        // Log SMS failure        
        digitalWrite(MOSFET_SD_PIN, HIGH); 
        delay(1000);
        sd.begin(SD_CS_PIN, SPI_FULL_SPEED);        
        sd_writeToFile(ERROR_FILENAME, String(unixTime) + ": " + ERROR_SMS); 
        sd_writeToFile(UNSENT_FILENAME, textMessage);  
        digitalWrite(MOSFET_SD_PIN, LOW); 
        delay(1000);        
      }        
    } 
    else 
    {
      // Log GSM failure
      digitalWrite(MOSFET_SD_PIN, HIGH); 
      delay(1000);
      sd.begin(SD_CS_PIN, SPI_FULL_SPEED);      
      sd_writeToFile(ERROR_FILENAME, String(unixTime) + ": " + ERROR_GSM);
      sd_writeToFile(UNSENT_FILENAME, textMessage);
      digitalWrite(MOSFET_SD_PIN, LOW); 
      delay(1000);
    }


    // Reset number of cached readings
    numCachedReadings = 0;    
    
    
    // 20. Turn off GSM.  
    // -----------------
 
    // Turn on GSM power pin.
    digitalWrite(GSM_PWRKEY, HIGH); 
    delay(1000);

    // Turn off GSM power pin.
    digitalWrite(GSM_PWRKEY, LOW); 
    delay(1000);
  
    // Turn off GSM MOSFET.   
    digitalWrite(MOSFET_GSM_PIN, LOW);
    delay(1000);
  }   
}


void gsm_sendTextMessage(String message)
{  
  // Because we want to send the SMS in text mode     
  Serial.print("AT+CMGF=1\r");
  delay(500);
  
  // Send sms message, be careful need to add a country code before the cellphone number  
  Serial.println("AT + CMGS = \"" + String(PHONE_NUMBER) + "\"");
  delay(500);
  
  // The content of the message  
  Serial.println(message);  
  delay(500);
  
  // The ASCII code of the ctrl+z is 26  
  Serial.println((char)26);
  delay(500);
}
 
 
// Clears the GSM buffer to make sure we don't unexpected characters
void gsm_clearBuffer() 
{
   char c;
   while (Serial.available() > 0) 
   {
     c = Serial.read();
   }
}

// Polls GSM buffer for "Call Ready" signal.
boolean gsm_ready(int timeout)
{
  char gsmReady[] = "Call Ready";
  char gsmReadyLength = 10;
  int matched = 0;
  char c;  
  while (timeout > 0) 
  {
    while (Serial.available()) 
    {
        c = Serial.read();
        if (c == gsmReady[matched]) 
        {
          matched += 1;
          if (matched == gsmReadyLength) 
          {
            return true;
          }
        } else {
          matched = 0;
        }
      }
      timeout -= 1;
      delay(100);     
    }
    return false;  
}


// Polls GSM buffer for two "OK" messages or one "ERROR" to
// check if SMS was sent successfully.
boolean gsm_smsSent(int timeout)
{
  char smsOK[] = "OK";
  int smsOKLength = 2;
  int numOKNeeded = 2;
  
  char smsError[] = "ERROR";
  int smsErrorLength = 5;
  
  char c;
  
  int matchedError = 0;  
  int matchedOK = 0;
  int foundOK = 0;

  while (timeout > 0) 
  {
    while (Serial.available()) 
    {
        c = Serial.read();
        if (c == smsError[matchedError]) 
        {
          matchedError += 1;
          matchedOK = 0;
          if (matchedError == smsErrorLength)
          {
            return false;
          }
        } 
        else if (c == smsOK[matchedOK]) 
        {
          matchedOK += 1;
          matchedError = 0;
          if (matchedOK == smsOKLength) 
          {
            foundOK += 1;
          }
         
          if (foundOK == smsOKLength)
          {
            return true;
          }
        } else {
          matchedOK = 0;
          matchedError = 0;
        }
      }
      timeout -= 1;
      delay(100);     
    }
    return false;  
}


// Saves data to specified file on SD Card
//
// Returns true if file written successfully, otherwise returns false.
//
boolean sd_writeToFile(char *filename, String data)
{  
  if (fh.open(filename, O_RDWR | O_CREAT | O_AT_END))
  {
    fh.println(data);
    fh.close();
    return true;
  }
  else
  {
    return false;
  }
}

// Reads file from sd card
// TODO(richard-to): Need to test this implementation.
//                   Not currently used in sketch.
String sd_readFile(char *filename)
{
  char c;
  String buffer = "";
  if (fh.open(filename, O_READ)) 
  {   
    while (fh.available()) 
    {
      c = fh.read();
      buffer += c;
    }
    fh.close();
  } 
  return buffer;
}


// Initializes RTC Clock
int rtc_init() 
{ 
  pinMode(RTC_CS_PIN, OUTPUT);

  SPI.begin();
  SPI.setBitOrder(MSBFIRST); 
  SPI.setDataMode(SPI_MODE3);
 
  digitalWrite(RTC_CS_PIN, LOW);  
  SPI.transfer(0x8E);
  SPI.transfer(0x60);
  digitalWrite(RTC_CS_PIN, HIGH);
  delay(10);
}

// Sets time on RTC CLOCK
//
// Notes: 
// * Year is calculated as `current year - 1970`. So 2014 would be 44 and not 14.
// * Time is in UTC
// * day(1-31), month(1-12), year(0-99), hour(0-23), minute(0-59), second(0-59)
//
int rtc_setTimeDate(int d, int mo, int y, int h, int mi, int s) 
{
  int timedate[7] = {s, mi, h, 0, d, mo, y};
  for (int i = 0; i <= 6; ++i) 
  {
    if (i == 3) 
    {
      i++;
    }
    
    int b = timedate[i] / 10;
    int a = timedate[i] - b * 10;
    
    if (i == 2) 
    {
      if (b == 2) 
      {
        b = B00000010;
      } 
      else if (b == 1) 
      {
        b = B00000001;
      }
    }
      	
    timedate[i] = a + (b << 4);
		  
    digitalWrite(RTC_CS_PIN, LOW);
    SPI.transfer(i+0x80); 
    SPI.transfer(timedate[i]);        
    digitalWrite(RTC_CS_PIN, HIGH);
  }
}

// Gets unix timestamp from RTC clock
time_t rtc_readTimeDate() 
{
  int timedate[7];		
  for (int i = 0; i <= 6; ++i) 
  {
    if (i == 3) 
    {
      i++;
    }

    digitalWrite(RTC_CS_PIN, LOW);
    SPI.transfer(i + 0x00); 
    unsigned int n = SPI.transfer(0x00);  
    digitalWrite(RTC_CS_PIN, HIGH);
    int a = n & B00001111;
    
    if (i == 2) 
    {	
      int b = (n & B00110000) >> 4;
      if (b == B00000010) 
      {
        b = 20;
      } else if (b == B00000001) 
      {
        b = 10;
      }
      timedate[i] = a + b;
    } 
    else if (i == 4) 
    {
      int  b = (n & B00110000) >> 4;
      timedate[i] = a + b * 10;
    } 
    else if (i == 5) 
    {
      int b = (n & B00010000) >> 4;
      timedate[i] = a + b * 10;
    }
    else if (i == 6) 
    {
      int b = (n & B11110000) >> 4;
      timedate[i] = a + b * 10;
    } 
    else 
    {	
      int b = (n & B01110000) >> 4;
      timedate[i] = a + b * 10;
    }
  }
  
  TimeElements tm;
  tm.Year = timedate[6];
  tm.Month = timedate[5];
  tm.Day = timedate[4];
  tm.Hour = timedate[2];
  tm.Minute = timedate[1];
  tm.Second = timedate[0];
  
  return makeTime(tm);
}


