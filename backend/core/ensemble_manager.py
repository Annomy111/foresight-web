"""Ensemble manager for coordinating multiple model queries"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from rich.progress import Progress, TaskID
from rich.console import Console

from core.api_client import OpenRouterClient
from config.settings import get_settings
from config.prompts import PromptTemplates
from utils.visual import visual
from analysis.bayesian_aggregator import BayesianAggregator
from analysis.consistency_scorer import ConsistencyScorer
from analysis.calibration import BatchCalibrator

logger = logging.getLogger(__name__)
console = Console()


class EnsembleManager:
    """Manages ensemble forecasting across multiple models"""

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True, dry_run: bool = False, enhanced_prompts: bool = False):
        """
        Initialize ensemble manager

        Args:
            api_key: OpenRouter API key
            use_cache: Whether to use response caching
            dry_run: Whether to run in dry-run mode (no API calls)
            enhanced_prompts: Whether to use enhanced ensemble-aware prompts with meta-reasoning
        """
        self.client = OpenRouterClient(api_key, use_cache=use_cache) if not dry_run else None
        self.settings = get_settings()
        self.dry_run = dry_run
        self.use_cache = use_cache
        self.enhanced_prompts = enhanced_prompts

    async def run_ensemble_forecast(
        self,
        question: str,
        definition: str,
        models: Optional[List[str]] = None,
        iterations: int = None,
        timeframe: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a complete ensemble forecast

        Args:
            question: Forecast question
            definition: Operational definition
            models: List of models to use (uses config default if None)
            iterations: Iterations per model (uses config default if None)
            timeframe: Time period for forecast
            context: Additional context

        Returns:
            Complete forecast results with all responses
        """
        # Use configuration defaults if not provided
        models = models or self.settings.models.enabled_models
        iterations = iterations or self.settings.models.iterations_per_model

        # Generate the prompt - use enhanced prompts if enabled
        if self.enhanced_prompts:
            prompt = PromptTemplates.get_ensemble_aware_super_forecaster_prompt(
                question=question,
                definition=definition,
                timeframe=timeframe,
                additional_context=context
            )
            console.print("[bold cyan]🧠 Using Enhanced Ensemble-Aware Prompts[/bold cyan]")
        else:
            prompt = PromptTemplates.get_super_forecaster_prompt(
                question=question,
                definition=definition,
                timeframe=timeframe,
                additional_context=context
            )

        console.print(f"\n[bold blue]Starting Ensemble Forecast[/bold blue]")
        console.print(f"Models: {len(models)}")
        console.print(f"Iterations per model: {iterations}")
        console.print(f"Total queries: {len(models) * iterations}")

        if self.dry_run:
            console.print("[yellow]DRY-RUN MODE: Generating mock data for testing[/yellow]")

        start_time = datetime.now()

        # Test connection first (skip in dry-run mode or when using free models)
        if not self.dry_run:
            # Check if all models are free tier
            all_free = all(':free' in model for model in models)
            if all_free:
                console.print("[cyan]✓ Using free tier models - skipping connection test[/cyan]")
            else:
                if not await self.client.test_connection():
                    console.print("[bold red]❌ API connection test failed![/bold red]")
                    raise ConnectionError("Could not connect to OpenRouter API")
                console.print("[green]✓ API connection successful[/green]")
        else:
            console.print("[yellow]✓ Skipping connection test (dry-run mode)[/yellow]")

        # Run queries for all models with enhanced progress tracking
        all_results = []

        with visual.create_enhanced_progress() as progress:
            main_task = progress.add_task(
                "🎯 Overall Analysis Progress",
                total=len(models) * iterations
            )

            for model in models:
                model_name = model.split('/')[-1]
                console.print(f"\n[cyan]🤖 Querying {model_name}...[/cyan]")

                model_task = progress.add_task(
                    f"🔄 {model_name}",
                    total=iterations
                )

                # Run batch queries for this model
                model_results = await self._run_model_batch(
                    model=model,
                    prompt=prompt,
                    iterations=iterations,
                    progress=progress,
                    task_id=model_task
                )

                # Update overall progress
                progress.update(main_task, advance=iterations)

                # Add model metadata
                for result in model_results:
                    result['ensemble_id'] = f"{model}_{result['iteration']:02d}"
                    result['question'] = question
                    result['definition'] = definition
                    result['timeframe'] = timeframe

                all_results.extend(model_results)

                # Show interim success rate
                successful = len([r for r in model_results if r.get('status') == 'success'])
                console.print(f"[green]✓ {model_name}: {successful}/{iterations} successful[/green]")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        console.print(f"\n[green]✓ Ensemble forecast completed in {duration:.1f}s[/green]")

        # Compile results
        forecast_result = {
            "metadata": {
                "question": question,
                "definition": definition,
                "timeframe": timeframe,
                "context": context,
                "models": models,
                "iterations_per_model": iterations,
                "total_queries": len(all_results),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            },
            "prompt": prompt,
            "responses": all_results,
            "summary": self._generate_summary(all_results)
        }

        return forecast_result

    async def run_ukraine_ceasefire_forecast(
        self,
        models: Optional[List[str]] = None,
        iterations: int = None,
        by_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the specific Ukraine ceasefire forecast from the research

        Args:
            models: Models to use
            iterations: Iterations per model
            by_date: Specific date for the forecast (e.g., "2026-03-31", "2026-06-30")

        Returns:
            Forecast results
        """
        if by_date:
            # Parse the date and generate dynamic prompt
            from datetime import datetime

            try:
                # Parse the date string
                target_date = datetime.strptime(by_date, "%Y-%m-%d")

                # Validate it's in 2026
                if target_date.year != 2026:
                    logger.warning(f"Date {by_date} is not in 2026, using full year 2026")
                    by_date = None
                else:
                    # German month names for proper formatting
                    german_months = {
                        1: "Januar", 2: "Februar", 3: "März", 4: "April",
                        5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
                        9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
                    }

                    # Format the date in German
                    day = target_date.day
                    month = german_months[target_date.month]
                    year = target_date.year

                    # Generate question with the specific date
                    question = f"Mit welcher Wahrscheinlichkeit kommt es bis zum {day}. {month} {year} zu einem Waffenstillstand in der Ukraine?"

                    # Set timeframe from Jan 1 to the specified date
                    timeframe = f"2026-01-01 bis {by_date}"

                    # Adjust definition with the specific end date
                    definition = f"Ein 'Waffenstillstand' wird für dieses Experiment definiert als eine von beiden Konfliktparteien (Regierung der Ukraine und Regierung der Russischen Föderation) offiziell verkündete und für mindestens 30 aufeinanderfolgende Tage eingehaltene Einstellung aller Kampfhandlungen an allen Fronten. Der Beginn des 30-Tage-Zeitraums muss zwischen dem 1. Januar 2026, 00:00 Uhr, und dem {day}. {month} {year}, 23:59 Uhr Kiewer Zeit, liegen. Kleinere, lokale Scharmützel, die innerhalb von 24 Stunden beendet sind und von keiner der beiden Parteien als Beendigung des Waffenstillstands deklariert werden, gelten nicht als Bruch."

            except ValueError as e:
                logger.error(f"Invalid date format {by_date}: {e}. Using full year 2026.")
                by_date = None

        # Default to full year if no valid date provided
        if not by_date:
            question = "Mit welcher Wahrscheinlichkeit kommt es im Jahr 2026 zu einem Waffenstillstand in der Ukraine?"
            timeframe = "2026-01-01 bis 2026-12-31"
            definition = "Ein 'Waffenstillstand' wird für dieses Experiment definiert als eine von beiden Konfliktparteien (Regierung der Ukraine und Regierung der Russischen Föderation) offiziell verkündete und für mindestens 30 aufeinanderfolgende Tage eingehaltene Einstellung aller Kampfhandlungen an allen Fronten. Der Beginn des 30-Tage-Zeitraums muss zwischen dem 1. Januar 2026, 00:00 Uhr, und dem 31. Dezember 2026, 23:59 Uhr Kiewer Zeit, liegen. Kleinere, lokale Scharmützel, die innerhalb von 24 Stunden beendet sind und von keiner der beiden Parteien als Beendigung des Waffenstillstands deklariert werden, gelten nicht als Bruch."

        return await self.run_ensemble_forecast(
            question=question,
            definition=definition,
            timeframe=timeframe,
            models=models,
            iterations=iterations
        )

    async def _run_model_batch(
        self,
        model: str,
        prompt: str,
        iterations: int,
        progress: Progress,
        task_id: TaskID
    ) -> List[Dict[str, Any]]:
        """
        Run batch queries for a single model

        Args:
            model: Model identifier
            prompt: Prompt to send
            iterations: Number of iterations
            progress: Rich progress instance
            task_id: Progress task ID

        Returns:
            List of results for this model
        """
        # Generate mock data in dry-run mode
        if self.dry_run:
            import random
            results = []
            for i in range(iterations):
                await asyncio.sleep(0.1)  # Simulate API delay
                # Generate realistic mock probabilities
                base_prob = random.gauss(35, 15)  # Center around 35% with std of 15
                probability = max(5, min(95, base_prob))  # Clamp between 5 and 95

                results.append({
                    "model": model,
                    "iteration": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "response_time": random.uniform(0.5, 2.0),
                    "status": "success",
                    "content": f"[DRY-RUN] Mock response for {model}\nPROGNOSE: {probability:.1f}%",
                    "probability": probability,
                    "response_source": "dry_run",
                    "usage": {
                        "prompt_tokens": 1500,
                        "completion_tokens": 500,
                        "total_tokens": 2000
                    }
                })
                progress.update(task_id, advance=1)
            return results

        # Check if model is free tier and needs rate limiting
        is_free_model = ':free' in model
        rate_limit_delay = getattr(self.settings.api, 'rate_limit_delay', 0) if is_free_model else 0

        # Create semaphore for concurrency control
        # For free models, use 1 concurrent request
        concurrent_limit = 1 if is_free_model else self.settings.models.concurrent_requests
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def limited_query(iteration: int):
            async with semaphore:
                # Add delay for free tier to avoid rate limiting
                if is_free_model and iteration > 0:
                    await asyncio.sleep(rate_limit_delay)

                # First attempt with full prompt
                result = await self.client.query_model(model, prompt, enable_web_search=True)

                # Check for empty responses and retry with simplified prompt if needed
                if result.get("status") == "empty_response" and ':free' in model:
                    logger.warning(f"Empty response from {model}, retrying with increased tokens")
                    # Retry once more with explicit max token override
                    result = await self.client.query_model(model, prompt, enable_web_search=True, max_tokens=10000)

                    # If still empty, log and continue
                    if result.get("status") == "empty_response":
                        logger.error(f"Still empty response from {model} after retry")

                result["iteration"] = iteration + 1
                progress.update(task_id, advance=1)
                return result

        # Run all iterations sequentially for free models, parallel for paid
        if is_free_model:
            # Sequential execution with delays for free tier
            results = []
            for i in range(iterations):
                try:
                    result = await limited_query(i)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Query {i+1} for {model} failed: {e}")
                    results.append(e)
        else:
            # Parallel execution for paid models
            tasks = [limited_query(i) for i in range(iterations)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i+1} for {model} failed: {result}")
                # Create error result
                valid_results.append({
                    "model": model,
                    "iteration": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(result),
                    "content": None,
                    "probability": None
                })
            else:
                valid_results.append(result)

        return valid_results

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from results

        Args:
            results: List of all query results

        Returns:
            Summary dictionary
        """
        # Separate results by model
        model_groups = {}
        valid_probabilities = []

        for result in results:
            model = result.get("model", "unknown")
            if model not in model_groups:
                model_groups[model] = []
            model_groups[model].append(result)

            # Collect valid probabilities
            if result.get("probability") is not None:
                valid_probabilities.append(result["probability"])

        # Calculate statistics
        summary = {
            "total_queries": len(results),
            "successful_queries": len([r for r in results if r.get("status") == "success"]),
            "failed_queries": len([r for r in results if r.get("status") != "success"]),
            "models_used": list(model_groups.keys()),
            "valid_probabilities": len(valid_probabilities)
        }

        # Overall statistics
        if valid_probabilities:
            import numpy as np

            # Basic statistics (for comparison)
            basic_mean = float(np.mean(valid_probabilities))
            summary["overall_stats"] = {
                "mean": basic_mean,
                "median": float(np.median(valid_probabilities)),
                "std": float(np.std(valid_probabilities)),
                "min": float(min(valid_probabilities)),
                "max": float(max(valid_probabilities)),
                "count": len(valid_probabilities)
            }

            # Advanced algorithms for enhanced ensemble prediction
            summary["advanced_analysis"] = self._apply_advanced_algorithms(
                model_groups, valid_probabilities
            )

        # Per-model statistics
        summary["model_stats"] = {}
        for model, model_results in model_groups.items():
            model_probs = [r["probability"] for r in model_results if r.get("probability") is not None]

            if model_probs:
                import numpy as np
                summary["model_stats"][model] = {
                    "mean": float(np.mean(model_probs)),
                    "std": float(np.std(model_probs)),
                    "min": float(min(model_probs)),
                    "max": float(max(model_probs)),
                    "count": len(model_probs),
                    "success_rate": len([r for r in model_results if r.get("status") == "success"]) / len(model_results)
                }

        return summary

    def _apply_advanced_algorithms(
        self,
        model_groups: Dict[str, List[Dict[str, Any]]],
        valid_probabilities: List[float]
    ) -> Dict[str, Any]:
        """
        Apply advanced scientific algorithms for enhanced ensemble prediction

        Args:
            model_groups: Dictionary of model results grouped by model
            valid_probabilities: All valid probability predictions

        Returns:
            Dictionary with advanced analysis results
        """
        try:
            import numpy as np

            # Initialize advanced algorithms
            consistency_scorer = ConsistencyScorer()
            calibrator = BatchCalibrator(method="platt")
            bayesian_aggregator = BayesianAggregator()

            # Prepare model predictions and consistency scores
            model_predictions = {}
            model_weights = {}
            calibrated_predictions = {}

            for model, results in model_groups.items():
                # Extract probabilities for this model
                model_probs = [r["probability"] for r in results if r.get("probability") is not None]

                if model_probs:
                    # Calculate consistency score (higher = more consistent)
                    consistency = consistency_scorer.calculate_consistency(model_probs)

                    # Apply batch calibration to improve probability calibration
                    # For future predictions, use temperature scaling instead of supervised methods
                    try:
                        calibrated_probs = calibrator.calibrate_batch(
                            np.array(model_probs) / 100.0  # Convert to 0-1 scale
                        ) * 100.0  # Convert back to percentage
                    except Exception as e:
                        # Fallback to simple temperature scaling for unsupervised case
                        logger.debug(f"Calibration failed for {model}, using temperature scaling: {e}")
                        calibrated_probs = self._apply_temperature_scaling(model_probs)

                    # Store results
                    model_predictions[model] = model_probs
                    # Ensure calibrated_probs is always a list
                    if hasattr(calibrated_probs, 'tolist'):
                        calibrated_predictions[model] = calibrated_probs.tolist()
                    else:
                        calibrated_predictions[model] = list(calibrated_probs)
                    model_weights[model] = consistency

            # Apply Robust Bayesian Expert Aggregation
            if model_predictions:
                # Prepare predictions and weights for Bayesian aggregation
                all_predictions = []
                all_weights = []
                model_names = []

                for model, probs in model_predictions.items():
                    model_mean = float(np.mean(probs))
                    all_predictions.append(model_mean / 100.0)  # Convert to 0-1 scale
                    all_weights.append(model_weights[model])
                    model_names.append(model)

                # Get Bayesian aggregated prediction
                bayesian_result = bayesian_aggregator.aggregate_forecasts(
                    forecasts=[p * 100.0 for p in all_predictions],  # Convert to 0-100 scale
                    expert_ids=model_names,
                    confidences=all_weights
                )
                bayesian_prediction = bayesian_result.get('aggregated_forecast', np.mean(all_predictions) * 100.0)

                # Get calibrated ensemble (mean of calibrated predictions)
                all_calibrated = []
                for cal_probs in calibrated_predictions.values():
                    all_calibrated.extend(cal_probs)
                calibrated_ensemble = float(np.mean(all_calibrated)) if all_calibrated else None

                # Enhanced statistics
                advanced_results = {
                    "bayesian_ensemble": float(bayesian_prediction),
                    "calibrated_ensemble": calibrated_ensemble,
                    "model_consistency_scores": model_weights,
                    "calibrated_predictions": calibrated_predictions,
                    "quality_assessment": {
                        "variance_reduction": self._calculate_variance_reduction(
                            valid_probabilities, bayesian_prediction
                        ),
                        "consensus_improvement": self._assess_consensus_improvement(
                            model_predictions, bayesian_prediction
                        )
                    },
                    "algorithm_comparison": {
                        "basic_mean": float(np.mean(valid_probabilities)),
                        "bayesian_weighted": float(bayesian_prediction),
                        "calibrated_mean": calibrated_ensemble,
                        "improvement_metrics": self._calculate_improvement_metrics(
                            valid_probabilities, bayesian_prediction, calibrated_ensemble
                        )
                    }
                }

                return advanced_results

        except Exception as e:
            logger.warning(f"Advanced algorithms failed: {e}")
            return {
                "error": str(e),
                "fallback_to_basic": True
            }

        return {"insufficient_data": True}

    def _calculate_variance_reduction(self, basic_predictions: List[float], enhanced_prediction: float) -> float:
        """Calculate how much variance is reduced by advanced algorithms"""
        try:
            import numpy as np
            basic_std = float(np.std(basic_predictions))
            # Variance reduction as percentage
            return max(0.0, (basic_std - abs(enhanced_prediction - np.mean(basic_predictions))) / basic_std * 100)
        except:
            return 0.0

    def _assess_consensus_improvement(self, model_predictions: Dict[str, List[float]], enhanced_prediction: float) -> Dict[str, float]:
        """Assess how much consensus is improved"""
        try:
            import numpy as np
            model_means = [np.mean(probs) for probs in model_predictions.values()]
            basic_range = max(model_means) - min(model_means)

            # How close is enhanced prediction to the center of the range
            center = (max(model_means) + min(model_means)) / 2
            enhanced_deviation = abs(enhanced_prediction - center)

            return {
                "basic_model_range": float(basic_range),
                "enhanced_deviation_from_center": float(enhanced_deviation),
                "consensus_score": max(0.0, (basic_range - enhanced_deviation) / basic_range * 100)
            }
        except:
            return {"error": "calculation_failed"}

    def _calculate_improvement_metrics(self, basic_predictions: List[float], bayesian_pred: float, calibrated_pred: Optional[float]) -> Dict[str, float]:
        """Calculate improvement metrics for different algorithms"""
        try:
            import numpy as np
            basic_mean = float(np.mean(basic_predictions))
            basic_std = float(np.std(basic_predictions))

            metrics = {
                "bayesian_vs_basic_difference": abs(bayesian_pred - basic_mean),
                "uncertainty_reduction": max(0.0, basic_std - abs(bayesian_pred - basic_mean))
            }

            if calibrated_pred is not None:
                metrics.update({
                    "calibrated_vs_basic_difference": abs(calibrated_pred - basic_mean),
                    "calibrated_vs_bayesian_difference": abs(calibrated_pred - bayesian_pred)
                })

            return metrics
        except:
            return {"error": "calculation_failed"}

    def _apply_temperature_scaling(self, probabilities: List[float], temperature: float = 1.5) -> List[float]:
        """
        Apply simple temperature scaling for unsupervised calibration

        Args:
            probabilities: List of probability values (0-100 scale)
            temperature: Temperature parameter for scaling (>1 = more uncertain, <1 = more confident)

        Returns:
            Calibrated probabilities
        """
        try:
            import numpy as np

            # Convert to 0-1 scale
            probs_01 = np.array(probabilities) / 100.0

            # Apply temperature scaling to logits
            # Convert probabilities to logits, scale, then back to probabilities
            epsilon = 1e-7  # Small value to avoid log(0)
            probs_01 = np.clip(probs_01, epsilon, 1 - epsilon)

            # Convert to logits
            logits = np.log(probs_01 / (1 - probs_01))

            # Apply temperature scaling
            scaled_logits = logits / temperature

            # Convert back to probabilities
            calibrated_probs_01 = 1 / (1 + np.exp(-scaled_logits))

            # Convert back to 0-100 scale
            calibrated_probs = calibrated_probs_01 * 100.0

            return calibrated_probs.tolist()

        except Exception as e:
            logger.warning(f"Temperature scaling failed: {e}, returning original probabilities")
            return probabilities