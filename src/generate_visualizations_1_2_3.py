#!/usr/bin/env python3
"""
Generate visualizations for federal survey concept mapping analysis.

Visualization 1: Coverage Gap Analysis (Treemap)
Visualization 2: Survey × Concept Heatmap with Hierarchical Clustering
Visualization 3: Sankey Diagram (Surveys → Topics → Subtopics)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

# Configuration
FINAL_DIR = Path('../output/final')
VIZ_DIR = Path('../output/visualizations')
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load master dataset and matrix."""
    master = pd.read_csv(FINAL_DIR / 'master_dataset.csv')
    matrix = pd.read_csv(FINAL_DIR / 'survey_concept_matrix.csv', index_col=0)
    return master, matrix

def viz1_coverage_gap_treemap(master_df):
    """
    Visualization 1: Coverage Gap Analysis
    Treemap showing question count per subtopic, colored by topic.
    Reveals over/under-sampled concepts.
    """
    print("\n1. COVERAGE GAP ANALYSIS (Treemap)")
    print("="*70)
    
    # Filter to successfully categorized
    valid = master_df[master_df['final_topic'].notna()].copy()
    
    # Count by topic and subtopic
    coverage = valid.groupby(['final_topic', 'final_subtopic']).size().reset_index(name='count')
    coverage = coverage.sort_values('count', ascending=False)
    
    print(f"   Total concepts covered: {len(coverage)}")
    print(f"   Questions analyzed: {len(valid)}")
    
    # Create treemap
    fig = px.treemap(
        coverage,
        path=[px.Constant("Federal Surveys"), 'final_topic', 'final_subtopic'],
        values='count',
        color='final_topic',
        color_discrete_sequence=px.colors.qualitative.Set3,
        title='Federal Survey Concept Coverage - Question Distribution Across Census Taxonomy',
        hover_data={'count': True}
    )
    
    fig.update_traces(
        textposition="middle center",
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>Questions: %{value}<br><extra></extra>'
    )
    
    fig.update_layout(
        width=1600,
        height=1000,
        font=dict(size=14),
        margin=dict(t=60, l=25, r=25, b=25)
    )
    
    # Save
    fig.write_html(VIZ_DIR / '1_coverage_treemap.html')
    print(f"   ✓ Saved: 1_coverage_treemap.html")
    
    # Generate gap analysis
    print("\n   Coverage Analysis:")
    print(f"   Top 5 most-covered concepts:")
    for idx, row in coverage.head(5).iterrows():
        print(f"     {row['final_topic']}.{row['final_subtopic']}: {row['count']} questions")
    
    print(f"\n   Bottom 5 least-covered concepts:")
    for idx, row in coverage.tail(5).iterrows():
        print(f"     {row['final_topic']}.{row['final_subtopic']}: {row['count']} questions")
    
    # Save coverage stats
    coverage.to_csv(VIZ_DIR / '1_coverage_analysis.csv', index=False)
    print(f"   ✓ Saved: 1_coverage_analysis.csv")

def viz2_clustered_heatmap(matrix_df):
    """
    Visualization 2: Survey × Concept Heatmap with Hierarchical Clustering
    Shows which surveys are similar based on concept coverage.
    """
    print("\n2. CLUSTERED HEATMAP (Survey × Concept)")
    print("="*70)
    
    # Filter to concepts that appear in at least 3 surveys (reduce noise)
    concept_counts = (matrix_df > 0).sum(axis=0)
    frequent_concepts = concept_counts[concept_counts >= 3].index
    matrix_filtered = matrix_df[frequent_concepts]
    
    # Filter to surveys with at least 10 questions
    survey_counts = matrix_filtered.sum(axis=1)
    active_surveys = survey_counts[survey_counts >= 10].index
    matrix_filtered = matrix_filtered.loc[active_surveys]
    
    print(f"   Surveys: {len(matrix_filtered)}")
    print(f"   Concepts: {len(matrix_filtered.columns)}")
    print(f"   (Filtered to concepts in 3+ surveys, surveys with 10+ questions)")
    
    # Hierarchical clustering on surveys
    if len(matrix_filtered) > 1:
        # Normalize by row (survey) to compare patterns not magnitudes
        matrix_norm = matrix_filtered.div(matrix_filtered.sum(axis=1), axis=0).fillna(0)
        
        # Cluster surveys
        survey_linkage = linkage(matrix_norm, method='ward')
        survey_dendro = dendrogram(survey_linkage, no_plot=True)
        survey_order = survey_dendro['leaves']
        
        # Cluster concepts
        concept_linkage = linkage(matrix_norm.T, method='ward')
        concept_dendro = dendrogram(concept_linkage, no_plot=True)
        concept_order = concept_dendro['leaves']
        
        # Reorder matrix
        matrix_ordered = matrix_filtered.iloc[survey_order, concept_order]
    else:
        matrix_ordered = matrix_filtered
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(20, 14))
    
    # Use log scale for better visualization (many zeros)
    matrix_log = np.log1p(matrix_ordered)
    
    sns.heatmap(
        matrix_log,
        cmap='YlOrRd',
        cbar_kws={'label': 'Question Count (log scale)'},
        xticklabels=True,
        yticklabels=True,
        ax=ax,
        linewidths=0
    )
    
    ax.set_xlabel('Census Concept (Subtopic)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Federal Survey', fontsize=12, fontweight='bold')
    ax.set_title('Survey Similarity Based on Concept Coverage\n(Hierarchically Clustered)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='right', fontsize=8)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)
    
    plt.tight_layout()
    plt.savefig(VIZ_DIR / '2_clustered_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: 2_clustered_heatmap.png")
    plt.close()
    
    # Identify survey clusters
    if len(matrix_filtered) > 1:
        from scipy.cluster.hierarchy import fcluster
        cluster_labels = fcluster(survey_linkage, t=5, criterion='maxclust')
        
        clusters = pd.DataFrame({
            'survey': matrix_filtered.index,
            'cluster': cluster_labels
        })
        
        print(f"\n   Identified {clusters['cluster'].nunique()} survey clusters:")
        for cluster_id in sorted(clusters['cluster'].unique()):
            cluster_surveys = clusters[clusters['cluster'] == cluster_id]['survey'].tolist()
            print(f"\n   Cluster {cluster_id} ({len(cluster_surveys)} surveys):")
            for survey in cluster_surveys[:5]:  # Show first 5
                print(f"     - {survey}")
            if len(cluster_surveys) > 5:
                print(f"     ... and {len(cluster_surveys)-5} more")
        
        clusters.to_csv(VIZ_DIR / '2_survey_clusters.csv', index=False)
        print(f"\n   ✓ Saved: 2_survey_clusters.csv")

def viz3_sankey_diagram(master_df):
    """
    Visualization 3: Sankey Diagram
    Flow from Surveys → Topics → Subtopics
    """
    print("\n3. SANKEY DIAGRAM (Surveys → Topics → Subtopics)")
    print("="*70)
    
    # Filter valid
    valid = master_df[master_df['final_topic'].notna()].copy()
    
    # For visualization, limit to top 15 surveys by question count
    top_surveys = valid['primary_survey'].value_counts().head(15).index
    valid_filtered = valid[valid['primary_survey'].isin(top_surveys)].copy()
    
    print(f"   Using top 15 surveys (for readability)")
    print(f"   Questions: {len(valid_filtered)}")
    
    # Create flows
    # Survey → Topic
    survey_topic = valid_filtered.groupby(['primary_survey', 'final_topic']).size().reset_index(name='count')
    
    # Topic → Subtopic (limit to top 30 subtopics per topic for readability)
    topic_subtopic_list = []
    for topic in valid_filtered['final_topic'].unique():
        topic_data = valid_filtered[valid_filtered['final_topic'] == topic]
        top_subtopics = topic_data['final_subtopic'].value_counts().head(30).index
        topic_sub = topic_data[topic_data['final_subtopic'].isin(top_subtopics)]
        topic_subtopic_list.append(
            topic_sub.groupby(['final_topic', 'final_subtopic']).size().reset_index(name='count')
        )
    topic_subtopic = pd.concat(topic_subtopic_list)
    
    # Create node labels and indices
    all_surveys = survey_topic['primary_survey'].unique().tolist()
    all_topics = valid_filtered['final_topic'].unique().tolist()
    all_subtopics = topic_subtopic['final_subtopic'].unique().tolist()
    
    node_labels = all_surveys + all_topics + all_subtopics
    
    # Create index mappings
    survey_idx = {s: i for i, s in enumerate(all_surveys)}
    topic_idx = {t: i + len(all_surveys) for i, t in enumerate(all_topics)}
    subtopic_idx = {s: i + len(all_surveys) + len(all_topics) for i, s in enumerate(all_subtopics)}
    
    # Build links
    sources = []
    targets = []
    values = []
    
    # Survey → Topic links
    for _, row in survey_topic.iterrows():
        sources.append(survey_idx[row['primary_survey']])
        targets.append(topic_idx[row['final_topic']])
        values.append(row['count'])
    
    # Topic → Subtopic links
    for _, row in topic_subtopic.iterrows():
        sources.append(topic_idx[row['final_topic']])
        targets.append(subtopic_idx[row['final_subtopic']])
        values.append(row['count'])
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color="lightblue"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(0,0,0,0.2)"
        )
    )])
    
    fig.update_layout(
        title_text="Federal Survey Question Flow: Surveys → Topics → Subtopics<br>(Top 15 Surveys, Top 30 Subtopics per Topic)",
        font_size=12,
        width=1600,
        height=1000
    )
    
    fig.write_html(VIZ_DIR / '3_sankey_flow.html')
    print(f"   ✓ Saved: 3_sankey_flow.html")

def main():
    print("="*70)
    print("VISUALIZATION GENERATION")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    master_df, matrix_df = load_data()
    print(f"   Master dataset: {len(master_df)} questions")
    print(f"   Concept matrix: {matrix_df.shape[0]} surveys × {matrix_df.shape[1]} concepts")
    
    # Generate visualizations
    viz1_coverage_gap_treemap(master_df)
    viz2_clustered_heatmap(matrix_df)
    viz3_sankey_diagram(master_df)
    
    print("\n" + "="*70)
    print("VISUALIZATIONS COMPLETE!")
    print("="*70)
    print(f"\nOutputs saved to: {VIZ_DIR}")
    print("\nGenerated:")
    print("  1. 1_coverage_treemap.html - Interactive treemap of concept coverage")
    print("  2. 2_clustered_heatmap.png - Survey similarity heatmap")
    print("  3. 3_sankey_flow.html - Interactive flow diagram")
    print("\nOpen the HTML files in your browser for interactive exploration!")

if __name__ == '__main__':
    main()
