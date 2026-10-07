from datetime import date, datetime
from unittest import TestCase
from commute.calendar import SEOUL
from commute.messages import build_message
from commute.planner import Journey, Leg
from commute.timing import CommuteSettings

SETTINGS = CommuteSettings("2026-10-07", "2026-10-07", 600, 120, 120, 210, 120, 120)

def journey(departure=34080, transfer=34980):
    return Journey(Leg("5", departure, 34720), Leg("3", transfer, 35130), 35250)

class MessageTests(TestCase):
    def render(self, preferred, comparison):
        return build_message(date(2026, 10, 6), "26-2", {210: preferred, 120: comparison},
                             datetime(2026, 10, 6, 6, tzinfo=SEOUL), "morning", SETTINGS)

    def test_identical_route_still_shows_both_details_and_preferred_action_times(self):
        message = self.render(journey(), journey())
        self.assertIn("집 출발 09:14 · 마포역 3번출구 09:24까지", message)
        self.assertIn("승강장 탑승 준비 09:26까지", message)
        self.assertIn("공식 열차 시각 **09:28:00**", message)
        self.assertIn("기본 추천 · 환승 3분 30초", message)
        self.assertIn("빠른 환승 · 환승 2분", message)
        self.assertNotIn("가정", message)
        self.assertEqual(message.count("충무로역 1번출구"), 2)

    def test_different_routes_keep_both_details_and_base_summary_on_preferred(self):
        message = self.render(journey(33900), journey())
        self.assertIn("집 출발 09:11", message)
        self.assertIn("공식 열차 시각 **09:25:00**", message)
        self.assertEqual(message.count("충무로역 1번출구"), 2)
        self.assertIn("빠른 환승 · 환승 2분", message)

    def test_same_first_train_different_connection_is_not_collapsed(self):
        message = self.render(journey(34080, 35010), journey())
        self.assertEqual(message.count("충무로역 1번출구"), 2)
        self.assertNotIn("같은 열차·경로", message)

    def test_comparison_only_never_claims_preferred_action_times(self):
        message = self.render(None, journey())
        self.assertIn("빠른 환승 경로만 가능합니다", message)
        self.assertNotIn("집 출발", message)
        self.assertIn("빠른 환승 · 환승 2분", message)

    def test_no_viable_condition_does_not_invent_time(self):
        message = self.render(None, None)
        self.assertIn("도착 마감에 맞는 열차가 없습니다", message)
        self.assertNotIn("공식 열차 시각", message)

    def test_title_uses_commute_weekday_and_minimal_footer(self):
        message = self.render(journey(), journey())
        self.assertTrue(message.startswith("**오늘 10/6(화) 등교 안내 · 26-2**"))
        self.assertTrue(message.endswith("-# 최근 조회: 10/6 06:00"))
