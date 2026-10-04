from collections import deque

from tilt55a.client import TiltClient


class FakeTransport:
    """An in-memory stand-in for a serial connection: queued lines in, writes recorded."""

    def __init__(self, lines: list[bytes]) -> None:
        self._lines = deque(lines)
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def readline(self) -> bytes:
        return self._lines.popleft()


def test_read_inclinometer_parses_the_next_line() -> None:
    line = b"$CSTLT,-0013.55,-0003.93,+0988.68,-000.785,-000.228,+032.0*53\r\n"
    client = TiltClient(FakeTransport([line]))

    reading = client.read_inclinometer()

    assert reading.pitch_deg == -0.228
    assert reading.temperature_c == 32.0


def test_read_sensor_data_parses_the_next_line() -> None:
    body = "CSAGD,-13.5,-3.9,988.6,0.1,-0.2,0.3,+032.0"
    checksum = 0
    for byte in body.encode("ascii"):
        checksum ^= byte
    line = f"${body}*{checksum:02X}\r\n".encode("ascii")
    client = TiltClient(FakeTransport([line]))

    reading = client.read_sensor_data()

    assert reading.gyro_x_dps == 0.1


def test_set_data_rate_hz_writes_the_command_and_parses_the_confirmation() -> None:
    transport = FakeTransport([b">New Output Data Rate: 400\r\n"])
    client = TiltClient(transport, unit=1)

    confirmed = client.set_data_rate_hz(400)

    assert transport.written == [b"[1D400\r"]
    assert confirmed == 400


def test_run_at_max_refresh_rate_drives_the_device_to_400_hz() -> None:
    transport = FakeTransport([b">New Output Data Rate: 400\r\n"])
    client = TiltClient(transport)

    confirmed = client.run_at_max_refresh_rate()

    assert transport.written == [b"[1D400\r"]
    assert confirmed == 400


def test_set_gyro_output_enables_gyro_data() -> None:
    transport = FakeTransport([b">Gyro Output: On\r\n"])
    client = TiltClient(transport, unit=1)

    enabled = client.set_gyro_output(True)

    assert transport.written == [b"[1G1\r"]
    assert enabled is True


def test_set_gyro_output_disables_gyro_data() -> None:
    transport = FakeTransport([b">Gyro Output: Off\r\n"])
    client = TiltClient(transport, unit=1)

    enabled = client.set_gyro_output(False)

    assert transport.written == [b"[1G0\r"]
    assert enabled is False
