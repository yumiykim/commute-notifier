import json
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import holidays
from commute.planner import class_start

SEOUL = ZoneInfo("Asia/Seoul")

def target_day(now, slot, scheduled=False):
    local = now.astimezone(SEOUL)
    today = local.date()
    if scheduled and slot == "evening" and local.hour < 6:
        return today
    return today + timedelta(days=1 if slot == "evening" else 0)

def load_calendar(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    for field in ("skip_dates", "extra_holidays", "class_overrides"):
        values = config.get(field, {})
        for item in values:
            date.fromisoformat(item)
    return config

def day_settings(day, config):
    holiday = day in holidays.KR(years=day.year) or day.isoformat() in config.get("extra_holidays", [])
    tag = 3 if holiday or day.weekday() == 6 else 2 if day.weekday() == 5 else 1
    if day.isoformat() in config.get("skip_dates", []):
        return None, tag
    override = config.get("class_overrides", {}).get(day.isoformat())
    if override:
        from commute.seoul import seconds
        return seconds(override), tag
    return (None if holiday else class_start(day)), tag
