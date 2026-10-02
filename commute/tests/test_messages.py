from datetime import date, datetime
from unittest import TestCase
from commute.calendar import SEOUL
from commute.messages import build_message
from commute.planner import Journey, Leg

def journey(departure):
    return Journey(Leg("5", departure, 45000), Leg("3", 45720, 45870), 45990)

class MessageTests(TestCase):
    def render(self, cases):
        return build_message(date(2026, 10, 2), "26-2", cases,
                             datetime(2026, 10, 2, 6, tzinfo=SEOUL), "morning")

    def test_equal_departures_show_one_summary(self):
        message = self.render({3: journey(44550), 2: journey(44550)})
        self.assertIn("⏰ **마포역 5호선 · 12:22:30 탑승**", message)
        self.assertNotIn("늦게 탑승 가능", message)
        self.assertIn("**🚶 환승 도보 3분**", message)
        self.assertIn("**🏃 환승 도보 2분**", message)

    def test_different_departures_show_time_gain(self):
        message = self.render({3: journey(44550), 2: journey(44940)})
        self.assertIn("걸으면 12:22:30 · 뛰면 12:29:00", message)
        self.assertIn("6분 30초 늦게 탑승 가능", message)

    def test_only_one_viable_condition_is_labeled(self):
        message = self.render({3: None, 2: journey(44940)})
        self.assertIn("12:29:00 탑승 (🏃 2분 환승)", message)
        self.assertNotIn("늦게 탑승 가능", message)

    def test_no_viable_condition_does_not_invent_time(self):
        message = self.render({3: None, 2: None})
        self.assertIn("도착 마감에 맞는 열차가 없습니다", message)
        self.assertNotIn("탑승**", message)
