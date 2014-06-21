#! /usr/bin/env python
import argparse
from datetime import datetime
import logging
from serial import Serial
from sqlite3 import ProgrammingError
from time import sleep

from core import SensorReadingsDataStore, DataParser, MessageFormatError
from gpio import enableUart
from sim900 import Sim900, SMSReader
from utils import get_config, create_logger_from_config


def main():

    # Parse command line arguments
    #
    # The default settings will work well for the pcDuino. If you
    # are using a laptop or Raspberry Pi, then you will need to set
    # the serial baud rate to 9600 and make sure the shield is running at
    # 4800. An alternative is to increase buffer size in the Arduino SoftwareSerial
    # library.
    parser = argparse.ArgumentParser(description='Run SMS Data Logger.')
    parser.add_argument('-p', '--port', help='Serial port', default='/dev/ttyS1')
    parser.add_argument('-b', '--baudrate', type=int, help='Baudrate of Sim900 GSM shield', default=115200)
    args = parser.parse_args()

    port = args.port
    baudrate = args.baudrate


    # Get config file for logging settings and db file path
    config = get_config()

    # Filepath path to sqlite3 database. Database does not need to exist.
    # Just make sure folder exists.
    db = config['SQLITE3_DB_PATH']

    # Setup logger
    logger = create_logger_from_config(config)


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
            except MessageFormatError as e:
                logger.error(str(e))
            except ProgrammingError as e:
                logger.error(str(e))


if __name__ == '__main__':
    main()