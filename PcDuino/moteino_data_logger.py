#! /usr/bin/env python
import argparse
from datetime import datetime
import logging
from serial import Serial
from core import DataParser, SensorReadingsDataStore
from sqlite3 import ProgrammingError
from time import sleep


LOG_FILE = 'log/sensor.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(levelname)s - %(message)s'


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
    parser.add_argument('-d', '--db', help='Sqlite3 database file', default='data/ua_sensors.sqlite3')
    parser.add_argument('-b', '--baudrate', type=int, help='Baudrate of Moteino', default=115200)
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

    # Creates a serial connection to Moteino
    serial = Serial(port, baudrate=baudrate, timeout=0)

    # Parses brige sensor message into usable data.
    parser = DataParser()

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
                except ValueError:
                    logger.error("Could not parse message!")
                except ProgrammingError:
                    logger.error("Could not save readings to database!")
        sleep(0.1)


if __name__ == '__main__':
    main()