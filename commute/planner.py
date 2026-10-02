"""시간표 공급자와 독립적인 고정 경로 계산. 시간은 당일 자정부터 초 단위."""
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Leg:
    train_id: str
    departure: int
    arrival: int
    destination: str = ""

    def __post_init__(self):
        if self.departure < 0 or self.arrival < self.departure:
            raise ValueError("열차 출발·도착 시간이 올바르지 않습니다.")

@dataclass(frozen=True)
class Journey:
    line5: Leg
    line3: Leg
    exit_arrival: int

def class_start(day: date, weekly_classes: dict) -> int | None:
    value = weekly_classes.get(str(day.weekday()))
    if value is None:
        return None
    hours, minutes, secs = map(int, value.split(":"))
    return hours * 3600 + minutes * 60 + secs

def plan(line5: list[Leg], line3: list[Leg], deadline: int,
         transfer_seconds: int = 180, exit_seconds: int = 120) -> list[Journey]:
    if min(transfer_seconds, exit_seconds) < 0:
        raise ValueError("도보 시간은 음수일 수 없습니다.")
    journeys = []
    for first in line5:
        connections = [second for second in line3
                       if first.arrival + transfer_seconds <= second.departure
                       and second.arrival + exit_seconds <= deadline]
        if connections:
            second = min(connections, key=lambda leg: (leg.arrival, leg.departure))
            journeys.append(Journey(first, second, second.arrival + exit_seconds))
    return sorted(journeys, key=lambda journey: (-journey.line5.departure, journey.exit_arrival))

def clock(seconds: int) -> str:
    return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02}"
