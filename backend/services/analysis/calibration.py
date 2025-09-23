"""Batch Calibration for improving forecast accuracy and reducing overconfidence"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class BatchCalibrator:
    """
    Implements Batch Calibration (BC) for post-hoc calibration of ensemble forecasts.
    Reduces overconfidence and improves probability estimates.
    """

    def __init__(self, method: str = "platt"):
        """
        Initialize batch calibrator

        Args:
            method: Calibration method ('platt', 'isotonic', or 'temperature')
        """
        self.method = method
        self.calibration_model = None
        self.temperature = 1.0
        self.is_fitted = False

    def fit(self, probabilities: List[float], labels: Optional[List[bool]] = None):
        """
        Fit calibration model on historical data

        Args:
            probabilities: List of predicted probabilities
            labels: List of actual outcomes (if available for supervised calibration)
        """
        if labels is not None and len(labels) == len(probabilities):
            # Supervised calibration with known outcomes
            self._fit_supervised(probabilities, labels)
        else:
            # Unsupervised calibration based on consistency
            self._fit_unsupervised(probabilities)

        self.is_fitted = True

    def _fit_supervised(self, probabilities: List[float], labels: List[bool]):
        """
        Fit calibration with known outcomes (post-event)

        Args:
            probabilities: Predicted probabilities
            labels: Actual binary outcomes
        """
        X = np.array(probabilities).reshape(-1, 1)
        y = np.array(labels).astype(int)

        if self.method == "platt":
            # Platt scaling using logistic regression
            self.calibration_model = LogisticRegression()
            self.calibration_model.fit(X, y)
            logger.info("Fitted Platt scaling calibration")

        elif self.method == "isotonic":
            # Isotonic regression for non-parametric calibration
            self.calibration_model = IsotonicRegression(out_of_bounds='clip')
            self.calibration_model.fit(X.ravel(), y)
            logger.info("Fitted isotonic regression calibration")

        elif self.method == "temperature":
            # Temperature scaling
            self.temperature = self._optimize_temperature(probabilities, labels)
            logger.info(f"Fitted temperature scaling with T={self.temperature:.3f}")

    def _fit_unsupervised(self, probabilities: List[float]):
        """
        Fit calibration without known outcomes using consistency analysis

        Args:
            probabilities: List of predicted probabilities
        """
        # Group probabilities into batches
        batches = self._create_batches(probabilities)

        if self.method == "temperature":
            # Estimate temperature from batch variance
            batch_variances = [np.var(batch) for batch in batches if len(batch) > 1]
            if batch_variances:
                # Higher variance suggests overconfidence
                avg_variance = np.mean(batch_variances)
                # Heuristic: scale temperature based on variance
                self.temperature = 1.0 + (avg_variance - 0.01) * 10
                self.temperature = max(0.5, min(2.0, self.temperature))  # Clamp
            else:
                self.temperature = 1.0
            logger.info(f"Estimated temperature T={self.temperature:.3f} from batch variance")

        else:
            # For other methods, create pseudo-labels based on consistency
            pseudo_X = []
            pseudo_y = []

            for batch in batches:
                if len(batch) > 1:
                    mean_prob = np.mean(batch)
                    consistency = 1.0 / (1.0 + np.std(batch))

                    # Create pseudo-labels based on consistency
                    # High consistency -> prediction likely correct
                    # Low consistency -> move toward 0.5
                    for prob in batch:
                        pseudo_X.append(prob)
                        if consistency > 0.7:
                            pseudo_y.append(1 if prob > 0.5 else 0)
                        else:
                            # Less confident, use softer labels
                            pseudo_y.append(mean_prob)

            if pseudo_X:
                X = np.array(pseudo_X).reshape(-1, 1)
                y = np.array(pseudo_y)

                if self.method == "platt":
                    self.calibration_model = LogisticRegression()
                    # Use sample weights based on consistency
                    weights = [1.0 / (1.0 + abs(p - 0.5)) for p in pseudo_X]
                    self.calibration_model.fit(X, y > 0.5, sample_weight=weights)
                elif self.method == "isotonic":
                    self.calibration_model = IsotonicRegression(out_of_bounds='clip')
                    self.calibration_model.fit(X.ravel(), y)

    def calibrate(self, probability: float) -> float:
        """
        Calibrate a single probability

        Args:
            probability: Uncalibrated probability (0-100)

        Returns:
            Calibrated probability (0-100)
        """
        if not self.is_fitted:
            return probability

        # Convert to 0-1 range
        prob_01 = probability / 100.0

        if self.method == "temperature":
            # Temperature scaling
            if self.temperature == 1.0:
                calibrated = prob_01
            else:
                # Apply temperature to logits
                logit_val = logit(np.clip(prob_01, 1e-7, 1 - 1e-7))
                calibrated = expit(logit_val / self.temperature)

        elif self.method in ["platt", "isotonic"] and self.calibration_model:
            # Apply fitted model
            X = np.array([[prob_01]])
            if self.method == "platt":
                calibrated = self.calibration_model.predict_proba(X)[0, 1]
            else:
                calibrated = self.calibration_model.predict(prob_01)

        else:
            calibrated = prob_01

        # Convert back to 0-100 range
        return float(np.clip(calibrated * 100, 0, 100))

    def calibrate_batch(self, probabilities: List[float]) -> List[float]:
        """
        Calibrate a batch of probabilities

        Args:
            probabilities: List of uncalibrated probabilities (0-100)

        Returns:
            List of calibrated probabilities (0-100)
        """
        # First fit on the batch if not already fitted
        if not self.is_fitted:
            self.fit(probabilities)

        return [self.calibrate(p) for p in probabilities]

    def _create_batches(self, probabilities: List[float], batch_size: int = 10) -> List[List[float]]:
        """
        Group probabilities into batches for analysis

        Args:
            probabilities: List of probabilities
            batch_size: Size of each batch

        Returns:
            List of batches
        """
        batches = []
        sorted_probs = sorted(probabilities)

        for i in range(0, len(sorted_probs), batch_size):
            batch = sorted_probs[i:i + batch_size]
            if batch:
                batches.append(batch)

        return batches

    def _optimize_temperature(self, probabilities: List[float], labels: List[bool]) -> float:
        """
        Optimize temperature parameter using maximum likelihood

        Args:
            probabilities: Predicted probabilities
            labels: Actual outcomes

        Returns:
            Optimal temperature
        """
        probs = np.array(probabilities) / 100.0
        labs = np.array(labels).astype(float)

        def neg_log_likelihood(T):
            # Apply temperature scaling
            scaled_logits = logit(np.clip(probs, 1e-7, 1 - 1e-7)) / T[0]
            scaled_probs = expit(scaled_logits)

            # Calculate negative log likelihood
            nll = -np.mean(
                labs * np.log(np.clip(scaled_probs, 1e-7, 1)) +
                (1 - labs) * np.log(np.clip(1 - scaled_probs, 1e-7, 1))
            )
            return nll

        # Optimize temperature
        result = minimize(neg_log_likelihood, [1.0], bounds=[(0.1, 10.0)])
        return result.x[0]

    def get_calibration_metrics(self, probabilities: List[float], labels: List[bool]) -> Dict[str, float]:
        """
        Calculate calibration metrics

        Args:
            probabilities: Predicted probabilities
            labels: Actual outcomes

        Returns:
            Dictionary of calibration metrics
        """
        probs = np.array(probabilities) / 100.0
        labs = np.array(labels).astype(float)

        # Expected calibration error (ECE)
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            mask = (probs > bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
            if np.sum(mask) > 0:
                bin_acc = np.mean(labs[mask])
                bin_conf = np.mean(probs[mask])
                bin_weight = np.sum(mask) / len(probs)
                ece += bin_weight * np.abs(bin_acc - bin_conf)

        # Maximum calibration error (MCE)
        mce = 0.0
        for i in range(n_bins):
            mask = (probs > bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
            if np.sum(mask) > 0:
                bin_acc = np.mean(labs[mask])
                bin_conf = np.mean(probs[mask])
                mce = max(mce, np.abs(bin_acc - bin_conf))

        # Brier score
        brier_score = np.mean((probs - labs) ** 2)

        return {
            "expected_calibration_error": float(ece),
            "maximum_calibration_error": float(mce),
            "brier_score": float(brier_score),
            "temperature": self.temperature if self.method == "temperature" else None
        }


class MultiModelCalibrator:
    """
    Calibrates predictions from multiple models in an ensemble
    """

    def __init__(self):
        """Initialize multi-model calibrator"""
        self.model_calibrators = {}

    def fit_model(self, model_name: str, probabilities: List[float], labels: Optional[List[bool]] = None):
        """
        Fit calibration for a specific model

        Args:
            model_name: Name of the model
            probabilities: Model's predictions
            labels: Actual outcomes (if available)
        """
        calibrator = BatchCalibrator(method="temperature")
        calibrator.fit(probabilities, labels)
        self.model_calibrators[model_name] = calibrator
        logger.info(f"Fitted calibration for model {model_name}")

    def calibrate_ensemble(self, model_predictions: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Calibrate predictions from all models

        Args:
            model_predictions: Dictionary mapping model names to their predictions

        Returns:
            Dictionary of calibrated predictions
        """
        calibrated_predictions = {}

        for model_name, predictions in model_predictions.items():
            if model_name in self.model_calibrators:
                # Use fitted calibrator
                calibrator = self.model_calibrators[model_name]
                calibrated = calibrator.calibrate_batch(predictions)
            else:
                # Fit new calibrator on the fly
                calibrator = BatchCalibrator(method="temperature")
                calibrated = calibrator.calibrate_batch(predictions)
                self.model_calibrators[model_name] = calibrator

            calibrated_predictions[model_name] = calibrated

        return calibrated_predictions