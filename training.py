"""Reproducible training with train-only preprocessing and no target-derived inputs."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, log_loss, top_k_accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
# The synthetic generator computes confidence_score and skill_gaps AFTER choosing
# the target career. Neither is valid evidence for predicting that target.
EXCLUDED_COLUMNS = {'user_id', 'recommended_career', 'top_3_careers', 'skill_gaps', 'confidence_score'}


def make_preprocessor(features):
    numeric = features.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [column for column in features if column not in numeric]
    return ColumnTransformer([
        ('num', StandardScaler(), numeric),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical),
    ])


def train_and_evaluate(data_path=BASE_DIR / 'synthetic_career_data.csv', output_dir=None):
    data_path = Path(data_path)
    frame = pd.read_csv(data_path)
    features = frame.drop(columns=list(EXCLUDED_COLUMNS), errors='ignore')
    labels = LabelEncoder().fit(frame['recommended_career'])
    target = labels.transform(frame['recommended_career'])
    train_x, test_x, train_y, test_y = train_test_split(features, target, test_size=0.2, random_state=42, stratify=target)
    pipeline = Pipeline([('preprocess', make_preprocessor(features)), ('model', LogisticRegression(max_iter=2000, random_state=42))])
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    search = GridSearchCV(pipeline, {'model__C': [0.1, 1.0, 10.0]}, cv=folds, scoring='f1_macro', n_jobs=1)
    search.fit(train_x, train_y)
    fitted = search.best_estimator_
    predictions = fitted.predict(test_x)
    probabilities = fitted.predict_proba(test_x)
    baseline = DummyClassifier(strategy='most_frequent').fit(train_x, train_y)
    numeric = train_x.select_dtypes(include=[np.number]).columns.tolist()
    info = {
        'original_features': list(features.columns), 'numeric_features': numeric,
        'categorical_features': [column for column in features if column not in numeric],
        'target_classes': labels.classes_.tolist(), 'train_size': len(train_x), 'test_size': len(test_x),
        'excluded_target_derived_features': ['confidence_score', 'skill_gaps'],
    }
    report = {
        'dataset': data_path.name, 'dataset_sha256': hashlib.sha256(data_path.read_bytes()).hexdigest(),
        'data_type': 'synthetic; no real-world validity established', 'random_seed': 42,
        'training_rows': len(train_x), 'test_rows': len(test_x), 'input_features': len(features.columns),
        'method': 'stratified 80/20 split; 5-fold train-only pipeline CV for C; held-out test used once',
        'excluded_columns': sorted(EXCLUDED_COLUMNS), 'best_C': search.best_params_['model__C'],
        'cv_macro_f1': float(search.best_score_), 'test_accuracy': float(accuracy_score(test_y, predictions)),
        'test_macro_f1': float(f1_score(test_y, predictions, average='macro')),
        'test_top_3_accuracy': float(top_k_accuracy_score(test_y, probabilities, k=3, labels=np.arange(len(labels.classes_)))),
        'test_log_loss': float(log_loss(test_y, probabilities, labels=np.arange(len(labels.classes_)))),
        'majority_baseline_accuracy': float(accuracy_score(test_y, baseline.predict(test_x))),
        'per_class': classification_report(test_y, predictions, target_names=labels.classes_, output_dict=True, zero_division=0),
        'confusion_matrix': confusion_matrix(test_y, predictions).tolist(), 'classes': labels.classes_.tolist(),
        'limitations': ['Small synthetic dataset', 'No employment outcomes or demographic fairness validation',
                        'Probability scores are uncalibrated', 'Existing historical holdout has been inspected in prior development'],
    }
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        joblib.dump(fitted.named_steps['model'], output / 'best_model.pkl')
        joblib.dump(fitted.named_steps['preprocess'], output / 'preprocessor.pkl')
        joblib.dump(labels, output / 'label_encoder.pkl')
        (output / 'preprocessing_info.json').write_text(json.dumps(info, indent=2), encoding='utf-8', newline='\n')
        report['artifacts_sha256'] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                      for name in ['best_model.pkl', 'preprocessor.pkl', 'label_encoder.pkl', 'preprocessing_info.json']}
        (output / 'model_evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8', newline='\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=BASE_DIR / 'synthetic_career_data.csv')
    parser.add_argument('--output', type=Path, default=BASE_DIR / '.run' / 'model-candidate')
    args = parser.parse_args()
    report = train_and_evaluate(args.data, args.output)
    print(json.dumps({key: report[key] for key in ['test_accuracy', 'test_macro_f1', 'test_top_3_accuracy', 'majority_baseline_accuracy']}, indent=2))
    print(f'Artifacts and full evaluation saved to {args.output}')


if __name__ == '__main__':
    main()
