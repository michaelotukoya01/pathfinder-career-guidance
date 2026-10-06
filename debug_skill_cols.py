# debug_skill_cols.py
import pandas as pd
import json

# Load original data
df = pd.read_csv('synthetic_career_data.csv')
feature_cols = [col for col in df.columns if col not in ['user_id', 'recommended_career', 'top_3_careers']]
X = df[feature_cols]
y = df['recommended_career']

print("All feature columns:", len(feature_cols))
print("First 10:", feature_cols[:10])

# Identify skill columns as we do in the code
skill_cols = [col for col in X.columns if col.startswith('skill_') and col != 'skill_gaps']
print("\nSkill columns (raw):", len(skill_cols))
print(skill_cols)

# Check dtypes
print("\nData types of skill columns:")
for col in skill_cols:
    print(f"{col}: {X[col].dtype}")

# Ensure numeric
skill_cols_numeric = [col for col in skill_cols if pd.api.types.is_numeric_dtype(X[col])]
print("\nNumeric skill columns:", len(skill_cols_numeric))
print(skill_cols_numeric)

# Now compute career skill profiles
skill_data = X[skill_cols_numeric]
df_skills = skill_data.copy()
df_skills['career'] = y.values

career_skill_profiles = {}
for career in df_skills['career'].unique():
    career_data = df_skills[df_skills['career'] == career]
    avg_skills = career_data[skill_cols_numeric].mean().values
    career_skill_profiles[career] = avg_skills

print("\nCareer skill profiles keys:", list(career_skill_profiles.keys()))
print("Example career 'Database Administrator' skill avg shape:", career_skill_profiles['Database Administrator'].shape)
print("Values:", career_skill_profiles['Database Administrator'])

# Now check what happens when we subtract
import numpy as np
user_skills_example = np.array([4, 3, 2, 2, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3])  # 14 skills
print("\nUser skills shape:", user_skills_example.shape)
print("Career avg skills shape:", career_skill_profiles['Database Administrator'].shape)
try:
    diff = career_skill_profiles['Database Administrator'] - user_skills_example
    print("Subtraction succeeded, diff shape:", diff.shape)
except Exception as e:
    print("Subtraction failed:", e)
    print("Career avg dtype:", career_skill_profiles['Database Administrator'].dtype)
    print("User skills dtype:", user_skills_example.dtype)