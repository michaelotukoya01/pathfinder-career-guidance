# Exploratory Data Analysis for AI Career Recommendation System
# Analyzes the synthetic dataset to understand patterns, distributions, and relationships

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load the dataset
print("Loading synthetic dataset...")
df = pd.read_csv('synthetic_career_data.csv')
print(f"Dataset shape: {df.shape}")
print(f"Number of records: {len(df)}")
print(f"Number of features: {len(df.columns)}")

print("\n=== DATASET INFO ===")
print(df.info())
print("\n=== BASIC STATISTICS ===")
print(df.describe())

print("\n=== MISSING VALUES ===")
missing = df.isnull().sum()
print(missing[missing > 0])
if missing.sum() == 0:
    print("No missing values found!")

print("\n=== CAREER DISTRIBUTION (TARGET VARIABLE) ===")
career_counts = df['recommended_career'].value_counts().sort_index()
print(career_counts)

# Visualize career distribution
plt.figure(figsize=(12, 6))
career_counts.plot(kind='bar')
plt.title('Distribution of Recommended Careers')
plt.xlabel('Career')
plt.ylabel('Count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('career_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n=== CONFIDENCE SCORE DISTRIBUTION ===")
print(f"Mean confidence score: {df['confidence_score'].mean():.3f}")
print(f"Median confidence score: {df['confidence_score'].median():.3f}")
print(f"Std deviation: {df['confidence_score'].std():.3f}")
print(f"Min confidence score: {df['confidence_score'].min():.3f}")
print(f"Max confidence score: {df['confidence_score'].max():.3f}")

# Visualize confidence score distribution
plt.figure(figsize=(10, 6))
plt.hist(df['confidence_score'], bins=20, edgecolor='black', alpha=0.7)
plt.title('Distribution of Confidence Scores')
plt.xlabel('Confidence Score')
plt.ylabel('Frequency')
plt.axvline(df['confidence_score'].mean(), color='red', linestyle='--', label=f'Mean: {df["confidence_score"].mean():.3f}')
plt.axvline(df['confidence_score'].median(), color='green', linestyle='--', label=f'Median: {df["confidence_score"].median():.3f}')
plt.legend()
plt.tight_layout()
plt.savefig('confidence_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# More specific column selection to avoid including skill_gaps in skill features
academic_cols = [col for col in df.columns if col.startswith('academic_')]
skill_cols = [col for col in df.columns if col.startswith('skill_') and col != 'skill_gaps']
interest_cols = [col for col in df.columns if col.startswith('interest_')]
workpref_cols = [col for col in df.columns if col.startswith('workpref_')]
personality_cols = [col for col in df.columns if col.startswith('personality_')]

print(f"\nFeature counts:")
print(f"Academic features: {len(academic_cols)}")
print(f"Skill features: {len(skill_cols)}")
print(f"Interest features: {len(interest_cols)}")
print(f"Work preference features: {len(workpref_cols)}")
print(f"Personality features: {len(personality_cols)}")

# Academic performance analysis
print("\n=== ACADEMIC PERFORMANCE ANALYSIS ===")
academic_data = df[academic_cols]
print("Academic statistics:")
print(academic_data.describe())

# Visualize academic performance
plt.figure(figsize=(10, 6))
academic_data.mean().plot(kind='bar')
plt.title('Average Academic Performance by Subject')
plt.ylabel('Average Score (1-5)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('academic_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# Technical skills analysis
print("\n=== TECHNICAL SKILLS ANALYSIS ===")
skill_data = df[skill_cols]
print("Skill statistics:")
print(skill_data.describe())

# Visualize skill proficiency
plt.figure(figsize=(12, 6))
skill_data.mean().sort_values(ascending=False).plot(kind='bar')
plt.title('Average Proficiency by Technical Skill')
plt.ylabel('Average Proficiency (0-5)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('skill_proficiency.png', dpi=300, bbox_inches='tight')
plt.close()

# Interests analysis
print("\n=== INTERESTS ANALYSIS ===")
interest_data = df[interest_cols]
print("Interest statistics:")
print(interest_data.describe())

# Visualize interests
plt.figure(figsize=(10, 6))
interest_data.mean().sort_values(ascending=False).plot(kind='bar')
plt.title('Average Interest Level by Area')
plt.ylabel('Average Interest (1-5)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('interest_areas.png', dpi=300, bbox_inches='tight')
plt.close()

# Work preferences analysis
print("\n=== WORK PREFERENCES ANALYSIS ===")
workpref_data = df[workpref_cols]
print("Work preference statistics:")
print(workpref_data.describe())

# Visualize work preferences
plt.figure(figsize=(10, 6))
workpref_data.mean().sort_values(ascending=False).plot(kind='bar')
plt.title('Average Work Preference Scores')
plt.ylabel('Average Score (1-5)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('work_preferences.png', dpi=300, bbox_inches='tight')
plt.close()

# Personality traits analysis
print("\n=== PERSONALITY TRAITS ANALYSIS ===")
personality_data = df[personality_cols]
print("Personality statistics:")
print(personality_data.describe())

# Visualize personality traits
plt.figure(figsize=(10, 6))
personality_data.mean().sort_values(ascending=False).plot(kind='bar')
plt.title('Average Personality Trait Scores')
plt.ylabel('Average Score (1-5)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('personality_traits.png', dpi=300, bbox_inches='tight')
plt.close()

# Correlation analysis
print("\n=== CORRELATION ANALYSIS ===")
# Select numeric columns for correlation
numeric_cols = df.select_dtypes(include=[np.number]).columns
correlation_matrix = df[numeric_cols].corr()

# Find strongest correlations with confidence score
confidence_corr = correlation_matrix['confidence_score'].drop('confidence_score').sort_values(key=abs, ascending=False)
print("Top 10 features most correlated with confidence score:")
print(confidence_corr.head(10))

# Visualize correlation matrix (subset)
plt.figure(figsize=(12, 10))
# Focus on key feature groups for better visualization
key_cols = academic_cols[:4] + skill_cols[:4] + interest_cols[:4] + workpref_cols[:3] + personality_cols[:3] + ['confidence_score']
subset_corr = df[key_cols].corr()
sns.heatmap(subset_corr, annot=True, cmap='coolwarm', center=0, square=True, linewidths=0.5)
plt.title('Correlation Matrix (Key Features)')
plt.tight_layout()
plt.savefig('correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

# Career-specific analysis
print("\n=== CAREER-SPECIFIC ANALYSIS ===")
# Compare average profiles for top 3 most common careers
top_careers = career_counts.head(3).index.tolist()
print(f"Top 3 careers: {top_careers}")

career_profiles = {}
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    career_profiles[career] = {
        'count': len(career_data),
        'avg_confidence': career_data['confidence_score'].mean(),
        'avg_academic': career_data[academic_cols].mean().mean(),
        'avg_skills': career_data[skill_cols].mean().mean(),
        'avg_interests': career_data[interest_cols].mean().mean(),
        'avg_workpref': career_data[workpref_cols].mean().mean(),
        'avg_personality': career_data[personality_cols].mean().mean()
    }

print("\nCareer profiles:")
for career, profile in career_profiles.items():
    print(f"{career}:")
    for key, value in profile.items():
        print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")

# Visualize career profiles
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Average Profiles by Career Category', fontsize=16)

# Academic profiles
ax = axes[0, 0]
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    means = career_data[academic_cols].mean()
    ax.plot(academic_cols, means.values, marker='o', label=career)
ax.set_title('Academic Profiles')
ax.set_ylabel('Average Score')
ax.legend()
ax.tick_params(axis='x', rotation=45)

# Skill profiles
ax = axes[0, 1]
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    means = career_data[skill_cols].mean()
    ax.plot(skill_cols, means.values, marker='o', label=career)
ax.set_title('Skill Profiles')
ax.set_ylabel('Average Proficiency')
ax.legend()
ax.tick_params(axis='x', rotation=45)

# Interest profiles
ax = axes[0, 2]
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    means = career_data[interest_cols].mean()
    ax.plot(interest_cols, means.values, marker='o', label=career)
ax.set_title('Interest Profiles')
ax.set_ylabel('Average Interest')
ax.legend()
ax.tick_params(axis='x', rotation=45)

# Work preference profiles
ax = axes[1, 0]
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    means = career_data[workpref_cols].mean()
    ax.plot(workpref_cols, means.values, marker='o', label=career)
ax.set_title('Work Preference Profiles')
ax.set_ylabel('Average Score')
ax.legend()
ax.tick_params(axis='x', rotation=45)

# Personality profiles
ax = axes[1, 1]
for career in top_careers:
    career_data = df[df['recommended_career'] == career]
    means = career_data[personality_cols].mean()
    ax.plot(personality_cols, means.values, marker='o', label=career)
ax.set_title('Personality Profiles')
ax.set_ylabel('Average Score')
ax.legend()
ax.tick_params(axis='x', rotation=45)

# Confidence score distribution by career
ax = axes[1, 2]
career_confidence_data = [df[df['recommended_career'] == career]['confidence_score'].values for career in top_careers]
ax.boxplot(career_confidence_data)
ax.set_xticklabels(top_careers, rotation=45)
ax.set_title('Confidence Score Distribution by Career')
ax.set_ylabel('Confidence Score')

plt.tight_layout()
plt.savefig('career_profiles.png', dpi=300, bbox_inches='tight')
plt.close()

# Feature importance analysis (simple approach)
print("\n=== FEATURE IMPORTANCE ANALYSIS (SIMPLE) ===")
# Calculate average absolute correlation with target for each feature group
feature_groups = {
    'Academic': academic_cols,
    'Skills': skill_cols,
    'Interests': interest_cols,
    'Work Preferences': workpref_cols,
    'Personality': personality_cols
}

group_importance = {}
for group_name, cols in feature_groups.items():
    # Get correlations with confidence score for this group
    corrs = []
    for col in cols:
        if col in correlation_matrix.columns:
            corr = abs(correlation_matrix.loc['confidence_score', col])
            corrs.append(corr)
    group_importance[group_name] = np.mean(corrs) if corrs else 0

print("Average absolute correlation with confidence score by feature group:")
for group, importance in sorted(group_importance.items(), key=lambda x: x[1], reverse=True):
    print(f"  {group}: {importance:.3f}")

# Visualize feature group importance
plt.figure(figsize=(10, 6))
groups = list(group_importance.keys())
importance_values = [group_importance[g] for g in groups]
plt.bar(groups, importance_values)
plt.title('Feature Group Importance (Avg |Correlation| with Confidence Score)')
plt.ylabel('Average Absolute Correlation')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('feature_group_importance.png', dpi=300, bbox_inches='tight')
plt.close()

# Save summary statistics to file
print("\n=== SAVING SUMMARY STATISTICS ===")
summary_stats = {
    'dataset_info': {
        'n_records': int(len(df)),
        'n_features': int(len(df.columns)),
        'career_distribution': df['recommended_career'].value_counts().to_dict(),
        'confidence_score_stats': {
            'mean': float(df['confidence_score'].mean()),
            'median': float(df['confidence_score'].median()),
            'std': float(df['confidence_score'].std()),
            'min': float(df['confidence_score'].min()),
            'max': float(df['confidence_score'].max())
        }
    },
    'academic_stats': academic_data.describe().to_dict(),
    'skill_stats': skill_data.describe().to_dict(),
    'interest_stats': interest_data.describe().to_dict(),
    'workpref_stats': workpref_data.describe().to_dict(),
    'personality_stats': personality_data.describe().to_dict(),
    'top_correlations_with_confidence': {
        'positive': confidence_corr.head(5).to_dict(),
        'negative': confidence_corr.tail(5).to_dict()
    },
    'feature_group_importance': group_importance
}

with open('eda_summary.json', 'w') as f:
    json.dump(summary_stats, f, indent=2)

print("\nExploratory Data Analysis complete!")
print("Generated visualizations:")
print("- career_distribution.png")
print("- confidence_distribution.png")
print("- academic_performance.png")
print("- skill_proficiency.png")
print("- interest_areas.png")
print("- work_preferences.png")
print("- personality_traits.png")
print("- correlation_matrix.png")
print("- career_profiles.png")
print("- feature_group_importance.png")
print("Saved summary statistics to: eda_summary.json")