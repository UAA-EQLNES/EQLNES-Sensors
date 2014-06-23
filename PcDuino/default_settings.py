# Web server
DEBUG = True
HOST = '127.0.0.1'
PORT = 5000
TEMPLATE = 'flot.html'

SITE_TITLE = "UA Sensors Visualization"

# Database location
SQLITE3_DB_PATH = 'data/ua_sensors.sqlite3'


# Sensor type mapping
#
# - First parameter is the identifier sent from sensors in the wild
# - Second parameter is the readable name of the sensor type
# - Third parameter is the types of readings returned
#   - Semi-colon separates different sensor reading types
#   - Each reading type needs to specify type and unit of measurement
#   - For, example TYPE UNITS; TYPE UNITS -> distance meters; temperature celsius
SENSOR_TYPES = (
    ("d", "Water", "distance meters; temperature celsius"),
    ("g", "Gate", "distance meters"),
    ("s", "Soil", "moisture percent; temperature celsius"),
)


# Maps sensor ids to more informative name.
#
# Not all sensors need to be named. Can be adjusted later, just remember to
# restart server on config file updates
#
# For instance, +12223334444 is not as informative as Campbell Creek Water Sensor
#
# Example format:
#
# SENSOR_NAMES = {
#   '+12223334444': 'Yosemite Distance Sensor',
#   '+01234567890': 'Siberia Gate Sensor',
#   'moteino_1': 'Arctic Ocean Moisture Sensor',
# }
SENSOR_NAMES = {}


# Data logger error logging
DATA_LOGGER_ERROR_FILE = 'log/ua_sensor.log'
DATA_LOGGER_ERROR_LEVEL = 'INFO'
DATA_LOGGER_ERROR_FORMAT = '%(levelname)s - %(message)s'