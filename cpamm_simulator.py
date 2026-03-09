"""
Usage examples:
    python cpamm_simulator.py --run-scenarios
    python cpamm_simulator.py --run-scenarios --csv scenario_results.csv
    python cpamm_simulator.py --reserve_a 10000 --reserve_b 10000 --fee 0.003
      --direction A_TO_B --amount_in 1000
    python cpamm_simulator.py --self-test
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
import argparse
import csv
import json
import unittest
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class SwapResult:
    """Class to help with task automatization"""
    reserve_a_before: float
    reserve_b_before: float
    reserve_a_after: float
    reserve_b_after: float
    fee: float
    direction: str
    amount_in: float
    amount_in_after_fee: float
    amount_out: float
    initial_price: float
    effective_price: float
    slippage_pct: float

    def to_dict(self) -> dict:
        """Lets me use it as a dict"""
        return asdict(self)


def _validate_inputs(reserve_a: float, reserve_b: float, fee: float, amount_in: float, direction: str) -> None:
    """
    Error handling function
    """
    if reserve_a <= 0 or reserve_b <= 0:
        raise ValueError("Reserves must be positive.")
    if not 0 <= fee < 1:
        raise ValueError("Fee must be in the range [0, 1).")
    if amount_in <= 0:
        raise ValueError("amount_in must be positive.")
    if direction not in {"A_TO_B", "B_TO_A"}:
        raise ValueError("direction must be 'A_TO_B' or 'B_TO_A'.")


def simulate_swap(
    reserve_a: float,
    reserve_b: float,
    fee: float,
    direction: str,
    amount_in: float,
) -> SwapResult:
    """
    Simulate an exact-input swap in a constant-product pool.
    """
    _validate_inputs(reserve_a, reserve_b, fee, amount_in, direction)

    if direction == "A_TO_B":
        reserve_in, reserve_out = reserve_a, reserve_b
        initial_price = reserve_b / reserve_a
    else:
        reserve_in, reserve_out = reserve_b, reserve_a
        initial_price = reserve_a / reserve_b

    amount_in_after_fee = amount_in * (1 - fee)
    amount_out = reserve_out * amount_in_after_fee / (reserve_in + amount_in_after_fee)
    effective_price = amount_out / amount_in
    slippage_pct = ((initial_price - effective_price) / initial_price) * 100

    if direction == "A_TO_B":
        reserve_a_after = reserve_a + amount_in
        reserve_b_after = reserve_b - amount_out
    else:
        reserve_a_after = reserve_a - amount_out
        reserve_b_after = reserve_b + amount_in

    return SwapResult(
        reserve_a_before=reserve_a,
        reserve_b_before=reserve_b,
        reserve_a_after=reserve_a_after,
        reserve_b_after=reserve_b_after,
        fee=fee,
        direction=direction,
        amount_in=amount_in,
        amount_in_after_fee=amount_in_after_fee,
        amount_out=amount_out,
        initial_price=initial_price,
        effective_price=effective_price,
        slippage_pct=slippage_pct,
    )


def default_scenarios() -> List[dict]:
    """
    defaultsc enarios for testing my code
    """
    return [
        {
            "name": "small_swap",
            "reserve_a": 10_000.0,
            "reserve_b": 10_000.0,
            "fee": 0.003,
            "direction": "A_TO_B",
            "amount_in": 100.0,
        },
        {
            "name": "medium_swap",
            "reserve_a": 10_000.0,
            "reserve_b": 10_000.0,
            "fee": 0.003,
            "direction": "A_TO_B",
            "amount_in": 1_000.0,
        },
        {
            "name": "large_swap",
            "reserve_a": 10_000.0,
            "reserve_b": 10_000.0,
            "fee": 0.003,
            "direction": "A_TO_B",
            "amount_in": 3_500.0,
        },
    ]


def run_scenarios(scenarios: Iterable[dict] | None = None) -> list[dict]:
    """
    A help function to run those scenarios
    """
    scenarios = list(default_scenarios() if scenarios is None else scenarios)
    results: list[dict] = []
    for scenario in scenarios:
        result = simulate_swap(
            reserve_a=scenario["reserve_a"],
            reserve_b=scenario["reserve_b"],
            fee=scenario["fee"],
            direction=scenario["direction"],
            amount_in=scenario["amount_in"],
        )
        row = {"scenario": scenario["name"], **result.to_dict()}
        results.append(row)
    return results


def save_results_to_csv(results: Iterable[dict], path: str | Path) -> None:
    """
    Help function to save results to the csv file
    """
    rows = list(results)
    if not rows:
        raise ValueError("No results to save.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def format_result_text(result: SwapResult) -> str:
    """
    Help function for a nice console output)
    """
    return (
        f"direction={result.direction}\n"
        f"amount_in={result.amount_in:.6f}\n"
        f"amount_out={result.amount_out:.6f}\n"
        f"reserve_a_after={result.reserve_a_after:.6f}\n"
        f"reserve_b_after={result.reserve_b_after:.6f}\n"
        f"initial_price={result.initial_price:.6f}\n"
        f"effective_price={result.effective_price:.6f}\n"
        f"slippage_pct={result.slippage_pct:.6f}"
    )


def run_self_tests() -> int:
    """
    Help function for testing the code
    """
    start_dir = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(start_dir), pattern="tests.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def build_parser() -> argparse.ArgumentParser:
    """
    Parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--reserve_a", type=float)
    parser.add_argument("--reserve_b", type=float)
    parser.add_argument("--fee", type=float, default=0.003)
    parser.add_argument("--direction", choices=["A_TO_B", "B_TO_A"])
    parser.add_argument("--amount_in", type=float)
    parser.add_argument("--run-scenarios", action="store_true")
    parser.add_argument("--csv", type=str)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> int:
    """
    Main function that outs code together
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return run_self_tests()

    if args.run_scenarios:
        results = run_scenarios()
        if args.csv:
            save_results_to_csv(results, args.csv)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for row in results:
                print(f"--- {row['scenario']} ---")
                print(
                    f"amount_out={row['amount_out']:.6f}, "
                    f"effective_price={row['effective_price']:.6f}, "
                    f"slippage_pct={row['slippage_pct']:.6f}"
                )
        return 0

    required = [args.reserve_a, args.reserve_b, args.direction, args.amount_in]
    if any(value is None for value in required):
        parser.error(
            "For a custom swap, provide --reserve_a, --reserve_b, --direction, and --amount_in; "
            "or use --run-scenarios or --self-test."
        )

    result = simulate_swap(
        reserve_a=args.reserve_a,
        reserve_b=args.reserve_b,
        fee=args.fee,
        direction=args.direction,
        amount_in=args.amount_in,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_result_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
