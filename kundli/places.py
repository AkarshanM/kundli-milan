"""Place lookup (free Open-Meteo geocoding, no API key) and conversion of a
local birth time to UTC using the IANA timezone database's history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass(frozen=True)
class Place:
    name: str
    admin1: str
    country: str
    latitude: float
    longitude: float
    timezone: str

    @property
    def label(self) -> str:
        parts = [self.name, self.admin1, self.country]
        where = ", ".join(p for p in parts if p)
        return f"{where}  ({self.latitude:.3f}, {self.longitude:.3f})"


def search_places(query: str, count: int = 10) -> list[Place]:
    resp = requests.get(
        GEOCODE_URL,
        params={"name": query, "count": count, "language": "en",
                "format": "json"},
        headers={"User-Agent": "kundli-milan-personal/1.0"},
        timeout=10,
    )
    resp.raise_for_status()
    out = []
    for r in resp.json().get("results") or []:
        if not r.get("timezone"):
            continue
        out.append(Place(
            name=r.get("name", ""),
            admin1=r.get("admin1", "") or "",
            country=r.get("country", "") or "",
            latitude=float(r["latitude"]),
            longitude=float(r["longitude"]),
            timezone=r["timezone"],
        ))
    return out


def all_timezones() -> list[str]:
    return sorted(available_timezones())


def format_offset(off: timedelta) -> str:
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"UTC{sign}{h:02d}:{m:02d}" + (f":{s:02d}" if s else "")


@dataclass
class ResolvedTime:
    local: datetime                 # naive local clock time as entered
    tz_name: str
    utc_offset: timedelta
    utc: datetime
    offset_source: str              # "timezone database" | "manual override"
    notes: list[str] = field(default_factory=list)

    @property
    def offset_label(self) -> str:
        return format_offset(self.utc_offset)


def resolve_local_time(d: date, t: time, tz_name: str,
                       override: timedelta | None = None) -> ResolvedTime:
    naive = datetime.combine(d, t)
    notes: list[str] = []

    if override is not None:
        offset = override
        source = "manual override"
    else:
        tz = ZoneInfo(tz_name)
        first = naive.replace(tzinfo=tz, fold=0)
        second = naive.replace(tzinfo=tz, fold=1)
        offset = first.utcoffset()
        source = "timezone database"
        if first.utcoffset() != second.utcoffset():
            back = first.astimezone(timezone.utc).astimezone(tz)
            if back.replace(tzinfo=None) != naive:
                notes.append(
                    "This clock time was skipped when clocks moved forward "
                    f"(daylight saving). Using {format_offset(offset)}; "
                    "override the offset if you know better.")
            else:
                notes.append(
                    "This clock time happened twice when clocks moved back "
                    f"(daylight saving). Using the first, {format_offset(offset)}; "
                    f"the second would be {format_offset(second.utcoffset())}. "
                    "Override the offset if needed.")

    utc = (naive - offset).replace(tzinfo=timezone.utc)

    if source == "timezone database":
        if d.year < 1970:
            notes.append(
                "Timezone records before 1970 are less reliable. Please "
                "double-check the UTC offset shown.")
        if tz_name == "Asia/Kolkata" and d.year < 1956:
            notes.append(
                "Before 1948 (Kolkata) and 1955 (Mumbai) those cities also "
                "kept local times: Calcutta Time UTC+05:53:20, Bombay Time "
                "UTC+04:51. If the birth was there and recorded in local "
                "time, set the offset manually.")
        if tz_name == "Asia/Kolkata" and offset == timedelta(hours=6, minutes=30):
            notes.append(
                "India used war time (UTC+06:30) in parts of 1941-1945. "
                "The database applies it here; confirm with family records "
                "if possible.")

    return ResolvedTime(local=naive, tz_name=tz_name, utc_offset=offset,
                        utc=utc, offset_source=source, notes=notes)


def local_day_bounds_utc(d: date, offset: timedelta) -> tuple[datetime, datetime]:
    start = (datetime.combine(d, time(0, 0)) - offset).replace(tzinfo=timezone.utc)
    return start, start + timedelta(hours=23, minutes=59)
