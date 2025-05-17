# Manages collection of TM outputs, D(n,m) calculation, completion logic
import json
from collections import Counter
from typing import Any, Dict, Optional

from .reduction_filters import apply_completion_rules as _apply_completion_rules


class OutputFrequencyDistribution:
    """
    Manages counts of TM outputs, non-halting reasons, and calculates D(n,m)
    distributions.
    """

    def __init__(self, num_states: int):
        self.num_states = num_states
        # Raw counts
        self.output_counts = Counter()  # counts of halted output strings
        self.total_processed_raw = 0  # total machines processed
        self.total_halting_raw = 0  # total halted machines
        self.non_halting_reasons = Counter()  # counts by filter name or 'timeout'
        # After completion (reduced enumeration)
        self.effective_output_counts: Optional[Counter] = None
        self.effective_non_halting: int = 0
        self.effective_halting: int = 0
        self.effective_total: int = 0
        # Distribution
        self.D_distribution: Dict[str, float] = {}

    def record_run_outcome(
        self,
        status: str,
        output_string: Optional[str] = None,
        filter_name: Optional[str] = None,
    ) -> None:
        """
        Record the outcome of a single TM run.

        :param status: 'halted', 'timeout', or 'filtered'
        :param output_string: the produced string if halted
        :param filter_name: name of the filter if filtered
        """
        self.total_processed_raw += 1
        if status == "halted" and output_string is not None:
            self.total_halting_raw += 1
            self.output_counts[output_string] += 1
        elif status == "timeout":
            self.non_halting_reasons["timeout"] += 1
        elif status == "filtered" and filter_name:
            self.non_halting_reasons[filter_name] += 1
        else:
            self.non_halting_reasons["unknown"] += 1

    def apply_completion_rules(self, M_red: int) -> None:
        """
        Apply output completion logic for reduced enumeration.

        :param M_red: number of machines run in reduced set
        Updates effective counts and totals.
        """
        total_counts, non_halting, halting, total = _apply_completion_rules(
            self.output_counts,
            sum(self.non_halting_reasons.values()),
            M_red,
            self.num_states,
        )
        self.effective_output_counts = total_counts
        self.effective_non_halting = non_halting
        self.effective_halting = halting
        self.effective_total = total

    def calculate_D_distribution(self) -> None:
        """
        Calculate D(n,m)(s) = count(s) / total_halting for each string.
        Uses effective counts if available, else raw counts.
        """
        if self.effective_output_counts is not None:
            counts = self.effective_output_counts
            denom = self.effective_halting
        else:
            counts = self.output_counts
            denom = self.total_halting_raw
        if denom <= 0:
            raise ValueError("No halting machines to calculate distribution.")
        self.D_distribution = {s: c / denom for s, c in counts.items()}

    def save_distribution_to_file(self, filepath: str, raw: bool = False) -> None:
        """
        Save the distribution and counts to a JSON file.

        :param filepath: Path to JSON output file.
        :param raw: If True, save raw counts; else save effective counts.
        """
        data: Dict[str, Any] = {
            "num_states": self.num_states,
            "total_processed_raw": self.total_processed_raw,
            "total_halting_raw": self.total_halting_raw,
            "non_halting_reasons": dict(self.non_halting_reasons),
        }
        if raw or self.effective_output_counts is None:
            data["output_counts"] = dict(self.output_counts)
        else:
            data["effective_output_counts"] = dict(self.effective_output_counts)
            data["effective_non_halting"] = self.effective_non_halting
            data["effective_halting"] = self.effective_halting
            data["effective_total"] = self.effective_total
            data["D_distribution"] = self.D_distribution
        with open(filepath, "w") as f:
            json.dump(data, f)

    def load_distribution_from_file(self, filepath: str, raw: bool = False) -> None:
        """
        Load counts and distribution from a JSON file.

        :param filepath: Path to JSON file.
        :param raw: If True, load raw counts; else load effective counts and
               distribution.
        """
        with open(filepath) as f:
            data = json.load(f)
        self.num_states = data.get("num_states", self.num_states)
        self.total_processed_raw = data.get("total_processed_raw", 0)
        self.total_halting_raw = data.get("total_halting_raw", 0)
        self.non_halting_reasons = Counter(data.get("non_halting_reasons", {}))
        if raw or "effective_output_counts" not in data:
            self.output_counts = Counter(data.get("output_counts", {}))
        else:
            effective_counts_data = data.get("effective_output_counts", {})
            self.effective_output_counts = Counter(effective_counts_data)
            self.effective_non_halting = data.get("effective_non_halting", 0)
            self.effective_halting = data.get("effective_halting", 0)
            self.effective_total = data.get("effective_total", 0)
            self.D_distribution = data.get("D_distribution", {})

    def record_run_batch(
        self,
        batch_output_counts: Dict[str, int],
        batch_non_halting_reasons: Dict[str, int],
        batch_total_processed: int,
        batch_total_halting: int,
    ) -> None:
        """
        Record outcomes of a batch of TM runs.
        :param batch_output_counts: counts of halted output strings.
        :param batch_non_halting_reasons: counts by filter name or 'timeout'.
        :param batch_total_processed: total machines processed in batch.
        :param batch_total_halting: total halted machines in batch.
        """
        # Update total processed and halted counts
        self.total_processed_raw += batch_total_processed
        self.total_halting_raw += batch_total_halting
        # Update output counts
        for s, c in batch_output_counts.items():
            self.output_counts[s] += c
        # Update non-halting reasons
        for reason, c in batch_non_halting_reasons.items():
            self.non_halting_reasons[reason] += c
