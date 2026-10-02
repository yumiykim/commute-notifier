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

def day_settings(day, config, semester):
    holiday = day in holidays.KR(years=day.year) or day.isoformat() in config.get("extra_holidays", [])
    tag = 3 if holiday or day.weekday() == 6 else 2 if day.weekday() == 5 else 1
    if day.isoformat() in config.get("skip_dates", []):
        return None, tag
    override = config.get("class_overrides", {}).get(day.isoformat())
    if override:
        from commute.seoul import seconds
        return seconds(override), tag
    return (None if holiday else class_start(day, semester["weekly_classes"])), tag

def load_semester(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("name"), str) or not config["name"].strip():
        raise ValueError("semester.json에 학기 이름이 필요합니다.")
    weekly = config.get("weekly_classes")
    if not isinstance(weekly, dict) or set(weekly) != {str(day) for day in range(7)}:
        raise ValueError("weekly_classes에 월요일(0)~일요일(6) 설정이 필요합니다.")
    for value in weekly.values():
        if value is None:
            continue
        import re
        if not isinstance(value, str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]", value):
            raise ValueError("수업 시각은 HH:MM:SS 형식 또는 null이어야 합니다.")
        if value < "00:10:00":
            raise ValueError("현재 서비스는 자정 10분 이후 수업을 지원합니다.")
    return config
