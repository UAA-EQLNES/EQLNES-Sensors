#!/usr/bin/env python

"""
Unit tests for Sim900 GSM module
"""

from sim900 import Sim900, SMSReader, TextMsg
from core import SensorReadingsDataStore, DataParser
import sqlite3
import unittest


class TestSMSReader(unittest.TestCase):

    def test_extract_valid_sms(self):
        sms = "\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\n"
        mock_sim900 = {}
        sms_reader = SMSReader(mock_sim900)
        result_text_msg = sms_reader.extract_sms(sms)
        expected_text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60")
        self.assertEqual(result_text_msg, expected_text_msg)

    def test_extract_valid_sms_with_gibberish(self):
        expected_sms = "\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\n"
        gibberish_sms = "asdadad adasds+CMadTsadad\r\nsdasdasd" + expected_sms + "\r\nsdsdfsdf sf\r\n+CM"
        mock_sim900 = {}
        sms_reader = SMSReader(mock_sim900)
        result_text_msg = sms_reader.extract_sms(expected_sms)
        expected_text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60")
        self.assertEqual(result_text_msg, expected_text_msg)

    def test_extract_invalid_sms_missing_cmt(self):
        sms = "sdfsdfsdf\r\n+CMDT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n1399735312 100 10;20 200 20;40 400 40;65 600 60\r\ndsfsd\r\nf"
        mock_sim900 = {}
        sms_reader = SMSReader(mock_sim900)
        result_text_msg = sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)

    def test_extract_invalid_sms_wrong_header(self):
        sms = "sdfsdfsdf\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\", \"extra_param\"\r\n399735312 100 10;20 200 20;40 400 40;65 6dsfsdff"
        mock_sim900 = {}
        sms_reader = SMSReader(mock_sim900)
        result_text_msg = sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)

    def test_extract_invalid_sms_garbled_ending(self):
        sms = "sdfsdfsdf\r\n+CMT: \"+12223334444\",\"\",\"14/05/30,00:13:34-32\"\r\n399735312 100 10;20 200 20;40 400 40;65 6dsfsdff"
        mock_sim900 = {}
        sms_reader = SMSReader(mock_sim900)
        result_text_msg = sms_reader.extract_sms(sms)
        self.assertIsNone(result_text_msg)


class TestDataParser(unittest.TestCase):

    def test_valid_readings(self):
        expected_readings = [
            ["+12223334444", 1399735312, 100, 10],
            ["+12223334444", 1399736512, 200, 20],
            ["+12223334444", 1399737712, 400, 40],
            ["+12223334444", 1399739212, 600, 60],
        ]
        text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60")
        parser = DataParser()
        readings = parser.parse(text_msg.phone_number, text_msg.message)
        self.assertItemsEqual(readings, expected_readings)

    def test_garbled_reading(self):
        with self.assertRaises(ValueError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "1399735312 100 10;20 200 20;40 400 40;65 600 60123; 23123 23")
            parser = DataParser()
            readings = parser.parse(text_msg.phone_number, text_msg.message)

    def test_valid_invalid_readings(self):
        with self.assertRaises(ValueError):
            text_msg = TextMsg("+12223334444", "14/05/30,00:13:34-32", "Hello, this is a random text message.")
            parser = DataParser()
            readings = parser.parse(text_msg.phone_number, text_msg.message)


class TestSensorReadingsDataStore(unittest.TestCase):

    def test_valid_readings(self):
        readings = [
            ["+12223334444", 1399735312, 'd', 100, 10],
            ["+12223334444", 1399736512, 'g', 200, 20],
            ["+12223334444", 1399737712, 'd', 400, 40],
            ["+12223334444", 1399739212, 'd', 600, 60],
        ]
        data_logger = SensorReadingsDataStore(':memory:', True)
        data_logger.setup()
        data_logger.store_readings(readings)


    def test_invalid_readings(self):
        readings = [
            ["+12223334444", 1399735312, 'd', 100, 10],
            ["+12223334444", 1399736512, 'd', 200],
            ["+12223334444", 1399737712, 'd', 400, 40],
            ["+12223334444", 1399739212, 'g', 600, 60],
        ]
        with self.assertRaises(sqlite3.ProgrammingError):
            data_logger = SensorReadingsDataStore(':memory:', True)
            data_logger.setup()
            data_logger.store_readings(readings)


if __name__ == '__main__':
    unittest.main()
