#!/usr/bin/env python3
"""
Explore normalized similarity distributions with survey context added.

This version adds survey name to questions to provide context before matching
to Census taxonomy concepts.
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
print("WITH SURVEY CONTEXT")
print("="*70)

# Load question embeddings with metadata
print("\n1. Loading question embeddings and metadata...")
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

# Load survey names from original data
print("   Loading survey names from original data...")
df = pd.read_csv('../data/raw/PublicSurveyQuestionsMap.csv')

# Create mapping from question to surveys
question_to_surveys = {}
for idx, row in df.iterrows():
    question = row['Question']
    # Get all survey columns (all except 'Question')
    surveys = [col for col in df.columns if col != 'Question' and pd.notna(row[col])]
    question_to_surveys[question] = surveys

# Map question_texts to their surveys (use first survey if multiple)
survey_names = []
for q_text in question_texts:
    surveys = question_to_surveys.get(q_text, ['Unknown'])
    survey_names.append(surveys[0] if surveys else 'Unknown')

print(f"   Mapped to {len(set(survey_names))} unique surveys")

# Load Census taxonomy
print("\n2. Loading Census taxonomy...")
taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
with open(taxonomy_path, 'r') as f:
    taxonomy_data = json.load(f)

taxonomy = taxonomy_data['taxonomy']
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

# Regenerate question embeddings WITH survey context
print("\n3. Regenerating question embeddings with survey context...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"   Using device: {device}")

model_name = 'roberta-large'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)
model.eval()

print("   Embedding questions with survey context...")
contextualized_embeddings = []
with torch.no_grad():
    for survey, question in tqdm(zip(survey_names, question_texts), 
                                  total=len(question_texts),
                                  desc="   Processing"):
        # Add survey context to question
        contextualized_text = f"Survey: {survey}. Question: {question}"
        
        inputs = tokenizer(
            contextualized_text,
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
        
        contextualized_embeddings.append(mean_pooled)

contextualized_embeddings = np.array(contextualized_embeddings)
print(f"   Generated {len(contextualized_embeddings)} contextualized embeddings")

# Generate concept embeddings
print("\n4. Generating concept embeddings...")
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
print("\n5. Computing similarity matrix...")
similarity_matrix = cosine_similarity(contextualized_embeddings, concept_embeddings)
print(f"   Shape: {similarity_matrix.shape}")

# Analyze raw similarity distribution
print("\n6. Raw similarity statistics:")
print(f"   Mean:   {similarity_matrix.mean():.4f}")
print(f"   Median: {np.median(similarity_matrix):.4f}")
print(f"   Std:    {similarity_matrix.std():.4f}")
print(f"   Min:    {similarity_matrix.min():.4f}")
print(f"   Max:    {similarity_matrix.max():.4f}")

# Normalize per question and analyze
print("\n7. Analyzing normalized distributions...")
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
print("\n8. Generating visualizations...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-1 distribution
axes[0, 0].hist(top_k_stats[1], bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].axvline(np.mean(top_k_stats[1]), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(top_k_stats[1]):.3f}')
axes[0, 0].set_xlabel('Proportion of Total Similarity')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Top-1 Concept Captures What % of Total Similarity?\n(With Survey Context)')
axes[0, 0].legend()

# Top-3 distribution
axes[0, 1].hist(top_k_stats[3], bins=50, edgecolor='black', alpha=0.7, color='orange')
axes[0, 1].axvline(np.mean(top_k_stats[3]), color='red', linestyle='--',
                   label=f'Mean: {np.mean(top_k_stats[3]):.3f}')
axes[0, 1].set_xlabel('Proportion of Total Similarity')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Top-3 Concepts Capture What % of Total Similarity?\n(With Survey Context)')
axes[0, 1].legend()

# Top-5 distribution
axes[1, 0].hist(top_k_stats[5], bins=50, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].axvline(np.mean(top_k_stats[5]), color='red', linestyle='--',
                   label=f'Mean: {np.mean(top_k_stats[5]):.3f}')
axes[1, 0].set_xlabel('Proportion of Total Similarity')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Top-5 Concepts Capture What % of Total Similarity?\n(With Survey Context)')
axes[1, 0].legend()

# Comparison boxplot
data_for_box = [top_k_stats[k] for k in [1, 2, 3, 5, 10]]
axes[1, 1].boxplot(data_for_box, tick_labels=['Top-1', 'Top-2', 'Top-3', 'Top-5', 'Top-10'])
axes[1, 1].set_ylabel('Proportion of Total Similarity')
axes[1, 1].set_title('Cumulative Similarity Mass by Top-K\n(With Survey Context)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
output_path = Path('../reports/figures/normalized_similarity_distributions_with_context.png')
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
print("COMPARISON TO NO-CONTEXT VERSION")
print("="*70)
print("\nDid adding survey context help differentiate concepts?")
print("Review the statistics above and compare to the no-context run.")
print("\nIf distributions are still flat (top-1 ~0.64%), context didn't help.")
print("If distributions show concentration (top-1 >5%), context is working.")
print("\nDone!")
