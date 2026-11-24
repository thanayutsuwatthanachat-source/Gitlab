"""Validated inputs and an isolated ngspice batch adapter for one CE circuit."""

import cmath
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

MODEL = "LAB_NPN"
# Generic teaching model, not a vendor model or an instructor-verified model.
MODEL_CARD = ".model LAB_NPN NPN(IS=1e-14 BF=100 VAF=100 CJE=20p CJC=8p TF=0.35n)"
AC_LOW, AC_HIGH, AC_REFERENCE = 0.1, 100e6, 1e3
ANALYSES = {"dc": ("DC", ".op"), "ac": ("AC", ".ac"), "tran": ("Transient", ".tran")}


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    unit: str
    default: str
    scale: float
    low: float
    high: float


BIAS_FIELDS = (
    Field("vcc", "VCC", "V", "12", 1, 0.1, 30),
    Field("r1", "R1", "kΩ", "100", 1e3, 0.01, 10000),
    Field("r2", "R2", "kΩ", "22", 1e3, 0.01, 10000),
    Field("rc", "RC", "kΩ", "2.2", 1e3, 0.01, 10000),
    Field("re", "RE", "kΩ", "1", 1e3, 0.01, 10000),
)
COUPLING_FIELDS = (
    Field("rl", "RL", "kΩ", "10", 1e3, 0.01, 10000),
    Field("cin", "Cin", "µF", "10", 1e-6, 0.001, 1000),
    Field("cout", "Cout", "µF", "10", 1e-6, 0.001, 1000),
)
SOURCE_FIELDS = (
    Field("amplitude", "Amplitude", "mV peak", "10", 1e-3, 0.01, 1000),
    Field("frequency", "Frequency", "Hz", "1000", 1, 1, 100000),
)
DEFAULTS = {f.key: f.default for f in BIAS_FIELDS + COUPLING_FIELDS + SOURCE_FIELDS}


def parse_inputs(analysis, form):
    if analysis not in ANALYSES:
        return {}, {"analysis": "ไม่รู้จักโหมดการวิเคราะห์"}
    fields = BIAS_FIELDS
    if analysis != "dc":
        fields += COUPLING_FIELDS
    if analysis == "tran":
        fields += SOURCE_FIELDS
    values, errors = {}, {}
    active = {field.key for field in fields}
    # Retain the same reference topology in every analysis. DC opens Cin/Cout.
    for field in BIAS_FIELDS + COUPLING_FIELDS + SOURCE_FIELDS:
        raw = form.get(field.key, "") if field.key in active else field.default
        try:
            number = float(raw)
        except (ValueError, TypeError):
            errors[field.key] = "ต้องเป็นตัวเลข"
            continue
        if not math.isfinite(number) or not field.low <= number <= field.high:
            errors[field.key] = f"ต้องอยู่ระหว่าง {field.low:g} ถึง {field.high:g} {field.unit}"
        else:
            values[field.key] = number * field.scale
    return values, errors


class SpiceError(Exception):
    """No trustworthy result can be returned for this run."""

    def __init__(self, message, log=""):
        super().__init__(message)
        self.log = log


def executable():
    override = os.environ.get("NGSPICE_BIN")
    if override:
        return shutil.which(override)
    # Prefer the console executable on Windows (not the GUI build).
    return shutil.which("ngspice_con") or shutil.which("ngspice")


def build_netlist(analysis, p):
    amp, freq = p["amplitude"], p["frequency"]
    period = 1 / freq
    directive, vectors = {
        "dc": (".op", "v(b) v(e) v(c) i(vsense)"),
        "ac": (f".ac dec 40 {AC_LOW:g} {AC_HIGH:g}", "v(vin) v(out)"),
        "tran": (f".tran {period/120:.12g} {12*period:.12g} "
                 f"{8*period:.12g} {period/120:.12g}", "v(vin) v(out)"),
    }[analysis]
    return f"""Lab 04 common-emitter voltage-divider reference
.options filetype=ascii temp=27
VCC vcc 0 {p['vcc']:.12g}
Vin vin 0 DC 0 AC 1 SIN(0 {amp:.12g} {freq:.12g})
R1 vcc b {p['r1']:.12g}
R2 b 0 {p['r2']:.12g}
RC vcc csense {p['rc']:.12g}
Vsense csense c 0
RE e 0 {p['re']:.12g}
Cin vin b {p['cin']:.12g}
Cout c out {p['cout']:.12g}
RL out 0 {p['rl']:.12g}
Q1 c b e {MODEL}
{MODEL_CARD}
{directive}
.save {vectors}
.end
"""


def parse_raw(text, analysis):
    """Read one ASCII netlist plot and verify its shape, vectors and values."""
    required = {
        "dc": {"v(b)", "v(e)", "v(c)", "i(vsense)"},
        "ac": {"frequency", "v(vin)", "v(out)"},
        "tran": {"time", "v(vin)", "v(out)"},
    }[analysis]
    try:
        header, data = text.split("Values:", 1)
        metadata, variables = header.split("\nVariables:", 1)
        headers = dict(line.split(":", 1) for line in metadata.splitlines() if ":" in line)
        if headers["Plotname"].strip() != {
            "dc": "Operating Point", "ac": "AC Analysis", "tran": "Transient Analysis",
        }[analysis]:
            raise ValueError
        complex_plot = headers["Flags"].split()[0] == "complex"
        if headers["Flags"].split()[0] != ("complex" if analysis == "ac" else "real"):
            raise ValueError
        count = int(headers["No. Points"])
        names = [line.split()[1].lower() for line in variables.splitlines() if line.strip()]
        if (set(names) != required or len(names) != len(required)
                or int(headers["No. Variables"]) != len(names)
                or not (count == 1 if analysis == "dc" else 2 <= count <= 10000)):
            raise ValueError
        tokens = data.split()
        stride = len(names) + 1
        if len(tokens) != count * stride:
            raise ValueError
        rows = {name: [] for name in names}
        for index in range(count):
            start = index * stride
            if int(tokens[start]) != index:
                raise ValueError
            for name, token in zip(names, tokens[start+1:start+stride]):
                if complex_plot:
                    real, imag = map(float, token.split(","))
                    # Complex raw files can leave the frequency imaginary slot undefined.
                    value = real if name == "frequency" else complex(real, imag)
                else:
                    value = float(token)
                if not cmath.isfinite(value):
                    raise ValueError
                rows[name].append(value)
        axis = rows.get("time", rows.get("frequency"))
        if axis and (axis[0] < 0 or any(left >= right for left, right in zip(axis, axis[1:]))):
            raise ValueError
        return rows
    except (IndexError, ValueError, KeyError, OverflowError) as exc:
        raise SpiceError("ผลลัพธ์ ngspice ว่าง ไม่ครบ หรือไม่ตรงกับโหมดที่เลือก") from exc


def run_spice(analysis, values):
    """Return vectors plus the exact source netlist and log for this run only."""
    binary = executable()
    if not binary:
        raise SpiceError("ไม่พบ ngspice — เพิ่มลง PATH หรือตั้งค่า NGSPICE_BIN")
    netlist = build_netlist(analysis, values)
    try:
        with TemporaryDirectory(prefix="lab04-") as folder:
            path = Path(folder)
            (path / "circuit.cir").write_text(netlist, encoding="ascii")
            job = subprocess.run(
                [binary, "-n", "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"],
                cwd=path, capture_output=True, text=True, errors="replace", timeout=12,
                shell=False,
            )
            log_path, raw_path = path / "run.log", path / "run.raw"
            log = log_path.read_text(errors="replace") if log_path.exists() else ""
            log = "\n".join(item for item in (log, job.stderr) if item).strip()[-6000:]
            if (job.returncode or not raw_path.exists()
                    or any("timestep too small" in line or "aborted" in line
                           or line.lstrip().startswith(("error:", "fatal error"))
                           for line in log.lower().splitlines())):
                raise SpiceError("ngspice รันไม่สำเร็จ — ตรวจรายละเอียดจาก Run log", log)
            if raw_path.stat().st_size > 2_000_000:
                raise SpiceError("ไฟล์ผลลัพธ์ ngspice ใหญ่เกินขีดจำกัด", log)
            try:
                raw = raw_path.read_bytes()
                rows = parse_raw(raw.decode("ascii"), analysis)
                if analysis == "tran" and not math.isclose(
                    rows["time"][-1], 12 / values["frequency"], rel_tol=1e-6
                ):
                    raise SpiceError("ngspice หยุดก่อนถึงเวลาท้ายของการจำลอง")
                if analysis == "ac" and not (
                    math.isclose(rows["frequency"][0], AC_LOW, rel_tol=1e-6)
                    and math.isclose(rows["frequency"][-1], AC_HIGH, rel_tol=1e-6)
                ):
                    raise SpiceError("ผล ngspice ไม่ครอบคลุมช่วงความถี่ที่ขอ")
            except (SpiceError, UnicodeError) as exc:
                raise SpiceError(str(exc), log) from exc
            return rows, {"netlist": netlist, "log": log,
                          "digest": hashlib.sha256(raw).hexdigest()}
    except subprocess.TimeoutExpired as exc:
        raise SpiceError("ngspice ใช้เวลาเกิน 12 วินาทีและถูกหยุด") from exc
    except OSError as exc:
        raise SpiceError("ไม่สามารถเรียก ngspice หรืออ่านไฟล์ผลการจำลองได้") from exc
