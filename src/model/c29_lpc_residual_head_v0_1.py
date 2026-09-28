#!/usr/bin/env python3
"""C29 fixed multiscale linear-prediction residual music head.

The representation is intentionally independent of C3 scores, C28 recurrence
features, source separation, and neural detector embeddings.  It summarizes
short-time waveform prediction residuals at 16, 8, and 4 kHz.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import signal
import soundfile as sf


TARGET_SAMPLE_RATE = 16_000
TARGET_SAMPLES = 64_000
EPSILON = 1.0e-12
SCALES = ((1, 24), (2, 16), (4, 8))
FRAME_SECONDS = 0.030
HOP_SECONDS = 0.015
SUMMARY_NAMES = ("mean", "std", "q05", "q25", "q50", "q75", "q95")
SCALAR_NAMES = (
    "log_prediction_gain",
    "residual_spectral_flatness",
    "residual_kurtosis",
    "residual_zcr",
    "residual_crest",
    "residual_abs_acf_lag1",
    "residual_abs_acf_lag2",
    "residual_abs_acf_lag4",
    "residual_abs_acf_lag8",
    "residual_power_band0",
    "residual_power_band1",
    "residual_power_band2",
    "residual_power_band3",
)


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def _center_or_tile(waveform: np.ndarray, samples: int = TARGET_SAMPLES) -> np.ndarray:
    x = np.asarray(waveform, dtype=np.float64).reshape(-1)
    if x.size == 0:
        raise ValueError("empty waveform")
    if x.size < samples:
        x = np.tile(x, int(np.ceil(samples / x.size)))
    if x.size > samples:
        start = (x.size - samples) // 2
        x = x[start : start + samples]
    return np.asarray(x[:samples], dtype=np.float64)


def canonicalize_waveform(waveform: np.ndarray, source_sample_rate: int) -> np.ndarray:
    x = np.asarray(waveform)
    if x.ndim == 2:
        x = np.mean(x.astype(np.float64), axis=1)
    elif x.ndim != 1:
        raise ValueError(f"unsupported waveform rank: {x.ndim}")
    x = np.asarray(x, dtype=np.float64)
    if not np.all(np.isfinite(x)):
        raise ValueError("waveform contains non-finite values")
    if int(source_sample_rate) <= 0:
        raise ValueError("invalid sample rate")
    if int(source_sample_rate) != TARGET_SAMPLE_RATE:
        divisor = int(np.gcd(int(source_sample_rate), TARGET_SAMPLE_RATE))
        x = signal.resample_poly(
            x,
            TARGET_SAMPLE_RATE // divisor,
            int(source_sample_rate) // divisor,
            window=("kaiser", 5.0),
        )
    x = _center_or_tile(x)
    x -= float(np.mean(x))
    rms = float(np.sqrt(np.mean(x * x) + EPSILON))
    x = np.clip(x / max(rms, 1.0e-6), -12.0, 12.0)
    return np.asarray(x, dtype=np.float64)


def load_audio(path: Path, format_hint: str | None = None) -> np.ndarray:
    path = Path(path)
    if format_hint == "little_endian_float32_pcm" or path.suffix.lower() == ".f32le":
        raw = np.fromfile(path, dtype="<f4")
        return canonicalize_waveform(raw, TARGET_SAMPLE_RATE)
    waveform, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    return canonicalize_waveform(waveform, int(sample_rate))


def _frame_signal(x: np.ndarray, sample_rate: int) -> np.ndarray:
    frame = max(32, int(round(FRAME_SECONDS * sample_rate)))
    hop = max(16, int(round(HOP_SECONDS * sample_rate)))
    if x.size < frame:
        x = np.pad(x, (0, frame - x.size))
    count = 1 + (x.size - frame) // hop
    starts = np.arange(count, dtype=np.int64) * hop
    frames = np.stack([x[start : start + frame] for start in starts], axis=0)
    frames -= np.mean(frames, axis=1, keepdims=True)
    rms = np.sqrt(np.mean(frames * frames, axis=1, keepdims=True) + EPSILON)
    frames = frames / np.maximum(rms, 1.0e-6)
    frames *= np.hamming(frame)[None, :]
    return np.asarray(frames, dtype=np.float64)


def _levinson_durbin(autocorrelation: np.ndarray, order: int) -> tuple[np.ndarray, np.ndarray, float]:
    r = np.asarray(autocorrelation, dtype=np.float64)
    coefficients = np.zeros(order + 1, dtype=np.float64)
    reflection = np.zeros(order, dtype=np.float64)
    coefficients[0] = 1.0
    error = max(float(r[0]), EPSILON)
    for index in range(1, order + 1):
        previous = coefficients.copy()
        cross = float(r[index])
        if index > 1:
            cross += float(np.dot(previous[1:index], r[index - 1 : 0 : -1]))
        kappa = float(np.clip(-cross / max(error, EPSILON), -0.999, 0.999))
        reflection[index - 1] = kappa
        if index > 1:
            coefficients[1:index] = previous[1:index] + kappa * previous[index - 1 : 0 : -1]
        coefficients[index] = kappa
        error = max(error * (1.0 - kappa * kappa), EPSILON)
    return coefficients, reflection, error


def _summary(values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    return np.asarray(
        [
            np.mean(x),
            np.std(x),
            np.quantile(x, 0.05),
            np.quantile(x, 0.25),
            np.quantile(x, 0.50),
            np.quantile(x, 0.75),
            np.quantile(x, 0.95),
        ],
        dtype=np.float64,
    )


def _scale_features(waveform: np.ndarray, downsample: int, order: int) -> np.ndarray:
    if downsample == 1:
        x = waveform.copy()
    else:
        x = signal.resample_poly(waveform, 1, downsample, window=("kaiser", 5.0))
    sample_rate = TARGET_SAMPLE_RATE // downsample
    frames = _frame_signal(x, sample_rate)
    hamming_energy = np.mean(frames * frames, axis=1)
    scalar_rows: list[list[float]] = []
    reflection_rows: list[np.ndarray] = []
    for frame_index, frame in enumerate(frames):
        autocorrelation = np.asarray(
            [np.dot(frame[lag:], frame[: frame.size - lag]) for lag in range(order + 1)],
            dtype=np.float64,
        )
        coefficients, reflection, _ = _levinson_durbin(autocorrelation, order)
        residual = np.convolve(frame, coefficients, mode="full")[: frame.size]
        residual = residual[order:]
        residual_energy = float(np.mean(residual * residual) + EPSILON)
        spectrum = np.abs(np.fft.rfft(residual)) ** 2 + EPSILON
        flatness = float(np.exp(np.mean(np.log(spectrum))) / np.mean(spectrum))
        centered = residual - float(np.mean(residual))
        variance = float(np.mean(centered * centered) + EPSILON)
        kurtosis = float(np.mean(centered**4) / (variance * variance))
        zcr = float(np.mean(np.signbit(residual[1:]) != np.signbit(residual[:-1])))
        crest = float(np.max(np.abs(residual)) / np.sqrt(residual_energy))
        acf_values = []
        denominator = float(np.dot(residual, residual) + EPSILON)
        for lag in (1, 2, 4, 8):
            acf_values.append(float(abs(np.dot(residual[lag:], residual[:-lag])) / denominator))
        band_values = []
        boundaries = np.linspace(0, spectrum.size, 5, dtype=np.int64)
        total_power = float(np.sum(spectrum) + EPSILON)
        for band in range(4):
            band_values.append(float(np.sum(spectrum[boundaries[band] : boundaries[band + 1]]) / total_power))
        scalar_rows.append(
            [
                float(np.log((hamming_energy[frame_index] + EPSILON) / residual_energy)),
                flatness,
                kurtosis,
                zcr,
                crest,
                *acf_values,
                *band_values,
            ]
        )
        reflection_rows.append(reflection)

    scalar = np.asarray(scalar_rows, dtype=np.float64)
    reflection_matrix = np.asarray(reflection_rows, dtype=np.float64)
    features: list[np.ndarray] = []
    for column in range(scalar.shape[1]):
        features.append(_summary(scalar[:, column]))
    features.extend(
        (
            np.mean(reflection_matrix, axis=0),
            np.std(reflection_matrix, axis=0),
            np.mean(np.abs(reflection_matrix), axis=0),
        )
    )
    global_values = np.asarray(
        [
            np.sqrt(np.mean(x * x) + EPSILON),
            np.max(np.abs(x)),
            np.mean(np.signbit(x[1:]) != np.signbit(x[:-1])),
            np.sqrt(np.mean(np.diff(x) ** 2) + EPSILON),
            np.sqrt(np.mean(np.diff(x, n=2) ** 2) + EPSILON),
            np.quantile(np.abs(x), 0.50),
            np.quantile(np.abs(x), 0.90),
            np.quantile(np.abs(x), 0.99),
        ],
        dtype=np.float64,
    )
    features.append(global_values)
    result = np.concatenate(features)
    return np.nan_to_num(result, nan=0.0, posinf=1.0e6, neginf=-1.0e6)


def feature_names() -> list[str]:
    names: list[str] = []
    for downsample, order in SCALES:
        prefix = f"sr{TARGET_SAMPLE_RATE // downsample}_p{order}"
        for scalar_name in SCALAR_NAMES:
            for summary_name in SUMMARY_NAMES:
                names.append(f"{prefix}_{scalar_name}_{summary_name}")
        for statistic in ("mean", "std", "mean_abs"):
            for coefficient in range(1, order + 1):
                names.append(f"{prefix}_reflection_k{coefficient}_{statistic}")
        for global_name in (
            "rms",
            "peak",
            "zcr",
            "diff1_rms",
            "diff2_rms",
            "abs_q50",
            "abs_q90",
            "abs_q99",
        ):
            names.append(f"{prefix}_global_{global_name}")
    return names


def extract_features(waveform: np.ndarray) -> np.ndarray:
    x = np.asarray(waveform, dtype=np.float64).reshape(-1)
    if x.size != TARGET_SAMPLES:
        raise ValueError(f"expected {TARGET_SAMPLES} canonical samples, got {x.size}")
    vector = np.concatenate([_scale_features(x, downsample, order) for downsample, order in SCALES])
    names = feature_names()
    if vector.shape != (len(names),):
        raise RuntimeError(f"feature schema mismatch: {vector.shape} vs {len(names)}")
    if not np.all(np.isfinite(vector)):
        raise RuntimeError("non-finite C29 feature")
    return np.asarray(vector, dtype=np.float64)


def fit_head(features: np.ndarray, labels: np.ndarray, sample_weight: np.ndarray):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    weights = np.asarray(sample_weight, dtype=np.float64)
    scaler = StandardScaler(with_mean=True, with_std=True)
    transformed = scaler.fit_transform(x)
    classifier = LogisticRegression(
        C=0.01,
        penalty="l2",
        solver="liblinear",
        fit_intercept=True,
        max_iter=2_000,
        tol=1.0e-7,
        random_state=236_749,
    )
    classifier.fit(transformed, y, sample_weight=weights)
    return scaler, classifier


def model_arrays(scaler, classifier) -> dict[str, np.ndarray]:
    return {
        "feature_names_utf8": np.frombuffer(
            json.dumps(feature_names(), ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            dtype=np.uint8,
        ),
        "scaler_mean": np.asarray(scaler.mean_, dtype=np.float64),
        "scaler_scale": np.asarray(scaler.scale_, dtype=np.float64),
        "coefficient": np.asarray(classifier.coef_[0], dtype=np.float64),
        "intercept": np.asarray(classifier.intercept_, dtype=np.float64),
    }


def predict_from_arrays(features: np.ndarray, arrays: dict[str, np.ndarray]) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    mean = np.asarray(arrays["scaler_mean"], dtype=np.float64)
    scale = np.asarray(arrays["scaler_scale"], dtype=np.float64)
    coefficient = np.asarray(arrays["coefficient"], dtype=np.float64)
    intercept = float(np.asarray(arrays["intercept"], dtype=np.float64).reshape(-1)[0])
    logits = ((x - mean) / np.maximum(scale, EPSILON)) @ coefficient + intercept
    logits = np.asarray(logits, dtype=np.float64)
    probabilities = np.empty_like(logits)
    positive = logits >= 0
    probabilities[positive] = 1.0 / (1.0 + np.exp(-logits[positive]))
    negative_exp = np.exp(logits[~positive])
    probabilities[~positive] = negative_exp / (1.0 + negative_exp)
    return probabilities


def save_model(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        np.savez(handle, **arrays)


def load_model(path: Path) -> dict[str, np.ndarray]:
    with np.load(Path(path), allow_pickle=False) as archive:
        arrays = {name: np.asarray(archive[name]) for name in archive.files}
    expected = {"feature_names_utf8", "scaler_mean", "scaler_scale", "coefficient", "intercept"}
    if set(arrays) != expected:
        raise RuntimeError(f"unexpected model arrays: {sorted(arrays)}")
    return arrays

