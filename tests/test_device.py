import subprocess
from unittest.mock import MagicMock

import pytest

from spoofer.device import (Location, LocationController, LocationError,
                            clear_command, friendly_error, set_command, validate)
from spoofer.server import create_app


def make_proc(timeout=True, returncode=0, stderr=""):
    proc = MagicMock()
    if timeout:
        proc.wait.side_effect = [subprocess.TimeoutExpired("x", 5), None]
        proc.poll.return_value = None
    else:
        proc.wait.return_value = returncode
        proc.poll.return_value = returncode
    proc.returncode = returncode
    proc.stderr.read.return_value = stderr
    return proc


def controller(proc=None, run_rc=0):
    popen = MagicMock(return_value=proc or make_proc())
    run = MagicMock(return_value=MagicMock(returncode=run_rc, stderr=""))
    return LocationController(popen=popen, run=run, cli_finder=lambda: "pmd3"), popen, run


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181), ("x", 0), (None, 1)])
def test_validate_rejects_bad_coordinates(lat, lon):
    with pytest.raises(LocationError):
        validate(lat, lon)


def test_validate_accepts_and_rounds():
    assert validate("40.1234567", -74) == Location(40.123457, -74.0)


def test_commands_use_tunnel_and_separator():
    assert set_command("pmd3", Location(1.5, -2.5))[-3:] == ["--", "1.5", "-2.5"]
    assert "--tunnel" in clear_command("pmd3")


def test_set_location_holds_running_process():
    ctl, popen, _ = controller()
    loc = ctl.set_location(10, 20)
    assert ctl.current == loc
    popen.assert_called_once()


def test_set_location_replaces_previous_process():
    first, second = make_proc(), make_proc()
    ctl, popen, _ = controller()
    popen.side_effect = [first, second]
    ctl.set_location(1, 1)
    ctl.set_location(2, 2)
    first.terminate.assert_called_once()
    assert ctl.current == Location(2, 2)


def test_set_location_reports_failure():
    ctl, _, _ = controller(make_proc(timeout=False, returncode=1, stderr="Developer Mode is disabled"))
    with pytest.raises(LocationError, match="Developer Mode"):
        ctl.set_location(1, 1)
    assert ctl.current is None


def test_current_resets_when_process_dies():
    proc = make_proc()
    ctl, _, _ = controller(proc)
    ctl.set_location(1, 1)
    proc.poll.return_value = 1
    assert ctl.current is None


def test_clear_stops_process_and_runs_clear():
    proc = make_proc()
    ctl, _, run = controller(proc)
    ctl.set_location(1, 1)
    ctl.clear()
    proc.terminate.assert_called_once()
    run.assert_called_once()
    assert ctl.current is None


def test_friendly_error_fallback():
    assert friendly_error("line1\nboom") == "Couldn't change location: boom"


def test_friendly_error_detects_disconnected_phone():
    stderr = ("pymobiledevice3.exceptions.NoDeviceConnectedError: Device is not connected.\n"
              "INFO Run again with -v for the full traceback")
    assert "iPhone not connected" in friendly_error(stderr)


def test_friendly_error_prefers_error_line_over_log_hint():
    stderr = "ValueError: bad thing\nINFO Run again with -v for the full traceback"
    assert friendly_error(stderr) == "Couldn't change location: ValueError: bad thing"


def test_server_endpoints():
    ctl, _, _ = controller()
    client = create_app(ctl).test_client()
    assert client.get("/status").json["data"]["spoofing"] is False
    res = client.post("/location", json={"lat": 5, "lon": 6})
    assert res.json["ok"] and res.json["data"]["lat"] == 5
    bad = client.post("/location", json={"lat": 500, "lon": 6})
    assert bad.status_code == 400 and not bad.json["ok"]
    assert client.post("/clear").json["data"]["spoofing"] is False
