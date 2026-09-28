"""C159: fixed CPU Dasheng music head; all assets are package-relative.

This is our C151-trained head, NOT the published DotCheck detector.
No fitting, remote code loading, network access or cross-file prediction state.
"""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import types


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


class MusicWindowModel:
    def __init__(self, directory):
        import numpy as np
        import torch
        from safetensors.torch import load_file
        self.directory = Path(directory).resolve()
        model_dir = self.directory / 'dasheng'
        if sha(model_dir / 'model.safetensors') != 'adaa439ebec13933501242364a29b7912c2695d0354061b278c873438b2736c3':
            raise RuntimeError('C159 backbone checksum mismatch')
        if sha(self.directory / 'music_head.npz') != '410bc2cba04580084c2a3ed6e78bbe81d0ef8e9a8ce80b75dbf6df9abfc1b2a3':
            raise RuntimeError('C159 head checksum mismatch')
        package = types.ModuleType('c159_local_dasheng')
        package.__path__ = [str(model_dir)]
        sys.modules[package.__name__] = package
        config_module = importlib.import_module('c159_local_dasheng.configuration_dasheng')
        model_module = importlib.import_module('c159_local_dasheng.modeling_dasheng')
        feature_module = importlib.import_module('c159_local_dasheng.feature_extraction_dasheng')
        config = config_module.DashengConfig(**json.loads((model_dir / 'config.json').read_text(encoding='utf-8')))
        with torch.device('meta'):
            self.model = model_module.DashengModel(config, outputdim=None)
        state = load_file(str(model_dir / 'model.safetensors'), device='cpu')
        self.model.load_state_dict(state, strict=True, assign=True)
        del state
        self.model.eval().requires_grad_(False)
        self.frontend = feature_module.DashengFeatureExtractor(**json.loads((model_dir / 'preprocessor_config.json').read_text(encoding='utf-8')))
        with np.load(self.directory / 'music_head.npz', allow_pickle=False) as z:
            self.head = {k: z[k].copy() for k in z.files}
        for k in ('mean', 'scale', 'coef'):
            if self.head[k].shape != (768,) or not np.isfinite(self.head[k]).all():
                raise RuntimeError('C159 head shape/finite failure: ' + k)
        if np.any(self.head['scale'] <= 0) or self.head['intercept'].shape != (1,):
            raise RuntimeError('C159 head scale/intercept failure')
        # Only the package's own small helper is loaded, without remote imports.
        import c159_music_window
        self.helper = c159_music_window

    def predict(self, mono16k, presence_starts, presence_ends, music_presence):
        start, _ = self.helper.select_start(len(mono16k), presence_starts, presence_ends, music_presence)
        wave = self.helper.extract_window(mono16k, start)
        feature = self.helper.encode_raw768(self.model, self.frontend, wave)
        return self.helper.predict_head(feature, self.head)

    def combine(self, c51_music_probability, selected_probability):
        return self.helper.mix_external_music(c51_music_probability, selected_probability)
