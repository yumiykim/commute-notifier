import os
from django.core.management.base import BaseCommand, CommandError
from commute.discord import send_message

class Command(BaseCommand):
    help = "설정한 웹훅에 열차 시각 없는 연결 확인 메시지를 한 번 보냅니다."

    def handle(self, *args, **options):
        try:
            send_message(os.getenv("DISCORD_WEBHOOK_URL", ""), "등교 열차 알리미 연결 확인 ✅\n실제 시간표 안내는 아직 활성화되지 않았습니다.")
        except (ValueError, RuntimeError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write("연결 확인 메시지를 보냈습니다.")
