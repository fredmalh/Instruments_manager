import unittest
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)

class TestDateUtils(unittest.TestCase):
    def setUp(self):
        # Set up test dates
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        self.next_month = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    def test_calculate_next_maintenance(self):
        # Test with valid last maintenance date
        next_date = calculate_next_maintenance(self.last_week, 2)
        expected_date = (datetime.strptime(self.last_week, '%Y-%m-%d') + timedelta(weeks=2)).strftime('%Y-%m-%d')
        self.assertEqual(next_date, expected_date)

        # Test with no last maintenance date
        next_date = calculate_next_maintenance(None, 2, self.today)
        self.assertEqual(next_date, self.today)

        # Test with 'Never' as last maintenance date
        next_date = calculate_next_maintenance('Never', 2, self.today)
        self.assertEqual(next_date, self.today)

        # Test with invalid date
        next_date = calculate_next_maintenance('invalid-date', 2)
        self.assertIsNone(next_date)

    def test_format_date_for_display(self):
        # Test valid date conversion
        display_date = format_date_for_display('2024-03-15')
        self.assertEqual(display_date, '15-03-2024')

        # Test None value
        display_date = format_date_for_display(None)
        self.assertEqual(display_date, 'Never')

        # Test 'Never' value
        display_date = format_date_for_display('Never')
        self.assertEqual(display_date, 'Never')

        # Test invalid date
        display_date = format_date_for_display('invalid-date')
        self.assertEqual(display_date, 'invalid-date')

    def test_format_date_for_db(self):
        # Test valid date conversion
        db_date = format_date_for_db('15-03-2024')
        self.assertEqual(db_date, '2024-03-15')

        # Test None value
        db_date = format_date_for_db(None)
        self.assertIsNone(db_date)

        # Test 'Never' value
        db_date = format_date_for_db('Never')
        self.assertIsNone(db_date)

        # Test invalid date
        db_date = format_date_for_db('invalid-date')
        self.assertIsNone(db_date)

    def test_get_maintenance_status(self):
        # Test overdue maintenance
        status, color = get_maintenance_status(self.last_week)
        self.assertEqual(status, 'overdue')
        self.assertEqual(color, 'red')

        # Test due soon maintenance
        status, color = get_maintenance_status(self.next_week)
        self.assertEqual(status, 'due_soon')
        self.assertEqual(color, 'yellow')

        # Test on schedule maintenance
        status, color = get_maintenance_status(self.next_month)
        self.assertEqual(status, 'on_schedule')
        self.assertEqual(color, 'green')

        # Test None value
        status, color = get_maintenance_status(None)
        self.assertEqual(status, 'on_schedule')
        self.assertIsNone(color)

        # Test invalid date
        status, color = get_maintenance_status('invalid-date')
        self.assertEqual(status, 'on_schedule')
        self.assertIsNone(color)

if __name__ == '__main__':
    unittest.main() 