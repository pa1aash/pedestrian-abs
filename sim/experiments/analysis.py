"""Statistical analysis utilities for experiment results."""

import numpy as np
from scipy import stats


class Stats:
    """Collection of statistical analysis methods."""

    @staticmethod
    def confidence_interval(data: np.ndarray, confidence: float = 0.95) -> tuple[float, float, float]:
        """Compute mean and 95% CI.

        Returns:
            (mean, ci_lower, ci_upper).
        """
        data = np.asarray(data)
        n = len(data)
        mean = float(np.mean(data))
        if n < 2:
            return mean, mean, mean
        se = float(stats.sem(data))
        t_crit = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_crit * se
        return mean, mean - margin, mean + margin

    @staticmethod
    def paired_ttest(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
        """Paired t-test.

        Returns:
            (t_statistic, p_value).
        """
        a, b = np.asarray(a), np.asarray(b)
        t_stat, p_val = stats.ttest_rel(a, b)
        return float(t_stat), float(p_val)

    @staticmethod
    def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
        """Cohen's d effect size for paired samples."""
        a, b = np.asarray(a), np.asarray(b)
        diff = a - b
        return float(np.mean(diff) / max(np.std(diff, ddof=1), 1e-10))

    @staticmethod
    def rmse(predicted: np.ndarray, observed: np.ndarray) -> float:
        """Root mean squared error."""
        return float(np.sqrt(np.mean((np.asarray(predicted) - np.asarray(observed)) ** 2)))

    @staticmethod
    def ks_test(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
        """Two-sample Kolmogorov-Smirnov test.

        Returns:
            (ks_statistic, p_value).
        """
        stat, p_val = stats.ks_2samp(a, b)
        return float(stat), float(p_val)

    @staticmethod
    def normality(data: np.ndarray) -> tuple[float, float]:
        """Shapiro-Wilk normality test.

        Returns:
            (w_statistic, p_value).
        """
        data = np.asarray(data)
        if len(data) < 3:
            return 1.0, 1.0
        w, p = stats.shapiro(data)
        return float(w), float(p)
