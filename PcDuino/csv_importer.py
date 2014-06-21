#! /usr/bin/env python
import argparse
import csv
import time
import sqlite3

from core import SensorReadingsDataStore


def main():
    """
    Example on how to import CSV into Sqlite3 database. In this case, the data comes
    from a csv file generated from dummy_data.py

    Expected order of columns:

        [0] = Sensor ID
        [1] = Sensor Type
        [2] = Unix timestamp
        [3] = Value
        [4] = Value Type
        [5] = Value Unit
    """

    parser = argparse.ArgumentParser(description='Import CSV data into sensor readings database')
    parser.add_argument('-d', '--db', help='Sqlite3 database file', default='data/ua_sensors_test.sqlite3')
    parser.add_argument('-c', '--csv', help='CSV Filename', default='dummy_data.csv')
    args = parser.parse_args()

    db = args.db
    csv_filename = args.csv
    readings = []
    with open(csv_filename, 'r') as csvfile:
        data = csv.reader(csvfile)
        for line in data:
            readings.append([line[0], line[1], int(line[2]), int(line[3]), line[4],line[5]])

    logger = SensorReadingsDataStore(db)
    logger.setup()
    logger.store_readings(readings)


if __name__ == '__main__':
    main()