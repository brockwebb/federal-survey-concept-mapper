#!/usr/bin/env python3
"""
Explore normalized similarity distributions to inform threshold selection.
"""

import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 10)

print("="*70)
print("NORMALIZED SIMILARITY DISTRIBUTION ANALYSIS")
print("="*70)

# Load question embeddings
print("\n1. Loading question embeddings...")
embeddings_path = Path('../data/processed/embeddings/embeddings_with_metadata.pkl')

if not embeddings_path.exists():
    print("ERROR: embeddings_with_metadata.pkl not found")
    print("Please run notebook 02 first to generate embeddings.")
    exit(1)

with open(embeddings_path, 'rb') as f:
    data = pickle.load(f)

embeddings = data['embeddings']
question_ids = data['question_ids']
question_texts = data['question_texts']
print(f"   Loaded {len(embeddings):,} question embeddings")

# Load Census taxonomy
print("\n2. Loading Census taxonomy...")
taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
with open(taxonomy_path, 'r') as f:
    data = json.load(f)

taxonomy = data['taxonomy']
print(f"   Found {len(taxonomy)} topics")

# Extract concepts
concepts = []

# Add topic-level concepts
for topic_name in taxonomy.keys():
    concepts.append({
        'id': f"topic_{len(concepts)}",
        'level': 'topic',
        'topic': topic_name,
        'subtopic': None,
        'text': topic_name,
        'name': topic_name
    })

# Add subtopic-level concepts
for topic_name, subtopics in taxonomy.items():
    for subtopic_name in subtopics:
        concepts.append({
            'id': f"subtopic_{len(concepts)}",
            'level': 'subtopic',
            'topic': topic_name,
            'subtopic': subtopic_name,
            'text': f"{topic_name} - {subtopic_name}",
            'name': subtopic_name
        })

print(f"   Extracted {len(concepts)} concepts")

# Generate concept embeddings
print("\n3. Generating concept embeddings...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"   Using device: {device}")

model_name = 'roberta-large'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)
model.eval()

concept_embeddings = []
with torch.no_grad():
    for concept in tqdm(concepts, desc="   Embedding concepts"):
        inputs = tokenizer(
            concept['text'],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        ).to(device)
        
        outputs = model(**inputs)
        embeddings_batch = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings_batch.size()).float()
        sum_embeddings = torch.sum(embeddings_batch * mask_expanded, 1)
        sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
        mean_pooled = (sum_embeddings / sum_mask).cpu().numpy()[0]
        
        concept_embeddings.append(mean_pooled)

concept_embeddings = np.array(concept_embeddings)
print(f"   Generated {len(concept_embeddings)} concept embeddings")

# Compute similarity matrix
print("\n4. Computing similarity matrix...")
similarity_matrix = cosine_similarity(embeddings, concept_embeddings)
print(f"   Shape: {similarity_matrix.shape}")

# Normalize per question and analyze
print("\n5. Analyzing normalized distributions...")
n_questions = similarity_matrix.shape[0]
n_concepts = similarity_matrix.shape[1]

# For each question, normalize its similarity scores
normalized_distributions = []
top_k_stats = {k: [] for k in [1, 2, 3, 5, 10]}

for i in range(n_questions):
    scores = similarity_matrix[i]
    
    # Sort descending
    sorted_scores = np.sort(scores)[::-1]
    
    # Normalize to sum to 1
    normalized = sorted_scores / sorted_scores.sum()
    normalized_distributions.append(normalized)
    
    # Cumulative for this question
    cumulative = np.cumsum(normalized)
    
    # Track what % of mass is captured by top-k
    for k in top_k_stats.keys():
        if k <= len(cumulative):
            top_k_stats[k].append(cumulative[k-1])

# Convert to arrays
normalized_distributions = np.array(normalized_distributions)

print("\n" + "="*70)
print("RESULTS: How much similarity mass do top-K concepts capture?")
print("="*70)

for k in sorted(top_k_stats.keys()):
    values = np.array(top_k_stats[k])
    print(f"\nTop-{k} concepts:")
    print(f"  Mean:   {values.mean():.4f} ({values.mean()*100:.2f}%)")
    print(f"  Median: {np.median(values):.4f} ({np.median(values)*100:.2f}%)")
    print(f"  Std:    {values.std():.4f}")
    print(f"  Min:    {values.min():.4f} ({values.min()*100:.2f}%)")
    print(f"  Max:    {values.max():.4f} ({values.max()*100:.2f}%)")
    print(f"  25th percentile: {np.percentile(values, 25):.4f}")
    print(f"  75th percentile: {np.percentile(values, 75):.4f}")

# Visualize
print("\n6. Generating visualizations...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-1 distribution
axes[0, 0].hist(top_k_stats[1], bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].axvline(np.mean(top_k_stats[1]), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(top_k_stats[1]):.3f}')
axes[0, 0].set_xlabel('Proportion of Total Similarity')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Top-1 Concept Captures What % of Total Similarity?')
axes[0, 0].legend()

# Top-3 distribution
axes[0, 1].hist(top_k_stats[3], bins=50, edgecolor='black', alpha=0.7, color='orange')
axes[0, 1].axvline(np.mean(top_k_stats[3]), color='red', linestyle='--',
                   label=f'Mean: {np.mean(top_k_stats[3]):.3f}')
axes[0, 1].set_xlabel('Proportion of Total Similarity')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Top-3 Concepts Capture What % of Total Similarity?')
axes[0, 1].legend()

# Top-5 distribution
axes[1, 0].hist(top_k_stats[5], bins=50, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].axvline(np.mean(top_k_stats[5]), color='red', linestyle='--',
                   label=f'Mean: {np.mean(top_k_stats[5]):.3f}')
axes[1, 0].set_xlabel('Proportion of Total Similarity')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Top-5 Concepts Capture What % of Total Similarity?')
axes[1, 0].legend()

# Comparison boxplot
data_for_box = [top_k_stats[k] for k in [1, 2, 3, 5, 10]]
axes[1, 1].boxplot(data_for_box, labels=['Top-1', 'Top-2', 'Top-3', 'Top-5', 'Top-10'])
axes[1, 1].set_ylabel('Proportion of Total Similarity')
axes[1, 1].set_title('Cumulative Similarity Mass by Top-K')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
output_path = Path('../reports/figures/normalized_similarity_distributions.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"   Saved visualization to {output_path}")

# Detailed analysis: How many concepts needed to reach thresholds?
print("\n" + "="*70)
print("THRESHOLD ANALYSIS: How many concepts needed to reach X% of mass?")
print("="*70)

thresholds = [0.80, 0.85, 0.90, 0.95, 0.975, 0.99]

for threshold in thresholds:
    n_concepts_needed = []
    for i in range(n_questions):
        cumulative = np.cumsum(normalized_distributions[i])
        n_needed = np.searchsorted(cumulative, threshold) + 1
        n_concepts_needed.append(min(n_needed, n_concepts))
    
    n_concepts_needed = np.array(n_concepts_needed)
    print(f"\nTo capture {threshold*100:.1f}% of similarity mass:")
    print(f"  Mean concepts needed:   {n_concepts_needed.mean():.2f}")
    print(f"  Median concepts needed: {np.median(n_concepts_needed):.0f}")
    print(f"  Min:  {n_concepts_needed.min()}")
    print(f"  Max:  {n_concepts_needed.max()}")
    print(f"  Std:  {n_concepts_needed.std():.2f}")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)
print("\nBased on the distributions above, choose a threshold that:")
print("1. Captures 'enough' similarity mass (90-95% seems reasonable)")
print("2. Doesn't require too many concepts per question (3-5 is manageable)")
print("3. Balances signal vs noise")
print("\nReview the plots and statistics, then update notebook 04 accordingly.")
print("\nDone!")
