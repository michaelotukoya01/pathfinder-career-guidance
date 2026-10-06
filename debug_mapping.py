# debug_mapping.py
import json
import pandas as pd
from main import preprocess_input, UserInput

# Load preprocessing info to get original_features
with open('preprocessing_info.json', 'r') as f:
    preprocessing_info = json.load(f)
original_features = preprocessing_info['original_features']

print("Original features (first few):", original_features[:5])
print("Total original features:", len(original_features))

# Sample input data (same as in test)
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

print("\nInput data keys (first 10):", list(sample_data.keys())[:10])

# Create UserInput object
user_input = UserInput(**sample_data)
print("\nUserInput created successfully")

# Convert to dict
input_dict = user_input.dict()
print("Input dict keys (first 10):", list(input_dict.keys())[:10])

# Apply field mapping
field_mapping = {
    'skill_data_analysis': 'skill data analysis',
    'skill_machine_learning': 'skill machine learning',
}

print("\nField mapping:", field_mapping)

# Create formatted_dict as in preprocess_input
formatted_dict = {}
for key, value in input_dict.items():
    original_key = field_mapping.get(key, key)
    formatted_dict[original_key] = value
    if key in field_mapping:
        print(f"Mapped '{key}' -> '{original_key}'")

print("\nFormatted dict keys (first 10):", list(formatted_dict.keys())[:10])
print("Formatted dict keys (last 10):", list(formatted_dict.keys())[-10:])

# Check if the problematic keys are present
print("\nDoes formatted_dict contain 'skill data analysis'? ", 'skill data analysis' in formatted_dict)
print("Does formatted_dict contain 'skill machine learning'? ", 'skill machine learning' in formatted_dict)

# Check missing
missing = set(original_features) - set(formatted_dict.keys())
print("\nMissing features:", missing)
if missing:
    print("First few missing:", list(missing)[:5])

# Let's also check if there are any extra keys in formatted_dict not in original_features
extra = set(formatted_dict.keys()) - set(original_features)
print("Extra features:", extra)

# Now let's see what the preprocess_input function does by calling it
print("\n--- Calling preprocess_input ---")
try:
    processed = preprocess_input(user_input)
    print("Preprocessing succeeded, shape:", processed.shape)
except Exception as e:
    print("Preprocessing failed:", e)