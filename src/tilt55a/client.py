"""A client for the TILT-55A speaking its documented ASCII protocol over a transport."""

from __future__ import annotations

from typing import Protocol

from tilt55a.messages import (
    InclinometerReading,
    SensorReading,
    build_set_data_rate_command,
    build_set_gyro_output_command,
    max_refresh_rate_hz,
    parse_gyro_output_response,
    parse_inclinometer_message,
    parse_sensor_message,
    parse_set_data_rate_response,
)


class Transport(Protocol):
    """What TiltClient needs from a connection: write bytes, read one line."""

    def write(self, data: bytes) -> None: ...

    def readline(self) -> bytes: ...


class TiltClient:
    """Reads sensor data from, and configures, a TILT-55A over `transport`."""

    def __init__(self, transport: Transport, unit: int = 1) -> None:
        self._transport = transport
        self._unit = unit

    def read_inclinometer(self) -> InclinometerReading:
        """Read and parse one ``$CSTLT`` inclinometer message."""
        return parse_inclinometer_message(self._read_line())

    def read_sensor_data(self) -> SensorReading:
        """Read and parse one ``$CSAGD`` sensor message."""
        return parse_sensor_message(self._read_line())

    def set_data_rate_hz(self, rate_hz: int) -> int:
        """Set the output data rate and return the rate the device confirms."""
        self._transport.write(build_set_data_rate_command(rate_hz, self._unit))
        return parse_set_data_rate_response(self._read_line())

    def run_at_max_refresh_rate(self) -> int:
        """Configure the device for its maximum output data rate; return it in Hz."""
        return self.set_data_rate_hz(max_refresh_rate_hz())

    def set_gyro_output(self, enabled: bool) -> bool:
        """Enable/disable gyroscope output and return the state the device confirms."""
        self._transport.write(build_set_gyro_output_command(enabled, self._unit))
        return parse_gyro_output_response(self._read_line())

    def _read_line(self) -> str:
        return self._transport.readline().decode("ascii")
