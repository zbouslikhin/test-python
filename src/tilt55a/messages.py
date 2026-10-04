"""Parsing and building of the TILT-55A's documented ASCII sentence/command protocol.

Per its datasheet, the device speaks a simple NMEA-0183-like ASCII protocol (not Modbus):
inclinometer/sensor data sentences such as ``$CSTLT,...*CC`` and short configuration
commands/responses such as ``[1D400<cr>`` / ``>New Output Data Rate: 400``.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Output data rates (Hz) the device can be configured to (datasheet sections 2.4 and 7).
DATA_RATES_HZ: tuple[int, ...] = (1, 2, 5, 10, 20, 25, 40, 50, 100, 200, 400)


class MessageFormatError(ValueError):
    """A sentence, command or response does not match the TILT-55A protocol."""


class ChecksumError(ValueError):
    """A sentence's checksum does not match its computed value."""


class UnsupportedDataRateError(ValueError):
    """The requested output data rate is not one the device supports."""


def compute_checksum(payload: str) -> int:
    """The 8-bit XOR checksum of `payload` (the bytes between ``$`` and ``*``)."""
    checksum = 0
    for byte in payload.encode("ascii"):
        checksum ^= byte
    return checksum


@dataclass(frozen=True)
class InclinometerReading:
    """A parsed ``$CSTLT`` message: acceleration, roll/pitch angles and temperature."""

    accel_x_mg: float
    accel_y_mg: float
    accel_z_mg: float
    roll_deg: float
    pitch_deg: float
    temperature_c: float


@dataclass(frozen=True)
class SensorReading:
    """A parsed ``$CSAGD`` message: raw accelerometer and gyroscope data."""

    accel_x_mg: float
    accel_y_mg: float
    accel_z_mg: float
    gyro_x_dps: float
    gyro_y_dps: float
    gyro_z_dps: float
    temperature_c: float


def _split_sentence(line: str) -> tuple[str, list[str]]:
    """Validate a sentence's envelope and checksum; return (talker, data fields)."""
    stripped = line.strip()
    if not stripped.startswith("$") or "*" not in stripped:
        raise MessageFormatError(f"not a TILT-55A sentence: {line!r}")
    body, _, checksum_hex = stripped[1:].partition("*")
    if not checksum_hex:
        raise MessageFormatError(f"missing checksum: {line!r}")
    try:
        expected = int(checksum_hex, 16)
    except ValueError as exc:
        raise MessageFormatError(f"invalid checksum characters: {line!r}") from exc
    actual = compute_checksum(body)
    if actual != expected:
        raise ChecksumError(f"checksum {checksum_hex} does not match computed {actual:02X}")
    fields = body.split(",")
    if not fields or not fields[0]:
        raise MessageFormatError(f"empty sentence body: {line!r}")
    return fields[0], fields[1:]


def _parse_floats(fields: list[str], line: str) -> list[float]:
    try:
        return [float(field) for field in fields]
    except ValueError as exc:
        raise MessageFormatError(f"non-numeric field in: {line!r}") from exc


def parse_inclinometer_message(line: str) -> InclinometerReading:
    """Parse a ``$CSTLT,AX,AY,AZ,roll,pitch,T*CC`` sentence."""
    talker, fields = _split_sentence(line)
    if talker != "CSTLT" or len(fields) != 6:
        raise MessageFormatError(f"not a $CSTLT inclinometer message: {line!r}")
    ax, ay, az, roll, pitch, temp = _parse_floats(fields, line)
    return InclinometerReading(ax, ay, az, roll, pitch, temp)


def parse_sensor_message(line: str) -> SensorReading:
    """Parse a ``$CSAGD,AX,AY,AZ,GX,GY,GZ,T*CC`` sentence."""
    talker, fields = _split_sentence(line)
    if talker != "CSAGD" or len(fields) != 7:
        raise MessageFormatError(f"not a $CSAGD sensor message: {line!r}")
    ax, ay, az, gx, gy, gz, temp = _parse_floats(fields, line)
    return SensorReading(ax, ay, az, gx, gy, gz, temp)


def max_refresh_rate_hz() -> int:
    """The device's highest selectable output data rate, in Hz."""
    return max(DATA_RATES_HZ)


def min_refresh_period_s() -> float:
    """The shortest period between messages at the device's maximum output data rate."""
    return 1.0 / max_refresh_rate_hz()


def _validate_unit(unit: int) -> None:
    """Raise MessageFormatError unless `unit` is a valid device unit number (1-9)."""
    if not 1 <= unit <= 9:
        raise MessageFormatError(f"unit number out of range (1-9): {unit}")


def build_set_data_rate_command(rate_hz: int, unit: int = 1) -> bytes:
    """The ``[nDxxx<cr>`` command bytes to set the output data rate, for `unit` (1-9)."""
    _validate_unit(unit)
    if rate_hz not in DATA_RATES_HZ:
        raise UnsupportedDataRateError(f"{rate_hz} Hz is not one of {DATA_RATES_HZ}")
    return f"[{unit}D{rate_hz}\r".encode("ascii")


def build_set_gyro_output_command(enabled: bool, unit: int = 1) -> bytes:
    """The ``[nGx<cr>`` command bytes to enable/disable gyroscope output, for `unit` (1-9)."""
    _validate_unit(unit)
    flag = 1 if enabled else 0
    return f"[{unit}G{flag}\r".encode("ascii")


def parse_set_data_rate_response(line: str) -> int:
    """The confirmed data rate (Hz) from a ``>New Output Data Rate: ddd`` response."""
    stripped = line.strip()
    prefix = ">New Output Data Rate:"
    if not stripped.startswith(prefix):
        raise MessageFormatError(f"not a data rate confirmation: {line!r}")
    value = stripped[len(prefix) :].strip()
    try:
        return int(value)
    except ValueError as exc:
        raise MessageFormatError(f"non-numeric data rate in: {line!r}") from exc


def parse_gyro_output_response(line: str) -> bool:
    """The confirmed gyro output state from a ``>Gyro Output: On``/``Off`` response."""
    stripped = line.strip()
    prefix = ">Gyro Output:"
    if not stripped.startswith(prefix):
        raise MessageFormatError(f"not a gyro output confirmation: {line!r}")
    value = stripped[len(prefix) :].strip().lower()
    if value == "on":
        return True
    if value == "off":
        return False
    raise MessageFormatError(f"non boolean gyro output state in: {line!r}")
