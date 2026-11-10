# Gitlab

## โปรแกรมคำนวณวงจรไฟฟ้ากระแสตรง (`electrical.py`)

คำอธิบาย: โปรแกรมคำนวณวงจรไฟฟ้ากระแสตรงที่ออกแบบมาเพื่อวิเคราะห์หาค่ากระแสไฟฟ้า แรงดันไฟฟ้า และกำลังไฟฟ้าในวงจรตัวต้านทาน ช่วยให้ผู้ใช้งานคำนวณวงจรแบบอนุกรม ขนาน และผสมได้อย่างรวดเร็วและแม่นยำ พร้อมแสดงผลการคำนวณในแต่ละจุดของวงจรเพื่อใช้ในการศึกษาหรือออกแบบ

รันด้วย `python electrical.py` และทดสอบด้วย `python -m unittest -v`.

---

## Lab 02 — BJT DC Bias Web App

ENG29 2121 — Computer Programming for Electrical Engineers
Common-emitter amplifier, voltage-divider bias (NPN), DC analysis only.

A small Flask application: Python computes the DC operating point, the templates
only display it.

## What it does

Inputs: `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE`, each with a unit selector
(V/mV for voltages, Ω/kΩ/MΩ for resistances).

Outputs: `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE` with engineering prefixes,
the operating region, and a warning banner for cutoff or saturation.

The displayed result uses the **approximate analysis** (the textbook shortcut that
ignores base-current loading), and the page shows a **cross-check** computed with
the **exact Thévenin analysis**, plus the percentage difference. The exact route is
itself verified in the test suite against an independent nodal solve.

## Layout

```
bjt/units.py        unit conversion and engineering formatting
bjt/validation.py   form parsing and validation
bjt/bias.py         approximate, exact, nodal solvers, region rules
web/app.py          Flask routes only
web/templates/      base.html, index.html, _circuit.html (inline SVG)
web/static/         style.css
tests/              unit tests for every layer
run.py              local server entry point
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python run.py
```

Open http://127.0.0.1:5000 and press **Calculate DC Bias**.

## Test

```powershell
.\.venv\Scripts\python -m unittest discover -v
```

## Engineering model

Topology: `R1` from `VCC` to base, `R2` from base to ground, `RC` from `VCC` to
collector, `RE` from emitter to ground. `VBE` is an input, not solved.

Approximate (primary display):

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

Exact (cross-check):

```
RB  = R1 || R2
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VBE + VE
VC  = VCC - IC * RC
VCE = VC - VE
```

Region rules: cutoff when `VBB <= VBE` (`IC = 0`, `VCE = VCC`); saturation when
`VCE <= 0.2 V` (reported `VCE` is clamped to `0.2 V`); otherwise active.

## Worked example

`VCC = 12 V`, `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RC = 2.2 kΩ`, `RE = 1 kΩ`,
`beta = 100`, `VBE = 0.70 V`:

| | approximate (shown) | exact (cross-check) |
|---|---|---|
| VB | 2.16 V | 1.94 V |
| VE | 1.46 V | 1.24 V |
| VC | 8.78 V | 9.29 V |
| VCE | 7.32 V | 8.05 V |
| IB | 14.6 µA | 12.3 µA |
| IC | 1.46 mA | 1.23 mA |

The ~19% difference is the base-current loading that the approximate method
ignores. The course reference app rounds its values (for example `2.20 V` for
`2.164 V`), so its numbers are close but not identical.
