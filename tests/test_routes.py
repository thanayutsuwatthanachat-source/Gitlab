import unittest

from web.app import app

VALID = {
    "vcc": "12", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1", "re_unit": "kΩ",
    "beta": "100",
    "vbe": "0.7", "vbe_unit": "V",
}


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_shows_form_and_circuit(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Input Parameters".encode(), r.data)
        self.assertIn(b"<svg", r.data)

    def test_valid_post_shows_results_and_banner(self):
        r = self.client.post("/solve", data=VALID)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Active region", r.data)
        self.assertIn(b"7.32 V", r.data)

    def test_cutoff_post_shows_amber_banner(self):
        r = self.client.post("/solve", data=dict(VALID, r2="5"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Cutoff", r.data)

    def test_saturation_post_shows_red_banner(self):
        r = self.client.post("/solve", data=dict(VALID, rc="10", re="0.1",
                                                 beta="300"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Saturation", r.data)

    def test_invalid_post_keeps_values_and_shows_error(self):
        r = self.client.post("/solve", data=dict(VALID, vcc="abc"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("ต้องเป็นตัวเลข".encode(), r.data)
        self.assertIn(b'value="abc"', r.data)

    def test_cutoff_hides_unphysical_crosscheck(self):
        r = self.client.post("/solve", data=dict(VALID, r2="5"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"not meaningful", r.data)
        self.assertNotIn(b"-122", r.data)

    def test_saturation_hides_unphysical_crosscheck(self):
        r = self.client.post("/solve", data=dict(VALID, rc="10", re="0.1",
                                                 beta="300"))
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(b"-80.2", r.data)

    def test_no_traceback_on_invalid_input(self):
        r = self.client.post("/solve", data=dict(VALID, re="0"))
        self.assertEqual(r.status_code, 400)
        self.assertNotIn(b"Traceback", r.data)


if __name__ == "__main__":
    unittest.main()
