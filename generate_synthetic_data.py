# Synthetic Data Generation for AI Career Recommendation System
# This script creates a synthetic dataset based on our career profiles and data collection design

import pandas as pd
import numpy as np
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define constants based on our career profiles
CAREERS = [
    "Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "Cybersecurity Analyst",
    "Network Engineer",
    "Cloud Engineer",
    "Database Administrator",
    "UI/UX Designer"
]

# Academic subjects and their relevance to careers (simplified mapping)
ACADEMIC_SUBJECTS = ["Mathematics", "Statistics", "Programming", "Computer Networking", "Database Management", "Web Development"]

# Technical skills
TECHNICAL_SKILLS = [
    "Python", "JavaScript", "Java", "C/C++", "SQL", "HTML/CSS", "React",
    "Networking", "Linux", "Databases", "Cloud", "Cybersecurity",
    "Data Analysis", "Machine Learning"
]

# Interest areas
INTEREST_AREAS = [
    "Building applications", "Analyzing data", "Artificial intelligence",
    "Cybersecurity", "Networking", "Cloud computing", "Databases",
    "UI/UX design", "Research"
]

# Work preferences
WORK_PREFERENCES = [
    "Building things", "Analyzing information", "Solving security problems",
    "Working with numbers", "Designing UI", "Investigating problems"
]

# Personality traits
PERSONALITY_TRAITS = [
    "Analytical", "Creative", "Problem-solver", "Detail-oriented",
    "Collaborative", "Independent worker"
]

def generate_synthetic_data(n_samples=500):
    """Generate synthetic dataset for career recommendation"""

    data = []

    for i in range(n_samples):
        # Basic demographics
        age_ranges = ["Under 18", "18-20", "21-23", "24-26", "27-30", "31+"]
        education_levels = ["High School", "Associate's", "Bachelor's", "Master's", "PhD", "Professional Certification"]
        fields_of_study = ["Computer Science", "Information Technology", "Computer Engineering",
                          "Software Engineering", "Data Science", "Information Systems",
                          "Electrical Engineering", "Mathematics", "Physics", "Other"]
        years_of_study = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate Year 1",
                         "Graduate Year 2+", "Graduate", "Not applicable"]

        # Generate basic info
        age_range = np.random.choice(age_ranges, p=[0.05, 0.15, 0.25, 0.25, 0.2, 0.1])
        education_level = np.random.choice(education_levels, p=[0.1, 0.1, 0.4, 0.25, 0.05, 0.1])
        field_of_study = np.random.choice(fields_of_study)
        year_of_study = np.random.choice(years_of_study)

        # Generate academic performance (1-5 scale)
        academic_scores = {}
        for subject in ACADEMIC_SUBJECTS:
            # Add some correlation between related subjects
            base_score = np.random.randint(1, 6)
            # Add some correlation for related subjects
            if subject in ["Mathematics", "Statistics"]:
                # Correlate these two
                if subject == "Mathematics":
                    math_score = base_score
                    stats_score = max(1, min(5, math_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = math_score
                else:  # Statistics
                    stats_score = base_score
                    math_score = max(1, min(5, stats_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = stats_score
            elif subject in ["Programming", "Web Development"]:
                # Correlate these two
                if subject == "Programming":
                    prog_score = base_score
                    web_score = max(1, min(5, prog_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = prog_score
                else:  # Web Development
                    web_score = base_score
                    prog_score = max(1, min(5, web_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = web_score
            elif subject in ["Computer Networking", "Database Management"]:
                # Correlate these two
                if subject == "Computer Networking":
                    net_score = base_score
                    db_score = max(1, min(5, net_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = net_score
                else:  # Database Management
                    db_score = base_score
                    net_score = max(1, min(5, db_score + np.random.randint(-1, 2)))
                    academic_scores[subject] = db_score
            else:
                academic_scores[subject] = base_score

        # Generate technical skills experience (1-5 scale, with some zeros for no experience)
        skill_scores = {}
        for skill in TECHNICAL_SKILLS:
            # Some correlation with academic background
            if skill == "Python" or skill == "Java" or skill == "C/C++":
                # Programming skills correlate with programming academic score
                prog_base = academic_scores["Programming"]
                skill_score = max(0, min(5, prog_base + np.random.randint(-2, 2)))
            elif skill == "SQL" or skill == "Databases":
                # Database skills correlate with database academic score
                db_base = academic_scores["Database Management"]
                skill_score = max(0, min(5, db_base + np.random.randint(-2, 2)))
            elif skill == "HTML/CSS" or skill == "JavaScript" or skill == "React":
                # Web skills correlate with web development academic score
                web_base = academic_scores["Web Development"]
                skill_score = max(0, min(5, web_base + np.random.randint(-2, 2)))
            elif skill == "Networking" or skill == "Linux":
                # Networking skills correlate with networking academic score
                net_base = academic_scores["Computer Networking"]
                skill_score = max(0, min(5, net_base + np.random.randint(-2, 2)))
            elif skill == "Machine Learning" or skill == "Data Analysis":
                # Data skills correlate with math/stats academic scores
                math_base = (academic_scores["Mathematics"] + academic_scores["Statistics"]) / 2
                skill_score = max(0, min(5, int(round(math_base)) + np.random.randint(-2, 2)))
            elif skill == "Cloud" or skill == "Cybersecurity":
                # These are somewhat independent but still have some correlation
                base_score = np.random.randint(1, 6)
                skill_score = max(0, min(5, base_score + np.random.randint(-2, 2)))
            else:
                skill_score = np.random.randint(0, 6)  # 0-5 scale

            skill_scores[skill] = skill_score

        # Generate interest levels (1-5 scale)
        interest_scores = {}
        for interest in INTEREST_AREAS:
            # Some correlations with skills and academics
            base_interest = np.random.randint(1, 6)

            # Add some correlations
            if interest == "Building applications":
                # Correlates with programming skills
                prog_skill = (skill_scores["Python"] + skill_scores["JavaScript"] +
                            skill_scores["Java"] + skill_scores["C/C++"]) / 4
                interest_score = max(1, min(5, int(round(prog_skill)) + np.random.randint(-1, 2)))
            elif interest == "Analyzing data":
                # Correlates with data analysis skills
                data_skill = (skill_scores["Data Analysis"] + skill_scores["SQL"] +
                            skill_scores["Machine Learning"]) / 3
                interest_score = max(1, min(5, int(round(data_skill)) + np.random.randint(-1, 2)))
            elif interest == "Artificial intelligence":
                # Correlates with ML and AI skills
                ai_skill = (skill_scores["Machine Learning"] + skill_scores["Python"]) / 2
                interest_score = max(1, min(5, int(round(ai_skill)) + np.random.randint(-1, 2)))
            elif interest == "Cybersecurity":
                # Correlates with cybersecurity skills
                sec_skill = skill_scores["Cybersecurity"]
                interest_score = max(1, min(5, int(round(sec_skill)) + np.random.randint(-1, 2)))
            elif interest == "Networking":
                # Correlates with networking skills
                net_skill = skill_scores["Networking"]
                interest_score = max(1, min(5, int(round(net_skill)) + np.random.randint(-1, 2)))
            elif interest == "Cloud computing":
                # Correlates with cloud skills
                cloud_skill = skill_scores["Cloud"]
                interest_score = max(1, min(5, int(round(cloud_skill)) + np.random.randint(-1, 2)))
            elif interest == "Databases":
                # Correlates with database skills
                db_skill = (skill_scores["SQL"] + skill_scores["Databases"]) / 2
                interest_score = max(1, min(5, int(round(db_skill)) + np.random.randint(-1, 2)))
            elif interest == "UI/UX design":
                # Correlates with frontend skills
                ui_skill = (skill_scores["HTML/CSS"] + skill_scores["JavaScript"] +
                          skill_scores["React"]) / 3
                interest_score = max(1, min(5, int(round(ui_skill)) + np.random.randint(-1, 2)))
            elif interest == "Research":
                # Correlates with academic performance
                acad_avg = np.mean(list(academic_scores.values()))
                interest_score = max(1, min(5, int(round(acad_avg)) + np.random.randint(-1, 2)))
            else:
                interest_score = base_interest

            interest_scores[interest] = interest_score

        # Generate work preferences (1-5 scale, where 1=strongly disagree, 5=strongly agree)
        work_prefs = {}
        for pref in WORK_PREFERENCES:
            # Some correlations with interests and skills
            base_pref = np.random.randint(1, 6)

            if pref == "Building things":
                # Correlates with building applications interest
                build_interest = interest_scores["Building applications"]
                pref_score = max(1, min(5, int(round(build_interest)) + np.random.randint(-1, 2)))
            elif pref == "Analyzing information":
                # Correlates with analyzing data interest
                analyze_interest = interest_scores["Analyzing data"]
                pref_score = max(1, min(5, int(round(analyze_interest)) + np.random.randint(-1, 2)))
            elif pref == "Solving security problems":
                # Correlates with cybersecurity interest
                security_interest = interest_scores["Cybersecurity"]
                pref_score = max(1, min(5, int(round(security_interest)) + np.random.randint(-1, 2)))
            elif pref == "Working with numbers":
                # Correlates with math/stats academics
                num_score = (academic_scores["Mathematics"] + academic_scores["Statistics"]) / 2
                pref_score = max(1, min(5, int(round(num_score)) + np.random.randint(-1, 2)))
            elif pref == "Designing UI":
                # Correlates with UI/UX interest
                ui_interest = interest_scores["UI/UX design"]
                pref_score = max(1, min(5, int(round(ui_interest)) + np.random.randint(-1, 2)))
            elif pref == "Investigating problems":
                # Correlates with research interest
                research_interest = interest_scores["Research"]
                pref_score = max(1, min(5, int(round(research_interest)) + np.random.randint(-1, 2)))
            else:
                pref_score = base_pref

            work_prefs[pref] = pref_score

        # Generate personality traits (1-5 scale)
        personality_scores = {}
        for trait in PERSONALITY_TRAITS:
            # Mostly random with slight correlations
            base_trait = np.random.randint(1, 6)

            if trait == "Analytical":
                # Correlates with math/stats and data analysis
                anal_score = (academic_scores["Mathematics"] + academic_scores["Statistics"] +
                            skill_scores["Data Analysis"]) / 3
                trait_score = max(1, min(5, int(round(anal_score)) + np.random.randint(-1, 2)))
            elif trait == "Creative":
                # Correlates with UI/UX and building apps interest
                creat_score = (interest_scores["UI/UX design"] + interest_scores["Building applications"]) / 2
                trait_score = max(1, min(5, int(round(creat_score)) + np.random.randint(-1, 2)))
            elif trait == "Problem-solver":
                # Correlates with multiple areas
                prob_score = (academic_scores["Mathematics"] + academic_scores["Programming"] +
                            skill_scores["Data Analysis"]) / 3
                trait_score = max(1, min(5, int(round(prob_score)) + np.random.randint(-1, 2)))
            elif trait == "Detail-oriented":
                # Somewhat random but slightly correlated with conscientiousness
                detail_score = np.random.randint(1, 6)
                trait_score = max(1, min(5, detail_score + np.random.randint(-1, 2)))
            elif trait == "Collaborative":
                # Somewhat random
                collab_score = np.random.randint(1, 6)
                trait_score = max(1, min(5, collab_score + np.random.randint(-1, 2)))
            elif trait == "Independent worker":
                # Inverse of collaborative to some extent
                # Since we don't have "Working in teams" in WORK_PREFERENCES, we'll make it somewhat random
                # but with a slight tendency to be inverse of collaborative
                collab_tendency = work_prefs.get("Building things", 3)  # Using Building things as proxy
                indep_score = max(1, min(5, (6 - collab_tendency) + np.random.randint(-1, 2)))
                trait_score = indep_score
            else:
                trait_score = base_trait

            personality_scores[trait] = trait_score

        # Determine career match based on rules (simplified for demo)
        career_scores = {}

        # Software Engineer
        se_score = (
            skill_scores["Python"] * 0.2 +
            skill_scores["Java"] * 0.2 +
            skill_scores["C/C++"] * 0.1 +
            skill_scores["JavaScript"] * 0.1 +
            academic_scores["Programming"] * 0.2 +
            academic_scores["Mathematics"] * 0.1 +
            interest_scores["Building applications"] * 0.1
        )
        career_scores["Software Engineer"] = se_score

        # Frontend Developer
        fe_score = (
            skill_scores["HTML/CSS"] * 0.25 +
            skill_scores["JavaScript"] * 0.25 +
            skill_scores["React"] * 0.2 +
            academic_scores["Web Development"] * 0.15 +
            interest_scores["UI/UX design"] * 0.1 +
            interest_scores["Building applications"] * 0.05
        )
        career_scores["Frontend Developer"] = fe_score

        # Backend Developer
        be_score = (
            skill_scores["Java"] * 0.2 +
            skill_scores["Python"] * 0.2 +
            skill_scores["SQL"] * 0.15 +
            skill_scores["Databases"] * 0.15 +
            academic_scores["Programming"] * 0.15 +
            academic_scores["Database Management"] * 0.1 +
            interest_scores["Building applications"] * 0.05
        )
        career_scores["Backend Developer"] = be_score

        # Data Analyst
        da_score = (
            skill_scores["SQL"] * 0.25 +
            skill_scores["Data Analysis"] * 0.2 +
            skill_scores["Python"] * 0.15 +
            academic_scores["Statistics"] * 0.15 +
            academic_scores["Mathematics"] * 0.1 +
            interest_scores["Analyzing data"] * 0.1 +
            work_prefs["Working with numbers"] * 0.05
        )
        career_scores["Data Analyst"] = da_score

        # Data Scientist
        ds_score = (
            skill_scores["Python"] * 0.2 +
            skill_scores["Machine Learning"] * 0.2 +
            skill_scores["Data Analysis"] * 0.15 +
            academic_scores["Statistics"] * 0.15 +
            academic_scores["Mathematics"] * 0.1 +
            academic_scores["Programming"] * 0.1 +
            interest_scores["Analyzing data"] * 0.05 +
            interest_scores["Artificial intelligence"] * 0.05
        )
        career_scores["Data Scientist"] = ds_score

        # Machine Learning Engineer
        mle_score = (
            skill_scores["Python"] * 0.25 +
            skill_scores["Machine Learning"] * 0.25 +
            skill_scores["Python"] * 0.15 +  # Software engineering proxy using Python
            academic_scores["Programming"] * 0.15 +
            academic_scores["Mathematics"] * 0.1 +
            academic_scores["Statistics"] * 0.1
        )
        career_scores["Machine Learning Engineer"] = mle_score

        # AI Engineer
        ai_score = (
            skill_scores["Python"] * 0.2 +
            skill_scores["Machine Learning"] * 0.2 +
            skill_scores["Machine Learning"] * 0.15 +  # Deep learning proxy using ML
            academic_scores["Mathematics"] * 0.15 +
            academic_scores["Statistics"] * 0.1 +
            academic_scores["Programming"] * 0.1 +
            interest_scores["Artificial intelligence"] * 0.1
        )
        career_scores["AI Engineer"] = ai_score

        # Cybersecurity Analyst
        csa_score = (
            skill_scores["Cybersecurity"] * 0.25 +
            skill_scores["Networking"] * 0.2 +
            skill_scores["Linux"] * 0.15 +
            academic_scores["Computer Networking"] * 0.15 +
            academic_scores["Programming"] * 0.1 +
            interest_scores["Cybersecurity"] * 0.1 +  # Fixed reference
            interest_scores["Research"] * 0.05  # Proxy for investigating problems
        )
        career_scores["Cybersecurity Analyst"] = csa_score

        # Network Engineer
        ne_score = (
            skill_scores["Networking"] * 0.25 +
            skill_scores["Linux"] * 0.2 +
            skill_scores["Cloud"] * 0.15 +
            academic_scores["Computer Networking"] * 0.2 +
            academic_scores["Mathematics"] * 0.1 +
            interest_scores["Networking"] * 0.1
        )
        career_scores["Network Engineer"] = ne_score

        # Cloud Engineer
        ce_score = (
            skill_scores["Cloud"] * 0.25 +
            skill_scores["Linux"] * 0.2 +
            skill_scores["Networking"] * 0.15 +
            skill_scores["Cloud"] * 0.1 +  # Docker proxy using Cloud
            academic_scores["Computer Networking"] * 0.1 +
            academic_scores["Programming"] * 0.1 +
            interest_scores["Cloud computing"] * 0.1
        )
        career_scores["Cloud Engineer"] = ce_score

        # Database Administrator
        dba_score = (
            skill_scores["SQL"] * 0.3 +
            skill_scores["Databases"] * 0.25 +
            academic_scores["Database Management"] * 0.2 +
            academic_scores["Mathematics"] * 0.1 +
            academic_scores["Programming"] * 0.1 +
            interest_scores["Databases"] * 0.1
        )
        career_scores["Database Administrator"] = dba_score

        # UI/UX Designer
        uiux_score = (
            skill_scores["HTML/CSS"] * 0.2 +
            skill_scores["JavaScript"] * 0.15 +
            skill_scores["React"] * 0.15 +
            academic_scores["Web Development"] * 0.1 +
            interest_scores["UI/UX design"] * 0.25 +
            interest_scores["Building applications"] * 0.1 +
            (personality_scores.get("Creative", 3) * 0.05 if "Creative" in personality_scores else 3 * 0.05)
        )
        career_scores["UI/UX Designer"] = uiux_score

        # Add some noise to scores
        for career in career_scores:
            career_scores[career] += np.random.normal(0, 0.5)
            career_scores[career] = max(0, min(5, career_scores[career]))  # Keep in 0-5 range

        # Determine recommended career (highest score)
        recommended_career = max(career_scores, key=career_scores.get)
        confidence_score = career_scores[recommended_career] / 5.0  # Normalize to 0-1

        # Get top 3 careers
        sorted_careers = sorted(career_scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = [career for career, score in sorted_careers[:3]]

        # Generate skill gap analysis (simplified)
        skill_gaps = {}
        if recommended_career == "Data Scientist":
            required_skills = ["Python", "Statistics", "Machine Learning", "Data Analysis"]
            for skill in required_skills:
                current_level = skill_scores.get(skill, 0)
                required_level = 4  # Assume level 4 is needed
                gap = max(0, required_level - current_level)
                skill_gaps[skill] = gap

        # Create data record
        record = {
            "user_id": f"U{str(i+1).zfill(4)}",
            "age_range": age_range,
            "education_level": education_level,
            "field_of_study": field_of_study,
            "year_of_study": year_of_study,
            "recommended_career": recommended_career,
            "confidence_score": round(confidence_score, 3),
            "top_3_careers": "|".join(top_3),
        }

        # Add academic scores
        for subject, score in academic_scores.items():
            record[f"academic_{subject.lower().replace(' ', '_')}"] = score

        # Add skill scores
        for skill, score in skill_scores.items():
            # Handle special characters in skill names
            safe_key = skill.lower().replace('+', 'plus').replace('/', '_').replace('.', '_')
            record[f"skill_{safe_key}"] = score

        # Add interest scores
        for interest, score in interest_scores.items():
            # Handle special characters in interest names
            safe_key = interest.lower().replace(' ', '_').replace('/', '_')
            record[f"interest_{safe_key}"] = score

        # Add work preference scores
        for pref, score in work_prefs.items():
            # Handle special characters in preference names
            safe_key = pref.lower().replace(' ', '_').replace('/', '_')
            record[f"workpref_{safe_key}"] = score

        # Add personality scores
        for trait, score in personality_scores.items():
            # Handle special characters in trait names
            safe_key = trait.lower().replace(' ', '_').replace('-', '_')
            record[f"personality_{safe_key}"] = score

        # Add skill gap info (simplified as JSON string)
        record["skill_gaps"] = str(skill_gaps)

        data.append(record)

    return pd.DataFrame(data)

# Generate the dataset
print("Generating synthetic dataset...")
df = generate_synthetic_data(500)

# Save to CSV
df.to_csv("synthetic_career_data.csv", index=False)
print(f"Generated dataset with {len(df)} records and {len(df.columns)} features")
print(f"Saved to synthetic_career_data.csv")

# Show basic info
print("\nDataset Info:")
print(df.head())
print(f"\nCareer distribution:")
print(df['recommended_career'].value_counts().sort_index())