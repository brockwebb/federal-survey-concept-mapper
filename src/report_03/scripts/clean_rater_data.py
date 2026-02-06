#!/usr/bin/env python3
"""
clean_rater_data.py - Deduplicate, validate, and merge three-rater barrier classifications

Part of Report 03: Harmonization Constraints
Stage: Post-Classification Data Cleanup (Stage 1)

Input:  output/results/barrier_results_{rater}_{model}.jsonl (raw, immutable)
Output: output/analysis/barrier_deduped_{rater}.jsonl (cleaned per-rater)
        output/analysis/barrier_coding_merged_3rater.csv (outer join)
        output/analysis/rater_cleaning_log.json (audit trail)

This script mirrors clean_arbitration_data.py but for Stage 1 rater outputs.
Handles checkpoint restart duplicates and null recoding.

Usage: python scripts/clean_rater_data.py
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add scripts dir to path for lib imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))
from lib.io_utils import load_config, load_jsonl, save_jsonl, ensure_dir


def dedupe_records(records, key='pair_id'):
    """
    Deduplicate records by key, keeping first occurrence.
    Handles checkpoint restart duplicates.
    Returns (deduped_records, dropped_records).
    """
    seen = set()
    deduped = []
    dropped = []

    for record in records:
        record_key = record.get(key)
        if record_key in seen:
            dropped.append(record)
        else:
            seen.add(record_key)
            deduped.append(record)

    return deduped, dropped


def validate_and_recode(records, rater_name):
    """
    Validate schema and recode null barriers to NHB.0.
    Returns (validated_records, validation_stats).
    """
    required_fields = [
        'pair_id', 'primary_barrier', 'feasibility',
        'specific_conflict', 'reasoning'
    ]
    
    # Additional optional fields
    optional_fields = ['additional_barriers', 'survey', 'batch_id', 'batch_index']

    stats = {
        'total': len(records),
        'null_barriers': 0,
        'none_string_barriers': 0,
        'empty_barriers': 0,
        'recoded_to_nhb0': 0,
        'missing_fields': [],
        'schema_valid': 0,
        'barrier_distribution': {}
    }

    validated = []
    for record in records:
        # Check required fields
        missing = [f for f in required_fields if f not in record]
        if missing:
            stats['missing_fields'].append({
                'pair_id': record.get('pair_id', 'UNKNOWN'),
                'missing': missing
            })

        # Check and recode null/None barriers
        barrier = record.get('primary_barrier')
        original_barrier = barrier

        if barrier is None:
            stats['null_barriers'] += 1
            record['primary_barrier'] = 'NHB.0'
            record['_recoded_from'] = 'null'
            stats['recoded_to_nhb0'] += 1
            barrier = 'NHB.0'
        elif isinstance(barrier, str):
            if barrier.lower() in ('none', 'na', 'n/a', 'null'):
                stats['none_string_barriers'] += 1
                record['primary_barrier'] = 'NHB.0'
                record['_recoded_from'] = barrier
                stats['recoded_to_nhb0'] += 1
                barrier = 'NHB.0'
            elif barrier.strip() == '':
                stats['empty_barriers'] += 1
                record['primary_barrier'] = 'NHB.0'
                record['_recoded_from'] = 'empty'
                stats['recoded_to_nhb0'] += 1
                barrier = 'NHB.0'

        # Track barrier distribution
        if barrier:
            # Extract L1 code (first part before dot)
            l1_code = barrier.split('.')[0] if '.' in barrier else barrier
            stats['barrier_distribution'][l1_code] = stats['barrier_distribution'].get(l1_code, 0) + 1

        if not missing:
            stats['schema_valid'] += 1

        validated.append(record)

    return validated, stats


def merge_raters(rater_data, config):
    """
    Outer merge rater results on pair_id.
    Returns DataFrame with coverage info.
    """
    dfs = {}
    rater_keys = list(rater_data.keys())

    for rater_name, records in rater_data.items():
        df = pd.DataFrame(records)
        
        # Fields to rename with rater suffix
        rename_map = {
            'primary_barrier': f'primary_barrier_{rater_name}',
            'feasibility': f'feasibility_{rater_name}',
            'specific_conflict': f'specific_conflict_{rater_name}',
            'reasoning': f'reasoning_{rater_name}',
            'additional_barriers': f'additional_barriers_{rater_name}',
            '_recoded_from': f'_recoded_from_{rater_name}'
        }
        
        # Keep pair_id, survey, batch info without renaming
        cols_to_keep = ['pair_id']
        if 'survey' in df.columns:
            cols_to_keep.append('survey')
        
        # Apply renaming
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        # Select relevant columns
        relevant_cols = cols_to_keep + [c for c in df.columns if rater_name in c]
        df = df[[c for c in relevant_cols if c in df.columns]]
        
        dfs[rater_name] = df

    # Start with first rater, outer merge others
    merged = dfs[rater_keys[0]]

    for rater_name in rater_keys[1:]:
        # Keep only pair_id and rater-specific columns from subsequent raters
        df = dfs[rater_name]
        cols_to_merge = ['pair_id'] + [c for c in df.columns if rater_name in c]
        merged = merged.merge(df[cols_to_merge], on='pair_id', how='outer')

    # Add coverage column
    def get_coverage(row):
        coverage = []
        for rater_name in rater_keys:
            col = f'primary_barrier_{rater_name}'
            if col in row.index and pd.notna(row[col]):
                coverage.append(rater_name)
        return coverage

    merged['rater_coverage'] = merged.apply(get_coverage, axis=1)
    merged['rater_coverage_count'] = merged['rater_coverage'].apply(len)

    # Sort by pair_id
    merged = merged.sort_values('pair_id').reset_index(drop=True)

    return merged


def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent
    results_dir = base_dir / "output" / "results"
    analysis_dir = base_dir / "output" / "analysis"
    ensure_dir(analysis_dir)

    # Load config
    config = load_config(base_dir / "config.yaml")

    print("=" * 60)
    print("RATER DATA CLEANING (Stage 1)")
    print("=" * 60)

    # Initialize cleaning log
    cleaning_log = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'stage': 'post_classification_cleanup',
        'raters': {},
        'merge_stats': {},
        'files_written': []
    }

    # Process each rater
    rater_data = {}

    for rater_key, rater_config in config.get('raters', {}).items():
        model_name = rater_config.get('model', '')
        model_safe = model_name.replace('/', '-').replace(':', '-')

        # Find matching file
        pattern = f"barrier_results_{rater_key}_*.jsonl"
        matching_files = list(results_dir.glob(pattern))

        if not matching_files:
            print(f"\nWARNING: No file found for rater {rater_key}")
            cleaning_log['raters'][rater_key] = {'status': 'file_not_found'}
            continue

        input_file = matching_files[0]  # Take first match
        print(f"\nProcessing {rater_key}: {input_file.name}")

        # Load raw data
        raw_records = load_jsonl(input_file)
        print(f"  Loaded: {len(raw_records)} records")

        # Deduplicate
        deduped, dropped = dedupe_records(raw_records)
        print(f"  After dedup: {len(deduped)} records ({len(dropped)} dropped)")

        # Validate and recode
        validated, val_stats = validate_and_recode(deduped, rater_key)
        print(f"  Schema valid: {val_stats['schema_valid']}/{len(validated)}")
        print(f"  Recoded to NHB.0: {val_stats['recoded_to_nhb0']}")
        
        # Show barrier distribution
        if val_stats['barrier_distribution']:
            print(f"  L1 distribution: {val_stats['barrier_distribution']}")

        # Write deduped file
        output_file = analysis_dir / f"barrier_deduped_{rater_key}.jsonl"
        save_jsonl(validated, output_file)
        print(f"  Written: {output_file.name}")

        # Log stats
        cleaning_log['raters'][rater_key] = {
            'input_file': input_file.name,
            'raw_count': len(raw_records),
            'deduped_count': len(deduped),
            'dropped_count': len(dropped),
            'dropped_pair_ids': [r['pair_id'] for r in dropped][:50],  # Limit logged IDs
            'total_dropped': len(dropped),
            'validation': val_stats,
            'output_file': output_file.name
        }
        cleaning_log['files_written'].append(str(output_file))

        # Store for merge
        rater_data[rater_key] = validated

    if len(rater_data) == 0:
        print("\nERROR: No rater data found. Run barrier pipeline first.")
        return

    # Merge raters
    print(f"\n{'=' * 40}")
    print(f"Merging {len(rater_data)} raters...")
    merged_df = merge_raters(rater_data, config)

    # Coverage summary
    coverage_counts = merged_df['rater_coverage_count'].value_counts().sort_index()
    print(f"  Total pairs: {len(merged_df)}")
    print(f"  Coverage distribution:")
    for count, num_pairs in coverage_counts.items():
        print(f"    {count} raters: {num_pairs} pairs")

    # Write merged CSV
    merged_file = analysis_dir / "barrier_coding_merged_3rater.csv"

    # Convert coverage list to string for CSV
    merged_df['rater_coverage_str'] = merged_df['rater_coverage'].apply(lambda x: ','.join(x))
    merged_df = merged_df.drop(columns=['rater_coverage'])
    merged_df = merged_df.rename(columns={'rater_coverage_str': 'rater_coverage'})

    merged_df.to_csv(merged_file, index=False)
    print(f"  Written: {merged_file.name}")

    # Log merge stats
    cleaning_log['merge_stats'] = {
        'total_pairs': len(merged_df),
        'coverage_distribution': {str(k): int(v) for k, v in coverage_counts.items()},
        'output_file': merged_file.name
    }
    cleaning_log['files_written'].append(str(merged_file))

    # Pair source breakdown (CPS vs FoodAPS)
    cps_count = len(merged_df[merged_df['pair_id'].str.startswith('CPS_')])
    foodaps_count = len(merged_df[merged_df['pair_id'].str.startswith('FOODAPS_')])
    cleaning_log['merge_stats']['pair_sources'] = {
        'CPS': cps_count,
        'FoodAPS': foodaps_count
    }
    print(f"\n  Pair sources: CPS={cps_count}, FoodAPS={foodaps_count}")

    # Three-way coverage stats
    three_way = merged_df[merged_df['rater_coverage_count'] == 3]
    if len(three_way) > 0:
        cps_3way = len(three_way[three_way['pair_id'].str.startswith('CPS_')])
        foodaps_3way = len(three_way[three_way['pair_id'].str.startswith('FOODAPS_')])
        cleaning_log['merge_stats']['three_way_coverage'] = {
            'total': len(three_way),
            'CPS': cps_3way,
            'FoodAPS': foodaps_3way
        }
        print(f"  Three-way coverage: {len(three_way)} pairs (CPS: {cps_3way}, FoodAPS: {foodaps_3way})")

    # Cross-rater agreement preview (L1 level)
    if len(three_way) > 0:
        rater_keys = list(rater_data.keys())
        if len(rater_keys) >= 3:
            l1_cols = [f'primary_barrier_{rk}' for rk in rater_keys]
            
            def extract_l1(val):
                if pd.isna(val):
                    return None
                return val.split('.')[0] if '.' in str(val) else str(val)
            
            three_way_l1 = three_way.copy()
            for col in l1_cols:
                three_way_l1[col + '_l1'] = three_way_l1[col].apply(extract_l1)
            
            l1_cols_check = [c + '_l1' for c in l1_cols]
            unanimous = three_way_l1[three_way_l1[l1_cols_check].nunique(axis=1) == 1]
            
            cleaning_log['merge_stats']['l1_agreement_preview'] = {
                'unanimous_l1': len(unanimous),
                'total_3way': len(three_way),
                'agreement_rate': round(len(unanimous) / len(three_way), 3) if len(three_way) > 0 else 0
            }
            print(f"  L1 unanimous agreement: {len(unanimous)}/{len(three_way)} ({len(unanimous)/len(three_way)*100:.1f}%)")

    # Write cleaning log
    log_file = analysis_dir / "rater_cleaning_log.json"
    with open(log_file, 'w') as f:
        json.dump(cleaning_log, f, indent=2)
    print(f"\nCleaning log: {log_file.name}")

    print("\n" + "=" * 60)
    print("RATER DATA CLEANING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
