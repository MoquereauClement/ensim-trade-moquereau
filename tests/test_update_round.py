import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_round import update_round


class RoundUpdateTests(unittest.TestCase):
    def test_an_order_and_its_explanation_are_recorded_once_per_round(self):
        timestamp = "2026-11-23T10:06:02Z"
        market = {
            "generated_at": timestamp,
            "products": ["A", "B", "C"],
            "history": [
                {"t": t, "timestamp": timestamp, "A": price, "B": 10, "C": 1}
                for t, price in enumerate([20, 10.3, 9.3, 10.5], 368)
            ],
        }
        holdings = {"money": 1000, "products": {"A": 1000, "B": 1000, "C": 1000}}
        leaderboard = {"generated_at": timestamp, "leaderboard": [{"id": "clement", "total_value": 18000}]}
        with tempfile.TemporaryDirectory() as folder:
            data_path = Path(folder) / "observations.json"
            decision_path = Path(folder) / "decision.json"
            self.assertTrue(update_round(market, holdings, leaderboard, data_path, decision_path))
            observation = json.loads(data_path.read_text(encoding="utf-8"))
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            self.assertEqual(observation["decisions"][0]["products"]["A"]["signal"], 0.1)
            self.assertEqual(decision["A"], 0.1)
            self.assertEqual(observation["performance"][0]["values"], {"clement": 18000})
            self.assertFalse(update_round(market, holdings, leaderboard, data_path, decision_path))
            self.assertEqual(json.loads(data_path.read_text(encoding="utf-8")), observation)

    def test_mismatched_feeds_cannot_overwrite_the_last_record(self):
        market = {"generated_at": "2026-11-23T10:06:02Z", "history": [{"t": 371}]}
        leaderboard = {"generated_at": "2026-11-23T01:19:09Z"}
        with tempfile.TemporaryDirectory() as folder:
            data_path = Path(folder) / "observations.json"
            decision_path = Path(folder) / "decision.json"
            decision_path.write_text("existing decision", encoding="utf-8")
            with self.assertRaises(ValueError):
                update_round(market, {}, leaderboard, data_path, decision_path)
            self.assertEqual(decision_path.read_text(encoding="utf-8"), "existing decision")
            self.assertFalse(data_path.exists())
