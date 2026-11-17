# Gitlab

## โปรแกรมคำนวณวงจรไฟฟ้ากระแสตรง (`electrical.py`)

คำอธิบาย: โปรแกรมคำนวณวงจรไฟฟ้ากระแสตรงที่ออกแบบมาเพื่อวิเคราะห์หาค่ากระแสไฟฟ้า แรงดันไฟฟ้า และกำลังไฟฟ้าในวงจรตัวต้านทาน ช่วยให้ผู้ใช้งานคำนวณวงจรแบบอนุกรม ขนาน และผสมได้อย่างรวดเร็วและแม่นยำ พร้อมแสดงผลการคำนวณในแต่ละจุดของวงจรเพื่อใช้ในการศึกษาหรือออกแบบ

รันด้วย `python electrical.py` และทดสอบด้วย `python -m unittest -v`.

---

## Lab 02–03 — BJT DC Bias Web App

ENG29 2121 — Computer Programming for Electrical Engineers
Common-emitter amplifier, NPN, DC operating point only.

A small Flask application: Python computes the DC bias, the templates only
display it. Lab 02 handled voltage-divider bias only. **Lab 03 adds fixed bias
and single-supply emitter bias**, selected from the same form.

### Modes

| Mode | Inputs used | Resistor placement |
| --- | --- | --- |
| Voltage Divider Bias | `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE` | `R1` VCC→base, `R2` base→ground, `RE` emitter→ground |
| Fixed Bias | `VCC`, `RB`, `RC`, `beta`, `VBE` | `RB` VCC→base, emitter grounded |
| Emitter Bias | `VCC`, `RB`, `RC`, `RE`, `beta`, `VBE` | `RB` VCC→base, `RE` emitter→ground |

Only the fields of the selected mode are rendered, parsed and validated.
An unknown `mode` is rejected instead of falling back to the divider.

### Engineering model (Lab 03)

All resistances are converted to ohms once, in `bjt/validation.py`; results are
stored in base units (V, A) and formatted for display in `bjt/units.py`.

```
Fixed   : I_B = (VCC - VBE) / RB
Emitter : I_B = (VCC - VBE) / (RB + (1 + beta) * RE)
Divider : I_B = (VBB - VBE) / (RB || ... ) -> see bjt/bias.py exact()
```

Common tail for every mode:

```
IC = beta * IB        IE = (1 + beta) * IB
VE = IE * RE          VB = VBE + VE
VC = VCC - IC * RC    VCE = VC - VE
```

### Lab 02 behaviour is preserved

The divider still shows the **approximate** analysis as the primary result and
the exact Thévenin solve as a cross-check, exactly as in Lab 02. For
`VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, beta = 100,
VBE = 0.70 V` it reports `IC = 1.46 mA`, `VCE = 7.32 V` with cross-check
`IC = 1.23 mA`, `VCE = 8.05 V`. Fixed and emitter bias use the worksheet
equations directly, so no cross-check is shown for them.

### Layout

```
bjt/units.py        unit conversion and engineering formatting
bjt/validation.py   mode-aware form parsing and validation
bjt/bias.py         divider (approximate/exact/nodal) + fixed + emitter, solve_mode()
web/app.py          Flask routes and the mode selector data
web/templates/      base.html, index.html, _circuit.html (inline SVG)
web/static/         style.css
tests/              unit tests for every layer (35 tests, Lab 02 suite unchanged)
run.py              local server entry point
```

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### Run

```powershell
.\.venv\Scripts\python run.py
```

Open http://127.0.0.1:5000 and press **Calculate DC Bias**.
Choose the circuit with the **Circuit Mode** card; the form reloads with only
that circuit's fields (no JavaScript needed).

### Test

```powershell
.\.venv\Scripts\python -m unittest discover -v
```

### Reference values (VCC = 12 V, RC = 2.2 kΩ, beta = 100, VBE = 0.70 V)

| Case | Mode and inputs | Expected |
| --- | --- | --- |
| A1 | Divider, R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | 1.46 mA / 7.32 V (approx, unchanged) · cross-check 1.23 mA / 8.05 V |
| A2 | Fixed, RB = 1 MΩ | 1.13 mA / 9.51 V |
| A3 | Emitter, RB = 1 MΩ, RE = 1 kΩ | 1.03 mA / 8.71 V |
| A4 | Emitter, RB = 1 MΩ, RE = 2 kΩ | 0.94 mA / 8.03 V |
| A5 | Fixed, RB = 0 | form shows `ต้องมากกว่า 0`, page does not crash |

Display uses 3 significant figures (`bjt/units.py`). Hand-calculated values
before rounding are in `docs/validation.md`.

### What the AI helped with

- Drafted `fixed()`, `emitter()` and `solve_mode()` in `bjt/bias.py` from the
  worksheet equations (student checks the formulas and units).
- Drafted the mode-aware parsing in `bjt/validation.py` and the dispatch in
  `web/app.py`.
- Drafted the mode selector and conditional fields in the templates.
- The Lab 02 test suite was kept and still passes.
