# Test the exact operations that were failing in the EDA script
import pandas as pd

df = pd.read_csv('synthetic_career_data.csv')

# Recreate the exact column selection from EDA script
skill_cols = [col for col in df.columns if col.startswith('skill_')]
print(f"Number of skill columns: {len(skill_cols)}")
print("First 10 skill columns:")
for i, col in enumerate(skill_cols[:10]):
    print(f"  {i}: '{col}'")

skill_data = df[skill_cols]
print(f"\nSkill data shape: {skill_data.shape}")
print(f"Skill data dtypes:\n{skill_data.dtypes}")

# Try to calculate mean - this is where it was failing
print("\nTrying to calculate mean...")
try:
    mean_result = skill_data.mean()
    print("Mean calculation successful!")
    print(f"Mean result type: {type(mean_result)}")
    print(f"Mean result length: {len(mean_result)}")
    print("First 5 mean values:")
    for i, (col, val) in enumerate(mean_result.items()):
        if i < 5:
            print(f"  {col}: {val}")
except Exception as e:
    print(f"Error calculating mean: {e}")
    import traceback
    traceback.print_exc()

# Let's check each column individually
print("\nChecking each skill column individually:")
problematic_cols = []
for col in skill_cols:
    try:
        col_mean = df[col].mean()
        # print(f"  {col}: {col_mean:.3f}")  # Too verbose
    except Exception as e:
        print(f"  ERROR with {col}: {e}")
        problematic_cols.append((col, str(e)))

if problematic_cols:
    print(f"\nFound {len(problematic_cols)} problematic columns:")
    for col, error in problematic_cols:
        print(f"  {col}: {error}")
else:
    print("\nAll columns processed successfully!")