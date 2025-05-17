import json
import subprocess
import sys
from pathlib import Path

import pytest


# Determine project root relative to this test file
def _project_root():
    return Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "workers,use_reduced",
    [
        (1, False),
        (2, True),
    ],
)
def test_run_ctm_simulation(tmp_path, workers, use_reduced):
    """
    Integration test for examples/run_ctm_simulation.py.
    Runs the script with a small number of machines, both sequential and parallel,
    and checks that the produced distribution sums to 1.
    """
    project_root = _project_root()
    script_path = project_root / "examples" / "run_ctm_simulation.py"
    # Setup paths for output and checkpoint
    output_file = tmp_path / (
        f"dist_{workers}_{'reduced' if use_reduced else 'raw'}.json"
    )
    checkpoint_file = tmp_path / (
        f"cp_{workers}_{'reduced' if use_reduced else 'raw'}.json"
    )
    # Build command
    cmd = [
        sys.executable,
        str(script_path),
        "--n-states",
        "2",
        "--max-steps",
        "5",
        "--workers",
        str(workers),
        "--checkpoint-file",
        str(checkpoint_file),
        "--output-file",
        str(output_file),
        "--checkpoint-interval",
        "10",
    ]
    if use_reduced:
        cmd.append("--use-reduced-enum")
    # Run the script
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
    # Assert successful execution
    assert result.returncode == 0, f"Script failed with stderr:\n{result.stderr}"
    # Check output files exist
    assert output_file.exists(), f"Missing output file: {output_file}"
    assert checkpoint_file.exists(), f"Missing checkpoint file: {checkpoint_file}"
    # Load output JSON
    data = json.loads(output_file.read_text())
    # Determine distribution source:
    # - use D_distribution if present
    # - else compute from raw output_counts
    if "D_distribution" in data:
        dist = data["D_distribution"]
        assert isinstance(dist, dict), "D_distribution is not a dict"
    else:
        # Raw enumeration case: distribution not saved directly
        assert "output_counts" in data, "output_counts key missing in output JSON"
        raw_counts = data["output_counts"]
        assert "total_halting_raw" in data, "total_halting_raw missing"
        halting = data["total_halting_raw"]
        assert halting > 0, "No halting machines in raw output"
        # Compute distribution manually
        dist = {s: c / halting for s, c in raw_counts.items()}
    # Distribution probabilities should sum to approximately 1
    total_prob = sum(dist.values())
    assert (
        abs(total_prob - 1.0) < 1e-6
    ), f"Distribution sums to {total_prob}, expected 1.0"
