# debug_sets.py
import json
import pandas as pd
from main import UserInput

with open('preprocessing_info.json', 'r') as f:
    preprocessing_info = json.load(f)
original_features = set(preprocessing_info['original_features'])
print("Number of original features:", len(original_features))
print("First 5 original features:", list(original_features)[:5])

# Sample input data
sample_data = {
    "age_range": "21-23",
    "education_level": "Bachelor's",
    "field_of_study": "Computer Science",
    "year_of_study": "Senior Year",
    "confidence_score": 0.85,
    "academic_mathematics": 3,
    "academic_statistics": 3,
    "academic_programming": 4,
    "academic_computer_networking": 3,
    "academic_database_management": 3,
    "academic_web_development": 3,
    "skill_python": 4,
    "skill_javascript": 3,
    "skill_java": 2,
    "skill_c_cplusplus": 2,
    "skill_sql": 3,
    "skill_html_css": 3,
    "skill_react": 2,
    "skill_networking": 3,
    "skill_linux": 3,
    "skill_databases": 3,
    "skill_cloud": 2,
    "skill_cybersecurity": 2,
    "skill_data_analysis": 3,
    "skill_machine_learning": 3,
    "interest_building_applications": 4,
    "interest_analyzing_data": 3,
    "interest_artificial_intelligence": 4,
    "interest_cybersecurity": 2,
    "interest_networking": 3,
    "interest_cloud_computing": 2,
    "interest_databases": 3,
    "interest_ui_ux_design": 2,
    "interest_research": 3,
    "workpref_building_things": 4,
    "workpref_analyzing_information": 3,
    "workpref_solving_security_problems": 2,
    "workpref_working_with_numbers": 3,
    "workpref_designing_ui": 2,
    "workpref_investigating_problems": 3,
    "personality_analytical": 4,
    "personality_creative": 2,
    "personality_problem_solver": 4,
    "personality_detail_oriented": 3,
    "personality_collaborative": 3,
    "personality_independent_worker": 3,
    "skill_gaps": "{'Python': 0, 'Statistics': 4, 'Machine Learning': 0, 'Data Analysis': 0}"
}

# Simulate the mapping inside preprocess_input (without the DataFrame creation)
field_mapping = {
    'skill_data_analysis': 'skill data analysis',
    'skill_machine_learning': 'skill machine learning',
}
formatted_dict = {}
for key, value in sample_data.items():
    original_key = field_mapping.get(key, key)
    formatted_dict[original_key] = value
    # Debug print for the two special keys
    if key in field_mapping:
        print(f"Mapping: {key} -> {original_key}")

print("\nNumber of formatted_dict keys:", len(formatted_dict))
print("Formatted dict keys (first 10):", list(formatted_dict.keys())[:10])

missing = original_features - set(formatted_dict.keys())
extra = set(formatted_dict.keys()) - original_features

print("\nMissing keys (in original_features but not in formatted_dict):", len(missing))
if missing:
    print("List of missing keys:")
    for m in sorted(missing):
        print(f"  {repr(m)}")

print("\nExtra keys (in formatted_dict but not in original_features):", len(extra))
if extra:
    print("List of extra keys:")
    for e in sorted(extra):
        print(f"  {repr(e)}")

# Now let's also check what the original_features actually contains for the two problematic ones
print("\nChecking specific strings:")
target1 = 'skill data analysis'
target2 = 'skill machine learning'
print(f"Target1: {repr(target1)}")
print(f"Target2: {repr(target2)}")
print(f"Target1 in original_features? {target1 in original_features}")
print(f"Target2 in original_features? {target2 in original_features}")
print(f"Target1 in formatted_dict? {target1 in formatted_dict}")
print(f"Target2 in formatted_dict? {target2 in formatted_dict}")