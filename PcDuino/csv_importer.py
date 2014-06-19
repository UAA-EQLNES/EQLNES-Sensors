#! /usr/bin/env python
import argparse
import csv
import time
import sqlite3
from datetime import datetime
from sim900 import SqliteDataLogger


def datetime_to_timestamp(date, date_format):
    """
    Converts date/time string to unix timestamp. Note that
    the date/time string will interpreted using the local
    timezone on your system.

    The resulting unix timestamp will be in GMT time.
    """
    dt = datetime.strptime(date, date_format)
    return int(time.mktime(dt.timetuple()))


def import_csv(csv_filename, db_filename, date_format="%m/%d/%Y %H:%M:%S"):
    readings = []
    with open(csv_filename, 'r') as csvfile:
        data = csv.reader(csvfile)
        next(data)
        for line in data:
            timestamp = datetime_to_timestamp(line[0], date_format)
            readings.append((line[3], timestamp, int(line[1]), int(line[2])))

    logger = SqliteDataLogger(db_filename)
    logger.init_logger()
    logger.log(readings)


def main():
    """
    Example on how to import CSV into Sqlite3 database. In this case, the
    CSV file was exported from Google Fusion tables with the following properties:

    [0] = Timestamp with the following format: "%m/%d/%Y %H:%M:%S". Example: 5/10/2014 13:12:12"
    [1] = Distance
    [2] = temperature
    [3] = Sensor ID
    """

    parser = argparse.ArgumentParser(description='Import CSV data into sensor readings database')
    parser.add_argument('-d', '--db', help='Sqlite3 database file', default='data/ua_sensors.sqlite3')
    parser.add_argument('-c', '--csv', help='CSV Filename', default='sample_data.csv')
    args = parser.parse_args()
    import_csv(args.csv, args.db)


if __name__ == '__main__':
    main()