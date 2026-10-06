# Pathfinder release model

## Intended use

An educational demonstration of technology-career exploration. The model ranks twelve career labels from self-reported ratings and background categories. It is not an aptitude test or a hiring, admissions, or employment-outcome predictor.

## Data and features

The repository contains 500 synthetically generated records. They are not observations of real students, employees, or employment outcomes. Labels reflect the rules in `generate_synthetic_data.py`.

The release trains on 45 fields: four background categories and 41 academic, technical, interest, work-preference, and personality ratings. IDs and target labels are excluded. The generator computes `confidence_score` and `skill_gaps` after selecting the target; these two fields are excluded to prevent target leakage.

Some demographic fields remain among the inputs. No fairness study, subgroup validation, or causal analysis has been performed. These fields must not be interpreted as evidence that a demographic characteristic determines career suitability.

## Training and evaluation

- Logistic regression with standardized numeric features and one-hot categorical encoding.
- Stratified 80/20 split, seed 42: 400 training records and 100 test records.
- Five stratified training folds select C from 0.1, 1, and 10 using macro F1; selected C is 0.1.
- Preprocessing is fitted inside each training fold. The final preprocessor is fitted only on the 400 training rows.
- The test partition is excluded from fitting and parameter selection. The same historical partition was inspected during earlier development, so this is not a new untouched external benchmark.

| Held-out metric | Result |
| --- | ---: |
| Top-choice accuracy | 0.45 |
| Top-three accuracy | 0.79 |
| Macro F1 | 0.4013 |
| Multiclass log loss | 1.4393 |
| Majority baseline accuracy | 0.18 |

Training-only CV macro F1 is 0.3461. Some classes have very few examples and poor or zero recall; the full [per-class report and confusion matrix](docs/model_evaluation.json) should be consulted instead of relying on aggregate accuracy.

These figures replace the earlier 54% claim, which involved target-derived fields and globally fitted preprocessing. Lower, properly scoped metrics are more informative than inflated comparisons.

## Inference behavior

Scores are uncalibrated model probabilities, not probabilities of career success. Mock market adjustments are off by default. Optional skill-recency adjustments are heuristic and have not been empirically validated. Skill targets are synthetic dataset averages, not verified employer requirements.

Optional third-party language-model explanations do not validate or improve the underlying classifier's measured accuracy. They must be considered explanatory text, not independent evidence.

## Reproducibility and next evaluation

Run `python training.py --output .run/model-candidate`. Dataset and artifact SHA-256 hashes are recorded in `docs/model_evaluation.json`. The candidate directory keeps a complete matching model, preprocessor, encoder, feature metadata, and evaluation report.

Before making stronger claims: collect consented representative data with meaningful outcomes, define an independent holdout before development, evaluate class balance and subgroup errors, measure calibration and uncertainty, and run usability studies with career-guidance professionals.
