# Let's first check the CSV file to see what's causing the issue
import pandas as pd

df = pd.read_csv('synthetic_career_data.csv')
print("Column names:")
for i, col in enumerate(df.columns):
    print(f"{i:2}: '{col}'")

print("\nFirst few rows:")
print(df.head())

print("\nData types:")
print(df.dtypes)