"""Controls the iPhone's simulated location through the pymobiledevice3 CLI.

Setting a location starts a long-running `simulate-location set` process; the
fake location stays active only while that process (and the tunnel) is alive.
"""

import shutil
import subprocess
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

MIN_LAT, MAX_LAT = -90.0, 90.0
MIN_LON, MAX_LON = -180.0, 180.0
CLEAR_TIMEOUT_SECONDS = 30
STOP_TIMEOUT_SECONDS = 5


class LocationError(Exception):
    """Raised with a user-friendly message when a location action fails."""


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float


def validate(lat: object, lon: object) -> Location:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        raise LocationError("Latitude and longitude must be numbers.")
    if not MIN_LAT <= lat_f <= MAX_LAT:
        raise LocationError("Latitude must be between -90 and 90.")
    if not MIN_LON <= lon_f <= MAX_LON:
        raise LocationError("Longitude must be between -180 and 180.")
    return Location(round(lat_f, 6), round(lon_f, 6))


def cli_path() -> str:
    path = shutil.which("pymobiledevice3")
    if not path:
        raise LocationError("pymobiledevice3 is not installed. Run ./run.sh to set it up.")
    return path


def set_command(cli: str, loc: Location) -> List[str]:
    # "--tunnel ''" uses the tunneld service (needed on iOS 17+).
    return [cli, "developer", "dvt", "simulate-location", "set", "--tunnel", "",
            "--", str(loc.lat), str(loc.lon)]


def clear_command(cli: str) -> List[str]:
    return [cli, "developer", "dvt", "simulate-location", "clear", "--tunnel", ""]


class LocationController:
    def __init__(self, popen: Callable = subprocess.Popen, run: Callable = subprocess.run,
                 cli_finder: Callable[[], str] = cli_path):
        self._popen = popen
        self._run = run
        self._cli_finder = cli_finder
        self._lock = threading.Lock()
        self._proc = None
        self._current: Optional[Location] = None

    @property
    def current(self) -> Optional[Location]:
        if self._proc is not None and self._proc.poll() is not None:
            # Process died (phone unplugged, tunnel dropped) -> real location is back.
            self._proc, self._current = None, None
        return self._current

    def set_location(self, lat: object, lon: object) -> Location:
        loc = validate(lat, lon)
        with self._lock:
            self._stop_process()
            proc = self._popen(set_command(self._cli_finder(), loc),
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            try:
                proc.wait(timeout=STOP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                # Still running after a few seconds = location is being held. Success.
                self._proc, self._current = proc, loc
                return loc
            # Exited early: either an error or an older iOS where "set" returns at once.
            err = (proc.stderr.read() if proc.stderr else "") or ""
            if proc.returncode != 0:
                raise LocationError(friendly_error(err))
            self._current = loc
            return loc

    def clear(self) -> None:
        with self._lock:
            self._stop_process()
            result = self._run(clear_command(self._cli_finder()), capture_output=True,
                               text=True, timeout=CLEAR_TIMEOUT_SECONDS)
            self._current = None
            if result.returncode != 0:
                raise LocationError(friendly_error(result.stderr or ""))

    def _stop_process(self) -> None:
        if self._proc is None:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=STOP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None


def friendly_error(stderr: str) -> str:
    text = stderr.lower()
    if "developer mode" in text:
        return "Developer Mode is off. Turn it on: Settings > Privacy & Security > Developer Mode."
    if "nodeviceconnected" in text or "not connected" in text or "no device" in text:
        return ("iPhone not connected. Plug it in with a cable that carries data, unlock it, "
                "tap 'Trust This Computer', then try again.")
    if "tunnel" in text or "rsd" in text:
        return "Can't reach the phone's tunnel. Make sure run.sh is running (it starts tunneld)."
    return "Couldn't change location: " + error_line(stderr)


def error_line(stderr: str) -> str:
    """Pick the most informative line: the last one naming an error, not the trailing log hint."""
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    errors = [line for line in lines if "error" in line.lower() or "exception" in line.lower()]
    return (errors or lines or ["unknown error"])[-1]
