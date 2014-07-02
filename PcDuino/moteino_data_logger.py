#! /usr/bin/env python
import argparse
from datetime import datetime
from serial import Serial
from sqlite3 import ProgrammingError
from time import sleep

from core import DataParser, SensorReadingsDataStore, MessageFormatError
from utils import get_config, create_logger_from_config, parse_sensor_types_config


def read_all(serial, delay=0.1):
    """
    Attempts to read all incoming input even if the
    baud rate is very slow (ie 4800 bps) and only returns
    if no change is encountered.
    """
    msg = ""
    prev_len = 0
    curr_len = 0
    while True:
        prev_len = curr_len
        while serial.inWaiting() != 0:
            msg += serial.read(serial.inWaiting())
            curr_len = len(msg)
            sleep(delay)
        if prev_len == curr_len:
            break
    return msg.strip()


def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Moteino Data Logger.')
    parser.add_argument('-p', '--port', help='Serial port')
    parser.add_argument('-b', '--baudrate', type=int, help='Baudrate of Moteino', default=115200)
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

    # Creates a serial connection to Moteino
    serial = Serial(port, baudrate=baudrate, timeout=0)

    # Parses brige sensor message into usable data.
    parser = DataParser(parse_sensor_types_config(config['SENSOR_TYPES']))

    # Logs data into Sqlite3 db
    data_logger = SensorReadingsDataStore(db)
    data_logger.setup()


    print "Initializing serial connection..."
    sleep(2)

    print ""
    print "Moteino Data Logger"
    print "----------------------"
    print ""
    print "Press CTRL+C to stop the program."
    print ""

    while True:
        if serial.inWaiting() > 0:
            message = read_all(serial)
            if len(message) > 0:
                logger.info("Message received at {0}.".format(datetime.now().strftime("%m/%d/%Y %H:%M:%S")))
                logger.info(message)

                try:
                    parts = message.split(':')
                    if len(parts) != 2:
                        raise ValueError
                    readings = parser.parse(parts[0], parts[1])
                    data_logger.store_readings(readings)
                except MessageFormatError as e:
                    logger.error(str(e))
                except ProgrammingError as e:
                    logger.error(str(e))
        sleep(0.1)


if __name__ == '__main__':
    main()