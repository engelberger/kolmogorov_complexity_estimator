#!/usr/bin/env python3
"""
Example script to run the Coding Theorem Method (CTM) simulation.
This sets up configuration parameters for TM enumeration and simulation.
"""
import argparse
import os
import sys
from pathlib import Path

# Ensure the package root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kolmogorov_complexity_estimator.tm_enumerator import (
    generate_raw_tm_tables,
    generate_reduced_tm_tables,
)
from kolmogorov_complexity_estimator.reduction_filters import (
    has_no_halt_transition,
    check_for_escapee,
    check_for_cycle_two,
)
from kolmogorov_complexity_estimator.turing_machine import TuringMachine
from kolmogorov_complexity_estimator.output_aggregator import OutputFrequencyDistribution


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run CTM simulation for Kolmogorov complexity estimation"
    )
    parser.add_argument(
        "--n-states", type=int, default=5,
        help="Number of non-halting TM states (n)"
    )
    parser.add_argument(
        "--max-steps", type=int, default=500,
        help="Maximum steps to run each TM"
    )
    parser.add_argument(
        "--use-reduced-enum", action="store_true",
        help="Use reduced enumeration (exploit symmetries)"
    )
    parser.add_argument(
        "--blank-symbol", choices=['0', '1'], default='0',
        help="Blank tape symbol to initialize"
    )
    parser.add_argument(
        "--output-file", type=str, default="distribution.json",
        help="Path to save the final distribution"
    )
    parser.add_argument(
        "--checkpoint-interval", type=int, default=100000,
        help="Number of TMs to process between checkpoints"
    )
    parser.add_argument(
        "--checkpoint-file", type=str, default="checkpoint.json",
        help="Filepath for saving/loading simulation checkpoints"
    )
    parser.add_argument(
        "--config-file", type=str,
        help="Optional config file (TOML/YAML) for parameters"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Initialize aggregator
    agg = OutputFrequencyDistribution(args.n_states)
    # Select enumerator
    if args.use_reduced_enum:
        enumerator = generate_reduced_tm_tables(args.n_states)
    else:
        enumerator = generate_raw_tm_tables(args.n_states)
    # Define runtime filters
    runtime_filters = [check_for_escapee, check_for_cycle_two]
    # Simulation loop
    for idx, tm_table in enumerate(enumerator, start=1):
        # Pre-run filter: no halt transition
        if has_no_halt_transition(tm_table):
            agg.record_run_outcome('filtered', None, 'no_halt_transition')
        else:
            # Instantiate and run TM
            tm = TuringMachine(
                args.n_states,
                tm_table,
                blank_symbol=args.blank_symbol
            )
            status, output, filter_name = tm.run(
                args.max_steps,
                runtime_filters=runtime_filters
            )
            agg.record_run_outcome(status, output, filter_name)
        # Checkpointing
        if idx % args.checkpoint_interval == 0:
            print(f"Checkpoint at {idx} TMs processed...")
            agg.save_distribution_to_file(args.checkpoint_file, raw=True)
    # After enumeration
    M_red = agg.total_processed_raw
    if args.use_reduced_enum:
        agg.apply_completion_rules(M_red)
    # Calculate distribution
    agg.calculate_D_distribution()
    # Save final distribution
    agg.save_distribution_to_file(args.output_file, raw=False)
    print(f"Simulation completed. Distribution saved to {args.output_file}")


if __name__ == "__main__":
    main() 