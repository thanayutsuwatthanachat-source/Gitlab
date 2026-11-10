import unittest

from bjt.units import format_engineering, to_ohms, to_volts


class TestUnits(unittest.TestCase):
    def test_to_volts(self):
        self.assertAlmostEqual(to_volts(12, "V"), 12.0)
        self.assertAlmostEqual(to_volts(12000, "mV"), 12.0)

    def test_to_ohms(self):
        self.assertAlmostEqual(to_ohms(100, "kΩ"), 100000.0)
        self.assertAlmostEqual(to_ohms(2.2, "MΩ"), 2.2e6)

    def test_format_engineering(self):
        self.assertEqual(format_engineering(7.3154, "V"), "7.32 V")
        self.assertEqual(format_engineering(1.4639e-3, "A"), "1.46 mA")
        self.assertEqual(format_engineering(1.4639e-5, "A"), "14.6 µA")
        self.assertEqual(format_engineering(0.0, "A"), "0 A")


if __name__ == "__main__":
    unittest.main()
