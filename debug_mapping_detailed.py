# debug_mapping_detailed.py
import json
from pydantic import BaseModel, Field
import pandas as pd

# Define the UserInput model exactly as in main.py
class UserInput(BaseModel):
    age_range: str = Field(..., example="21-23")
    education_level: str = Field(..., example="Bachelor's")
    field_of_study: str = Field(..., example="Computer Science")
    year_of_study: str = Field(..., example="Senior Year")
    confidence_score: float = Field(..., ge=0.0, le=1.0, example=0.85)
    academic_mathematics: int = Field(..., ge=1, le=5, example=3)
    academic_statistics: int = Field(..., ge=1, le=5, example=3)
    academic_programming: int = Field(..., ge=1, le=5, example=3)
    academic_computer_networking: int = Field(..., ge=1, le=5, example=3)
    academic_database_management: int = Field(..., ge=1, le=5, example=3)
    academic_web_development: int = Field(..., ge=1, le=5, example=3)
    skill_python: int = Field(..., ge=0, le=5, example=3)
    skill_javascript: int = Field(..., ge=0, le=5, example=3)
    skill_java: int = Field(..., ge=0, le=5, example=3)
    skill_c_cplusplus: int = Field(..., ge=0, le=5, example=3)
    skill_sql: int = Field(..., ge=0, le=5, example=3)
    skill_html_css: int = Field(..., ge=0, le=5, example=3)
    skill_react: int = Field(..., ge=0, le=5, example=3)
    skill_networking: int = Field(..., ge=0, le=5, example=3)
    skill_linux: int = Field(..., ge=0, le=5, example=3)
    skill_databases: int = Field(..., ge=0, le=5, example=3)
    skill_cloud: int = Field(..., ge=0, le=5, example=3)
    skill_cybersecurity: int = Field(..., ge=0, le=5, example=3)
    skill_data_analysis: int = Field(..., ge=0, le=5, example=3)
    skill_machine_learning: int = Field(..., ge=0, le=5, example=3)
    interest_building_applications: int = Field(..., ge=1, le=5, example=3)
    interest_analyzing_data: int = Field(..., ge=1, le=5, example=3)
    interest_artificial_intelligence: int = Field(..., ge=1, le=5, example=3)
    interest_cybersecurity: int = Field(..., ge=1, le=5, example=3)
    interest_networking: int = Field(..., ge=1, le=5, example=3)
    interest_cloud_computing: int = Field(..., ge=1, le=5, example=3)
    interest_databases: int = Field(..., ge=1, le=5, example=3)
    interest_ui_ux_design: int = Field(..., ge=1, le=5, example=3)
    interest_research: int = Field(..., ge=1, le=5, example=3)
    workpref_building_things: int = Field(..., ge=1, le=5, example=3)
    workpref_analyzing_information: int = Field(..., ge=1, le=5, example=3)
    workpref_solving_security_problems: int = Field(..., ge=1, le=5, example=3)
    workpref_working_with_numbers: int = Field(..., ge=1, le=5, example=3)
    workpref_designing_ui: int = Field(..., ge=1, le=5, example=3)
    workpref_investigating_problems: int = Field(..., ge=1, le=5, example=3)
    personality_analytical: int = Field(..., ge=1, le=5, example=3)
    personality_creative: int = Field(..., ge=1, le=5, example=3)
    personality_problem_solver: int = Field(..., ge=1, le=5, example=3)
    personality_detail_oriented: int = Field(..., ge=1, le=5, example=3)
    personality_collaborative: int = Field(..., ge=1, le=5, example=3)
    personality_independent_worker: int = Field(..., ge=1, le=5, example=3)
    skill_gaps: str = Field(..., example="{'Python': 0, 'Statistics': 4, 'Machine Learning': 0, 'Data Analysis': 0}")

    class Config:
        validate_by_name = True

# Load preprocessing info to get original_features
with open('preprocessing_info.json', 'r') as f:
    preprocessing_info = json.load(f)
original_features = preprocessing_info['original_features']

print("=== DEBUGGING MAPPING ===")
print(f"Number of original features: {len(original_features)}")

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

print("\n1. Creating UserInput object...")
user_input = UserInput(**sample_data)
print("   Success!")

print("\n2. Converting to dict using model_dump()...")
input_dict = user_input.model_dump()
print(f"   Dict has {len(input_dict)} keys")

print("\n3. Checking for specific keys in input_dict:")
print(f"   'skill_data_analysis' in input_dict: {'skill_data_analysis' in input_dict}")
print(f"   'skill_machine_learning' in input_dict: {'skill_machine_learning' in input_dict}")
if 'skill_data_analysis' in input_dict:
    print(f"   Value: {input_dict['skill_data_analysis']}")
if 'skill_machine_learning' in input_dict:
    print(f"   Value: {input_dict['skill_machine_learning']}")

print("\n4. Defining field mapping:")
field_mapping = {
    'skill_data_analysis': 'skill data analysis',
    'skill_machine_learning': 'skill machine learning',
}
print(f"   Mapping: {field_mapping}")

print("\n5. Applying mapping to create formatted_dict...")
formatted_dict = {}
for key, value in input_dict.items():
    original_key = field_mapping.get(key, key)
    formatted_dict[original_key] = value
    if key in field_mapping:
        print(f"   Mapped '{key}' -> '{original_key}'")

print(f"\n6. Formatted dict has {len(formatted_dict)} keys")

print("\n7. Checking for mapped keys in formatted_dict:")
mapped_key1 = 'skill data analysis'
mapped_key2 = 'skill machine learning'
print(f"   '{mapped_key1}' in formatted_dict: {mapped_key1 in formatted_dict}")
print(f"   '{mapped_key2}' in formatted_dict: {mapped_key2 in formatted_dict}")

if mapped_key1 in formatted_dict:
    print(f"   Value of '{mapped_key1}': {formatted_dict[mapped_key1]}")
if mapped_key2 in formatted_dict:
    print(f"   Value of '{mapped_key2}': {formatted_dict[mapped_key2]}")

print("\n8. Checking original_features for these keys:")
print(f"   '{mapped_key1}' in original_features: {mapped_key1 in original_features}")
print(f"   '{mapped_key2}' in original_features: {mapped_key2 in original_features}")

print("\n9. Computing missing and extra keys:")
formatted_keys_set = set(formatted_dict.keys())
original_features_set = set(original_features)

missing = original_features_set - formatted_keys_set
extra = formatted_keys_set - original_features_set

print(f"   Number of missing keys: {len(missing)}")
if missing:
    print("   Missing keys:")
    for key in sorted(missing):
        print(f"     {repr(key)}")

print(f"   Number of extra keys: {len(extra)}")
if extra:
    print("   Extra keys:")
    for key in sorted(extra):
        print(f"     {repr(key)}")

print("\n10. Let's also check what the actual values are for the two problematic mappings:")
print(f"    original_features[23] = {repr(original_features[23])}")
print(f"    original_features[24] = {repr(original_features[24])}")

print("\n11. Checking if our mapped values match exactly:")
print(f"    'skill data analysis' == original_features[23]: {'skill data analysis' == original_features[23]}")
print(f"    'skill machine learning' == original_features[24]: {'skill machine learning' == original_features[24]}")

print("\n=== END DEBUG ===")