-- Database Schema for AI Career Recommendation System
-- Compatible with SQLite and PostgreSQL (with minor adjustments)

-- Drop tables if they exist (for clean slate)
DROP TABLE IF EXISTS user_feedback;
DROP TABLE IF EXISTS user_queries;
DROP TABLE IF EXISTS learning_resources;
DROP TABLE IF EXISTS career_skills;
DROP TABLE IF EXISTS user_skills;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS careers;
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) UNIQUE NOT NULL,  -- External user ID (e.g., from authentication system)
    age_range VARCHAR(20),
    education_level VARCHAR(50),
    field_of_study VARCHAR(100),
    year_of_study VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Careers table
CREATE TABLE careers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),  -- e.g., 'Technical', 'Soft', 'Language'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User skills (many-to-many between users and skills)
CREATE TABLE user_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level INTEGER CHECK (proficiency_level >= 0 AND proficiency_level <= 5),
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE(user_id, skill_id)
);

-- Career skills (many-to-many between careers and skills with required proficiency)
CREATE TABLE career_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    career_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    required_proficiency INTEGER NOT NULL CHECK (required_proficiency >= 0 AND required_proficiency <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (career_id) REFERENCES careers(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE(career_id, skill_id)
);

-- Learning resources table
CREATE TABLE learning_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    platform VARCHAR(100),  -- e.g., 'Coursera', 'Udemy', 'edX', 'YouTube'
    difficulty_level VARCHAR(20),  -- Beginner, Intermediate, Advanced
    estimated_duration_hours INTEGER,
    is_free BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many between learning_resources and skills (a resource can teach multiple skills)
CREATE TABLE resource_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    relevance_score REAL CHECK (relevance_score >= 0 AND relevance_score <= 1),  -- How relevant this resource is for the skill
    FOREIGN KEY (resource_id) REFERENCES learning_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE(resource_id, skill_id)
);

-- User queries (to store recommendation requests for analysis and improvement)
CREATE TABLE user_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recommended_career VARCHAR(100),
    confidence_score REAL,
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_user_skills_user ON user_skills(user_id);
CREATE INDEX idx_user_skills_skill ON user_skills(skill_id);
CREATE INDEX idx_career_skills_career ON career_skills(career_id);
CREATE INDEX idx_career_skills_skill ON career_skills(skill_id);
CREATE INDEX idx_resource_skills_resource ON resource_skills(resource_id);
CREATE INDEX idx_resource_skills_skill ON resource_skills(skill_id);
CREATE INDEX idx_user_queries_user ON user_queries(user_id);
CREATE INDEX idx_user_queries_timestamp ON user_queries(query_timestamp);

-- Optional: Insert some sample data for demonstration
-- Uncomment the following lines if you want to insert sample data when creating the database

-- INSERT INTO users (user_id, age_range, education_level, field_of_study, year_of_study) VALUES
-- ('user_001', '21-23', 'Bachelors', 'Computer Science', 'Senior Year'),
-- ('user_002', '24-26', 'Masters', 'Data Science', 'Graduate');

-- INSERT INTO careers (name, description) VALUES
-- ('Software Engineer', 'Develops and maintains software applications'),
-- ('Data Scientist', 'Analyzes complex data to help organizations make decisions'),
-- ('Database Administrator', 'Manages and maintains database systems');

-- INSERT INTO skills (name, category) VALUES
-- ('Python', 'Technical'),
-- ('Java', 'Technical'),
-- ('SQL', 'Technical'),
-- ('Machine Learning', 'Technical'),
-- ('Data Analysis', 'Technical'),
-- ('Web Development', 'Technical'),
-- ('Cybersecurity', 'Technical'),
-- ('Problem Solving', 'Soft'),
-- ('Communication', 'Soft');

-- INSERT INTO user_skills (user_id, skill_id, proficiency_level) VALUES
-- (1, 1, 3),  -- user_001 has Python level 3
-- (1, 2, 2),  -- user_001 has Java level 2
-- (2, 1, 4),  -- user_002 has Python level 4
-- (2, 4, 3);  -- user_002 has Machine Learning level 3

-- INSERT INTO career_skills (career_id, skill_id, required_proficiency) VALUES
-- (1, 1, 4),  -- Software Engineer requires Python level 4
-- (1, 2, 3),  -- Software Engineer requires Java level 3
-- (2, 1, 4),  -- Data Scientist requires Python level 4
-- (2, 4, 4),  -- Data Scientist requires Machine Learning level 4
-- (2, 5, 4),  -- Data Scientist requires Data Analysis level 4
-- (3, 3, 4),  -- Database Administrator requires SQL level 4
-- (3, 6, 3);  -- Database Administrator requires Web Development level 3

-- INSERT INTO learning_resources (title, description, url, platform, difficulty_level, estimated_duration_hours, is_free) VALUES
-- ('Python for Everybody', 'Learn to program and analyze data with Python', 'https://www.coursera.org/specializations/python', 'Coursera', 'Beginner', 40, TRUE),
-- ('Complete Python Bootcamp', 'Go from zero to hero in Python', 'https://www.udemy.com/course/complete-python-bootcamp/', 'Udemy', 'Beginner to Advanced', 50, FALSE),
-- ('Introduction to Cyber Security', 'Learn the basics of cybersecurity', 'https://www.coursera.org/learn/introduction-to-cyber-security', 'Coursera', 'Beginner', 20, TRUE),
-- ('Cybersecurity Specialization', 'In-depth cybersecurity training', 'https://www.coursera.org/specializations/cyber-security', 'Coursera', 'Intermediate', 60, TRUE),
-- ('Introduction to Databases', 'Learn about relational databases and SQL', 'https://www.edx.org/course/introduction-to-databases', 'edX', 'Beginner', 30, TRUE),
-- ('SQL for Data Science', 'Learn SQL for data science applications', 'https://www.coursera.org/learn/sql-for-data-science', 'Coursera', 'Beginner', 25, TRUE);

-- INSERT INTO resource_skills (resource_id, skill_id, relevance_score) VALUES
-- (1, 1, 0.9),  -- Python for Everybody -> Python
-- (2, 1, 0.95), -- Complete Python Bootcamp -> Python
-- (3, 7, 0.8),  -- Introduction to Cyber Security -> Cybersecurity
-- (4, 7, 0.9),  -- Cybersecurity Specialization -> Cybersecurity
-- (5, 3, 0.85), -- Introduction to Databases -> SQL
-- (6, 3, 0.9);  -- SQL for Data Science -> SQL