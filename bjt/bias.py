"""DC bias solvers for an NPN common-emitter stage.

Lab 02: voltage-divider bias only.
Lab 03: adds fixed bias and single-supply emitter bias, selected by solve_mode().

All arguments are in base units: volts and ohms.
Every solver returns the same keys: ib, ic, ie, vb, vc, ve, vce.
"""

VCE_SAT = 0.2

MODE_DIVIDER = "divider"
MODE_FIXED = "fixed"
MODE_EMITTER = "emitter"
MODES = (MODE_DIVIDER, MODE_FIXED, MODE_EMITTER)


def approximate(vcc, r1, r2, rc, re, beta, vbe):
    """Textbook approximation: the divider is stiff, so base current is ignored."""
    vbb = vcc * r2 / (r1 + r2)
    vb = vbb
    ve = vb - vbe
    ic = ve / re
    ib = ic / beta
    ie = ic + ib
    vc = vcc - ic * rc
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "vc": vc, "ve": ve,
            "vce": vc - ve}


def exact(vcc, r1, r2, rc, re, beta, vbe):
    """Exact closed form: Thevenin source and base resistance seen by the base."""
    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)
    ib = (vbb - vbe) / (rb + (1 + beta) * re)
    ic = beta * ib
    ie = (1 + beta) * ib
    ve = ie * re
    vb = vbe + ve
    vc = vcc - ic * rc
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "vc": vc, "ve": ve,
            "vce": vc - ve}


def nodal(vcc, r1, r2, rc, re, beta, vbe):
    """Independent route: solve the linear node equations for VE, IB and VC."""
    matrix = [
        [1 / r1 + 1 / r2, 1.0, 0.0],
        [1 / re, -(1 + beta), 0.0],
        [0.0, beta, 1 / rc],
    ]
    rhs = [(vcc - vbe) / r1 - vbe / r2, 0.0, vcc / rc]
    ve, ib, vc = _gauss(matrix, rhs)
    ic = beta * ib
    ie = (1 + beta) * ib
    return {"ib": ib, "ic": ic, "ie": ie, "vb": ve + vbe, "vc": vc, "ve": ve,
            "vce": vc - ve}


def _gauss(matrix, rhs):
    """Gaussian elimination with partial pivoting."""
    n = len(rhs)
    a = [row[:] for row in matrix]
    b = rhs[:]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            b[col], b[pivot] = b[pivot], b[col]
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for k in range(col, n):
                a[row][k] -= factor * a[col][k]
            b[row] -= factor * b[col]
    solution = [0.0] * n
    for row in reversed(range(n)):
        total = sum(a[row][k] * solution[k] for k in range(row + 1, n))
        solution[row] = (b[row] - total) / a[row][row]
    return solution


def apply_region(vcc, r1, r2, rc, re, beta, vbe, values):
    """Return the reported values and the operating region."""
    vbb = vcc * r2 / (r1 + r2)
    if vbb <= vbe:
        return ({"ib": 0.0, "ic": 0.0, "ie": 0.0, "vb": vbb, "vc": vcc,
                 "ve": 0.0, "vce": vcc}, "cutoff")
    if values["vce"] <= VCE_SAT:
        ic = (vcc - VCE_SAT) / (rc + re)
        ib = ic / beta
        ie = ic + ib
        ve = ie * re
        vc = VCE_SAT + ve
        return ({"ib": ib, "ic": ic, "ie": ie, "vb": vbe + ve, "vc": vc,
                 "ve": ve, "vce": VCE_SAT}, "saturation")
    return dict(values), "active"


def warning_for(region, vcc, vbe, vce):
    if region == "cutoff":
        return {
            "level": "warn",
            "title": "Cutoff region",
            "detail": (f"VBE = {vbe:.2f} V is not enough to forward bias the "
                       "base-emitter junction (VBB ≤ VBE)"),
        }
    if region == "saturation":
        return {
            "level": "bad",
            "title": "Saturation warning",
            "detail": (f"VCE = {vce:.2f} V ≤ {VCE_SAT} V — the transistor is "
                       "saturated and no longer in the active region"),
        }
    return {
        "level": "ok",
        "title": "Active region approximation OK",
        "detail": (f"VCE = {vce:.2f} V > {VCE_SAT} V (transistor in active "
                   "region)"),
    }


def solve(vcc, r1, r2, rc, re, beta, vbe):
    raw = approximate(vcc, r1, r2, rc, re, beta, vbe)
    values, region = apply_region(vcc, r1, r2, rc, re, beta, vbe, raw)
    exact_values = exact(vcc, r1, r2, rc, re, beta, vbe)
    nodal_values = nodal(vcc, r1, r2, rc, re, beta, vbe)
    return {
        "values": values,
        "region": region,
        "warning": warning_for(region, vcc, vbe, values["vce"]),
        "exact": exact_values,
        "nodal": nodal_values,
        "delta": {
            "ic_pct": _percent(values["ic"], exact_values["ic"]),
            "vce_pct": _percent(values["vce"], exact_values["vce"]),
        },
    }


def _percent(primary, reference):
    if reference == 0:
        return 0.0
    return abs(primary - reference) / abs(reference) * 100


# --------------------------------------------------------------------------
# Lab 03: fixed bias and single-supply emitter bias
# --------------------------------------------------------------------------


def _from_ib(ib, vcc, rc, re, beta, vbe):
    """Common tail: currents and node voltages from I_B (base units)."""
    ic = beta * ib
    ie = (1 + beta) * ib
    ve = ie * re
    vb = vbe + ve
    vc = vcc - ic * rc
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "vc": vc, "ve": ve,
            "vce": vc - ve}


def fixed(vcc, rb, rc, beta, vbe):
    """Fixed bias: R_B from VCC to base, emitter grounded (R_E = 0).

    I_B = (VCC - VBE) / R_B
    """
    ib = (vcc - vbe) / rb
    return _from_ib(ib, vcc, rc, 0.0, beta, vbe)


def emitter(vcc, rb, rc, re, beta, vbe):
    """Single-supply emitter bias: R_B to base, R_E from emitter to ground.

    I_B = (VCC - VBE) / [R_B + (1 + beta) * R_E]
    """
    ib = (vcc - vbe) / (rb + (1 + beta) * re)
    return _from_ib(ib, vcc, rc, re, beta, vbe)


def region_for(values):
    """Forward-active check for the two modes added in Lab 03.

    Cutoff and saturation are only reported here: the worksheet does not ask
    for a re-solve outside the forward-active region.
    """
    if values["ib"] <= 0:
        return "cutoff"
    if values["vce"] <= VCE_SAT:
        return "saturation"
    return "active"


def warning_for_mode(region, vce):
    if region == "cutoff":
        return {
            "level": "warn",
            "title": "Cutoff region",
            "detail": ("I_B ≤ 0 — V_BE is not enough to forward bias the "
                       "base-emitter junction, so the model stops here"),
        }
    if region == "saturation":
        return {
            "level": "bad",
            "title": "Saturation warning",
            "detail": (f"VCE = {vce:.2f} V ≤ {VCE_SAT} V — the forward-active "
                       "model is no longer valid"),
        }
    return {
        "level": "ok",
        "title": "Active region OK",
        "detail": f"VCE = {vce:.2f} V > {VCE_SAT} V (forward active)",
    }


def solve_mode(mode, values):
    """Dispatch on the selected circuit. Divider keeps the Lab 02 result."""
    if mode == MODE_DIVIDER:
        return dict(solve(**values), mode=mode)
    if mode == MODE_FIXED:
        raw = fixed(**values)
    elif mode == MODE_EMITTER:
        raw = emitter(**values)
    else:
        raise ValueError(f"ไม่รู้จักโหมด '{mode}'")

    region = region_for(raw)
    return {
        "values": raw,
        "region": region,
        "warning": warning_for_mode(region, raw["vce"]),
        "exact": None,
        "nodal": None,
        "delta": None,
        "mode": mode,
    }
