"""Flask routes only. Engineering lives in bjt/, presentation in templates/."""

from flask import Flask, render_template, request

from bjt.bias import solve
from bjt.units import RESISTANCE_UNITS, VOLTAGE_UNITS, format_engineering
from bjt.validation import parse

DEFAULTS = {
    "vcc": "12.0", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1.0", "re_unit": "kΩ",
    "beta": "100",
    "vbe": "0.70", "vbe_unit": "V",
}

FIELDS = (
    {"name": "vcc", "symbol": "V", "sub": "CC", "hint": "Supply Voltage",
     "units": tuple(VOLTAGE_UNITS)},
    {"name": "r1", "symbol": "R", "sub": "1", "hint": "Upper Divider",
     "units": tuple(RESISTANCE_UNITS)},
    {"name": "r2", "symbol": "R", "sub": "2", "hint": "Lower Divider",
     "units": tuple(RESISTANCE_UNITS)},
    {"name": "rc", "symbol": "R", "sub": "C", "hint": "Collector Resistor",
     "units": tuple(RESISTANCE_UNITS)},
    {"name": "re", "symbol": "R", "sub": "E", "hint": "Emitter Resistor",
     "units": tuple(RESISTANCE_UNITS)},
    {"name": "beta", "symbol": "β", "sub": "", "hint": "Current Gain",
     "units": ()},
    {"name": "vbe", "symbol": "V", "sub": "BE", "hint": "Base-Emitter Voltage",
     "units": tuple(VOLTAGE_UNITS)},
)

RESULT_ROWS = (
    ("V", "B", "vb"),
    ("V", "E", "ve"),
    ("V", "C", "vc"),
    ("V", "CE", "vce"),
    ("I", "B", "ib"),
    ("I", "C", "ic"),
    ("I", "E", "ie"),
)

CURRENT_KEYS = ("ib", "ic", "ie")


def _display(values):
    return {
        key: format_engineering(values[key], "A" if key in CURRENT_KEYS else "V")
        for _, _, key in RESULT_ROWS
    }


def _render(values, errors, result=None):
    return render_template(
        "index.html",
        fields=FIELDS,
        rows=RESULT_ROWS,
        values=values,
        errors=errors,
        result=result,
        display=_display(result["values"]) if result else {},
        exact_display=_display(result["exact"]) if result else {},
    )


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return _render(DEFAULTS, {})

    @app.post("/solve")
    def solve_bias():
        parsed, errors = parse(request.form)
        if errors:
            return _render(request.form, errors), 400
        return _render(request.form, {}, solve(**parsed))

    return app


app = create_app()
