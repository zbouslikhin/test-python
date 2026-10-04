import pytest

from tilt55a.messages import (
    ChecksumError,
    MessageFormatError,
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

# Worked examples straight from the TILT-55A datasheet (section 5).
DATASHEET_SENTENCES = [
    "$CSTLT,-0013.55,-0003.93,+0988.68,-000.785,-000.228,+032.0*53",
    "$CSTLT,-0013.5,-0003.7,+0988.4,-000.790,-000.219,+032.0*67",
    "$CSTLT,-0013,-0003,+0989,-000.79,-000.22,+032*6A",
]


def test_compute_checksum_matches_the_datasheets_worked_examples() -> None:
    assert compute_checksum("CSTLT,-0013.55,-0003.93,+0988.68,-000.785,-000.228,+032.0") == 0x53


@pytest.mark.parametrize("sentence", DATASHEET_SENTENCES)
def test_parse_inclinometer_message_reads_the_datasheet_examples(sentence: str) -> None:
    reading = parse_inclinometer_message(sentence)
    assert reading.temperature_c == pytest.approx(32.0, abs=0.1)
    assert reading.roll_deg < 0


def test_parse_inclinometer_message_rejects_a_tampered_checksum() -> None:
    tampered = DATASHEET_SENTENCES[0].replace("*53", "*54")
    with pytest.raises(ChecksumError):
        parse_inclinometer_message(tampered)


def test_parse_inclinometer_message_rejects_a_sensor_message() -> None:
    sensor_sentence = "$CSAGD,-1,-2,+988,0.1,0.2,0.3,+032.0"
    checksum = compute_checksum(sensor_sentence[1:])
    with pytest.raises(MessageFormatError):
        parse_inclinometer_message(f"{sensor_sentence}*{checksum:02X}")


def test_parse_inclinometer_message_rejects_malformed_input() -> None:
    with pytest.raises(MessageFormatError):
        parse_inclinometer_message("not a sentence at all")


def test_parse_inclinometer_message_rejects_non_numeric_fields() -> None:
    body = "CSTLT,bad,-0003.93,+0988.68,-000.785,-000.228,+032.0"
    sentence = f"${body}*{compute_checksum(body):02X}"
    with pytest.raises(MessageFormatError):
        parse_inclinometer_message(sentence)


def test_parse_sensor_message_reads_accelerometer_and_gyroscope_data() -> None:
    body = "CSAGD,-13.5,-3.9,988.6,0.1,-0.2,0.3,+032.0"
    sentence = f"${body}*{compute_checksum(body):02X}"
    reading = parse_sensor_message(sentence)
    assert reading.gyro_z_dps == pytest.approx(0.3)
    assert reading.temperature_c == pytest.approx(32.0)


def test_max_refresh_rate_and_min_refresh_period_match_the_datasheet() -> None:
    assert max_refresh_rate_hz() == 400
    assert min_refresh_period_s() == pytest.approx(0.0025)


def test_build_set_data_rate_command_formats_the_configuration_command() -> None:
    assert build_set_data_rate_command(400, unit=1) == b"[1D400\r"


def test_build_set_data_rate_command_rejects_an_unsupported_rate() -> None:
    with pytest.raises(UnsupportedDataRateError):
        build_set_data_rate_command(300)


def test_build_set_data_rate_command_rejects_an_out_of_range_unit() -> None:
    with pytest.raises(MessageFormatError):
        build_set_data_rate_command(400, unit=10)


def test_parse_set_data_rate_response_reads_the_confirmed_rate() -> None:
    assert parse_set_data_rate_response(">New Output Data Rate: 400\r\n") == 400


def test_parse_set_data_rate_response_rejects_an_unrelated_line() -> None:
    with pytest.raises(MessageFormatError):
        parse_set_data_rate_response(">Firmware Version:1.19")


def test_build_set_gyro_output_command_formats_the_enable_command() -> None:
    assert build_set_gyro_output_command(True, unit=1) == b"[1G1\r"


def test_build_set_gyro_output_command_formats_the_disable_command() -> None:
    assert build_set_gyro_output_command(False, unit=1) == b"[1G0\r"


def test_build_set_gyro_output_command_rejects_an_out_of_range_unit() -> None:
    with pytest.raises(MessageFormatError):
        build_set_gyro_output_command(True, unit=10)


def test_parse_gyro_output_response_reads_the_enabled_state() -> None:
    assert parse_gyro_output_response(">Gyro Output: On\r\n") is True


def test_parse_gyro_output_response_reads_the_disabled_state() -> None:
    assert parse_gyro_output_response(">Gyro Output: Off\r\n") is False


def test_parse_gyro_output_response_rejects_an_unrelated_line() -> None:
    with pytest.raises(MessageFormatError):
        parse_gyro_output_response(">Firmware Version:1.19")


def test_parse_gyro_output_response_rejects_a_non_boolean_state() -> None:
    with pytest.raises(MessageFormatError):
        parse_gyro_output_response(">Gyro Output: Maybe")
