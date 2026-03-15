import math
from typing import List


def calculate_uncertainty(values: List[float], coverage_factor: float = 2.0) -> dict:
    """
    Calculate measurement uncertainty from a list of repeated observations.

    Returns standard uncertainty, expanded uncertainty, coverage factor,
    and the associated confidence level string.
    """
    n = len(values)
    if n == 0:
        return {
            "standard_uncertainty": 0.0,
            "expanded_uncertainty": 0.0,
            "coverage_factor": coverage_factor,
            "confidence_level": "95% (k=2)",
        }

    mean = sum(values) / n

    if n == 1:
        # Cannot compute standard deviation from a single observation
        standard_uncertainty = 0.0
    else:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance)
        # Standard uncertainty of the mean
        standard_uncertainty = std_dev / math.sqrt(n)

    expanded_uncertainty = coverage_factor * standard_uncertainty

    # Map common coverage factors to confidence levels
    confidence_map = {
        1.0: "68%",
        1.645: "90%",
        1.960: "95%",
        2.0: "95% (k=2)",
        2.576: "99%",
        3.0: "99.7% (k=3)",
    }
    confidence_level = confidence_map.get(round(coverage_factor, 3), f"k={coverage_factor}")

    return {
        "standard_uncertainty": round(standard_uncertainty, 6),
        "expanded_uncertainty": round(expanded_uncertainty, 6),
        "coverage_factor": coverage_factor,
        "confidence_level": confidence_level,
    }
