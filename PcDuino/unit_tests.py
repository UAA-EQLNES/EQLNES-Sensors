#!/usr/bin/env python

"""
Unit tests for Sim900 GSM module
"""

from os import remove
import sqlite3
import unittest

from core import SensorReadingsDataStore, DataParser, MessageFormatError
from sim900 import Sim900, SMSReader, TextMsg
from utils import get_config, parse_sensor_types_config, create_logger_from_config


class TestSMSReader(unittest.TestCase):

    def setUp(self):
        mock_sim900 = {}
        self.sms_reader = SMSReader(mock_sim900)

    def test_extract_valid_sms(self):
        sms = "\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\n"
        result_text_msg = self.sms_reader.extract_sms(sms)
        expected_text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60")
        self.assertEqual(result_text_msg, expected_text_msg)

    def test_extract_valid_sms_with_gibberish(self):
        expected_sms = "\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\n"
        gibberish_sms = "asdadad adasds+CMadTsadad\r\nsdasdasd" + expected_sms + "\r\nsdsdfsdf sf\r\n+CM"
        result_text_msg = self.sms_reader.extract_sms(expected_sms)
        expected_text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60")
        self.assertEqual(result_text_msg, expected_text_msg)

    def test_extract_invalid_sms_missing_cmt(self):
        sms = "sdfsdfsdf\r\n+CMDT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\ndsfsd\r\nf"
        result_text_msg = self.sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)

    def test_extract_invalid_sms_wrong_header(self):
        sms = "sdfsdfsdf\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\", \"extra_param\"\r\n399735312 100 10;20 200 20;40 400 40;65 6dsfsdff"
        result_text_msg = self.sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)

    def test_extract_invalid_sms_garbled_ending(self):
        sms = "sdfsdfsdf\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n399735312 100 10;20 200 20;40 400 40;65 6dsfsdff"
        result_text_msg = self.sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)


class TestUtils(unittest.TestCase):

    def test_util_create_logger_from_config(self):
        test_log_file = 'unit_test.log'
        config = {
            'DATA_LOGGER_ERROR_FILE': test_log_file,
            'DATA_LOGGER_ERROR_LEVEL': 'WARN'
        }
        logger = create_logger_from_config(config)
        remove(test_log_file)

    def test_util_parse_sensor_types_config(self):
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
        sensor_types = (
            ("a", "A_TYPE", "distance meters; temperature celsius"),
            ("b", "B_TYPE", "distance meters"),
            ("c", "C_TYPE", "moisture percent; temperature celsius; distance meters"),
        )
        result = parse_sensor_types_config(sensor_types)
        self.assertItemsEqual(result, expected_result)


class TestDataParser(unittest.TestCase):

    def setUp(self):
        config = get_config()
        sensor_types_map = parse_sensor_types_config(config['SENSOR_TYPES'])
        self.parser = DataParser(sensor_types_map)


    def test_valid_readings(self):
        expected_readings = [
            ["+12223334444", 'Water', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'Water', 1399735312, 10, 'temperature', 'celsius'],
            ["+12223334444", 'Water', 1399736512, 200, 'distance', 'meters'],
            ["+12223334444", 'Water', 1399736512, 20, 'temperature', 'celsius'],
            ["+12223334444", 'Water', 1399737712, 400, 'distance', 'meters'],
            ["+12223334444", 'Water', 1399737712, 40, 'temperature', 'celsius'],
            ["+12223334444", 'Water', 1399739212, 600, 'distance', 'meters'],
            ["+12223334444", 'Water', 1399739212, 60, 'temperature', 'celsius'],
        ]
        text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "d 1399735312 100 10;20 200 20;40 400 40;65 600 60")
        readings = self.parser.parse(text_msg.phone_number, text_msg.message)
        self.assertItemsEqual(readings, expected_readings)

    def test_no_sensor_type_reading(self):
        with self.assertRaises(MessageFormatError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60123; 23123 23")
            readings = self.parser.parse(text_msg.phone_number, text_msg.message)

    def test_incorrect_sensor_type_reading(self):
        with self.assertRaises(MessageFormatError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "g 1399735312 100 10;20 200 20;40 400 40;65 600 60123; 23123 23")
            readings = self.parser.parse(text_msg.phone_number, text_msg.message)

    def test_garbled_reading(self):
        with self.assertRaises(MessageFormatError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "d 1399735312 100 10;20 200 20;40 400 40;65 600 60123; 23123 23")
            readings = self.parser.parse(text_msg.phone_number, text_msg.message)

    def test_valid_invalid_readings(self):
        with self.assertRaises(MessageFormatError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "Hello, this is a random text message.")
            readings = self.parser.parse(text_msg.phone_number, text_msg.message)


class TestSensorReadingsDataStore(unittest.TestCase):

    def setUp(self):
        self.data_logger = SensorReadingsDataStore(':memory:', True)
        self.data_logger.setup()

    def test_valid_readings(self):
        readings = [
            ["+12223334444", 'distance', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'distance', 1399735312, 20, 'temperature', 'celsius'],
            ["+12223334444", 'gate', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'soil', 1399737712, 90, 'moisture', 'percent'],
            ["+12223334444", 'soil', 1399737712, 30, 'temperature', 'celsius'],
        ]
        self.data_logger.store_readings(readings)

    def test_invalid_readings(self):
        readings = [
            ["+12223334444", 'distance', 1399735312, 100, 'distance', 'meters'],
            ["+12223334444", 'distance', 1399735312, 20, 'temperature', 'celsius'],
            ["+12223334444", 'gate', 1399735312, 100, 'distance'],
            ["+12223334444", 'soil', 1399737712, 90, 'moisture', 'percent'],
            ["+12223334444", 'soil', 1399737712, 30, 'temperature', 'celsius'],
        ]
        with self.assertRaises(sqlite3.ProgrammingError):
            self.data_logger.store_readings(readings)


if __name__ == '__main__':
    unittest.main()
