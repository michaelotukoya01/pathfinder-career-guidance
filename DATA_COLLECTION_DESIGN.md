# AI Career Recommendation & Guidance System - Data Collection & Dataset Design

## PART 8 — DATA COLLECTION

### Data Collection Strategy:
We'll use a hybrid approach combining existing datasets with custom data collection to ensure both breadth and relevance.

#### Option A — Public Datasets Exploration:
We'll investigate these potential public datasets:
1. **Kaggle datasets** on career preferences, student skills, and career outcomes
2. **UCI Machine Learning Repository** datasets related to education and career choice
3. **O*NET dataset** for detailed occupation information
4. **LinkedIn/Economic Graph datasets** (if accessible through academic programs)
5. **UNESCO/World Bank education and employment datasets**
6. **Stack Overflow Developer Survey** (annual dataset with tech skills and career info)
7. **Kaggle's "Data Science Salary Survey"** and similar tech career surveys

#### Option B — Custom Questionnaire Development:
We'll design and deploy a questionnaire targeting university students interested in technology careers.

#### Option C — Hybrid Approach (Recommended):
1. Use public datasets to understand general patterns and validate career profiles
2. Collect targeted dataset from university students for model training and validation
3. Use O*NET and similar sources to validate skill-career mappings

### Target Sample Characteristics:
- **Primary**: University students (especially STEM/tech-focused)
- **Secondary**: Recent graduates, career changers
- **Target Size**: Minimum 300-500 responses for initial model training
- **Diversity Goals**: Various academic years, different technical backgrounds, diverse demographics

## PART 9 — DESIGN YOUR DATASET

### Dataset Structure Design:

Our dataset will consist of several interconnected tables/entities:

#### 1. User Profile Table
- user_id (Primary Key)
- age_range
- education_level
- field_of_study
- year_of_study
- institution_type
- demographics (optional, handled carefully for privacy)

#### 2. Academic Information Table
- user_id (Foreign Key)
- subject_area (mathematics, statistics, programming, networking, databases, web_dev)
- proficiency_level (1-5 scale: Very Weak to Excellent)

#### 3. Technical Skills Table
- user_id (Foreign Key)
- skill_name (Python, JavaScript, Java, C/C++, SQL, HTML/CSS, React, Networking, Linux, Databases, Cloud, Cybersecurity, Data Analysis, Machine Learning)
- experience_level (1-5 scale: None to Expert)
- years_of_experience (numeric, optional)

#### 4. Interests Table
- user_id (Foreign Key)
- interest_area (building_apps, data_analysis, AI, cybersecurity, networking, cloud, databases, UI/UX, research)
- interest_level (1-5 scale: Not Interested to Very Interested)

#### 5. Work Preferences Table
- user_id (Foreign Key)
- preference_question (building_things, analyzing_info, security_problems, working_with_numbers, designing_ui, investigating_problems)
- preference_value (boolean or 1-5 scale)

#### 6. Personality/Psychometric Table
- user_id (Foreign Key)
- trait_dimension (analytical, creative, problem_solving, detail_orientation, collaboration, independent_work)
- trait_score (1-5 scale)

#### 7. Career Outcomes/Targets Table (for supervised learning)
- user_id (Foreign Key)
- recommended_career (from our 12 career categories)
- confidence_score (model-generated)
- alternative_careers (top 3 alternatives)
- skill_gap_analysis (JSON/text field)
- learning_path_recommendations (JSON/text field)

#### 8. Career Reference Tables (Reference Data)
- careers table: career_id, career_name, description
- career_skills table: career_id, skill_id, required_proficiency_level
- career_interests table: career_id, interest_id, required_interest_level
- career_academic table: career_id, academic_area, required_academic_level

### Data Collection Instrument Design:

#### Section A: Basic Demographics (4 questions)
1. Age range: [Dropdown: Under 18, 18-20, 21-23, 24-26, 27-30, 31+]
2. Current education level: [Dropdown: High School, Associate's, Bachelor's, Master's, PhD, Professional Certification, Other]
3. Field of study: [Text input with suggestions: Computer Science, IT, Engineering, Mathematics, Physics, Business, etc.]
4. Year of study: [Dropdown: Freshman, Sophomore, Junior, Senior, Graduate Year 1, Graduate Year 2+, Graduate, Not applicable]

#### Section B: Academic Background (6 questions - 1-5 scale)
For each subject area, ask: "How would you rate your ability/performance in [subject]?"
1. Mathematics
2. Statistics
3. Programming/Coding
4. Computer Networking
5. Database Management
6. Web Development

#### Section C: Technical Skills (14 questions - experience level)
For each skill, ask: "What is your experience level with [technology/skill]?"
Options: None, Beginner, Intermediate, Advanced, Expert
Skills: Python, JavaScript, Java, C/C++, SQL, HTML/CSS, React, Networking, Linux, Databases, Cloud, Cybersecurity, Data Analysis, Machine Learning

#### Section D: Interests (9 questions - 1-5 scale)
For each area, ask: "How interested are you in [activity]?"
Scale: 1 (Not at all interested) to 5 (Extremely interested)
Areas: Building applications, Analyzing data, Artificial intelligence, Cybersecurity, Networking, Cloud computing, Databases, UI/UX design, Research

#### Section E: Work Preferences (6 questions - boolean or scale)
1. Do you prefer building things vs. analyzing existing systems? [Scale: 1-5]
2. Do you enjoy solving security problems? [Yes/No or 1-5]
3. Do you prefer working with numbers and data? [Yes/No or 1-5]
4. Do you enjoy designing user interfaces? [Yes/No or 1-5]
5. Do you enjoy investigating problems to find root causes? [Yes/No or 1-5]
6. Do you prefer working independently or in teams? [Scale: 1-5]

#### Section F: Personality Traits (6 questions - 1-5 scale)
For each trait, ask: "How strongly do you identify with being [trait description]?"
Scale: 1 (Not at all) to 5 (Very much)
Traits: Analytical, Creative, Problem-solver, Detail-oriented, Collaborative, Independent worker

### Data Quality Considerations:
1. **Validation**: Implement validation rules to prevent obviously inconsistent responses
2. **Completeness**: Allow "Prefer not to answer" for sensitive questions
3. **Consistency checks**: Flag responses that show extreme inconsistencies (e.g., expert in programming but novice in math for a programming-heavy careers)
4. **Privacy**: Anonymize data, store minimally necessary personal information
5. **Bias awareness**: Monitor for demographic biases in collection and design questions to minimize cultural bias

### Next Steps for Data Collection:
1. Create survey instrument using Google Forms, Typeform, or similar
2. Pilot test with small group (20-30 students) to refine questions
3. Deploy to target university populations through relevant departments/clubs
4. Collect and clean data
5. Perform exploratory data analysis
6. Prepare features for machine learning modeling

## NEXT STEPS
Proceed to PART 10 — LEARN THE DATA SCIENCE TOOLS