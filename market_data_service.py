# market_data_service.py
"""
Mock service for job market data (salary, demand, growth projections).
In a production environment, this would integrate with APIs like BLS, Adzuna, LinkedIn, etc.
"""

import json
import random
from typing import Dict, Any

# Mock data for careers: maps career name to market data
# In a real app, this would be fetched from an external API
MOCK_MARKET_DATA = {
    "Data Scientist": {
        "median_salary": 120000,
        "salary_range": [95000, 150000],
        "job_growth_rate": 0.35,  # 35% growth projected
        "demand_score": 0.9,      # 0-1 scale
        "remote_friendly": 0.7,   # 0-1 scale
        "last_updated": "2024-01-15"
    },
    "Machine Learning Engineer": {
        "median_salary": 130000,
        "salary_range": [105000, 165000],
        "job_growth_rate": 0.40,
        "demand_score": 0.95,
        "remote_friendly": 0.8,
        "last_updated": "2024-01-15"
    },
    "Database Administrator": {
        "median_salary": 95000,
        "salary_range": [75000, 120000],
        "job_growth_rate": 0.08,
        "demand_score": 0.6,
        "remote_friendly": 0.4,
        "last_updated": "2024-01-15"
    },
    "Software Engineer": {
        "median_salary": 105000,
        "salary_range": [80000, 140000],
        "job_growth_rate": 0.22,
        "demand_score": 0.85,
        "remote_friendly": 0.75,
        "last_updated": "2024-01-15"
    },
    "Cybersecurity Analyst": {
        "median_salary": 90000,
        "salary_range": [70000, 115000],
        "job_growth_rate": 0.33,
        "demand_score": 0.88,
        "remote_friendly": 0.5,
        "last_updated": "2024-01-15"
    },
    "Product Manager": {
        "median_salary": 115000,
        "salary_range": [90000, 150000],
        "job_growth_rate": 0.10,
        "demand_score": 0.75,
        "remote_friendly": 0.6,
        "last_updated": "2024-01-15"
    },
    "UX/UI Designer": {
        "median_salary": 85000,
        "salary_range": [65000, 110000],
        "job_growth_rate": 0.13,
        "demand_score": 0.7,
        "remote_friendly": 0.65,
        "last_updated": "2024-01-15"
    },
    "Network Engineer": {
        "median_salary": 85000,
        "salary_range": [65000, 110000],
        "job_growth_rate": 0.05,
        "demand_score": 0.55,
        "remote_friendly": 0.3,
        "last_updated": "2024-01-15"
    },
    "IT Support Specialist": {
        "median_salary": 55000,
        "salary_range": [40000, 75000],
        "job_growth_rate": 0.08,
        "demand_score": 0.6,
        "remote_friendly": 0.4,
        "last_updated": "2024-01-15"
    }
}

def get_market_data(career: str) -> Dict[str, Any]:
    """
    Get market data for a given career.
    Returns default data if career not found.
    """
    # Normalize the career name for lookup (title case)
    aliases = {"ui/ux designer": "ux/ui designer"}
    lookup = aliases.get(career.casefold(), career.casefold())
    career_title = next((name for name in MOCK_MARKET_DATA if name.casefold() == lookup), career)

    # Return mock data if available, else return default
    if career_title in MOCK_MARKET_DATA:
        return MOCK_MARKET_DATA[career_title]
    else:
        # Return default/mock data for unknown careers
        return {
            "median_salary": 75000,
            "salary_range": [50000, 100000],
            "job_growth_rate": 0.10,
            "demand_score": 0.5,
            "remote_friendly": 0.5,
            "last_updated": "2024-01-15"
        }

def get_market_data_for_multiple_careers(careers: list) -> dict:
    """
    Get market data for multiple careers.
    """
    return {career: get_market_data(career) for career in careers}

# For testing
if __name__ == "__main__":
    print(get_market_data("Data Scientist"))
    print(get_market_data("Unknown Career"))