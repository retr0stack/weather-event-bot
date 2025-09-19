from datetime import datetime
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder

TF = TimezoneFinder()

def detect_timezone_name(lat: float, lon: float) -> str:
    return TF.timezone_at(lat=lat, lng=lon) or "UTC"

def tz_now(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))
