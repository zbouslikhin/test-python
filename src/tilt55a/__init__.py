"""Client for the CTi TILT-55A dynamic inclinometer's documented ASCII protocol.

The device (per its datasheet) communicates over a simple ASCII/NMEA-0183-like serial
protocol, not Modbus: ``$CSTLT``/``$CSAGD`` data sentences and ``[n...`` configuration
commands. This package parses that protocol and drives it through a small transport.
"""

from tilt55a.client import TiltClient, Transport
from tilt55a.messages import (
    ChecksumError,
    InclinometerReading,
    MessageFormatError,
    SensorReading,
    UnsupportedDataRateError,
    build_set_data_rate_command,
    build_set_gyro_output_command,
    compute_checksum,
    max_refresh_rate_hz,
    min_refresh_period_s,
    parse_gyro_output_response,
    parse_inclinometer_message,
    parse_sensor_message,
    parse_set_data_rate_response,
)

__all__ = [
    "ChecksumError",
    "InclinometerReading",
    "MessageFormatError",
    "SensorReading",
    "TiltClient",
    "Transport",
    "UnsupportedDataRateError",
    "build_set_data_rate_command",
    "build_set_gyro_output_command",
    "compute_checksum",
    "max_refresh_rate_hz",
    "min_refresh_period_s",
    "parse_gyro_output_response",
    "parse_inclinometer_message",
    "parse_sensor_message",
    "parse_set_data_rate_response",
]
