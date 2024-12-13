from django.test import TestCase
from tutorials.models import Frequency
from django.core.exceptions import ValidationError

class FrequencyTestCase(TestCase):
    #Test cases for the Frequency utility class.

    def test_to_string_valid_values(self):
        """Test that valid numeric values are correctly converted to strings."""
        self.assertEqual(Frequency.to_string(0.5), 'Fortnightly')
        self.assertEqual(Frequency.to_string(1.0), 'Weekly')
        self.assertEqual(Frequency.to_string(2.0), 'Biweekly')
        self.assertEqual(Frequency.to_string(4.0), 'Monthly')

    def test_to_string_invalid_value(self):
        """Test that invalid numeric values return 'Unknown'."""
        self.assertEqual(Frequency.to_string(3.0), 'Unknown')
        self.assertEqual(Frequency.to_string(None), 'Unknown')

    def test_to_numeric_valid_labels(self):
        """Test that valid string labels are correctly converted to numeric values."""
        self.assertEqual(Frequency.to_numeric('fortnightly'), 0.5)
        self.assertEqual(Frequency.to_numeric('weekly'), 1.0)
        self.assertEqual(Frequency.to_numeric('biweekly'), 2.0)
        self.assertEqual(Frequency.to_numeric('monthly'), 4.0)

    def test_to_numeric_invalid_label(self):
        """Test that invalid string labels return None."""
        self.assertIsNone(Frequency.to_numeric('yearly'))
        self.assertIsNone(Frequency.to_numeric('unknown'))
        self.assertIsNone(Frequency.to_numeric(''))
        self.assertIsNone(Frequency.to_numeric(None))

    def test_to_numeric_case_insensitivity(self):
        """Test that string labels are case-insensitive."""
        self.assertEqual(Frequency.to_numeric('Fortnightly'), 0.5)
        self.assertEqual(Frequency.to_numeric('WEEKLY'), 1.0)
        self.assertEqual(Frequency.to_numeric('BiWeekly'), 2.0)
        self.assertEqual(Frequency.to_numeric('monthly'), 4.0)