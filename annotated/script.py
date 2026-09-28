#!/usr/bin/env python3
# 보관용 설명 사본(2026-09-28): 원 C693의 실행문은 그대로 두고 주석만 추가했다.
# byte-identical 원본은 ../src/script.py, 구조·권리·재현 한계는 ../MODEL_CARD.md 참고.
# 이 디렉터리는 실행용 제출 패키지가 아니다. 가중치·상류 구현·전체 manifest가 없다.
"""DACON 236749 C693 fixed C688 native-domain tail, File-only integration.

All C596 models, weights, preprocessing, windows and component/presence outputs
are unchanged. Only FILE_FAKE_PROB is recomputed with the original C51 raw/stem
paths, replacing their direct Fourier input with the existing external Music
probability. Legacy global/aligned music and all coefficients stay frozen.
The frozen C688 tail reads the same DF prefix once per window and changes only
the internal raw/stem voice evidence supplied to C660 File. Original external
Voice, Music and Presence outputs remain unchanged. No fitting or routing.
Each file is predicted independently; no evaluation-set statistics or fitting.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import time
import wave
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
DF_ARENA_DIR = MODEL_DIR / "df_arena_1b"
HTDEMUCS_DIR = MODEL_DIR / "htdemucs"
PANNS_DIR = MODEL_DIR / "panns"
SONICS_DIR = MODEL_DIR / "sonics"
SPECTRA_DIR = MODEL_DIR / "spectra_aasist3"
DEEZER_DIR = MODEL_DIR / "deezer_specnn"
FOURIER_DIR = MODEL_DIR / "fourier_fingerprint"
C29_DIR = MODEL_DIR / "c29_lpc_residual_music"

# DACON mounts these directories beside script.py.
DEFAULT_TEST_DIR = BASE_DIR / "data" / "test"
DEFAULT_SAMPLE_SUBMISSION = BASE_DIR / "data" / "sample_submission.csv"
DEFAULT_OUTPUT_PATH = BASE_DIR / "output" / "submission.csv"

# All network-capable model loaders must stay offline.
# 평가 중 다운로드·학습 없이 같은 파일의 정보만 사용한다. 경로별 모델은 로컬 자산이다.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.dont_write_bytecode = True

AUDIO_SAMPLE_RATE = 16_000
PANNS_SAMPLE_RATE = 32_000
DF_SEGMENT_SAMPLES = 64_600
SONICS_SEGMENT_SAMPLES = 80_000
SILENCE_RMS = 1e-5

# Fixed, per-file limits make the worst-case runtime independent of file order.
# Six uniformly spaced crops cover a 60 second file at roughly 10 second gaps.
MAX_DF_SEGMENTS = 6
# 6개 균등 crop의 제한이지 긴 음원 전체의 모든 순간을 빠짐없이 검사한다는 뜻은 아니다.
MAX_SONICS_SEGMENTS = 12
DF_BATCH_SIZE = 2
SPECTRA_BATCH_SIZE = 3
ROBUST_POOL_MAX_WEIGHT = 0.75
SONICS_BATCH_SIZE = 6

# Public Deezer SpecNN full-width V7 signal path.  source_nyquist_372 keeps
# only bins supported by the original 16 kHz stem after exact 44.1 kHz
# resampling.  Per-file pooling is the arithmetic mean of 1-P_REAL.
DEEZER_MODEL_RATE = 44_100
DEEZER_SEGMENT_SAMPLES = 34_398
DEEZER_MAX_SEGMENTS = 12
DEEZER_N_FFT = 2_048
DEEZER_HOP_LENGTH = 512
DEEZER_FRAME_COUNT = 64
DEEZER_BANDWIDTH_BINS = 372
DEEZER_BATCH_SIZE = 12
DEEZER_POWER_MIN = 1e-10
DEEZER_POWER_MAX = 1e6

# Builder-frozen eighth weights.  The three non-negative integers must sum to
# exactly eight.  Supported spaces are "probability" and "logit".
TRIAD_SPACE = "logit"
TRIAD_WEIGHT_S = 2
TRIAD_WEIGHT_D = 3
TRIAD_WEIGHT_F = 3
DEEZER_INPUT = "raw"
TRIAD_WEIGHT_TOTAL = 8
TRIAD_LOGIT_EPSILON = 1e-6

# Frozen C2 File-fusion calibrator fitted only on the public full-400
# development split. Component predictions remain byte/semantically unchanged.
C2_FILE_FUSION_ID = "C2_monotone_calibrated_or"
C2_FILE_LOGIT_EPSILON = 1e-06
C2_VOICE_PARAMETERS = (-2.0869628015642805, 1.0625184085698496, 0.6041475168370548)
C2_MUSIC_PARAMETERS = (0.6957057142670172, 1.0422811159994994, 0.5001081908291056)

C3_FILE_FUSION_ID = 'C3_safeguarded_aligned_or'
C3_FILE_LOGIT_EPSILON = 1e-06
C3_VOICE_PARAMETERS = (-0.8595823450507174, 0.46889799013355016, 0.5244599073233204, 1.254272264295923)
C3_MUSIC_PARAMETERS = (1.1745520470047117, 0.4736794442356167, 0.4120100842222669, 0.7199968613160255)
C51_FILE_FUSION_ID = "C51_c46_uncompressed_fourier_c29_music_or"
C51_MUSIC_PARAMETERS = (0.6247621768875313, 0.1758110900096306, 0.32782341355110767, 0.235938364315404, 0.38193243652953396, 0.0)

DEEZER_NPZ_SHA256 = "a73e90ecd65772699ea5856d7b05e2725a284caf449404673819110223a364d8"
# 주의: 파일명 official_weights와 달리 이 SHA는 자체 미세 조정한 C180 파생 가중치다.
DEEZER_MANIFEST_SHA256 = "483ae36c6c3408bec8006d3283b7c4974b7d951d0284e4266d5ef69d073676bc"
FOURIER_FEATURE_SOURCE_SHA256 = "f4cee4b5aba70dbc11d7b6ff2d457bc4931114dfaccccf5a97381daf5ecaae8a"
FOURIER_COEF_SHA256 = "05cc68dd0f99eea5b96180c0c6274aaa6029416936c3e2e002aaca025ab3885a"
FOURIER_INTERCEPT_SHA256 = "40f157a09b927a172d7b05f3684478814b5f494e12c7eda6d63e9f5b4cfc26c0"
FOURIER_MIN_SAMPLES = 4 * AUDIO_SAMPLE_RATE
FOURIER_MAX_SAMPLES = 60 * AUDIO_SAMPLE_RATE
C29_SOURCE_SHA256 = "cbdb8e1f4ed484999e5cc8ea4376d51166ebe1e8a0a048cc27a1248f96b948fa"
C29_MODEL_SHA256 = "179ab7962b5efdf63ee43abcb2815e093bd146ede131f93e775479512ac961d3"
C29_TRAINING_RECEIPT_SHA256 = "4b024008e1775eae42d36455d1df7490d85392a2c1defcf8ba86332add558ad8"
C29_FEATURE_DIMENSION = 441

# Selected without DACON predictions from 17 public Speech Anti-Spoofing Arena
# domains after excluding the DF-Arena training datasets.  Leave-one-domain-out
# validation retained the gain.  Formula in bona-fide direction:
#   DF logit + 0.69183097 * Spectra raw logit
SPECTRA_BONAFIDE_LOGIT_WEIGHT = 0.69183097

ABLATION_BASELINE = "submit_v5_triad_s2d3f3"
ABLATION_VARIANT = "submission_c51_uncompressed_file_music"
ABLATION_ACTIVE_CHANGE = "file_music_head_receives_separate_fourier_and_c29_logits"

PREDICTION_COLUMNS = [
    "FILE_FAKE_PROB",
    "VOICE_FAKE_PROB",
    "MUSIC_FAKE_PROB",
    "VOICE_PRESENT_PROB",
    "MUSIC_PRESENT_PROB",
]
EXPECTED_COLUMNS = ["ID", *PREDICTION_COLUMNS]
SUPPORTED_AUDIO_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
    ".wma",
}

# Heavy packages are deliberately imported only after --self-test handling.
np = None
torch = None
torchaudio = None
librosa = None
apply_model = None
get_model = None
load_track = None
tqdm = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline deepvoice inference")
    parser.add_argument("--test-dir", type=Path, default=DEFAULT_TEST_DIR)
    parser.add_argument(
        "--sample-submission", type=Path, default=DEFAULT_SAMPLE_SUBMISSION
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run standard-library I/O and schema tests without loading models",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check runtime imports, CUDA, and packaged model files",
    )
    return parser.parse_args(argv)


def import_runtime_dependencies() -> None:
    global np, torch, torchaudio, librosa
    global apply_model, get_model, load_track, tqdm

    if torch is not None:
        return

    import librosa as _librosa
    import numpy as _np
    import torch as _torch
    import torchaudio as _torchaudio
    from demucs.apply import apply_model as _apply_model
    from demucs.pretrained import get_model as _get_model
    from demucs.separate import load_track as _load_track
    from tqdm import tqdm as _tqdm

    np = _np
    torch = _torch
    torchaudio = _torchaudio
    librosa = _librosa
    apply_model = _apply_model
    get_model = _get_model
    load_track = _load_track
    tqdm = _tqdm


def select_device(device_name: str):
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    device = torch.device(device_name)
    if device.type == "cuda":
        torch.set_float32_matmul_precision("high")
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    return device


def find_audio_files(test_dir: Path) -> list[Path]:
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")

    audio_files = sorted(
        (
            path
            for path in test_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ),
        key=lambda path: (path.stem, path.name),
    )
    if not audio_files:
        raise FileNotFoundError(f"No supported audio files found in {test_dir}")

    audio_ids = [path.stem for path in audio_files]
    if len(audio_ids) != len(set(audio_ids)):
        raise ValueError("Audio IDs (filename stems) must be unique")
    return audio_files


def read_sample_submission(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Sample submission not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        rows = list(reader)

    if columns != EXPECTED_COLUMNS:
        raise ValueError(
            f"Expected sample columns {EXPECTED_COLUMNS}, received {columns}"
        )
    if not rows:
        raise ValueError("Sample submission has no rows")

    seen_ids: set[str] = set()
    for row in rows:
        audio_id = str(row["ID"]).strip()
        if not audio_id:
            raise ValueError("Sample submission contains an empty ID")
        if audio_id in seen_ids:
            raise ValueError(f"Duplicate ID in sample submission: {audio_id}")
        seen_ids.add(audio_id)
        row["ID"] = audio_id
    return list(columns), rows


def order_audio_files(
    audio_files: list[Path], submission_rows: list[dict[str, str]]
) -> list[Path]:
    audio_by_id = {path.stem: path for path in audio_files}
    submission_ids = [row["ID"] for row in submission_rows]
    missing = [audio_id for audio_id in submission_ids if audio_id not in audio_by_id]
    extra = [audio_id for audio_id in audio_by_id if audio_id not in submission_ids]
    if missing or extra:
        raise ValueError(
            "Test audio and sample IDs do not match. "
            f"Missing={missing[:5]}, extra={extra[:5]}"
        )
    return [audio_by_id[audio_id] for audio_id in submission_ids]


def validate_prediction_rows(
    rows: list[dict[str, object]], expected_ids: list[str]
) -> None:
    if len(rows) != len(expected_ids):
        raise ValueError(f"Expected {len(expected_ids)} rows, received {len(rows)}")

    actual_ids: list[str] = []
    for index, row in enumerate(rows):
        if list(row.keys()) != EXPECTED_COLUMNS:
            raise ValueError(f"Row {index} does not have the exact output schema")
        audio_id = str(row["ID"])
        actual_ids.append(audio_id)
        for column in PREDICTION_COLUMNS:
            try:
                value = float(row[column])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Non-numeric {column} for {audio_id}") from error
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Invalid {column}={value!r} for {audio_id}; expected [0, 1]"
                )

    if actual_ids != expected_ids:
        raise ValueError("Output IDs or their order differ from sample_submission.csv")
    if len(actual_ids) != len(set(actual_ids)):
        raise ValueError("Output contains duplicate IDs")


def save_submission_atomic(
    output_path: Path,
    columns: list[str],
    rows: list[dict[str, object]],
    expected_ids: list[str],
) -> None:
    if columns != EXPECTED_COLUMNS:
        raise ValueError("Refusing to write a submission with an unexpected header")
    validate_prediction_rows(rows, expected_ids)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        _, saved_rows = read_sample_submission(temporary_path)
        validate_prediction_rows(saved_rows, expected_ids)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def get_segment_starts(
    audio_length: int, segment_samples: int, max_segments: int | None
) -> list[int]:
    if audio_length <= 0:
        raise ValueError("Audio length must be positive")
    if audio_length <= segment_samples:
        return [0]

    last_start = audio_length - segment_samples
    full_count = math.ceil(audio_length / segment_samples)
    count = full_count if max_segments is None else min(full_count, max_segments)
    if count <= 1:
        return [round(last_start / 2)]

    # Deterministic linspace without NumPy, including both file boundaries.
    starts = [round(index * last_start / (count - 1)) for index in range(count)]
    return list(dict.fromkeys(starts))


def extract_df_segment(audio, start: int):
    if audio.size < DF_SEGMENT_SAMPLES:
        repeats = DF_SEGMENT_SAMPLES // audio.size + 1
        return np.tile(audio, repeats)[:DF_SEGMENT_SAMPLES].astype(np.float32)
    return audio[start : start + DF_SEGMENT_SAMPLES].astype(np.float32, copy=False)


def extract_sonics_segment(audio, start: int):
    segment = audio[start : start + SONICS_SEGMENT_SAMPLES]
    if segment.size < SONICS_SEGMENT_SAMPLES:
        segment = np.pad(segment, (0, SONICS_SEGMENT_SAMPLES - segment.size))
    segment = segment.astype(np.float32, copy=False)
    return segment / max(float(np.std(segment)), 1e-6)


def load_audio(audio_path: Path):
    audio, _ = librosa.load(
        audio_path, sr=AUDIO_SAMPLE_RATE, mono=True, dtype=np.float32
    )
    if audio.size == 0 or not np.isfinite(audio).all():
        raise ValueError(f"Decoded audio is empty or non-finite: {audio_path}")
    return audio


def calculate_rms(audio) -> float:
    return float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))


# ---------------------------------------------------------------------------
# Presence: PANNs Cnn14 (official baseline)
# ---------------------------------------------------------------------------


def prepare_panns_labels() -> None:
    source = PANNS_DIR / "class_labels_indices.csv"
    target = Path.home() / "panns_data" / "class_labels_indices.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file() or target.read_bytes() != source.read_bytes():
        shutil.copy2(source, target)


def load_panns_model(device):
    prepare_panns_labels()
    from panns_inference import AudioTagging, labels

    model = AudioTagging(
        checkpoint_path=str(PANNS_DIR / "Cnn14_mAP=0.431.pth"),
        device=device.type,
    )
    groups = json.loads(
        (PANNS_DIR / "component_labels.json").read_text(encoding="utf-8")
    )
    label_to_index = {label: index for index, label in enumerate(labels)}
    voice_indices = [label_to_index[label] for label in groups["voice"]]
    music_indices = [label_to_index[label] for label in groups["music"]]
    return model, voice_indices, music_indices


def make_panns_segments(audio):
    segments = []
    starts = get_segment_starts(audio.size, DF_SEGMENT_SAMPLES, max_segments=None)
    for start in starts:
        segment = extract_df_segment(audio, start)
        segment = librosa.resample(
            segment,
            orig_sr=AUDIO_SAMPLE_RATE,
            target_sr=PANNS_SAMPLE_RATE,
            res_type="soxr_hq",
        )
        segments.append(segment.astype(np.float32))
    return np.stack(segments)


def predict_presence(model, voice_indices: list[int], music_indices: list[int], audio):
    predictions, _ = model.inference(make_panns_segments(audio))
    voice_probability = float(predictions[:, voice_indices].max())
    music_probability = float(predictions[:, music_indices].max())
    if not math.isfinite(voice_probability) or not math.isfinite(music_probability):
        raise RuntimeError("PANNs returned a non-finite presence score")
    return (
        min(max(voice_probability, 0.0), 1.0),
        min(max(music_probability, 0.0), 1.0),
    )


# ---------------------------------------------------------------------------
# Separation: HTDemucs (official baseline, kept resident on the GPU)
# ---------------------------------------------------------------------------


def load_htdemucs_model(device):
    original_torch_load = torch.load

    def load_trusted_checkpoint(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return original_torch_load(*args, **kwargs)

    torch.load = load_trusted_checkpoint
    try:
        model = get_model("htdemucs", repo=HTDEMUCS_DIR)
    finally:
        torch.load = original_torch_load

    # The bundled YAML describes a one-model BagOfModels.  Moving the bag here
    # prevents a CPU<->GPU weight transfer on every evaluation file.
    return model.to(device).eval()


def separate_voice_and_music(audio_path: Path, model, device):
    waveform = load_track(audio_path, model.audio_channels, model.samplerate).float()
    mono_waveform = waveform.mean(0)
    mean = mono_waveform.mean()
    std = mono_waveform.std()

    if float(std) < 1e-8:
        length = round(waveform.shape[-1] * AUDIO_SAMPLE_RATE / model.samplerate)
        silence = np.zeros(max(1, length), dtype=np.float32)
        return silence, silence.copy()

    normalized = (waveform - mean) / std
    with torch.inference_mode():
        sources = apply_model(
            model,
            normalized[None],
            device=device,
            shifts=0,
            split=True,
            overlap=0.25,
            progress=False,
        )[0]
    sources = sources * std + mean

    vocal_index = model.sources.index("vocals")
    voice = sources[vocal_index].mean(0, keepdim=True)
    # Same accompaniment definition as the official baseline, without an
    # intermediate stack allocation.
    music = (sources.sum(dim=0) - sources[vocal_index]).mean(0, keepdim=True)
    components = torch.cat((voice, music), dim=0)
    components = torchaudio.functional.resample(
        components, model.samplerate, AUDIO_SAMPLE_RATE
    )
    return (
        components[0].cpu().numpy().astype(np.float32),
        components[1].cpu().numpy().astype(np.float32),
    )


# ---------------------------------------------------------------------------
# Component fake: DF-Arena + Spectra voice, SONICS alpha-5s music
# ---------------------------------------------------------------------------


def load_df_arena_model(device):
    if str(MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(MODEL_DIR))
    from df_arena_1b.modeling_antispoofing import DF_Arena_1B_Antispoofing

    previous_directory = Path.cwd()
    os.chdir(DF_ARENA_DIR)
    try:
        model = DF_Arena_1B_Antispoofing.from_pretrained(
            str(DF_ARENA_DIR),
            local_files_only=True,
            low_cpu_mem_usage=True,
        )
    finally:
        os.chdir(previous_directory)
    model = model.to(device).eval()
    return model, int(model.config.label2id["spoof"])


def load_sonics_model(device):
    if str(MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(MODEL_DIR))
    from sonics import load_sonics_detector

    return load_sonics_detector(SONICS_DIR, device)


def load_deezer_arrays() -> dict[str, object]:
    """Load the audited pickle-free SpecNN deployment arrays fail-closed."""

    weights_path = DEEZER_DIR / "deezer_specnn_official_weights.v1.npz"
    manifest_path = DEEZER_DIR / "deezer_specnn_official_weights.v1.manifest.json"
    if sha256_file(weights_path) != DEEZER_NPZ_SHA256:
        raise RuntimeError("Deezer SpecNN NPZ hash mismatch")
    if sha256_file(manifest_path) != DEEZER_MANIFEST_SHA256:
        raise RuntimeError("Deezer SpecNN manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact = manifest["artifact"]
    if (
        artifact["sha256"] != DEEZER_NPZ_SHA256
        or artifact["size"] != weights_path.stat().st_size
        or artifact["array_count"] != 40
        or artifact["pickle_allowed"] is not False
    ):
        raise RuntimeError("Deezer SpecNN artifact contract mismatch")

    records = manifest["arrays"]
    expected_names = [record["name"] for record in records]
    if len(expected_names) != 40 or len(set(expected_names)) != 40:
        raise RuntimeError("Deezer SpecNN manifest array names are invalid")
    arrays: dict[str, object] = {}
    with np.load(weights_path, allow_pickle=False) as archive:
        if archive.files != expected_names:
            raise RuntimeError("Deezer SpecNN NPZ member order or names drifted")
        for record in records:
            name = record["name"]
            value = np.ascontiguousarray(archive[name])
            if (
                value.dtype != np.dtype("float32")
                or list(value.shape) != record["shape"]
                or not np.isfinite(value).all()
                or hashlib.sha256(value.tobytes(order="C")).hexdigest()
                != record["c_order_sha256"]
            ):
                raise RuntimeError(f"Invalid Deezer SpecNN array: {name}")
            arrays[name] = value
    return arrays


def build_deezer_model(device):
    """Build the parity-audited full-width PyTorch SpecNN network."""

    arrays = load_deezer_arrays()

    class DeezerSpecNN(torch.nn.Module):
        def __init__(self):
            super().__init__()
            channels = (16, 32, 64, 128, 256, 512)
            inputs = (1, *channels[:-1])
            self.convolutions = torch.nn.ModuleList(
                torch.nn.Conv2d(in_channels, out_channels, 3, padding=1)
                for in_channels, out_channels in zip(inputs, channels)
            )
            self.batch_norms = torch.nn.ModuleList(
                torch.nn.BatchNorm2d(out_channels, eps=0.001)
                for out_channels in channels
            )
            self.dense = torch.nn.Linear(512, 128)
            self.output = torch.nn.Linear(128, 1)

        def forward(self, value):
            for convolution, batch_norm in zip(
                self.convolutions, self.batch_norms
            ):
                value = batch_norm(
                    torch.nn.functional.max_pool2d(
                        torch.nn.functional.relu(convolution(value)), 2
                    )
                )
            value = value.mean(dim=(-2, -1))
            value = torch.nn.functional.silu(self.dense(value))
            return torch.sigmoid(self.output(value))

    model = DeezerSpecNN()
    state = model.state_dict()
    expected_state_arrays = {
        name for name in state if not name.endswith("num_batches_tracked")
    }
    if set(arrays) != expected_state_arrays:
        raise RuntimeError("Deezer SpecNN arrays do not match model state")
    with torch.no_grad():
        for name, value in arrays.items():
            if tuple(state[name].shape) != tuple(value.shape):
                raise RuntimeError(f"Deezer SpecNN tensor geometry drift: {name}")
            state[name].copy_(torch.from_numpy(value))
    return model.to(device).eval()


def load_fourier_model():
    """Load the audited float32 public-data logistic head and feature API."""

    feature_path = FOURIER_DIR / "fourier_fingerprint_features_v1.py"
    coefficient_path = FOURIER_DIR / "coef.float32.npy"
    intercept_path = FOURIER_DIR / "intercept.float32.npy"
    if sha256_file(feature_path) != FOURIER_FEATURE_SOURCE_SHA256:
        raise RuntimeError("Fourier feature source hash mismatch")
    if sha256_file(coefficient_path) != FOURIER_COEF_SHA256:
        raise RuntimeError("Fourier coefficient hash mismatch")
    if sha256_file(intercept_path) != FOURIER_INTERCEPT_SHA256:
        raise RuntimeError("Fourier intercept hash mismatch")
    if str(FOURIER_DIR) not in sys.path:
        sys.path.insert(0, str(FOURIER_DIR))
    from fourier_fingerprint_features_v1 import artifact_fingerprint
    from fourier_fingerprint_features_v1 import contract_manifest

    coefficient = np.ascontiguousarray(
        np.load(coefficient_path, allow_pickle=False)
    )
    intercept = np.ascontiguousarray(np.load(intercept_path, allow_pickle=False))
    contract = contract_manifest()
    if (
        coefficient.dtype != np.dtype("float32")
        or coefficient.shape != (7167,)
        or intercept.dtype != np.dtype("float32")
        or intercept.shape != (1,)
        or contract["feature_count"] != 7167
        or contract["sample_rate_hz"] != AUDIO_SAMPLE_RATE
        or not np.isfinite(coefficient).all()
        or not np.isfinite(intercept).all()
    ):
        raise RuntimeError("Fourier deployment geometry mismatch")
    return coefficient, np.float32(intercept[0]), artifact_fingerprint, contract


def load_spectra_model(device):
    if str(MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(MODEL_DIR))
    from safetensors.torch import load_model as load_safetensors_model
    from spectra_aasist3 import SpectraAASIST3

    model = SpectraAASIST3()
    # strict=True rejects any architecture/checkpoint mismatch.  The released
    # file is self-contained, including the XLS-R-300M encoder tensors.
    load_safetensors_model(
        model,
        str(SPECTRA_DIR / "model.safetensors"),
        strict=True,
        device="cpu",
    )
    return model.to(device).eval()


def preemphasize(audio, coefficient: float = 0.97):
    """Apply Spectra's public Arena preprocessing to one complete component."""

    emphasized = np.empty_like(audio, dtype=np.float32)
    emphasized[0] = audio[0]
    emphasized[1:] = audio[1:] - coefficient * audio[:-1]
    return emphasized


def predict_voice_fake(
    df_model,
    df_fake_label_index: int,
    spectra_model,
    audio,
    device,
) -> float:
    """Fuse paired per-window voice evidence, then apply official max pooling."""

    if calculate_rms(audio) < SILENCE_RMS:
        return 0.0

    starts = get_segment_starts(
        audio.size, DF_SEGMENT_SAMPLES, max_segments=MAX_DF_SEGMENTS
    )
    df_segments = [extract_df_segment(audio, start) for start in starts]

    # DF's public benchmark score is softmax bona-fide probability.  Its logit
    # is exactly (bona-fide raw logit - spoof raw logit); compute the opposite
    # fake direction without a numerically fragile softmax/logit round trip.
    df_fake_logits: list[float] = []
    df_bonafide_index = 1 - df_fake_label_index
    for offset in range(0, len(df_segments), DF_BATCH_SIZE):
        batch = np.stack(df_segments[offset : offset + DF_BATCH_SIZE])
        batch_tensor = torch.from_numpy(batch).to(device)
        with torch.inference_mode():
            logits = df_model(input_values=batch_tensor)["logits"].float()
            values = (
                logits[:, df_fake_label_index] - logits[:, df_bonafide_index]
            ).cpu().tolist()
        df_fake_logits.extend(float(value) for value in values)

    # The published Spectra Arena wrapper preemphasizes the complete waveform,
    # then takes/tile-pads a 64,600-sample window and reads logit index 1 as
    # bona-fide.  Use the identical crop locations as DF for paired evidence.
    emphasized = preemphasize(audio)
    spectra_segments = [extract_df_segment(emphasized, start) for start in starts]
    spectra_bonafide_logits: list[float] = []
    for offset in range(0, len(spectra_segments), SPECTRA_BATCH_SIZE):
        batch = np.stack(spectra_segments[offset : offset + SPECTRA_BATCH_SIZE])
        batch_tensor = torch.from_numpy(batch).to(device)
        with torch.inference_mode():
            values = spectra_model(batch_tensor).float()[:, 1].cpu().tolist()
        spectra_bonafide_logits.extend(float(value) for value in values)

    if len(df_fake_logits) != len(spectra_bonafide_logits):
        raise RuntimeError("Voice detector segment counts differ")
    denominator = 1.0 + SPECTRA_BONAFIDE_LOGIT_WEIGHT
    fused_fake_logits: list[float] = []
    for df_fake_logit, spectra_bonafide_logit in zip(
        df_fake_logits, spectra_bonafide_logits
    ):
        fused_fake_logit = (
            df_fake_logit
            - SPECTRA_BONAFIDE_LOGIT_WEIGHT * spectra_bonafide_logit
        ) / denominator
        fused_fake_logits.append(fused_fake_logit)
    return stable_sigmoid(robust_pool_logits(fused_fake_logits))


def predict_music_fake(model, audio, device) -> float:
    """Score only the isolated accompaniment with SONICS alpha-5s."""

    if calculate_rms(audio) < SILENCE_RMS:
        return 0.0
    starts = get_segment_starts(
        audio.size, SONICS_SEGMENT_SAMPLES, max_segments=MAX_SONICS_SEGMENTS
    )
    segments = [extract_sonics_segment(audio, start) for start in starts]
    logits: list[float] = []
    for offset in range(0, len(segments), SONICS_BATCH_SIZE):
        batch = np.stack(segments[offset : offset + SONICS_BATCH_SIZE])
        batch_tensor = torch.from_numpy(batch).to(device)
        with torch.inference_mode():
            values = model(batch_tensor).float().flatten().cpu().tolist()
        logits.extend(float(value) for value in values)

    # Retain v1's fixed file-internal partial-fake pooling while removing its
    # cross-domain DF music score and raw-mixture label contamination.
    strongest = sorted(logits, reverse=True)[: min(2, len(logits))]
    pooled_logit = 0.75 * strongest[0] + 0.25 * (
        sum(strongest) / len(strongest)
    )
    return stable_sigmoid(pooled_logit)


def get_deezer_segment_starts(model_rate_samples: int) -> list[int]:
    if type(model_rate_samples) is not int or model_rate_samples <= 0:
        raise ValueError("Deezer model-rate length must be a positive integer")
    if model_rate_samples <= DEEZER_SEGMENT_SAMPLES:
        return [0]
    last_start = model_rate_samples - DEEZER_SEGMENT_SAMPLES
    count = min(
        math.ceil(model_rate_samples / DEEZER_SEGMENT_SAMPLES),
        DEEZER_MAX_SEGMENTS,
    )
    if count <= 1:
        return [round(last_start / 2)]
    starts = [round(index * last_start / (count - 1)) for index in range(count)]
    return list(dict.fromkeys(starts))


def adapt_deezer_source_nyquist_372(audio):
    """Apply the frozen V7 16 kHz -> full-width NCHW signal path."""

    if (
        type(audio) is not np.ndarray
        or audio.dtype != np.dtype("float32")
        or audio.ndim != 1
        or not audio.flags.c_contiguous
        or audio.size <= 0
        or not np.isfinite(audio).all()
    ):
        raise ValueError("Deezer input must be finite contiguous mono float32")
    source = torch.from_numpy(audio)
    model_rate = torchaudio.functional.resample(
        source,
        orig_freq=AUDIO_SAMPLE_RATE,
        new_freq=DEEZER_MODEL_RATE,
        lowpass_filter_width=6,
        rolloff=0.99,
        resampling_method="sinc_interp_hann",
        beta=None,
    )
    pieces = []
    for start in get_deezer_segment_starts(int(model_rate.numel())):
        piece = model_rate[start : start + DEEZER_SEGMENT_SAMPLES]
        if piece.numel() < DEEZER_SEGMENT_SAMPLES:
            piece = torch.nn.functional.pad(
                piece,
                (0, DEEZER_SEGMENT_SAMPLES - int(piece.numel())),
                mode="constant",
                value=0.0,
            )
        pieces.append(piece)
    segments = torch.stack(pieces, dim=0)
    window = torch.hann_window(
        DEEZER_N_FFT,
        periodic=True,
        dtype=torch.float32,
        device=segments.device,
        requires_grad=False,
    )
    spectrum = torch.stft(
        segments,
        n_fft=DEEZER_N_FFT,
        hop_length=DEEZER_HOP_LENGTH,
        win_length=DEEZER_N_FFT,
        window=window,
        center=False,
        pad_mode="reflect",
        normalized=False,
        onesided=True,
        return_complex=True,
    )
    if tuple(spectrum.shape[1:]) != (1025, DEEZER_FRAME_COUNT):
        raise RuntimeError("Deezer STFT geometry drift")
    power = spectrum.abs().square()
    transformed = torch.log10(
        torch.clamp(power, min=DEEZER_POWER_MIN, max=DEEZER_POWER_MAX)
    )
    normalized = (transformed + 4.0) / 3.0
    features = (
        normalized[:, :DEEZER_BANDWIDTH_BINS, :]
        .transpose(1, 2)
        .unsqueeze(1)
        .contiguous()
    )
    if tuple(features.shape[1:]) != (
        1,
        DEEZER_FRAME_COUNT,
        DEEZER_BANDWIDTH_BINS,
    ) or not bool(torch.isfinite(features).all()):
        raise RuntimeError("Deezer input tensor geometry or values are invalid")
    return features


def predict_deezer_music_fake(model, audio, device) -> float:
    features = adapt_deezer_source_nyquist_372(audio)
    fake_probabilities = []
    with torch.inference_mode():
        for offset in range(0, int(features.shape[0]), DEEZER_BATCH_SIZE):
            real = model(
                features[offset : offset + DEEZER_BATCH_SIZE].to(device)
            ).reshape(-1)
            if not bool(torch.isfinite(real).all()) or bool(
                ((real < 0.0) | (real > 1.0)).any()
            ):
                raise RuntimeError("Deezer SpecNN returned invalid P_REAL")
            fake_probabilities.append(1.0 - real)
    fake = torch.cat(fake_probabilities)
    if int(fake.numel()) != int(features.shape[0]):
        raise RuntimeError("Deezer segment/output count mismatch")
    result = float(fake.mean().item())
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise RuntimeError("Deezer pooled P_FAKE is invalid")
    return result


def predict_fourier_music_fake(
    coefficient,
    intercept,
    artifact_fingerprint,
    raw_complete_audio,
) -> float:
    """Score the complete original mono 16 kHz file, never a Demucs stem."""

    waveform = np.ascontiguousarray(raw_complete_audio, dtype=np.float32)
    if waveform.ndim != 1 or waveform.size == 0 or not bool(np.isfinite(waveform).all()):
        raise ValueError("Fourier input must be finite, non-empty mono audio")
    # The official evaluation contract is 4--60 s, but codec boundary
    # rounding and the organizer's shorter dummy WAV must not abort the whole
    # submission.  This adjustment is deterministic and strictly per-file.
    if waveform.size < FOURIER_MIN_SAMPLES:
        waveform = np.pad(
            waveform,
            (0, FOURIER_MIN_SAMPLES - waveform.size),
            mode="constant",
        )
    elif waveform.size > FOURIER_MAX_SAMPLES:
        waveform = waveform[:FOURIER_MAX_SAMPLES]
    waveform = np.ascontiguousarray(waveform, dtype=np.float32)
    feature = artifact_fingerprint(waveform)
    if feature.dtype != np.dtype("float32") or feature.shape != (7167,):
        raise RuntimeError("Fourier feature geometry drift")
    logit = float(np.dot(coefficient, feature) + np.float32(intercept))
    if not math.isfinite(logit):
        raise RuntimeError("Fourier logistic head returned a non-finite logit")
    return stable_sigmoid(logit)


def load_c29_model():
    source_path = MODEL_DIR / "c29_lpc_residual_head_v0_1.py"
    model_path = C29_DIR / "c29_lpc_residual_model.v0_1.npz"
    receipt_path = C29_DIR / "C29_FULL_PUBLIC_TRAINING_RECEIPT.v0_1.json"
    pinned = (
        (source_path, C29_SOURCE_SHA256),
        (model_path, C29_MODEL_SHA256),
        (receipt_path, C29_TRAINING_RECEIPT_SHA256),
    )
    for path, digest in pinned:
        if not path.is_file() or path.is_symlink() or sha256_file(path) != digest:
            raise RuntimeError(f"C29 packaged asset mismatch: {path}")
    if str(MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(MODEL_DIR))
    import c29_lpc_residual_head_v0_1 as c29_head

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("status") != "PASS_C29_FULL_PUBLIC_FIXED_HEAD"
        or receipt.get("private_evaluation_data_accessed") is not False
        or receipt.get("counts", {}).get("feature_dimension") != C29_FEATURE_DIMENSION
        or receipt.get("pins", {}).get("model", {}).get("sha256") != C29_MODEL_SHA256
    ):
        raise RuntimeError("C29 training receipt contract mismatch")
    arrays = c29_head.load_model(model_path)
    expected_shapes = {
        "scaler_mean": (C29_FEATURE_DIMENSION,),
        "scaler_scale": (C29_FEATURE_DIMENSION,),
        "coefficient": (C29_FEATURE_DIMENSION,),
        "intercept": (1,),
    }
    if any(tuple(arrays[name].shape) != shape for name, shape in expected_shapes.items()):
        raise RuntimeError("C29 deployment-array geometry mismatch")
    if any(not bool(np.isfinite(arrays[name]).all()) for name in expected_shapes):
        raise RuntimeError("C29 deployment arrays contain non-finite values")
    encoded_names = bytes(np.asarray(arrays["feature_names_utf8"], dtype=np.uint8))
    if json.loads(encoded_names.decode("utf-8")) != c29_head.feature_names():
        raise RuntimeError("C29 feature-name contract mismatch")
    return c29_head, arrays


def predict_c29_music_fake(c29_head, arrays, raw_complete_audio) -> float:
    waveform = c29_head.canonicalize_waveform(raw_complete_audio, AUDIO_SAMPLE_RATE)
    feature = c29_head.extract_features(waveform)
    if feature.shape != (C29_FEATURE_DIMENSION,) or not bool(np.isfinite(feature).all()):
        raise RuntimeError("C29 feature geometry drift")
    probability = float(c29_head.predict_from_arrays(feature[None, :], arrays)[0])
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise RuntimeError("C29 head returned an invalid probability")
    return probability


def blend_classical_music_scores(
    fourier_probability: float, c29_probability: float
) -> float:
    scores = (float(fourier_probability), float(c29_probability))
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in scores):
        raise ValueError("Classical detector inputs must be finite probabilities in [0,1]")
    return stable_sigmoid(
        0.75 * triad_logit(fourier_probability)
        + 0.25 * triad_logit(c29_probability)
    )


def validate_triad_configuration() -> None:
    weights = (TRIAD_WEIGHT_S, TRIAD_WEIGHT_D, TRIAD_WEIGHT_F)
    if (
        TRIAD_SPACE not in ("probability", "logit")
        or DEEZER_INPUT not in ("raw", "stem")
        or any(type(weight) is not int or weight < 0 for weight in weights)
        or sum(weights) != TRIAD_WEIGHT_TOTAL
        or TRIAD_WEIGHT_TOTAL != 8
    ):
        raise RuntimeError("Invalid frozen triad score-space or eighth weights")


def triad_logit(probability: float) -> float:
    clipped = min(
        max(float(probability), TRIAD_LOGIT_EPSILON),
        1.0 - TRIAD_LOGIT_EPSILON,
    )
    return math.log(clipped) - math.log1p(-clipped)


def blend_triad_music_scores(
    sonics_probability: float,
    deezer_probability: float,
    fourier_probability: float,
) -> float:
    validate_triad_configuration()
    scores = (
        float(sonics_probability),
        float(deezer_probability),
        float(fourier_probability),
    )
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in scores):
        raise ValueError("Triad inputs must be finite probabilities in [0,1]")
    weights = (TRIAD_WEIGHT_S, TRIAD_WEIGHT_D, TRIAD_WEIGHT_F)
    if TRIAD_SPACE == "probability":
        return sum(weight * value for weight, value in zip(weights, scores)) / 8.0
    blended_logit = sum(
        weight * triad_logit(value) for weight, value in zip(weights, scores)
    ) / 8.0
    return stable_sigmoid(blended_logit)


def robust_pool_logits(logits: list[float]) -> float:
    if not logits or not all(math.isfinite(value) for value in logits):
        raise ValueError("Pooling requires finite logits")
    return ROBUST_POOL_MAX_WEIGHT * max(logits) + (
        1.0 - ROBUST_POOL_MAX_WEIGHT
    ) * (sum(logits) / len(logits))


def stable_sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def combine_file_fake_score(
    voice_fake: float,
    music_fake: float,
    voice_present: float,
    music_present: float,
) -> float:
    """Frozen C2 monotone-calibrated branches followed by probabilistic OR."""

    inputs = (voice_fake, music_fake, voice_present, music_present)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in inputs):
        raise ValueError("C2 File-fusion inputs must be finite probabilities in [0,1]")
    voice_linear = (
        C2_VOICE_PARAMETERS[0]
        + C2_VOICE_PARAMETERS[1] * triad_logit(voice_fake)
        + C2_VOICE_PARAMETERS[2] * triad_logit(voice_present)
    )
    music_linear = (
        C2_MUSIC_PARAMETERS[0]
        + C2_MUSIC_PARAMETERS[1] * triad_logit(music_fake)
        + C2_MUSIC_PARAMETERS[2] * triad_logit(music_present)
    )
    voice_branch = stable_sigmoid(voice_linear)
    music_branch = stable_sigmoid(music_linear)
    result = 1.0 - (1.0 - voice_branch) * (1.0 - music_branch)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise RuntimeError("C2 File-fusion output is invalid")
    return result

def bounded_probability(value: float, name: str, audio_id: str) -> float:
    if not math.isfinite(value):
        raise RuntimeError(f"Non-finite {name} prediction for {audio_id}")
    return min(max(float(value), 0.0), 1.0)


def c3_interval_bounds(starts: list[int], window_samples: int, audio_length: int):
    ends = [min(start + window_samples, audio_length) for start in starts]
    if not starts or any(start < 0 or end <= start for start, end in zip(starts, ends)):
        raise RuntimeError("C3 interval geometry drift")
    return starts, ends


def c3_overlap_weighted(
    target_starts, target_ends, source_starts, source_ends, source_probabilities
) -> list[float]:
    # 서로 다른 모델의 창을 '현재 파일 내부' 시간 겹침 길이로 맞춘다.
    # 겹침이 없더라도 아래 fallback은 같은 파일의 최근접 창만 사용한다.
    if not (
        len(target_starts) == len(target_ends)
        and len(source_starts) == len(source_ends) == len(source_probabilities)
        and target_starts
        and source_starts
    ):
        raise RuntimeError("C3 overlap array geometry drift")
    result = []
    for target_start, target_end in zip(target_starts, target_ends):
        overlaps = [
            max(0, min(target_end, source_end) - max(target_start, source_start))
            for source_start, source_end in zip(source_starts, source_ends)
        ]
        total = sum(overlaps)
        if total <= 0:
            # Some codecs are decoded to slightly different durations by the
            # raw and Demucs paths.  Use only the nearest interval from this
            # same file, with an explicit deterministic tie-break.  Normal
            # overlap arithmetic is untouched.
            target_center_twice = target_start + target_end
            nearest_index = min(
                range(len(source_starts)),
                key=lambda index: (
                    max(
                        source_starts[index] - target_end,
                        target_start - source_ends[index],
                        0,
                    ),
                    abs(
                        source_starts[index]
                        + source_ends[index]
                        - target_center_twice
                    ),
                    index,
                ),
            )
            result.append(float(source_probabilities[nearest_index]))
            continue
        result.append(
            sum(overlap * probability for overlap, probability in zip(overlaps, source_probabilities))
            / total
        )
    return result


def predict_presence_c3(model, voice_indices, music_indices, audio):
    starts = get_segment_starts(int(audio.size), DF_SEGMENT_SAMPLES, max_segments=None)
    predictions, _ = model.inference(make_panns_segments(audio))
    predictions = np.asarray(predictions)
    if predictions.ndim != 2 or predictions.shape[0] != len(starts):
        raise RuntimeError("C3 PANNs segment/output count mismatch")
    voice_scores = predictions[:, list(voice_indices)].max(axis=1).astype(np.float64)
    music_scores = predictions[:, list(music_indices)].max(axis=1).astype(np.float64)
    if (
        not np.isfinite(voice_scores).all()
        or not np.isfinite(music_scores).all()
        or np.any((voice_scores < 0.0) | (voice_scores > 1.0))
        or np.any((music_scores < 0.0) | (music_scores > 1.0))
    ):
        raise RuntimeError("C3 PANNs returned invalid segment probabilities")
    starts, ends = c3_interval_bounds(starts, DF_SEGMENT_SAMPLES, int(audio.size))
    return (
        float(voice_scores.max()),
        float(music_scores.max()),
        starts,
        ends,
        voice_scores.tolist(),
        music_scores.tolist(),
    )


def predict_voice_fake_c3(
    df_model, df_fake_label_index, spectra_model, audio, device, *, file_tail=None
):
    # 두 출력의 용도를 구분한다: 원 DF는 외부 Voice, C688 tail은 File 내부 Voice.
    # 창 위치·Spectra는 공유하되 외부 Voice 점수를 학습 tail로 덮어쓰지 않는다.
    if calculate_rms(audio) < SILENCE_RMS:
        empty = (0.0, [], [], [])
        return (empty, empty) if file_tail is not None else empty
    starts = get_segment_starts(
        int(audio.size), DF_SEGMENT_SAMPLES, max_segments=MAX_DF_SEGMENTS
    )
    segments = [extract_df_segment(audio, start) for start in starts]
    df_logits = []
    file_df_logits = []
    bonafide_index = 1 - df_fake_label_index
    for offset in range(0, len(segments), DF_BATCH_SIZE):
        batch = torch.from_numpy(np.stack(segments[offset : offset + DF_BATCH_SIZE])).to(device)
        with torch.inference_mode():
            if file_tail is None:
                output = df_model(input_values=batch)["logits"].float()
            else:
                from c693_tail import forward_shared
                output, file_output = forward_shared(df_model, file_tail, batch)
                file_df_logits.extend(
                    float(value) for value in
                    (file_output[:, df_fake_label_index] - file_output[:, bonafide_index]).cpu().tolist()
                )
        df_logits.extend(
            float(value)
            for value in (output[:, df_fake_label_index] - output[:, bonafide_index]).cpu().tolist()
        )
    emphasized = preemphasize(audio)
    spectra_segments = [extract_df_segment(emphasized, start) for start in starts]
    spectra_logits = []
    for offset in range(0, len(spectra_segments), SPECTRA_BATCH_SIZE):
        batch = torch.from_numpy(
            np.stack(spectra_segments[offset : offset + SPECTRA_BATCH_SIZE])
        ).to(device)
        with torch.inference_mode():
            values = spectra_model(batch).float()[:, 1].cpu().tolist()
        spectra_logits.extend(float(value) for value in values)
    if len(df_logits) != len(spectra_logits) or len(df_logits) != len(starts):
        raise RuntimeError("C3 voice detector segment counts differ")
    denominator = 1.0 + SPECTRA_BONAFIDE_LOGIT_WEIGHT
    # DF는 spoof-bonafide margin, Spectra는 bonafide 방향이므로 Spectra 항을 뺀다.
    fused = [
        (df_value - SPECTRA_BONAFIDE_LOGIT_WEIGHT * spectra_value) / denominator
        for df_value, spectra_value in zip(df_logits, spectra_logits)
    ]
    starts, ends = c3_interval_bounds(starts, DF_SEGMENT_SAMPLES, int(audio.size))
    original = (stable_sigmoid(robust_pool_logits(fused)), starts, ends, fused)
    if file_tail is None:
        return original
    if len(file_df_logits) != len(starts):
        raise RuntimeError("C693 learned tail segment counts differ")
    file_fused = [
        (df_value - SPECTRA_BONAFIDE_LOGIT_WEIGHT * spectra_value) / denominator
        for df_value, spectra_value in zip(file_df_logits, spectra_logits)
    ]
    adapted = (stable_sigmoid(robust_pool_logits(file_fused)), starts, ends, file_fused)
    return original, adapted


def predict_sonics_fake_c3(model, audio, device):
    if calculate_rms(audio) < SILENCE_RMS:
        return 0.0, [], [], []
    starts = get_segment_starts(
        int(audio.size), SONICS_SEGMENT_SAMPLES, max_segments=MAX_SONICS_SEGMENTS
    )
    segments = [extract_sonics_segment(audio, start) for start in starts]
    logits = []
    for offset in range(0, len(segments), SONICS_BATCH_SIZE):
        batch = torch.from_numpy(np.stack(segments[offset : offset + SONICS_BATCH_SIZE])).to(device)
        with torch.inference_mode():
            values = model(batch).float().flatten().cpu().tolist()
        logits.extend(float(value) for value in values)
    strongest = sorted(logits, reverse=True)[: min(2, len(logits))]
    global_probability = stable_sigmoid(
        0.75 * strongest[0] + 0.25 * (sum(strongest) / len(strongest))
    )
    starts, ends = c3_interval_bounds(starts, SONICS_SEGMENT_SAMPLES, int(audio.size))
    return global_probability, starts, ends, [stable_sigmoid(value) for value in logits]


def adapt_deezer_c3(audio):
    source = torch.from_numpy(audio)
    model_rate = torchaudio.functional.resample(
        source,
        orig_freq=AUDIO_SAMPLE_RATE,
        new_freq=DEEZER_MODEL_RATE,
        lowpass_filter_width=6,
        rolloff=0.99,
        resampling_method="sinc_interp_hann",
        beta=None,
    )
    model_length = int(model_rate.numel())
    starts = get_deezer_segment_starts(model_length)
    pieces = []
    for start in starts:
        piece = model_rate[start : start + DEEZER_SEGMENT_SAMPLES]
        if piece.numel() < DEEZER_SEGMENT_SAMPLES:
            piece = torch.nn.functional.pad(
                piece, (0, DEEZER_SEGMENT_SAMPLES - int(piece.numel())), value=0.0
            )
        pieces.append(piece)
    segments = torch.stack(pieces, dim=0)
    window = torch.hann_window(DEEZER_N_FFT, periodic=True, dtype=torch.float32)
    spectrum = torch.stft(
        segments,
        n_fft=DEEZER_N_FFT,
        hop_length=DEEZER_HOP_LENGTH,
        win_length=DEEZER_N_FFT,
        window=window,
        center=False,
        pad_mode="reflect",
        normalized=False,
        onesided=True,
        return_complex=True,
    )
    if tuple(spectrum.shape[1:]) != (1025, DEEZER_FRAME_COUNT):
        raise RuntimeError("C3 Deezer STFT geometry drift")
    transformed = torch.log10(
        torch.clamp(spectrum.abs().square(), min=DEEZER_POWER_MIN, max=DEEZER_POWER_MAX)
    )
    features = (
        ((transformed + 4.0) / 3.0)[:, :DEEZER_BANDWIDTH_BINS, :]
        .transpose(1, 2)
        .unsqueeze(1)
        .contiguous()
    )
    if tuple(features.shape[1:]) != (1, DEEZER_FRAME_COUNT, DEEZER_BANDWIDTH_BINS):
        raise RuntimeError("C3 Deezer input geometry drift")
    return features, starts, model_length


def predict_deezer_fake_c3(model, audio, device):
    features, model_starts, model_length = adapt_deezer_c3(audio)
    batches = []
    with torch.inference_mode():
        for offset in range(0, int(features.shape[0]), DEEZER_BATCH_SIZE):
            real = model(features[offset : offset + DEEZER_BATCH_SIZE].to(device)).reshape(-1)
            if not bool(torch.isfinite(real).all()) or bool(((real < 0) | (real > 1)).any()):
                raise RuntimeError("C3 Deezer returned invalid P_REAL")
            batches.append(1.0 - real)
    fake = torch.cat(batches)
    if int(fake.numel()) != len(model_starts):
        raise RuntimeError("C3 Deezer segment/output count mismatch")
    probabilities = [float(value) for value in fake.cpu().tolist()]
    model_ends = [min(start + DEEZER_SEGMENT_SAMPLES, model_length) for start in model_starts]
    source_starts = [start * AUDIO_SAMPLE_RATE // DEEZER_MODEL_RATE for start in model_starts]
    source_ends = [
        min(
            (end * AUDIO_SAMPLE_RATE + DEEZER_MODEL_RATE - 1) // DEEZER_MODEL_RATE,
            int(audio.size),
        )
        for end in model_ends
    ]
    return float(fake.mean().item()), source_starts, source_ends, probabilities


def aligned_voice_event_c3(
    starts, ends, fused_logits, presence_starts, presence_ends, presence_probabilities
) -> float:
    if not fused_logits:
        return 0.0
    local_presence = c3_overlap_weighted(
        starts, ends, presence_starts, presence_ends, presence_probabilities
    )
    event_logits = [
        triad_logit(stable_sigmoid(logit) * (0.5 + 0.5 * presence))
        for logit, presence in zip(fused_logits, local_presence)
    ]
    return stable_sigmoid(robust_pool_logits(event_logits))


def aligned_music_event_c3(
    sonics_starts,
    sonics_ends,
    sonics_probabilities,
    deezer_starts,
    deezer_ends,
    deezer_probabilities,
    presence_starts,
    presence_ends,
    presence_probabilities,
    fourier_probability,
) -> float:
    if not sonics_probabilities:
        return 0.0
    local_deezer = c3_overlap_weighted(
        sonics_starts, sonics_ends, deezer_starts, deezer_ends, deezer_probabilities
    )
    local_presence = c3_overlap_weighted(
        sonics_starts, sonics_ends, presence_starts, presence_ends, presence_probabilities
    )
    events = []
    for sonics, deezer, presence in zip(
        sonics_probabilities, local_deezer, local_presence
    ):
        triad_probability = stable_sigmoid(
            (
                2.0 * triad_logit(sonics)
                + 3.0 * triad_logit(deezer)
                + 3.0 * triad_logit(fourier_probability)
            )
            / 8.0
        )
        events.append(triad_logit(triad_probability * (0.5 + 0.5 * presence)))
    strongest = sorted(events, reverse=True)[: min(2, len(events))]
    return stable_sigmoid(
        0.75 * strongest[0] + 0.25 * (sum(strongest) / len(strongest))
    )


def combine_c51_file_fake_score(
    voice_fake,
    music_fake,
    voice_present,
    music_present,
    aligned_voice,
    aligned_music,
    fourier_music_fake,
    c29_music_fake,
) -> float:
    # 고정 logistic이 음성 사건 qV와 음악 사건 qM을 만든 뒤 noisy-OR로 결합한다.
    # 수치는 calibration의 완전성을 보장하지 않는다. 이름만 보고 단일 탐지기로 읽지 말 것.
    values = (
        voice_fake,
        music_fake,
        voice_present,
        music_present,
        aligned_voice,
        aligned_music,
        fourier_music_fake,
        c29_music_fake,
    )
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("C51 inputs must be finite probabilities in [0,1]")
    voice_linear = C3_VOICE_PARAMETERS[0] + sum(
        coefficient * triad_logit(value)
        for coefficient, value in zip(
            C3_VOICE_PARAMETERS[1:], (voice_fake, voice_present, aligned_voice)
        )
    )
    music_inputs = (
        music_fake,
        music_present,
        aligned_music,
        fourier_music_fake,
        c29_music_fake,
    )
    music_linear = C51_MUSIC_PARAMETERS[0] + sum(
        coefficient * triad_logit(value)
        for coefficient, value in zip(C51_MUSIC_PARAMETERS[1:], music_inputs)
    )
    voice_branch = stable_sigmoid(voice_linear)
    music_branch = stable_sigmoid(music_linear)
    return 1.0 - (1.0 - voice_branch) * (1.0 - music_branch)


def combine_c660_file_fake_score(
    voice_fake,
    raw_voice_fake,
    legacy_music_fake,
    external_music_fake,
    voice_present,
    music_present,
    aligned_voice,
    raw_aligned_voice,
    aligned_music,
    c29_music_fake,
) -> float:
    """Reuse both frozen C51 paths; replace only the direct Fourier slot."""
    # C660의 핵심: direct Fourier 인수 자리에 이미 계산한 외부 Music 앙상블을 전달.
    # Fourier 자체는 legacy/외부 Music 안에 남아 있다. 두 raw/stem OR의 큰 값을 사용한다.
    stem_file = combine_c51_file_fake_score(
        voice_fake, legacy_music_fake, voice_present, music_present,
        aligned_voice, aligned_music, external_music_fake, c29_music_fake,
    )
    raw_file = combine_c51_file_fake_score(
        raw_voice_fake, legacy_music_fake, voice_present, music_present,
        raw_aligned_voice, aligned_music, external_music_fake, c29_music_fake,
    )
    return max(stem_file, raw_file)


def run_inference(
    audio_files: list[Path], submission_rows: list[dict[str, object]], device
) -> list[dict[str, object]]:
    started = time.monotonic()
    print(
        "Loading C241: C212 models, music-presence-conditioned Deezer and File-only raw voice rescue..."
    )
    validate_triad_configuration()
    panns_model, voice_indices, music_indices = load_panns_model(device)
    df_model, fake_label_index = load_df_arena_model(device)
    from c693_tail import load_tail
    file_tail = load_tail(MODEL_DIR / "c693" / "C688_TRAINED_TAIL.pt", device)
    spectra_model = load_spectra_model(device)
    demucs_model = load_htdemucs_model(device)
    sonics_model = load_sonics_model(device)
    deezer_model = build_deezer_model(device)
    fourier_coefficient, fourier_intercept, fourier_feature, _ = load_fourier_model()
    c29_head, c29_arrays = load_c29_model()
    sys.path.insert(0, str(MODEL_DIR / "c159"))
    sys.path.insert(0, str(MODEL_DIR / "c212"))
    from c159_runtime import MusicWindowModel
    from c212_runtime import load_second_deezer, predict_dual_deezer
    sys.path.insert(0, str(MODEL_DIR / "c239"))
    from c239_runtime import pool_deezer_by_presence
    sys.path.insert(0, str(MODEL_DIR / "c346"))
    import c346_runtime as c346
    c212_anchor = sys.modules[__name__]
    second_deezer = load_second_deezer(c212_anchor, deezer_model, MODEL_DIR / "c212", device)
    selected_music_model = MusicWindowModel(MODEL_DIR / "c159")
    sys.path.insert(0, str(MODEL_DIR / "c596_eat"))
    from c596_runtime import C596Music
    c596_music_model = C596Music(MODEL_DIR / "c596_eat", device=device)

    for index, audio_path in enumerate(tqdm(audio_files, desc="C3+C29 inference")):
        audio_id = audio_path.stem
        original_audio = load_audio(audio_path)
        (
            voice_present,
            music_present,
            presence_starts,
            presence_ends,
            voice_presence_segments,
            music_presence_segments,
        ) = predict_presence_c3(
            panns_model, voice_indices, music_indices, original_audio
        )
        voice_audio, music_audio = separate_voice_and_music(audio_path, demucs_model, device)
        original_voice, adapted_voice = predict_voice_fake_c3(
            df_model, fake_label_index, spectra_model, voice_audio, device, file_tail=file_tail
        )
        voice_fake, voice_starts, voice_ends, voice_logits = original_voice
        file_voice_fake, file_vs, file_ve, file_vl = adapted_voice
        (
            sonics_music_fake,
            sonics_starts,
            sonics_ends,
            sonics_probabilities,
        ) = predict_sonics_fake_c3(sonics_model, music_audio, device)
        (
            deezer_music_fake,
            deezer_starts,
            deezer_ends,
            deezer_probabilities,
        ) = predict_dual_deezer(c212_anchor, deezer_model, second_deezer, original_audio, device)
        deezer_music_fake = pool_deezer_by_presence(
            c212_anchor, deezer_music_fake, deezer_starts, deezer_ends,
            deezer_probabilities, presence_starts, presence_ends,
            music_presence_segments,
        )
        fourier_music_fake = predict_fourier_music_fake(
            fourier_coefficient, fourier_intercept, fourier_feature, original_audio
        )
        c29_music_fake = predict_c29_music_fake(c29_head, c29_arrays, original_audio)
        # C29 계산은 역사적 경로와 검증 보존용. 현재 C51의 direct C29 계수는 0.0이다.
        selected_dasheng = selected_music_model.predict(
            original_audio, presence_starts, presence_ends, music_presence_segments
        )
        # C212 replaces ONLY indirect C29; direct File C29 stays original.
        classical_music_fake = blend_classical_music_scores(
            fourier_music_fake, selected_dasheng
        )
        # 여기의 두 번째 성분은 selected Dasheng이며, C29가 아니다.
        music_fake = blend_triad_music_scores(
            sonics_music_fake, deezer_music_fake, classical_music_fake
        )
        external_music_fake = c346.global_probability(
            c212_anchor, sonics_music_fake, deezer_music_fake,
            fourier_music_fake, selected_dasheng
        )
        # 이 C346 값은 아래 C596의 최종 외부 Music으로 덮어써지는 역사적 중간값이다.
        aligned_voice = aligned_voice_event_c3(
            voice_starts,
            voice_ends,
            voice_logits,
            presence_starts,
            presence_ends,
            voice_presence_segments,
        )
        aligned_music = aligned_music_event_c3(
            sonics_starts,
            sonics_ends,
            sonics_probabilities,
            deezer_starts,
            deezer_ends,
            deezer_probabilities,
            presence_starts,
            presence_ends,
            music_presence_segments,
            classical_music_fake,
        )
        file_fake = combine_c51_file_fake_score(
            voice_fake,
            music_fake,
            voice_present,
            music_present,
            aligned_voice,
            aligned_music,
            fourier_music_fake,
            c29_music_fake,
        )
        # C232: retain C212's stem voice and all four external outputs.
        # Raw voice uses the SAME existing models, windows and C3 calibrator.
        original_raw_voice, adapted_raw_voice = predict_voice_fake_c3(
            df_model, fake_label_index, spectra_model, original_audio, device, file_tail=file_tail
        )
        raw_voice_fake, raw_vs, raw_ve, raw_vl = original_raw_voice
        file_raw_voice_fake, file_raw_vs, file_raw_ve, file_raw_vl = adapted_raw_voice
        raw_aligned_voice = aligned_voice_event_c3(
            raw_vs, raw_ve, raw_vl, presence_starts, presence_ends,
            voice_presence_segments,
        )
        raw_file_fake = combine_c51_file_fake_score(
            raw_voice_fake, music_fake, voice_present, music_present,
            raw_aligned_voice, aligned_music, fourier_music_fake, c29_music_fake,
        )
        # Same music event in both File calls: max here == OR(max(qV), qM).
        file_fake = max(file_fake, raw_file_fake)
        # C596: original C349 File is complete; change external Music only.
        c596_music = c596_music_model.predict(
            original_audio, c212_anchor, presence_starts, presence_ends,
            music_presence_segments, deezer_music_fake, fourier_music_fake, selected_dasheng)
        external_music_fake = c596_music["Music"]
        # 최종 외부 Music = D239/Fourier/Dasheng/EAT의 고정 logit 결합.
        # 원 C51으로 위에서 계산한 file_fake도 아래에서 다시 계산되므로 최종 출력이 아니다.
        file_aligned_voice = aligned_voice_event_c3(
            file_vs, file_ve, file_vl, presence_starts, presence_ends, voice_presence_segments,
        )
        file_raw_aligned_voice = aligned_voice_event_c3(
            file_raw_vs, file_raw_ve, file_raw_vl, presence_starts, presence_ends, voice_presence_segments,
        )
        # C660: only File's direct music-evidence slot changes. All existing
        # model calls and the four component/presence outputs stay unchanged.
        file_fake = combine_c660_file_fake_score(
            voice_fake=file_voice_fake,
            raw_voice_fake=file_raw_voice_fake,
            legacy_music_fake=music_fake,
            external_music_fake=external_music_fake,
            voice_present=voice_present,
            music_present=music_present,
            aligned_voice=file_aligned_voice,
            raw_aligned_voice=file_raw_aligned_voice,
            aligned_music=aligned_music,
            c29_music_fake=c29_music_fake,
        )
        # 위 마지막 호출이 실제 FILE_FAKE_PROB: C688 raw/stem 음성과 C660 음악 연결을 사용.
        # 아래 나머지 네 출력은 원 Voice, C596 Music, PANNs 두 Presence를 유지한다.
        values = {
            "FILE_FAKE_PROB": file_fake,
            "VOICE_FAKE_PROB": voice_fake,
            "MUSIC_FAKE_PROB": external_music_fake,
            "VOICE_PRESENT_PROB": voice_present,
            "MUSIC_PRESENT_PROB": music_present,
        }
        row = submission_rows[index]
        if row["ID"] != audio_id:
            raise RuntimeError("Internal ID ordering invariant was violated")
        for column, value in values.items():
            row[column] = round(bounded_probability(value, column, audio_id), 10)
        if device.type == "cuda" and (index + 1) % 100 == 0:
            peak_gib = torch.cuda.max_memory_allocated(device) / (1024**3)
            elapsed_minutes = (time.monotonic() - started) / 60.0
            print(
                f"Processed {index + 1}/{len(audio_files)}; "
                f"elapsed={elapsed_minutes:.1f}m, peak_cuda={peak_gib:.2f}GiB"
            )
    del panns_model, df_model, spectra_model, demucs_model, sonics_model
    del deezer_model, fourier_coefficient, fourier_feature
    del c29_head, c29_arrays, second_deezer, selected_music_model, c596_music_model
    del file_tail
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return submission_rows

def verify_packaged_model_files() -> None:
    # 원 제출 manifest의 모든 파일을 요구한다. 이 소스 보관본에 모델 자산은 포함되지 않는다.
    # 주석으로 달라진 파일 크기/SHA를 맞추려고 원 검증 값을 바꾸거나 우회하지 않는다.
    manifest_path = MODEL_DIR / "MODEL_MANIFEST.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing model manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = MODEL_DIR / entry["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Missing packaged model file: {path}")
        if path.stat().st_size != entry["size"]:
            raise RuntimeError(f"Unexpected size for packaged model file: {path}")


def check_environment() -> None:
    import_runtime_dependencies()
    verify_packaged_model_files()
    # panns-inference 0.1.1 imports its label CSV at module import time.
    prepare_panns_labels()
    import demucs
    import panns_inference
    import safetensors
    import transformers

    details = {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "torchaudio": torchaudio.__version__,
        "numpy": np.__version__,
        "librosa": librosa.__version__,
        "transformers": transformers.__version__,
        "demucs": getattr(demucs, "__version__", "unknown"),
        "panns_inference": getattr(panns_inference, "__version__", "unknown"),
        "safetensors": getattr(safetensors, "__version__", "unknown"),
        "cuda_available": torch.cuda.is_available(),
    }
    if torch.cuda.is_available():
        details["cuda_device"] = torch.cuda.get_device_name(0)
        details["cuda_version"] = torch.version.cuda
    print(json.dumps(details, indent=2, ensure_ascii=False))


def run_self_test() -> None:
    global np, torch
    import numpy as _np
    import torch as _torch

    np = _np
    torch = _torch
    validate_triad_configuration()
    probe_scores = (0.2, 0.7, 0.9)
    observed_blend = blend_triad_music_scores(*probe_scores)
    weights = (TRIAD_WEIGHT_S, TRIAD_WEIGHT_D, TRIAD_WEIGHT_F)
    if TRIAD_SPACE == "probability":
        expected_blend = sum(
            weight * score for weight, score in zip(weights, probe_scores)
        ) / 8.0
    else:
        raw_logits = []
        for score in probe_scores:
            clipped = min(
                max(score, TRIAD_LOGIT_EPSILON),
                1.0 - TRIAD_LOGIT_EPSILON,
            )
            raw_logits.append(math.log(clipped) - math.log1p(-clipped))
        expected_blend = stable_sigmoid(
            sum(weight * value for weight, value in zip(weights, raw_logits))
            / 8.0
        )
    if observed_blend != expected_blend:
        raise AssertionError("Triad blend formula drifted")

    observed_classical = blend_classical_music_scores(0.2, 0.8)
    expected_classical = stable_sigmoid(
        0.75 * triad_logit(0.2) + 0.25 * triad_logit(0.8)
    )
    if observed_classical != expected_classical or not math.isclose(
        observed_classical, 1.0 / 3.0, rel_tol=0.0, abs_tol=1e-15
    ):
        raise AssertionError("C29 classical evidence split drifted")

    per_file_scores = {
        "a": (0.1, 0.4, 0.8),
        "b": (0.9, 0.2, 0.3),
        "c": (0.5, 0.5, 0.5),
    }
    forward = {
        key: blend_triad_music_scores(*value)
        for key, value in per_file_scores.items()
    }
    reverse = {
        key: blend_triad_music_scores(*per_file_scores[key])
        for key in reversed(tuple(per_file_scores))
    }
    if forward != reverse:
        raise AssertionError("Triad score depends on cross-file order or state")

    deezer_model = build_deezer_model(torch.device("cpu"))
    with torch.inference_mode():
        output = deezer_model(
            torch.zeros(
                (2, 1, DEEZER_FRAME_COUNT, DEEZER_BANDWIDTH_BINS),
                dtype=torch.float32,
            )
        )
    if tuple(output.shape) != (2, 1) or not bool(torch.isfinite(output).all()):
        raise AssertionError("Deezer model tensor geometry failed")

    coefficient, intercept, _, contract = load_fourier_model()
    if (
        coefficient.shape != (7167,)
        or coefficient.dtype != np.dtype("float32")
        or not math.isfinite(intercept)
        or contract["feature_count"] != 7167
        or contract["duration_samples_inclusive"] != [64000, 960000]
    ):
        raise AssertionError("Fourier parameter or feature geometry failed")

    if get_segment_starts(64_000, DF_SEGMENT_SAMPLES, 6) != [0]:
        raise AssertionError("Short segment start calculation failed")
    starts = get_segment_starts(960_000, DF_SEGMENT_SAMPLES, 6)
    if len(starts) != 6 or starts[0] != 0 or starts[-1] != 895_400:
        raise AssertionError("Uniform segment coverage failed")

    with tempfile.TemporaryDirectory(prefix="deepvoice_selftest_") as directory:
        root = Path(directory)
        test_dir = root / "data" / "test"
        test_dir.mkdir(parents=True)
        for filename in ("b.WAV", "a.mp3", "c.flac"):
            (test_dir / filename).touch()

        sample_path = root / "data" / "sample_submission.csv"
        with sample_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            for audio_id in ("c", "a", "b"):
                writer.writerow({column: audio_id if column == "ID" else 0 for column in EXPECTED_COLUMNS})

        files = find_audio_files(test_dir)
        columns, rows = read_sample_submission(sample_path)
        ordered = order_audio_files(files, rows)
        if [path.stem for path in ordered] != ["c", "a", "b"]:
            raise AssertionError("Sample-based audio ordering failed")

        for index, row in enumerate(rows):
            for column_index, column in enumerate(PREDICTION_COLUMNS):
                row[column] = (index + column_index + 1) / 10
        output = root / "output" / "submission.csv"
        expected_ids = [row["ID"] for row in rows]
        save_submission_atomic(output, columns, rows, expected_ids)
        _, saved = read_sample_submission(output)
        validate_prediction_rows(saved, expected_ids)

        invalid = [dict(row) for row in rows]
        invalid[0]["FILE_FAKE_PROB"] = float("nan")
        try:
            validate_prediction_rows(invalid, expected_ids)
        except ValueError:
            pass
        else:
            raise AssertionError("NaN output was not rejected")

        wav_path = root / "probe.wav"
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(AUDIO_SAMPLE_RATE)
            wav_file.writeframes(b"\x00\x00" * 160)
        if wav_path.stat().st_size <= 44:
            raise AssertionError("WAV fixture creation failed")

    print(
        "Self-test passed: triad formula/eighths, per-file invariance, Deezer "
        "model geometry, Fourier geometry, paths, schema, and atomic CSV"
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_arguments(argv)
    if args.self_test:
        run_self_test()
        return
    if args.check_env:
        check_environment()
        return

    import_runtime_dependencies()
    verify_packaged_model_files()
    device = select_device(args.device)
    audio_files = find_audio_files(args.test_dir)
    columns, submission_rows = read_sample_submission(args.sample_submission)
    audio_files = order_audio_files(audio_files, submission_rows)
    expected_ids = [row["ID"] for row in submission_rows]

    started = time.monotonic()
    submission_rows = run_inference(
        audio_files, submission_rows, device
    )
    save_submission_atomic(args.output, columns, submission_rows, expected_ids)
    elapsed_minutes = (time.monotonic() - started) / 60.0
    print(
        f"Saved {len(submission_rows)} predictions to {args.output} "
        f"in {elapsed_minutes:.2f} minutes"
    )


if __name__ == "__main__":
    main()
