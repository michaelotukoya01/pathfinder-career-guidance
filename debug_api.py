# debug_api.py
import json
import pandas as pd
from main import app, preprocess_input, UserInput
from pydantic import ValidationError

# Load the data
with open('preprocessing_info.json', 'r') as f:
    preprocessing_info = json.load(f)
original_features = preprocessing_info['original_features']

# Test data from test_api_fixed.py
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

print("Creating UserInput object...")
try:
    user_input = UserInput(**sample_data)
    print("Success! UserInput created.")
except ValidationError as e:
    print(f"Validation error: {e}")
    exit(1)

print("\nCalling preprocess_input...")
try:
    processed = preprocess_input(user_input)
    print(f"Success! Processed shape: {processed.shape}")
except Exception as e:
    print(f"Error in preprocess_input: {e}")
    import traceback
    traceback.print_exc()

    # Let's debug step by step
    print("\n--- Debugging ---")
    input_dict = user_input.model_dump()
    print(f"Input dict keys count: {len(input_dict)}")

    field_mapping = {
        'skill_data_analysis': 'skill data analysis',
        'skill_machine_learning': 'skill machine learning',
    }

    print(f"Field mapping: {field_mapping}")

    formatted_dict = {}
    for key, value in input_dict.items():
        original_key = field_mapping.get(key, key)
        formatted_dict[original_key] = value
        if key in field_mapping:
            print(f"  Mapped '{key}' -> '{original_key}'")

    print(f"Formatted dict keys count: {len(formatted_dict)}")

    missing = set(original_features) - set(formatted_dict.keys())
    extra = set(formatted_dict.keys()) - set(original_features)

    print(f"Missing keys: {missing}")
    print(f"Extra keys: {extra}")

    # Let's see what the actual original features are
    print(f"\nFirst 10 original features: {list(original_features)[:10]}")
    print(f"Last 10 original features: {list(original_features)[-10:]}")

    # Check specifically for the problematic ones
    print(f"\nDoes original_features contain 'skill data analysis'? {'skill data analysis' in original_features}")
    print(f"Does original_features contain 'skill machine learning'? {'skill machine learning' in original_features}")
    print(f"Does formatted_dict contain 'skill data analysis'? {'skill data analysis' in formatted_dict}")
    print(f"Does formatted_dict contain 'skill machine learning'? {'skill machine learning' in formatted_dict}")