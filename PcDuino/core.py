from datetime import datetime, timedelta
import re
import sqlite3
import time

class DataParser(object):
    """
    Parses bridge message into list of readings.
    """

    READING_FORMAT = "^\d+ \d+ \d+(?:;\d+ \d+ \d+)+$"
    SECONDS_PER_MINUTE = 60
    READING_DELIM = ';'
    DATA_DELIM = ' '

    SENSOR_ID_IDX = 0
    TIMESTAMP_IDX = 1
    DISTANCE_IDX = 2
    TEMPERATURE_IDX = 3

    def __init__(self):
        self.readings_regex = re.compile(self.READING_FORMAT)

    def parse(self, sensor_id, message):
        """
        Parses bridge sensor messages.

        Returns:
            List of parsed readings. Each reading contains:

            [0] = Sensor id
            [1] = Unix timestamp
            [2] = Distance
            [3] = Temperature
        """
        result = self.readings_regex.findall(message.strip())
        if len(result) == 0:
            raise ValueError("Received invalid message format!")

        body = result[0]
        raw_readings = [section.split(self.DATA_DELIM) for section in body.split(self.READING_DELIM)]
        first_reading = [int(val.strip()) for val in raw_readings[0]]
        first_reading.insert(self.SENSOR_ID_IDX, sensor_id)

        readings = [first_reading]
        for raw_reading in raw_readings[1:]:
            reading = [int(val.strip()) for val in raw_reading]
            reading.insert(self.SENSOR_ID_IDX, sensor_id)
            reading[self.TIMESTAMP_IDX] = (first_reading[self.TIMESTAMP_IDX] +
                (reading[self.TIMESTAMP_IDX] * self.SECONDS_PER_MINUTE))
            readings.append(reading)
        return readings


class SensorReadingsDataStore(object):
    """
    Fetches sensor data from sqlite3 database.
    """

    TABLE = 'readings'
    COLUMNS = ('sensor_id', 'reading_date', 'distance', 'temperature')

    CREATE_TABLE_QUERY = """
        CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id TEXT,
        sensor_type TEXT,
        reading_date INTEGER,
        distance INTEGER,
        temperature INTEGER
    );
    """

    INPUT_DATE_FORMAT = "%m/%d/%Y"
    MILLIS_PER_SECOND = 1000

    def __init__(self, db_name, persistent=False):
        self.db_name = db_name
        self.persistent = persistent
        self.sensors = None
        self.conn = None

    def setup(self):
        """
        Creates Sqlite3 connection and creates readings
        table if it does not exist yet.
        """
        self.open_connection()
        cursor = self.conn.cursor()
        cursor.execute(self.CREATE_TABLE_QUERY)
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
        if self.conn is None:
            self.open_connection()

        query = "INSERT INTO {} ({}) VALUES ({})".format(
            self.TABLE,
            ','.join(self.COLUMNS),
            ','.join(['?' for x in xrange(len(self.COLUMNS))]))

        cursor = self.conn.cursor()
        cursor.executemany(query, readings)
        self.conn.commit()
        cursor.close()

        if not self.persistent:
            self.close_connection()

    def fetch_sensors(self, cached=False):
        """
        Fetches list of sensors with data in the database.
        """
        if cached and self.sensors:
            return self.sensors

        query = "SELECT DISTINCT {0} FROM {1}".format(self.COLUMNS[0], self.TABLE)
        data = []
        for row in self.execute_query(query):
            data.append(row[0])
        self.sensors = data

        return data

    def fetch(self, sensor=None, start_date=None, end_date=None):
        """
        Fetches timestamp, temperature and distance data from database.

        Args:
            sensor: Name of sensor
            start_date: Start date in the format "%m/%d/%Y". Implied time is 00:00:00.
            end_date: End date in the format "%m/%d/%Y". Implied time would be 23:59:59.

        Returns:
            A list containing a list of distance readings and a list of temperature readings.
        """
        query = "SELECT {0} FROM {1}".format(','.join(self.COLUMNS), self.TABLE)

        clause = []
        params = []

        sensors = self.fetch_sensors(True)
        if sensor in sensors:
            clause.append("{0} = ?".format(self.COLUMNS[0]))
            params.append(sensor)

        if start_date:
            start_dt = datetime.strptime(start_date, self.INPUT_DATE_FORMAT)
            start_timestamp = int(time.mktime(start_dt.timetuple()))
            clause.append("{0} >= ?".format(self.COLUMNS[1]))
            params.append(start_timestamp)

        if end_date:
            end_dt = datetime.strptime(end_date, self.INPUT_DATE_FORMAT)
            end_dt += timedelta(days=1)
            end_timestamp = int(time.mktime(end_dt.timetuple()))
            clause.append("{0} <= ?".format(self.COLUMNS[1]))
            params.append(end_timestamp)

        if len(clause) > 0 and len(clause) == len(params):
            query += ' WHERE ' + ' AND '.join(clause)

        data_distance = []
        data_temperature = []
        for row in self.execute_query(query, params):
            data_distance.append((row[1] * self.MILLIS_PER_SECOND, row[2]))
            data_temperature.append((row[1] * self.MILLIS_PER_SECOND, row[3]))
        return [data_distance, data_temperature]

    def execute_query(self, query, params=[]):
        """
        Executes query against db and returns data for processing using
        generator/yield feature.
        """
        if self.conn is None:
            self.open_connection()

        cursor = self.conn.cursor()
        for row in cursor.execute(query, params):
            yield row
        cursor.close()

        if not self.persistent:
            self.close_connection()
