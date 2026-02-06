"""I/O utilities for config, JSONL, and CSV handling."""
import json
import yaml
import pandas as pd
from pathlib import Path


def load_config(config_path='config.yaml'):
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_jsonl(path):
    """Load JSONL file as list of dicts."""
    records = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def save_jsonl(records, path):
    """Save list of dicts to JSONL file."""
    ensure_dir(Path(path).parent)
    with open(path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_merged_csv(path):
    """Load merged CSV with standard column handling."""
    df = pd.read_csv(path)
    return df


def get_project_root():
    """Get the report directory root (where config.yaml lives)."""
    # Walk up from current file to find config.yaml
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / 'config.yaml').exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find config.yaml in parent directories")
