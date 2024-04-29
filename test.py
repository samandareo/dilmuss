import unittest
from freezegun import freeze_time
from with_flask_api import app  # make sure to import your Flask app correctly

class TestTimeIntervals(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @freeze_time("2024-04-26 08:59:00")
    def test_just_before_nine(self):
        response = self.app.get('/')
        # Check if time rounds to 9 AM
        self.assertIn("09:00", response.data.decode())

    @freeze_time("2024-04-26 10:59:00")
    def test_just_before_eleven(self):
        response = self.app.get('/')
        # Check if time rounds to 11 AM
        self.assertIn("11:00", response.data.decode())


if __name__ == '__main__':
    unittest.main()
