import logging

def get_config():
    """
    Gets the config file parsed by the Flask web server app

    The import is specified within the function so that
    app instance is garbage collected. Need to verify this.

    Kind of slows down application start up. May want to create
    custom function that only extracts config instead of loading
    all the web server code which is unnecessary.
    """
    from server import app
    return app.config.copy()


def create_logger_from_config(config):
    """
    Creates a python logger object to log to file and console

    Currently the logger must be created. No option to turn off yet,
    but possible setting to error level ERROR would be enough.

    Expected values in config dict:

    - DATA_LOGGER_ERROR_LEVEL
    - DATA_LOGGER_ERROR_FORMAT
    - DATA_LOGGER_ERROR_FILE

    Args:
        config: dict containing log level, log format, and log file values

    Returns:
        Instance of python logger

    """
    level = getattr(logging, config.get('DATA_LOGGER_ERROR_LEVEL', 'ERROR'))
    format = config.get('DATA_LOGGER_ERROR_FORMAT', '%(levelname)s - %(message)s')
    filepath = config.get('DATA_LOGGER_ERROR_FILE', 'log/sensor.log')
    logging.basicConfig(level=level, format=format)

    logger = logging.getLogger()
    file_log_handler = logging.FileHandler(filepath)
    logger.addHandler(file_log_handler)

    formatter = logging.Formatter(format)
    file_log_handler.setFormatter(formatter)

    return logger


def parse_sensor_types_config(sensor_types):
    """
    Parses sensor types config values to be more code friendly.

    The sensor types config was designed to be simple and use as
    little syntax as possible. However it is not the best format
    for for processing. This function just transforms the config
    format to something more usable.

    Args:
        sensor_types: A 2d tuple. Inner tuple contains metadata for sensor types

    Returns:
        Sensor type metadata in better format. Example:

        expected_result = {
            'a': {
                'name': 'A_TYPE',
                'data_types': (('distance, meters'), ('temperature celsius'))
            },
            'b': {
                'name': 'B_TYPE',
                'data_types': (('distance, meters'))
            },
            'c': {
                'name': 'B_TYPE',
                'data_types': (('moisture, percent'), ('temperature celsius'), ('distance, meters'))
            },
        }
    """
    sensor_types_map = {}
    for sensor_meta in sensor_types:
        sensor_types_map[sensor_meta[0]] = {
            'name': sensor_meta[1],
            'data_types': tuple([(data_meta.strip().split(' ')) for data_meta in sensor_meta[2].split(';')])
        }
    return sensor_types_map
