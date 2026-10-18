# Annotated mirror: I change comments/docstrings only; src keeps the original bytes.
"""Extract a spectral artifact fingerprint without reading labels or scores.

This module performs no file, network, model, checkpoint, or score I/O.  It is
an independent NumPy/SciPy implementation of the feature described by Afchar
et al. (ISMIR 2025), specialized to the competition's mono 16 kHz input.

I start from a mean log-power spectrum, retain frequencies between 1 and 8 kHz,
subtract a smooth lower spectral envelope, and normalize the clipped residual.
The result is a 7,167-value feature. The caller loads the project's frozen
logistic coefficients and converts this feature to a fake probability; this
module itself neither trains a classifier nor changes evidence across files.
"""

from __future__ import annotations

from typing import Final

import numpy as np


SAMPLE_RATE: Final[int] = 16_000
N_FFT: Final[int] = 16_384
HOP_LENGTH: Final[int] = 8_192
FREQ_MIN_EXCLUSIVE: Final[float] = 1_000.0
FREQ_MAX_EXCLUSIVE: Final[float] = 8_000.0
HULL_AREA: Final[int] = 10
MIN_DB: Final[float] = -45.0
MAX_RESIDUE_DB: Final[float] = 5.0
NORMALIZATION_EPS: Final[float] = 1e-6
MIN_SAMPLES: Final[int] = 4 * SAMPLE_RATE
MAX_SAMPLES: Final[int] = 60 * SAMPLE_RATE


class FourierFingerprintV1Error(ValueError):
    """Raised when an input or computed fingerprint violates the V1 contract."""


def feature_frequencies_hz() -> np.ndarray:
    """Return the exact retained frequency coordinates as float64."""

    frequencies = np.linspace(
        0.0, SAMPLE_RATE / 2.0, num=(N_FFT // 2) + 1, dtype=np.float64
    )
    mask = (frequencies > FREQ_MIN_EXCLUSIVE) & (
        frequencies < FREQ_MAX_EXCLUSIVE
    )
    result = frequencies[mask]
    if result.shape != (7167,):
        raise FourierFingerprintV1Error("unexpected V1 frequency geometry")
    return result


def periodic_hann_window() -> np.ndarray:
    """Return the periodic Hann window used by torch/torchaudio STFT."""

    index = np.arange(N_FFT, dtype=np.float64)
    return 0.5 - 0.5 * np.cos((2.0 * np.pi * index) / float(N_FFT))


def _validate_waveform(waveform: np.ndarray) -> np.ndarray:
    if type(waveform) is not np.ndarray:
        raise FourierFingerprintV1Error("waveform must be a built-in numpy.ndarray")
    if waveform.dtype != np.dtype("float32"):
        raise FourierFingerprintV1Error("waveform dtype must be exactly float32")
    if waveform.ndim != 1:
        raise FourierFingerprintV1Error("waveform must be exactly one-dimensional mono")
    if not waveform.flags.c_contiguous:
        raise FourierFingerprintV1Error("waveform must be C-contiguous")
    if not MIN_SAMPLES <= waveform.size <= MAX_SAMPLES:
        raise FourierFingerprintV1Error("waveform must contain 4 to 60 seconds")
    if not bool(np.isfinite(waveform).all()):
        raise FourierFingerprintV1Error("waveform contains a non-finite sample")
    return waveform.copy()


def mean_log_power_spectrum(waveform: np.ndarray) -> np.ndarray:
    """Compute the exact centered-reflect mean log-power spectrum.

    The output has ``N_FFT // 2 + 1`` bins and is float64.  A private copy of
    the caller's waveform is made before any computation, so later caller
    mutation cannot affect the result.
    """

    frozen = _validate_waveform(waveform).astype(np.float64, copy=False)
    half = N_FFT // 2
    padded = np.pad(frozen, (half, half), mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, N_FFT)[
        ::HOP_LENGTH
    ]
    expected_frames = 1 + (frozen.size // HOP_LENGTH)
    if windows.shape != (expected_frames, N_FFT):
        raise FourierFingerprintV1Error("unexpected centered STFT frame geometry")
    frames = windows * periodic_hann_window()[None, :]
    spectrum = np.fft.rfft(frames, n=N_FFT, axis=1)
    power = (spectrum.real * spectrum.real) + (spectrum.imag * spectrum.imag)
    log_power = 10.0 * np.log10(np.clip(power, 1e-10, 1e6))
    mean_spectrum = np.mean(log_power, axis=0, dtype=np.float64)
    if mean_spectrum.shape != ((N_FFT // 2) + 1,):
        raise FourierFingerprintV1Error("unexpected mean-spectrum shape")
    if not bool(np.isfinite(mean_spectrum).all()):
        raise FourierFingerprintV1Error("mean spectrum is not finite")
    return np.ascontiguousarray(mean_spectrum, dtype=np.float64)


def _validate_mean_spectrum(mean_spectrum_db: np.ndarray) -> np.ndarray:
    if type(mean_spectrum_db) is not np.ndarray:
        raise FourierFingerprintV1Error(
            "mean spectrum must be a built-in numpy.ndarray"
        )
    if mean_spectrum_db.dtype not in (np.dtype("float32"), np.dtype("float64")):
        raise FourierFingerprintV1Error("mean spectrum must be float32 or float64")
    if mean_spectrum_db.shape != ((N_FFT // 2) + 1,):
        raise FourierFingerprintV1Error("mean spectrum has the wrong shape")
    if not bool(np.isfinite(mean_spectrum_db).all()):
        raise FourierFingerprintV1Error("mean spectrum contains a non-finite value")
    return np.ascontiguousarray(mean_spectrum_db, dtype=np.float64)


def _lower_hull_knots(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce the official sliding-window unique-argmin knot algorithm."""

    indices: list[int] = []
    hull: list[float] = []
    for start in range(values.size - HULL_AREA + 1):
        patch = values[start : start + HULL_AREA]
        absolute = start + int(np.argmin(patch))
        if absolute not in indices:
            indices.append(absolute)
            hull.append(float(patch[absolute - start]))
    if not indices:
        raise FourierFingerprintV1Error("lower-hull construction produced no knot")
    if indices[0] != 0:
        indices.insert(0, 0)
        hull.insert(0, float(values[0]))
    if indices[-1] != values.size - 1:
        indices.append(values.size - 1)
        hull.append(float(values[-1]))
    if len(indices) < 3 or any(a >= b for a, b in zip(indices, indices[1:])):
        raise FourierFingerprintV1Error("lower-hull knots are not strictly ordered")
    return np.asarray(indices, dtype=np.int64), np.asarray(hull, dtype=np.float64)


def artifact_fingerprint_from_mean_spectrum(
    mean_spectrum_db: np.ndarray,
) -> np.ndarray:
    """Convert a complete mean log-power spectrum into a 7,167-D feature."""

    from scipy.interpolate import interp1d

    frozen = _validate_mean_spectrum(mean_spectrum_db)
    all_frequencies = np.linspace(
        0.0, SAMPLE_RATE / 2.0, num=(N_FFT // 2) + 1, dtype=np.float64
    )
    mask = (all_frequencies > FREQ_MIN_EXCLUSIVE) & (
        all_frequencies < FREQ_MAX_EXCLUSIVE
    )
    frequencies = all_frequencies[mask]
    band = frozen[mask]
    indices, hull_values = _lower_hull_knots(band)
    interpolator = interp1d(
        frequencies[indices],
        hull_values,
        kind="quadratic",
        bounds_error=True,
        assume_sorted=True,
    )
    interpolated = np.asarray(interpolator(frequencies), dtype=np.float64)
    clipped_hull = np.clip(interpolated, MIN_DB, None)
    residue = np.clip(band - clipped_hull, 0.0, None)
    residue = np.clip(residue, 0.0, MAX_RESIDUE_DB)
    denominator = float(np.max(residue)) + NORMALIZATION_EPS
    feature = residue / denominator
    if feature.shape != (7167,):
        raise FourierFingerprintV1Error("unexpected fingerprint shape")
    if not bool(np.isfinite(feature).all()):
        raise FourierFingerprintV1Error("fingerprint is not finite")
    if bool(np.any(feature < 0.0)) or bool(np.any(feature >= 1.0)):
        raise FourierFingerprintV1Error("fingerprint is outside [0,1)")
    return np.ascontiguousarray(feature, dtype=np.float32)


def artifact_fingerprint(waveform: np.ndarray) -> np.ndarray:
    """Compute the fixed spectral residual representation for one file (V1)."""

    return artifact_fingerprint_from_mean_spectrum(mean_log_power_spectrum(waveform))


def contract_manifest() -> dict[str, object]:
    """Return a fresh immutable-value description of the numerical contract."""

    return {
        "schema_version": 1,
        "sample_rate_hz": 16000,
        "duration_samples_inclusive": [64000, 960000],
        "n_fft": 16384,
        "hop_length": 8192,
        "window": "periodic_hann",
        "center": True,
        "pad_mode": "reflect",
        "power": 2,
        "log_power": "10*log10(clip(power,1e-10,1e6))",
        "frequency_hz_exclusive": [1000, 8000],
        "feature_count": 7167,
        "hull_area_bins": 10,
        "hull_interpolation": "quadratic",
        "minimum_hull_db": -45.0,
        "maximum_residue_db": 5.0,
        "normalization_epsilon": 1e-6,
        "output_dtype": "float32",
        "cross_file_state": False,
    }


__all__ = [
    "FourierFingerprintV1Error",
    "artifact_fingerprint",
    "artifact_fingerprint_from_mean_spectrum",
    "contract_manifest",
    "feature_frequencies_hz",
    "mean_log_power_spectrum",
    "periodic_hann_window",
]
