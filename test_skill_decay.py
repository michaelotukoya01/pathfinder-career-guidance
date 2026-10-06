#!/usr/bin/env python3
"""
Unit tests for the skill decay utility.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skill_decay_utils import SkillDecayModel, apply_skill_decay, get_skill_decay_info

def test_skill_decay_model_initialization():
    """Test that the SkillDecayModel initializes correctly."""
    print("Testing SkillDecayModel initialization...")

    # Test default initialization
    model = SkillDecayModel()
    assert hasattr(model, 'decay_rates')
    assert len(model.decay_rates) > 0
    print("  PASS: Default initialization works")

    # Test custom decay rates
    custom_rates = {'skill_python': 0.5, 'skill_java': 0.3}
    model = SkillDecayModel(decay_rates=custom_rates)
    assert model.decay_rates['skill_python'] == 0.5
    assert model.decay_rates['skill_java'] == 0.3
    print("  PASS: Custom decay rates work")

def test_calculate_decayed_skill():
    """Test the decay calculation function."""
    print("\nTesting decay calculation...")

    model = SkillDecayModel()

    # Test no decay (recent use) - use a date very close to today
    from datetime import date
    today = date.today().isoformat()
    result = model.calculate_decayed_skill(5.0, 'skill_python', today)
    # Should be very close to 5.0 (allowing for small floating point differences)
    assert abs(result - 5.0) < 0.001
    print("  PASS: No decay for recent use")

    # Test no decay (None date)
    result = model.calculate_decayed_skill(5.0, 'skill_python', None)
    assert result == 5.0  # Should be no decay for None date
    print("  PASS: No decay for None date")

    # Test decay calculation
    # Using a known date to calculate expected result
    # For simplicity, we'll just check that decayed value is less than original
    result = model.calculate_decayed_skill(5.0, 'skill_python', '2020-01-01')
    assert 0 <= result < 5.0
    print("  PASS: Decay reduces skill value appropriately")

    # Test zero skill (should remain zero)
    result = model.calculate_decayed_skill(0.0, 'skill_python', '2020-01-01')
    assert result == 0.0
    print("  PASS: Zero skill remains zero")

def test_apply_skill_decay():
    """Test applying decay to a user profile."""
    print("\nTesting apply_skill_decay function...")

    user_data = {
        'skill_python': 5.0,
        'skill_java': 3.0,
        'skill_machine_learning': 2.0,
        'last_used_skill_python': '2022-06-01',
        'last_used_skill_java': '2020-01-01',
        'last_used_skill_machine_learning': None,  # No decay expected
        'age_range': '21-23',
        'education_level': "Bachelor's"
    }

    decayed_data = apply_skill_decay(user_data)

    # Check that decayed values are present and reasonable
    assert 'skill_python' in decayed_data
    assert 'skill_java' in decayed_data
    assert 'skill_machine_learning' in decayed_data

    # Python and Java should have decayed
    assert decayed_data['skill_python'] < user_data['skill_python']
    assert decayed_data['skill_java'] < user_data['skill_java']

    # Machine learning should not have decayed (no date)
    assert decayed_data['skill_machine_learning'] == user_data['skill_machine_learning']

    # Non-skill fields should be unchanged
    assert decayed_data['age_range'] == user_data['age_range']
    assert decayed_data['education_level'] == user_data['education_level']

    print("  PASS: Skill decay applied correctly to user profile")

def test_get_skill_decay_info():
    """Test getting decay information."""
    print("\nTesting get_skill_decay_info function...")

    user_data = {
        'skill_python': 5.0,
        'skill_java': 3.0,
        'last_used_skill_python': '2022-06-01',
        'last_used_skill_java': '2020-01-01'
    }

    decay_info = get_skill_decay_info(user_data)

    # Check structure
    assert 'skill_python' in decay_info
    assert 'skill_java' in decay_info

    python_info = decay_info['skill_python']
    java_info = decay_info['skill_java']

    # Check required fields
    required_fields = ['original_level', 'decayed_level', 'decay_amount', 'last_used', 'days_since_used']
    for field in required_fields:
        assert field in python_info
        assert field in java_info

    # Check values
    assert python_info['original_level'] == 5.0
    assert java_info['original_level'] == 3.0
    assert python_info['decayed_level'] < 5.0
    assert java_info['decayed_level'] < 3.0
    assert python_info['decay_amount'] > 0
    assert java_info['decay_amount'] > 0
    assert python_info['last_used'] == '2022-06-01'
    assert java_info['last_used'] == '2020-01-01'

    print("  PASS: Decay information retrieved correctly")

def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")

    model = SkillDecayModel()

    # Unknown skill should use default decay rate
    result = model.calculate_decayed_skill(5.0, 'unknown_skill', '2020-01-01')
    assert 0 <= result < 5.0
    print("  PASS: Unknown skills use default decay rate")

    # Empty user data
    empty_data = {}
    decayed = apply_skill_decay(empty_data)
    assert decayed == {}
    print("  PASS: Empty data handled correctly")

    # User data with no last_used fields
    no_decay_data = {
        'skill_python': 4.0,
        'skill_java': 3.0
    }
    decayed = apply_skill_decay(no_decay_data)
    assert decayed['skill_python'] == 4.0
    assert decayed['skill_java'] == 3.0
    print("  PASS: No decay when no last_used fields present")

def run_all_tests():
    """Run all tests."""
    print("Running skill decay utility tests...\n")

    try:
        test_skill_decay_model_initialization()
        test_calculate_decayed_skill()
        test_apply_skill_decay()
        test_get_skill_decay_info()
        test_edge_cases()

        print("\nPASS: All tests passed!")
        return True
    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)