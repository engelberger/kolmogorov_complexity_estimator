#!/usr/bin/env python3
"""
Example script to run the Coding Theorem Method (CTM) simulation.
This sets up configuration parameters for TM enumeration and simulation.
"""
import argparse
import os
import sys
from collections import Counter
from itertools import islice
from pathlib import Path

# Ensure the package root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kolmogorov_complexity_estimator.output_aggregator import (
    OutputFrequencyDistribution,
)
from kolmogorov_complexity_estimator.parallel_utils import (
    initialize_globals,
    process_tm_batch,
)
from kolmogorov_complexity_estimator.reduction_filters import (
    check_for_cycle_two,
    check_for_escapee,
    has_no_halt_transition,
)
from kolmogorov_complexity_estimator.tm_enumerator import (
    generate_raw_tm_tables,
    generate_reduced_tm_tables,
)
from kolmogorov_complexity_estimator.turing_machine import TuringMachine

# Worker globals for multiprocessing
_GLOBAL_N_STATES = None
_GLOBAL_BLANK_SYMBOL = None
_GLOBAL_MAX_STEPS = None
_GLOBAL_RUNTIME_FILTERS = None


def _process_tm(tm_table):
    # Worker task: apply pre-run filter and run TM
    if has_no_halt_transition(tm_table):
        return ("filtered", None, "no_halt_transition")
    tm = TuringMachine(
        num_states=_GLOBAL_N_STATES,
        transition_table=tm_table,
        blank_symbol=_GLOBAL_BLANK_SYMBOL,
    )
    return tm.run(_GLOBAL_MAX_STEPS, runtime_filters=_GLOBAL_RUNTIME_FILTERS)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run CTM simulation for Kolmogorov complexity estimation"
    )
    parser.add_argument(
        "--n-states", type=int, default=5, help="Number of non-halting TM states (n)"
    )
    parser.add_argument(
        "--max-steps", type=int, default=500, help="Maximum steps to run each TM"
    )
    parser.add_argument(
        "--use-reduced-enum",
        action="store_true",
        help="Use reduced enumeration (exploit symmetries)",
    )
    parser.add_argument(
        "--blank-symbol",
        choices=["0", "1"],
        default="0",
        help="Blank tape symbol to initialize",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="distribution.json",
        help="Path to save the final distribution",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100000,
        help="Number of TMs to process between checkpoints",
    )
    parser.add_argument(
        "--checkpoint-file",
        type=str,
        default="checkpoint.json",
        help="Filepath for saving/loading simulation checkpoints",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes for parallel simulation",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Number of TM tables per batch for parallel processing",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        help="Optional config file (TOML/YAML) for parameters",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of TMs to process (for testing/profiling)",
    )
    return parser.parse_args()


def chunked_iterator(iterator, size):
    """
    Yield lists of items from iterator in batches of given size.
    """
    it = iter(iterator)
    while True:
        batch = list(islice(it, size))
        if not batch:
            break
        yield batch


def main():  # noqa: C901
    args = parse_args()
    # Initialize aggregator
    agg = OutputFrequencyDistribution(args.n_states)
    # Resume from checkpoint if available
    if os.path.exists(args.checkpoint_file):
        agg.load_distribution_from_file(args.checkpoint_file, raw=True)
        processed = agg.total_processed_raw
        print(
            f"Resuming from checkpoint: {args.checkpoint_file} "
            f"with {processed} machines already processed."
        )
    else:
        processed = 0
    # Select enumerator
    if args.use_reduced_enum:
        enumerator = generate_reduced_tm_tables(args.n_states)
    else:
        enumerator = generate_raw_tm_tables(args.n_states)
    # Skip already processed machines when resuming
    if processed > 0:
        enumerator = islice(enumerator, processed, None)
    # Apply limit if provided (relative to resume)
    if args.limit is not None:
        enumerator = islice(enumerator, args.limit)
    # Define runtime filters
    runtime_filters = [check_for_escapee, check_for_cycle_two]
    # Parallel or sequential processing
    if args.workers > 1:
        # Initialize globals for worker processes
        initialize_globals(
            args.n_states,
            args.blank_symbol,
            args.max_steps,
            runtime_filters,
        )

        # Process TMs in parallel using 'fork' context to avoid pickling issues
        from multiprocessing import get_context

        ctx = get_context("fork")
        # Batch processing to reduce IPC overhead
        chunked_iter = chunked_iterator(enumerator, args.batch_size)
        # Track when to checkpoint next
        next_checkpoint = (
            (processed // args.checkpoint_interval) + 1
        ) * args.checkpoint_interval
        with ctx.Pool(processes=args.workers) as pool:
            for (
                batch_counts_list,
                batch_non_halting_list,
                batch_processed,
                batch_halting,
            ) in pool.imap(
                process_tm_batch,
                chunked_iter,
                chunksize=1,  # Each task is one batch
            ):
                # Convert lists back to Counter for record_run_batch
                # or modify record_run_batch to accept lists directly.
                # For now, convert here:
                batch_output_counts = Counter(dict(batch_counts_list))
                batch_non_halting_reasons = Counter(dict(batch_non_halting_list))

                agg.record_run_batch(
                    batch_output_counts,
                    batch_non_halting_reasons,
                    batch_processed,
                    batch_halting,
                )
                processed += batch_processed
                # Checkpoint if we've crossed the next threshold
                if processed >= next_checkpoint:
                    print(f"Checkpoint at {processed} TMs processed...")
                    agg.save_distribution_to_file(args.checkpoint_file, raw=True)
                    next_checkpoint += args.checkpoint_interval
    else:
        # Sequential processing
        for _idx, tm_table in enumerate(enumerator, start=processed + 1):
            # Pre-run filter: no halt transition
            if has_no_halt_transition(tm_table):
                agg.record_run_outcome("filtered", None, "no_halt_transition")
                continue
            tm = TuringMachine(
                num_states=args.n_states,
                transition_table=tm_table,
                blank_symbol=args.blank_symbol,
            )
            status, output, filter_name = tm.run(
                args.max_steps, runtime_filters=runtime_filters
            )
            agg.record_run_outcome(status, output, filter_name)
            # Checkpoint using aggregator counts
            if agg.total_processed_raw % args.checkpoint_interval == 0:
                print(f"Checkpoint at {agg.total_processed_raw} TMs processed...")
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
