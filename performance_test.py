#!/usr/bin/env python3
"""
Performance test for the AI Career Recommendation & Guidance System.
Measures response times for various endpoints.
"""

import json
import time
import statistics
import requests
import sys

BASE_URL = "http://localhost:8000"

def time_request(method, endpoint, json_data=None, params=None):
    """Time a single request and return the response time in seconds."""
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        end_time = time.time()
        response_time = end_time - start_time

        return response_time, response.status_code
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Error during {method} {endpoint}: {e}")
        return response_time, None

def test_health_endpoint():
    """Test the health endpoint response time."""
    print("Testing health endpoint...")
    times = []
    for i in range(10):
        response_time, status_code = time_request("GET", "/health")
        if status_code == 200:
            times.append(response_time)
        else:
            print(f"  Request {i+1} failed with status {status_code}")

    if times:
        avg_time = statistics.mean(times) * 1000  # Convert to milliseconds
        min_time = min(times) * 1000
        max_time = max(times) * 1000
        print(f"  Health endpoint: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        return avg_time
    else:
        print("  Health endpoint: All requests failed")
        return None

def test_profile_creation():
    """Test profile creation response time."""
    print("Testing profile creation...")
    times = []
    for i in range(10):
        payload = {
            "name": f"Perf Test User {i}",
            "email": f"perftest{i}@example.com",
            "age_range": "21-23",
            "education_level": "Bachelor's",
            "field_of_study": "Computer Science",
            "year_of_study": "Senior Year",
            "confidence_score": 0.85
        }
        response_time, status_code = time_request("POST", "/profiles", json_data=payload)
        if status_code == 200:
            times.append(response_time)
        else:
            print(f"  Request {i+1} failed with status {status_code}")

    if times:
        avg_time = statistics.mean(times) * 1000
        min_time = min(times) * 1000
        max_time = max(times) * 1000
        print(f"  Profile creation: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        return avg_time
    else:
        print("  Profile creation: All requests failed")
        return None

def test_recommendation():
    """Test recommendation endpoint response time."""
    print("Testing recommendation endpoint...")
    times = []
    for i in range(10):
        payload = {
            "age_range": "21-23",
            "education_level": "Bachelor's",
            "field_of_study": "Computer Science",
            "year_of_study": "Senior Year",
            "confidence_score": 0.85,
            "academic_mathematics": 4,
            "academic_statistics": 3,
            "academic_programming": 5,
            "academic_computer_networking": 4,
            "academic_database_management": 3,
            "academic_web_development": 4,
            "skill_python": 5,
            "skill_javascript": 4,
            "skill_java": 3,
            "skill_c_cplusplus": 2,
            "skill_sql": 4,
            "skill_html_css": 4,
            "skill_react": 3,
            "skill_networking": 3,
            "skill_linux": 3,
            "skill_databases": 4,
            "skill_cloud": 2,
            "skill_cybersecurity": 2,
            "skill_data_analysis": 4,
            "skill_machine_learning": 2,
            "interest_building_applications": 4,
            "interest_analyzing_data": 3,
            "interest_artificial_intelligence": 5,
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
            "skill_gaps": "{'Python': 0, 'Statistics': 1, 'Machine Learning': 0, 'Data Analysis': 0}"
        }
        response_time, status_code = time_request("POST", "/recommend", json_data=payload)
        if status_code == 200:
            times.append(response_time)
        else:
            print(f"  Request {i+1} failed with status {status_code}")

    if times:
        avg_time = statistics.mean(times) * 1000
        min_time = min(times) * 1000
        max_time = max(times) * 1000
        print(f"  Recommendation: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        return avg_time
    else:
        print("  Recommendation: All requests failed")
        return None

def main():
    """Run all performance tests."""
    print("Starting performance tests...\n")

    # Test various endpoints
    health_time = test_health_endpoint()
    print()

    profile_time = test_profile_creation()
    print()

    recommend_time = test_recommendation()
    print()

    # Summary
    print("Performance Test Summary:")
    print("=" * 40)
    if health_time is not None:
        print(f"Health Check:     {health_time:.2f} ms")
    if profile_time is not None:
        print(f"Profile Creation: {profile_time:.2f} ms")
    if recommend_time is not None:
        print(f"Recommendation:   {recommend_time:.2f} ms")

    # Check if performance meets requirements (< 2000ms for API calls as mentioned in success criteria)
    print("\nPerformance Rating:")
    if recommend_time is not None and recommend_time < 2000:
        print("✓ Response times are within acceptable limits (< 2000ms)")
    elif recommend_time is not None:
        print("! Response times exceed acceptable limits (> 2000ms)")
    else:
        print("✗ Could not measure response times")

    return 0 if all(t is not None for t in [health_time, profile_time, recommend_time]) else 1

if __name__ == "__main__":
    sys.exit(main())