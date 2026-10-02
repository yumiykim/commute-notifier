from datetime import date
from unittest import TestCase
from commute.planner import Leg, class_start, plan

class PlannerTests(TestCase):
    def test_transfer_boundary(self):
        first = [Leg("5", 0, 600)]
        second = [Leg("too-early", 779, 1000), Leg("connect", 780, 1100)]
        result = plan(first, second, 1220)
        self.assertEqual(result[0].line3.train_id, "connect")

    def test_exit_deadline(self):
        self.assertEqual(plan([Leg("5", 0, 600)], [Leg("3", 780, 1101)], 1220), [])

    def test_latest_departure_is_selected(self):
        result = plan([Leg("early", 0, 600), Leg("late", 60, 660)], [Leg("3", 900, 1100)], 1220)
        self.assertEqual(result[0].line5.train_id, "late")

    def test_weekly_schedule(self):
        self.assertEqual(class_start(date(2026, 10, 5)), 36000)
        self.assertEqual(class_start(date(2026, 10, 2)), 46800)
        self.assertIsNone(class_start(date(2026, 10, 3)))
