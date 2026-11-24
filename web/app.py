"""Flask routes only. Engineering lives in bjt/, presentation in templates/."""

import os

from flask import Flask, redirect, render_template, request, url_for

from bjt.bias import solve_mode
from bjt import spice
from bjt.units import RESISTANCE_UNITS, VOLTAGE_UNITS, format_engineering
from bjt.validation import BAD_MODE, MODE_FIELDS, parse
from web.plots import prepare_plots

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

MODE_HINTS = {
    "divider": "R1 (VCC→base), R2 (base→ground), RE (emitter→ground)",
    "fixed": "RB (VCC→base), emitter grounded",
    "emitter": "RB (VCC→base), RE (emitter→ground)",
}

DEFAULTS = {
    "mode": "divider",
    "vcc": "12.0", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rb": "1000", "rb_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1.0", "re_unit": "kΩ",
    "beta": "100",
    "vbe": "0.70", "vbe_unit": "V",
}

FIELD_DEFS = {
    "vcc": {"name": "vcc", "symbol": "V", "sub": "CC", "hint": "Supply Voltage",
            "units": tuple(VOLTAGE_UNITS)},
    "rb": {"name": "rb", "symbol": "R", "sub": "B", "hint": "Base Resistor",
           "units": tuple(RESISTANCE_UNITS)},
    "r1": {"name": "r1", "symbol": "R", "sub": "1", "hint": "Upper Divider",
           "units": tuple(RESISTANCE_UNITS)},
    "r2": {"name": "r2", "symbol": "R", "sub": "2", "hint": "Lower Divider",
           "units": tuple(RESISTANCE_UNITS)},
    "rc": {"name": "rc", "symbol": "R", "sub": "C", "hint": "Collector Resistor",
           "units": tuple(RESISTANCE_UNITS)},
    "re": {"name": "re", "symbol": "R", "sub": "E", "hint": "Emitter Resistor",
           "units": tuple(RESISTANCE_UNITS)},
    "beta": {"name": "beta", "symbol": "β", "sub": "", "hint": "Current Gain",
             "units": ()},
    "vbe": {"name": "vbe", "symbol": "V", "sub": "BE",
            "hint": "Base-Emitter Voltage", "units": tuple(VOLTAGE_UNITS)},
}

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


def _fields_for(mode):
    if mode not in MODE_FIELDS:
        return []
    return [FIELD_DEFS[name] for name in MODE_FIELDS[mode]]


def _display(values):
    return {
        key: format_engineering(values[key], "A" if key in CURRENT_KEYS else "V")
        for _, _, key in RESULT_ROWS
    }


def _render(mode, values, errors, result=None):
    known = mode in MODE_LABELS
    return render_template(
        "index.html",
        modes=MODE_LABELS,
        mode=mode if known else None,
        mode_label=MODE_LABELS.get(mode),
        mode_hint=MODE_HINTS.get(mode),
        fields=_fields_for(mode),
        rows=RESULT_ROWS,
        values=values,
        errors=errors,
        result=result,
        display=_display(result["values"]) if result else {},
        exact_display=_display(result["exact"]) if result and result.get("exact") else {},
    )


def create_app():
    app = Flask(__name__)
    app.config.update(
        LAB04_HOME=os.environ.get("LAB04_HOME", "bias"),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    @app.get("/healthz")
    def health():
        return ("ok\n", 200) if spice.executable() else ("ngspice unavailable\n", 503)

    @app.get("/")
    def index():
        if app.config["LAB04_HOME"] == "simulator" and "mode" not in request.args:
            return redirect(url_for("simulator"))
        mode = (request.args.get("mode") or "divider").strip()
        if mode not in MODE_LABELS:
            return _render(None, DEFAULTS, {"mode": BAD_MODE}), 400
        return _render(mode, DEFAULTS, {})

    @app.post("/solve")
    def solve_bias():
        mode = (request.form.get("mode") or "divider").strip()
        if mode not in MODE_LABELS:
            return _render(None, request.form, {"mode": BAD_MODE}), 400

        parsed, errors = parse(request.form)
        if errors:
            return _render(mode, request.form, errors), 400

        return _render(mode, request.form, {}, solve_mode(mode, parsed))

    @app.route("/simulator", methods=["GET", "POST"])
    def simulator():
        submitted = request.method == "POST"
        source = request.form if submitted else request.args
        selection = source.get("analysis", "dc")
        analysis = selection if selection in spice.ANALYSES else "dc"
        values = {key: source.get(key, "" if submitted else default)
                  for key, default in spice.DEFAULTS.items()}
        summary, charts, evidence, reference, errors = {}, [], {}, {}, {}
        failure, log, status = "", "", 200
        if submitted:
            params, errors = spice.parse_inputs(selection, values)
            if errors:
                status = 400
            else:
                try:
                    rows, evidence = spice.run_spice(analysis, params)
                    if analysis == "dc":
                        vb, ve, vc, ic = (rows[key][0] for key in
                                          ("v(b)", "v(e)", "v(c)", "i(vsense)"))
                        summary = {
                            label: f"{number:.5g} {unit}" for label, number, unit in (
                                ("VB", vb, "V"), ("VE", ve, "V"), ("VC", vc, "V"),
                                ("VCE", vc-ve, "V"), ("IC", 1000*ic, "mA"),
                            )
                        }
                        if params["vcc"] > 0.7:
                            bias = {field.key: params[field.key] for field in spice.BIAS_FIELDS}
                            ref = solve_mode("divider", dict(bias, beta=100, vbe=0.7))
                            reference = _display(ref["values"])
                    else:
                        charts, summary = prepare_plots(analysis, rows)
                except spice.SpiceError as exc:
                    evidence, failure, log, status = {}, str(exc), exc.log, 503
        return render_template(
            "simulator.html", analysis=analysis, analyses=spice.ANALYSES,
            bias_fields=spice.BIAS_FIELDS, coupling_fields=spice.COUPLING_FIELDS,
            source_fields=spice.SOURCE_FIELDS, values=values, errors=errors,
            model=spice.MODEL, model_card=spice.MODEL_CARD, charts=charts,
            summary=summary, evidence=evidence, reference=reference,
            failure=failure, log=log,
        ), status

    return app


app = create_app()
