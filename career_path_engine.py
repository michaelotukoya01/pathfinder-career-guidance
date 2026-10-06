# career_path_engine.py
"""
Career path and transition analysis for the AI Career Recommendation System.
Builds graphs showing potential career transitions based on skill similarity.
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import itertools

class CareerPathEngine:
    """
    Analyzes career transitions and builds progression paths based on skill similarities.
    """

    def __init__(self, career_skill_profiles: Dict[str, np.ndarray], skill_columns: List[str]):
        """
        Initialize the career path engine.

        Args:
            career_skill_profiles: Dictionary mapping career names to average skill vectors
            skill_columns: List of skill column names used in the vectors
        """
        self.career_skill_profiles = career_skill_profiles
        self.skill_columns = skill_columns
        self.careers = list(career_skill_profiles.keys())
        self.similarity_matrix = self._calculate_skill_similarity_matrix()

    def _calculate_skill_similarity_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate cosine similarity between all career pairs based on skill profiles.
        """
        similarity_matrix = defaultdict(dict)

        for career1, career2 in itertools.combinations(self.careers, 2):
            vec1 = self.career_skill_profiles[career1]
            vec2 = self.career_skill_profiles[career2]

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm_a = np.linalg.norm(vec1)
            norm_b = np.linalg.norm(vec2)

            if norm_a == 0 or norm_b == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm_a * norm_b)

            similarity_matrix[career1][career2] = float(similarity)
            similarity_matrix[career2][career1] = float(similarity)

        # Set self-similarity to 1.0
        for career in self.careers:
            similarity_matrix[career][career] = 1.0

        return dict(similarity_matrix)

    def get_career_similarity(self, career1: str, career2: str) -> float:
        """
        Get similarity score between two careers (0-1).
        """
        return self.similarity_matrix.get(career1, {}).get(career2, 0.0)

    def get_related_careers(self, career: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Get most similar careers to a given career.
        """
        if career not in self.similarity_matrix:
            return []

        similarities = self.similarity_matrix[career]
        # Sort by similarity (descending) and exclude self
        sorted_similarities = sorted(
            [(c, s) for c, s in similarities.items() if c != career],
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_similarities[:top_n]

    def calculate_transition_difficulty(self, from_career: str, to_career: str) -> Dict[str, Any]:
        """
        Calculate the difficulty and requirements for transitioning between careers.
        """
        if from_career not in self.career_skill_profiles or to_career not in self.career_skill_profiles:
            return {"error": "One or both careers not found"}

        from_skills = self.career_skill_profiles[from_career]
        to_skills = self.career_skill_profiles[to_career]

        # Calculate skill gaps (what needs to be learned)
        skill_gaps = to_skills - from_skills  # Positive = need to improve, Negative = excess

        # Overall difficulty based on skill gaps
        total_positive_gap = np.sum(np.maximum(skill_gaps, 0))  # Only count deficits
        max_possible_gap = len(self.skill_columns) * 5  # Max gap if going from 0 to 5 in all skills
        difficulty_score = min(1.0, total_positive_gap / max_possible_gap) if max_possible_gap > 0 else 0.0

        # Specific skill recommendations
        skill_recommendations = []
        for i, skill in enumerate(self.skill_columns):
            gap = skill_gaps[i]
            if gap > 0.5:  # Significant gap to address
                skill_recommendations.append({
                    "skill": skill,
                    "current_level": float(from_skills[i]),
                    "target_level": float(to_skills[i]),
                    "gap": float(gap),
                    "priority": "high" if gap > 2.0 else "medium" if gap > 1.0 else "low"
                })

        # Sort by gap descending
        skill_recommendations.sort(key=lambda x: x["gap"], reverse=True)

        return {
            "from_career": from_career,
            "to_career": to_career,
            "similarity": self.get_career_similarity(from_career, to_career),
            "difficulty_score": float(difficulty_score),
            "difficulty_level": "easy" if difficulty_score < 0.3 else "medium" if difficulty_score < 0.7 else "hard",
            "estimated_time_months": int(difficulty_score * 24),  # Rough estimate: 0-24 months
            "skill_recommendations": skill_recommendations[:10],  # Top 10 skills to develop
            "total_skills_to_improve": len([s for s in skill_recommendations if s["gap"] > 0.5])
        }

    def find_career_paths(self, start_career: str, max_steps: int = 3,
                         min_similarity: float = 0.3) -> List[List[str]]:
        """
        Find possible career progression paths starting from a given career.
        Uses a simple breadth-first approach based on similarity thresholds.
        """
        if start_career not in self.careers:
            return []

        # BFS to find paths
        paths = [[start_career]]
        completed_paths = []

        for step in range(max_steps):
            new_paths = []
            for path in paths:
                current_career = path[-1]

                # Get related careers that aren't already in the path
                related = self.get_related_careers(current_career, top_n=10)
                related = [career for career, similarity in related
                          if similarity >= min_similarity and career not in path]

                for next_career in related:
                    new_path = path + [next_career]
                    new_paths.append(new_path)

                    # If this is a good endpoint (high similarity or interesting progression),
                    # consider it a completed path
                    if len(new_path) >= 2:
                        completed_paths.append(new_path)

            paths = new_paths
            if not paths:
                break

        # Also include the direct paths found
        all_paths = []
        for path in [[start_career]]:  # Reset and collect
            current = path[-1]
            related = self.get_related_careers(current, top_n=5)
            for career, similarity in related:
                if similarity >= min_similarity:
                    all_paths.append([start_career, career])

        # Add longer paths
        all_paths.extend(completed_paths)

        # Remove duplicates and sort by length (shorter first) then by average similarity
        unique_paths = []
        seen = set()
        for path in all_paths:
            path_tuple = tuple(path)
            if path_tuple not in seen:
                seen.add(path_tuple)
                unique_paths.append(path)

        def path_score(p):
            if len(p) < 2:
                return 0
            # Calculate average consecutive similarity
            similarities = []
            for i in range(len(p)-1):
                sim = self.get_career_similarity(p[i], p[i+1])
                similarities.append(sim)
            return np.mean(similarities) if similarities else 0

        unique_paths.sort(key=path_score, reverse=True)
        return unique_paths[:10]  # Return top 10 paths

    def get_career_progression_data(self, start_career: str) -> Dict[str, Any]:
        """
        Get comprehensive data for career progression visualization.
        """
        if start_career not in self.careers:
            return {"error": "Starting career not found"}

        # Get related careers (lateral moves)
        lateral_moves = self.get_related_careers(start_career, top_n=8)

        # Get potential progression paths
        progression_paths = self.find_career_paths(start_career, max_steps=3)

        # Calculate transition details for lateral moves
        lateral_transitions = []
        for career, similarity in lateral_moves:
            transition = self.calculate_transition_difficulty(start_career, career)
            lateral_transitions.append({
                "target_career": career,
                "similarity": similarity,
                "transition": transition
            })

        # Calculate details for progression paths
        path_details = []
        for path in progression_paths[:5]:  # Top 5 paths
            path_transitions = []
            total_difficulty = 0
            for i in range(len(path)-1):
                transition = self.calculate_transition_difficulty(path[i], path[i+1])
                path_transitions.append({
                    "from": path[i],
                    "to": path[i+1],
                    "transition": transition
                })
                total_difficulty += transition.get("difficulty_score", 0)

            avg_difficulty = total_difficulty / max(1, len(path_transitions))

            path_details.append({
                "path": path,
                "length": len(path),
                "average_difficulty": avg_difficulty,
                "transitions": path_transitions
            })

        return {
            "start_career": start_career,
            "lateral_moves": lateral_transitions,
            "progression_paths": path_details,
            "similarity_matrix_available": bool(self.similarity_matrix)
        }

def build_career_path_engine_from_dataframe(df: pd.DataFrame) -> CareerPathEngine:
    """
    Build a CareerPathEngine from the training dataframe.
    """
    # Identify skill columns
    feature_cols = [col for col in df.columns if col not in ['user_id', 'recommended_career', 'top_3_careers']]
    skill_cols = [col for col in feature_cols if col.startswith('skill_') and col != 'skill_gaps']
    skill_cols = [col for col in skill_cols if pd.api.types.is_numeric_dtype(df[col])]

    # Calculate career skill profiles
    skill_data = df[skill_cols]
    df_skills = skill_data.copy()
    df_skills['career'] = df['recommended_career'].values

    career_skill_profiles = {}
    for career in df_skills['career'].unique():
        career_data = df_skills[df_skills['career'] == career]
        avg_skills = career_data[skill_cols].mean().values
        career_skill_profiles[career] = avg_skills

    return CareerPathEngine(career_skill_profiles, skill_cols)

# Example usage and testing
if __name__ == "__main__":
    # This would normally be called with actual data
    print("Career Path Engine module loaded successfully")
    print("To use: engine = CareerPathEngine(career_skill_profiles, skill_columns)")