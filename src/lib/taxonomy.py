"""Barrier taxonomy utilities."""

# L1 barrier categories
BARRIER_L1 = {
    'TC': 'Temporal/Chronological',
    'CC': 'Construct/Concept',
    'PC': 'Population/Coverage',
    'RS': 'Response Scale',
    'MC': 'Mode/Context',
    'PM': 'Policy/Market',
    'NHB': 'No Harmonization Barrier'
}

# Full barrier codes (L1.L2)
BARRIER_CODES = [
    'TC.1', 'TC.2', 'TC.3',
    'CC.1', 'CC.2', 'CC.3', 'CC.4',
    'PC.1', 'PC.2', 'PC.3',
    'RS.1', 'RS.2', 'RS.3', 'RS.4',
    'MC.1', 'MC.2', 'MC.3', 'MC.4',
    'PM.1', 'PM.2',
    'NHB.0'
]

FEASIBILITY_LEVELS = ['F1', 'F2', 'F3']


def extract_l1(barrier_code):
    """
    Extract L1 category from full barrier code.

    Args:
        barrier_code: str like 'CC.1', 'TC.2', or None

    Returns:
        L1 category string (e.g., 'CC', 'TC') or None
    """
    if barrier_code is None or barrier_code == '':
        return None
    if '.' in str(barrier_code):
        return str(barrier_code).split('.')[0]
    return str(barrier_code)


def extract_l2(barrier_code):
    """
    Extract L2 subcategory from full barrier code.

    Args:
        barrier_code: str like 'CC.1', 'TC.2'

    Returns:
        L2 subcategory string (e.g., '1', '2') or None
    """
    if barrier_code is None or barrier_code == '':
        return None
    parts = str(barrier_code).split('.')
    if len(parts) >= 2:
        return parts[1]
    return None


def normalize_barrier_code(code):
    """Normalize barrier code to standard format (uppercase, trimmed)."""
    if code is None:
        return None
    return str(code).strip().upper()


def is_valid_l1(code):
    """Check if code is a valid L1 category."""
    return extract_l1(code) in BARRIER_L1


def is_valid_full_code(code):
    """Check if code is a valid full barrier code."""
    return normalize_barrier_code(code) in BARRIER_CODES
