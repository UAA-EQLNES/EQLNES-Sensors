*Note: Documentation is a work in progress.*

## How to install the Arduino libraries for the bridge sensor

- Option 1: Drag the four folders into the Arduino user libraries folder
- Option 2: Import the four folders using the Arduino IDE's import library feature

## List of example sketches

The following are descriptions of the example sketches and their purpose:

#### UA_Sensors

- **BasicUltrasonic** - Used to verify readings from Ultrasonic senor
- **BridgeSensorGSM** - Full sketch that utilizes all features of the sensor platform
- **BridgeSensorLoggerMoteino** - Listens for sensor readings sent from a Moteino and passes to another program via serial
- **BridgeSensorMoteino** - Modified version of BridgeSensorGSM that uses Moteinos instead.
- **LowPowerGSMTest** - Verifies that the GSM shield sends on the sensor platform
- **LowPowerSDTest** - Verifies that the SD breakoutboard records data on the sensor platform
- **LowPowerThermistorTest** - Verifies that the Thermistor works on the sensor platform
- **LowPowerUltrasonicTest** - Verifies that the Ultrasonic sensor works on the sensor platform
- **Sim900CmdConsole** - A simple serial console to send AT commands to GSM shield
- **Sim900Mediator** - Sketch that forwards data to and from GSM shield and Raspberry Pi/Laptop

#### UA\_Sensors\_RTC

- **RTCTester** - Read/Set time on RTC board

#### UA\_Sensors\_SDCard

- **SDCardTester** - Read/Write text to SD Card

#### UA\_Sensors\_Sim900

- **Sim900Tester** - Verifies that the power functions and SMS messaging works