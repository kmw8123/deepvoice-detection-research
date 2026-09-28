"""File-independent C346 fusion; model evidence and interval geometry are unchanged."""
import math

WEIGHT_ORDER = ("SONICS_stem", "C239_dual_Deezer", "Fourier", "selected_Dasheng")
WEIGHTS = (
    7.507253011514864e-18,
    0.475285712267941,
    0.3127043353757541,
    0.21200995235630501,
)
WEIGHT_RECEIPT_SHA256 = "6d9a190cd377def65166fa3595196183b3d0a0a5557f1d4dbea75f4d8936ff27"


def validate_weights():
    if len(WEIGHTS) != 4 or any(not math.isfinite(w) or w < 0 for w in WEIGHTS):
        raise ValueError("Invalid frozen C346 weights")
    if not math.isclose(sum(WEIGHTS), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("C346 weights must sum to one")


def global_probability(anchor, sonics, deezer, fourier, dasheng):
    validate_weights()
    probabilities = tuple(float(p) for p in (sonics, deezer, fourier, dasheng))
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("C346 inputs must be finite probabilities")
    return anchor.stable_sigmoid(sum(w * anchor.triad_logit(p) for w, p in zip(WEIGHTS, probabilities)))


def aligned_probability(
    anchor, sonics_starts, sonics_ends, sonics_probabilities,
    deezer_starts, deezer_ends, deezer_probabilities,
    presence_starts, presence_ends, presence_probabilities,
    fourier_probability, dasheng_probability,
):
    if len(sonics_probabilities) == 0:
        return 0.0
    # Retain the production same-file overlap and nearest-interval fallback.
    local_deezer = anchor.c3_overlap_weighted(
        sonics_starts, sonics_ends, deezer_starts, deezer_ends, deezer_probabilities
    )
    local_presence = anchor.c3_overlap_weighted(
        sonics_starts, sonics_ends, presence_starts, presence_ends, presence_probabilities
    )
    if not len(sonics_probabilities) == len(local_deezer) == len(local_presence):
        raise ValueError("C346 interval alignment length mismatch")
    events = []
    for sonics, deezer, presence in zip(sonics_probabilities, local_deezer, local_presence):
        probability = global_probability(anchor, sonics, deezer, fourier_probability, dasheng_probability)
        events.append(anchor.triad_logit(probability * (0.5 + 0.5 * presence)))
    strongest = sorted(events, reverse=True)[:2]
    return anchor.stable_sigmoid(0.75 * strongest[0] + 0.25 * sum(strongest) / len(strongest))
