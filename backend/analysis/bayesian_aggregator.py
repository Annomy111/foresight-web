"""Robust Bayesian Expert Aggregation for handling conflicting forecasts"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy.stats import beta, norm, truncnorm
from scipy.special import logsumexp
import warnings

logger = logging.getLogger(__name__)


class BayesianAggregator:
    """
    Implements Robust Bayesian Expert Aggregation for combining
    potentially conflicting probabilistic forecasts.
    """

    def __init__(self, prior_strength: float = 1.0, outlier_threshold: float = 2.5):
        """
        Initialize Bayesian aggregator

        Args:
            prior_strength: Strength of prior belief (higher = more conservative)
            outlier_threshold: Z-score threshold for outlier detection
        """
        self.prior_strength = prior_strength
        self.outlier_threshold = outlier_threshold
        self.expert_weights = {}
        self.historical_performance = {}

    def aggregate_forecasts(
        self,
        forecasts: List[float],
        expert_ids: Optional[List[str]] = None,
        confidences: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate forecasts using Bayesian pooling

        Args:
            forecasts: List of probability forecasts (0-100)
            expert_ids: Optional list of expert/model identifiers
            confidences: Optional list of confidence scores for each forecast

        Returns:
            Dictionary with aggregated forecast and metadata
        """
        if not forecasts:
            return {"error": "No forecasts provided"}

        # Convert to 0-1 range
        probs = np.array(forecasts) / 100.0

        # Generate default expert IDs if not provided
        if expert_ids is None:
            expert_ids = [f"expert_{i}" for i in range(len(forecasts))]

        # Generate default confidences if not provided
        if confidences is None:
            confidences = np.ones(len(forecasts))
        else:
            confidences = np.array(confidences)

        # Detect and handle outliers
        outlier_mask = self._detect_outliers(probs)
        if np.any(outlier_mask):
            logger.info(f"Detected {np.sum(outlier_mask)} outliers in forecasts")

        # Calculate weights for each expert
        weights = self._calculate_expert_weights(
            probs, expert_ids, confidences, outlier_mask
        )

        # Perform Bayesian aggregation
        aggregated = self._bayesian_pool(probs, weights)

        # Calculate uncertainty
        uncertainty = self._calculate_uncertainty(probs, weights)

        # Update historical performance
        self._update_expert_performance(expert_ids, probs, aggregated["mean"])

        return {
            "aggregated_probability": float(aggregated["mean"] * 100),
            "confidence_interval": [
                float(aggregated["lower"] * 100),
                float(aggregated["upper"] * 100)
            ],
            "uncertainty": uncertainty,
            "expert_weights": dict(zip(expert_ids, weights.tolist())),
            "outliers_detected": int(np.sum(outlier_mask)),
            "method": "robust_bayesian",
            "posterior_variance": float(aggregated["variance"])
        }

    def _detect_outliers(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Detect outliers using robust statistics

        Args:
            probabilities: Array of probabilities (0-1)

        Returns:
            Boolean mask indicating outliers
        """
        if len(probabilities) < 3:
            return np.zeros(len(probabilities), dtype=bool)

        # Use median absolute deviation (MAD) for robust outlier detection
        median = np.median(probabilities)
        mad = np.median(np.abs(probabilities - median))

        # Modified Z-score using MAD
        if mad > 0:
            modified_z_scores = 0.6745 * (probabilities - median) / mad
            outliers = np.abs(modified_z_scores) > self.outlier_threshold
        else:
            # If MAD is 0, use IQR method
            q1, q3 = np.percentile(probabilities, [25, 75])
            iqr = q3 - q1
            if iqr > 0:
                outliers = (probabilities < q1 - 1.5 * iqr) | (probabilities > q3 + 1.5 * iqr)
            else:
                outliers = np.zeros(len(probabilities), dtype=bool)

        return outliers

    def _calculate_expert_weights(
        self,
        probabilities: np.ndarray,
        expert_ids: List[str],
        confidences: np.ndarray,
        outlier_mask: np.ndarray
    ) -> np.ndarray:
        """
        Calculate weights for each expert based on multiple factors

        Args:
            probabilities: Array of probability forecasts
            expert_ids: List of expert identifiers
            confidences: Array of confidence scores
            outlier_mask: Boolean mask for outliers

        Returns:
            Array of expert weights
        """
        n_experts = len(probabilities)
        weights = np.ones(n_experts)

        # 1. Confidence-based weighting
        weights *= confidences

        # 2. Outlier penalty
        weights[outlier_mask] *= 0.1  # Heavily down-weight outliers

        # 3. Historical performance weighting
        for i, expert_id in enumerate(expert_ids):
            if expert_id in self.historical_performance:
                perf = self.historical_performance[expert_id]
                # Weight based on historical accuracy (inverse Brier score)
                hist_weight = 1.0 / (1.0 + perf.get("avg_error", 0.5))
                weights[i] *= hist_weight

        # 4. Agreement with consensus (iterative refinement)
        for _ in range(3):  # Few iterations to converge
            weighted_mean = np.average(probabilities, weights=weights)
            distances = np.abs(probabilities - weighted_mean)
            agreement_weights = 1.0 / (1.0 + distances * 5)  # Penalize disagreement
            weights *= agreement_weights

        # Normalize weights
        weights = weights / np.sum(weights)

        return weights

    def _bayesian_pool(
        self,
        probabilities: np.ndarray,
        weights: np.ndarray
    ) -> Dict[str, float]:
        """
        Perform Bayesian pooling of probability estimates

        Args:
            probabilities: Array of probabilities (0-1)
            weights: Array of expert weights

        Returns:
            Dictionary with pooled estimates
        """
        # Use Beta distribution for Bayesian updating
        # Prior: uniform Beta(1, 1) modified by prior_strength
        alpha_prior = self.prior_strength
        beta_prior = self.prior_strength

        # Update with expert opinions
        # Convert probabilities to pseudo-counts
        n_virtual_samples = 10  # Virtual sample size for each expert

        alpha_updates = probabilities * weights * n_virtual_samples
        beta_updates = (1 - probabilities) * weights * n_virtual_samples

        # Posterior parameters
        alpha_post = alpha_prior + np.sum(alpha_updates)
        beta_post = beta_prior + np.sum(beta_updates)

        # Posterior distribution
        posterior_dist = beta(alpha_post, beta_post)

        # Extract statistics
        mean = posterior_dist.mean()
        variance = posterior_dist.var()

        # Confidence interval (95%)
        lower = posterior_dist.ppf(0.025)
        upper = posterior_dist.ppf(0.975)

        return {
            "mean": mean,
            "variance": variance,
            "lower": lower,
            "upper": upper,
            "alpha": alpha_post,
            "beta": beta_post
        }

    def _calculate_uncertainty(
        self,
        probabilities: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """
        Calculate uncertainty measure for the aggregation

        Args:
            probabilities: Array of probabilities
            weights: Array of weights

        Returns:
            Uncertainty score (0-1)
        """
        # Multiple uncertainty components

        # 1. Variance in predictions
        weighted_mean = np.average(probabilities, weights=weights)
        variance = np.average((probabilities - weighted_mean)**2, weights=weights)

        # 2. Entropy of weights (concentration)
        weight_entropy = -np.sum(weights * np.log(weights + 1e-10))
        max_entropy = np.log(len(weights))
        normalized_entropy = weight_entropy / max_entropy if max_entropy > 0 else 0

        # 3. Disagreement measure
        pairwise_distances = []
        for i in range(len(probabilities)):
            for j in range(i+1, len(probabilities)):
                dist = abs(probabilities[i] - probabilities[j])
                pairwise_distances.append(dist * weights[i] * weights[j])

        avg_disagreement = np.mean(pairwise_distances) if pairwise_distances else 0

        # Combine uncertainty measures
        uncertainty = (variance + normalized_entropy + avg_disagreement) / 3

        return float(np.clip(uncertainty, 0, 1))

    def _update_expert_performance(
        self,
        expert_ids: List[str],
        predictions: np.ndarray,
        consensus: float
    ):
        """
        Update historical performance tracking for experts

        Args:
            expert_ids: List of expert identifiers
            predictions: Their predictions
            consensus: The consensus prediction
        """
        for expert_id, pred in zip(expert_ids, predictions):
            if expert_id not in self.historical_performance:
                self.historical_performance[expert_id] = {
                    "predictions": [],
                    "errors": [],
                    "avg_error": 0.5
                }

            # Track prediction
            self.historical_performance[expert_id]["predictions"].append(pred)

            # Track error relative to consensus
            error = abs(pred - consensus)
            self.historical_performance[expert_id]["errors"].append(error)

            # Update running average error
            errors = self.historical_performance[expert_id]["errors"]
            self.historical_performance[expert_id]["avg_error"] = np.mean(errors[-20:])  # Last 20

    def supra_bayesian_aggregation(
        self,
        model_distributions: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Advanced Supra-Bayesian aggregation for full probability distributions

        Args:
            model_distributions: Dict mapping models to their distribution parameters
                                Each should have 'mean' and 'variance'

        Returns:
            Aggregated distribution parameters
        """
        if not model_distributions:
            return {"error": "No distributions provided"}

        # Extract means and variances
        means = []
        variances = []
        model_names = []

        for model, dist in model_distributions.items():
            means.append(dist.get("mean", 0.5))
            variances.append(dist.get("variance", 0.01))
            model_names.append(model)

        means = np.array(means)
        variances = np.array(variances)

        # Calculate precision (inverse variance) weights
        precisions = 1.0 / (variances + 1e-10)
        weights = precisions / np.sum(precisions)

        # Pooled mean (precision-weighted)
        pooled_mean = np.sum(weights * means)

        # Pooled variance (accounting for both within and between model variance)
        within_variance = 1.0 / np.sum(precisions)
        between_variance = np.sum(weights * (means - pooled_mean)**2)
        pooled_variance = within_variance + between_variance

        # Calculate credible interval
        pooled_std = np.sqrt(pooled_variance)
        lower_ci = pooled_mean - 1.96 * pooled_std
        upper_ci = pooled_mean + 1.96 * pooled_std

        return {
            "pooled_mean": float(pooled_mean * 100),  # Convert to percentage
            "pooled_variance": float(pooled_variance),
            "pooled_std": float(pooled_std),
            "credible_interval": [
                float(max(0, lower_ci) * 100),
                float(min(1, upper_ci) * 100)
            ],
            "model_weights": dict(zip(model_names, weights.tolist())),
            "method": "supra_bayesian"
        }

    def evidence_based_update(
        self,
        prior_prob: float,
        evidence: Dict[str, Any]
    ) -> float:
        """
        Update probability based on new evidence using Bayesian updating

        Args:
            prior_prob: Prior probability (0-100)
            evidence: Dictionary containing evidence strength and direction

        Returns:
            Updated probability
        """
        prior = prior_prob / 100.0

        # Extract evidence parameters
        likelihood_ratio = evidence.get("likelihood_ratio", 1.0)
        confidence = evidence.get("confidence", 1.0)

        # Apply Bayesian update with confidence weighting
        if likelihood_ratio != 1.0:
            # Temper the update by confidence
            effective_lr = 1.0 + (likelihood_ratio - 1.0) * confidence

            # Bayes' rule
            odds_prior = prior / (1 - prior + 1e-10)
            odds_post = odds_prior * effective_lr
            posterior = odds_post / (1 + odds_post)
        else:
            posterior = prior

        return float(posterior * 100)