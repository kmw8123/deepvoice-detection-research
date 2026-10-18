# Annotated mirror: I change comments/docstrings only; src keeps the original bytes.
"""Average two frozen SpecNN music detectors on matching raw-audio crops (C212).

I reuse the script's existing SpecNN preprocessing and inference interface
(C190) and load a second local checkpoint into the same architecture. Each
detector scores the same windows; their probabilities receive equal weight.
The caller later applies same-file music-presence pooling to this evidence.

The companion selected-window Dasheng integration (C159) is handled by the
caller: it replaces an indirect classical music input rather than using the
older equal-mean final-probability helper. No evaluation-time fitting occurs.
"""
import copy
import hashlib
import json
from pathlib import Path


def load_second_deezer(anchor, first_model, directory, device):
    """Clone the existing architecture and strictly load the second local weights.

    The anchor is the caller's script module, providing NumPy and Torch with
    the same runtime versions as the first detector.
    """
    directory = Path(directory)
    manifest = json.loads((directory / 'C205_COMPAT40.manifest.json').read_text(encoding='utf-8'))
    path = directory / 'C205_COMPAT40.npz'
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['c212_npz_sha256']:
        raise RuntimeError('C212 second Deezer checkpoint checksum mismatch')
    second = copy.deepcopy(first_model)
    state = second.state_dict()
    expected = {k for k in state if not k.endswith('num_batches_tracked')}
    with anchor.np.load(path, allow_pickle=False) as weights:
        if set(weights.files) != expected:
            raise RuntimeError('C212 second Deezer state keys mismatch')
        for key in expected:
            value = weights[key]
            if value.dtype != anchor.np.float32 or value.shape != tuple(state[key].shape) or not anchor.np.isfinite(value).all():
                raise RuntimeError('C212 second Deezer invalid tensor: ' + key)
            state[key] = anchor.torch.from_numpy(value.copy()).to(device)
    second.load_state_dict(state, strict=True)
    return second.eval().requires_grad_(False)


def predict_dual_deezer(anchor, first, second, mono16k, device):
    """Return the equal-mean score, shared intervals, and paired window means."""
    # Independently preserve original float32 model inference. Only the fixed
    # between-model and across-window means use float64, preserving the
    # audited dual-detector arithmetic (C210/C212).
    _, starts, ends, a = anchor.predict_deezer_fake_c3(first, mono16k, device)
    _, starts_b, ends_b, b = anchor.predict_deezer_fake_c3(second, mono16k, device)
    if starts != starts_b or ends != ends_b or len(a) != len(b):
        raise RuntimeError('C212 dual Deezer interval mismatch')
    probabilities = (0.5 * anchor.np.asarray(a, dtype=anchor.np.float64)
                     + 0.5 * anchor.np.asarray(b, dtype=anchor.np.float64))
    if not anchor.np.isfinite(probabilities).all() or anchor.np.any((probabilities < 0) | (probabilities > 1)):
        raise RuntimeError('C212 dual Deezer invalid probability')
    return float(probabilities.mean()), starts, ends, probabilities.tolist()
