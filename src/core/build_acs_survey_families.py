#!/usr/bin/env python3
"""
Build ACS Survey Families Analysis

Analyzes overlap between ACS and other federal surveys to identify natural
survey families/clusters based on shared conceptual coverage.

Outputs:
- acs_survey_families.csv: Survey family assignments with overlap metrics
- acs_family_summary.csv: Family-level aggregates
- acs_overlap_ranked.csv: All surveys ranked by ACS overlap
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "output" / "visualizations"
OUTPUT_DIR = PROJECT_ROOT / "output" / "visualizations"

def load_acs_overlap_matrix():
    """Load the existing ACS overlap matrix."""
    df = pd.read_csv(DATA_DIR / "acs_overlap_matrix.csv", index_col=0)
    # Clean up column names
    df.columns = df.columns.str.strip()
    return df

def calculate_survey_overlap_scores(df):
    """Calculate total overlap scores for each survey with ACS."""
    # Sum questions across all subtopics for each survey
    survey_totals = df.sum(axis=0)
    
    # Count subtopics with any overlap
    subtopic_counts = (df > 0).sum(axis=0)
    
    # Create summary dataframe
    overlap_df = pd.DataFrame({
        'survey': survey_totals.index,
        'total_shared_questions': survey_totals.values,
        'subtopics_with_overlap': subtopic_counts.values
    })
    
    # Remove empty/unknown columns
    overlap_df = overlap_df[
        (overlap_df['total_shared_questions'] > 0) & 
        (~overlap_df['survey'].str.contains('Unnamed|Unknown', case=False, na=False))
    ].copy()
    
    # Sort by total overlap
    overlap_df = overlap_df.sort_values('total_shared_questions', ascending=False)
    
    return overlap_df

def identify_primary_overlap_domains(df, survey):
    """Identify the primary conceptual domains where a survey overlaps with ACS."""
    survey_col = df[survey]
    
    # Get subtopics with overlap, sorted by question count
    overlaps = survey_col[survey_col > 0].sort_values(ascending=False)
    
    if len(overlaps) == 0:
        return [], []
    
    # Extract topic from subtopic (format: "Topic > Subtopic")
    topics = [s.split(' > ')[0] for s in overlaps.index]
    
    # Get top 3 subtopics
    top_subtopics = list(overlaps.head(3).index)
    
    # Get dominant topic
    topic_counts = pd.Series(topics).value_counts()
    
    return top_subtopics, topic_counts

def assign_survey_families(overlap_df, matrix_df):
    """
    Assign surveys to ACS-centric families based on overlap patterns.
    
    Families:
    1. Economic Core: High overlap in income, employment, economic concepts
    2. Housing Core: High overlap in housing structure, costs, utilities
    3. Health/Social Core: High overlap in health insurance, disability, health status
    4. Demographics Extended: Moderate overlap primarily in demographics
    5. Specialized/Limited: Low overall overlap
    """
    
    families = []
    
    for _, row in overlap_df.iterrows():
        survey = row['survey']
        total = row['total_shared_questions']
        
        # Get the overlap pattern for this survey
        if survey not in matrix_df.columns:
            continue
            
        survey_overlap = matrix_df[survey]
        
        # Calculate domain-specific scores
        economic_subtopics = [s for s in survey_overlap.index if s.startswith('Economic')]
        housing_subtopics = [s for s in survey_overlap.index if s.startswith('Housing')]
        social_subtopics = [s for s in survey_overlap.index if s.startswith('Social')]
        demographic_subtopics = [s for s in survey_overlap.index if s.startswith('Demographic')]
        
        economic_score = survey_overlap[economic_subtopics].sum() if economic_subtopics else 0
        housing_score = survey_overlap[housing_subtopics].sum() if housing_subtopics else 0
        social_score = survey_overlap[social_subtopics].sum() if social_subtopics else 0
        demographic_score = survey_overlap[demographic_subtopics].sum() if demographic_subtopics else 0
        
        # Get top 3 subtopics for this survey
        top_subtopics = survey_overlap[survey_overlap > 0].nlargest(3)
        top_subtopic_str = "; ".join([f"{s.split(' > ')[1]} ({v})" for s, v in top_subtopics.items()])
        
        # Assign family based on dominant domain
        scores = {
            'Economic': economic_score,
            'Housing': housing_score,
            'Health/Social': social_score,
            'Demographic': demographic_score
        }
        
        max_domain = max(scores, key=scores.get)
        max_score = scores[max_domain]
        
        # Determine family with thresholds
        if total < 10:
            family = "5. Limited Overlap"
        elif max_domain == 'Economic' and economic_score >= 50:
            family = "1. ACS Economic Family"
        elif max_domain == 'Housing' and housing_score >= 30:
            family = "2. ACS Housing Family"
        elif max_domain == 'Health/Social' and social_score >= 30:
            family = "3. ACS Health/Social Family"
        elif total >= 30:
            # Mixed/moderate overlap
            if economic_score > housing_score and economic_score > social_score:
                family = "1. ACS Economic Family"
            elif housing_score > social_score:
                family = "2. ACS Housing Family"
            else:
                family = "3. ACS Health/Social Family"
        else:
            family = "4. Demographics Extended"
        
        families.append({
            'survey': survey,
            'family': family,
            'total_shared_questions': total,
            'subtopics_with_overlap': row['subtopics_with_overlap'],
            'economic_questions': economic_score,
            'housing_questions': housing_score,
            'social_questions': social_score,
            'demographic_questions': demographic_score,
            'top_overlap_areas': top_subtopic_str
        })
    
    return pd.DataFrame(families)

def create_family_summary(family_df):
    """Create summary statistics by family."""
    summary = family_df.groupby('family').agg({
        'survey': 'count',
        'total_shared_questions': ['sum', 'mean', 'min', 'max'],
        'subtopics_with_overlap': ['mean', 'max']
    }).round(1)
    
    summary.columns = ['n_surveys', 'total_questions', 'mean_questions', 
                       'min_questions', 'max_questions', 'mean_subtopics', 'max_subtopics']
    
    return summary.reset_index()

def main():
    print("Loading ACS overlap matrix...")
    matrix_df = load_acs_overlap_matrix()
    print(f"  Matrix shape: {matrix_df.shape}")
    print(f"  Subtopics: {len(matrix_df)}")
    print(f"  Surveys: {len(matrix_df.columns)}")
    
    print("\nCalculating survey overlap scores...")
    overlap_df = calculate_survey_overlap_scores(matrix_df)
    print(f"  Surveys with ACS overlap: {len(overlap_df)}")
    
    print("\nAssigning survey families...")
    family_df = assign_survey_families(overlap_df, matrix_df)
    
    print("\nCreating family summary...")
    summary_df = create_family_summary(family_df)
    
    # Save outputs
    print("\nSaving outputs...")
    
    # Ranked overlap
    overlap_df.to_csv(OUTPUT_DIR / "acs_overlap_ranked.csv", index=False)
    print(f"  Saved: acs_overlap_ranked.csv")
    
    # Family assignments
    family_df = family_df.sort_values(['family', 'total_shared_questions'], ascending=[True, False])
    family_df.to_csv(OUTPUT_DIR / "acs_survey_families.csv", index=False)
    print(f"  Saved: acs_survey_families.csv")
    
    # Family summary
    summary_df.to_csv(OUTPUT_DIR / "acs_family_summary.csv", index=False)
    print(f"  Saved: acs_family_summary.csv")
    
    # Print summary to console
    print("\n" + "="*70)
    print("ACS SURVEY FAMILIES SUMMARY")
    print("="*70)
    
    for family in sorted(family_df['family'].unique()):
        family_surveys = family_df[family_df['family'] == family]
        print(f"\n{family}")
        print("-" * 50)
        for _, row in family_surveys.iterrows():
            print(f"  {row['survey']}: {row['total_shared_questions']} questions across {row['subtopics_with_overlap']} subtopics")
            print(f"    Top areas: {row['top_overlap_areas']}")
    
    print("\n" + "="*70)
    print("FAMILY STATISTICS")
    print("="*70)
    print(summary_df.to_string(index=False))
    
    return family_df, summary_df

if __name__ == "__main__":
    family_df, summary_df = main()
