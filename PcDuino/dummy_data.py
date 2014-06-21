#! /usr/bin/env python
import argparse
import csv
import random
import time

from utils import get_config, parse_sensor_types_config

MAX_VALUE = 200
MIN_VALUE = 20
SECONDS_IN_DAY = 60 * 60 * 24

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate dummy data for testing.')
    parser.add_argument('-o', '--output', help="Output file path for csv", default="dummy_data.csv")
    parser.add_argument('-s', '--sensors', help='Number of sensors', type=int, default=4)
    parser.add_argument('-r', '--readings', help='Number of readings per sensor per day', type=int, default=60)
    parser.add_argument('-d', '--days', help='Number of days of stored data', type=int, default=60)

    args = parser.parse_args()
    outfile = args.output
    num_sensors = args.sensors
    num_readings = args.readings
    num_days = args.days
    total_readings = num_days * num_readings
    interval = SECONDS_IN_DAY / num_readings


    # Get sensor types defined in configuration file
    config = get_config()
    sensor_types = parse_sensor_types_config(config['SENSOR_TYPES'])


    # Generate random value ranges that the sensor types will read
    sensor_ranges = {}
    for key, value in sensor_types.items():
        sensor_ranges[key] = []

        for data_type in value['data_types']:
            min_value = random.randint(MIN_VALUE, MAX_VALUE)
            if min_value > MAX_VALUE - (MAX_VALUE / 10):
                max_value = min_value
                min_value = random.randint(MIN_VALUE, max_value)
            else:
                max_value = random.randint(min_value, MAX_VALUE)
            sensor_ranges[key].append((min_value, max_value))


    # Create a some fake sensors
    sensor_list = []
    for i in xrange(num_sensors):
        sensor_list.append({
            'id': "sensor_" + str(i),
            'code': random.choice(sensor_types.keys()),
        })


    # Generate fake readings starting from today to `num_days` in the past
    readings = []
    current_time = None
    for i in xrange(total_readings):
        if current_time is None:
            current_time = int(time.time())
        else:
            current_time -= interval

        for sensor in sensor_list:
            sensor_type = sensor_types[sensor['code']]['name']
            data_types = sensor_types[sensor['code']]['data_types']
            data_ranges = sensor_ranges[sensor['code']]
            for j in xrange(len(data_types)):
                readings.append((
                    sensor['id'],
                    sensor_type,
                    current_time,
                    random.randint(*data_ranges[j]),
                    data_types[j][0],
                    data_types[j][1]
                ))

    with open(outfile, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(readings)


if __name__ == '__main__':
    main()
