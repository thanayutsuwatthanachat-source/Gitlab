"""Parse and validate the bias form. Returns base units (V, Ω).

Lab 03: the form carries a `mode` field. Only the inputs that the selected
circuit actually needs are parsed and validated; the missing ones stay absent
from the returned dict (and from the errors dict).
"""

import math

from .units import RESISTANCE_UNITS, VOLTAGE_UNITS, to_ohms, to_volts

MODES = ("divider", "fixed", "emitter")
DEFAULT_MODE = "divider"

MODE_FIELDS = {
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

FIELDS = ("vcc", "rb", "r1", "r2", "rc", "re", "beta", "vbe")

UNIT_NAMES = {
    "vcc": "vcc_unit",
    "rb": "rb_unit",
    "r1": "r1_unit",
    "r2": "r2_unit",
    "rc": "rc_unit",
    "re": "re_unit",
    "beta": "",
    "vbe": "vbe_unit",
}

VOLTAGE_FIELDS = ("vcc", "vbe")
RESISTANCE_FIELDS = ("rb", "r1", "r2", "rc", "re")

NOT_A_NUMBER = "ต้องเป็นตัวเลข"
NOT_FINITE = "ต้องเป็นค่าจำกัด"
NOT_POSITIVE = "ต้องมากกว่า 0"
BETA_RANGE = "ต้องมีค่า >= 1"
VBE_RANGE = "ต้องอยู่ระหว่าง 0 กับ VCC"
BAD_UNIT = "หน่วยไม่ถูกต้อง"
BAD_MODE = "โหมดไม่ถูกต้อง"


def parse(form):
    mode = (form.get("mode") or DEFAULT_MODE).strip()
    if mode not in MODE_FIELDS:
        return None, {"mode": BAD_MODE}

    required = MODE_FIELDS[mode]
    values = {}
    errors = {}

    for field in required:
        try:
            number = float(form.get(field, ""))
        except (TypeError, ValueError):
            errors[field] = NOT_A_NUMBER
            continue
        if not math.isfinite(number):
            errors[field] = NOT_FINITE
            continue

        if field in VOLTAGE_FIELDS:
            unit = form.get(UNIT_NAMES[field], "V")
            try:
                converted = to_volts(number, unit)
            except KeyError:
                errors[field] = BAD_UNIT
                continue
        elif field in RESISTANCE_FIELDS:
            unit = form.get(UNIT_NAMES[field], "Ω")
            try:
                converted = to_ohms(number, unit)
            except KeyError:
                errors[field] = BAD_UNIT
                continue
        else:
            converted = number

        if not math.isfinite(converted):
            errors[field] = NOT_FINITE
            continue
        values[field] = converted

    if errors:
        return None, errors

    if values["vcc"] <= 0:
        errors["vcc"] = NOT_POSITIVE
    for field in required:
        if field in RESISTANCE_FIELDS and values[field] <= 0:
            errors[field] = NOT_POSITIVE
    if values["beta"] < 1:
        errors["beta"] = BETA_RANGE

    # Divider keeps the Lab 02 input rule (0 < VBE < VCC). The two modes added
    # in Lab 03 are allowed to reach I_B <= 0, because the worksheet asks for a
    # model warning there instead of an input error.
    if mode == "divider":
        if not 0 < values["vbe"] < values["vcc"]:
            errors["vbe"] = VBE_RANGE
    elif values["vbe"] <= 0:
        errors["vbe"] = NOT_POSITIVE

    if errors:
        return None, errors
    return values, {}


__all__ = ["FIELDS", "MODE_FIELDS", "MODES", "UNIT_NAMES", "parse",
           "VOLTAGE_UNITS", "RESISTANCE_UNITS"]
