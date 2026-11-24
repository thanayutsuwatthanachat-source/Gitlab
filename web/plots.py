"""Presentation geometry for SVG plots; all traces come from ngspice vectors."""

import cmath
import math

from bjt.spice import AC_REFERENCE, SpiceError


def _tick(value):
    return f"{value:.4g}" if abs(value) >= 0.001 or value == 0 else f"{value:.2e}"


def _nice_ticks(low, high):
    step = (high - low) / 5
    power = 10 ** math.floor(math.log10(step))
    step = next(unit * power for unit in (1, 2, 2.5, 5, 10) if unit * power >= step)
    return [step * i for i in range(math.ceil(low / step), math.floor(high / step) + 1)]


def _chart(title, x_label, y_label, x, series, log=False):
    left, right, top, bottom = 65, 395, 12, 153
    x0, x1 = (math.log10(x[0]), math.log10(x[-1])) if log else (x[0], x[-1])
    low = min(min(y) for _, _, y in series)
    high = max(max(y) for _, _, y in series)
    pad = (high - low) * 0.08 or max(abs(low) * 0.1, 1e-9)
    low, high = low - pad, high + pad

    def px(value):
        return left + (right - left) * (value - x0) / (x1 - x0)

    def py(value):
        return bottom - (bottom - top) * (value - low) / (high - low)

    if log:
        x_ticks = [(px(i), label) for i, label in (
            (-1, "0.1"), (1, "10"), (3, "1k"), (5, "100k"), (7, "10M"), (8, "100M")
        )]
    else:
        x_ticks = [(px(tick), _tick(tick)) for tick in _nice_ticks(x0, x1)]
    return {
        "title": title, "x_label": x_label, "y_label": y_label,
        "x_ticks": x_ticks,
        "y_ticks": [(py(y), _tick(y)) for y in _nice_ticks(low, high)],
        "curves": [
            {"name": name, "color": color, "points": " ".join(
                f"{px(math.log10(t) if log else t):.2f},{py(v):.2f}" for t, v in zip(x, y)
            )}
            for name, color, y in series
        ],
    }


def _crossing(freq, db, ref, direction):
    target = db[ref] - 3
    for i in range(ref, 0 if direction < 0 else len(db) - 1, direction):
        j = i + direction
        if db[i] >= target >= db[j] and db[i] != db[j]:
            fraction = (target - db[i]) / (db[j] - db[i])
            return 10 ** (math.log10(freq[i]) + fraction * math.log10(freq[j]/freq[i]))
    return None


def prepare_plots(analysis, rows):
    if analysis == "ac":
        freq = rows["frequency"]
        try:
            ratio = [out / source for out, source in zip(rows["v(out)"], rows["v(vin)"])]
            db = [20 * math.log10(abs(gain)) for gain in ratio]
        except (ZeroDivisionError, ValueError) as exc:
            raise SpiceError("ไม่สามารถหาอัตราขยายจากผล AC รอบนี้ได้") from exc
        phase = []
        for gain in ratio:
            degrees = math.degrees(cmath.phase(gain))
            if phase:
                degrees = phase[-1] + (degrees - phase[-1] + 180) % 360 - 180
            phase.append(degrees)
        ref = min(range(len(freq)), key=lambda i: abs(freq[i] - AC_REFERENCE))
        return [
            _chart("Gain magnitude", "Frequency (Hz · log)", "Gain (dB)", freq,
                   [("20 log₁₀ |Vout/Vin|", "output", db)], log=True),
            _chart("Phase response", "Frequency (Hz · log)", "Phase (°)", freq,
                   [("∠(Vout/Vin)", "output", phase)], log=True),
        ], {
            "Gain at 1 kHz": f"{abs(ratio[ref]):.4g} V/V · {db[ref]:.3f} dB",
            "Phase at 1 kHz": f"{phase[ref]:.2f}°",
            "Lower −3 dB": _cutoff(_crossing(freq, db, ref, -1)),
            "Upper −3 dB": _cutoff(_crossing(freq, db, ref, 1)),
            "Frequency samples": str(len(freq)),
        }
    t = [1000 * value for value in rows["time"]]
    vin = [1000 * value for value in rows["v(vin)"]]
    vout = [1000 * value for value in rows["v(out)"]]
    return [_chart("Input and output voltages", "Time (ms)", "Voltage (mV)", t,
                   [("Vin · source", "input", vin), ("Vout · load", "output", vout)])], {
        "Vin peak-to-peak": f"{max(vin)-min(vin):.4g} mVpp",
        "Vout peak-to-peak": f"{max(vout)-min(vout):.4g} mVpp",
        "Time samples": str(len(t)),
    }


def _cutoff(value):
    if value is None:
        return "Not determined in sweep range"
    if value >= 1e6:
        return f"{value/1e6:.4g} MHz"
    if value >= 1e3:
        return f"{value/1e3:.4g} kHz"
    return f"{value:.4g} Hz"
