#!/usr/bin/env python3
"""
One-time fix for Google arbitration JSONL.
Re-derives selected_rater_key from selected_rater + rater_order.

Run: python scripts/fix_google_selected_rater_key.py
"""
import json
from pathlib import Path

def fix_selected_rater_key(record):
    """Fix selected_rater_key using selected_rater and rater_order."""
    selected = record.get('selected_rater', 'synthesis')
    rater_order = record.get('rater_order', ['openai', 'anthropic', 'google'])
    
    # Normalize: handle "Rater A" format
    if selected and selected.upper().startswith('RATER '):
        selected = selected[-1].upper()
    
    if selected in ['A', 'B', 'C']:
        label_to_idx = {'A': 0, 'B': 1, 'C': 2}
        record['selected_rater_key'] = rater_order[label_to_idx[selected]]
    else:
        record['selected_rater_key'] = 'synthesis'
    
    return record

def main():
    base = Path(__file__).parent.parent
    results_dir = base / 'output' / 'results'
    
    # Find Google JSONL
    google_files = list(results_dir.glob('arbitration_v3_results_google_*.jsonl'))
    
    if not google_files:
        print("No Google arbitration files found")
        return
    
    for fpath in google_files:
        print(f"Processing: {fpath.name}")
        
        # Read all records
        records = []
        with open(fpath) as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # Count fixes needed
        fixes = 0
        for r in records:
            old_key = r.get('selected_rater_key')
            fix_selected_rater_key(r)
            if r['selected_rater_key'] != old_key:
                fixes += 1
        
        # Write back
        with open(fpath, 'w') as f:
            for r in records:
                f.write(json.dumps(r) + '\n')
        
        print(f"  Records: {len(records)}, Fixed: {fixes}")

if __name__ == '__main__':
    main()
