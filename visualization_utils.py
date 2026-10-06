# visualization_utils.py
"""
Visualization utilities for the AI Career Recommendation System.
Provides functions to generate charts and graphs for various aspects of the system.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import io
import base64
from typing import Dict, List, Tuple, Any, Optional
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
import networkx as nx

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_skill_radar_chart(skills_data: List[Dict[str, Any]],
                           title: str = "Skills Profile") -> str:
    """
    Create a radar chart for skills visualization.

    Args:
        skills_data: List of dicts with 'skill', 'user_level', 'career_average' keys
        title: Chart title

    Returns:
        Base64 encoded PNG image
    """
    # Prepare data
    skills = [item['skill'] for item in skills_data]
    user_levels = [item['user_level'] for item in skills_data]
    career_levels = [item['career_average'] for item in skills_data]

    # Number of variables
    N = len(skills)

    # Compute angle for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the circle

    # Add the first value again to close the circle
    user_levels += user_levels[:1]
    career_levels += career_levels[:1]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # Plot user data
    ax.plot(angles, user_levels, 'o-', linewidth=2, label='Your Level', color='#1f77b4')
    ax.fill(angles, user_levels, alpha=0.25, color='#1f77b4')

    # Plot career data
    ax.plot(angles, career_levels, 'o-', linewidth=2, label='Career Requirement', color='#ff7f0e')
    ax.fill(angles, career_levels, alpha=0.25, color='#ff7f0e')

    # Fix axis to go in the right order and start at 12 o'clock
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw axis lines for each angle and label
    ax.set_thetagrids(np.degrees(angles[:-1]), skills)

    # Set y-axis limits
    ax.set_ylim(0, 5)

    # Add title
    plt.title(title, size=20, y=1.08)

    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

    # Save to base64 string
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def create_skill_gap_bar_chart(skill_gaps: List[Dict[str, Any]],
                             top_n: int = 10,
                             title: str = "Skill Gap Analysis") -> str:
    """
    Create a horizontal bar chart showing skill gaps.

    Args:
        skill_gaps: List of dicts with skill, gap, user_level, career_average
        top_n: Number of top gaps to show
        title: Chart title

    Returns:
        Base64 encoded PNG image
    """
    # Sort by gap (absolute value) and take top N
    sorted_gaps = sorted(skill_gaps, key=lambda x: abs(x['gap']), reverse=True)[:top_n]

    # Separate positive (deficits) and negative (surplus) gaps
    deficits = [g for g in sorted_gaps if g['gap'] > 0]
    surplus = [g for g in sorted_gaps if g['gap'] < 0]

    # Prepare data for plotting
    skills = [g['skill'] for g in deficits + surplus]
    gaps = [g['gap'] for g in deficits + surplus]
    colors = ['#ff7f0e' if g > 0 else '#2ca02c' for g in gaps]  # Orange for deficits, green for surplus

    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    y_pos = np.arange(len(skills))
    bars = ax.barh(y_pos, gaps, color=colors, alpha=0.8)

    # Customize the chart
    ax.set_yticks(y_pos)
    ax.set_yticklabels(skills)
    ax.set_xlabel('Skill Gap (Career Average - Your Level)')
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    # Add value labels on bars
    for i, (bar, gap) in enumerate(zip(bars, gaps)):
        width = bar.get_width()
        label_x = width + (0.05 if width >= 0 else -0.05)
        ax.text(label_x, bar.get_y() + bar.get_height()/2,
                f'{gap:.1f}', ha='left' if width >= 0 else 'right',
                va='center', fontweight='bold')

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#ff7f0e', alpha=0.8, label='Skill to Develop (Gap > 0)'),
        Patch(facecolor='#2ca02c', alpha=0.8, label='Strength (Gap < 0)')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()

    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def create_career_path_graph(career_paths: List[List[str]],
                           similarity_data: Dict[str, Dict[str, float]],
                           title: str = "Career Pathways") -> str:
    """
    Create a graph visualization of career paths.

    Args:
        career_paths: List of career paths (each path is a list of careers)
        similarity_data: Dictionary of career similarities
        title: Graph title

    Returns:
        Base64 encoded PNG image
    """
    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes and edges from paths
    for path in career_paths:
        for i in range(len(path)):
            G.add_node(path[i])
            if i < len(path) - 1:
                G.add_edge(path[i], path[i+1])

    # Add additional similarity edges if not already present
    for career1, similarities in similarity_data.items():
        for career2, similarity in similarities.items():
            if similarity > 0.3 and not G.has_edge(career1, career2) and not G.has_edge(career2, career1):
                # Add undirected edge for similarity
                G.add_edge(career1, career2, weight=similarity, type='similarity')

    # Create the plot
    plt.figure(figsize=(14, 10))

    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=3, iterations=50)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue',
                          node_size=3000, alpha=0.9)

    # Draw edges - different styles for path vs similarity
    path_edges = []
    similarity_edges = []

    for u, v, data in G.edges(data=True):
        if data.get('type') == 'similarity':
            similarity_edges.append((u, v))
        else:
            path_edges.append((u, v))

    # Draw path edges (solid lines)
    nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                          edge_color='blue', width=2, alpha=0.7,
                          arrows=True, arrowsize=20)

    # Draw similarity edges (dashed lines)
    nx.draw_networkx_edges(G, pos, edgelist=similarity_edges,
                          edge_color='gray', width=1, alpha=0.5,
                          style='dashed')

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    # Add edge labels for similarity weights
    similarity_edge_labels = {}
    for u, v, data in G.edges(data=True):
        if data.get('type') == 'similarity':
            similarity_edge_labels[(u, v)] = f"{data['weight']:.2f}"

    nx.draw_networkx_edge_labels(G, pos, similarity_edge_labels,
                                font_size=8, alpha=0.7)

    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()

    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def create_skill_decay_chart(skill_history: List[Dict[str, Any]],
                           skill_name: str,
                           title: str = "Skill Decay Over Time") -> str:
    """
    Create a line chart showing skill decay over time.

    Args:
        skill_history: List of dicts with 'date' and 'skill_level' keys
        skill_name: Name of the skill being tracked
        title: Chart title

    Returns:
        Base64 encoded PNG image
    """
    if not skill_history:
        # Create a placeholder chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No skill history data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_title(title)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{image_base64}"

    # Sort by date
    sorted_history = sorted(skill_history, key=lambda x: x['date'])
    dates = [item['date'] for item in sorted_history]
    levels = [item['skill_level'] for item in sorted_history]

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the skill level over time
    ax.plot(dates, levels, marker='o', linewidth=2, markersize=6, color='#1f77b4')

    # Add a trend line (linear regression)
    if len(dates) > 1:
        # Convert dates to numeric for regression
        date_nums = np.array([(d - datetime.min).days for d in dates])
        z = np.polyfit(date_nums, levels, 1)
        p = np.poly1d(z)
        plt.plot(dates, p(date_nums), "--", color='red', alpha=0.8, label='Trend')

    # Customize the chart
    ax.set_xlabel('Date')
    ax.set_ylabel('Skill Level (0-5)')
    ax.set_title(f'{title}: {skill_name}', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 5)

    # Format dates on x-axis
    plt.xticks(rotation=45)

    # Add legend if we have a trend line
    if len(dates) > 1:
        plt.legend()

    plt.tight_layout()

    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def create_market_data_comparison_chart(market_data: Dict[str, Dict[str, Any]],
                                      title: str = "Market Data Comparison") -> str:
    """
    Create a grouped bar chart comparing market data across careers.

    Args:
        market_data: Dictionary mapping career names to market data dicts
        title: Chart title

    Returns:
        Base64 encoded PNG image
    """
    if not market_data:
        # Create a placeholder chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No market data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_title(title)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{image_base64}"

    # Prepare data
    careers = list(market_data.keys())
    metrics = ['median_salary', 'job_growth_rate', 'demand_score', 'remote_friendly']
    metric_labels = ['Median Salary ($)', 'Job Growth Rate', 'Demand Score', 'Remote Friendly']

    # Normalize data for comparison (0-1 scale)
    normalized_data = {}
    for metric in metrics:
        values = [market_data[career].get(metric, 0) for career in careers]
        if metric == 'median_salary':
            # Special handling for salary - normalize to 0-1 range assuming 40k-200k
            normalized = [(max(0, min(1, (v - 40000) / 160000))) for v in values]
        elif metric == 'job_growth_rate':
            # Normalize growth rate assuming 0-50% range
            normalized = [(max(0, min(1, v / 0.5))) for v in values]
        else:
            # Already 0-1 scale
            normalized = [max(0, min(1, v)) for v in values]
        normalized_data[metric] = normalized

    # Set up the bar chart
    x = np.arange(len(careers))
    width = 0.2
    multiplier = 0

    fig, ax = plt.subplots(figsize=(14, 8))

    # Colors for each metric
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # Plot each metric
    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        offset = width * multiplier
        rects = ax.bar(x + offset, normalized_data[metric], width,
                      label=label, color=colors[i])
        autolabel(ax, rects, fmt=lambda x: f'{x:.2f}' if i > 0 else f'${int(x*160000+40000):,}')
        multiplier += 1

    # Customize the chart
    ax.set_xlabel('Careers')
    ax.set_ylabel('Normalized Score (0-1)')
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xticks(x + width * (len(metrics)-1) / 2)
    ax.set_xticklabels(careers, rotation=45, ha='right')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def autolabel(ax, rects, fmt=lambda x: f'{x}'):
    """Attach a text label above each bar displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(fmt(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

def create_progress_tracking_chart(assessment_history: List[Dict[str, Any]],
                                 skill_name: str,
                                 title: str = "Skill Progress Tracking") -> str:
    """
    Create a line chart showing skill progress over multiple assessments.

    Args:
        assessment_history: List of assessment dicts with timestamp and skill data
        skill_name: Name of the skill to track
        title: Chart title

    Returns:
        Base64 encoded PNG image
    """
    if not assessment_history:
        # Create a placeholder chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No assessment history available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_title(title)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{image_base64}"

    # Sort by timestamp
    sorted_history = sorted(assessment_history, key=lambda x: x.get('timestamp', ''))

    # Extract dates and skill levels (this would need to be adapted based on actual data structure)
    dates = []
    levels = []

    for assessment in sorted_history:
        timestamp = assessment.get('timestamp')
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                dates.append(date)
            except:
                continue

        # Extract skill level from skill_gap_analysis or similar
        # This is simplified - in reality, you'd need to parse the assessment data
        skill_level = 3.0  # Placeholder
        levels.append(skill_level)

    if not dates:
        # Create a placeholder chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No valid date data in assessment history',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_title(title)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{image_base64}"

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the skill level over time
    ax.plot(dates, levels, marker='o', linewidth=2, markersize=6, color='#2ca02c')

    # Add target line (example: target level of 4.0)
    target_level = 4.0
    ax.axhline(y=target_level, color='red', linestyle='--', alpha=0.7, label=f'Target Level ({target_level})')

    # Customize the chart
    ax.set_xlabel('Assessment Date')
    ax.set_ylabel('Skill Level')
    ax.set_title(f'{title}: {skill_name}', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 5)

    # Format dates on x-axis
    plt.xticks(rotation=45)

    # Add legend
    plt.legend()

    plt.tight_layout()

    # Save to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{image_base64}"

# Export functions for easy importing
__all__ = [
    'create_skill_radar_chart',
    'create_skill_gap_bar_chart',
    'create_career_path_graph',
    'create_skill_decay_chart',
    'create_market_data_comparison_chart',
    'create_progress_tracking_chart'
]