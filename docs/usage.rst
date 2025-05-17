Usage Guide
===========

This guide explains how to use the `KolmogorovComplexityEstimatorPythonPackage` for running CTM simulations and estimating Kolmogorov complexity.

Using the Command-Line Scripts
------------------------------

The package provides two main example scripts in the `examples/` directory:

1.  `run_ctm_simulation.py`: For running CTM simulations to generate :math:`D(n,m)` distributions.
2.  `estimate_complexity_from_file.py`: For estimating :math:`K(s)` using a precomputed :math:`D(n,m)` distribution file.

### `run_ctm_simulation.py`

This script orchestrates the enumeration of Turing machines, their simulation, and the aggregation of output frequencies.

**Command-Line Arguments:**

*   `--n_states` (int, required): The number of states (n) for the Turing machines to simulate.
*   `--max_runtime_steps` (int, required): The maximum number of simulation steps to run each Turing machine before considering it non-halting (timeout).
*   `--output_file_path` (str, required): Path to save the resulting :math:`D(n,m)` distribution (or raw counts) as a JSON file.
*   `--use_reduced_enumeration` (flag, optional): If set, uses the reduced enumeration strategy described in the paper. Default is to use raw enumeration.
*   `--blank_symbol` (str, optional): The blank symbol to use for the tape (e.g., '0' or '1'). Defaults to '0'. Note: Completion rules, if used with reduced enumeration, typically handle symmetry for the other blank symbol.
*   `--checkpoint_interval` (int, optional): Save simulation state every N machines. Useful for long runs. Default might be disabled or a large number.
*   `--num_machines_to_run` (int, optional): Run only the first N machines from the enumerator. Useful for testing or partial runs. By default, runs all machines in the selected enumeration.
*   `--log_level` (str, optional): Set logging level (e.g., DEBUG, INFO, WARNING). Defaults to INFO.
*   `--save_raw_counts` (flag, optional): If set, saves the raw output counts and non-halting statistics instead of the final D(n,m) probability distribution. This can be useful for later custom processing or merging.

**Example:**

.. code-block:: bash

   python examples/run_ctm_simulation.py \
       --n_states 3 \
       --max_runtime_steps 200 \
       --output_file_path examples/d_3_states_200_steps.json \
       --use_reduced_enumeration \
       --checkpoint_interval 10000

This command will simulate 3-state Turing machines, using reduced enumeration, for a maximum of 200 steps each. The output distribution will be saved to `examples/d_3_states_200_steps.json`, and checkpoints will be saved every 10,000 machines processed.

### `estimate_complexity_from_file.py`

This script loads a precomputed :math:`D(n,m)` distribution and uses it to estimate Kolmogorov complexity or rank strings.

**Command-Line Arguments:**

*   `--distribution_file` (str, required): Path to the JSON file containing the :math:`D(n,m)` distribution (output from `run_ctm_simulation.py`).
*   `--string` (str, optional): A specific binary string for which to estimate :math:`K(s)`.
*   `--top_n` (int, optional): If provided, lists the top N strings with the lowest estimated complexity from the distribution.
*   `--input_strings_file` (str, optional): Path to a file containing multiple binary strings (one per line) for which to estimate complexity.

**Examples:**

1.  Estimate complexity for a single string:

    .. code-block:: bash

       python examples/estimate_complexity_from_file.py \
           --distribution_file examples/d_3_states_200_steps.json \
           --string "101"

2.  List the top 10 simplest strings:

    .. code-block:: bash

       python examples/estimate_complexity_from_file.py \
           --distribution_file examples/d_3_states_200_steps.json \
           --top_n 10

3.  Estimate complexity for strings in a file:

    .. code-block:: bash

       python examples/estimate_complexity_from_file.py \
           --distribution_file examples/d_3_states_200_steps.json \
           --input_strings_file my_strings.txt

    (Where `my_strings.txt` contains one binary string per line.)


Using the Package Programmatically
----------------------------------

You can also use the core classes of the package in your own Python scripts.

### `KolmogorovComplexityEstimator`

The `KolmogorovComplexityEstimator` class from `kolmogorov_complexity_estimator.complexity_engine` is used to load a :math:`D(n,m)` distribution and estimate complexities.

.. code-block:: python

   from kolmogorov_complexity_estimator.complexity_engine import KolmogorovComplexityEstimator

   # Load a distribution from a file
   estimator = KolmogorovComplexityEstimator(D_distribution_path_or_dict='path/to/your/d_n_m.json')

   # Estimate K(s) for a string
   k_value = estimator.estimate_K("01101")
   if k_value is not None:
       print(f"Estimated K('01101') = {k_value:.4f}")
   else:
       print("String '01101' not found in the distribution.")

   # Get the top 5 ranked strings
   top_strings = estimator.get_ranked_strings(top_n=5)
   print("\nTop 5 simplest strings:")
   for s, k in top_strings:
       print(f"  K('{s}') = {k:.4f}")

### Other Components

While direct use of other components like `TuringMachine`, `tm_enumerator`, or `OutputFrequencyDistribution` is possible for advanced scenarios or custom simulation loops, the `run_ctm_simulation.py` script provides a comprehensive interface for most simulation needs.

If you need to implement a custom simulation pipeline, you would typically:

1.  Initialize `OutputFrequencyDistribution`.
2.  Use a generator from `tm_enumerator` (`generate_raw_tm_tables` or `generate_reduced_tm_tables`).
3.  For each TM table from the enumerator:
    a.  Optionally apply pre-run filters (e.g., `has_no_halt_transition` from `reduction_filters`).
    b.  Instantiate `TuringMachine`.
    c.  Call the `run()` method on the TM instance, possibly passing runtime filter functions (e.g., `check_for_escapee`, `check_for_cycle_two` from `reduction_filters`).
    d.  Record the outcome using `OutputFrequencyDistribution.record_run_outcome()`.
4.  If using reduced enumeration, call `OutputFrequencyDistribution.apply_completion_rules()`.
5.  Calculate the final distribution using `OutputFrequencyDistribution.calculate_D_distribution()`.
6.  Save the distribution.

Consult the API documentation (generated by Sphinx, see `docs/api.rst` or `docs/_build/html/api.html`) for detailed information on the classes and their methods. 