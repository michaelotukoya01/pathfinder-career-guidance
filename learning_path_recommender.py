# Learning Path Recommendation System for AI Career Guidance
# Suggests learning resources based on skill gaps

import json

def load_learning_resources():
    """
    Load a dictionary of learning resources for various skills.
    In a real application, this would come from a database or API.
    """
    # This is a simplified mock dataset
    resources = {
        'skill_python': [
            {'title': 'Python for Everybody', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/python', 'level': 'Beginner'},
            {'title': 'Complete Python Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/complete-python-bootcamp/', 'level': 'Beginner to Advanced'},
            {'title': 'Python Documentation', 'platform': 'Python.org', 'url': 'https://docs.python.org/3/', 'level': 'All'}
        ],
        'skill_java': [
            {'title': 'Java Programming and Software Engineering Fundamentals', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/java-programming', 'level': 'Beginner'},
            {'title': 'Java In-Depth: Become a Complete Java Engineer!', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/java-in-depth/', 'level': 'Intermediate to Expert'}
        ],
        'skill_machine learning': [
            {'title': 'Machine Learning by Andrew Ng', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/machine-learning', 'level': 'Beginner'},
            {'title': 'Deep Learning Specialization', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/deep-learning', 'level': 'Intermediate'},
            {'title': 'Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow', 'platform': 'Book', 'url': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/', 'level': 'Practical'}
        ],
        'skill_databases': [
            {'title': 'Introduction to Databases', 'platform': 'edX', 'url': 'https://www.edx.org/course/introduction-to-databases', 'level': 'Beginner'},
            {'title': 'SQL for Data Science', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/sql-for-data-science', 'level': 'Beginner'}
        ],
        'skill_sql': [
            {'title': 'SQL for Data Science', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/sql-for-data-science', 'level': 'Beginner'},
            {'title': 'Master SQL for Data Science', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/master-sql-for-data-science/', 'level': 'Intermediate'}
        ],
        'skill_cloud': [
            {'title': 'Google Cloud Platform Fundamentals', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/gcp-fundamentals', 'level': 'Beginner'},
            {'title': 'AWS Fundamentals: Going Cloud-Native', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/aws-fundamentals-getting-started-with-cloud-computing', 'level': 'Beginner'}
        ],
        'skill_cybersecurity': [
            {'title': 'Introduction to Cyber Security', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/introduction-to-cyber-security', 'level': 'Beginner'},
            {'title': 'Cybersecurity Specialization', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/cyber-security', 'level': 'Intermediate'}
        ],
        'skill_html_css': [
            {'title': 'HTML, CSS, and Javascript for Web Developers', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/html-css-javascript', 'level': 'Beginner'},
            {'title': 'The Complete Web Developer Course 2.0', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/the-complete-web-developer-course-2/', 'level': 'Full Stack'}
        ],
        'skill_javascript': [
            {'title': 'JavaScript Algorithms and Data Structures', 'platform': 'freecodecamp.org', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'level': 'Free Interactive'},
            {'title': 'The Modern JavaScript Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/the-modern-javascript-bootcamp/', 'level': 'Beginner to Advanced'}
        ],
        'skill_data analysis': [
            {'title': 'Data Analysis with Python', 'platform': 'freecodecamp.org', 'url': 'https://www.freecodecamp.org/learn/data-analysis-with-python/', 'level': 'Free Interactive'},
            {'title': 'Data Analysis and Presentation Skills: the PwC Approach', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/data-analysis-presentation-pwc', 'level': 'Intermediate'}
        ]
    }
    return resources

def get_learning_path(skill_gaps, top_n=3):
    """
    Generate learning path recommendations based on skill gaps.
    skill_gaps: list of dictionaries from recommendaton engine (sorted by gap descending)
    top_n: number of top skills to generate learning paths for
    """
    resources = load_learning_resources()
    learning_paths = []

    # Consider only skills with positive gaps (where user needs to improve)
    deficit_skills = [skill for skill in skill_gaps if skill['gap'] > 0]

    # Sort by gap descending (largest gap first)
    deficit_skills.sort(key=lambda x: x['gap'], reverse=True)

    # Take top N skills
    top_skills = deficit_skills[:top_n]

    for skill_info in top_skills:
        skill_name = skill_info['skill']
        gap = skill_info['gap']

        if skill_name in resources:
            skill_resources = resources[skill_name]
            # Sort resources by level (we can define an order: Beginner < Intermediate < Advanced)
            # For simplicity, we'll just take the first two
            recommended = skill_resources[:2]
            learning_paths.append({
                'skill': skill_name,
                'gap': gap,
                'recommended_resources': recommended
            })
        else:
            # If no specific resources, provide a generic suggestion
            learning_paths.append({
                'skill': skill_name,
                'gap': gap,
                'recommended_resources': [{
                    'title': f'Search for {skill_name} courses on online learning platforms',
                    'platform': 'Various',
                    'url': '#',
                    'level': 'Varies'
                }]
            })

    return learning_paths

def print_learning_path(learning_paths):
    """Print the learning path recommendations in a readable format."""
    if not learning_paths:
        print("No skill gaps to address or no resources found.")
        return

    print("\n" + "="*60)
    print("LEARNING PATH RECOMMENDATIONS")
    print("="*60)

    for i, path in enumerate(learning_paths, 1):
        print(f"\n{i}. Skill to Improve: {path['skill']}")
        print(f"   Current Gap: {path['gap']:.1f} points")
        print("   Recommended Resources:")
        for j, resource in enumerate(path['recommended_resources'], 1):
            print(f"     {j}. {resource['title']} ({resource['platform']})")
            print(f"        Level: {resource['level']}")
            print(f"        URL: {resource['url']}")

    print("\n" + "="*60)

def main():
    """Main function to demonstrate the learning path recommendation system."""
    print("Learning Path Recommendation System")
    print("="*40)

    # Example skill gaps (similar to what would come from recommendation engine)
    # In practice, these would be generated by the recommendation_engine.py
    example_skill_gaps = [
        {'skill': 'skill_python', 'user_level': 0.0, 'career_average': 2.12, 'gap': 2.12},
        {'skill': 'skill_cybersecurity', 'user_level': 1.0, 'career_average': 2.58, 'gap': 1.58},
        {'skill': 'skill_databases', 'user_level': 3.0, 'career_average': 4.12, 'gap': 1.12},
        {'skill': 'skill_sql', 'user_level': 3.0, 'career_average': 4.01, 'gap': 1.01},
        {'skill': 'skill_cloud', 'user_level': 2.0, 'career_average': 2.49, 'gap': 0.49},
        {'skill': 'skill_java', 'user_level': 2.0, 'career_average': 2.18, 'gap': 0.18},
        {'skill': 'skill_html_css', 'user_level': 2.0, 'career_average': 2.11, 'gap': 0.11},
        {'skill': 'skill_javascript', 'user_level': 3.0, 'career_average': 2.13, 'gap': -0.87},  # Negative gap (strength)
        {'skill': 'skill_data analysis', 'user_level': 4.0, 'career_average': 2.88, 'gap': -1.12},  # Negative gap
        {'skill': 'skill_machine learning', 'user_level': 2.0, 'career_average': 2.41, 'gap': 0.41}
    ]

    # Sort by gap descending (as done in recommendation engine)
    example_skill_gaps.sort(key=lambda x: x['gap'], reverse=True)

    # Get learning path recommendations
    learning_paths = get_learning_path(example_skill_gaps, top_n=3)

    # Print the recommendations
    print_learning_path(learning_paths)

    print("\nNote: This is a demonstration. In a real system, the skill gaps would come from the recommendation engine.")

if __name__ == "__main__":
    main()