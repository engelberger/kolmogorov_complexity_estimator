import pstats
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# --- Configuration ---
PROFILING_DIR = Path("profiling_results_py")  # Directory where .prof files are stored
PLOT_OUTPUT_DIR = Path("profiling_plots")
BASE_PROFILE_NAME_PREFIX = "profile_batch_py_"  # From the experiment script

# Functions to look for in profiling stats (use a broader match for some)
# List of (display_name, regex_pattern_for_filename_lineno_function)
IPC_FUNCTION_PATTERNS = [
    ("Pool/Queue Wait/Mgmt", r"pool\.py.*(_wait_for_updates|_maintain_pool|acquire)"),
    (
        "Connection Recv/Send",
        r"connection\.py.*(recv|send|_recv_bytes|_send_bytes|wait|poll)",
    ),
    ("OS Read/Write (IPC)", r"({built-in method posix.(read|write)})"),
    ("Pickling", r"(_pickle\.Pickler\.dump|reduction\.dumps)"),
    ("Selectors", r"selectors\.py.*(select)"),
    ("Queue Ops", r"queues\.py.*(empty|get|put)"),
]


def parse_prof_file(prof_file_path, batch_size):
    """Parses a .prof file to extract total time and IPC-related times."""
    stats = pstats.Stats(str(prof_file_path))

    total_time = 0
    # Find total time: often the cumtime of the top-level script or exec
    # We'll look for the main script or the first entry if that's not obvious
    if stats.stats:
        # The first key in stats.stats is often the entry point
        # Or look for run_ctm_simulation.py specifically
        main_script_key = None
        for key_tuple in stats.stats.keys():
            if "run_ctm_simulation.py" in key_tuple[0] and key_tuple[2] == "<module>":
                main_script_key = key_tuple
                break
        if main_script_key:
            total_time = stats.stats[main_script_key][3]  # cumtime
        else:  # Fallback to the very first entry's cumtime if main script isn't obvious
            # This might not be perfect but gives an estimate
            try:
                first_key = next(iter(stats.stats))
                total_time = stats.stats[first_key][3]
            except StopIteration:
                print(
                    f"Warning: Could not determine total time for {prof_file_path}, "
                    "stats object might be empty."
                )
                total_time = 0.0

    ipc_times = {name: 0.0 for name, _ in IPC_FUNCTION_PATTERNS}

    for func_data, func_stats_tuple in stats.stats.items():
        # func_data is a tuple: (filename, line_number, function_name)
        # func_stats_tuple is: (ncalls, nprimitives, tottime, cumtime, callers)

        tt = func_stats_tuple[2]  # tottime (time spent in this function only)

        func_full_name = f"{func_data[0]}:{func_data[1]}({func_data[2]})"

        for display_name, pattern in IPC_FUNCTION_PATTERNS:
            if re.search(pattern, func_full_name, re.IGNORECASE):
                ipc_times[
                    display_name
                ] += tt  # Sum tottime for these direct contributors

    return {"batch_size": batch_size, "total_time": total_time, **ipc_times}


def main():
    if not PROFILING_DIR.exists():
        print(f"Profiling directory not found: {PROFILING_DIR}")
        print("Please run the `run_batch_experiments_python.py` script first.")
        return

    PLOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_data = []
    prof_files = sorted(PROFILING_DIR.glob(f"{BASE_PROFILE_NAME_PREFIX}*.prof"))

    if not prof_files:
        print(
            f"No .prof files found in {PROFILING_DIR} matching prefix "
            f"'{BASE_PROFILE_NAME_PREFIX}'."
        )
        return

    for prof_file in prof_files:
        try:
            # Extract batch_size from filename, e.g., profile_batch_py_10000.prof
            match = re.search(r"_(\d+)\.prof$", prof_file.name)
            if match:
                batch_size = int(match.group(1))
                data = parse_prof_file(prof_file, batch_size)
                all_data.append(data)
            else:
                print(
                    f"Warning: Could not parse batch size from filename: "
                    f"{prof_file.name}"
                )
        except Exception as e:
            print(f"Error parsing file {prof_file}: {e}")
            continue

    if not all_data:
        print("No data parsed. Exiting.")
        return

    df = pd.DataFrame(all_data)
    if df.empty:
        print("DataFrame is empty after parsing. No plots will be generated.")
        return

    df = df.sort_values(by="batch_size").reset_index(drop=True)

    print("--- Parsed Data ---")
    print(df)

    # --- Plotting ---
    sns.set_theme(style="whitegrid")
    pastel_palette = sns.color_palette("pastel")

    # Plot 1: Total Execution Time vs. Batch Size
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        x="batch_size", y="total_time", data=df, marker="o", color=pastel_palette[0]
    )
    plt.title("Total Execution Time vs. Batch Size", fontsize=16)
    plt.xlabel("Batch Size", fontsize=12)
    plt.ylabel("Total Execution Time (seconds)", fontsize=12)
    plt.xscale("log")  # Batch sizes vary widely
    plt.grid(True, which="both", ls="--")
    plot_path = PLOT_OUTPUT_DIR / "total_time_vs_batch_size.png"
    plt.savefig(plot_path)
    print(f"Saved plot: {plot_path}")
    plt.close()

    # Plot 2: IPC-Related Times vs. Batch Size (Lines)
    ipc_cols = [name for name, _ in IPC_FUNCTION_PATTERNS]
    df_ipc = df[["batch_size"] + ipc_cols]

    plt.figure(figsize=(14, 8))
    df_ipc_melted = df_ipc.melt(
        id_vars="batch_size", var_name="IPC_Component", value_name="Time (s)"
    )

    sns.lineplot(
        x="batch_size",
        y="Time (s)",
        hue="IPC_Component",
        data=df_ipc_melted,
        marker="o",
        palette="pastel",
    )
    plt.title(
        "IPC/Multiprocessing Overhead Components vs. Batch Size (Line Plot)",
        fontsize=16,
    )
    plt.xlabel("Batch Size", fontsize=12)
    plt.ylabel("Sum of Top-Level Time (seconds, tottime in component)", fontsize=12)
    plt.xscale("log")
    plt.yscale("log")  # Times can also vary widely
    plt.grid(True, which="both", ls="--")
    plt.legend(title="IPC Component", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plot_path_ipc = PLOT_OUTPUT_DIR / "ipc_components_lines_vs_batch_size.png"
    plt.savefig(plot_path_ipc)
    print(f"Saved plot: {plot_path_ipc}")
    plt.close()

    # Plot 3: Stacked Bar chart for IPC components
    df_ipc_sum = df_ipc.set_index("batch_size")

    if not df_ipc_sum.empty:
        fig, ax = plt.subplots(figsize=(14, 8))
        # Using a perceptually uniform colormap for better distinction in stacked bars
        df_ipc_sum.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")

        ax.set_title("IPC/Multiprocessing Overhead (Stacked Bar)", fontsize=16)
        ax.set_xlabel("Batch Size", fontsize=12)
        ax.set_ylabel(
            "Sum of Top-Level Time (seconds, tottime in component)", fontsize=12
        )
        ax.set_xticklabels(
            [str(bs) for bs in df_ipc_sum.index], rotation=45, ha="right"
        )
        plt.legend(title="IPC Component", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout(rect=[0, 0, 0.85, 1])
        plot_path_ipc_stacked = PLOT_OUTPUT_DIR / "ipc_stacked_bar_vs_batch_size.png"
        plt.savefig(plot_path_ipc_stacked)
        print(f"Saved plot: {plot_path_ipc_stacked}")
        plt.close()
    else:
        print("No IPC data to plot for stacked bar chart.")

    print(f"--- All plots saved to {PLOT_OUTPUT_DIR} ---")


if __name__ == "__main__":
    main()
