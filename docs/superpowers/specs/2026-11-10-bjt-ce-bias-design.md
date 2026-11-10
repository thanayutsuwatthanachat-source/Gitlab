# Lab 02: BJT DC Bias Web App — Design

Course: ENG29 2121 — Computer Programming for Electrical Engineers
Date: 2026-11-10
Status: awaiting approval

## Intent

A small but real Flask application that computes the DC operating point of an NPN
common-emitter amplifier with voltage-divider bias. It must look and behave like the
course reference app (three-column page with a circuit diagram and a region banner),
and it must compute the engineering values in Python, not in the template.

Why: this is the Week 2 lab deliverable. It has to run on localhost in class and be
committed to GitHub the same day.

## Goals

- Inputs: `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE` (with unit selectors for V and Ω).
- Outputs: `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE` with units, plus the operating region.
- Validate every input and show the error next to the offending field.
- Warn clearly for cutoff and saturation.
- Cross-check the displayed result against an independent calculation and show the delta.

## Non-goals

- No AC analysis, no gain, no Bode plot, no transient response.
- No function generator, no oscilloscope, no waveform display.
- No schematic editor, no drag-and-drop, no FET/MOSFET, no PNP.
- No database, login, or persistence. No JavaScript framework.

## Anti-goals

- Results computed in the template or in JavaScript instead of Python.
- Two methods that silently disagree with no explanation.
- A page that only works for the one example from the screenshot.

## Constraints

- Python 3.12 (system `python`), Flask only — no numpy, no pandas.
- Style follows the existing repo: `unittest`, plain dicts.
- The existing suite is red (`test_zero_voltage` expects `analyze_dc(0, 10)` to pass,
  but validation rejects zero). Fix that test to expect `ValueError` in Task 0 so the
  branch starts from a green baseline. `electrical.py` itself is not modified.
- `git.exe` is not on `PATH`; use
  `C:\Users\B6821524\AppData\Local\Programs\Git\cmd\git.exe`.

## Approaches considered

- **A. Approximate analysis as the primary display, exact Thévenin as the cross-check.**
  Matches the reference app's numbers, and the ~16% difference between the two is a
  teachable, explainable quantity (base-current loading). **Chosen.**
- **B. Exact analysis as the primary display.** More accurate, but `VCE` comes out
  ~0.8 V higher than the reference app, so the demo would not match the lab sheet.
- **C. Show both columns with equal weight.** Correct but the grader cannot tell which
  value is "the answer".

Rejected: single-file app (violates the required separation), numpy solver (unneeded
dependency), and any AC/transient feature (out of scope for this lab).

## Engineering model

Topology: NPN, `R1` from `VCC` to base, `R2` from base to ground, `RC` from `VCC` to
collector, `RE` from emitter to ground. `VBE` is given, not solved.

### Primary — approximate (ignores base-current loading)

```
VBB = VCC * R2 / (R1 + R2)
VB  = VBB
VE  = VB - VBE
IE  = VE / RE
IC  = IE
IB  = IC / beta
VC  = VCC - IC * RC
VCE = VC - VE
```

### Cross-check — exact (Thévenin base loop)

```
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VBE + VE
VC  = VCC - IC * RC
VCE = VC - VE
```

### Independent verification — nodal analysis

Solved with Gaussian elimination in pure Python (no numpy). Unknowns `VE, IB, VC`,
with `VB = VE + VBE`:

```
[ 1/R1 + 1/R2      1          0    ] [VE]   [ (VCC - VBE)/R1 - VBE/R2 ]
[ 1/RE          -(1+beta)     0    ] [IB] = [            0             ]
[ 0               beta       1/RC  ] [VC]   [          VCC/RC          ]
```

`IC = beta*IB`, `IE = (1+beta)*IB`. This route shares no algebra with the closed-form
solution, so a test asserts the two agree to 1e-9. The approximate result is then
compared against the exact result and the percentage difference is displayed.

### Region rules (evaluated on the primary result)

| Condition | Region | Reported values |
|---|---|---|
| `VBB <= VBE` | cutoff | `IC = IE = 0`, `VE = 0`, `VC = VCC`, `VCE = VCC` |
| `VCE <= 0.2 V` | saturation | `VCE = 0.2`, `IC = (VCC - 0.2)/(RC + RE)`, then `IB = IC/beta`, `IE = IC + IB`, `VE = IE*RE`, `VC = VCE + VE` |
| otherwise | active | primary values as computed |

`VCE_SAT = 0.2 V` is a named constant.

## Validation rules

All fields required, numeric and finite.

| Field | Rule |
|---|---|
| `VCC` | `> 0` |
| `R1`, `R2`, `RC`, `RE` | `> 0` (RE = 0 needs a separate branch — out of scope) |
| `beta` | `>= 1` |
| `VBE` | `0 < VBE < VCC` |

Invalid input returns HTTP 400 with the submitted values preserved and an inline message
per field. No traceback ever reaches the browser.

Units are converted server-side to base units (V, Ω) before any calculation:
voltage `V`, `mV`; resistance `Ω`, `kΩ`, `MΩ`.

## Page layout (matches the reference screenshot)

```
┌ header: chip icon │ Lab 02: BJT DC Bias Web App            │ badge ┐
│                    │ ENG29 2121 - Common Emitter (VD Bias)         │
├───────────────────┬──────────────────────────┬─────────────────────┤
│ Input Parameters  │ Circuit: CE Amplifier    │ DC Bias Results     │
│  VCC [12.0][V]    │   (inline SVG schematic) │  VB    2.16 V       │
│  R1 [100][kΩ]     │   labels bound to inputs │  VE    1.46 V       │
│  R2 [22][kΩ]      │                          │  VC    8.78 V       │
│  RC [2.2][kΩ]     │                          │  VCE   7.32 V       │
│  RE [1.0][kΩ]     │                          │  IB   14.6 µA       │
│  β  [100][–]      │                          │  IC    1.46 mA      │
│  VBE[0.70][V]     │                          │  IE    1.48 mA      │
│  [ Calculate ]    │                          │ ┌ green banner ───┐ │
│                   │                          │ │ Active region OK│ │
│                   │                          │ └─────────────────┘ │
│                   │                          │ cross-check (exact) │
├───────────────────┴──────────────────────────┴─────────────────────┤
│ Week 2 Goal: ...                                                   │
└────────────────────────────────────────────────────────────────────┘
```

- Single page: the form and the results live in the same template, so the values stay
  visible after submitting.
- Banner colours: green = active, amber = cutoff, red = saturation.
- Cross-check line inside the results card (small type): exact `IC`/`VCE` and the
  percentage difference. This is the only addition beyond the screenshot, and it exists
  because the lab requires comparison with an independent calculation.

## File layout

```
bjt/__init__.py
bjt/units.py          unit conversion
bjt/validation.py     parse + validate the form
bjt/bias.py           approximate, exact, nodal, region, warnings
web/__init__.py
web/app.py            Flask routes only
web/templates/base.html
web/templates/index.html
web/templates/_circuit.html   inline SVG partial, so the labels bind to the inputs
web/static/style.css
tests/test_units.py
tests/test_validation.py
tests/test_bias.py
tests/test_routes.py
run.py                python run.py -> 127.0.0.1:5000
requirements.txt
README.md
```

## Acceptance criteria

1. `GET /` returns 200 and shows 7 inputs, 7 unit selectors, the SVG circuit and an
   empty results card.
2. Posting `12, 100k, 22k, 2.2k, 1k, 100, 0.70` returns 200 with
   `VB 2.16`, `VE 1.46`, `VC 8.78`, `VCE 7.32`, `IB 14.6 µA`, `IC 1.46 mA`, `IE 1.48 mA`
   (each within ±0.05 of the displayed precision).
3. Region banner is green and reads "Active region approximation OK" with the `VCE` value.
4. `VBB <= VBE` (e.g. `R1=100k, R2=5k`) gives the amber cutoff banner and `IC = 0`.
5. `RC=10k, RE=100, beta=300` gives the red saturation banner and `VCE = 0.20 V`.
6. Non-numeric or out-of-range input returns 400, keeps the submitted values and shows
   one inline error per bad field; no traceback in the response.
7. Exact closed-form and nodal results agree to `1e-9` for every case in the test suite.
8. `python -m unittest discover -v` is fully green.
9. `python run.py` serves the page on `http://127.0.0.1:5000` with no debug traceback.
10. One commit on `main` pushed to `origin`.

## Left to the builder

- Exact wording of the warning sentences and the Week 2 Goal strip.
- Spacing, type sizes and colour values in the CSS.
- SVG path details (must remain readable at 360 px wide).
- Number formatting helper (engineering prefixes: µ, m, k).

## Decisions I made (check these)

- `RE > 0` only; `RE = 0` is out of scope.
- `VCE_SAT = 0.2 V`.
- Units offered: V/mV and Ω/kΩ/MΩ.
- Approximate is the headline result, exact is the cross-check (Approach A).
- The existing failing test is fixed to expect `ValueError`, not a behaviour change.
