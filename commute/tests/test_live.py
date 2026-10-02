import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from commute.calendar import day_settings, target_day
from commute.delivery import DeliveryLedger
from commute.seoul import SeoulClient, SeoulError, join_trains, seconds

def row(train="5007", departure="09:00:30", arrival="09:11:00", destination="2566"):
    return {"TRAIN_NO": train, "LEFTTIME": departure, "ARRIVETIME": arrival,
            "ORIGINSTATION": "2511", "DESTSTATION": destination, "SUBWAYENAME": "하남검단산"}

class LiveTests(TestCase):
    def test_match_train_and_destination(self):
        result = join_trains([row(), row("5009")], [row(), row("5009", destination="2561")])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].departure, 32430)

    def test_duplicate_train_is_rejected(self):
        with self.assertRaises(SeoulError):
            join_trains([row()], [row(), row()])

    def test_invalid_time_is_rejected(self):
        with self.assertRaises(SeoulError):
            seconds("09:70:00")

    def test_holiday_override_uses_holiday_timetable(self):
        day = date(2026, 10, 9)
        self.assertEqual(day_settings(day, {}), (None, 3))
        self.assertEqual(day_settings(day, {"class_overrides": {"2026-10-09": "10:00:00"}}), (36000, 3))

    def test_skip_overrides_class(self):
        self.assertIsNone(day_settings(date(2026, 10, 6), {"skip_dates": ["2026-10-06"]})[0])

    def test_evening_crosses_year_boundary(self):
        now = datetime(2026, 12, 31, 11, tzinfo=timezone.utc)
        self.assertEqual(target_day(now, "evening"), date(2027, 1, 1))

    def test_pending_and_sent_both_block_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            ledger = DeliveryLedger(path)
            self.assertTrue(ledger.reserve("2026-10-06:morning"))
            self.assertFalse(DeliveryLedger(path).reserve("2026-10-06:morning"))
            ledger.mark_sent("2026-10-06:morning")
            self.assertFalse(DeliveryLedger(path).reserve("2026-10-06:morning"))
            self.assertTrue(ledger.reserve("2026-10-06:evening"))

    def test_transport_requires_explicit_consent(self):
        with self.assertRaises(SeoulError):
            SeoulClient("fake-test-key")

    def test_network_failure_does_not_leak_key(self):
        with patch("commute.seoul.urlopen", side_effect=URLError("url contains fake-test-key")):
            with self.assertRaises(SeoulError) as failure:
                SeoulClient("fake-test-key", allow_http=True).timetable("2529", 1)
        self.assertNotIn("fake-test-key", str(failure.exception))

    def test_wrong_direction_response_is_rejected(self):
        response = MagicMock()
        payload = {"SearchSTNTimeTableByIDService": {"RESULT": {"CODE": "INFO-000"}, "list_total_count": 1,
                   "row": [{"STATION_CD": "2529", "INOUT_TAG": "1", "WEEK_TAG": "1"}]}}
        with patch("commute.seoul.urlopen", return_value=response), patch("commute.seoul.json.load", return_value=payload):
            with self.assertRaises(SeoulError):
                SeoulClient("fake-test-key", allow_http=True).timetable("2529", 1)

    def test_delayed_evening_uses_same_commute_day(self):
        now = datetime(2026, 10, 5, 16, tzinfo=timezone.utc)  # 한국 10/6 01시
        self.assertEqual(target_day(now, "evening", scheduled=True), date(2026, 10, 6))
