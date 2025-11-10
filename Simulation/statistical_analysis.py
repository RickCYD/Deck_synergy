"""Statistical analysis tools for deck simulation validation.

This module provides statistical metrics to determine if the sample size
is sufficient for reliable conclusions about deck performance.
"""

from __future__ import annotations

import math
from typing import List, Dict, Tuple
import statistics


def calculate_confidence_interval(
    values: List[float],
    confidence_level: float = 0.95
) -> Tuple[float, float, float]:
    """Calculate mean and confidence interval for a sample.

    Parameters
    ----------
    values
        List of sample values
    confidence_level
        Confidence level (default 0.95 for 95% CI)

    Returns
    -------
    tuple
        (mean, lower_bound, upper_bound)
    """
    n = len(values)
    if n < 2:
        mean_val = values[0] if values else 0
        return mean_val, mean_val, mean_val

    mean_val = statistics.mean(values)
    std_dev = statistics.stdev(values)

    # For large samples (n >= 30), use Z-score. For small samples, use t-distribution
    if n >= 30:
        # Z-score for 95% confidence is 1.96, for 99% is 2.576
        z_score = 1.96 if confidence_level == 0.95 else 2.576
        margin_of_error = z_score * (std_dev / math.sqrt(n))
    else:
        # Simplified t-score approximation (conservative)
        # For exact values, would need scipy.stats.t.ppf
        t_score = 2.0 + (0.5 / math.sqrt(n))  # Conservative estimate
        margin_of_error = t_score * (std_dev / math.sqrt(n))

    return mean_val, mean_val - margin_of_error, mean_val + margin_of_error


def calculate_coefficient_of_variation(values: List[float]) -> float:
    """Calculate coefficient of variation (CV = std_dev / mean).

    CV tells us about relative variability:
    - CV < 0.1: Low variance, consistent results
    - CV 0.1-0.3: Moderate variance
    - CV > 0.3: High variance, less consistent

    Parameters
    ----------
    values
        List of sample values

    Returns
    -------
    float
        Coefficient of variation as a decimal (0.15 = 15%)
    """
    if len(values) < 2:
        return 0.0

    mean_val = statistics.mean(values)
    if mean_val == 0:
        return 0.0

    std_dev = statistics.stdev(values)
    return std_dev / abs(mean_val)


def recommend_sample_size(
    current_values: List[float],
    desired_margin_of_error: float = 0.05,
    confidence_level: float = 0.95
) -> Tuple[int, str]:
    """Recommend sample size based on observed variance.

    Parameters
    ----------
    current_values
        Current sample values
    desired_margin_of_error
        Desired margin of error as fraction of mean (0.05 = 5%)
    confidence_level
        Desired confidence level (default 0.95)

    Returns
    -------
    tuple
        (recommended_n, interpretation)
    """
    if len(current_values) < 2:
        return 100, "Insufficient data for recommendation"

    cv = calculate_coefficient_of_variation(current_values)
    n_current = len(current_values)

    # Z-score for confidence level
    z = 1.96 if confidence_level == 0.95 else 2.576

    # Required sample size: n = (z * cv / desired_error)^2
    required_n = math.ceil((z * cv / desired_margin_of_error) ** 2)

    # Interpretation
    if cv < 0.10:
        interpretation = f"✓ Low variance (CV={cv:.2f}). Current sample size ({n_current}) is sufficient."
        recommended_n = max(100, n_current)
    elif cv < 0.20:
        interpretation = f"⚠ Moderate variance (CV={cv:.2f}). Recommend {required_n} samples for {desired_margin_of_error*100:.0f}% margin of error."
        recommended_n = max(required_n, 200)
    elif cv < 0.30:
        interpretation = f"⚠ Moderate-high variance (CV={cv:.2f}). Recommend {required_n} samples for reliable results."
        recommended_n = max(required_n, 300)
    else:
        interpretation = f"✗ High variance (CV={cv:.2f}). Recommend {required_n}+ samples. Consider deck consistency issues."
        recommended_n = max(required_n, 500)

    return recommended_n, interpretation


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate percentile distribution of values.

    Parameters
    ----------
    values
        List of sample values

    Returns
    -------
    dict
        Percentiles (p10, p25, p50, p75, p90) plus min and max
    """
    if not values:
        return {
            "min": 0,
            "p10": 0,
            "p25": 0,
            "median": 0,
            "p75": 0,
            "p90": 0,
            "max": 0
        }

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return {
        "min": sorted_vals[0],
        "p10": sorted_vals[int(n * 0.10)],
        "p25": sorted_vals[int(n * 0.25)],
        "median": statistics.median(sorted_vals),
        "p75": sorted_vals[int(n * 0.75)],
        "p90": sorted_vals[int(n * 0.90)],
        "max": sorted_vals[-1]
    }


def analyze_metric_distribution(
    metric_name: str,
    values: List[float]
) -> Dict[str, any]:
    """Complete statistical analysis of a single metric.

    Parameters
    ----------
    metric_name
        Name of the metric being analyzed
    values
        List of values across all simulations

    Returns
    -------
    dict
        Complete statistical summary including:
        - Basic stats (mean, median, std, min, max)
        - Confidence intervals
        - Coefficient of variation
        - Percentiles
        - Sample size recommendation
    """
    if not values or len(values) < 2:
        return {
            "metric": metric_name,
            "n": len(values),
            "error": "Insufficient data"
        }

    mean_val, ci_lower, ci_upper = calculate_confidence_interval(values)
    cv = calculate_coefficient_of_variation(values)
    percentiles = calculate_percentiles(values)
    recommended_n, interpretation = recommend_sample_size(values)

    return {
        "metric": metric_name,
        "n": len(values),
        "mean": round(mean_val, 2),
        "median": round(percentiles["median"], 2),
        "std_dev": round(statistics.stdev(values), 2),
        "min": round(percentiles["min"], 2),
        "max": round(percentiles["max"], 2),
        "ci_95_lower": round(ci_lower, 2),
        "ci_95_upper": round(ci_upper, 2),
        "margin_of_error": round((ci_upper - ci_lower) / 2, 2),
        "margin_of_error_pct": round(((ci_upper - ci_lower) / 2 / mean_val * 100) if mean_val != 0 else 0, 1),
        "coefficient_of_variation": round(cv, 3),
        "percentiles": {k: round(v, 2) for k, v in percentiles.items()},
        "recommended_n": recommended_n,
        "interpretation": interpretation
    }


def summarize_simulation_validity(
    key_metrics: Dict[str, List[float]],
    num_games: int
) -> Dict[str, any]:
    """Generate overall assessment of simulation validity.

    Parameters
    ----------
    key_metrics
        Dictionary mapping metric names to lists of per-game values
    num_games
        Number of games simulated

    Returns
    -------
    dict
        Overall validity assessment including:
        - Per-metric analysis
        - Overall recommendation
        - Variance assessment
    """
    metric_analyses = {}
    cvs = []
    recommended_ns = []

    for metric_name, values in key_metrics.items():
        analysis = analyze_metric_distribution(metric_name, values)
        metric_analyses[metric_name] = analysis

        if "coefficient_of_variation" in analysis:
            cvs.append(analysis["coefficient_of_variation"])
            recommended_ns.append(analysis["recommended_n"])

    # Overall assessment
    avg_cv = statistics.mean(cvs) if cvs else 0
    max_recommended_n = max(recommended_ns) if recommended_ns else num_games

    if avg_cv < 0.10:
        overall_status = "EXCELLENT"
        overall_message = f"✓ Current sample size ({num_games}) is sufficient. Low variance across metrics."
    elif avg_cv < 0.20:
        overall_status = "GOOD"
        overall_message = f"✓ Current sample size ({num_games}) provides reasonable estimates. Consider {max_recommended_n} for higher precision."
    elif avg_cv < 0.30:
        overall_status = "FAIR"
        overall_message = f"⚠ Moderate variance detected. Recommend {max_recommended_n} samples for reliable results."
    else:
        overall_status = "NEEDS IMPROVEMENT"
        overall_message = f"✗ High variance detected. Recommend {max_recommended_n}+ samples. Deck may have consistency issues."

    return {
        "num_games": num_games,
        "overall_status": overall_status,
        "overall_message": overall_message,
        "avg_coefficient_of_variation": round(avg_cv, 3),
        "recommended_sample_size": max_recommended_n,
        "metric_analyses": metric_analyses
    }


def format_statistical_report(validity_summary: Dict[str, any]) -> str:
    """Format statistical analysis into readable report.

    Parameters
    ----------
    validity_summary
        Output from summarize_simulation_validity()

    Returns
    -------
    str
        Formatted text report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("STATISTICAL VALIDITY REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Sample Size: {validity_summary['num_games']} games")
    lines.append(f"Overall Status: {validity_summary['overall_status']}")
    lines.append(f"Average CV: {validity_summary['avg_coefficient_of_variation']:.3f}")
    lines.append(f"Recommended N: {validity_summary['recommended_sample_size']}")
    lines.append("")
    lines.append(validity_summary['overall_message'])
    lines.append("")
    lines.append("-" * 80)
    lines.append("PER-METRIC ANALYSIS")
    lines.append("-" * 80)
    lines.append("")

    for metric_name, analysis in validity_summary['metric_analyses'].items():
        if "error" in analysis:
            lines.append(f"❌ {metric_name}: {analysis['error']}")
            continue

        lines.append(f"📊 {metric_name}")
        lines.append(f"   Mean: {analysis['mean']:.2f} ± {analysis['margin_of_error']:.2f} ({analysis['margin_of_error_pct']:.1f}%)")
        lines.append(f"   95% CI: [{analysis['ci_95_lower']:.2f}, {analysis['ci_95_upper']:.2f}]")
        lines.append(f"   Median: {analysis['median']:.2f} | Std Dev: {analysis['std_dev']:.2f}")
        lines.append(f"   Range: [{analysis['min']:.2f}, {analysis['max']:.2f}]")
        lines.append(f"   CV: {analysis['coefficient_of_variation']:.3f} | Recommended N: {analysis['recommended_n']}")
        lines.append(f"   {analysis['interpretation']}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("")
    lines.append("INTERPRETATION GUIDE:")
    lines.append("  • CV < 0.10: Low variance, very consistent")
    lines.append("  • CV 0.10-0.20: Moderate variance, reasonable consistency")
    lines.append("  • CV 0.20-0.30: Moderate-high variance")
    lines.append("  • CV > 0.30: High variance, consider deck consistency issues")
    lines.append("")
    lines.append("  • Margin of Error: ±X means true value is likely within X of reported mean")
    lines.append("  • 95% CI: We're 95% confident the true mean lies in this range")
    lines.append("=" * 80)

    return "\n".join(lines)
