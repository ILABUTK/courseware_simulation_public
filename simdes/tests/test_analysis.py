"""Unit tests for output analysis utilities."""

import numpy as np
import pytest

from simdes.analysis.ci import confidence_interval, n_reps_required
from simdes.analysis.replications import batch_means
from simdes.analysis.warmup import welch_method
from simdes.analysis.scenarios import compare_scenarios, paired_crn


class TestConfidenceInterval:
    def test_ci_contains_true_mean(self):
        """95% CI should contain the true mean in a large majority of trials."""
        rng = np.random.default_rng(0)
        true_mean = 5.0
        hits = 0
        for _ in range(200):
            data = rng.normal(loc=true_mean, scale=1.0, size=20)
            mean, lo, hi = confidence_interval(data)
            if lo <= true_mean <= hi:
                hits += 1
        assert hits >= 180, f"Only {hits}/200 CIs contained the true mean"

    def test_ci_ordering(self):
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mean, lo, hi = confidence_interval(data)
        assert lo < mean < hi

    def test_too_few_observations(self):
        with pytest.raises(ValueError):
            confidence_interval([3.0])


class TestNRepsRequired:
    def test_returns_positive_integer(self):
        n = n_reps_required(pilot_std=2.0, half_width=0.5)
        assert isinstance(n, int) and n >= 1

    def test_wider_hw_needs_fewer_reps(self):
        n_narrow = n_reps_required(pilot_std=2.0, half_width=0.1)
        n_wide = n_reps_required(pilot_std=2.0, half_width=1.0)
        assert n_narrow > n_wide


class TestBatchMeans:
    def test_shape(self):
        data = np.arange(100, dtype=float)
        bm = batch_means(data, n_batches=5)
        assert bm.shape == (5,)

    def test_too_short(self):
        with pytest.raises(ValueError):
            batch_means(np.ones(3), n_batches=10)


class TestWelchMethod:
    def test_output_length(self):
        rng = np.random.default_rng(1)
        reps = rng.normal(loc=3.0, size=(5, 100))
        t, y = welch_method(reps, window=5)
        assert len(t) == 100
        assert len(y) == 100

    def test_1d_input(self):
        rng = np.random.default_rng(2)
        series = rng.normal(size=50)
        t, y = welch_method(series, window=3)
        assert len(t) == 50


class TestScenarioComparison:
    def test_compare_returns_two_rows(self):
        rng = np.random.default_rng(3)
        a = rng.normal(loc=2.0, size=20)
        b = rng.normal(loc=3.0, size=20)
        df = compare_scenarios(a, b)
        assert len(df) == 2
        assert "mean" in df.columns

    def test_paired_crn_mean_diff(self):
        rng = np.random.default_rng(4)
        a = rng.normal(loc=1.0, size=30)
        b = a + 0.5  # deterministic shift
        result = paired_crn(a, b)
        assert abs(result["mean_diff"] - (-0.5)) < 0.01

    def test_paired_crn_length_mismatch(self):
        with pytest.raises(ValueError):
            paired_crn(np.ones(10), np.ones(12))
