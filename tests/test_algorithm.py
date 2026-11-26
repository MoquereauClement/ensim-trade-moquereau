import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "algorithm", Path(__file__).resolve().parents[1] / "scripts" / "algorithm.py"
)
algorithm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(algorithm)


class StrategyTests(unittest.TestCase):
    def test_buy_on_rebound_in_low_zone(self):
        self.assertEqual(algorithm.compute_signal([20, 10.3, 9.3, 10.5]), 1.0)

    def test_sell_on_reversal_in_high_zone(self):
        self.assertEqual(algorithm.compute_signal([1, 10.3, 11.3, 10.5]), -1.0)

    def test_sell_after_eligible_peak_even_below_threshold_on_confirmation(self):
        cases = {
            "A": [1, 10.3, 11.3, 8.0],
            "B": [12, 10, 10.6, 13.6, 12.8],
            "C": [0.9021, 1.3177, 1.3699, 1.3495],
        }
        for product, prices in cases.items():
            with self.subTest(product=product):
                _, sell_limit = algorithm.signal_limits(prices, product)
                self.assertLess(prices[-1], sell_limit)
                self.assertEqual(algorithm.compute_signal(prices[:-1], product), 0)
                self.assertEqual(algorithm.compute_signal(prices, product), -1.0)
        self.assertEqual(algorithm.compute_signal([0.9021, 1.3177, 1.3690, 1.3495], "C"), 0)

    def test_middle_reversals_do_not_trade(self):
        self.assertEqual(algorithm.compute_signal([0.5, 20, 10.3, 9.3, 10.5]), 0)
        self.assertEqual(algorithm.compute_signal([0.5, 20, 10.3, 11.3, 10.5]), 0)

    def test_keep_waiting_while_price_falls_or_rises(self):
        self.assertEqual(algorithm.compute_signal([20, 10.5, 10.3, 9.3]), 0)
        self.assertEqual(algorithm.compute_signal([1, 10.3, 10.5, 11.3]), 0)

    def test_short_flat_or_plateau_history_does_not_trade(self):
        for prices in [[], [5], [5, 4], [5, 5, 5], [20, 10, 10, 10.5]]:
            with self.subTest(prices=prices):
                self.assertEqual(algorithm.compute_signal(prices), 0)

    def test_budget_guard_preserves_reserve_after_rounding(self):
        signal = algorithm.apply_budget_guard(1.0, 50.16, 1)
        self.assertGreaterEqual(signal, 0)
        self.assertLessEqual(100 * signal, 0.16)
        self.assertEqual(algorithm.apply_budget_guard(1.0, 50, 1), 0)
        self.assertEqual(algorithm.apply_budget_guard(1.0, 957.39, 12.5156), 0.725)

    def test_cycle_buy_and_sell_for_B_and_C(self):
        cases = [
            ("B", [10, 12, 10, 9.8, 9.85], 1.0),
            ("B", [12, 10, 10.6, 13.6, 13.5], -1.0),
            ("C", [3, 3.3, 2.8, 1.95, 1.98], 1.0),
            ("C", [3, 2, 2.3, 3.2, 3.15], -1.0),
        ]
        for product, prices, expected in cases:
            with self.subTest(product=product, prices=prices):
                self.assertEqual(algorithm.compute_signal(prices, product), expected)

    def test_cycle_reversal_outside_target_does_not_trade(self):
        self.assertEqual(algorithm.compute_signal([10, 12, 11, 10.9, 11], "B"), 0)
        self.assertEqual(algorithm.compute_signal([3, 3.3, 2.8, 2.7, 2.8], "C"), 0)

    def test_cycle_target_without_reversal_does_not_trade(self):
        self.assertEqual(algorithm.compute_signal([10, 12, 10, 9.8, 9.7], "B"), 0)
        self.assertEqual(algorithm.compute_signal([3, 3.3, 2.8, 1.95, 1.9], "C"), 0)

    def test_cycle_references_filter_noise_and_use_latest_peak(self):
        prices = [10, 12, 11.9, 12.1, 11, 9, 10, 11, 10]
        self.assertEqual(algorithm.cycle_references(prices, 0.05), (11, 9))
        self.assertEqual(algorithm.cycle_references([10, 10.1, 10], 0.05), (None, None))

    def test_no_reference_or_invalid_prices_does_not_trade(self):
        for product in ["B", "C"]:
            self.assertEqual(algorithm.compute_signal([10, 10.01, 10], product), 0)
            self.assertEqual(algorithm.compute_signal([10, float("nan"), 10], product), 0)
            self.assertEqual(algorithm.compute_signal([10, 0, 10], product), 0)

    def run_main(self, prices, money=1000, units=1000):
        market = {
            "products": ["A", "B", "C"],
            "history": [{p: price for p in ["A", "B", "C"]} for price in prices],
        }
        holdings = {"money": money, "products": {"A": units, "B": units, "C": units}}
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "decision.json"
            with patch.object(algorithm, "fetch_json", side_effect=[market, holdings]), patch.object(
                algorithm, "DECISION_PATH", destination
            ), patch("builtins.print"):
                algorithm.main()
            return json.loads(destination.read_text(encoding="utf-8"))

    def test_main_can_trade_all_three_products(self):
        result = self.run_main([20, 10.3, 9.3, 10.5], money=4000)
        self.assertEqual(result["A"], 1.0)
        self.assertEqual(result["B"], 1.0)
        self.assertEqual(result["C"], 1.0)
        self.assertTrue(result["updated_at"].endswith("Z"))

    def test_simultaneous_buys_share_one_budget(self):
        result = self.run_main([20, 10.3, 9.3, 10.5], money=1500)
        spent = sum(100 * max(0, result[p]) * 10.5 for p in ["A", "B", "C"])
        self.assertLessEqual(spent, 1500 - algorithm.MIN_MONEY_RESERVE)
        self.assertEqual(result["A"], 1.0)
        self.assertEqual(result["B"], 0.38)
        self.assertEqual(result["C"], 0)

    def test_sales_are_not_counted_as_available_cash(self):
        with patch.object(algorithm, "compute_signal", side_effect=[-1.0, 1.0, 1.0]):
            result = self.run_main([10, 9, 10], money=50)
        self.assertEqual(result["A"], -1.0)
        self.assertEqual(result["B"], 0)
        self.assertEqual(result["C"], 0)

    def test_main_caps_sales_to_owned_units(self):
        for units, expected in [(0, 0), (2.56, -0.025), (30, -0.3), (150, -1.0)]:
            with self.subTest(units=units):
                result = self.run_main([1, 10.3, 11.3, 10.5], units=units)
                self.assertEqual(result["A"], expected)
                self.assertLessEqual(abs(result["A"]) * 100, units)

    def test_main_with_empty_history(self):
        result = self.run_main([])
        self.assertEqual([result[p] for p in ["A", "B", "C"]], [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
