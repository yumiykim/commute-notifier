import json
from datetime import date
from pathlib import Path
from django.conf import settings
from commute.calendar import load_semester, load_calendar, day_settings
from django.core.management.base import BaseCommand, CommandError
from commute.planner import Leg, class_start, plan, clock

class Command(BaseCommand):
    help = "명시적으로 지정한 예시 시간표로 계산만 합니다. 실제 운행 정보가 아니며 발송하지 않습니다."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", required=True)
        parser.add_argument("--date", required=True)

    def handle(self, *args, **options):
        try:
            day = date.fromisoformat(options["date"])
            data = json.loads(Path(options["fixture"]).read_text(encoding="utf-8"))
            semester = load_semester(settings.BASE_DIR / "semester.json")
            calendar = load_calendar(settings.BASE_DIR / "calendar.json")
            start, _ = day_settings(day, calendar, semester)
            if start is None:
                self.stdout.write("수업 없는 날: 등교 안내 없음")
                return
            first = [Leg(**row) for row in data["line5"]]
            second = [Leg(**row) for row in data["line3"]]
            cases = [(minutes, plan(first, second, start - 600, transfer_seconds=minutes * 60)) for minutes in (3, 2)]
        except (ValueError, OSError, KeyError, TypeError):
            raise CommandError("날짜 또는 예시 시간표 파일을 확인하세요.") from None
        self.stdout.write("[예시 데이터 · 실제 탑승에 사용 금지]")
        for minutes, candidates in cases:
            label = f"환승 도보 {minutes}분"
            if not candidates:
                self.stdout.write(f"{label}: 가능한 조합 없음")
                continue
            result = candidates[0]
            self.stdout.write(f"{label}: 마포 {clock(result.line5.departure)} / 종로3가 3호선 {clock(result.line3.departure)} / 출구 {clock(result.exit_arrival)}")
