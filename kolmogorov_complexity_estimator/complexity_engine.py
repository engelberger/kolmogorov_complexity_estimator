# Applies Coding Theorem to D(n,m) to get K_m(s) 
import json
import math
from typing import Union, Dict, List, Tuple, Optional

class KolmogorovComplexityEstimator:
    """
    Estimate Kolmogorov complexity from a D(n,m) distribution via the Coding Theorem:
    K_m(s) = -log2 D(n,m)(s)
    """
    def __init__(
        self,
        D_distribution_path_or_dict: Union[str, Dict[str, float]]
    ):
        """
        Initialize the estimator with a distribution.

        :param D_distribution_path_or_dict: Path to JSON file containing 'D_distribution',
               or a dict mapping strings to probabilities.
        """
        if isinstance(D_distribution_path_or_dict, str):
            with open(D_distribution_path_or_dict) as f:
                data = json.load(f)
            # Extract distribution
            if 'D_distribution' in data:
                D = data['D_distribution']
            else:
                D = data  # assume file itself is the distribution
        else:
            D = D_distribution_path_or_dict
        # Store distribution
        self.D: Dict[str, float] = D
        # Precompute K values, handling zero probabilities
        self.K: Dict[str, float] = {}
        for s, p in self.D.items():
            if p is None or p <= 0:
                self.K[s] = float('inf')
            else:
                self.K[s] = -math.log2(p)

    def estimate_K(self, s: str) -> float:
        """
        Estimate K(s) given the loaded distribution.

        :param s: Binary string for which to estimate complexity.
        :return: Estimated Kolmogorov complexity (float), inf if unknown or p=0.
        """
        return self.K.get(s, float('inf'))

    def get_ranked_strings(
        self,
        top_n: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Get strings ranked by increasing complexity (lower K first).

        :param top_n: If provided, return only the top_n entries.
        :return: List of (string, K) tuples sorted by K.
        """
        ranked = sorted(self.K.items(), key=lambda item: item[1])
        if top_n is not None:
            return ranked[:top_n]
        return ranked 