from datetime import datetime, timedelta
import re
import sqlite3
import time
from utils import parse_sensor_types_config


class MessageFormatError(Exception):
    """
    Thrown for format errors when parsing messages
    """
    pass


class DataParser(object):
    """
    Parses sensor messages into list of readings.

    General format:*

    sensor_type unix_timestamp sensor_value [ sensor_value ...][;minutes_since_first_reading sensor_value [ sensor_value ...]...]

    Example message: g 1399735312 120 20;20 124 15; 40 122 18

    \* Format syntax notes:
      - Braces represent optional text. Depends on number of readings sent.
      - sensor_type: Is a single character, such as 'd', 'g', 's', etc
      - unix_timestamp: Is unix timestamp
      - sensor_value: Depends on sensor. Could represent any value, but is expected to be integer
      - minutes_since_first_reading: Is number of minutes since first reading in message.
      - semi-colon delimits new reading
      - Reading can contain multiple sensor values depending on type of sensor.
        For example may have sensor may send ultrasonic and themistor data back
    """

    READING_FORMAT_TEMPLATE = "^\d+ {0}(?:;\d+ {0})+$"
    SECONDS_PER_MINUTE = 60
    READING_DELIM = ';'
    DATA_DELIM = ' '

    def __init__(self, sensor_types_map):
        """
        Initalizes data parser

        Parser is fairly strict and will throw MessageFormatError. Make sure
        sensor type code has the correct number/types of data to be expected
        from that type of sensor.

        Args:
            sensor_types_map: See format specified by utils.parse_sensor_types_config
        """
        self.sensor_types_map = sensor_types_map
        self.data_format = {}
        for key, value in self.sensor_types_map.items():
            reading_re = re.compile(DataParser.READING_FORMAT_TEMPLATE.format(
                ' '.join(['\d+' for x in xrange(len(value['data_types']))])))
            self.data_format[key] = reading_re

    def parse(self, sensor_id, message):
        """
        Parses bridge sensor messages.

        Args:
            sensor_id: Unique sensor id. For GSM shields, can be phone number
            message: Formatted message received from sensor that contains data

        Returns:
            List of parsed readings. Each reading contains:

            [0] = Sensor id
            [1] = Sensor type
            [2] = Unix timestamp
            [3] = Value
            [4] = Value type
            [5] = Value unit
        """

        if message[0] not in self.data_format:
            raise MessageFormatError('Missing sensor code!')

        sensor_type_meta = self.sensor_types_map[message[0]]
        readings_format = self.data_format[message[0]]
        result = readings_format.findall(message[1:].strip())
        if len(result) == 0:
            raise MessageFormatError("Invalid message format!")

        body = result[0]
        raw_readings = [section.split(self.DATA_DELIM) for section in body.split(self.READING_DELIM)]

        readings = []
        data_types = sensor_type_meta['data_types']
        for raw_reading in raw_readings:
            timestamp = int(raw_reading[0])
            if len(readings) > 0:
                timestamp = readings[0][2] + (timestamp * self.SECONDS_PER_MINUTE)

            data_values = raw_reading[1:]
            for i in xrange(len(data_values)):
                readings.append([
                    sensor_id,
                    sensor_type_meta['name'],
                    timestamp,
                    int(data_values[i]),
                    data_types[i][0],
                    data_types[i][1]
                ])
        return readings


class SensorReadingsTable(object):
    """
    Represents metadata used to build database table
    """

    NAME = 'readings'
    COLUMNS = (
        ('sensor_id', 'INTEGER'),
        ('sensor_type', 'TEXT'),
        ('timestamp', 'INTEGER'),
        ('value', 'INTEGER'),
        ('value_type', 'TEXT'),
        ('value_unit', 'TEXT'),
    )

    @staticmethod
    def get_col_names():
        """
        Gets the list of columns as a tuple with out data type

        Returns:
            Tuple of column names
        """
        return tuple([col[0] for col in SensorReadingsTable.COLUMNS])

# Kind of a hack to add special class variables to SensorReadingsTable class
#
# Basically allows you to specify the name of a column. Ex: SensorReadingsTable.COL_SENSOR_ID == 'sensor_id'
# There is also an option to get column index. Ex: SensorReadingsTable.IDX_TIMESTAMP == 2
for col_index in xrange(len(SensorReadingsTable.COLUMNS)):
    column = SensorReadingsTable.COLUMNS[col_index]
    setattr(SensorReadingsTable, 'COL_' + column[0].upper(), column[0])
    setattr(SensorReadingsTable, 'IDX_' + column[0].upper(), col_index)


class SensorReadingsDataStore(object):
    """
    Provides basic access to sensor data from sqlite3 database.
    """

    MILLIS_PER_SECOND = 1000

    CREATE_TABLE_QUERY = """
        CREATE TABLE IF NOT EXISTS {} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {}
    );
    """

    def __init__(self, db_name, persistent=False, table=SensorReadingsTable):
        """
        Initializes class

        Args:
            db_name: Filepath to sqlite3 database
            persistent: Use a persistent db connection
            table: Metadata class that represent db table. Defaults to SensorReadingsTable
        """
        self.db_name = db_name
        self.table = SensorReadingsTable
        self.persistent = persistent
        self.sensors = None
        self.conn = None

    def setup(self):
        """
        Creates Sqlite3 connection and creates necessary table if it does not exist yet.
        """
        self.open_connection()
        cursor = self.conn.cursor()

        query = self.CREATE_TABLE_QUERY.format(
            self.table.NAME,
            ', '.join([' '.join(meta) for meta in self.table.COLUMNS]))
        cursor.execute(query)

        self.conn.commit()
        cursor.close()

        if not self.persistent:
            self.close_connection()

    def open_connection(self):
        self.conn = sqlite3.connect(self.db_name)

    def close_connection(self):
        self.conn.close()
        self.conn = None

    def store_readings(self, readings):
        """
        Saves properly formatted list of sensor readings in database

        Example format of readings:

        readings = [
            ["+12223334444", 'distance', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'distance', 1399735312, 20, 'temperature', 'celsius'],
            ["+12223334444", 'gate', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'soil', 1399737712, 90, 'moisture', 'percent'],
            ["+12223334444", 'soil', 1399737712, 30, 'temperature', 'celsius'],
        ]

        Currently order of sensor data fields is based on order specified in
        SensorReadingsTable class or equivalent class.

        Args:
            readings: 2d list of sensor readings with correct data.
        """
        if self.conn is None:
            self.open_connection()

        columns = self.table.get_col_names()
        query = "INSERT INTO {} ({}) VALUES ({})".format(
            self.table.NAME,
            ','.join(columns),
            ','.join(['?' for x in xrange(len(columns))]))

        cursor = self.conn.cursor()
        cursor.executemany(query, readings)
        self.conn.commit()
        cursor.close()

        if not self.persistent:
            self.close_connection()

    def fetch_sensors(self, cached=False):
        """
        Fetches tuple of sensors with data in the database.

        This value can be cached to avoid repeatedly getting the same set of sensors. May want
        to turn the cache setting off when initially populating database or adding new sensors
        into the field.

        Args:
            cached: Whether to cache sensor list or not

        Returns:
            List of sensor ids. Ex: ('sensor1', 'sensor2', 'sensor3')
        """
        if cached and self.sensors:
            return self.sensors

        query = "SELECT DISTINCT {0} FROM {1}".format(self.table.COL_SENSOR_ID, self.table.NAME)
        data = []
        for row in self._execute_query(query):
            data.append(str(row[0]))
        self.sensors = data

        return tuple(data)

    def fetch(self, sensor=None, start_date=None, end_date=None, date_format="%m/%d/%Y"):
        """
        Fetches sensor readings data from database.

        Args:
            sensor: Name of sensor
            start_date: Start date in the format "%m/%d/%Y". Implied time is 00:00:00.
            end_date: End date in the format "%m/%d/%Y". Implied time would be 23:59:59.

        Returns:
            A list containing a list of measurements with timestamp
        """
        query = "SELECT {0} FROM {1}".format(','.join(self.table.get_col_names()), self.table.NAME)

        clause = []
        params = []

        sensors = self.fetch_sensors(True)
        if sensor in sensors:
            clause.append("{0} = ?".format(self.table.COL_SENSOR_ID))
            params.append(sensor)

        if start_date:
            start_dt = datetime.strptime(start_date, date_format)
            start_timestamp = int(time.mktime(start_dt.timetuple()))
            clause.append("{0} >= ?".format(self.table.COL_TIMESTAMP))
            params.append(start_timestamp)

        if end_date:
            end_dt = datetime.strptime(end_date, date_format)
            end_dt += timedelta(days=1)
            end_timestamp = int(time.mktime(end_dt.timetuple()))
            clause.append("{0} <= ?".format(self.table.COL_TIMESTAMP))
            params.append(end_timestamp)

        if len(clause) > 0 and len(clause) == len(params):
            query += ' WHERE ' + ' AND '.join(clause)

        data = {}
        for row in self._execute_query(query, params):

            sensor_id = row[self.table.IDX_SENSOR_ID]
            sensor_type = row[self.table.IDX_SENSOR_TYPE]
            timestamp = row[self.table.IDX_TIMESTAMP]
            value = row[self.table.IDX_VALUE]
            value_type = row[self.table.IDX_VALUE_TYPE]
            value_unit = row[self.table.IDX_VALUE_UNIT]

            if value_type not in data:
                data[value_type] = {
                    'meta': {
                        self.table.COL_SENSOR_TYPE: sensor_type,
                        self.table.COL_VALUE_TYPE: value_type,
                        self.table.COL_VALUE_UNIT: value_unit
                    },
                    'data': []
                }
            data[value_type]['data'].append((timestamp * self.MILLIS_PER_SECOND, value))
        return data.values()

    def _execute_query(self, query, params=[]):
        """
        Executes query against db and returns data for processing using
        generator/yield feature.

        Private helper method. Should not be used directly.
        """
        if self.conn is None:
            self.open_connection()

        cursor = self.conn.cursor()
        for row in cursor.execute(query, params):
            yield row
        cursor.close()

        if not self.persistent:
            self.close_connection()
