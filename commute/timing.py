"""현장 측정에 따른 이동 기준과 행동 시각. 열차 시각은 공식 시간표를 유지한다."""
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from commute.planner import plan

@dataclass(frozen=True)
class CommuteSettings:
    measurement_date: str
    applied_date: str
    home_to_entrance_seconds: int
    entrance_to_platform_seconds: int
    early_train_seconds: int
    preferred_transfer_seconds: int
    comparison_transfer_seconds: int
    exit_walk_seconds: int

def load_commute(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != set(CommuteSettings.__dataclass_fields__):
            raise ValueError
        for name in ("measurement_date", "applied_date"):
            date.fromisoformat(data[name])
        for name, value in data.items():
            if name.endswith("_seconds") and (type(value) is not int or not 0 < value <= 3600):
                raise ValueError
        if data["preferred_transfer_seconds"] <= data["comparison_transfer_seconds"]:
            raise ValueError
        return CommuteSettings(**data)
    except (TypeError, ValueError, KeyError):
        raise ValueError("commute.json의 항목·날짜·이동 시간을 확인하세요.") from None

def calculate_cases(first, second, deadline, settings):
    cases = {}
    for seconds in (settings.preferred_transfer_seconds, settings.comparison_transfer_seconds):
        candidates = plan(first, second, deadline, transfer_seconds=seconds, exit_seconds=settings.exit_walk_seconds)
        cases[seconds] = candidates[0] if candidates else None
    return cases

@dataclass(frozen=True)
class ActionTimes:
    home_departure: int
    entrance_arrival: int
    platform_ready: int

def action_times(departure, settings):
    platform = departure - settings.early_train_seconds
    entrance = platform - settings.entrance_to_platform_seconds
    return ActionTimes(entrance - settings.home_to_entrance_seconds, entrance, platform)

def minute_clock(seconds):
    # 자정 이전 행동 시각은 전날로 표시하고 항상 분 단위로 내린다.
    days, within_day = divmod(seconds, 86400)
    prefix = "전날 " if days < 0 else "다음 날 " if days > 0 else ""
    return f"{prefix}{within_day // 3600:02}:{within_day % 3600 // 60:02}"

def duration(seconds):
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}분" + (f" {remainder}초" if remainder else "")
