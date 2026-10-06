# Recommendation Engine with Skill Gap Analysis for AI Career Recommendation System
# Uses trained model to predict career and identify skill gaps
# Enhanced with skill decay modeling

import numpy as np
import pandas as pd
import joblib
import json
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

# Import skill decay utilities
from skill_decay_utils import SkillDecayModel

def load_artifacts():
    """Load the trained model, preprocessor, label encoder, and feature names."""
    print("Loading model and preprocessing artifacts...")
    model = joblib.load('best_model.pkl')  # This is the Logistic Regression model
    preprocessor = joblib.load('preprocessor.pkl')
    label_encoder = joblib.load('label_encoder.pkl')

    with open('feature_names.json', 'r') as f:
        feature_names = json.load(f)

    return model, preprocessor, label_encoder, feature_names

def load_training_data():
    """Load the original training data to compute career-wise skill averages."""
    print("Loading training data for skill profile computation...")
    df = pd.read_csv('synthetic_career_data.csv')
    # We need to separate features and target as done in preprocessing
    feature_cols = [col for col in df.columns if col not in ['user_id', 'recommended_career', 'top_3_careers']]
    X = df[feature_cols]
    y = df['recommended_career']
    return X, y

def get_career_skill_profiles(X, y):
    """
    Compute average skill levels for each career from the training data.
    Returns a dictionary mapping career names to arrays of skill values.
    """
    # Identify skill columns (those starting with 'skill_') and exclude non-numeric ones like 'skill_gaps'
    skill_cols = [col for col in X.columns if col.startswith('skill_') and col != 'skill_gaps']
    # Further ensure we only take numeric columns (should be all numeric except skill_gaps)
    skill_cols = [col for col in skill_cols if pd.api.types.is_numeric_dtype(X[col])]
    skill_data = X[skill_cols]

    # Combine with target
    df_skills = skill_data.copy()
    df_skills['career'] = y.values

    # Compute mean skill values per career
    career_skill_profiles = {}
    for career in df_skills['career'].unique():
        career_data = df_skills[df_skills['career'] == career]
        # Average of each skill for this career
        avg_skills = career_data[skill_cols].mean().values
        career_skill_profiles[career] = avg_skills

    return career_skill_profiles, skill_cols

def preprocess_user_input(user_data_raw, preprocessor):
    """
    Preprocess user input to match the format expected by the model.
    user_data_raw: dict containing raw feature values (same as original features)
    """
    # Convert to DataFrame with single row
    df_user = pd.DataFrame([user_data_raw])
    # Apply the same preprocessing steps
    user_processed = preprocessor.transform(df_user)
    return user_processed

def predict_career(model, processed_input, label_encoder):
    """Predict career and return probabilities."""
    # Get predicted class
    pred_encoded = model.predict(processed_input)
    pred_career = label_encoder.inverse_transform(pred_encoded)[0]

    # Get probabilities
    probabilities = model.predict_proba(processed_input)[0]
    # Get top 3 predictions
    top_3_indices = np.argsort(probabilities)[::-1][:3]
    top_3_careers = label_encoder.inverse_transform(top_3_indices)
    top_3_probabilities = probabilities[top_3_indices]

    return pred_career, list(zip(top_3_careers, top_3_probabilities))

def apply_skill_decay(user_data, decay_model=None):
    """
    Apply skill decay to user data based on last_used timestamps.

    Args:
        user_data: Dictionary containing user data including potential 'last_used_*' fields
        decay_model: Optional SkillDecayModel instance (will create if not provided)

    Returns:
        Dictionary with decayed skill values applied
    """
    if decay_model is None:
        decay_model = SkillDecayModel()

    # Create a copy to avoid modifying original
    decayed_data = user_data.copy()

    # Identify all skill-related fields
    skill_fields = [key for key in user_data.keys() if key.startswith('skill_') and
                   key != 'skill_gaps' and
                   isinstance(user_data[key], (int, float))]

    # For each skill, check if there's a corresponding last_used field
    for skill_field in skill_fields:
        last_used_field = f"last_used_{skill_field}"

        if last_used_field in user_data and user_data[last_used_field] is not None:
            # Apply decay based on last used date
            try:
                decayed_value = decay_model.calculate_decayed_skill(
                    user_data[skill_field],
                    skill_field,
                    user_data[last_used_field]
                )
                decayed_data[skill_field] = decayed_value
            except Exception as e:
                # If there's an error in date parsing, keep original value
                print(f"Warning: Could not apply decay to {skill_field}: {e}")
                pass

    return decayed_data

def calculate_skill_gaps(user_data, career_skill_profiles, skill_cols, predicted_career, decay_model=None):
    """
    Calculate skill gaps for the predicted career, incorporating skill decay.

    Args:
        user_data: Dictionary containing user data (may include last_used_* fields)
        career_skill_profiles: dict mapping career to average skill levels
        skill_cols: list of skill column names
        predicted_career: the career predicted by the model
        decay_model: Optional SkillDecayModel instance

    Returns:
        Tuple of (skill_gap_info, career_avg_skills) where skill_gap_info is a list of dicts
        containing skill, user_level, career_average, and gap
    """
    if decay_model is None:
        decay_model = SkillDecayModel()

    # Apply skill decay to user data
    decayed_user_data = apply_skill_decay(user_data, decay_model)

    if predicted_career not in career_skill_profiles:
        return None, None

    career_avg_skills = career_skill_profiles[predicted_career]

    # Extract user's skill vector (in the same order as skill_cols) from decayed data
    user_skills = np.array([decayed_user_data.get(col, 0) for col in skill_cols])

    # Compute difference (career average - user level)
    skill_differences = career_avg_skills - user_skills

    # Create a list of tuples (skill_name, user_level, career_average, gap)
    skill_gap_info = []
    for i, skill in enumerate(skill_cols):
        skill_gap_info.append({
            'skill': skill,
            'user_level': float(user_skills[i]),
            'career_average': float(career_avg_skills[i]),
            'gap': float(skill_differences[i])
        })

    # Sort by gap (largest gap first - areas needing most improvement)
    skill_gap_info.sort(key=lambda x: x['gap'], reverse=True)

    return skill_gap_info, career_avg_skills

def generate_learning_recommendations(skill_gap_info, top_n=5):
    """
    Generate learning recommendations based on skill gaps.
    Returns top N skills to improve.
    """
    # Filter for positive gaps (where career average > user level)
    deficits = [skill for skill in skill_gap_info if skill['gap'] > 0]

    # Sort by gap descending (largest deficit first)
    deficits.sort(key=lambda x: x['gap'], reverse=True)

    # Return top N recommendations
    return deficits[:top_n]

def get_skill_decay_info(user_data, decay_model=None):
    """
    Get information about skill decay applied to user data.

    Returns:
        Dictionary mapping skill names to decay information
    """
    if decay_model is None:
        decay_model = SkillDecayModel()

    decay_info = {}

    # Identify all skill-related fields
    skill_fields = [key for key in user_data.keys() if key.startswith('skill_') and
                   key != 'skill_gaps' and
                   isinstance(user_data[key], (int, float))]

    for skill_field in skill_fields:
        last_used_field = f"last_used_{skill_field}"

        if last_used_field in user_data and user_data[last_used_field] is not None:
            try:
                original_level = user_data[skill_field]
                decayed_level = decay_model.calculate_decayed_skill(
                    original_level,
                    skill_field,
                    user_data[last_used_field]
                )

                decay_info[skill_field] = {
                    'original_level': original_level,
                    'decayed_level': decayed_level,
                    'decay_amount': original_level - decayed_level,
                    'last_used': user_data[last_used_field],
                    'days_since_used': (datetime.now() - datetime.strptime(user_data[last_used_field], '%Y-%m-%d')).days
                }
            except Exception as e:
                decay_info[skill_field] = {
                    'error': str(e),
                    'original_level': user_data[skill_field],
                    'decayed_level': user_data[skill_field]
                }
        else:
            decay_info[skill_field] = {
                'original_level': user_data[skill_field],
                'decayed_level': user_data[skill_field],
                'decay_amount': 0,
                'last_used': None,
                'days_since_used': None
            }

    return decay_info

def main():
    """Main function to demonstrate the recommendation engine with skill decay."""
    print("="*60)
    print("AI Career Recommendation Engine with Skill Gap Analysis")
    print("Enhanced with Skill Decay Modeling")
    print("="*60)

    # Load artifacts
    model, preprocessor, label_encoder, feature_names = load_artifacts()

    # Load training data to compute career skill profiles
    X_train_raw, y_train = load_training_data()
    career_skill_profiles, skill_cols = get_career_skill_profiles(X_train_raw, y_train)

    print(f"\nLoaded model: {type(model).__name__}")
    print(f"Available careers: {list(label_encoder.classes_)}")
    print(f"Number of skill features: {len(skill_cols)}")

    # Initialize decay model
    decay_model = SkillDecayModel()

    # Example: Create a sample user profile with skill decay information
    print("\n" + "-"*50)
    print("EXAMPLE RECOMMENDATION WITH SKILL DECAY")
    print("-"*50)

    # Let's create a hypothetical user by sampling from the dataset
    sample_idx = 0  # First user in dataset
    sample_user_raw = {}

    # Get the original feature names (before preprocessing)
    df_original = pd.read_csv('synthetic_career_data.csv')
    feature_cols = [col for col in df_original.columns if col not in ['user_id', 'recommended_career', 'top_3_careers']]

    # Create user data from sample
    for i, col in enumerate(feature_cols):
        sample_user_raw[col] = df_original.iloc[sample_idx][col]

    # Add skill decay information (last used dates)
    # Note: Using the actual column names from the dataset (with spaces)
    sample_user_raw['last_used_skill_python'] = '2022-06-01'   # Used ~1.5 years ago
    sample_user_raw['last_used_skill_java'] = '2020-01-01'     # Used ~4 years ago
    sample_user_raw['last_used_skill_machine learning'] = None # Never used recently (note the space)
    sample_user_raw['last_used_skill_data analysis'] = '2023-01-15'                   # Used ~1 year ago (note the space)

    # Let's modify some skills to create a gap
    # Reduce some key skills by 2 points (but not below 0)
    skills_to_reduce = ['skill_python', 'skill_java', 'skill_machine learning']
    for skill in skills_to_reduce:
        if skill in sample_user_raw:
            sample_user_raw[skill] = max(0, sample_user_raw[skill] - 2)

    print(f"Sample user profile (modified to show skill gaps):")
    print(f"  Age range: {sample_user_raw['age_range']}")
    print(f"  Education: {sample_user_raw['education_level']}")
    print(f"  Field of study: {sample_user_raw['field_of_study']}")
    print(f"  Year of study: {sample_user_raw['year_of_study']}")
    print(f"  Confidence score: {sample_user_raw['confidence_score']:.3f}")

    # Show some skill values with decay info
    print(f"  Python: {sample_user_raw['skill_python']} (last used: {sample_user_raw.get('last_used_skill_python', 'N/A')})")
    print(f"  Java: {sample_user_raw['skill_java']} (last used: {sample_user_raw.get('last_used_skill_java', 'N/A')})")
    print(f"  ML: {sample_user_raw['skill_machine learning']} (last used: {sample_user_raw.get('last_used_skill_machine learning', 'N/A')})")
    print(f"  Data Analysis: {sample_user_raw['skill_data analysis']} (last used: {sample_user_raw.get('last_used_skill_data analysis', 'N/A')})")

    # Preprocess user input
    try:
        processed_input = preprocess_user_input(sample_user_raw, preprocessor)
    except Exception as e:
        print(f"Error preprocessing user input: {e}")
        print("Falling back to using the first row of training data as example...")
        processed_input = preprocessor.transform(X_train_raw.iloc[[0]])
        # Use the actual first user's data
        for col in feature_cols:
            sample_user_raw[col] = X_train_raw.iloc[0][col]

    # Predict career
    predicted_career, top_3_predictions = predict_career(model, processed_input, label_encoder)

    print(f"\nTop 3 Career Predictions:")
    for i, (career, prob) in enumerate(top_3_predictions, 1):
        print(f"  {i}. {career}: {prob:.3f}")

    print(f"\nPrimary Recommendation: {predicted_career}")

    # Extract user's skill vector (in the same order as skill_cols) BEFORE decay for comparison
    user_skills_original = np.array([sample_user_raw.get(col, 0) for col in skill_cols])

    # Apply skill decay and get decayed skills
    decayed_user_data = apply_skill_decay(sample_user_raw, decay_model)
    user_skills_decayed = np.array([decayed_user_data.get(col, 0) for col in skill_cols])

    # Calculate skill gaps with decay
    skill_gap_info, career_avg_skills = calculate_skill_gaps(
        sample_user_raw, career_skill_profiles, skill_cols, predicted_career, decay_model
    )

    if skill_gap_info is None:
        print(f"\nCould not compute skill gaps for {predicted_career}")
    else:
        print(f"\nSkill Gap Analysis for {predicted_career} (with skill decay):")
        print(f"{'Skill':<25} {'User Level':<12} {'Decayed Level':<15} {'Career Avg':<12} {'Gap':<8}")
        print("-"*80)
        for i, skill_info in enumerate(skill_gap_info[:10]):  # Show top 10
            skill_name = skill_info['skill']
            user_level = skill_info['user_level']
            # Get the decayed level for this skill
            decayed_level = decayed_user_data.get(skill_name, user_level)
            career_avg = skill_info['career_average']
            gap = skill_info['gap']
            print(f"{skill_name:<25} {user_level:<12.2f} {decayed_level:<15.2f} {career_avg:<12.2f} {gap:<8.2f}")

        # Show decay information
        print(f"\nSkill Decay Information:")
        print(f"{'Skill':<25} {'Original':<10} {'Decayed':<10} {'Decay':<10} {'Days Ago':<10}")
        print("-"*65)
        decay_info = get_skill_decay_info(sample_user_raw, decay_model)
        for skill in ['skill_python', 'skill_java', 'skill_machine learning', 'skill_data analysis']:
            if skill in decay_info:
                info = decay_info[skill]
                if 'error' not in info:
                    orig = info['original_level']
                    decayed = info['decayed_level']
                    decay_amt = info['decay_amount']
                    days = info.get('days_since_used', 'N/A')
                    days_str = f"{days}" if isinstance(days, int) else days
                    print(f"{skill:<25} {orig:<10.2f} {decayed:<10.2f} {decay_amt:<10.2f} {days_str:<10}")
                else:
                    print(f"{skill:<25} {'ERROR':<10} {'ERROR':<10} {'ERROR':<10} {'ERROR':<10}")

        # Show overall match percentage
        total_possible_gap = len(skill_cols) * 5  # Max gap per skill is 5 (if user=0, career=5)
        total_actual_gap = sum(max(0, skill['gap']) for skill in skill_gap_info)  # Only count deficits
        match_percentage = max(0, 100 - (total_actual_gap / total_possible_gap * 100)) if total_possible_gap > 0 else 100
        print(f"\nOverall Skill Match: {match_percentage:.1f}%")

        # Generate learning recommendations
        recommendations = generate_learning_recommendations(skill_gap_info, top_n=5)
        print(f"\nTop 5 Skill Development Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            skill_name = rec['skill']
            user_level = decayed_user_data.get(skill_name, 0)  # Use decayed level for recommendation
            print(f"  {i}. {skill_name}: Increase from {user_level:.1f} to {rec['career_average']:.1f} "
                  f"(+{rec['gap']:.1f})")

    print("\n" + "="*60)
    print("Recommendation engine demonstration complete.")
    print("="*60)

if __name__ == "__main__":
    main()