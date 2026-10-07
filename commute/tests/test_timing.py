import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from commute.planner import Leg
from commute.timing import load_commute, action_times, calculate_cases, minute_clock
from commute.tests.test_messages import SETTINGS

class TimingTests(TestCase):
    def test_exact_seconds_preserved_and_action_minutes_floor(self):
        actions = action_times(9*3600+28*60+30, SETTINGS)
        self.assertEqual(actions.platform_ready, 9*3600+26*60+30)
        self.assertEqual(minute_clock(actions.platform_ready), "09:26")
        self.assertEqual(minute_clock(actions.entrance_arrival), "09:24")
        self.assertEqual(minute_clock(actions.home_departure), "09:14")

    def test_actions_before_midnight_show_previous_day(self):
        actions = action_times(300, SETTINGS)
        self.assertEqual(minute_clock(actions.home_departure), "전날 23:51")

    def test_transfer_210_boundary_selects_latest_feasible_train(self):
        first = [Leg("earlier", 8*3600, 9*3600), Leg("later", 8*3600+300, 9*3600+30)]
        second = [Leg("3", 9*3600+210, 9*3600+600)]
        cases = calculate_cases(first, second, 9*3600+720, SETTINGS)
        self.assertEqual(cases[210].line5.train_id, "earlier")
        self.assertEqual(cases[120].line5.train_id, "later")

    def test_one_second_short_transfer_and_exit_deadline_are_rejected(self):
        first = [Leg("5", 8*3600, 9*3600+1)]
        second = [Leg("3", 9*3600+210, 9*3600+600)]
        self.assertIsNone(calculate_cases(first, second, 9*3600+720, SETTINGS)[210])
        self.assertIsNone(calculate_cases(first, second, 9*3600+719, SETTINGS)[120])

    def test_invalid_configuration_is_rejected(self):
        original = dict(SETTINGS.__dict__)
        variants = []
        for name, value in [("early_train_seconds", -1), ("home_to_entrance_seconds", True),
                            ("exit_walk_seconds", 1.5), ("measurement_date", "2026-13-06"),
                            ("preferred_transfer_seconds", 120)]:
            changed = dict(original)
            changed[name] = value
            variants.append(changed)
        variants.extend([{}, {**original, "unexpected": 1}, []])
        with TemporaryDirectory() as folder:
            path = Path(folder) / "commute.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            self.assertEqual(load_commute(path), SETTINGS)
            for variant in variants:
                with self.subTest(variant=variant):
                    path.write_text(json.dumps(variant), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_commute(path)

    def test_friday_timetable_snapshot_selects_later_fast_train(self):
        # 서울시 2026-10-06 조회: 종로3가 12:39:30 도착 → 12:42 출발은 150초.
        first = [Leg("5601", 44550, 45180), Leg("5087", 44940, 45570)]
        second = [Leg("3175", 45720, 45870)]
        cases = calculate_cases(first, second, 46200, SETTINGS)
        self.assertEqual(cases[210].line5.departure, 44550)
        self.assertEqual(cases[120].line5.departure, 44940)
        self.assertEqual(cases[210].line3, cases[120].line3)
        self.assertEqual(cases[210].exit_arrival, 45990)

    def test_fast_transfer_exact_120_seconds_is_allowed_but_119_is_not(self):
        second = [Leg("3", 10000, 10200)]
        exact = calculate_cases([Leg("5", 9000, 9880)], second, 10320, SETTINGS)
        short = calculate_cases([Leg("5", 9000, 9881)], second, 10320, SETTINGS)
        self.assertIsNotNone(exact[120])
        self.assertIsNone(short[120])
