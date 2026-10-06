# main.py - Enhanced with security measures and skill decay modeling
# FastAPI backend for AI Career Recommendation System with security enhancements

import json
import pickle
import os
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
from typing import Dict, Any, List, Tuple, Optional
import uuid
import hashlib
import secrets
from datetime import datetime
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Request, status, BackgroundTasks, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import re
from collections import defaultdict, deque

# Import security utilities
from security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    sanitize_input,
    SecurityValidator,
    mask_pii
)
from security import RequestBodyLimitMiddleware

# Import skill decay utilities
from skill_decay_utils import SkillDecayModel, apply_skill_decay, get_skill_decay_info

# Import profile store
from profile_store import profile_store

# Import market data service
from market_data_service import get_market_data_for_multiple_careers, get_market_data

# Import career path engine
from career_path_engine import CareerPathEngine, build_career_path_engine_from_dataframe

# Optional: Anthropic LLM integration
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. LLM explanations will be disabled.")
    anthropic_client = None
else:
    # Initialize Anthropic client if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        anthropic_client = anthropic.Anthropic(api_key=api_key)
        print("Anthropic client initialized successfully")
    else:
        anthropic_client = None
        print("Warning: ANTHROPIC_API_KEY not found in environment variables. LLM explanations disabled.")

# Import model retraining functions
from model_retraining import (
    start_retraining_scheduler,
    stop_retraining_scheduler,
    check_and_retrain,
    get_model_versions,
    promote_model_version as promote_stored_model_version,
    model_retrainer
)

# Load the trained model and preprocessing artifacts
print("Loading model and preprocessing artifacts...")
model = joblib.load(BASE_DIR / 'best_model.pkl')  # Logistic Regression model
preprocessor = joblib.load(BASE_DIR / 'preprocessor.pkl')  # Fitted preprocessing pipeline
label_encoder = joblib.load(BASE_DIR / 'label_encoder.pkl')  # Label encoder for target

# Initialize skill decay model
decay_model = SkillDecayModel()

# Load feature names and original features info
with open(BASE_DIR / 'preprocessing_info.json', 'r') as f:
    preprocessing_info = json.load(f)

original_features = preprocessing_info['original_features']  # 50 features
numeric_features = preprocessing_info['numeric_features']
categorical_features = preprocessing_info['categorical_features']
target_classes = preprocessing_info['target_classes']

print(f"Loaded model: {type(model).__name__}")
print(f"Number of classes: {len(target_classes)}")
print(f"Original features count: {len(original_features)}")
print(f"Skill decay model initialized with {len(decay_model.decay_rates)} decay rates")

# Helper to get skill column names (as in original_features) excluding skill_gaps
def get_skill_column_names():
    """Return list of skill feature names (as they appear in original_features) excluding skill_gaps."""
    return [f for f in original_features if f.startswith('skill_') and f != 'skill_gaps']

# Define the input data model based on original features with validation
class UserInput(BaseModel):
    # Basic Information
    age_range: str = Field(..., examples=["21-23"])
    education_level: str = Field(..., examples=["Bachelor's"])
    field_of_study: str = Field(..., examples=["Computer Science"])
    year_of_study: str = Field(..., examples=["Senior Year"])

    # Academic Information (1-5 scale)
    confidence_score: float = Field(..., ge=0.0, le=1.0, examples=[0.85])
    academic_mathematics: int = Field(..., ge=1, le=5, examples=[3])
    academic_statistics: int = Field(..., ge=1, le=5, examples=[3])
    academic_programming: int = Field(..., ge=1, le=5, examples=[3])
    academic_computer_networking: int = Field(..., ge=1, le=5, examples=[3])
    academic_database_management: int = Field(..., ge=1, le=5, examples=[3])
    academic_web_development: int = Field(..., ge=1, le=5, examples=[3])

    # Technical Skills (Experience Level: 0-5)
    skill_python: float = Field(..., ge=0, le=5, examples=[3])
    skill_javascript: float = Field(..., ge=0, le=5, examples=[3])
    skill_java: float = Field(..., ge=0, le=5, examples=[3])
    skill_c_cplusplus: float = Field(..., ge=0, le=5, examples=[3])
    skill_sql: float = Field(..., ge=0, le=5, examples=[3])
    skill_html_css: float = Field(..., ge=0, le=5, examples=[3])
    skill_react: float = Field(..., ge=0, le=5, examples=[3])
    skill_networking: float = Field(..., ge=0, le=5, examples=[3])
    skill_linux: float = Field(..., ge=0, le=5, examples=[3])
    skill_databases: float = Field(..., ge=0, le=5, examples=[3])
    skill_cloud: float = Field(..., ge=0, le=5, examples=[3])
    skill_cybersecurity: float = Field(..., ge=0, le=5, examples=[3])
    skill_data_analysis: float = Field(..., ge=0, le=5, examples=[3])  # Note: underscore instead of space
    skill_machine_learning: float = Field(..., ge=0, le=5, examples=[3])  # Note: underscore instead of space

    # Interests (1-5 scale)
    interest_building_applications: int = Field(..., ge=1, le=5, examples=[3])
    interest_analyzing_data: int = Field(..., ge=1, le=5, examples=[3])
    interest_artificial_intelligence: int = Field(..., ge=1, le=5, examples=[3])
    interest_cybersecurity: int = Field(..., ge=1, le=5, examples=[3])
    interest_networking: int = Field(..., ge=1, le=5, examples=[3])
    interest_cloud_computing: int = Field(..., ge=1, le=5, examples=[3])
    interest_databases: int = Field(..., ge=0, le=5, examples=[3])
    interest_ui_ux_design: int = Field(..., ge=1, le=5, examples=[3])
    interest_research: int = Field(..., ge=1, le=5, examples=[3])

    # Work Preferences (1-5 scale)
    workpref_building_things: int = Field(..., ge=1, le=5, examples=[3])
    workpref_analyzing_information: int = Field(..., ge=1, le=5, examples=[3])
    workpref_solving_security_problems: int = Field(..., ge=1, le=5, examples=[3])
    workpref_working_with_numbers: int = Field(..., ge=1, le=5, examples=[3])
    workpref_designing_ui: int = Field(..., ge=1, le=5, examples=[3])
    workpref_investigating_problems: int = Field(..., ge=1, le=5, examples=[3])

    # Personality/Psychometric Dimensions (1-5 scale)
    personality_analytical: int = Field(..., ge=1, le=5, examples=[3])
    personality_creative: int = Field(..., ge=1, le=5, examples=[3])
    personality_problem_solver: int = Field(..., ge=1, le=5, examples=[3])
    personality_detail_oriented: int = Field(..., ge=1, le=5, examples=[3])
    personality_collaborative: int = Field(..., ge=1, le=5, examples=[3])
    personality_independent_worker: int = Field(..., ge=1, le=5, examples=[3])

    # Skill gaps (string representation of dictionary)
    skill_gaps: str = Field('{}', examples=["{'Python': 0, 'Statistics': 4, 'Machine Learning': 0, 'Data Analysis': 0}"])

    model_config = ConfigDict(extra="allow", json_schema_extra={
            "example": {
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
        })

    # Custom validators for additional security
    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('age_range', 'education_level', 'field_of_study', 'year_of_study', mode='before')
    @classmethod
    def validate_text_fields(cls, v):
        if isinstance(v, str):
            return sanitize_input(v, 100)
        return v

@asynccontextmanager
async def lifespan(app):
    reload_active_model()
    if os.getenv("ENABLE_RETRAINING_SCHEDULER", "false").lower() == "true":
        start_retraining_scheduler()
    try:
        yield
    finally:
        stop_retraining_scheduler()


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Pathfinder Career Guidance API",
    description="API for recommending technology careers based on user skills, interests, and academic background with security protections and skill decay modeling",
    version="1.0.0"
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(RateLimitMiddleware, calls=30, period=60)  # 30 requests per minute per IP

# Enhanced middleware for request/response logging and monitoring
class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging for requests and responses"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code

            # Calculate processing time
            process_time = time.time() - start_time

            # Log request details
            print(f"{client_ip} - {method} {url} - {status_code} - {process_time:.3f}s")

            # Add response headers for tracing
            response.headers["X-Process-Time"] = str(process_time)

            return response
        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log exception
            print(f"{client_ip} - {method} {url} - FAILED - {process_time:.3f}s - {str(exc)}")

            # Re-raise the exception to be handled by exception handlers
            raise exc

app.add_middleware(EnhancedLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",") if origin.strip()],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Global exception handlers for consistent error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent JSON format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": getattr(exc, 'error_code', f"HTTP_{exc.status_code}"),
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed feedback"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": jsonable_encoder(exc.errors(), custom_encoder={ValueError: str}),
            "error_code": "VALIDATION_ERROR",
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    # Log the full error for debugging (in production, use proper logging)
    print(f"Unhandled exception: {str(exc)}")
    import traceback
    print(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

def _to_original_feature_dict(user_input: UserInput) -> dict:
    """Convert UserInput to a dictionary with original feature names (with spaces where needed)."""
    input_dict = user_input.model_dump()
    field_mapping = {
        'skill_data_analysis': 'skill_data analysis',
        'skill_machine_learning': 'skill_machine learning',
    }
    formatted_dict = {}
    for key, value in input_dict.items():
        original_key = field_mapping.get(key, key)
        formatted_dict[original_key] = value
    return formatted_dict

def preprocess_input(user_input: UserInput) -> np.ndarray:
    """
    Convert UserInput object to a numpy array in the format expected by the preprocessor.
    """
    # Get dictionary with original feature names
    formatted_dict = _to_original_feature_dict(user_input)

    # Ensure we have all original features (should be 50)
    missing = set(original_features) - set(formatted_dict.keys())
    if missing:
        raise ValueError(f"Missing features: {missing}")

    # Create DataFrame with columns in the same order as original_features
    input_df = pd.DataFrame([formatted_dict], columns=original_features)

    # Apply the preprocessor
    processed = preprocessor.transform(input_df)

    return processed

# Mock market data is opt-in and excluded from the default recommendation.
MARKET_WEIGHT = float(os.getenv("MARKET_WEIGHT", "0"))
if not 0 <= MARKET_WEIGHT <= 1:
    raise ValueError("MARKET_WEIGHT must be between 0 and 1")

def get_market_adjusted_predictions(processed_input: np.ndarray) -> tuple[str, list[tuple[str, float]]]:
    """
    Predict career and return top 3 predictions with probabilities adjusted by market data.
    """
    # Get predicted class from raw ML model
    pred_encoded = model.predict(processed_input)
    pred_career = label_encoder.inverse_transform(pred_encoded)[0]

    # Get probabilities from ML model
    probabilities = model.predict_proba(processed_input)[0]
    # Get top 5 indices to have more options for market adjustment
    top_n = 5
    top_n_indices = np.argsort(probabilities)[::-1][:top_n]
    top_n_careers = label_encoder.inverse_transform(top_n_indices)
    top_n_probabilities = probabilities[top_n_indices]

    # Create list of (career, ml_probability) tuples
    ml_predictions = list(zip(top_n_careers, top_n_probabilities))

    # Adjust predictions with market data
    adjusted_predictions = adjust_predictions_with_market(ml_predictions, MARKET_WEIGHT)

    # Return top 3 after adjustment
    top_3_adjusted = adjusted_predictions[:3]

    return top_3_adjusted[0][0], top_3_adjusted


def adjust_predictions_with_market(predictions: list[tuple[str, float]], market_weight: float) -> list[tuple[str, float]]:
    """
    Adjust ML predictions with market data scores.

    Args:
        predictions: List of (career, ml_probability) tuples
        market_weight: Weight to give market factors (0-1)

    Returns:
        Adjusted list of (career, adjusted_probability) tuples sorted by adjusted probability
    """
    if not predictions:
        return predictions

    # Get market data for all predicted careers
    careers = [career for career, _ in predictions]
    market_data = get_market_data_for_multiple_careers(careers)

    # Calculate market scores for each career (normalized 0-1)
    market_scores = {}
    for career in careers:
        data = market_data.get(career, {
            "median_salary": 50000,
            "job_growth_rate": 0.05,
            "demand_score": 0.5
        })

        # Normalize factors to 0-1 scale
        # Salary: normalize against reasonable range (40k-200k)
        salary_score = min(1.0, max(0.0, (data["median_salary"] - 40000) / 160000))
        # Growth: normalize against reasonable range (0%-50%)
        growth_score = min(1.0, max(0.0, data["job_growth_rate"] / 0.5))
        # Demand: already 0-1 scale
        demand_score = data["demand_score"]

        # Weighted combination of market factors
        market_score = (0.4 * salary_score + 0.3 * growth_score + 0.3 * demand_score)
        market_scores[career] = market_score

    # Normalize market scores to sum to 1.0 for weighting
    total_market_score = sum(market_scores.values())
    if total_market_score > 0:
        normalized_market_scores = {k: v/total_market_score for k, v in market_scores.items()}
    else:
        normalized_market_scores = {k: 1.0/len(market_scores) for k in market_scores.keys()}

    # Combine ML predictions with market scores
    adjusted_predictions = []
    for career, ml_prob in predictions:
        market_score = normalized_market_scores.get(career, 0.0)
        # Blend ML probability with market score
        adjusted_prob = (1 - market_weight) * ml_prob + market_weight * market_score
        adjusted_predictions.append((career, adjusted_prob))

    # Renormalize to ensure probabilities sum to 1.0
    total_prob = sum(prob for _, prob in adjusted_predictions)
    if total_prob > 0:
        adjusted_predictions = [(career, prob/total_prob) for career, prob in adjusted_predictions]

    # Sort by adjusted probability (descending)
    adjusted_predictions.sort(key=lambda x: x[1], reverse=True)

    return adjusted_predictions


def predict_career(processed_input: np.ndarray) -> tuple[str, list[tuple[str, float]]]:
    """
    Predict career and return top 3 predictions with probabilities.
    Maintained for backward compatibility.
    """
    # Get predicted class
    pred_encoded = model.predict(processed_input)
    pred_career = label_encoder.inverse_transform(pred_encoded)[0]

    # Get probabilities
    probabilities = model.predict_proba(processed_input)[0]
    # Get top 3 indices
    top_3_indices = np.argsort(probabilities)[::-1][:3]
    top_3_careers = label_encoder.inverse_transform(top_3_indices)
    top_3_probabilities = probabilities[top_3_indices]

    top_3 = list(zip(top_3_careers, top_3_probabilities))

    return pred_career, top_3


def adjust_predictions_with_market_data(predictions: list[tuple[str, float]], market_weight: float = 0.3) -> list[tuple[str, float]]:
    """
    Adjust career predictions based on market data (demand, salary, growth).

    Args:
        predictions: List of (career, probability) tuples from ML model
        market_weight: Weight to give market factors (0-1). ML weight is (1-market_weight)

    Returns:
        Adjusted list of (career, adjusted_probability) tuples
    """
    if not predictions:
        return predictions

    # Get market data for all predicted careers
    careers = [career for career, _ in predictions]
    market_data = get_market_data_for_multiple_careers(careers)

    # Calculate market scores for each career
    market_scores = {}
    for career in careers:
        data = market_data.get(career, {
            "median_salary": 50000,
            "job_growth_rate": 0.05,
            "demand_score": 0.5
        })

        # Normalize factors to 0-1 scale
        # Salary: normalize against reasonable range (40k-200k)
        salary_score = min(1.0, max(0.0, (data["median_salary"] - 40000) / 160000))
        # Growth: normalize against reasonable range (0%-50%)
        growth_score = min(1.0, max(0.0, data["job_growth_rate"] / 0.5))
        # Demand: already 0-1 scale
        demand_score = data["demand_score"]

        # Weighted combination of market factors
        market_score = (0.4 * salary_score + 0.3 * growth_score + 0.3 * demand_score)
        market_scores[career] = market_score

    # Normalize market scores to sum to 1.0 for weighting
    total_market_score = sum(market_scores.values())
    if total_market_score > 0:
        normalized_market_scores = {k: v/total_market_score for k, v in market_scores.items()}
    else:
        normalized_market_scores = {k: 1.0/len(market_scores) for k in market_scores.keys()}

    # Combine ML predictions with market scores
    adjusted_predictions = []
    for career, ml_prob in predictions:
        market_score = normalized_market_scores.get(career, 0.0)
        # Blend ML probability with market score
        adjusted_prob = (1 - market_weight) * ml_prob + market_weight * market_score
        adjusted_predictions.append((career, adjusted_prob))

    # Renormalize to ensure probabilities sum to 1.0
    total_prob = sum(prob for _, prob in adjusted_predictions)
    if total_prob > 0:
        adjusted_predictions = [(career, prob/total_prob) for career, prob in adjusted_predictions]

    # Sort by adjusted probability (descending)
    adjusted_predictions.sort(key=lambda x: x[1], reverse=True)

    return adjusted_predictions

def extract_skill_vector(user_input: UserInput) -> np.ndarray:
    """
    Extract the skill vector (only skill features) from user input.
    Excludes skill_gaps.
    """
    # Get dictionary with original feature names
    formatted_dict = _to_original_feature_dict(user_input)
    # Get skill column names (excluding skill_gaps)
    skill_features = get_skill_column_names()

    # Now extract in order of skill_features
    skill_vector = [formatted_dict.get(feat, 0) for feat in skill_features]

    return np.array(skill_vector)

# Load career skill profiles once at startup
print("Loading career skill profiles...")
# Load original training data
df = pd.read_csv(BASE_DIR / 'synthetic_career_data.csv')
feature_cols = [col for col in df.columns if col not in ['user_id', 'recommended_career', 'top_3_careers']]
X = df[feature_cols]
y = df['recommended_career']

# Identify skill columns (starting with 'skill_' and not 'skill_gaps')
skill_cols = [col for col in X.columns if col.startswith('skill_') and col != 'skill_gaps']
# Ensure numeric
skill_cols = [col for col in skill_cols if pd.api.types.is_numeric_dtype(X[col])]

skill_data = X[skill_cols]
df_skills = skill_data.copy()
df_skills['career'] = y.values

career_skill_profiles = {}
for career in df_skills['career'].unique():
    career_data = df_skills[df_skills['career'] == career]
    avg_skills = career_data[skill_cols].mean().values
    career_skill_profiles[career] = avg_skills

print(f"Loaded skill profiles for {len(career_skill_profiles)} careers")
print(f"Number of skill features: {len(skill_cols)}")

def calculate_skill_gaps_with_decay(user_input: UserInput, career_skill_profiles: dict, skill_cols: list, predicted_career: str, decay_model: SkillDecayModel, now: datetime) -> list[dict]:
    """
    Calculate skill gaps for the predicted career, incorporating skill decay.
    Returns list of dicts sorted by gap descending.
    """
    if predicted_career not in career_skill_profiles:
        return []

    # Apply skill decay to user input
    user_input_dict = user_input.model_dump()
    decayed_user_data = apply_skill_decay(user_input_dict, decay_model, now)

    # Dataset columns contain spaces; API fields use underscores.
    user_skills = np.array([decayed_user_data.get(col.replace(' ', '_'), 0) for col in skill_cols])

    career_avg_skills = career_skill_profiles[predicted_career]
    skill_differences = career_avg_skills - user_skills  # positive means user needs to improve

    skill_gap_info = []
    for i, skill in enumerate(skill_cols):
        skill_gap_info.append({
            'skill': skill.replace(' ', '_'),
            'user_level': float(user_skills[i]),
            'career_average': float(career_avg_skills[i]),
            'gap': float(skill_differences[i])
        })

    # Sort by gap descending (largest gap first)
    skill_gap_info.sort(key=lambda x: x['gap'], reverse=True)
    return skill_gap_info

def calculate_skill_gaps(user_skills: np.ndarray, career_skill_profiles: dict, skill_cols: list, predicted_career: str) -> list[dict]:
    """
    Calculate skill gaps for the predicted career (without decay - kept for backward compatibility).
    Returns list of dicts sorted by gap descending.
    """
    if predicted_career not in career_skill_profiles:
        return []

    career_avg_skills = career_skill_profiles[predicted_career]
    skill_differences = career_avg_skills - user_skills  # positive means user needs to improve

    skill_gap_info = []
    for i, skill in enumerate(skill_cols):
        skill_gap_info.append({
            'skill': skill.replace(' ', '_'),
            'user_level': float(user_skills[i]),
            'career_average': float(career_avg_skills[i]),
            'gap': float(skill_differences[i])
        })

    # Sort by gap descending (largest gap first)
    skill_gap_info.sort(key=lambda x: x['gap'], reverse=True)
    return skill_gap_info

def generate_explanation_prompt(user_input: UserInput, recommended_career: str, top_3_predictions: list, skill_gaps: list[dict]) -> str:
    """
    Generate a prompt for the LLM to explain the career recommendation.
    """
    # Format top 3 predictions
    top_3_text = ", ".join([f"{career} ({prob:.1%})" for career, prob in top_3_predictions])

    # Format top skill gaps (both strengths and gaps)
    strengths = [sg for sg in skill_gaps if sg['gap'] < 0][:3]  # Top 3 strengths (negative gaps)
    gaps = [sg for sg in skill_gaps if sg['gap'] > 0][:3]      # Top 3 gaps (positive gaps)

    strengths_text = ", ".join([f"{sg['skill']} (you: {sg['user_level']:.1f}, ideal: {sg['career_average']:.1f})" for sg in strengths])
    gaps_text = ", ".join([f"{sg['skill']} (you: {sg['user_level']:.1f}, ideal: {sg['career_average']:.1f})" for sg in gaps])

    # Add decay information if available
    decay_info_text = ""
    try:
        user_dict = user_input.model_dump()
        # Use current time once for all decay calculations in this request
        now = datetime.now()
        decay_info = get_skill_decay_info(user_dict, decay_model, now)
        significant_decay = {k: v for k, v in decay_info.items() if v.get('decay_amount', 0) > 0.5}
        if significant_decay:
            decay_details = []
            for skill, info in list(significant_decay.items())[:3]:  # Show top 3
                decay_details.append(f"{skill}: {info['original_level']:.1f} → {info['decayed_level']:.1f} (-{info['decay_amount']:.1f})")
            decay_info_text = f"\n\nSkill Decay Notes (skills not used recently): {', '.join(decay_details)}"
    except Exception:
        pass  # Skip decay info if there's an error

    prompt = f"""You are an expert career counselor specializing in technology careers. Explain why the AI system recommended "{recommended_career}" for this user based on their profile.

User Profile:
- Age Range: {user_input.age_range}
- Education: {user_input.education_level}
- Field of Study: {user_input.field_of_study}
- Year of Study: {user_input.year_of_study}
- Confidence Score: {user_input.confidence_score:.2f}

Top 3 Career Matches: {top_3_text}

Key Strengths (where user exceeds recommendations): {strengths_text if strengths_text else "None significant"}

Key Development Areas (where user falls short of recommendations): {gaps_text if gaps_text else "None significant"}{decay_info_text}

Provide a clear, encouraging explanation that:
1. Validates the user's strengths
2. Explains why this career is a good fit based on their profile
3. Identifies 1-2 key areas for growth that would make them an even stronger candidate
4. Suggests concrete steps to develop those skills
5. Keeps the tone supportive and motivational

Explanation:"""

    return prompt

def get_llm_explanation(prompt: str) -> str:
    """
    Get explanation from Anthropic Claude API.
    """
    if not anthropic_client:
        return "LLM explanations are not available. Please configure ANTHROPIC_API_KEY environment variable."

    try:
        message = anthropic_client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            max_tokens=300,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

# Profile Management Pydantic Models
class ProfileBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    age_range: Optional[str] = Field(None, max_length=30)
    education_level: Optional[str] = Field(None, max_length=100)
    field_of_study: Optional[str] = Field(None, max_length=100)
    year_of_study: Optional[str] = Field(None, max_length=100)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class ProfileCreate(ProfileBase):
    name: str
    email: str

class ProfileUpdate(ProfileBase):
    pass

class AssessmentBase(BaseModel):
    id: Optional[str] = Field(None, min_length=1, max_length=100)
    recommended_career: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_3_predictions: List[Dict[str, Any]]
    skill_gap_analysis: List[Dict[str, Any]]
    timestamp: Optional[str] = None
    explanation: Optional[str] = None
    skill_decay_info: Optional[Dict[str, Any]] = None

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the AI Career Recommendation API with Security Enhancements and Skill Decay Modeling"}

# Recommendation endpoint
@app.post("/recommend")
async def recommend_career(request: Request, user_input: UserInput, include_explanation: bool = False):
    """
    Provide career recommendation based on user input.
    Returns predicted career, top 3 predictions, skill gap analysis, and optionally an LLM-generated explanation.
    Now includes skill decay modeling for skills not used recently.
    """
    try:
        now = datetime.now()
        processed_input = preprocess_input(user_input)
        predicted_career, predictions = get_market_adjusted_predictions(processed_input)
        gaps = calculate_skill_gaps_with_decay(
            user_input, career_skill_profiles, skill_cols, predicted_career, decay_model, now
        )
        response = {
            "recommended_career": predicted_career,
            "confidence": float(predictions[0][1]),
            "top_3_predictions": [
                {"career": career, "probability": float(prob)} for career, prob in predictions
            ],
            "skill_gap_analysis": gaps,
        }
        if include_explanation:
            if anthropic_client:
                prompt = generate_explanation_prompt(user_input, predicted_career, predictions, gaps)
                response["explanation"] = get_llm_explanation(prompt)
            else:
                response["explanation"] = "LLM explanations are not available. Your recommendation and skill analysis are still available."
        decay_info = get_skill_decay_info(user_input.model_dump(), decay_model, now)
        significant_decay = {k: v for k, v in decay_info.items() if v.get('decay_amount', 0) > 0.1}
        if significant_decay:
            response["skill_decay_info"] = significant_decay
        return response
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Recommendation failed: {exc}")
        raise HTTPException(status_code=500, detail="Unable to generate recommendation") from exc

# Explanation endpoint
@app.post("/explain")
async def explain_recommendation(request: Request, user_input: UserInput):
    """
    Generate a detailed explanation for a career recommendation using LLM.
    This endpoint focuses specifically on providing explanations.
    Now includes skill decay modeling.
    """
    if not anthropic_client:
        raise HTTPException(
            status_code=503,
            detail="LLM explanations are not available. Please set the ANTHROPIC_API_KEY environment variable."
        )

    try:
        # Get client IP for logging/monitoring
        client_ip = request.client.host if request.client else "unknown"

        # Process the request same as recommend endpoint
        processed_input = preprocess_input(user_input)
        predicted_career, top_3_predictions = get_market_adjusted_predictions(processed_input)
        user_skills = extract_skill_vector(user_input)
        skill_gaps = calculate_skill_gaps_with_decay(user_input, career_skill_profiles, skill_cols, predicted_career, decay_model, datetime.now())

        # Generate explanation
        prompt = generate_explanation_prompt(user_input, predicted_career, top_3_predictions, skill_gaps)
        explanation = get_llm_explanation(prompt)

        # Add skill decay information to explanation response
        decay_info = {}
        try:
            user_dict = user_input.model_dump()
            # Get current time once for efficiency
            now = datetime.now()
            decay_info = get_skill_decay_info(user_dict, decay_model, now)
        except Exception as e:
            print(f"Warning: Could not generate decay info for explanation: {e}")

        response = {
            "recommended_career": predicted_career,
            "top_3_predictions": [
                {"career": career, "probability": float(prob)}
                for career, prob in top_3_predictions
            ],
            "explanation": explanation
        }

        if decay_info:
            response["skill_decay_info"] = decay_info

        return response

    except Exception as e:
        # Log error (without sensitive data)
        client_ip = request.client.host if request.client else "unknown"
        print(f"ERROR PROCESSING EXPLANATION REQUEST - IP: {client_ip}, Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Profiles use high-entropy device tokens; administrators use a separate key.
profile_bearer = HTTPBearer(auto_error=False)


def require_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(profile_bearer)):
    expected = os.getenv("ADMIN_API_KEY", "")
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail="Administrator access is not configured")
    if not credentials or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=401, detail="Administrator authentication required", headers={"WWW-Authenticate": "Bearer"})


def require_profile_access(profile_id: uuid.UUID, credentials: Optional[HTTPAuthorizationCredentials] = Depends(profile_bearer)):
    profile = profile_store.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    provided = hashlib.sha256(credentials.credentials.encode()).hexdigest() if credentials else ""
    expected = profile.get("_access_token_hash", "")
    if not expected or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="This profile requires its device access token", headers={"WWW-Authenticate": "Bearer"})


# Profile Management Endpoints
@app.post("/profiles")
async def create_profile(profile: ProfileBase):
    """Create a new user profile."""
    try:
        # Generate a unique ID
        profile_id = str(uuid.uuid4())
        access_token = secrets.token_urlsafe(32)
        now = datetime.now()

        # Create profile data
        profile_data = {
            "id": profile_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "_access_token_hash": hashlib.sha256(access_token.encode()).hexdigest(),
            **profile.model_dump()
        }

        # Save profile
        success = profile_store._save_profile(profile_id, profile_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create profile")

        return {"id": profile_id, "access_token": access_token, "message": "Profile created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/profiles/{profile_id}", dependencies=[Depends(require_profile_access)])
async def get_profile(profile_id: uuid.UUID):
    """Get a user profile by ID."""
    profile = profile_store.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {key: value for key, value in profile.items() if not key.startswith("_")}

@app.put("/profiles/{profile_id}", dependencies=[Depends(require_profile_access)])
async def update_profile(profile_id: uuid.UUID, profile: ProfileBase):
    """Update an existing user profile."""
    try:
        # Check if profile exists
        existing_profile = profile_store.get_profile(profile_id)
        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Update fields
        update_data = profile.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now().isoformat()

        # Save profile
        success = profile_store.update_profile(profile_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/profiles/{profile_id}", dependencies=[Depends(require_profile_access)])
async def delete_profile(profile_id: uuid.UUID):
    """Delete a user profile."""
    try:
        success = profile_store.delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles", dependencies=[Depends(require_admin)])
async def list_profiles(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """List user profiles with pagination."""
    profiles = profile_store.list_profiles()
    # Apply pagination
    paginated_profiles = profiles[offset:offset + limit]
    return paginated_profiles

@app.post("/profiles/{profile_id}/assessments", dependencies=[Depends(require_profile_access)])
async def add_assessment(profile_id: uuid.UUID, assessment: AssessmentBase):
    """Add an assessment to a user's profile."""
    try:
        # Check if profile exists
        existing_profile = profile_store.get_profile(profile_id)
        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Prepare assessment data
        assessment_data = assessment.model_dump()
        if not assessment_data.get("timestamp"):
            assessment_data["timestamp"] = datetime.now().isoformat()

        # Add assessment to profile
        success = profile_store.add_assessment(profile_id, assessment_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add assessment")

        return {"message": "Assessment added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/profiles/{profile_id}/assessments", dependencies=[Depends(require_profile_access)])
async def get_assessments(profile_id: uuid.UUID, limit: int = Query(50, ge=1, le=1000)):
    """Get assessment history for a user profile."""
    try:
        if not profile_store.get_profile(profile_id):
            raise HTTPException(status_code=404, detail="Profile not found")
        assessments = profile_store.get_assessment_history(profile_id)
        # Apply limit
        return assessments[:limit]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "preprocessor_loaded": preprocessor is not None,
        "label_encoder_loaded": label_encoder is not None,
        "anthropic_available": anthropic_client is not None,
        "decay_model_loaded": decay_model is not None,
        "profile_store_available": profile_store is not None,
        "timestamp": time.time()
    }

# Model management endpoints
@app.post("/model/retrain", dependencies=[Depends(require_admin)])
async def trigger_retrain(background_tasks: BackgroundTasks, force: bool = False):
    """
    Trigger model retraining. Can be run in the background.
    """
    def retrain_task():
        result = check_and_retrain(force=force)
        if result:
            reload_active_model()
            print(f"Retraining completed successfully. New version: {result}")
        else:
            print("Retraining did not produce a new model.")

    background_tasks.add_task(retrain_task)
    return {"message": "Retraining started in background", "force": force}

@app.get("/model/versions", dependencies=[Depends(require_admin)])
async def list_model_versions():
    """List all available model versions."""
    versions = get_model_versions()
    return {"versions": versions}

@app.post("/model/promote/{version_id}", dependencies=[Depends(require_admin)])
async def promote_model_endpoint(version_id: str):
    """Promote a specific version to be the current model."""
    success = promote_stored_model_version(version_id)
    if success:
        reload_active_model()
        return {"message": f"Version {version_id} promoted to current model"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to promote version {version_id}")

@app.post("/model/scheduler/start", dependencies=[Depends(require_admin)])
async def start_scheduler_endpoint():
    """Start the automatic retraining scheduler."""
    start_retraining_scheduler()
    return {"message": "Retraining scheduler started"}

@app.post("/model/scheduler/stop", dependencies=[Depends(require_admin)])
async def stop_scheduler_endpoint():
    """Stop the automatic retraining scheduler."""
    stop_retraining_scheduler()
    return {"message": "Retraining scheduler stopped"}

def reload_active_model():
    """Activate a complete trained artifact set for subsequent requests."""
    global model, preprocessor, label_encoder
    if model_retrainer.model is not None:
        model, preprocessor, label_encoder = (
            model_retrainer.model, model_retrainer.preprocessor, model_retrainer.label_encoder
        )


model_retrainer.on_model_updated = reload_active_model


# For running directly with uvicorn: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
