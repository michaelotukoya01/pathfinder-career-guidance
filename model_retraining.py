# model_retraining.py
"""
Automated model retraining with drift detection and versioning for the AI Career Recommendation System.
"""

import os
import json
import pickle
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import joblib
import schedule
import time
import threading
from pathlib import Path

# Preprocessing and modeling imports
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression


class ModelRetrainer:
    """
    Handles automated model retraining, drift detection, and version management.
    """

    def __init__(self,
                 model_dir: str = "models",
                 data_dir: str = "data",
                 performance_threshold: float = 0.05,
                 check_interval_hours: int = 24):
        """
        Initialize the model retrainer.

        Args:
            model_dir: Directory to store model versions
            data_dir: Directory containing training data
            performance_threshold: Minimum performance drop to trigger retraining
            check_interval_hours: How often to check for retraining needs
        """
        self.model_dir = Path(__file__).resolve().parent / model_dir
        self.data_dir = Path(__file__).resolve().parent / data_dir
        self.performance_threshold = performance_threshold
        self.check_interval_hours = check_interval_hours

        # Create directories if they don't exist
        self.model_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Track current model info
        self.current_model_path = self.model_dir / "current_model.pkl"
        self.current_preprocessor_path = self.model_dir / "current_preprocessor.pkl"
        self.current_label_encoder_path = self.model_dir / "current_label_encoder.pkl"
        self.metadata_path = self.model_dir / "model_metadata.json"

        # Performance tracking
        self.performance_history = []

        # Scheduler thread
        self.scheduler_thread = None
        self._stop_event = threading.Event()
        self._scheduler = schedule.Scheduler()

        # Load existing model or initialize
        self._load_current_model()

    def _load_current_model(self):
        """Load the current production model."""
        try:
            if self.current_model_path.exists():
                self.model = joblib.load(self.current_model_path)
                self.preprocessor = joblib.load(self.current_preprocessor_path)
                self.label_encoder = joblib.load(self.current_label_encoder_path)
                self._validate_artifacts(self.model, self.preprocessor, self.label_encoder)
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                print(f"Loaded current model version {self.metadata.get('version', 'unknown')}")
            else:
                print("No current model found. Will need to train initial model.")
                self.model = None
                self.preprocessor = None
                self.label_encoder = None
                self.metadata = {}
        except Exception as e:
            print(f"Error loading current model: {e}")
            self.model = None
            self.preprocessor = None
            self.label_encoder = None
            self.metadata = {}

    def _validate_artifacts(self, model, preprocessor, label_encoder):
        """Reject legacy artifact sets that cannot process the API's numeric input."""
        features, _, _ = self.load_training_data()
        if set(getattr(preprocessor, 'feature_names_in_', [])) != set(features.columns):
            raise ValueError("Stored model feature schema differs from the release schema; retrain before promotion")
        sample = features.iloc[:1].copy()
        numeric = sample.select_dtypes(include=[np.number]).columns
        sample[numeric] = sample[numeric].astype(float)
        processed = preprocessor.transform(sample)
        probabilities = model.predict_proba(processed)
        label_encoder.inverse_transform(model.classes_)
        if probabilities.shape[1] != len(label_encoder.classes_):
            raise ValueError("Model and label encoder classes do not match")

    def _save_model_version(self,
                           model: Any,
                           preprocessor: Any,
                           label_encoder: Any,
                           metadata: Dict[str, Any]) -> str:
        """
        Save a model version and return its version ID.

        Args:
            model: Trained model object
            preprocessor: Fitted preprocessor
            label_encoder: Fitted label encoder
            metadata: Metadata about this version

        Returns:
            Version ID string
        """
        # Generate version ID based on timestamp and hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        version_id = f"v{timestamp}"
        metadata = {**metadata, "version": version_id}

        # Create version directory
        version_dir = self.model_dir / version_id
        version_dir.mkdir(exist_ok=True)

        # Save components
        model_path = version_dir / "model.pkl"
        preprocessor_path = version_dir / "preprocessor.pkl"
        label_encoder_path = version_dir / "label_encoder.pkl"
        metadata_path = version_dir / "metadata.json"

        joblib.dump(model, model_path)
        joblib.dump(preprocessor, preprocessor_path)
        joblib.dump(label_encoder, label_encoder_path)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Update current model symlinks/copies
        joblib.dump(model, self.current_model_path)
        joblib.dump(preprocessor, self.current_preprocessor_path)
        joblib.dump(label_encoder, self.current_label_encoder_path)
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Update current model reference
        self.model = model
        self.preprocessor = preprocessor
        self.label_encoder = label_encoder
        self.metadata = metadata
        callback = getattr(self, "on_model_updated", None)
        if callback:
            callback()

        print(f"Saved model version {version_id}")
        return version_id

    def _calculate_model_hash(self, model: Any) -> str:
        """Calculate a hash of the model for change detection."""
        # Serialize model to bytes and hash
        model_bytes = pickle.dumps(model)
        return hashlib.md5(model_bytes).hexdigest()

    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data for retraining.
        In a real system, this would load from a database or feature store.
        """
        # For now, load the original synthetic data
        data_path = self.data_dir / "synthetic_career_data.csv"
        if not data_path.exists():
            # Fallback to root directory
            data_path = Path(__file__).resolve().parent / "synthetic_career_data.csv"

        df = pd.read_csv(data_path)

        # Prepare features and target
        from training import EXCLUDED_COLUMNS
        feature_cols = [col for col in df.columns if col not in EXCLUDED_COLUMNS]
        X = df[feature_cols]
        y = df['recommended_career']

        return X, y.values, feature_cols

    def preprocess_features(self, X: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, ColumnTransformer, LabelEncoder]:
        """
        Preprocess features using the same logic as in data_preprocessing.py.
        Returns processed features, fitted preprocessor, and fitted label encoder.
        """
        # Identify column types
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = [column for column in X.columns if column not in numeric_features]

        # Create preprocessing pipelines
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])

        # Combine preprocessing steps
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])

        # Fit and transform the data
        X_processed = preprocessor.fit_transform(X)

        # Encode target variable (we'll do this separately for y)
        return X_processed, preprocessor

    def evaluate_model_performance(self,
                                 model: Any,
                                 preprocessor: Any,
                                 label_encoder: Any,
                                 X_test: np.ndarray,
                                 y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance on test data.

        Returns:
            Dictionary with accuracy, f1_score, etc.
        """
        # Preprocess test data
        X_test_processed = preprocessor.transform(X_test)

        # Make predictions
        y_pred = model.predict(X_test_processed)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')

        return {
            "accuracy": float(accuracy),
            "f1_score": float(f1),
            "timestamp": datetime.now().isoformat()
        }

    def detect_data_drift(self,
                         reference_data: np.ndarray,
                         current_data: np.ndarray,
                         feature_names: List[str],
                         threshold: float = 0.1) -> Dict[str, Any]:
        """
        Detect data drift using statistical tests.
        Simplified implementation using mean and std differences.
        """
        if reference_data.shape[1] != current_data.shape[1]:
            raise ValueError("Reference and current data must have same number of features")

        drift_detected = False
        drift_details = {}

        for i, feature_name in enumerate(feature_names):
            ref_mean = np.mean(reference_data[:, i])
            ref_std = np.std(reference_data[:, i])
            curr_mean = np.mean(current_data[:, i])
            curr_std = np.std(current_data[:, i])

            # Calculate normalized difference in means
            if ref_std > 0:
                mean_diff = abs(ref_mean - curr_mean) / ref_std
            else:
                mean_diff = abs(ref_mean - curr_mean)

            # Calculate ratio of stds
            if ref_std > 0:
                std_ratio = curr_std / ref_std
            else:
                std_ratio = 1.0 if curr_std == 0 else float('inf')

            # Drift detected if significant change in mean or std
            drift_feature = (mean_diff > threshold) or (abs(std_ratio - 1.0) > threshold)
            if drift_feature:
                drift_detected = True

            drift_details[feature_name] = {
                "mean_difference": float(mean_diff),
                "std_ratio": float(std_ratio),
                "drift_detected": bool(drift_feature)
            }

        return {
            "drift_detected": drift_detected,
            "details": drift_details,
            "drift_score": np.mean([det["mean_difference"] for det in drift_details.values()])
        }

    def should_retrain(self) -> Tuple[bool, str]:
        """
        Determine if the model should be retrained based on performance degradation or data drift.

        Returns:
            Tuple of (should_retrain, reason)
        """
        # Check if we have a current model
        if self.model is None:
            return True, "No current model found"

        # Check time-based retraining (if enabled)
        if hasattr(self, 'last_training_time'):
            time_since_training = datetime.now() - self.last_training_time
            if time_since_training > timedelta(hours=self.check_interval_hours):
                return True, f"Time-based trigger: {self.check_interval_hours} hours elapsed"

        # Load recent performance data (in real system, this would come from monitoring)
        # For now, we'll simulate by checking if we have new data
        try:
            X_raw, y_raw, feature_cols = self.load_training_data()
            X_df = pd.DataFrame(X_raw, columns=feature_cols)

            # Evaluate using the current model's fitted feature and label mappings.
            y_encoded = self.label_encoder.transform(y_raw)
            _, X_test, _, y_test = train_test_split(
                X_df, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )
            current_performance = self.evaluate_model_performance(
                self.model, self.preprocessor, self.label_encoder, X_test, y_test
            )

            # Check if we have historical performance to compare
            if self.performance_history:
                last_performance = self.performance_history[-1]
                accuracy_drop = last_performance["accuracy"] - current_performance["accuracy"]

                if accuracy_drop > self.performance_threshold:
                    return True, f"Performance degradation: accuracy dropped by {accuracy_drop:.3f}"

            # Store current performance
            self.performance_history.append(current_performance)

            # Check for data drift (comparing recent data to training data)
            # In practice, you'd compare recent production data to training data
            # For demo, we'll skip this or use a simplified check

        except Exception as e:
            print(f"Error during evaluation: {e}")
            return True, f"Evaluation error: {str(e)}"

        return False, "No retraining trigger detected"

    def retrain_model(self,
                     force: bool = False,
                     validation_split: float = 0.2) -> Optional[str]:
        """
        Retrain the model with latest data.

        Args:
            force: Force retraining even if not triggered
            validation_split: Fraction of data to use for validation

        Returns:
            Version ID of new model if retrained, None otherwise
        """
        # Check if retraining is needed
        if not force:
            should_retrain, reason = self.should_retrain()
            if not should_retrain:
                print(f"Retraining not needed: {reason}")
                return None
            print(f"Retraining triggered: {reason}")

        try:
            print("Loading training data...")
            X_raw, y_raw, feature_cols = self.load_training_data()
            X_df = pd.DataFrame(X_raw, columns=feature_cols)

            label_encoder = LabelEncoder()
            y_encoded = label_encoder.fit_transform(y_raw)
            # Fit preprocessing on training rows only to avoid validation leakage.
            X_train_raw, X_val_raw, y_train, y_val = train_test_split(
                X_df, y_encoded, test_size=validation_split, random_state=42, stratify=y_encoded
            )
            X_train, preprocessor = self.preprocess_features(X_train_raw, feature_cols)
            X_val = preprocessor.transform(X_val_raw)

            print(f"Training set size: {X_train.shape[0]}")
            print(f"Validation set size: {X_val.shape[0]}")

            # Train model (using LogisticRegression as it was the best model in baseline)
            print("Training model...")
            model = LogisticRegression(random_state=42, max_iter=1000)
            model.fit(X_train, y_train)

            # Evaluate on validation set
            print("Evaluating model...")
            val_predictions = model.predict(X_val)
            val_accuracy = accuracy_score(y_val, val_predictions)
            val_f1 = f1_score(y_val, val_predictions, average='weighted')

            print(f"Validation accuracy: {val_accuracy:.4f}")
            print(f"Validation F1 score: {val_f1:.4f}")

            # Prepare metadata
            metadata = {
                "version": f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "training_samples": int(X_train.shape[0]),
                "validation_samples": int(X_val.shape[0]),
                "validation_accuracy": float(val_accuracy),
                "validation_f1_score": float(val_f1),
                "feature_count": int(X_train.shape[1]),
                "class_count": len(np.unique(y_encoded)),
                "training_trigger": "manual" if force else "automatic",
                "retrain_reason": self.should_retrain()[1] if not force else "forced"
            }

            # Save the new version
            version_id = self._save_model_version(
                model, preprocessor, label_encoder, metadata
            )

            self.last_training_time = datetime.now()

            print(f"Model retraining completed. New version: {version_id}")
            return version_id

        except Exception as e:
            print(f"Error during retraining: {e}")
            import traceback
            traceback.print_exc()
            return None

    def start_scheduler(self):
        """Start one interruptible scheduler owned by this retrainer."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return
        self._stop_event.clear()
        self._scheduler.clear()
        self._scheduler.every(self.check_interval_hours).hours.do(self._scheduled_check)

        def run_scheduler():
            while not self._stop_event.wait(1):
                self._scheduler.run_pending()

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """Stop promptly, without leaving duplicate jobs on restart."""
        self._stop_event.set()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        self._scheduler.clear()

    def _scheduled_check(self):
        """Internal method called by scheduler to check for retraining needs."""
        try:
            print(f"[{datetime.now()}] Performing scheduled retraining check...")
            version_id = self.retrain_model()
            if version_id:
                print(f"[{datetime.now()}] Scheduled retraining completed: {version_id}")
            else:
                print(f"[{datetime.now()}] No retraining needed at this time.")
        except Exception as e:
            print(f"[{datetime.now()}] Error during scheduled check: {e}")

    def get_model_versions(self) -> List[Dict[str, Any]]:
        """Get information about all available model versions."""
        versions = []

        if self.model_dir.exists():
            for version_dir in self.model_dir.iterdir():
                if version_dir.is_dir() and version_dir.name.startswith('v'):
                    metadata_path = version_dir / "metadata.json"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            versions.append({
                                "version_id": version_dir.name,
                                "path": str(version_dir),
                                "metadata": metadata
                            })
                        except Exception as e:
                            print(f"Error reading metadata for {version_dir.name}: {e}")

        # Sort by version (newest first)
        versions.sort(key=lambda x: x["version_id"], reverse=True)
        return versions

    def promote_model(self, version_id: str) -> bool:
        """
        Promote a specific version to be the current model.

        Args:
            version_id: Version ID to promote

        Returns:
            True if successful, False otherwise
        """
        if not version_id or Path(version_id).name != version_id or not version_id.startswith("v"):
            return False
        version_dir = self.model_dir / version_id
        if not version_dir.exists():
            print(f"Version {version_id} not found")
            return False

        try:
            # Load the version
            model = joblib.load(version_dir / "model.pkl")
            preprocessor = joblib.load(version_dir / "preprocessor.pkl")
            label_encoder = joblib.load(version_dir / "label_encoder.pkl")
            self._validate_artifacts(model, preprocessor, label_encoder)

            with open(version_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)

            # Promote to current
            joblib.dump(model, self.current_model_path)
            joblib.dump(preprocessor, self.current_preprocessor_path)
            joblib.dump(label_encoder, self.current_label_encoder_path)
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            self.model, self.preprocessor, self.label_encoder = model, preprocessor, label_encoder
            self.metadata = metadata
            callback = getattr(self, "on_model_updated", None)
            if callback:
                callback()
            print(f"Promoted version {version_id} to current model")
            return True
        except Exception as e:
            print(f"Error promoting version {version_id}: {e}")
            return False

# Global instance
model_retrainer = ModelRetrainer(
    model_dir=os.getenv("MODEL_STORAGE_DIR", "models"),
    data_dir=os.getenv("TRAINING_DATA_DIR", "data"),
)

# Convenience functions
def start_retraining_scheduler():
    """Start the automatic retraining scheduler."""
    model_retrainer.start_scheduler()

def stop_retraining_scheduler():
    """Stop the automatic retraining scheduler."""
    model_retrainer.stop_scheduler()

def check_and_retrain(force: bool = False) -> Optional[str]:
    """Check if retraining is needed and perform it if so."""
    return model_retrainer.retrain_model(force=force)

def get_model_versions() -> List[Dict[str, Any]]:
    """Get all available model versions."""
    return model_retrainer.get_model_versions()

def promote_model_version(version_id: str) -> bool:
    """Promote a specific version to current."""
    return model_retrainer.promote_model(version_id)

if __name__ == "__main__":
    # Example usage
    print("Model Retrainer initialized")
    print("To start automatic retraining: start_retraining_scheduler()")
    print("To manually trigger retraining: check_and_retrain()")
    print("To force retraining: check_and_retrain(force=True)")
