import os
from datetime import date, datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from commute.calendar import SEOUL, day_settings, load_calendar, load_semester
from commute.discord import send_message
from commute.messages import build_message
from commute.planner import plan
from commute.seoul import SeoulClient

class Command(BaseCommand):
    help = "개인 채널에 연결 확인 또는 표시 확인용 메시지를 한 번 보냅니다."

    def add_arguments(self, parser):
        parser.add_argument("--example", action="store_true", help="실제 시간표로 표시 확인용 예시를 발송")
        parser.add_argument("--date", help="예시 등교일 YYYY-MM-DD (기본: 오늘)")

    def handle(self, *args, **options):
        try:
            content = "등교 열차 알리미 연결 확인 ✅"
            if options["example"]:
                day = date.fromisoformat(options["date"]) if options["date"] else datetime.now(SEOUL).date()
                semester = load_semester(settings.BASE_DIR / "semester.json")
                calendar = load_calendar(settings.BASE_DIR / "calendar.json")
                start, tag = day_settings(day, calendar, semester)
                if start is None:
                    raise ValueError("예시 등교일에 수업이 없습니다. --date로 수업 날짜를 지정하세요.")
                client = SeoulClient(os.getenv("SEOUL_API_KEY", ""), os.getenv("ALLOW_HTTP_SEOUL", "false").lower() == "true")
                first, second = client.route(tag)
                cases = {}
                for minutes in (3, 2):
                    journeys = plan(first, second, start - 600, transfer_seconds=minutes * 60)
                    cases[minutes] = journeys[0] if journeys else None
                content = "-# 테스트 메시지 · 표시 확인용\n\n" + build_message(day, semester["name"], cases, datetime.now(SEOUL), "morning")
            send_message(os.getenv("DISCORD_WEBHOOK_URL", ""), content)
        except (ValueError, RuntimeError, OSError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write("디스코드 테스트 메시지를 한 번 보냈습니다.")
