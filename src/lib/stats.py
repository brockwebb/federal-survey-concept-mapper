"""Statistical functions for inter-rater agreement analysis."""
import numpy as np
from collections import Counter

try:
    import krippendorff as kripp_lib
    HAS_KRIPPENDORFF = True
except ImportError:
    HAS_KRIPPENDORFF = False


def cohens_kappa(labels1, labels2):
    """
    Compute Cohen's Kappa for two raters.

    Args:
        labels1, labels2: Arrays of categorical labels (same length)

    Returns:
        kappa: float, chance-corrected agreement (-1 to 1)
    """
    labels1 = np.array(labels1)
    labels2 = np.array(labels2)

    # Remove pairs where either is null
    mask = ~(np.equal(labels1, None) | np.equal(labels2, None))
    labels1 = labels1[mask]
    labels2 = labels2[mask]

    n = len(labels1)
    if n == 0:
        return np.nan

    # Observed agreement
    po = np.mean(labels1 == labels2)

    # Expected agreement (by chance)
    categories = list(set(labels1) | set(labels2))
    pe = 0
    for cat in categories:
        p1 = np.mean(labels1 == cat)
        p2 = np.mean(labels2 == cat)
        pe += p1 * p2

    # Kappa
    if pe == 1:
        return 1.0 if po == 1 else 0.0

    kappa = (po - pe) / (1 - pe)
    return kappa


def fleiss_kappa(ratings_matrix):
    """
    Compute Fleiss' Kappa for multiple raters.

    Args:
        ratings_matrix: 2D array, shape (n_items, n_raters)
                       Each cell contains the category label

    Returns:
        kappa: float, multi-rater agreement statistic
    """
    ratings = np.array(ratings_matrix)
    n_items, n_raters = ratings.shape

    # Get unique categories
    categories = list(set(ratings.flatten()))
    n_categories = len(categories)
    cat_to_idx = {cat: i for i, cat in enumerate(categories)}

    # Count matrix: for each item, count of each category
    counts = np.zeros((n_items, n_categories))
    for i in range(n_items):
        for j in range(n_raters):
            cat_idx = cat_to_idx[ratings[i, j]]
            counts[i, cat_idx] += 1

    # P_i for each item
    P_i = (np.sum(counts ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = np.mean(P_i)

    # P_j for each category (proportion across all ratings)
    p_j = np.sum(counts, axis=0) / (n_items * n_raters)
    P_e_bar = np.sum(p_j ** 2)

    # Kappa
    if P_e_bar == 1:
        return 1.0 if P_bar == 1 else 0.0

    kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
    return kappa


def percent_agreement(labels1, labels2):
    """Simple percentage agreement between two raters."""
    labels1 = np.array(labels1)
    labels2 = np.array(labels2)
    mask = ~(np.equal(labels1, None) | np.equal(labels2, None))
    if mask.sum() == 0:
        return np.nan
    return np.mean(labels1[mask] == labels2[mask])


def interpret_kappa(kappa):
    """Landis & Koch interpretation of kappa values."""
    if kappa < 0:
        return "Poor"
    elif kappa < 0.20:
        return "Slight"
    elif kappa < 0.40:
        return "Fair"
    elif kappa < 0.60:
        return "Moderate"
    elif kappa < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


def krippendorff_alpha(ratings_matrix, level_of_measurement='nominal'):
    """
    Compute Krippendorff's Alpha for multiple raters.

    Args:
        ratings_matrix: 2D array, shape (n_items, n_raters)
        level_of_measurement: 'nominal', 'ordinal', 'interval', 'ratio'

    Returns:
        alpha: float, reliability coefficient
    """
    if not HAS_KRIPPENDORFF:
        raise ImportError("krippendorff package required. Install with: pip install krippendorff")

    # krippendorff expects shape (n_raters, n_items), so transpose
    # Also convert to list of lists with None for missing
    data = np.array(ratings_matrix).T.tolist()
    return kripp_lib.alpha(reliability_data=data, level_of_measurement=level_of_measurement)


def interpret_kappa_mchugh(value):
    """
    McHugh (2012) interpretation for health research.

    Returns:
        tuple: (interpretation_string, quality_gate_passed)
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ("Invalid", False)
    if value >= 0.80:
        return ("Almost Perfect", True)
    elif value >= 0.60:
        return ("Substantial", False)
    elif value >= 0.40:
        return ("Moderate", False)
    elif value >= 0.21:
        return ("Fair", False)
    else:
        return ("Slight/Poor", False)
