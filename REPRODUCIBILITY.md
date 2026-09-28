# 재현성 및 실행 범위

이 저장소는 C693의 실행 소스와 설명을 남기는 경량 보관본이다. 모델 가중치, 오디오, 상류 모델 구현, 설치 wheel을 생략했으므로 **소스만으로 즉시 실행할 수 없다**. 실제 재실행의 정본은 원 작업공간에 보존된 제출 ZIP이다.

## 세 가지 자료의 역할

| 자료 | 역할 |
|---|---|
| `src/` | C693의 `script.py`, `c693_tail.py`, 필요한 통합 helper 8개의 원본 바이트 사본 |
| `annotated/` | main 두 파일에 한국어 주석을 추가한 설명본. 실행 로직의 AST는 원본과 같아야 하지만 바이트/hash는 다름 |
| 원 작업공간의 ZIP·학습 기록 | 실제 가중치·원 상류 구현·설정·라이선스·학습 자료와 함께 보존하는 재실행 근거 |

주석본으로 원 제출 파일을 덮어쓰지 않는다. Fourier/C29 source hash, EAT source hash, 전체 파일 크기 manifest 검사가 있어 주석만 추가해도 원 패키지 검사와 충돌할 수 있다. AST 동일성은 수치 결과나 실행 환경 재현 검증을 대신하지 않는다.

## 로컬 정본 위치

아래는 **원 작업공간 기준 상대 경로**다. 이 저장소에 해당 대용량 파일을 포함했다는 뜻은 아니다.

```text
artifacts/submit_c693.zip
artifacts/submit_c693.zip.receipt.json
artifacts/submit_c704.zip
artifacts/submit_c704.zip.receipt.json
research/c687_df_native_music_adaptation/c693_package_integration/package_src/
```

`submit_c693.zip`의 기록상 크기는 7,288,933,071 bytes다. ZIP receipt와 `package_src/model/MODEL_MANIFEST.json`, `SHA256SUMS_C693.txt`가 원 inventory를 기록한다. 이번 보관 작업에서는 큰 가중치나 ZIP 전체를 새로 해시하거나 재실행하지 않았다.

C693의 `C693_DEPLOYMENT.json`은 2026-09-24 패키징 당시의 문서다. 그 문서의 official ADS null 또는 당시 미검증 상태를 나중 사용자 보고 서버 결과로 덮어쓰지 않는다. C660 명칭의 문서와 기존 `MODEL_PROVENANCE.md`도 이전 단계의 기록이다. 현재 구조는 실제 C693 소스와 C693 deployment 정보를 함께 읽는다.

## 복원에 필요한 런타임 자산

아래 경로는 원 `package_src/model/` 기준이다. 이 저장소에서는 아래 가중치·배열·vendor 구현을 제외한다.

| 구성 | 필요한 파일·디렉터리 |
|---|---|
| DF-Arena | `df_arena_1b/pytorch_model.bin`, `config.json`, Python 구현, `facebook/wav2vec2-xls-r-1b/config.json` |
| C688 tail | `c693/C688_TRAINED_TAIL.pt` |
| Spectra | `spectra_aasist3/model.safetensors`, `wav2vec2_config.json`, Python 구현 |
| HTDemucs | `htdemucs/955717e8-8726e21a.th`, `htdemucs.yaml` |
| PANNs | `panns/Cnn14_mAP=0.431.pth`, `class_labels_indices.csv`, `component_labels.json` |
| SONICS | `sonics/pytorch_model.bin`, `config.json`, Python 구현 |
| C180 Deezer | `deezer_specnn/deezer_specnn_official_weights.v1.npz`, 대응 manifest |
| C205 Deezer | `c212/C205_COMPAT40.npz`, 대응 manifest |
| Fourier | `fourier_fingerprint/coef.float32.npy`, `intercept.float32.npy`, 원 feature helper |
| C29 | `c29_lpc_residual_music/c29_lpc_residual_model.v0_1.npz`, training receipt, 원 helper |
| Dasheng | `c159/dasheng/`의 가중치·설정·Python 구현, `c159/music_head.npz` |
| EAT | `c596_eat/model.safetensors`, `C593_FINAL_MODEL.pt`, 설정·Python 구현 |
| 설치 | `c596_eat/wheels/`의 timm/torchvision wheel, `SERVER_CONSTRAINTS.txt`, 원 requirements |

DF backbone의 설정 로더는 중첩된 `facebook/wav2vec2-xls-r-1b/config.json`을 로컬 경로로 읽는다. 이 디렉터리를 생략하면 오프라인 복원이 성립하지 않는다. PANNs는 동봉 label CSV를 사용자 `panns_data`에 준비한다.

원 `verify_packaged_model_files()`는 연산에 쓰는 가중치뿐 아니라 `MODEL_MANIFEST.json`에 나열된 과거 문서·receipt 등 **모든 파일의 존재와 크기**를 검사한다. 따라서 위 표만 복원하는 것으로 원 script의 실행 계약이 완성되지는 않는다. 원 ZIP의 전체 파일 구조와 원 고지를 보존하는 것이 기준이다.

주요 고정 값은 다음과 같다. 기록의 해시는 원 파일을 식별하며 주석본의 해시가 아니다.

| 파일 | 기록된 SHA-256 |
|---|---|
| `script.py` | `200d9b69f8651f2856a39763e0bfb725a98cf9f3e900b22e8e916ceff8ad1d84` |
| `c693_tail.py` | `f178536cc58858d7415ae5f651fa3bf7a79e48ed09c791e14b5cb14965ab1e0c` |
| `C688_TRAINED_TAIL.pt` | `0281f889b4506af2f7d0d4280ba5f2b458e538a57dfcea1a020e112d1e968afc` |
| `C593_FINAL_MODEL.pt` | `3b788240581c7fe6e53859f6009c63f92139a62db670e8f85466a930ccf375fa` |

## 실행 환경과 입출력 계약

원 제출 환경은 Ubuntu 22.04.5, Python 3.11.15, NVIDIA L4, torch/torchaudio 2.7.1+cu128, transformers 4.57.6을 전제로 했다. 모델·설정은 로컬에서 로드하며 설치 이후 네트워크가 없는 환경을 대상으로 한다. [공식 평가 환경 안내](https://dacon.io/competitions/official/236749/overview/evaluation)

직접 의존성은 NumPy, SciPy, soundfile, librosa, torch, torchaudio, transformers, safetensors, einops, demucs, panns-inference, tqdm, timm 및 전이 의존성이다. 원 `requirements.txt`는 전체 환경을 새로 설치하는 범용 목록이 아니다. 서버 기본 패키지 위에 `--no-index`로 동봉 timm0.9.12와 Linux CP311용 torchvision0.22.1+cu128 wheel을 설치하고 core 버전을 제약한다. 이 Linux wheel은 Windows용이 아니다.

원 ZIP의 입력은 `data/test/`와 `data/sample_submission.csv`, 출력은 `output/submission.csv`다. CSV 열은 `ID`와 다섯 확률이며, ID 일치·누락·중복·finite·범위 검사를 수행한다. 평가 페이지의 일부 `open/` 문구와 실제 baseline의 `data/test/`가 달랐다는 과거 불일치 기록은 유지한다.

복원 후에는 라이선스와 접근 권한을 갖춘 환경에서 원 ZIP·설치·오프라인 로드·입력 형식·메모리·전체 실행 시간을 별도로 확인해야 한다. 이번 정리에서는 설치, 모델 import, audio decode, 신경망 실행, 성능 측정을 수행하지 않았다. 저장소에 일반적인 `pip install` 한 번으로 재현된다는 안내를 넣지 않는 이유다.

## 학습 재현 기록

C693 tail의 실제 학습 경로는 다음이다.

```text
research/c687_df_native_music_adaptation/C687_TRAIN_PLAN.json
research/c687_df_native_music_adaptation/c688_stratified/train_stratified.py
research/c687_df_native_music_adaptation/c688_stratified/C688_TRAIN_RESULT.json
research/c687_df_native_music_adaptation/c688_stratified/C688_INPUT_REGISTRY.json
research/c687_df_native_music_adaptation/c688_stratified/manifests/UPDATE_128.json
```

C687 plan은 C616 speech source/audio manifest와 C683 native music source/audio manifest, 실제 소비 waveform과 encoded parent, 라이선스 기록에 연결된다. `C688_TRAIN_RESULT`는 초기 원 tail, code/scope/input hash, 결정된 schedule, update 완료 결과를 기록한다. C688은 270 unique bag/596 unique window를 고정 schedule로 반복해 640 bag exposure/1,792 window forward를 수행했다. unique 자료 수와 반복 노출 수를 구별한다.

기존 구성의 학습 계보는 원 패키지의 다음 문서에 연결된다.

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

이 보관본의 `src/`는 추론 코드 중심이며 완전한 학습 실행 환경·자료 묶음은 아니다. 재현 메타데이터는 실제 학습 파일 제출을 대신하지 않는다. 원 학습 오디오, 생성 오디오, 원 부모, checkpoint, STOP와 완료 기록은 원 작업공간에서 보존한다. 저장소에서 제외했다는 것은 로컬 원본 삭제를 뜻하지 않는다.

## 점수와 검증의 구분

서버 점수는 [모델 카드](MODEL_CARD.md)의 사용자 보고값으로 기록한다. 과거 CPU smoke, 정적 해시·구조 확인, 공개 proxy 평가, 서버 점수는 증거의 범위가 다르다. 소스 보관과 한국어 주석 추가는 새로운 모델 성능 검증이 아니며, 목표 ADS 0.85 달성이나 비공개 평가에 대한 일반화를 추가로 주장하지 않는다.
