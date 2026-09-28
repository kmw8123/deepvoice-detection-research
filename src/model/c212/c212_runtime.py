"""C212: fixed within-file experts; no training, label or cross-file state.

The original C190 loader/inference and C159 selected-window encoder are reused.
Dasheng is an indirect classical slot, NOT the C159 final-probability mixture.
"""
import copy
import hashlib
import json
from pathlib import Path


def load_second_deezer(anchor, first_model, directory, device):
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
    # Independently preserve original float32 model inference. Only the fixed
    # between-model and across-window means are float64, as in C210/C212.
    _, starts, ends, a = anchor.predict_deezer_fake_c3(first, mono16k, device)
    _, starts_b, ends_b, b = anchor.predict_deezer_fake_c3(second, mono16k, device)
    if starts != starts_b or ends != ends_b or len(a) != len(b):
        raise RuntimeError('C212 dual Deezer interval mismatch')
    probabilities = (0.5 * anchor.np.asarray(a, dtype=anchor.np.float64)
                     + 0.5 * anchor.np.asarray(b, dtype=anchor.np.float64))
    if not anchor.np.isfinite(probabilities).all() or anchor.np.any((probabilities < 0) | (probabilities > 1)):
        raise RuntimeError('C212 dual Deezer invalid probability')
    return float(probabilities.mean()), starts, ends, probabilities.tolist()
