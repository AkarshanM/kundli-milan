"""Place lookup (free Open-Meteo geocoding, no API key) and conversion of a
local birth time to UTC using the IANA timezone database's history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

import requests

from .i18n import M, Msg

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
    offset_source: str              # "tzdb" | "manual"
    notes: list[Msg] = field(default_factory=list)

    @property
    def offset_label(self) -> str:
        return format_offset(self.utc_offset)


def resolve_local_time(d: date, t: time, tz_name: str,
                       override: timedelta | None = None) -> ResolvedTime:
    naive = datetime.combine(d, t)
    notes: list[str] = []

    if override is not None:
        offset = override
        source = "manual"
    else:
        tz = ZoneInfo(tz_name)
        first = naive.replace(tzinfo=tz, fold=0)
        second = naive.replace(tzinfo=tz, fold=1)
        offset = first.utcoffset()
        source = "tzdb"
        if first.utcoffset() != second.utcoffset():
            back = first.astimezone(timezone.utc).astimezone(tz)
            if back.replace(tzinfo=None) != naive:
                notes.append(M("tz_gap", off=format_offset(offset)))
            else:
                notes.append(M("tz_fold", off=format_offset(offset),
                               off2=format_offset(second.utcoffset())))

    utc = (naive - offset).replace(tzinfo=timezone.utc)

    if source == "tzdb":
        if d.year < 1970:
            notes.append(M("tz_pre1970"))
        if tz_name == "Asia/Kolkata" and d.year < 1956:
            notes.append(M("tz_india_local"))
        if tz_name == "Asia/Kolkata" and offset == timedelta(hours=6, minutes=30):
            notes.append(M("tz_war_time"))

    return ResolvedTime(local=naive, tz_name=tz_name, utc_offset=offset,
                        utc=utc, offset_source=source, notes=notes)


def local_day_bounds_utc(d: date, offset: timedelta) -> tuple[datetime, datetime]:
    start = (datetime.combine(d, time(0, 0)) - offset).replace(tzinfo=timezone.utc)
    return start, start + timedelta(hours=23, minutes=59)
