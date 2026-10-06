# test_api_fixed.py
# Test the FastAPI application using TestClient

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    print("Root endpoint test passed")

def test_recommend():
    # Sample input data (matching the expected format)
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

    response = client.post("/recommend", json=sample_data)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
    json_data = response.json()
    assert "recommended_career" in json_data
    assert "top_3_predictions" in json_data
    assert "skill_gap_analysis" in json_data
    print("Recommendation endpoint test passed")

if __name__ == "__main__":
    test_root()
    test_recommend()
    print("All tests passed!")