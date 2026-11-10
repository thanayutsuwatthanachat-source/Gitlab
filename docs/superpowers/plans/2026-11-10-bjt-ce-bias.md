# BJT CE DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A one-page Flask app that computes the DC operating point of an NPN common-emitter voltage-divider bias circuit and shows the result, region banner and cross-check exactly like the course reference app.

**Architecture:** Three layers with no leakage: `bjt/` holds pure engineering functions (units, validation, solvers) that never import Flask; `web/app.py` holds routes only and calls `bjt`; `web/templates/` + `web/static/` hold presentation only and never compute. Tests drive every layer from the bottom up.

**Tech Stack:** Python 3.12, Flask, Jinja2, plain CSS, inline SVG, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Flask is the only third-party dependency. No numpy, pandas, pytest, or JavaScript framework.
- Use `unittest` and plain dicts, matching the existing `test_electrical.py` style.
- Base units everywhere inside Python: volts and ohms. Conversion happens once, in `bjt/units.py`.
- `VCE_SAT = 0.2` V, defined once in `bjt/bias.py`.
- Primary display is the approximate analysis; exact Thévenin is the cross-check.
- No AC, transient, Bode, function generator, schematic editor, or FET.
- `git.exe` is not on `PATH`. Use `C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe`.
- Run Python from the venv: `.\.venv\Scripts\python.exe`.
- Work on `main` (single-developer lab repo), commit after every task, push at the end.

## Review Focus

1. **`VBE >= VCC`** — a student typing `VBE = 12` with `VCC = 12` must get an inline validation error, not a division by zero or a negative current.
2. **Non-finite input** (`nan`, `inf`, `1e999`) — must be rejected with the same "must be a finite number" message, not crash Jinja formatting.
3. **`VBB <= VBE`** — must land in cutoff with `IC = 0` and `VCE = VCC`; must never display a negative current.
4. **Very small `RE`** (e.g. `100 Ω`) — must trip the saturation branch and clamp `VCE` to `0.2 V` instead of reporting a negative `VCE`.
5. **Blank field** — must produce one inline error for that field while keeping the other entered values on screen.

Each of these has a test in the task that owns the code.

---

### Task 1: Environment, green baseline, units module

**Files:**
- Create: `.gitignore`, `requirements.txt`, `bjt/__init__.py`, `bjt/units.py`
- Modify: `test_electrical.py:12-15`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `bjt.units.VOLTAGE_UNITS: dict[str, float]` = `{"V": 1.0, "mV": 1e-3}`
  - `bjt.units.RESISTANCE_UNITS: dict[str, float]` = `{"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}`
  - `bjt.units.to_volts(value: float, unit: str) -> float`
  - `bjt.units.to_ohms(value: float, unit: str) -> float`
  - `bjt.units.format_engineering(value: float, unit: str) -> str` — 3 significant figures with an SI prefix (`7.32 V`, `1.46 mA`, `14.6 µA`)

- [ ] **Step 1: Create the venv and install Flask**

Run:
```powershell
cd C:\Users\B6821524\Desktop\Gitlab
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install flask
```
Expected: `Successfully installed Flask-...`

- [ ] **Step 2: Add `.gitignore` and `requirements.txt`**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
```

`requirements.txt`:
```
Flask>=3.0
```

- [ ] **Step 3: Fix the existing red test**

Replace the body of `test_zero_voltage` in `test_electrical.py` so it asserts rejection:
```python
	def test_zero_voltage(self):
		with self.assertRaises(ValueError):
			analyze_dc(0, 10)
```
Do not change `electrical.py`.

- [ ] **Step 4: Verify the baseline is green**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 2 tests ... OK`

- [ ] **Step 5: Write the failing unit tests**

`tests/test_units.py`:
```python
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
```

- [ ] **Step 6: Run it to watch it fail**

Run: `.\.venv\Scripts\python -m unittest tests.test_units -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt'`

- [ ] **Step 7: Implement `bjt/units.py`**

Create `bjt/__init__.py` (empty) and `bjt/units.py` with the two unit dicts, the two converters (raise `KeyError` on an unknown unit), and `format_engineering`. `format_engineering` picks the prefix from `[(1e9,"G"),(1e6,"M"),(1e3,"k"),(1,""),(1e-3,"m"),(1e-6,"µ"),(1e-9,"n")]`, formats with `f"{value/scale:.3g}"`, and returns `f"{number} {prefix}{unit}"`; zero returns `"0 A"`-style output with no prefix.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 5 tests ... OK`

- [ ] **Step 9: Commit**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add .gitignore requirements.txt bjt tests test_electrical.py
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: project setup, green baseline and unit conversion"
```

---

### Task 2: Input validation

**Files:**
- Create: `bjt/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: `bjt.units.to_volts`, `bjt.units.to_ohms`.
- Produces:
  - `bjt.validation.FIELDS: tuple[str, ...]` = `("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
  - `bjt.validation.UNIT_NAMES: dict[str, str]` mapping each field to its unit-select name (`"vcc" -> "vcc_unit"`, …, `"beta" -> ""`)
  - `bjt.validation.parse(form: Mapping[str, str]) -> tuple[dict[str, float] | None, dict[str, str]]` — values in base units, errors keyed by field name. Never raises.

- [ ] **Step 1: Write the failing tests**

`tests/test_validation.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.\.venv\Scripts\python -m unittest tests.test_validation -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt.validation'`

- [ ] **Step 3: Implement `bjt/validation.py`**

`parse` reads each field, converts with `float()`, rejects non-finite values via `math.isfinite`, converts units, then applies the rules from the spec: `VCC > 0`, `R1/R2/RC/RE > 0`, `beta >= 1`, `0 < VBE < VCC`. Unit conversion must happen before the `VBE < VCC` check. Return `(None, errors)` if any error exists.

- [ ] **Step 4: Run to verify it passes**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 14 tests ... OK`

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add bjt/validation.py tests/test_validation.py
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: validate and unit-convert bias inputs"
```

---

### Task 3: Approximate solver, region and warning

**Files:**
- Create: `bjt/bias.py`
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: nothing (pure arithmetic, base units).
- Produces:
  - `bjt.bias.VCE_SAT: float` = `0.2`
  - `bjt.bias.approximate(vcc, r1, r2, rc, re, beta, vbe) -> dict[str, float]` with keys `ib, ic, ie, vb, vc, ve, vce`
  - `bjt.bias.apply_region(vcc, r1, r2, rc, re, beta, vbe, values: dict) -> tuple[dict, str]` — returns the reported values and `"active" | "cutoff" | "saturation"`
  - `bjt.bias.warning_for(region: str, vcc, vbe, vce) -> dict[str, str]` with keys `level` (`"ok" | "warn" | "bad"`), `title`, `detail`

- [ ] **Step 1: Write the failing tests**

`tests/test_bias.py`:
```python
import unittest

from bjt.bias import VCE_SAT, apply_region, approximate, warning_for

BASE = dict(vcc=12, r1=100000, r2=22000, rc=2200, re=1000, beta=100, vbe=0.7)


class TestApproximate(unittest.TestCase):
    def test_reference_example(self):
        r = approximate(**BASE)
        self.assertAlmostEqual(r["vb"], 2.1639, places=3)
        self.assertAlmostEqual(r["ve"], 1.4639, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.4639, places=3)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.4639, places=3)
        self.assertAlmostEqual(r["ib"] * 1e6, 14.639, places=2)
        self.assertAlmostEqual(r["vc"], 8.7793, places=3)
        self.assertAlmostEqual(r["vce"], 7.3154, places=3)


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
        self.assertAlmostEqual(values["ic"], (12 - VCE_SAT) / (10000 + 100), places=9)


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.\.venv\Scripts\python -m unittest tests.test_bias -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt.bias'`

- [ ] **Step 3: Implement the approximate solver and region logic**

Implement `approximate` exactly as in the spec's "Primary" block. `apply_region` evaluates cutoff first (`VBB <= VBE`), then saturation (`VCE <= VCE_SAT`), otherwise active; in cutoff set `ic = ie = ib = ve = 0`, `vc = vce = vcc`; in saturation set `vce = VCE_SAT`, `ic = (vcc - VCE_SAT) / (rc + re)`, `ib = ic / beta`, `ie = ic + ib`, `ve = ie * re`, `vc = vce + ve`. `warning_for` returns the three copy strings; the active detail must contain the actual `VCE` value.

- [ ] **Step 4: Run to verify it passes**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 23 tests ... OK`

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add bjt/bias.py tests/test_bias.py
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: approximate DC bias solver with region warnings"
```

---

### Task 4: Exact cross-check and independent nodal verification

**Files:**
- Modify: `bjt/bias.py`
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: `approximate`, `apply_region`, `warning_for`, `VCE_SAT`.
- Produces:
  - `bjt.bias.exact(vcc, r1, r2, rc, re, beta, vbe) -> dict[str, float]` (same keys as `approximate`)
  - `bjt.bias.nodal(vcc, r1, r2, rc, re, beta, vbe) -> dict[str, float]` (same keys as `approximate`)
  - `bjt.bias.solve(vcc, r1, r2, rc, re, beta, vbe) -> dict` with keys `values`, `region`, `warning`, `exact`, `nodal`, `delta` where `delta = {"ic_pct": float, "vce_pct": float}`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bias.py`:
```python
from bjt.bias import exact, nodal, solve


class TestExactAndNodal(unittest.TestCase):
    def test_exact_reference_example(self):
        r = exact(**BASE)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.299, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)

    def test_nodal_matches_exact(self):
        for case in (BASE, dict(BASE, r2=5000), dict(BASE, rc=10000, re=100, beta=300)):
            a, b = exact(**case), nodal(**case)
            for key in ("ib", "ic", "ie", "vb", "vc", "ve"):
                self.assertAlmostEqual(a[key], b[key], places=9, msg=f"{key} {case}")

    def test_solve_reports_delta_between_methods(self):
        out = solve(**BASE)
        self.assertEqual(out["region"], "active")
        self.assertGreater(out["delta"]["ic_pct"], 10.0)
        self.assertLess(out["delta"]["ic_pct"], 25.0)

    def test_solve_is_consistent_with_approximate(self):
        out = solve(**BASE)
        self.assertAlmostEqual(out["values"]["vce"], approximate(**BASE)["vce"], places=9)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.\.venv\Scripts\python -m unittest tests.test_bias -v`
Expected: FAIL with `ImportError: cannot import name 'exact'`

- [ ] **Step 3: Implement `exact`, `nodal` and `solve`**

`exact` follows the spec's "Cross-check" block. `nodal` builds the 3×3 matrix from the spec, solves it with a private `_gauss(matrix, rhs)` Gaussian elimination with partial pivoting, and derives `ic/ie/vb` from `ve/ib/vc`. `solve` runs `approximate`, applies the region, runs `exact` and `nodal` on the raw circuit, and computes `delta` as the absolute percentage difference of `ic` and `vce` between primary and exact (guard against division by zero).

- [ ] **Step 4: Run to verify it passes**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 27 tests ... OK`

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add bjt/bias.py tests/test_bias.py
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: exact and nodal cross-check with method delta"
```

---

### Task 5: Flask page, templates, SVG and CSS

**Files:**
- Create: `web/__init__.py`, `web/app.py`, `web/templates/base.html`, `web/templates/index.html`, `web/templates/_circuit.html`, `web/static/style.css`
- Test: `tests/test_routes.py`

**Interfaces:**
- Consumes: `bjt.validation.parse`, `bjt.bias.solve`, `bjt.units.format_engineering`, `bjt.units.VOLTAGE_UNITS`, `bjt.units.RESISTANCE_UNITS`.
- Produces: `web.app.create_app() -> Flask` and a module-level `app` for `flask --app web.app`. Routes: `GET /` and `POST /solve`.

- [ ] **Step 1: Write the failing route tests**

`tests/test_routes.py`:
```python
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
        r = self.client.post("/solve", data=dict(VALID, rc="10", re="0.1", beta="300"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Saturation", r.data)

    def test_invalid_post_keeps_values_and_shows_error(self):
        r = self.client.post("/solve", data=dict(VALID, vcc="abc"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("ต้องเป็นตัวเลข".encode(), r.data)
        self.assertIn(b'value="abc"', r.data)

    def test_no_traceback_on_invalid_input(self):
        r = self.client.post("/solve", data=dict(VALID, re="0"))
        self.assertEqual(r.status_code, 400)
        self.assertNotIn(b"Traceback", r.data)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.\.venv\Scripts\python -m unittest tests.test_routes -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'web'`

- [ ] **Step 3: Implement `web/app.py`**

`create_app()` builds the Flask app, sets `DEFAULTS` (the reference example, with `*_unit` keys), and registers two routes. `GET /` renders `index.html` with `values=DEFAULTS, errors={}, result=None`. `POST /solve` calls `parse`; on errors renders `index.html` with the raw `request.form` and status 400; otherwise calls `solve(**values)` and renders with `result=...`, converting every displayed number through `format_engineering`.

- [ ] **Step 4: Build the templates**

`base.html`: document shell, header with the chip icon, title "Lab 02: BJT DC Bias Web App", subtitle "ENG29 2121 – Common Emitter (Voltage Divider Bias)", right-hand badge "Computer Programming for Electrical Engineers", the Week 2 Goal strip at the bottom, and `{% block content %}`.

`index.html`: three-column grid. Left card "Input Parameters" with a 7-row loop rendering label, number input (`value="{{ values[name] }}"`), unit `<select>` (voltage units for `vcc`/`vbe`, resistance units for `r1..re`, none for `beta`) and `{{ errors[name] }}`. Middle card "Circuit: Common-Emitter Amplifier" includes `_circuit.html`. Right card "DC Bias Results" shows `VB VE VC VCE IB IC IE`, then the banner (`class="banner {{ result.warning.level }}"`) and the cross-check line.

`_circuit.html`: inline SVG schematic with labelled `R1`, `R2`, `RC`, `RE`, `Q1 NPN`, `VCC`; text nodes bind to `{{ values.* }}` and the unit labels.

`style.css`: light `#eef2f7` page background, white cards with `border-radius: 10px`, teal accent `#0f7b8a`, three-column grid that collapses to one column below 900 px, table rows with a tinted value column, `.banner.ok` green, `.banner.warn` amber, `.banner.bad` red, `.err` red small text.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 33 tests ... OK`

- [ ] **Step 6: Commit**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add web tests/test_routes.py
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: Flask page with circuit diagram and region banner"
```

---

### Task 6: Entry point, README, demo and push

**Files:**
- Create: `run.py`, `README.md`
- Test: manual demo check (no new test file)

**Interfaces:**
- Consumes: `web.app.app`.
- Produces: `python run.py` serving `http://127.0.0.1:5000`.

- [ ] **Step 1: Add `run.py`**

```python
from web.app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
```

- [ ] **Step 2: Write `README.md`**

Course name, the seven inputs with units, the two methods and why they differ, how to install (`python -m venv .venv`, `pip install -r requirements.txt`), how to run (`python run.py`), how to test (`python -m unittest discover -v`), and one worked example with the expected numbers.

- [ ] **Step 3: Run the full suite one last time**

Run: `.\.venv\Scripts\python -m unittest discover -v`
Expected: `Ran 33 tests ... OK`

- [ ] **Step 4: Start the server and check it by hand**

Run: `.\.venv\Scripts\python run.py`
Expected: `Running on http://127.0.0.1:5000`. Open it, submit the reference example, confirm `VB 2.16 V`, `VCE 7.32 V`, green banner. Stop with Ctrl+C.

- [ ] **Step 5: Commit and push**

```powershell
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" add run.py README.md
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" commit -m "docs: run instructions and lab README"
& "C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe" push origin main
```
Expected: push succeeds to `origin/main`.

---

## Self-Review

- **Spec coverage:** inputs/units → Tasks 1–2; approximate + region + warnings → Task 3; exact + nodal + delta → Task 4; layout, SVG, banner, cross-check line → Task 5; run/demo/commit → Task 6. No spec section is unowned.
- **Step scan:** every step names one action and its check; no "TBD" or "add appropriate validation".
- **Type consistency:** all solvers return the same seven keys (`ib ic ie vb vc ve vce`); `solve()` returns `values/region/warning/exact/nodal/delta`, and Task 5 consumes exactly those names.
- **Review Focus:** items 1–5 are covered by `test_vbe_must_be_below_vcc`, `test_non_finite`, `test_cutoff_when_vbb_below_vbe`, `test_saturation_clamps_vce`, `test_blank_field`.
- **Proportion:** 6 tasks, ~33 tests, roughly 250 lines of production code — finishable in one lab session.
