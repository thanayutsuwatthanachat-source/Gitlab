import math


def _validate_positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def analyze_dc(voltage_v, resistance_ohm):
    _validate_positive(voltage_v, "Voltage")
    _validate_positive(resistance_ohm, "Resistance")
    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def equivalent_resistance(circuit):
    """Return the equivalent resistance of a nested series/parallel circuit."""
    circuit_type = circuit.get("type")
    if circuit_type == "resistor":
        resistance = circuit.get("resistance_ohm")
        _validate_positive(resistance, "Resistance")
        return resistance

    if circuit_type not in ("series", "parallel"):
        raise ValueError("Circuit type must be resistor, series, or parallel")

    components = circuit.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("A circuit group must contain at least one component")

    resistances = [equivalent_resistance(component) for component in components]
    if circuit_type == "series":
        return sum(resistances)
    return 1 / sum(1 / resistance for resistance in resistances)


def analyze_circuit(voltage_v, circuit):
    """Analyze a nested circuit and return totals and values for each resistor."""
    _validate_positive(voltage_v, "Voltage")
    total_resistance = equivalent_resistance(circuit)
    total_current = voltage_v / total_resistance
    resistors = []

    def visit(component, component_voltage, path):
        component_type = component["type"]
        if component_type == "resistor":
            resistance = component["resistance_ohm"]
            current = component_voltage / resistance
            resistors.append({
                "path": path,
                "resistance_ohm": resistance,
                "voltage_v": component_voltage,
                "current_a": current,
                "power_w": component_voltage * current,
            })
            return

        components = component["components"]
        if component_type == "series":
            group_current = component_voltage / equivalent_resistance(component)
            for index, child in enumerate(components, 1):
                child_voltage = group_current * equivalent_resistance(child)
                visit(child, child_voltage, f"{path}.{index}")
        else:
            for index, child in enumerate(components, 1):
                visit(child, component_voltage, f"{path}.{index}")

    visit(circuit, voltage_v, "1")
    return {
        "equivalent_resistance_ohm": total_resistance,
        "total_current_a": total_current,
        "total_power_w": voltage_v * total_current,
        "resistors": resistors,
    }


def _read_number(prompt):
    while True:
        try:
            value = float(input(prompt))
            _validate_positive(value, "Value")
            return value
        except ValueError as error:
            print(f"Invalid input: {error}")


def _read_circuit():
    while True:
        circuit_type = input("Component type (resistor/series/parallel): ").strip().lower()
        if circuit_type in ("resistor", "series", "parallel"):
            break
        print("Please enter resistor, series, or parallel.")

    if circuit_type == "resistor":
        return {"type": "resistor", "resistance_ohm": _read_number("Resistance (ohm): ")}

    while True:
        try:
            count = int(input(f"Number of components in {circuit_type}: "))
            if count > 0:
                break
            print("Enter a number greater than zero.")
        except ValueError:
            print("Enter a whole number greater than zero.")

    components = []
    for index in range(1, count + 1):
        print(f"Component {index}:")
        components.append(_read_circuit())
    return {"type": circuit_type, "components": components}


def main():
    print("DC circuit calculator")
    voltage_v = _read_number("Source voltage (V): ")
    circuit = _read_circuit()
    result = analyze_circuit(voltage_v, circuit)

    print(f"\nEquivalent resistance: {result['equivalent_resistance_ohm']:.4g} ohm")
    print(f"Total current: {result['total_current_a']:.4g} A")
    print(f"Total power: {result['total_power_w']:.4g} W")
    print("\nResistor results:")
    for resistor in result["resistors"]:
        print(
            f"  R{resistor['path']}: {resistor['resistance_ohm']:.4g} ohm, "
            f"{resistor['voltage_v']:.4g} V, {resistor['current_a']:.4g} A, "
            f"{resistor['power_w']:.4g} W"
        )


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nCalculation cancelled.")