# skill_decay_utils.py
"""
Skill decay modeling for the AI Career Recommendation System.
Implements temporal decay functions for skill proficiency based on time since last use.
"""

import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import json
import os

def days_since_used(last_used_date: str, now: datetime) -> int:
    """Compare date-only and ISO timestamps consistently, including UTC offsets."""
    last_used = datetime.fromisoformat(last_used_date.replace('Z', '+00:00'))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if last_used.tzinfo is None:
        last_used = last_used.replace(tzinfo=timezone.utc)
    return max(0, (now - last_used).days)


class SkillDecayModel:
    """
    Models skill decay over time using exponential decay function.

    The decay formula: skill_effective = skill_base * e^(-lambda * time_since_use)
    where:
    - skill_base: current self-reported skill level (0-5)
    - lambda: decay rate constant (higher = faster decay)
    - time_since_use: time elapsed since last using the skill (in years)
    """

    def __init__(self, decay_rates: Optional[Dict[str, float]] = None):
        """
        Initialize the skill decay model.

        Args:
            decay_rates: Dictionary mapping skill categories to decay rates (lambda values).
                        If None, uses default rates.
        """
        # Default decay rates by skill category (higher = faster skill decay)
        # These values represent approximately how quickly skills degrade without use
        self.default_decay_rates = {
            # Technical skills decay faster without practice
            'skill_python': 0.3,
            'skill_javascript': 0.3,
            'skill_java': 0.3,
            'skill_c_cplusplus': 0.3,
            'skill_sql': 0.25,
            'skill_html_css': 0.25,
            'skill_react': 0.35,
            'skill_networking': 0.2,
            'skill_linux': 0.2,
            'skill_databases': 0.2,
            'skill_cloud': 0.3,
            'skill_cybersecurity': 0.25,
            'skill_data_analysis': 0.25,
            'skill_machine_learning': 0.3,

            # Academic/knowledge-based skills decay slower
            'academic_mathematics': 0.1,
            'academic_statistics': 0.1,
            'academic_programming': 0.15,
            'academic_computer_networking': 0.15,
            'academic_database_management': 0.15,
            'academic_web_development': 0.15,

            # Soft skills and interests decay very slowly
            'interest_building_applications': 0.05,
            'interest_analyzing_data': 0.05,
            'interest_artificial_intelligence': 0.05,
            'interest_cybersecurity': 0.05,
            'interest_networking': 0.05,
            'interest_cloud_computing': 0.05,
            'interest_databases': 0.05,
            'interest_ui_ux_design': 0.05,
            'interest_research': 0.05,

            'workpref_building_things': 0.05,
            'workpref_analyzing_information': 0.05,
            'workpref_solving_security_problems': 0.05,
            'workpref_working_with_numbers': 0.05,
            'workpref_designing_ui': 0.05,
            'workpref_investigating_problems': 0.05,

            'personality_analytical': 0.01,  # Personality traits change very slowly
            'personality_creative': 0.01,
            'personality_problem_solver': 0.01,
            'personality_detail_oriented': 0.01,
            'personality_collaborative': 0.01,
            'personality_independent_worker': 0.01,
        }

        self.decay_rates = decay_rates if decay_rates is not None else self.default_decay_rates

    def calculate_decayed_skill(self, skill_level: float, skill_name: str,
                              last_used_date: Optional[str] = None,
                              now: Optional[datetime] = None) -> float:
        """
        Calculate the effective skill level after applying decay.

        Args:
            skill_level: Self-reported skill level (0-5)
            skill_name: Name of the skill (must match keys in decay_rates)
            last_used_date: Date when skill was last used (ISO format string: YYYY-MM-DD).
                           If None, assumes skill was used recently (no decay).
            now: Optional datetime to use as current time (for performance optimization).
                If None, uses datetime.now().

        Returns:
            Effective skill level after decay (0-5)
        """
        if skill_level <= 0:
            return 0.0

        if skill_name not in self.decay_rates:
            # Use a default decay rate for unknown skills
            lambda_val = 0.1
        else:
            lambda_val = self.decay_rates[skill_name]

        if not last_used_date:
            # No decay if we don't know when it was last used
            return skill_level

        try:
            # Parse the date
            # Use provided now time or get current time
            if now is None:
                now = datetime.now()

            # Calculate time difference in years
            years_since_use = days_since_used(last_used_date, now) / 365.25

            # Apply exponential decay: skill_effective = skill_base * e^(-lambda * time)
            decayed_skill = skill_level * np.exp(-lambda_val * years_since_use)

            # Ensure we don't go below 0
            return max(0.0, min(5.0, decayed_skill))
        except (ValueError, TypeError, AttributeError):
            # If date parsing fails, return original skill level
            return skill_level

    def apply_decay_to_user_profile(self, user_data: Dict, now: Optional[datetime] = None) -> Dict:
        """
        Apply skill decay to all skills in a user profile.

        Expects user_data to contain:
        - Skill fields (skill_*, academic_*, interest_*, workpref_*, personality_*)
        - Optional: last_used_<skill_name> fields for each skill

        Returns:
            Updated user data with decayed skill values
        """
        # Get current time once for efficiency
        if now is None:
            now = datetime.now()

        # Create a copy to avoid modifying the original
        result = user_data.copy()

        # Apply decay to each skill type
        skill_prefixes = ['skill_', 'academic_', 'interest_', 'workpref_', 'personality_']

        for key, value in user_data.items():
            # Check if this is a skill field
            if any(key.startswith(prefix) for prefix in skill_prefixes) and isinstance(value, (int, float)):
                # Look for corresponding last_used field
                last_used_key = f"last_used_{key}"
                last_used_date = user_data.get(last_used_key)

                # Apply decay
                decayed_value = self.calculate_decayed_skill(
                    float(value), key, last_used_date, now
                )
                result[key] = decayed_value

        return result

def decay_skill_skill(skill_level: float, years_unused: float, decay_rate: float = 0.2) -> float:
    """
    Simple utility function to calculate skill decay.

    Args:
        skill_level: Current skill level (0-5)
        years_unused: Years since skill was last used
        decay_rate: Decay rate constant (default 0.2)

    Returns:
        Decayed skill level (0-5)
    """
    if skill_level <= 0 or years_unused <= 0:
        return skill_level

    decayed = skill_level * np.exp(-decay_rate * years_unused)
    return max(0.0, min(5.0, decayed))

def get_skill_category_decay_rate(skill_name: str) -> float:
    """
    Get the default decay rate for a skill based on its name.

    Args:
        skill_name: Name of the skill

    Returns:
        Decay rate lambda value
    """
    default_rates = {
        # Technical skills decay faster without practice
        'skill_python': 0.3,
        'skill_javascript': 0.3,
        'skill_java': 0.3,
        'skill_c_cplusplus': 0.3,
        'skill_sql': 0.25,
        'skill_html_css': 0.25,
        'skill_react': 0.35,
        'skill_networking': 0.2,
        'skill_linux': 0.2,
        'skill_databases': 0.2,
        'skill_cloud': 0.3,
        'skill_cybersecurity': 0.25,
        'skill_data_analysis': 0.25,
        'skill_machine_learning': 0.3,

        # Academic/knowledge-based skills decay slower
        'academic_mathematics': 0.1,
        'academic_statistics': 0.1,
        'academic_programming': 0.15,
        'academic_computer_networking': 0.15,
        'academic_database_management': 0.15,
        'academic_web_development': 0.15,

        # Soft skills and interests decay very slowly
        'interest_building_applications': 0.05,
        'interest_analyzing_data': 0.05,
        'interest_artificial_intelligence': 0.05,
        'interest_cybersecurity': 0.05,
        'interest_networking': 0.05,
        'interest_cloud_computing': 0.05,
        'interest_databases': 0.05,
        'interest_ui_ux_design': 0.05,
        'interest_research': 0.05,

        'workpref_building_things': 0.05,
        'workpref_analyzing_information': 0.05,
        'workpref_solving_security_problems': 0.05,
        'workpref_working_with_numbers': 0.05,
        'workpref_designing_ui': 0.05,
        'workpref_investigating_problems': 0.05,

        'personality_analytical': 0.01,
        'personality_creative': 0.01,
        'personality_problem_solver': 0.01,
        'personality_detail_oriented': 0.01,
        'personality_collaborative': 0.01,
        'personality_independent_worker': 0.01,
    }

    return default_rates.get(skill_name, 0.1)  # Default rate for unknown skills

def apply_skill_decay(user_data, decay_model=None, now=None):
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

    if now is None:
        now = datetime.now()

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
                    user_data[last_used_field],
                    now
                )
                decayed_data[skill_field] = decayed_value
            except Exception as e:
                # If there's an error in date parsing, keep original value
                print(f"Warning: Could not apply decay to {skill_field}: {e}")
                pass

    return decayed_data


def get_skill_decay_info(user_data, decay_model=None, now=None):
    """
    Get information about skill decay applied to user data.

    Args:
        user_data: Dictionary containing user data
        decay_model: Optional SkillDecayModel instance
        now: Optional datetime to use as current time (for performance optimization)

    Returns:
        Dictionary mapping skill names to decay information
    """
    if decay_model is None:
        decay_model = SkillDecayModel()

    # Get current time once for efficiency
    if now is None:
        now = datetime.now()

    decay_info = {}

    # Identify all skill-related fields
    skill_fields = [key for key in user_data.keys() if key.startswith('skill_') and
                   key != 'skill_gaps' and
                   isinstance(user_data[key], (int, float))]

    for skill_field in skill_fields:
        last_used_field = f"last_used_{skill_field}"

        if user_data.get(last_used_field):
            try:
                original_level = user_data[skill_field]
                decayed_level = decay_model.calculate_decayed_skill(
                    original_level,
                    skill_field,
                    user_data[last_used_field],
                    now
                )

                decay_info[skill_field] = {
                    'original_level': original_level,
                    'decayed_level': decayed_level,
                    'decay_amount': original_level - decayed_level,
                    'last_used': user_data[last_used_field],
                    'days_since_used': days_since_used(user_data[last_used_field], now)
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


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Recent skill usage (no decay)
    decay_model = SkillDecayModel()
    recent_skill = decay_model.calculate_decayed_skill(4.0, 'skill_python', '2024-01-15')
    print(f"Skill used recently (2024-01-15): {recent_skill:.2f} (original: 4.0)")

    # Example 2: Skill not used for 2 years
    old_skill = decay_model.calculate_decayed_skill(4.0, 'skill_python', '2022-01-15')
    print(f"Skill not used for 2 years: {old_skill:.2f} (original: 4.0)")

    # Example 3: Skill not used for 5 years
    very_old_skill = decay_model.calculate_decayed_skill(4.0, 'skill_python', '2019-01-15')
    print(f"Skill not used for 5 years: {very_old_skill:.2f} (original: 4.0)")

    # Example 4: Never used recently (no date provided)
    no_date = decay_model.calculate_decayed_skill(4.0, 'skill_python', None)
    print(f"No date provided: {no_date:.2f} (original: 4.0)")

    # Example 5: Apply to full user profile
    sample_user = {
        'skill_python': 4.0,
        'skill_java': 3.0,
        'skill_machine_learning': 2.0,
        'academic_mathematics': 4.0,
        'interest_artificial_intelligence': 5.0,
        'last_used_skill_python': '2022-06-01',  # Used 1.5 years ago
        'last_used_skill_java': '2020-01-01',    # Used 4 years ago
        'last_used_skill_machine_learning': None, # No date - no decay
    }

    decayed_user = decay_model.apply_decay_to_user_profile(sample_user)
    print("\nUser profile after decay:")
    for skill in ['skill_python', 'skill_java', 'skill_machine_learning']:
        original = sample_user[skill]
        decayed = decayed_user[skill]
        print(f"  {skill}: {original:.1f} -> {decayed:.2f}")
