"""Sample Consistency Calibration for weighting predictions by internal consistency"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from collections import defaultdict
from scipy.stats import entropy, kendalltau, spearmanr

logger = logging.getLogger(__name__)


class ConsistencyScorer:
    """
    Implements Sample Consistency Calibration by measuring internal consistency
    of predictions and up-weighting consistent paths.
    """

    def __init__(self, method: str = "ensemble"):
        """
        Initialize consistency scorer

        Args:
            method: Scoring method ('direct', 'indirect', 'ensemble')
        """
        self.method = method
        self.consistency_scores = {}
        self.model_consistencies = defaultdict(list)

    def calculate_consistency(self, samples: List[float]) -> float:
        """
        Calculate consistency score for a set of samples

        Args:
            samples: List of probability predictions

        Returns:
            Consistency score (0-1, higher is more consistent)
        """
        if len(samples) < 2:
            return 1.0

        samples_array = np.array(samples)

        if self.method == "direct":
            # Direct method: inverse of coefficient of variation
            mean_val = np.mean(samples_array)
            std_val = np.std(samples_array)
            if mean_val > 0:
                cv = std_val / mean_val
                consistency = 1.0 / (1.0 + cv)
            else:
                consistency = 1.0 if std_val == 0 else 0.0

        elif self.method == "indirect":
            # Indirect method: based on entropy of distribution
            # Discretize probabilities into bins
            bins = np.linspace(0, 100, 11)
            hist, _ = np.histogram(samples_array, bins=bins)
            hist_norm = hist / np.sum(hist)

            # Low entropy means high consistency
            ent = entropy(hist_norm + 1e-10)
            max_entropy = np.log(len(bins) - 1)
            consistency = 1.0 - (ent / max_entropy) if max_entropy > 0 else 1.0

        elif self.method == "ensemble":
            # Ensemble method: combination of multiple metrics
            # 1. Standard deviation based
            std_score = 1.0 / (1.0 + np.std(samples_array) / 10.0)

            # 2. Range based
            range_val = np.max(samples_array) - np.min(samples_array)
            range_score = 1.0 - (range_val / 100.0)

            # 3. Inter-quartile range based
            q75, q25 = np.percentile(samples_array, [75, 25])
            iqr = q75 - q25
            iqr_score = 1.0 / (1.0 + iqr / 20.0)

            # Combine scores
            consistency = (std_score + range_score + iqr_score) / 3.0

        else:
            # Fallback to simple std-based metric
            consistency = 1.0 / (1.0 + np.std(samples_array))

        return float(np.clip(consistency, 0, 1))

    def score_model_samples(self, model_name: str, samples: List[float]) -> Dict[str, Any]:
        """
        Score samples from a specific model

        Args:
            model_name: Name of the model
            samples: List of probability predictions from this model

        Returns:
            Dictionary with consistency metrics
        """
        consistency = self.calculate_consistency(samples)

        # Store for later analysis
        self.model_consistencies[model_name].append(consistency)

        # Calculate additional metrics
        metrics = {
            "model": model_name,
            "consistency_score": consistency,
            "sample_count": len(samples),
            "mean": float(np.mean(samples)) if samples else 0,
            "std": float(np.std(samples)) if len(samples) > 1 else 0,
            "min": float(np.min(samples)) if samples else 0,
            "max": float(np.max(samples)) if samples else 0,
            "confidence_level": self._classify_confidence(consistency)
        }

        self.consistency_scores[model_name] = metrics
        return metrics

    def score_ensemble(self, model_samples: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Score consistency across entire ensemble

        Args:
            model_samples: Dictionary mapping model names to their sample lists

        Returns:
            Ensemble consistency metrics
        """
        all_scores = []
        model_metrics = {}

        for model_name, samples in model_samples.items():
            metrics = self.score_model_samples(model_name, samples)
            model_metrics[model_name] = metrics
            all_scores.append(metrics["consistency_score"])

        # Calculate ensemble-level consistency
        ensemble_consistency = self._calculate_ensemble_consistency(model_samples)

        return {
            "model_scores": model_metrics,
            "ensemble_consistency": ensemble_consistency,
            "mean_model_consistency": float(np.mean(all_scores)) if all_scores else 0,
            "consistency_variance": float(np.var(all_scores)) if len(all_scores) > 1 else 0,
            "most_consistent_model": max(model_metrics, key=lambda x: model_metrics[x]["consistency_score"])
            if model_metrics else None,
            "least_consistent_model": min(model_metrics, key=lambda x: model_metrics[x]["consistency_score"])
            if model_metrics else None
        }

    def calculate_weighted_aggregate(self, model_predictions: Dict[str, List[float]]) -> float:
        """
        Calculate consistency-weighted aggregate prediction

        Args:
            model_predictions: Dictionary mapping models to their predictions

        Returns:
            Weighted ensemble probability
        """
        weighted_sum = 0.0
        total_weight = 0.0

        for model_name, predictions in model_predictions.items():
            if not predictions:
                continue

            # Calculate consistency weight
            consistency = self.calculate_consistency(predictions)

            # Apply non-linear weighting (square to emphasize consistent models)
            weight = consistency ** 2

            # Calculate mean prediction for this model
            mean_pred = np.mean(predictions)

            weighted_sum += weight * mean_pred
            total_weight += weight

        if total_weight > 0:
            return float(weighted_sum / total_weight)
        else:
            # Fallback to simple mean
            all_preds = [p for preds in model_predictions.values() for p in preds]
            return float(np.mean(all_preds)) if all_preds else 50.0

    def get_confidence_weights(self, model_predictions: Dict[str, List[float]]) -> Dict[str, float]:
        """
        Get confidence-based weights for each model

        Args:
            model_predictions: Dictionary mapping models to predictions

        Returns:
            Dictionary of model weights
        """
        weights = {}

        for model_name, predictions in model_predictions.items():
            consistency = self.calculate_consistency(predictions)

            # Transform consistency to weight with adjustable aggressiveness
            # Higher power = more aggressive weighting toward consistent models
            weight = consistency ** 1.5

            weights[model_name] = weight

        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _calculate_ensemble_consistency(self, model_samples: Dict[str, List[float]]) -> float:
        """
        Calculate consistency across the entire ensemble

        Args:
            model_samples: Dictionary of model samples

        Returns:
            Ensemble-level consistency score
        """
        # Get mean prediction from each model
        model_means = []
        for samples in model_samples.values():
            if samples:
                model_means.append(np.mean(samples))

        if len(model_means) < 2:
            return 1.0

        # Calculate consistency of model means
        ensemble_consistency = self.calculate_consistency(model_means)

        # Also consider agreement in rankings
        if len(model_samples) >= 2:
            # Create prediction rankings for correlation
            models = list(model_samples.keys())
            if len(models) >= 2 and all(len(model_samples[m]) > 1 for m in models[:2]):
                # Compare first two models' patterns
                corr, _ = spearmanr(
                    model_samples[models[0]][:min(len(model_samples[models[0]]), len(model_samples[models[1]]))],
                    model_samples[models[1]][:min(len(model_samples[models[0]]), len(model_samples[models[1]]))]
                )
                if not np.isnan(corr):
                    # Combine mean consistency with correlation
                    ensemble_consistency = (ensemble_consistency + (corr + 1) / 2) / 2

        return float(ensemble_consistency)

    def _classify_confidence(self, consistency_score: float) -> str:
        """
        Classify confidence level based on consistency

        Args:
            consistency_score: Consistency score (0-1)

        Returns:
            Confidence classification
        """
        if consistency_score >= 0.9:
            return "very_high"
        elif consistency_score >= 0.75:
            return "high"
        elif consistency_score >= 0.5:
            return "medium"
        elif consistency_score >= 0.25:
            return "low"
        else:
            return "very_low"

    def generate_consistency_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive consistency report

        Returns:
            Dictionary with detailed consistency analysis
        """
        if not self.consistency_scores:
            return {"error": "No consistency scores calculated yet"}

        # Aggregate statistics
        all_scores = [s["consistency_score"] for s in self.consistency_scores.values()]

        report = {
            "summary": {
                "mean_consistency": float(np.mean(all_scores)),
                "median_consistency": float(np.median(all_scores)),
                "std_consistency": float(np.std(all_scores)) if len(all_scores) > 1 else 0,
                "min_consistency": float(np.min(all_scores)),
                "max_consistency": float(np.max(all_scores))
            },
            "model_details": self.consistency_scores,
            "confidence_distribution": self._get_confidence_distribution(),
            "recommendations": self._generate_recommendations()
        }

        return report

    def _get_confidence_distribution(self) -> Dict[str, int]:
        """
        Get distribution of confidence levels

        Returns:
            Count of models in each confidence category
        """
        distribution = defaultdict(int)
        for score in self.consistency_scores.values():
            level = score.get("confidence_level", "unknown")
            distribution[level] += 1
        return dict(distribution)

    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on consistency analysis

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not self.consistency_scores:
            return ["Insufficient data for recommendations"]

        # Check overall consistency
        all_scores = [s["consistency_score"] for s in self.consistency_scores.values()]
        mean_consistency = np.mean(all_scores)

        if mean_consistency < 0.5:
            recommendations.append("Low overall consistency detected - consider increasing iterations or reviewing prompt clarity")

        if mean_consistency > 0.8:
            recommendations.append("High consistency observed - predictions are reliable for aggregation")

        # Check variance
        if len(all_scores) > 1:
            variance = np.var(all_scores)
            if variance > 0.1:
                recommendations.append("High variance in model consistencies - consider model-specific calibration")

        # Identify problematic models
        for model_name, score in self.consistency_scores.items():
            if score["consistency_score"] < 0.3:
                recommendations.append(f"Model {model_name} shows very low consistency - consider excluding or recalibrating")

        return recommendations