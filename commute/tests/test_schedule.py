from datetime import datetime, date
from io import StringIO
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import json

from django.core.management import call_command
from django.test import override_settings
from commute.calendar import SEOUL, scheduled_slot, target_day
from commute.planner import Leg


class ScheduleTests(TestCase):
    def test_due_windows_and_midnight(self):
        for hour, expected in [(0, "evening"), (5, "evening"), (6, "morning"),
                               (12, "morning"), (13, None), (19, None), (20, "evening")]:
            with self.subTest(hour=hour):
                now = datetime(2026, 10, 6, hour, tzinfo=SEOUL)
                self.assertEqual(scheduled_slot(now), expected)
        now = datetime(2026, 10, 6, 0, 44, tzinfo=SEOUL)
        self.assertEqual(target_day(now, scheduled_slot(now), scheduled=True), date(2026, 10, 6))

    def run_auto(self, now, folder, client, sender):
        base = Path(folder)
        (base / "commute.json").write_text(json.dumps({'measurement_date': '2026-10-07', 'applied_date': '2026-10-07', 'home_to_entrance_seconds': 600, 'entrance_to_platform_seconds': 120, 'early_train_seconds': 120, 'preferred_transfer_seconds': 210, 'comparison_transfer_seconds': 120, 'exit_walk_seconds': 120}), encoding="utf-8")
        (base / "calendar.json").write_text("{}", encoding="utf-8")
        (base / "semester.json").write_text(json.dumps({"name": "26-2", "weekly_classes":
            {str(i): "13:00:00" if i == 4 else "10:00:00" if i < 4 else None for i in range(7)}}), encoding="utf-8")
        module = "commute.management.commands.notify_commute"
        out = StringIO()
        with override_settings(BASE_DIR=base), patch(module + ".datetime") as clock, \
                patch(module + ".SeoulClient", client), patch(module + ".send_message", sender), \
                patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/fake"}):
            clock.now.return_value = now
            call_command("notify_commute", slot="auto", send=True, stdout=out)
        return out.getvalue()

    def test_late_evening_sent_once_with_today_title(self):
        from unittest.mock import MagicMock
        client, sender = MagicMock(), MagicMock()
        client.return_value.route.return_value = ([Leg("5", 9*3600, 9*3600+600)],
                                                 [Leg("3", 9*3600+900, 9*3600+1200)])
        with TemporaryDirectory() as folder:
            now = datetime(2026, 10, 6, 0, 44, tzinfo=SEOUL)
            self.run_auto(now, folder, client, sender)
            self.run_auto(now, folder, client, sender)
            sender.assert_called_once()
            self.assertIn("오늘 10/6(화)", sender.call_args.args[1])
            records = json.loads((Path(folder) / ".state/deliveries.json").read_text())
            self.assertEqual(records, {"2026-10-06:evening": "sent"})

    def test_expired_morning_and_holiday_do_not_query_or_send(self):
        from unittest.mock import MagicMock
        for now in [datetime(2026, 10, 6, 9, 50, tzinfo=SEOUL),
                    datetime(2026, 10, 5, 6, tzinfo=SEOUL),
                    datetime(2026, 10, 6, 19, tzinfo=SEOUL)]:
            with self.subTest(now=now), TemporaryDirectory() as folder:
                client, sender = MagicMock(), MagicMock()
                self.run_auto(now, folder, client, sender)
                client.assert_not_called()
                sender.assert_not_called()

    def test_morning_is_separate_from_evening(self):
        from unittest.mock import MagicMock
        client, sender = MagicMock(), MagicMock()
        client.return_value.route.return_value = ([Leg("5", 9*3600, 9*3600+600)],
                                                 [Leg("3", 9*3600+900, 9*3600+1200)])
        with TemporaryDirectory() as folder:
            self.run_auto(datetime(2026, 10, 6, 0, 44, tzinfo=SEOUL), folder, client, sender)
            self.run_auto(datetime(2026, 10, 6, 6, 17, tzinfo=SEOUL), folder, client, sender)
            self.assertEqual(sender.call_count, 2)
