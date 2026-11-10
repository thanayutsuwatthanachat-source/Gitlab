import unittest

from bjt.bias import (VCE_SAT, apply_region, approximate, exact, nodal, solve,
                      warning_for)

BASE = dict(vcc=12, r1=100000, r2=22000, rc=2200, re=1000, beta=100, vbe=0.7)


class TestApproximate(unittest.TestCase):
    def test_reference_example(self):
        r = approximate(**BASE)
        self.assertAlmostEqual(r["vb"], 2.1639, places=3)
        self.assertAlmostEqual(r["ve"], 1.4639, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.4785, places=3)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.4639, places=3)
        self.assertAlmostEqual(r["ib"] * 1e6, 14.639, places=2)
        self.assertAlmostEqual(r["vc"], 8.7793, places=3)
        self.assertAlmostEqual(r["vce"], 7.3154, places=3)

    def test_ie_equals_ic_plus_ib(self):
        r = approximate(**BASE)
        self.assertAlmostEqual(r["ie"], r["ic"] + r["ib"], places=12)


class TestRegion(unittest.TestCase):
    def test_active(self):
        values, region = apply_region(**BASE, values=approximate(**BASE))
        self.assertEqual(region, "active")
        self.assertAlmostEqual(values["vce"], 7.3154, places=3)

    def test_cutoff_when_vbb_below_vbe(self):
        case = dict(BASE, r2=5000)
        values, region = apply_region(**case, values=approximate(**case))
        self.assertEqual(region, "cutoff")
        self.assertEqual(values["ic"], 0.0)
        self.assertEqual(values["ie"], 0.0)
        self.assertAlmostEqual(values["vce"], 12.0)

    def test_saturation_clamps_vce(self):
        case = dict(BASE, rc=10000, re=100, beta=300)
        values, region = apply_region(**case, values=approximate(**case))
        self.assertEqual(region, "saturation")
        self.assertAlmostEqual(values["vce"], VCE_SAT)
        self.assertAlmostEqual(values["ic"], (12 - VCE_SAT) / (10000 + 100),
                               places=9)


class TestWarning(unittest.TestCase):
    def test_active_message(self):
        w = warning_for("active", 12, 0.7, 7.3154)
        self.assertEqual(w["level"], "ok")
        self.assertIn("Active region", w["title"])

    def test_cutoff_message(self):
        w = warning_for("cutoff", 12, 0.7, 12.0)
        self.assertEqual(w["level"], "warn")
        self.assertIn("Cutoff", w["title"])

    def test_saturation_message(self):
        w = warning_for("saturation", 12, 0.7, 0.2)
        self.assertEqual(w["level"], "bad")
        self.assertIn("Saturation", w["title"])


class TestExactAndNodal(unittest.TestCase):
    def test_exact_reference_example(self):
        r = exact(**BASE)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.299, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)

    def test_nodal_matches_exact(self):
        for case in (BASE, dict(BASE, r2=5000),
                     dict(BASE, rc=10000, re=100, beta=300)):
            a, b = exact(**case), nodal(**case)
            for key in ("ib", "ic", "ie", "vb", "vc", "ve"):
                self.assertAlmostEqual(a[key], b[key], places=9,
                                       msg=f"{key} {case}")

    def test_solve_reports_delta_between_methods(self):
        out = solve(**BASE)
        self.assertEqual(out["region"], "active")
        self.assertGreater(out["delta"]["ic_pct"], 10.0)
        self.assertLess(out["delta"]["ic_pct"], 25.0)

    def test_solve_is_consistent_with_approximate(self):
        out = solve(**BASE)
        self.assertAlmostEqual(out["values"]["vce"],
                               approximate(**BASE)["vce"], places=9)


if __name__ == "__main__":
    unittest.main()
