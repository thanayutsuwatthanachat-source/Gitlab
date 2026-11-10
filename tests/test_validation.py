import unittest

from bjt.validation import parse


def form(**overrides):
    base = {
        "vcc": "12", "vcc_unit": "V",
        "r1": "100", "r1_unit": "kΩ",
        "r2": "22", "r2_unit": "kΩ",
        "rc": "2.2", "rc_unit": "kΩ",
        "re": "1", "re_unit": "kΩ",
        "beta": "100",
        "vbe": "0.7", "vbe_unit": "V",
    }
    base.update(overrides)
    return base


class TestValidation(unittest.TestCase):
    def test_valid_converts_to_base_units(self):
        values, errors = parse(form())
        self.assertEqual(errors, {})
        self.assertAlmostEqual(values["r1"], 100000.0)
        self.assertAlmostEqual(values["vcc"], 12.0)

    def test_non_numeric(self):
        _, errors = parse(form(vcc="abc"))
        self.assertIn("vcc", errors)

    def test_blank_field(self):
        _, errors = parse(form(rc=""))
        self.assertIn("rc", errors)

    def test_non_finite(self):
        for bad in ("nan", "inf", "1e999"):
            _, errors = parse(form(r2=bad))
            self.assertIn("r2", errors, bad)

    def test_zero_or_negative_resistance(self):
        for bad in ("0", "-5"):
            _, errors = parse(form(re=bad))
            self.assertIn("re", errors, bad)

    def test_beta_below_one(self):
        _, errors = parse(form(beta="0.5"))
        self.assertIn("beta", errors)

    def test_vbe_must_be_below_vcc(self):
        _, errors = parse(form(vbe="12"))
        self.assertIn("vbe", errors)

    def test_vbe_must_be_positive(self):
        _, errors = parse(form(vbe="0"))
        self.assertIn("vbe", errors)

    def test_vbe_compared_after_unit_conversion(self):
        _, errors = parse(form(vcc="12000", vcc_unit="mV", vbe="12"))
        self.assertIn("vbe", errors)


if __name__ == "__main__":
    unittest.main()
