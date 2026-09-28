# Reproducibility and Execution Scope

I use this lightweight archive to preserve C693's executable source and documentation. I omit model weights, audio, upstream model implementations, and installation wheels, so **the source alone cannot run inference immediately**. The submission ZIP preserved in my original workspace is the authoritative package for an actual rerun.

## Roles of the three sets of materials

| Material | Role |
|---|---|
| `src/` | Byte-for-byte copies of C693's `script.py`, `c693_tail.py`, and eight required integration helpers |
| `annotated/` | Explanatory copies of the two main files with English comments; their executable ASTs must match the originals, but their bytes/hashes differ |
| ZIP and training records in my original workspace | Evidence for rerunning, preserved alongside the actual weights, original upstream implementations, configurations, licenses, and training materials |

I keep the annotated copies separate from the original submission files. The original package checks Fourier/C29 source hashes, EAT source hashes, and a manifest of all file sizes; even comments can cause those checks to fail. AST equality does not replace verification of numerical results or the execution environment.

## Authoritative local locations

The following paths are **relative to my original workspace**. The large files at these paths are not included in this repository.

```text
artifacts/submit_c693.zip
artifacts/submit_c693.zip.receipt.json
artifacts/submit_c704.zip
artifacts/submit_c704.zip.receipt.json
research/c687_df_native_music_adaptation/c693_package_integration/package_src/
```

The recorded size of `submit_c693.zip` is 7,288,933,071 bytes. The ZIP receipt, `package_src/model/MODEL_MANIFEST.json`, and `SHA256SUMS_C693.txt` record the original inventory. I did not rehash large weights or the entire ZIP, or rerun the package, while preparing this archive.

C693's `C693_DEPLOYMENT.json` records the packaging state on 2026-09-24. I preserve its null official ADS and items unverified at that time without overwriting them with the server results I recorded later. Documents named for C660 and the existing `MODEL_PROVENANCE.md` also describe earlier stages. The actual C693 source and C693 deployment information should be read together to understand the archived structure.

## Runtime assets required for restoration

The paths below are relative to the original `package_src/model/`. I exclude these weights, arrays, and vendor implementations from this repository.

| Component | Required files and directories |
|---|---|
| DF-Arena | `df_arena_1b/pytorch_model.bin`, `config.json`, Python implementation, `facebook/wav2vec2-xls-r-1b/config.json` |
| C688 tail | `c693/C688_TRAINED_TAIL.pt` |
| Spectra | `spectra_aasist3/model.safetensors`, `wav2vec2_config.json`, Python implementation |
| HTDemucs | `htdemucs/955717e8-8726e21a.th`, `htdemucs.yaml` |
| PANNs | `panns/Cnn14_mAP=0.431.pth`, `class_labels_indices.csv`, `component_labels.json` |
| SONICS | `sonics/pytorch_model.bin`, `config.json`, Python implementation |
| C180 Deezer | `deezer_specnn/deezer_specnn_official_weights.v1.npz`, corresponding manifest |
| C205 Deezer | `c212/C205_COMPAT40.npz`, corresponding manifest |
| Fourier | `fourier_fingerprint/coef.float32.npy`, `intercept.float32.npy`, original feature helper |
| C29 | `c29_lpc_residual_music/c29_lpc_residual_model.v0_1.npz`, training receipt, original helper |
| Dasheng | Weights, configuration, and Python implementation in `c159/dasheng/`; `c159/music_head.npz` |
| EAT | `c596_eat/model.safetensors`, `C593_FINAL_MODEL.pt`, configuration and Python implementation |
| Installation | timm/torchvision wheels in `c596_eat/wheels/`, `SERVER_CONSTRAINTS.txt`, original requirements |

The DF backbone's configuration loader reads the nested `facebook/wav2vec2-xls-r-1b/config.json` locally. Omitting this directory breaks offline restoration. PANNs prepares the bundled label CSV in the runtime user's `panns_data` directory.

The original `verify_packaged_model_files()` checks **the existence and size of every file** listed in `MODEL_MANIFEST.json`, including historical documents and receipts, as well as weights used in computation. Restoring only the table above therefore does not satisfy the original script's execution contract. The complete file structure and original notices in the original ZIP must be preserved.

The following are key pinned values. These hashes identify the original files, not the annotated copies.

| File | Recorded SHA-256 |
|---|---|
| `script.py` | `200d9b69f8651f2856a39763e0bfb725a98cf9f3e900b22e8e916ceff8ad1d84` |
| `c693_tail.py` | `f178536cc58858d7415ae5f651fa3bf7a79e48ed09c791e14b5cb14965ab1e0c` |
| `C688_TRAINED_TAIL.pt` | `0281f889b4506af2f7d0d4280ba5f2b458e538a57dfcea1a020e112d1e968afc` |
| `C593_FINAL_MODEL.pt` | `3b788240581c7fe6e53859f6009c63f92139a62db670e8f85466a930ccf375fa` |

## Execution environment and input/output contract

The original submission targets Ubuntu 22.04.5, Python 3.11.15, NVIDIA L4, torch/torchaudio 2.7.1+cu128, and transformers 4.57.6. Models and configurations load locally, with no network access after installation. [Official evaluation environment guide](https://dacon.io/competitions/official/236749/overview/evaluation)

Dependencies include NumPy, SciPy, soundfile, librosa, torch, torchaudio, transformers, safetensors, einops, demucs, panns-inference, tqdm, timm, and their transitive dependencies. The original `requirements.txt` is not a general-purpose list for installing an entire environment from scratch. It uses `--no-index` to install bundled timm 0.9.12 and torchvision 0.22.1+cu128 wheels for Linux CP311 over the server's base packages, while constraining core versions. These Linux wheels are not for Windows.

The original ZIP reads `data/test/` and `data/sample_submission.csv` and writes `output/submission.csv`. The CSV contains `ID` and five probability columns; the code checks ID matching, missing/duplicate rows, finite values, and probability ranges. I preserve the historical discrepancy between an `open/` reference on the evaluation page and the actual baseline's `data/test/` path.

Any restoration requires separate checks of the original ZIP, installation, offline loading, input formats, memory use, and full runtime in an environment with the necessary licenses and access rights. I did not install dependencies, import models, decode audio, run neural networks, or measure performance for this archive. I therefore do not describe a single generic `pip install` command as sufficient for reproduction.

## Training reproduction records

The actual training records for the C693 tail are at:

```text
research/c687_df_native_music_adaptation/C687_TRAIN_PLAN.json
research/c687_df_native_music_adaptation/c688_stratified/train_stratified.py
research/c687_df_native_music_adaptation/c688_stratified/C688_TRAIN_RESULT.json
research/c687_df_native_music_adaptation/c688_stratified/C688_INPUT_REGISTRY.json
research/c687_df_native_music_adaptation/c688_stratified/manifests/UPDATE_128.json
```

The C687 plan links to the C616 speech source/audio manifests, C683 native music source/audio manifests, the waveforms actually consumed and their encoded parents, and license records. `C688_TRAIN_RESULT` records the original tail used for initialization, code/scope/input hashes, the fixed schedule, and update completion results. C688 repeated 270 unique bags/596 unique windows on that schedule for 640 bag exposures/1,792 window forwards. Unique data counts and repeated exposures are different quantities.

The training lineage of the inherited components is documented in the original package at:

```text
model/fourier_fingerprint/FOURIER_LOGISTIC_MODEL.v1.json
model/c159/C151_ACTUAL_TRAINING_MANIFEST.json
model/c190/C180_ACTUAL_TRAINING_MANIFEST.json
model/c190/C190_DEPLOYMENT_TRAINING_RECEIPT.json
model/c212/C205_TRAINING_PRESERVATION.json
model/c212/C205_TRAIN_RESULT.json
model/c596_eat/provenance/C593_FREEZE.md
model/c596_eat/provenance/C594_FIT_TRANSFER_FREEZE.md
model/C693_DEPLOYMENT.json
model/c693/C693_PROVENANCE.md
```

The archive's `src/` focuses on inference code; it is not a complete training environment and data bundle. Reproduction metadata does not replace the requirement to submit the actual training files. I preserve original training audio, generated audio, source parents, checkpoints, and STOP/completion records in my original workspace. Excluding them from this repository does not mean deleting the local originals.

## Distinguishing scores from verification

The [model card](MODEL_CARD.md) contains the server scores I recorded. Earlier CPU smoke checks, static hash/structure checks, public proxy evaluations, and server scores provide different kinds of evidence. Preserving source code and adding English comments does not constitute a new performance evaluation. I make no additional claim of reaching the target ADS of 0.85 or generalizing to the private evaluation data.
