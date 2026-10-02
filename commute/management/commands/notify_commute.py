import os
from datetime import date, datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from commute.calendar import SEOUL, target_day, load_calendar, day_settings
from commute.delivery import DeliveryLedger
from commute.discord import send_message
from commute.messages import build_message
from commute.planner import plan
from commute.seoul import SeoulClient, SeoulError

class Command(BaseCommand):
    help = "실제 시간표 계산. 기본은 미리보기이며 --send를 지정해야 디스코드에 발송합니다."

    def add_arguments(self, parser):
        parser.add_argument("--slot", choices=["morning", "evening"], required=True)
        parser.add_argument("--date", help="조회할 등교일 YYYY-MM-DD. 생략하면 슬롯 기준 자동 결정")
        parser.add_argument("--send", action="store_true")
        parser.add_argument("--scheduled", action="store_true", help="예약 실행 지연 감지")

    def handle(self, *args, **options):
        try:
            now = datetime.now(SEOUL)
            if options["scheduled"]:
                slot = options["slot"]
                if (slot == "evening" and 6 <= now.hour < 20) or (slot == "morning" and (now.hour < 6 or now.hour >= 13)):
                    raise CommandError("예약 실행이 허용 시간대를 벗어나 잘못된 날짜 안내를 방지하기 위해 중단합니다.")
            day = date.fromisoformat(options["date"]) if options["date"] else target_day(now, options["slot"], options["scheduled"])
            config = load_calendar(settings.BASE_DIR / "calendar.json")
            start, week_tag = day_settings(day, config)
            if start is None:
                self.stdout.write(f"{day}: 주말·공휴일·휴강일로 발송 생략")
                return
            deadline = start - 600
            if options["send"] and (day < now.date() or (day == now.date() and now.hour * 3600 + now.minute * 60 + now.second >= deadline)):
                raise CommandError("도착 마감이 지난 등교 안내는 발송하지 않습니다.")
            ledger = DeliveryLedger(settings.BASE_DIR / ".state" / "deliveries.json")
            delivery_key = f"{day}:{options['slot']}"
            if options["send"] and delivery_key in ledger.entries:
                self.stdout.write("이미 발송했거나 발송 여부가 불확실한 안내: 재발송 생략")
                return
            client = SeoulClient(os.getenv("SEOUL_API_KEY", ""), os.getenv("ALLOW_HTTP_SEOUL", "false").lower() == "true")
            first, second = client.route(week_tag)
            latest = plan(first, second, deadline)
            recommended = plan(first, second, deadline - 180)
            content = build_message(day, start, recommended[0] if recommended else None,
                                    latest[0] if latest else None, datetime.now(SEOUL), options["slot"])
            self.stdout.write(content)
            if options["send"]:
                if not os.getenv("DISCORD_WEBHOOK_URL"):
                    raise CommandError("DISCORD_WEBHOOK_URL을 설정하세요.")
                if not ledger.reserve(delivery_key):
                    return
                send_message(os.getenv("DISCORD_WEBHOOK_URL"), content)
                ledger.mark_sent(delivery_key)
                self.stdout.write("디스코드 발송 완료")
        except (SeoulError, ValueError, OSError, RuntimeError) as error:
            raise CommandError(str(error)) from None
