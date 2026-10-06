# Check the problematic columns specifically
import pandas as pd

df = pd.read_csv('synthetic_career_data.csv')

# Check the specific columns that were causing issues
prob_cols = ['skill_data analysis', 'skill_machine learning']
print("Checking problematic columns:")
for col in prob_cols:
    print(f"\n{col}:")
    print(f"  Data type: {df[col].dtype}")
    print(f"  Unique values: {df[col].unique()[:10]}...")  # First 10 unique values
    print(f"  Number of unique values: {df[col].nunique()}")
    print(f"  Min value: {df[col].min()}")
    print(f"  Max value: {df[col].max()}")

    # Check if all values are numeric
    try:
        numeric_check = pd.to_numeric(df[col], errors='coerce')
        null_count = numeric_check.isnull().sum()
        print(f"  Non-numeric values: {null_count}")
        if null_count > 0:
            print(f"  Non-numeric entries: {df[col][numeric_check.isnull()].unique()}")
    except Exception as e:
        print(f"  Error converting to numeric: {e}")

# Let's also check if there are any other columns that might be problematic
print("\n\nChecking all columns for non-numeric values where expected:")
numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
print(f"Columns detected as numeric: {len(numeric_cols)}")

# Try to force convert all except the known string columns
str_cols = ['user_id', 'age_range', 'education_level', 'field_of_study', 'year_of_study',
            'recommended_career', 'top_3_careers', 'skill_gaps']
print(f"Known string columns: {len(str_cols)}")

# Check if any other columns have string values
for col in df.columns:
    if col not in str_cols:
        # Try to convert to numeric
        try:
            pd.to_numeric(df[col], errors='raise')
        except ValueError as e:
            print(f"Column '{col}' cannot be converted to numeric: {e}")
            # Show some problematic values
            non_numeric = []
            for val in df[col].unique():
                try:
                    float(val)
                except:
                    non_numeric.append(val)
                    if len(non_numeric) >= 5:  # Limit output
                        break
            if non_numeric:
                print(f"  Sample non-numeric values: {non_numeric}")