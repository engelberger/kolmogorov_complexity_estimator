#!/usr/bin/env python3
"""
Example script to estimate Kolmogorov complexity using a precomputed D(n,m) distribution.
Shows how to load a distribution file and estimate complexity for specified strings or list top N simplest.
"""
import argparse
from kolmogorov_complexity_estimator.complexity_engine import KolmogorovComplexityEstimator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Estimate Kolmogorov complexity from a precomputed D distribution"
    )
    parser.add_argument(
        "--distribution-file", type=str, required=True,
        help="Path to JSON file containing the D_distribution field or root distribution"
    )
    parser.add_argument(
        "--top-n", type=int, default=None,
        help="Show the top N simplest strings from the distribution"
    )
    parser.add_argument(
        "strings", nargs="*",
        help="Binary strings to estimate complexity for"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    estimator = KolmogorovComplexityEstimator(args.distribution_file)

    if args.top_n:
        print(f"Top {args.top_n} simplest strings and their estimated K values:")
        for s, k in estimator.get_ranked_strings(top_n=args.top_n):
            print(f"{s}: {k:.4f}")
        print()

    for s in args.strings or []:
        k = estimator.estimate_K(s)
        print(f"Estimated K for '{s}': {k:.4f}")

if __name__ == "__main__":
    main() 