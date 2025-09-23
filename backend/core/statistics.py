"""
Statistics module for ensemble forecasting
Provides basic statistical functions for model aggregation
"""
from typing import List, Dict, Any
import statistics

def calculate_ensemble_probability(probabilities: List[float]) -> float:
    """
    Calculate ensemble probability from individual model probabilities
    """
    if not probabilities:
        return 0.0

    return round(sum(probabilities) / len(probabilities), 1)

def calculate_model_statistics(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate statistics for model results
    """
    model_stats = {}

    for result in results:
        model = result.get('model', 'unknown')
        probability = result.get('probability', 0.0)

        model_stats[model] = {
            'mean': probability,
            'count': 1
        }

    return model_stats