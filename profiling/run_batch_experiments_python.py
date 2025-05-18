import subprocess
from pathlib import Path

# --- Configuration ---
CONDA_ENV_NAME = "kolmogorov"
BATCH_SIZES = [10, 100, 1000, 5000, 10000]
# BATCH_SIZES = [10000, 50000] # Smaller set for quick testing

N_STATES = 3
WORKERS = 16
BASE_PROFILE_NAME = "profile_batch_py"
RESULTS_DIR = Path("profiling_results_py")
EXAMPLE_SCRIPT = Path("examples/run_ctm_simulation.py")
CHECKPOINT_FILE = Path("checkpoint.json")


# --- Helper Functions ---
def run_command(command, capture_output=False, text=False, check=True, shell=False):
    """Runs a command using subprocess."""
    print(
        f"Executing: {' '.join(command) if isinstance(command, list) else command}"
    )
    try:
        # Use shell=True if conda activate needs it, but prefer conda run
        process = subprocess.run(
            command,
            capture_output=capture_output,
            text=text,
            check=check,
            shell=shell,
        )
        return process
    except subprocess.CalledProcessError as e:
        print(
            f"Error running command: "
            f"{' '.join(command) if isinstance(command, list) else command}"
        )
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        raise


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Commands will be prefixed with 'conda run -n ENV_NAME'
    # to ensure correct environment
    conda_run_prefix = ["conda", "run", "-n", CONDA_ENV_NAME]
    # For setup.py, direct python might be okay
    # if script itself is run with correct python
    # but conda run is safer.

    print(f"--- Building Cython extensions in {CONDA_ENV_NAME} environment ---")
    build_command = conda_run_prefix + ["python", "setup.py", "build_ext", "--inplace"]
    run_command(build_command)

    base_args = [
        str(EXAMPLE_SCRIPT),
        "--n-states",
        str(N_STATES),
        "--workers",
        str(WORKERS),
    ]

    for batch_size in BATCH_SIZES:
        print(f"\\n--- Running experiment with Batch Size: {batch_size} ---")

        profile_file = RESULTS_DIR / f"{BASE_PROFILE_NAME}_{batch_size}.prof"
        stats_file = RESULTS_DIR / f"{BASE_PROFILE_NAME}_{batch_size}.txt"

        if CHECKPOINT_FILE.exists():
            print(f"Removing old checkpoint: {CHECKPOINT_FILE}")
            CHECKPOINT_FILE.unlink()

        print(f"Running cProfile for batch size {batch_size}...")
        cprofile_command = (
            conda_run_prefix
            + [
                "python",
                "-m",
                "cProfile",
                "-o",
                str(profile_file),
            ]
            + base_args
            + ["--batch-size", str(batch_size)]
        )
        run_command(cprofile_command)

        print(f"Generating pstats report for batch size {batch_size}...")
        pstats_script = (
            f"import pstats; "
            f"stats = pstats.Stats('{str(profile_file)}'); "
            f"stats.strip_dirs().sort_stats('cumtime').print_stats(50)"
        )
        # Using python -c with conda run
        pstats_command = conda_run_prefix + ["python", "-c", pstats_script]

        # Capture output for pstats
        process = run_command(pstats_command, capture_output=True, text=True)
        with open(stats_file, "w") as f:
            f.write(process.stdout)

        print(f"Profiling for batch size {batch_size} complete.")
        print(f"  Profile: {profile_file}")
        print(f"  Stats:   {stats_file}")

    print("\\n--- All batch size experiments completed ---")
    print(f"Results are in the '{RESULTS_DIR}' directory.")


if __name__ == "__main__":
    # It's best to run this script from within the activated conda environment.
    # If not, the `conda run` prefix handles execution within the target environment.
    # Check if EXAMPLE_SCRIPT exists
    if not EXAMPLE_SCRIPT.exists():
        print(f"Error: Example script not found at {EXAMPLE_SCRIPT}")
        print(
            "Please ensure you are in the root directory of the "
            "'kolmogorov_complexity_estimator' project."
        )
        exit(1)
    main()
