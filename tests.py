"""File for unit tests"""
import math
import unittest

from cpamm_simulator import default_scenarios, run_scenarios, simulate_swap


class TestCPAMMSimulator(unittest.TestCase):
    """
    Unit tests function
    """
    def test_invalid_direction_raises(self):
        """test invalid direction raises"""
        with self.assertRaises(ValueError):
            simulate_swap(10_000, 10_000, 0.003, "BAD", 100)

    def test_invalid_amount_raises(self):
        """test invalid amount raises"""
        with self.assertRaises(ValueError):
            simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 0)

    def test_known_amount_out_value(self):
        """test known amount out value"""
        result = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 100)
        expected = 10_000 * (100 * (1 - 0.003)) / (10_000 + 100 * (1 - 0.003))
        self.assertTrue(math.isclose(result.amount_out, expected, rel_tol=1e-12))

    def test_fee_reduces_output(self):
        """test fee reduces output"""
        no_fee = simulate_swap(10_000, 10_000, 0.0, "A_TO_B", 1_000)
        with_fee = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 1_000)
        self.assertGreater(no_fee.amount_out, with_fee.amount_out)

    def test_product_increases_with_fee_collection(self):
        """test product increases with fee collection"""
        result = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 1_000)
        old_k = 10_000 * 10_000
        new_k = result.reserve_a_after * result.reserve_b_after
        self.assertGreater(new_k, old_k)

    def test_slippage_grows_with_trade_size(self):
        """test slippage grows with trade size"""
        small = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 100)
        medium = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 1_000)
        large = simulate_swap(10_000, 10_000, 0.003, "A_TO_B", 3_500)
        self.assertLess(small.slippage_pct, medium.slippage_pct)
        self.assertLess(medium.slippage_pct, large.slippage_pct)

    def test_reverse_direction_updates_reserves_correctly(self):
        """test reverse direction updates reserves correctly"""
        result = simulate_swap(10_000, 20_000, 0.003, "B_TO_A", 500)
        self.assertLess(result.reserve_a_after, 10_000)
        self.assertGreater(result.reserve_b_after, 20_000)
        self.assertGreater(result.amount_out, 0)

    def test_default_scenarios_count(self):
        """test default scenarios count"""
        self.assertEqual(len(default_scenarios()), 3)

    def test_run_scenarios_returns_named_rows(self):
        """test run scenarios returns named_rows"""
        rows = run_scenarios()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["scenario"], "small_swap")
        self.assertIn("amount_out", rows[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
