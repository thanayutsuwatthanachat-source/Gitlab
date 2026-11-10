"""Unit conversion and engineering-notation formatting."""

VOLTAGE_UNITS = {"V": 1.0, "mV": 1e-3}
RESISTANCE_UNITS = {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}

_PREFIXES = (
    (1e9, "G"),
    (1e6, "M"),
    (1e3, "k"),
    (1.0, ""),
    (1e-3, "m"),
    (1e-6, "µ"),
    (1e-9, "n"),
)


def to_volts(value, unit):
    return value * VOLTAGE_UNITS[unit]


def to_ohms(value, unit):
    return value * RESISTANCE_UNITS[unit]


def format_engineering(value, unit):
    """Format a base-unit value with an SI prefix and 3 significant figures."""
    if value == 0:
        return f"0 {unit}"
    magnitude = abs(value)
    for scale, prefix in _PREFIXES:
        if magnitude >= scale:
            return f"{value / scale:.3g} {prefix}{unit}"
    return f"{value / 1e-9:.3g} n{unit}"
