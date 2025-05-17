Methodology: The Coding Theorem Method (CTM)
==============================================

This document provides a summary of the Coding Theorem Method (CTM) used in this package to estimate Kolmogorov complexity. It is based on the principles outlined in the paper "Calculating Kolmogorov Complexity from the Output Frequency Distributions of Small Turing Machines" by Soler-Toscano, Zenil, Delahaye, and Gauvrit (2014).

1. Kolmogorov-Chaitin Complexity
---------------------------------
Kolmogorov-Chaitin complexity of a string :math:`s` with respect to a universal Turing machine (UTM) :math:`T` is defined as:

.. math::

   K_T(s) = \min\{|p| : T(p) = s\}

where :math:`p` is a binary program that, when executed on :math:`T`, outputs :math:`s`. :math:`K(s)` is uncomputable in general.

The **Invariance Theorem** states that for any two UTMs :math:`U_1` and :math:`U_2`, there exists a constant :math:`c` such that for all strings :math:`s`:

.. math::

   |K_{U_1}(s) - K_{U_2}(s)| \le c

This means the choice of UTM affects the complexity value by at most an additive constant.

2. Solomonoff-Levin Algorithmic Probability
-------------------------------------------
The algorithmic probability of a string :math:`s` with respect to a universal prefix-free Turing machine :math:`U` is:

.. math::

   \mathfrak{m}(s) = \sum_{p : U(p) = s} 2^{-|p|}

where the sum is over all binary programs :math:`p` that output :math:`s` and halt. :math:`\mathfrak{m}(s)` is a universal prior and is lower semi-computable.

3. The Coding Theorem
---------------------
The Coding Theorem establishes a fundamental relationship between Kolmogorov complexity and algorithmic probability:

.. math::

   K(s) = -\log_2 \mathfrak{m}(s) + O(1)

This theorem implies that strings with higher algorithmic probability (i.e., those more frequently produced by random programs) have lower Kolmogorov complexity.

4. The Coding Theorem Method (CTM)
----------------------------------
CTM approximates :math:`K(s)` by estimating :math:`\mathfrak{m}(s)` through empirical means.

   a. **Turing Machine Enumeration and Execution**:
      A large set of small Turing machines (e.g., with :math:`n` states and :math:`m` symbols, typically :math:`m=2`) are systematically enumerated and simulated.
      The simulations are run for a predefined maximum number of steps (runtime cutoff). The paper uses values like 107 steps for 4-state TMs and 500 steps for 5-state TMs.

   b. **Output Frequency Distribution :math:`D(n,m)`**:
      The outputs of all halting Turing machines are collected. The frequency distribution :math:`D(n,m)(s)` is calculated as:

      .. math::

         D(n,m)(s) = \frac{\|\{T \in (n,m) : T \text{ outputs } s\}\|}{\|\{T \in (n,m) : T \text{ halts}\}\|}

      This empirical distribution :math:`D(n,m)(s)` serves as an approximation of :math:`\mathfrak{m}(s)`.

   c. **Reduction Techniques**:
      To manage the vast number of Turing machines, CTM employs several reduction techniques:
      *   **Reduced Enumeration**: Symmetries (e.g., blank-symbol complements, left-right mirror, trivial initial transitions) are exploited to run only a representative subset of machines. The paper details a scheme that reduces the number of 5-state machines to roughly 4/11 of the total.
      *   **Pre-run Filters**: Machines that can be identified as non-halting from their transition table (e.g., no transition to a halt state) are filtered out before simulation.
      *   **Runtime Filters**: During simulation, non-halting behaviors are detected:
          *   **Escapees**: Machines moving monotonically on fresh blank cells while repeating states.
          *   **Period-2 Cycles**: Machines caught in a two-step loop where tape and state repeat.

   d. **Output Completion**:
      When a reduced enumeration is used, the resulting output counts are analytically completed to reflect the full space of machines. This involves accounting for:
      *   Symmetry of the blank symbol (e.g., if run with '0' as blank, results are complemented for '1' as blank).
      *   Right-left movement symmetry (reversing strings).
      *   Contributions from machines with initial halting or self-looping transitions that were excluded by the reduced enumeration.

   e. **Complexity Estimation**:
      Finally, the estimated Kolmogorov complexity :math:`\hat{K}(s)` is calculated from the completed :math:`D(n,m)(s)` distribution using the Coding Theorem:

      .. math::

         \hat{K}(s) = -\log_2 D(n,m)(s)

      This :math:`\hat{K}(s)` approximates the true :math:`K(s)` up to an additive constant, especially for the chosen class of (n,m) Turing machines.

For a more detailed discussion, refer to the original paper:

*   Soler-Toscano, F., Zenil, H., Delahaye, J.-P., & Gauvrit, N. (2014). Calculating Kolmogorov Complexity from the Output Frequency Distributions of Small Turing Machines. *PLoS ONE, 9*(5), e96223. `https://doi.org/10.1371/journal.pone.0096223 <https://doi.org/10.1371/journal.pone.0096223>`_ 