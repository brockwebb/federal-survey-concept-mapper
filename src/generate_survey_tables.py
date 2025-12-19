#!/usr/bin/env python3
"""
Generate survey analysis tables for federal decision-makers.

1. Survey Profile Table - Overview of each survey's coverage
2. Consolidation Candidates - Surveys with high concept overlap
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter

# Configuration
FINAL_DIR = Path('../output/final')
VIZ_DIR = Path('../output/visualizations')
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load master dataset and matrix."""
    master = pd.read_csv(FINAL_DIR / 'master_dataset.csv')
    matrix = pd.read_csv(FINAL_DIR / 'survey_concept_matrix.csv', index_col=0)
    return master, matrix

def create_survey_profile_table(master_df):
    """
    Survey Profile Table - Overview of coverage and key concepts.
    """
    print("\n1. SURVEY PROFILE TABLE")
    print("="*70)
    
    # Filter valid categorizations
    valid = master_df[
        (master_df['final_topic'].notna()) & 
        (master_df['final_topic'] != 'Unknown')
    ].copy()
    
    profiles = []
    
    for survey in sorted(valid['primary_survey'].unique()):
        survey_data = valid[valid['primary_survey'] == survey]
        
        # Primary topic (most common)
        primary_topic = survey_data['final_topic'].mode()[0] if len(survey_data) > 0 else 'Unknown'
        
        # Topic distribution
        topic_dist = survey_data['final_topic'].value_counts()
        topic_pct = (topic_dist / len(survey_data) * 100).round(1)
        
        # Top 5 concepts
        survey_data['concept'] = survey_data['final_topic'] + '.' + survey_data['final_subtopic']
        top_concepts = survey_data['concept'].value_counts().head(5)
        top_concepts_str = ', '.join([f"{c.split('.')[1]} ({v})" for c, v in top_concepts.items()])
        
        # Topic coverage string
        topic_coverage = ', '.join([f"{t} ({p}%)" for t, p in topic_pct.head(3).items()])
        
        # Unique concepts
        unique_concepts = survey_data['concept'].nunique()
        
        profiles.append({
            'Survey': survey,
            'Questions': len(survey_data),
            'Primary_Topic': primary_topic,
            'Topic_Coverage': topic_coverage,
            'Unique_Concepts': unique_concepts,
            'Top_5_Concepts': top_concepts_str
        })
    
    profiles_df = pd.DataFrame(profiles).sort_values('Questions', ascending=False)
    
    # Save full table
    profiles_df.to_csv(VIZ_DIR / 'survey_profiles.csv', index=False)
    print(f"   ✓ Saved: survey_profiles.csv")
    
    # Print summary
    print(f"\n   Total surveys analyzed: {len(profiles_df)}")
    print(f"   Mean questions per survey: {profiles_df['Questions'].mean():.0f}")
    print(f"   Median questions per survey: {profiles_df['Questions'].median():.0f}")
    
    print(f"\n   Top 10 surveys by question count:")
    for _, row in profiles_df.head(10).iterrows():
        print(f"     {row['Survey']}: {row['Questions']} questions, {row['Primary_Topic']}")
    
    return profiles_df

def calculate_concept_overlap(matrix_df):
    """
    Calculate pairwise concept overlap between surveys.
    Returns similarity matrix and overlap details.
    """
    # Convert to binary (has concept or not)
    binary_matrix = (matrix_df > 0).astype(int)
    
    # Calculate Jaccard similarity for each pair
    surveys = matrix_df.index.tolist()
    n_surveys = len(surveys)
    
    similarity_matrix = np.zeros((n_surveys, n_surveys))
    
    for i, survey1 in enumerate(surveys):
        for j, survey2 in enumerate(surveys):
            if i == j:
                similarity_matrix[i, j] = 1.0
            elif i < j:
                # Jaccard: intersection / union
                concepts1 = set(binary_matrix.loc[survey1][binary_matrix.loc[survey1] == 1].index)
                concepts2 = set(binary_matrix.loc[survey2][binary_matrix.loc[survey2] == 1].index)
                
                if len(concepts1) == 0 and len(concepts2) == 0:
                    similarity = 0
                else:
                    intersection = len(concepts1 & concepts2)
                    union = len(concepts1 | concepts2)
                    similarity = intersection / union if union > 0 else 0
                
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity
    
    similarity_df = pd.DataFrame(similarity_matrix, index=surveys, columns=surveys)
    
    return similarity_df

def create_consolidation_candidates(matrix_df, master_df, threshold=0.50):
    """
    Identify survey pairs with high concept overlap - consolidation candidates.
    """
    print("\n2. CONSOLIDATION CANDIDATES")
    print("="*70)
    
    print(f"   Calculating concept overlap (Jaccard similarity)...")
    similarity_df = calculate_concept_overlap(matrix_df)
    
    # Find high-overlap pairs
    candidates = []
    
    surveys = similarity_df.index.tolist()
    for i, survey1 in enumerate(surveys):
        for j, survey2 in enumerate(surveys):
            if i < j:  # Only upper triangle
                similarity = similarity_df.loc[survey1, survey2]
                
                if similarity >= threshold:
                    # Get shared concepts
                    survey1_concepts = set(matrix_df.columns[matrix_df.loc[survey1] > 0])
                    survey2_concepts = set(matrix_df.columns[matrix_df.loc[survey2] > 0])
                    shared = survey1_concepts & survey2_concepts
                    
                    # Get question counts
                    valid = master_df[
                        (master_df['final_topic'].notna()) & 
                        (master_df['final_topic'] != 'Unknown')
                    ]
                    q1 = len(valid[valid['primary_survey'] == survey1])
                    q2 = len(valid[valid['primary_survey'] == survey2])
                    
                    candidates.append({
                        'Survey_1': survey1,
                        'Survey_2': survey2,
                        'Overlap_Pct': round(similarity * 100, 1),
                        'Shared_Concepts': len(shared),
                        'Survey_1_Questions': q1,
                        'Survey_2_Questions': q2,
                        'Total_Questions': q1 + q2,
                        'Top_Shared_Concepts': ', '.join(sorted(list(shared))[:5])
                    })
    
    candidates_df = pd.DataFrame(candidates).sort_values('Overlap_Pct', ascending=False)
    
    # Save
    candidates_df.to_csv(VIZ_DIR / 'consolidation_candidates.csv', index=False)
    print(f"   ✓ Saved: consolidation_candidates.csv")
    
    print(f"\n   Found {len(candidates_df)} survey pairs with ≥{threshold*100}% overlap")
    
    if len(candidates_df) > 0:
        print(f"\n   Top 10 consolidation opportunities:")
        for idx, row in candidates_df.head(10).iterrows():
            print(f"     {row['Survey_1']} ↔ {row['Survey_2']}")
            print(f"       Overlap: {row['Overlap_Pct']}% ({row['Shared_Concepts']} shared concepts)")
            print(f"       Combined: {row['Total_Questions']} questions")
            print()
    else:
        print(f"\n   No survey pairs found with ≥{threshold*100}% overlap")
        print(f"   Try lowering threshold (currently {threshold})")
    
    # Save similarity matrix
    similarity_df.to_csv(VIZ_DIR / 'survey_similarity_matrix.csv')
    print(f"   ✓ Saved: survey_similarity_matrix.csv")
    
    return candidates_df, similarity_df

def create_topic_grouping_table(master_df):
    """
    Group surveys by primary topic area.
    """
    print("\n3. SURVEYS BY TOPIC AREA")
    print("="*70)
    
    # Filter valid
    valid = master_df[
        (master_df['final_topic'].notna()) & 
        (master_df['final_topic'] != 'Unknown')
    ].copy()
    
    # Calculate primary topic for each survey
    survey_topics = []
    
    for survey in sorted(valid['primary_survey'].unique()):
        survey_data = valid[valid['primary_survey'] == survey]
        
        # Get topic distribution
        topic_counts = survey_data['final_topic'].value_counts()
        primary_topic = topic_counts.index[0]
        primary_pct = (topic_counts.iloc[0] / len(survey_data) * 100)
        
        survey_topics.append({
            'Survey': survey,
            'Primary_Topic': primary_topic,
            'Primary_Topic_Pct': round(primary_pct, 1),
            'Question_Count': len(survey_data),
            'Concept_Count': survey_data['final_subtopic'].nunique()
        })
    
    topic_df = pd.DataFrame(survey_topics).sort_values(['Primary_Topic', 'Question_Count'], ascending=[True, False])
    
    # Save
    topic_df.to_csv(VIZ_DIR / 'surveys_by_topic.csv', index=False)
    print(f"   ✓ Saved: surveys_by_topic.csv")
    
    # Print grouped view
    print(f"\n   Survey Families by Topic:")
    for topic in sorted(topic_df['Primary_Topic'].unique()):
        topic_surveys = topic_df[topic_df['Primary_Topic'] == topic]
        print(f"\n   {topic} ({len(topic_surveys)} surveys):")
        for _, row in topic_surveys.head(10).iterrows():
            print(f"     • {row['Survey']}: {row['Question_Count']} questions ({row['Primary_Topic_Pct']}% {topic})")
        if len(topic_surveys) > 10:
            print(f"     ... and {len(topic_surveys)-10} more")
    
    return topic_df

def main():
    print("="*70)
    print("SURVEY ANALYSIS TABLES FOR DECISION-MAKERS")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    master_df, matrix_df = load_data()
    print(f"   Master dataset: {len(master_df)} questions")
    print(f"   Matrix: {matrix_df.shape[0]} surveys × {matrix_df.shape[1]} concepts")
    
    # Generate tables
    profiles_df = create_survey_profile_table(master_df)
    candidates_df, similarity_df = create_consolidation_candidates(matrix_df, master_df, threshold=0.50)
    topic_df = create_topic_grouping_table(master_df)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nOutputs saved to: {VIZ_DIR}")
    print("\nGenerated:")
    print("  - survey_profiles.csv - Complete survey overview")
    print("  - consolidation_candidates.csv - High-overlap survey pairs")
    print("  - survey_similarity_matrix.csv - Pairwise similarity scores")
    print("  - surveys_by_topic.csv - Surveys grouped by primary topic")
    print("\nThese tables are ready for stakeholder reports and decision memos!")

if __name__ == '__main__':
    main()
