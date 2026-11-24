"""Adapter, route error states, and optional real ngspice regression."""

from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from bjt import spice
from web.app import app, create_app
from web.plots import prepare_plots


class TestSpice(unittest.TestCase):
    def test_hosted_home_and_health(self):
        hosted = create_app()
        hosted.config["LAB04_HOME"] = "simulator"
        client = hosted.test_client()
        self.assertTrue(client.get("/").location.endswith("/simulator"))
        self.assertIn(b"Calculate DC Bias", client.get("/?mode=divider").data)
        for binary, code in (("/usr/bin/ngspice", 200), (None, 503)):
            with patch("bjt.spice.executable", return_value=binary):
                self.assertEqual(client.get("/healthz").status_code, code)

    def test_units_and_mode_specific_validation(self):
        dc, errors = spice.parse_inputs("dc", dict(spice.DEFAULTS, amplitude="bad", cin="0"))
        self.assertFalse(errors)
        self.assertEqual(dc["re"], 1000)
        ac, errors = spice.parse_inputs("ac", dict(spice.DEFAULTS, amplitude="bad"))
        self.assertFalse(errors)
        self.assertAlmostEqual(ac["cin"], 10e-6)
        tran, errors = spice.parse_inputs("tran", spice.DEFAULTS)
        self.assertFalse(errors)
        self.assertEqual(tran["amplitude"], 0.01)

    def test_invalid_numbers_are_rejected(self):
        _, errors = spice.parse_inputs(
            "tran", dict(spice.DEFAULTS, re="0", cin="nan", frequency="inf", amplitude="1\n.end"),
        )
        self.assertEqual(set(errors), {"re", "cin", "frequency", "amplitude"})

    def test_raw_fixture_and_truncation(self):
        path = Path(__file__).resolve().parents[1] / "docs/evidence/baseline-dc.raw"
        text = path.read_text(encoding="ascii")
        rows = spice.parse_raw(text, "dc")
        self.assertAlmostEqual(rows["i(vsense)"][0], 0.00127754)
        for broken in ("", text.rsplit("\n", 2)[0], text.replace("Flags: real", "Flags: complex")):
            with self.assertRaises(spice.SpiceError):
                spice.parse_raw(broken, "dc")

    def test_timeout_maps_to_user_error(self):
        values, _ = spice.parse_inputs("dc", spice.DEFAULTS)
        with patch("bjt.spice.executable", return_value="ngspice"), patch(
            "bjt.spice.subprocess.run", side_effect=subprocess.TimeoutExpired("ngspice", 12),
        ):
            with self.assertRaisesRegex(spice.SpiceError, "12"):
                spice.run_spice("dc", values)

    def test_missing_engine_does_not_show_results(self):
        with patch("bjt.spice.executable", return_value=None):
            res = app.test_client().post("/simulator", data=dict(spice.DEFAULTS, analysis="ac"))
        self.assertEqual(res.status_code, 503)
        self.assertIn(b"Run failed", res.data)
        self.assertNotIn(b"plot-trace", res.data)
        self.assertNotIn(b"Succeeded", res.data)

    def test_invalid_post_does_not_call_engine(self):
        with patch("bjt.spice.run_spice") as runner:
            res = app.test_client().post(
                "/simulator", data=dict(spice.DEFAULTS, analysis="tran", re="0"),
            )
        runner.assert_not_called()
        self.assertEqual(res.status_code, 400)
        self.assertIn(b'aria-invalid="true"', res.data)

    @unittest.skipUnless(spice.executable(), "real ngspice is not configured")
    def test_real_three_analyses_and_changes(self):
        def run(mode, **changes):
            params, errors = spice.parse_inputs(mode, dict(spice.DEFAULTS, **changes))
            self.assertFalse(errors)
            return spice.run_spice(mode, params)[0]

        dc, updated_dc = run("dc"), run("dc", re="2")
        self.assertAlmostEqual(dc["v(c)"][0] - dc["v(e)"][0], 7.90, places=2)
        self.assertLess(updated_dc["i(vsense)"][0], dc["i(vsense)"][0])
        ac = run("ac")
        self.assertEqual(len(ac["frequency"]), 361)
        charts, _ = prepare_plots("ac", ac)
        self.assertEqual(len(charts), 2)
        i = min(range(361), key=lambda point: abs(ac["frequency"][point] - 1000))
        self.assertAlmostEqual((ac["v(out)"][i] / ac["v(vin)"][i]).real, -1.75, places=2)
        tran, updated_tran = run("tran"), run("tran", amplitude="25", frequency="2000")
        self.assertAlmostEqual(tran["time"][-1], 0.012)
        self.assertAlmostEqual(updated_tran["time"][-1], 0.006)
        self.assertLess(abs(max(tran["v(out)"])), abs(max(updated_tran["v(out)"])))
