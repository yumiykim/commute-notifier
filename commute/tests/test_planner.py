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
        self.assertEqual(class_start(date(2026, 10, 5), {"0": "10:00:00"}), 36000)
        self.assertEqual(class_start(date(2026, 10, 2), {"4": "13:00:00"}), 46800)
        self.assertIsNone(class_start(date(2026, 10, 3), {"5": None}))

    def test_two_minute_transfer_can_catch_later_train(self):
        first = [Leg("earlier", 9 * 3600 + 20 * 60, 9 * 3600 + 31 * 60),
                 Leg("later", 9 * 3600 + 28 * 60, 9 * 3600 + 39 * 60)]
        second = [Leg("3", 9 * 3600 + 41 * 60, 9 * 3600 + 44 * 60)]
        deadline = 9 * 3600 + 50 * 60
        self.assertEqual(plan(first, second, deadline, transfer_seconds=180)[0].line5.train_id, "earlier")
        self.assertEqual(plan(first, second, deadline, transfer_seconds=120)[0].line5.train_id, "later")

    def test_new_semester_changes_weekly_classes(self):
        next_semester = {"0": "11:00:00", "4": None}
        self.assertEqual(class_start(date(2026, 10, 5), next_semester), 39600)
        self.assertIsNone(class_start(date(2026, 10, 2), next_semester))
