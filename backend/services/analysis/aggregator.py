"""Statistical aggregation and analysis of ensemble forecast results"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict

from services.core.models import ModelResponse, EnsembleStatistics, ModelStatistics
from services.analysis.calibration import BatchCalibrator, MultiModelCalibrator
from services.analysis.consistency_scorer import ConsistencyScorer
from services.analysis.bayesian_aggregator import BayesianAggregator

logger = logging.getLogger(__name__)


class ForecastAggregator:
    """Aggregates and analyzes ensemble forecast results with multiple advanced methods"""

    def __init__(self, method: str = "ensemble"):
        """
        Initialize aggregator with specified method

        Args:
            method: Aggregation method ('simple', 'calibrated', 'bayesian', 'consistency', 'ensemble')
        """
        self.method = method
        self.calibrator = BatchCalibrator(method="temperature")
        self.multi_calibrator = MultiModelCalibrator()
        self.consistency_scorer = ConsistencyScorer()
        self.bayesian_aggregator = BayesianAggregator()

    def aggregate_results(self, responses: List[ModelResponse]) -> EnsembleStatistics:
        """
        Aggregate forecast results into comprehensive statistics

        Args:
            responses: List of model responses

        Returns:
            EnsembleStatistics with aggregated data
        """
        # Separate successful responses
        successful_responses = [r for r in responses if r.status.value == "success"]
        valid_probabilities = [r.probability for r in successful_responses if r.probability is not None]

        # Group by model
        model_groups = defaultdict(list)
        for response in responses:
            model_groups[response.model].append(response)

        # Calculate per-model statistics
        model_stats = {}
        for model, model_responses in model_groups.items():
            model_stats[model] = self._calculate_model_statistics(model, model_responses)

        # Calculate overall statistics
        overall_stats = {}
        if valid_probabilities:
            overall_stats = {
                "mean": float(np.mean(valid_probabilities)),
                "median": float(np.median(valid_probabilities)),
                "std": float(np.std(valid_probabilities, ddof=1) if len(valid_probabilities) > 1 else 0),
                "min": float(min(valid_probabilities)),
                "max": float(max(valid_probabilities))
            }

        # Create ensemble statistics
        stats_obj = EnsembleStatistics(
            total_queries=len(responses),
            successful_queries=len(successful_responses),
            failed_queries=len(responses) - len(successful_responses),
            valid_probabilities=len(valid_probabilities),
            models_used=list(model_groups.keys()),
            model_stats=model_stats,
            **overall_stats
        )

        return stats_obj

    def _calculate_model_statistics(self, model: str, responses: List[ModelResponse]) -> ModelStatistics:
        """
        Calculate statistics for a single model

        Args:
            model: Model identifier
            responses: List of responses for this model

        Returns:
            ModelStatistics object
        """
        successful_responses = [r for r in responses if r.status.value == "success"]
        valid_probabilities = [r.probability for r in successful_responses if r.probability is not None]

        if not valid_probabilities:
            # Return empty statistics if no valid probabilities
            return ModelStatistics(
                model=model,
                count=0,
                mean=0.0,
                median=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                success_rate=0.0
            )

        return ModelStatistics(
            model=model,
            count=len(valid_probabilities),
            mean=float(np.mean(valid_probabilities)),
            median=float(np.median(valid_probabilities)),
            std=float(np.std(valid_probabilities, ddof=1) if len(valid_probabilities) > 1 else 0),
            min=float(min(valid_probabilities)),
            max=float(max(valid_probabilities)),
            success_rate=len(successful_responses) / len(responses) if responses else 0.0
        )

    def calculate_ensemble_probability(self, responses: List[ModelResponse]) -> Optional[float]:
        """
        Calculate the ensemble probability using specified method

        Args:
            responses: List of model responses

        Returns:
            Ensemble probability or None if no valid responses
        """
        valid_probabilities = [r.probability for r in responses
                             if r.status.value == "success" and r.probability is not None]

        if not valid_probabilities:
            return None

        if self.method == "simple":
            return float(np.mean(valid_probabilities))

        elif self.method == "calibrated":
            # Apply batch calibration
            calibrated = self.calibrator.calibrate_batch(valid_probabilities)
            return float(np.mean(calibrated))

        elif self.method == "consistency":
            # Group by model for consistency scoring
            model_predictions = defaultdict(list)
            for r in responses:
                if r.status.value == "success" and r.probability is not None:
                    model_predictions[r.model].append(r.probability)

            # Calculate consistency-weighted aggregate
            return self.consistency_scorer.calculate_weighted_aggregate(model_predictions)

        elif self.method == "bayesian":
            # Use Bayesian aggregation
            expert_ids = [r.model for r in responses if r.status.value == "success" and r.probability is not None]
            result = self.bayesian_aggregator.aggregate_forecasts(valid_probabilities, expert_ids)
            return result.get("aggregated_probability")

        elif self.method == "ensemble":
            # Ensemble of methods
            methods_results = []

            # Simple mean
            methods_results.append(np.mean(valid_probabilities))

            # Calibrated mean
            calibrated = self.calibrator.calibrate_batch(valid_probabilities)
            methods_results.append(np.mean(calibrated))

            # Consistency weighted
            model_predictions = defaultdict(list)
            for r in responses:
                if r.status.value == "success" and r.probability is not None:
                    model_predictions[r.model].append(r.probability)
            if model_predictions:
                methods_results.append(
                    self.consistency_scorer.calculate_weighted_aggregate(model_predictions)
                )

            # Bayesian
            expert_ids = [r.model for r in responses if r.status.value == "success" and r.probability is not None]
            bayesian_result = self.bayesian_aggregator.aggregate_forecasts(valid_probabilities, expert_ids)
            methods_results.append(bayesian_result.get("aggregated_probability"))

            # Return mean of all methods
            return float(np.mean([r for r in methods_results if r is not None]))

        else:
            # Default to simple mean
            return float(np.mean(valid_probabilities))

    def calculate_weighted_ensemble_probability(
        self,
        responses: List[ModelResponse],
        model_weights: Optional[Dict[str, float]] = None
    ) -> Optional[float]:
        """
        Calculate weighted ensemble probability

        Args:
            responses: List of model responses
            model_weights: Dictionary of model weights (defaults to equal weights)

        Returns:
            Weighted ensemble probability
        """
        # Group by model
        model_groups = defaultdict(list)
        for response in responses:
            if response.status.value == "success" and response.probability is not None:
                model_groups[response.model].append(response.probability)

        if not model_groups:
            return None

        # Default to equal weights
        if model_weights is None:
            model_weights = {model: 1.0 for model in model_groups.keys()}

        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0

        for model, probabilities in model_groups.items():
            if model in model_weights:
                weight = model_weights[model]
                model_mean = np.mean(probabilities)
                weighted_sum += weight * model_mean
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else None

    def analyze_consensus(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """
        Analyze consensus between models

        Args:
            responses: List of model responses

        Returns:
            Dictionary with consensus metrics
        """
        valid_probabilities = [r.probability for r in responses
                             if r.status.value == "success" and r.probability is not None]

        if len(valid_probabilities) < 2:
            return {"consensus_score": None, "message": "Insufficient valid responses"}

        # Calculate various consensus metrics
        std_dev = np.std(valid_probabilities, ddof=1)
        coefficient_of_variation = std_dev / np.mean(valid_probabilities) if np.mean(valid_probabilities) > 0 else None

        # Consensus score (inverse of coefficient of variation, normalized)
        consensus_score = max(0, 1 - (coefficient_of_variation or 1)) if coefficient_of_variation is not None else None

        # Calculate percentile ranges
        p25 = np.percentile(valid_probabilities, 25)
        p75 = np.percentile(valid_probabilities, 75)
        iqr = p75 - p25

        return {
            "consensus_score": consensus_score,
            "std_deviation": std_dev,
            "coefficient_of_variation": coefficient_of_variation,
            "iqr": iqr,
            "p25": p25,
            "p75": p75,
            "range": max(valid_probabilities) - min(valid_probabilities),
            "count": len(valid_probabilities)
        }

    def identify_outliers(self, responses: List[ModelResponse], method: str = "iqr") -> List[str]:
        """
        Identify outlier responses

        Args:
            responses: List of model responses
            method: Outlier detection method ('iqr' or 'zscore')

        Returns:
            List of ensemble_ids of outlier responses
        """
        valid_responses = [r for r in responses
                          if r.status.value == "success" and r.probability is not None]

        if len(valid_responses) < 4:  # Need minimum responses for outlier detection
            return []

        probabilities = [r.probability for r in valid_responses]
        outlier_ids = []

        if method == "iqr":
            q1 = np.percentile(probabilities, 25)
            q3 = np.percentile(probabilities, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            for response in valid_responses:
                if response.probability < lower_bound or response.probability > upper_bound:
                    outlier_ids.append(response.ensemble_id)

        elif method == "zscore":
            z_scores = np.abs(stats.zscore(probabilities))
            threshold = 2.5  # Standard threshold for outliers

            for i, response in enumerate(valid_responses):
                if z_scores[i] > threshold:
                    outlier_ids.append(response.ensemble_id)

        return outlier_ids

    def compare_models(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """
        Compare performance between different models

        Args:
            responses: List of model responses

        Returns:
            Dictionary with model comparison metrics
        """
        # Group by model
        model_groups = defaultdict(list)
        for response in responses:
            model_groups[response.model].append(response)

        if len(model_groups) < 2:
            return {"message": "Need at least 2 models for comparison"}

        model_comparison = {}

        for model, model_responses in model_groups.items():
            valid_probs = [r.probability for r in model_responses
                          if r.status.value == "success" and r.probability is not None]

            model_comparison[model] = {
                "count": len(valid_probs),
                "success_rate": len([r for r in model_responses if r.status.value == "success"]) / len(model_responses),
                "mean": np.mean(valid_probs) if valid_probs else None,
                "std": np.std(valid_probs, ddof=1) if len(valid_probs) > 1 else 0,
                "consistency": 1 / (1 + np.std(valid_probs, ddof=1)) if len(valid_probs) > 1 else 1,
                "avg_response_time": np.mean([r.response_time for r in model_responses])
            }

        # Rank models by different criteria
        rankings = {
            "by_consistency": sorted(model_comparison.keys(),
                                   key=lambda x: model_comparison[x]["consistency"],
                                   reverse=True),
            "by_success_rate": sorted(model_comparison.keys(),
                                    key=lambda x: model_comparison[x]["success_rate"],
                                    reverse=True),
            "by_speed": sorted(model_comparison.keys(),
                             key=lambda x: model_comparison[x]["avg_response_time"])
        }

        return {
            "model_metrics": model_comparison,
            "rankings": rankings
        }

    def get_advanced_aggregation(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """
        Get comprehensive aggregation results using all available methods

        Args:
            responses: List of model responses

        Returns:
            Dictionary with results from all aggregation methods
        """
        valid_responses = [r for r in responses if r.status.value == "success" and r.probability is not None]
        if not valid_responses:
            return {"error": "No valid responses for aggregation"}

        valid_probabilities = [r.probability for r in valid_responses]

        # Group by model
        model_predictions = defaultdict(list)
        for r in valid_responses:
            model_predictions[r.model].append(r.probability)

        results = {
            "simple_mean": float(np.mean(valid_probabilities)),
            "median": float(np.median(valid_probabilities)),
            "trimmed_mean": float(stats.trim_mean(valid_probabilities, 0.1)),  # 10% trimmed
        }

        # Calibrated aggregation
        calibrated = self.calibrator.calibrate_batch(valid_probabilities)
        results["calibrated_mean"] = float(np.mean(calibrated))
        results["calibration_temperature"] = self.calibrator.temperature

        # Consistency-weighted aggregation
        consistency_result = self.consistency_scorer.score_ensemble(model_predictions)
        results["consistency_weighted"] = self.consistency_scorer.calculate_weighted_aggregate(model_predictions)
        results["ensemble_consistency"] = consistency_result["ensemble_consistency"]
        results["consistency_scores"] = consistency_result["model_scores"]

        # Bayesian aggregation
        expert_ids = [r.model for r in valid_responses]
        bayesian_result = self.bayesian_aggregator.aggregate_forecasts(
            valid_probabilities, expert_ids
        )
        results["bayesian_aggregated"] = bayesian_result["aggregated_probability"]
        results["bayesian_confidence_interval"] = bayesian_result["confidence_interval"]
        results["bayesian_uncertainty"] = bayesian_result["uncertainty"]

        # Ensemble of all methods
        all_estimates = [
            results["simple_mean"],
            results["calibrated_mean"],
            results["consistency_weighted"],
            results["bayesian_aggregated"]
        ]
        results["ensemble_of_methods"] = float(np.mean(all_estimates))
        results["methods_std"] = float(np.std(all_estimates))

        # Add method recommendations
        results["recommended_estimate"] = self._get_recommended_estimate(results, consistency_result)
        results["confidence_in_estimate"] = self._calculate_confidence_score(results, valid_probabilities)

        return results

    def _get_recommended_estimate(self, results: Dict[str, Any], consistency_result: Dict[str, Any]) -> float:
        """
        Get recommended estimate based on data characteristics

        Args:
            results: All aggregation results
            consistency_result: Consistency analysis results

        Returns:
            Recommended probability estimate
        """
        # If high consistency, use consistency-weighted
        if consistency_result.get("ensemble_consistency", 0) > 0.8:
            return results["consistency_weighted"]

        # If high uncertainty, use Bayesian
        if results.get("bayesian_uncertainty", 1) > 0.5:
            return results["bayesian_aggregated"]

        # Default to ensemble of methods
        return results["ensemble_of_methods"]

    def _calculate_confidence_score(self, results: Dict[str, Any], probabilities: List[float]) -> float:
        """
        Calculate confidence in the estimate

        Args:
            results: Aggregation results
            probabilities: List of probabilities

        Returns:
            Confidence score (0-1)
        """
        # Factors affecting confidence:
        # 1. Agreement between methods
        methods_std = results.get("methods_std", 10)
        agreement_score = 1.0 / (1.0 + methods_std / 10)

        # 2. Ensemble consistency
        consistency = results.get("ensemble_consistency", 0.5)

        # 3. Sample size
        n_samples = len(probabilities)
        sample_score = min(1.0, n_samples / 50)  # Max confidence at 50+ samples

        # 4. Spread of predictions
        spread = np.std(probabilities)
        spread_score = 1.0 / (1.0 + spread / 20)

        # Combine scores
        confidence = (agreement_score + consistency + sample_score + spread_score) / 4

        return float(np.clip(confidence, 0, 1))

    def calculate_brier_score(self, responses: List[ModelResponse], actual_outcome: bool) -> Dict[str, float]:
        """
        Calculate Brier scores for post-event evaluation

        Args:
            responses: List of model responses
            actual_outcome: True if event occurred, False otherwise

        Returns:
            Dictionary with Brier scores
        """
        outcome_binary = 1.0 if actual_outcome else 0.0

        # Calculate overall Brier score
        valid_probabilities = [r.probability / 100.0 for r in responses
                             if r.status.value == "success" and r.probability is not None]

        if not valid_probabilities:
            return {"error": "No valid probabilities for Brier score calculation"}

        ensemble_prob = np.mean(valid_probabilities)
        ensemble_brier = (ensemble_prob - outcome_binary) ** 2

        # Calculate per-model Brier scores
        model_groups = defaultdict(list)
        for response in responses:
            if response.status.value == "success" and response.probability is not None:
                model_groups[response.model].append(response.probability / 100.0)

        model_brier_scores = {}
        for model, probabilities in model_groups.items():
            model_mean = np.mean(probabilities)
            model_brier_scores[model] = (model_mean - outcome_binary) ** 2

        return {
            "ensemble_brier_score": ensemble_brier,
            "model_brier_scores": model_brier_scores,
            "reference_score": 0.25  # Score for always predicting 50%
        }