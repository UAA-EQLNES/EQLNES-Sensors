#! /usr/bin/env python
import argparse
from core import SensorReadingsDataStore, DataParser
from datetime import datetime
from gpio import enableUart
import logging
from serial import Serial
from sim900 import Sim900, SMSReader
from sqlite3 import ProgrammingError
from time import sleep


LOG_FILE = 'log/ua_sensors.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(levelname)s - %(message)s'


def main():

    # Parse command line arguments
    #
    # The default settings will work well for the pcDuino. If you
    # are using a laptop or Raspberry Pi, then you will need to set
    # the serial baud rate to 9600 and make sure the shield is running at
    # 4800. An alternative is to increase buffer size in the Arduino SoftwareSerial
    # library.
    parser = argparse.ArgumentParser(description='Run SMS Data Logger.')
    parser.add_argument('-d', '--db', help='Sqlite3 database file', default='data/ua_sensors.sqlite3')
    parser.add_argument('-p', '--port', help='Serial port', default='/dev/ttyS1')
    parser.add_argument('-b', '--baudrate', type=int, help='Baudrate of Sim900 GSM shield', default=115200)
    args = parser.parse_args()

    db = args.db
    port = args.port
    baudrate = args.baudrate


    # Setup logger
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

    logger = logging.getLogger()
    file_log_handler = logging.FileHandler(LOG_FILE)
    logger.addHandler(file_log_handler)

    formatter = logging.Formatter(LOG_FORMAT)
    file_log_handler.setFormatter(formatter)


    # Need to initalize gpio0 and gpio1 to UART mode if pcDuino.
    # If not pcDuino, just ignore the error.
    try:
        enableUart()
    except:
        pass

    # Creates a serial connection to Sim900 shield
    sim900 = Sim900(Serial(port, baudrate=baudrate, timeout=0), delay=0.5)

    # Listens for incoming SMS
    reader = SMSReader(sim900)

    # Parses brige sensor message into usable data.
    parser = DataParser()

    # Logs data into Sqlite3 db
    data_logger = SensorReadingsDataStore(db)
    data_logger.setup()

    # For non-pcDuino devices, there looks to be a delay before commands
    # are sent and read correctly. Waiting two seconds seems to work.
    print "Initializing serial connection..."
    sleep(2)

    print ""
    print "Sim900 SMS Data Logger"
    print "----------------------"
    print ""
    print "Press CTRL+C to stop the program."
    print ""

    print reader.init_reader()

    while True:
        text_msg = reader.listen()
        if text_msg is not None:
            logger.info("Text message received at {0}.".format(datetime.now().strftime("%m/%d/%Y %H:%M:%S")))
            logger.info(text_msg)
            try:
                readings = parser.parse(text_msg.phone_number, text_msg.message)
                data_logger.store_readings(readings)
                logger.info("{0} readings logged from sensor {1}.".format(len(readings), readings[0][0]))
            except ValueError:
                logger.error("Could not parse text message!")
            except ProgrammingError:
                logger.error("Could not save readings to database!")


if __name__ == '__main__':
    main()