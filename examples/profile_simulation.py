"""
Profile core CTM simulation loop using cProfile and visualize with snakeviz.

Usage:
    python examples/profile_simulation.py \
        --n_states 2 --max_steps 100 --num_machines 1000 \
        --output_profile profile.prof

Then run:
    snakeviz profile.prof
"""

import argparse
import cProfile

from kolmogorov_complexity_estimator.output_aggregator import (
    OutputFrequencyDistribution,
)
from kolmogorov_complexity_estimator.reduction_filters import (
    check_for_cycle_two,
    check_for_escapee,
    has_no_halt_transition,
)
from kolmogorov_complexity_estimator.tm_enumerator import generate_raw_tm_tables, generate_reduced_tm_tables
from kolmogorov_complexity_estimator.turing_machine import TuringMachine


def run_simulation(n_states, max_steps, num_machines, use_reduced=False):
    """
    Run a small CTM simulation for profiling.
    """
    ofd = OutputFrequencyDistribution(n_states)
    # Choose raw or reduced enumeration
    if use_reduced:
        enumerator = generate_reduced_tm_tables(n_states)
    else:
        enumerator = generate_raw_tm_tables(n_states)
    for idx, tm_table in enumerate(enumerator):
        if idx >= num_machines:
            break
        # Pre-run filter
        if has_no_halt_transition(tm_table):
            ofd.record_run_outcome("filtered", None, "has_no_halt_transition")
            continue
        tm = TuringMachine(num_states=n_states, transition_table=tm_table)
        status, output, filter_type = tm.run(
            max_steps, runtime_filters=[check_for_escapee, check_for_cycle_two]
        )
        ofd.record_run_outcome(status, output, filter_type)
    return ofd


def main():
    parser = argparse.ArgumentParser(
        description="Profile CTM simulation loop with cProfile"
    )
    parser.add_argument(
        "--n_states", type=int, default=2, help="Number of states for Turing machines"
    )
    parser.add_argument("--max_steps", type=int, default=100, help="Max steps per TM")
    parser.add_argument(
        "--num_machines", type=int, default=1000, help="Number of machines to simulate"
    )
    parser.add_argument(
        "--use_reduced",
        action="store_true",
        help="Use reduced enumeration (exploit symmetries)",
    )
    parser.add_argument(
        "--output_profile",
        type=str,
        default="profile.prof",
        help="Output .prof filename",
    )
    args = parser.parse_args()

    # Run under cProfile
    cProfile.runctx(
        "run_simulation(args.n_states, args.max_steps, args.num_machines, args.use_reduced)",
        globals(),
        locals(),
        filename=args.output_profile,
    )
    print(f"Profile data saved to {args.output_profile}. Use snakeviz to visualize it.")


if __name__ == "__main__":
    main()
