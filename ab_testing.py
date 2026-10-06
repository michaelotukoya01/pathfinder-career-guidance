# ab_testing.py
"""
A/B testing framework for the AI Career Recommendation System.
Allows comparison of different model versions, algorithms, or configurations.
"""

import json
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np

@dataclass
class ExperimentResult:
    """Result of a single experiment trial."""
    experiment_id: str
    variant: str
    user_id: Optional[str]
    timestamp: float
    input_data: Dict[str, Any]
    prediction: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class ExperimentMetrics:
    """Aggregated metrics for an experiment variant."""
    variant: str
    total_trials: int
    avg_confidence: float
    prediction_distribution: Dict[str, int]
    conversion_rate: float  # Custom metric - e.g., user satisfaction, action taken
    avg_processing_time: float

class ABTestManager:
    """
    Manages A/B tests for comparing different approaches in the recommendation system.
    """

    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.results: List[ExperimentResult] = []
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant

    def create_experiment(self,
                         name: str,
                         variants: List[str],
                         traffic_allocation: Optional[Dict[str, float]] = None) -> str:
        """
        Create a new A/B test experiment.

        Args:
            name: Unique name for the experiment
            variants: List of variant identifiers (e.g., ['control', 'treatment'])
            traffic_allocation: Optional dict mapping variant to traffic percentage (0-1)

        Returns:
            Experiment ID
        """
        experiment_id = str(uuid.uuid4())

        if traffic_allocation is None:
            # Equal distribution by default
            equal_share = 1.0 / len(variants)
            traffic_allocation = {v: equal_share for v in variants}

        # Validate traffic allocation
        total = sum(traffic_allocation.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total}")

        self.experiments[experiment_id] = {
            "name": name,
            "variants": variants,
            "traffic_allocation": traffic_allocation,
            "created_at": time.time(),
            "active": True
        }

        return experiment_id

    def assign_variant(self, experiment_id: str, user_id: Optional[str] = None) -> str:
        """
        Assign a user to a variant for an experiment.

        Args:
            experiment_id: ID of the experiment
            user_id: Optional user identifier for consistent assignment

        Returns:
            Assigned variant string
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        exp = self.experiments[experiment_id]
        if not exp["active"]:
            raise ValueError(f"Experiment {experiment_id} is not active")

        # If user_id provided, try to get consistent assignment
        if user_id and user_id in self.variant_assignments:
            # Check if this assignment is still valid for this experiment
            # In a real system, you'd store experiment-specific assignments
            pass

        # Assign based on traffic allocation
        rand_val = np.random.random()
        cumulative = 0.0

        for variant, allocation in exp["traffic_allocation"].items():
            cumulative += allocation
            if rand_val <= cumulative:
                # Store assignment for consistency (simplified)
                if user_id:
                    self.variant_assignments[f"{experiment_id}:{user_id}"] = variant
                return variant

        # Fallback to first variant
        return exp["variants"][0]

    def record_result(self,
                     experiment_id: str,
                     variant: str,
                     user_id: Optional[str],
                     input_data: Dict[str, Any],
                     prediction: str,
                     confidence: float,
                     processing_time: float,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Record a trial result for an experiment.

        Args:
            experiment_id: ID of the experiment
            variant: Variant that was used
            user_id: User identifier (can be None for anonymous)
            input_data: Input data used for the prediction
            prediction: Output prediction
            confidence: Confidence score of prediction
            processing_time: Time taken to generate prediction
            metadata: Additional metadata about the trial
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            user_id=user_id,
            timestamp=time.time(),
            input_data=input_data,
            prediction=prediction,
            confidence=confidence,
            metadata=metadata or {}
        )

        self.results.append(result)

    def get_experiment_results(self, experiment_id: str) -> Dict[str, ExperimentMetrics]:
        """
        Get aggregated results for an experiment.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Dictionary mapping variant to metrics
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Filter results for this experiment
        exp_results = [r for r in self.results if r.experiment_id == experiment_id]

        # Group by variant
        variant_results = defaultdict(list)
        for result in exp_results:
            variant_results[result.variant].append(result)

        # Calculate metrics for each variant
        metrics = {}
        exp = self.experiments[experiment_id]

        for variant in exp["variants"]:
            results = variant_results.get(variant, [])

            if not results:
                metrics[variant] = ExperimentMetrics(
                    variant=variant,
                    total_trials=0,
                    avg_confidence=0.0,
                    prediction_distribution={},
                    conversion_rate=0.0,
                    avg_processing_time=0.0
                )
                continue

            # Calculate metrics
            total_trials = len(results)
            avg_confidence = np.mean([r.confidence for r in results])

            # Prediction distribution
            pred_counts = defaultdict(int)
            for r in results:
                pred_counts[r.prediction] += 1

            # Conversion rate (placeholder - would be based on actual user actions)
            # For demo, we'll use a simple heuristic based on confidence
            conversion_rate = np.mean([1.0 if r.confidence > 0.7 else 0.0 for r in results])

            # Average processing time (if available in metadata)
            processing_times = []
            for r in results:
                if 'processing_time' in r.metadata:
                    processing_times.append(r.metadata['processing_time'])
            avg_processing_time = np.mean(processing_times) if processing_times else 0.0

            metrics[variant] = ExperimentMetrics(
                variant=variant,
                total_trials=total_trials,
                avg_confidence=float(avg_confidence),
                prediction_distribution=dict(pred_counts),
                conversion_rate=float(conversion_rate),
                avg_processing_time=float(avg_processing_time)
            )

        return metrics

    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get a summary of the experiment including statistical significance.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Dictionary with experiment summary
        """
        metrics = self.get_experiment_results(experiment_id)
        exp = self.experiments[experiment_id]

        # Determine if there's a clear winner (simplified)
        variants = list(metrics.keys())
        if len(variants) >= 2:
            # Compare first two variants based on confidence and conversion
            var_a, var_b = variants[0], variants[1]
            m_a, m_b = metrics[var_a], metrics[var_b]

            # Simple comparison: higher confidence and conversion is better
            score_a = m_a.avg_confidence * 0.6 + m_a.conversion_rate * 0.4
            score_b = m_b.avg_confidence * 0.6 + m_b.conversion_rate * 0.4

            if abs(score_a - score_b) < 0.05:
                winner = "inconclusive"
            else:
                winner = var_a if score_a > score_b else var_b
        else:
            winner = variants[0] if variants else None

        return {
            "experiment_id": experiment_id,
            "name": exp["name"],
            "variants": exp["variants"],
            "traffic_allocation": exp["traffic_allocation"],
            "created_at": exp["created_at"],
            "active": exp["active"],
            "total_trials": sum(m.total_trials for m in metrics.values()),
            "metrics": {k: asdict(v) for k, v in metrics.items()},
            "preliminary_winner": winner,
            "recommendation": self._get_recommendation(metrics, winner)
        }

    def _get_recommendation(self, metrics: Dict[str, ExperimentMetrics], winner: Optional[str]) -> str:
        """Get recommendation based on experiment results."""
        if not winner or winner == "inconclusive":
            return "Results are inconclusive. Consider running the experiment longer or increasing sample size."

        winning_metrics = metrics[winner]
        return f"Variant '{winner}' shows promising results with {winning_metrics.avg_confidence:.3f} avg confidence and {winning_metrics.conversion_rate:.3f} conversion rate. Consider rolling out to all traffic."

    def stop_experiment(self, experiment_id: str):
        """Stop an experiment from collecting new data."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["active"] = False

    def delete_experiment(self, experiment_id: str):
        """Delete an experiment and its data."""
        if experiment_id in self.experiments:
            del self.experiments[experiment_id]
        # Optionally keep results for historical analysis
        self.results = [r for r in self.results if r.experiment_id != experiment_id]

# Global instance
ab_test_manager = ABTestManager()

# Convenience functions
def create_ab_test(name: str, variants: List[str], traffic_allocation: Optional[Dict[str, float]] = None) -> str:
    """Create a new A/B test."""
    return ab_test_manager.create_experiment(name, variants, traffic_allocation)

def assign_variant(experiment_id: str, user_id: Optional[str] = None) -> str:
    """Assign a user to a variant."""
    return ab_test_manager.assign_variant(experiment_id, user_id)

def record_ab_test_result(experiment_id: str, variant: str, user_id: Optional[str],
                         input_data: Dict[str, Any], prediction: str,
                         confidence: float, processing_time: float,
                         metadata: Optional[Dict[str, Any]] = None):
    """Record a result for an A/B test."""
    ab_test_manager.record_result(experiment_id, variant, user_id, input_data,
                                 prediction, confidence, processing_time, metadata)

def get_ab_test_results(experiment_id: str) -> Dict[str, Any]:
    """Get results for an A/B test."""
    return ab_test_manager.get_experiment_summary(experiment_id)

# Example usage
if __name__ == "__main__":
    # Example: Comparing two model versions
    exp_id = create_ab_test(
        "model_v2_vs_v1",
        ["model_v1", "model_v2"],
        {"model_v1": 0.5, "model_v2": 0.5}
    )

    print(f"Created experiment: {exp_id}")
    print("To use:")
    print("1. Assign users: variant = assign_variant(experiment_id, user_id)")
    print("2. Record results: record_ab_test_result(exp_id, variant, user_id, input_data, prediction, confidence, processing_time)")
    print("3. Get results: results = get_ab_test_results(exp_id)")