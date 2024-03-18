import logging
import unittest
import datetime
from pathlib import Path

from freezegun import freeze_time

from LengthNestProMQ.src.day_based_rot_file_handler import DayBasedRotatingFileHandler


class TestLogger(unittest.TestCase):
    @freeze_time("2024-01-01")
    def test_filename_changes_with_date(self):
        # Create logger
        logger = logging.getLogger("DayBasedLogger")
        logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Create handler
        handler = DayBasedRotatingFileHandler(filename='../../logs_test/log_{date}.log', backup_count=3)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        expected_filename = '../../logs_test/log_2024-01-01.log'
        self.assertEqual(handler.filename, expected_filename)
        self.assertTrue(True)

    @freeze_time("2024-01-01")
    def test_log_rotator_rotates(self):
        # Create logger
        logger = logging.getLogger("DayBasedLogger")
        logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Create handler
        handler = DayBasedRotatingFileHandler(filename='../../logs_test/log_{date}.log', backup_count=3)

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        for i in range(2, 5):
            new_datetime = datetime.datetime(year=2024, month=1, day=i,
                                             hour=0, minute=0, second=0)

            with freeze_time(new_datetime) as frozen_datetime:
                logger.info('hi for day: ' + str(new_datetime))

        file_path = Path('../../logs_test/log_2024-01-01.log')
        self.assertFalse(file_path.exists(), "File should have been removed by log rotator")
        file_path = Path('../../logs_test/log_2024-01-02.log')
        self.assertTrue(file_path.exists(), "File does not exist")
        file_path = Path('../../logs_test/log_2024-01-03.log')
        self.assertTrue(file_path.exists(), "File does not exist")
        file_path = Path('../../logs_test/log_2024-01-04.log')
        self.assertTrue(file_path.exists(), "File does not exist")


if __name__ == '__main__':
    unittest.main()
