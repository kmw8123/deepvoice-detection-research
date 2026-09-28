"""C239: fixed within-file presence weighting of the global Deezer mean only."""
import math


def pool_deezer_by_presence(anchor, global_probability, starts, ends, probabilities,
                            presence_starts, presence_ends, music_presence_segments):
    """All intervals use 16 kHz sample indices. Never mutates input evidence."""
    original = float(global_probability)
    if not math.isfinite(original) or not 0.0 <= original <= 1.0:
        raise RuntimeError('C239 invalid original Deezer probability')
    np = anchor.np
    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1:
        raise RuntimeError('C239 Deezer probabilities must be one dimensional')
    if not len(values):
        return original
    if len(starts) != len(values) or len(ends) != len(values):
        raise RuntimeError('C239 Deezer interval geometry mismatch')
    if not np.isfinite(values).all() or np.any((values < 0.0) | (values > 1.0)):
        raise RuntimeError('C239 invalid Deezer window probabilities')
    if len(values) == 1:
        return float(values[0])
    weights = np.asarray(anchor.c3_overlap_weighted(
        starts, ends, presence_starts, presence_ends, music_presence_segments), dtype=np.float64)
    if weights.shape != values.shape or not np.isfinite(weights).all() or np.any((weights < 0.0) | (weights > 1.0)):
        raise RuntimeError('C239 invalid aligned music presence')
    total = weights.sum()
    if total == 0.0:
        return original
    result = float(np.dot(values, weights) / total)
    if not math.isfinite(result):
        raise RuntimeError('C239 nonfinite pooled Deezer probability')
    return result
