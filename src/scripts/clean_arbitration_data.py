#!/usr/bin/env python3
"""
clean_arbitration_data.py - Deduplicate and validate arbitration results

Part of Report 03: Harmonization Constraints
Stage: Post-Arbitration Data Cleanup

Input:  output/results/arbitration_v3_results_*.jsonl (raw, immutable)
Output: output/analysis/arbitration_deduped_*.jsonl (cleaned)
        output/analysis/arbitration_merged.csv (outer join)
        output/analysis/data_cleaning_log.json (audit trail)

Usage: python scripts/clean_arbitration_data.py
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

# Add lib to path
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.io_utils import load_config, load_jsonl, save_jsonl


def dedupe_records(records, key='pair_id'):
    """
    Deduplicate records by key, keeping first occurrence.
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


def validate_and_recode(records, arbitrator_name):
    """
    Validate schema and recode null barriers to NHB.0.
    Returns (validated_records, validation_stats).
    """
    required_fields = [
        'pair_id', 'final_barrier_code', 'final_feasibility',
        'selected_rater', 'selected_rater_key', 'arbitrator'
    ]

    stats = {
        'total': len(records),
        'null_barriers': 0,
        'none_string_barriers': 0,
        'empty_barriers': 0,
        'recoded_to_nhb0': 0,
        'missing_fields': [],
        'schema_valid': 0
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
        barrier = record.get('final_barrier_code')

        if barrier is None:
            stats['null_barriers'] += 1
            record['final_barrier_code'] = 'NHB.0'
            record['_recoded_from'] = 'null'
            stats['recoded_to_nhb0'] += 1
        elif isinstance(barrier, str):
            if barrier.lower() in ('none', 'na', 'n/a', 'null'):
                stats['none_string_barriers'] += 1
                record['final_barrier_code'] = 'NHB.0'
                record['_recoded_from'] = barrier
                stats['recoded_to_nhb0'] += 1
            elif barrier.strip() == '':
                stats['empty_barriers'] += 1
                record['final_barrier_code'] = 'NHB.0'
                record['_recoded_from'] = 'empty'
                stats['recoded_to_nhb0'] += 1

        if not missing:
            stats['schema_valid'] += 1

        validated.append(record)

    return validated, stats


def merge_arbitrators(arbitrator_data):
    """
    Outer merge arbitrator results on pair_id.
    Returns DataFrame with coverage column.
    """
    dfs = {}

    for arb_name, records in arbitrator_data.items():
        df = pd.DataFrame(records)

        # Prefix columns with arbitrator name (except pair_id)
        rename_cols = {col: f"{arb_name}_{col}" for col in df.columns if col != 'pair_id'}
        df = df.rename(columns=rename_cols)

        dfs[arb_name] = df

    # Start with first arbitrator, outer merge others
    arb_names = list(dfs.keys())
    merged = dfs[arb_names[0]]

    for arb_name in arb_names[1:]:
        merged = merged.merge(dfs[arb_name], on='pair_id', how='outer')

    # Add coverage column - which arbitrators have data for this pair
    def get_coverage(row):
        coverage = []
        for arb_name in arb_names:
            # Check if this arbitrator has data (non-null final_barrier_code)
            col = f"{arb_name}_final_barrier_code"
            if col in row and pd.notna(row[col]):
                coverage.append(arb_name)
        return coverage

    merged['coverage'] = merged.apply(get_coverage, axis=1)
    merged['coverage_count'] = merged['coverage'].apply(len)

    # Sort by pair_id
    merged = merged.sort_values('pair_id').reset_index(drop=True)

    return merged


def main():
    # Setup paths
    base_dir = REPO_ROOT  # post-restructure: use repo root
    results_dir = base_dir / "output" / "report_03" / "results"
    analysis_dir = base_dir / "output" / "report_03" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    config = load_config(base_dir / "config" / "report_03.yaml")

    # Initialize cleaning log
    cleaning_log = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'stage': 'post_arbitration_cleanup',
        'arbitrators': {},
        'merge_stats': {},
        'files_written': []
    }

    # Process each arbitrator
    arbitrator_data = {}

    for arb_key, arb_config in config.get('arbitrators', {}).items():
        model_name = arb_config.get('model', '')

        # Find matching file
        pattern = f"arbitration_v3_results_{arb_key}_*.jsonl"
        matching_files = list(results_dir.glob(pattern))

        if not matching_files:
            print(f"WARNING: No file found for arbitrator {arb_key}")
            cleaning_log['arbitrators'][arb_key] = {'status': 'file_not_found'}
            continue

        input_file = matching_files[0]  # Take first match
        print(f"\nProcessing {arb_key}: {input_file.name}")

        # Load raw data
        raw_records = load_jsonl(input_file)
        print(f"  Loaded: {len(raw_records)} records")

        # Deduplicate
        deduped, dropped = dedupe_records(raw_records)
        print(f"  After dedup: {len(deduped)} records ({len(dropped)} dropped)")

        # Validate and recode
        validated, val_stats = validate_and_recode(deduped, arb_key)
        print(f"  Schema valid: {val_stats['schema_valid']}/{len(validated)}")
        print(f"  Recoded to NHB.0: {val_stats['recoded_to_nhb0']}")

        # Write deduped file
        output_file = analysis_dir / f"arbitration_deduped_{arb_key}.jsonl"
        save_jsonl(validated, output_file)
        print(f"  Written: {output_file.name}")

        # Log stats
        cleaning_log['arbitrators'][arb_key] = {
            'input_file': input_file.name,
            'raw_count': len(raw_records),
            'deduped_count': len(deduped),
            'dropped_count': len(dropped),
            'dropped_pair_ids': [r['pair_id'] for r in dropped],
            'validation': val_stats,
            'output_file': output_file.name
        }
        cleaning_log['files_written'].append(str(output_file))

        # Store for merge
        arbitrator_data[arb_key] = validated

    # Merge arbitrators
    print(f"\nMerging {len(arbitrator_data)} arbitrators...")
    merged_df = merge_arbitrators(arbitrator_data)

    # Coverage summary
    coverage_counts = merged_df['coverage_count'].value_counts().sort_index()
    print(f"  Total pairs: {len(merged_df)}")
    print(f"  Coverage distribution:")
    for count, num_pairs in coverage_counts.items():
        print(f"    {count} arbitrators: {num_pairs} pairs")

    # Write merged CSV
    merged_file = analysis_dir / "arbitration_merged.csv"

    # Convert coverage list to string for CSV
    merged_df['coverage_str'] = merged_df['coverage'].apply(lambda x: ','.join(x))
    merged_df = merged_df.drop(columns=['coverage'])
    merged_df = merged_df.rename(columns={'coverage_str': 'coverage'})

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

    # Three-way coverage by source
    three_way = merged_df[merged_df['coverage_count'] == 3]
    if len(three_way) > 0:
        cps_3way = len(three_way[three_way['pair_id'].str.startswith('CPS_')])
        foodaps_3way = len(three_way[three_way['pair_id'].str.startswith('FOODAPS_')])
        cleaning_log['merge_stats']['three_way_coverage'] = {
            'total': len(three_way),
            'CPS': cps_3way,
            'FoodAPS': foodaps_3way
        }
        print(f"\n  Three-way coverage: {len(three_way)} pairs (CPS: {cps_3way}, FoodAPS: {foodaps_3way})")

    # Write cleaning log
    log_file = analysis_dir / "data_cleaning_log.json"
    with open(log_file, 'w') as f:
        json.dump(cleaning_log, f, indent=2)
    print(f"\nCleaning log: {log_file.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
