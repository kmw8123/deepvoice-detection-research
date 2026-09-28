# Deepvoice Detection Research Archive

DACON 236749 딥보이스 탐지 대회의 실험 회고와 최고 성능 모델 **C693**을 보존한 소스 중심 기록입니다. 2026-09-28 연구를 종료했으며, 이 저장소 정리를 위해 학습이나 추론을 다시 수행하지 않았습니다.

| 결과 | 사용자 제공 서버 기록 |
|---|---:|
| 최고 ADS | **0.8362380952** — C693 / C704 동점 |
| 총점 | 0.8515229365 |
| CPS | 0.9890865079 |
| 목표 ADS | 0.85 — 미달 |

사용자가 종료 시점에 알려 준 순위는 30위입니다. 공식 최종 순위를 새로 확인한 기록은 아닙니다. 더 단순한 C693을 대표 구현으로 보존하고 C704는 동점 변형으로 설명합니다.

## 먼저 읽을 문서

- **[전체 시행착오 기록](EXPERIMENTS.md)** — 베이스라인부터 C753까지 가설·성공·실패·코드 및 검증 오류·방향 전환을 한 문서에 정리했습니다. 마지막 부록에 656개 C-번호 / 704개 디렉터리의 근거 경로가 있습니다. 이는 656회의 학습을 뜻하지 않습니다.
- **[최고 모델 설명](MODEL_CARD.md)** — File / Voice / Music / Presence의 서로 다른 계산 경로, C688 tail 학습, C660의 음악 증거 전달을 설명합니다.
- **[한국어 주석을 단 주 실행 코드](annotated/script.py)** · **[공유 DF tail 코드](annotated/c693_tail.py)** — 설명용 사본입니다. 실행문 AST가 원본과 같은지 검사합니다.
- **[재현 범위와 보관 방법](REPRODUCIBILITY.md)** — 원본 ZIP, 필요한 자산, 현재 저장소만으로 실행할 수 없는 이유를 명시합니다.
- **[외부 구성요소·고지](THIRD_PARTY_NOTICES.md)** · **[라이선스 정책](LICENSE_POLICY.md)** — 전체 프로젝트에 일괄 MIT 허가를 부여하지 않습니다.

## 포함 / 제외

`src/`에는 제출본에서 그대로 복사한 통합 코드 10개와 서버 전용 requirements가 있습니다. `annotated/`는 주석만 추가한 주 코드 2개, `notices/`는 원문 고지, `provenance/`는 원본·사본의 해시와 정적 검증 결과입니다. `experiment_inventory.json`은 원 작업공간 상대 경로의 추적용 색인입니다.

**가중치, 음원, 학습 데이터, 파일별 평가 예측, feature cache, wheel, 7.29GB 제출 ZIP은 포함하지 않습니다.** 상류 모델 구현 전체도 포함하지 않습니다. 따라서 이 저장소는 즉시 실행 가능한 배포 패키지가 아닙니다. 주석본을 원 제출 ZIP과 byte-identical하다고 보아서는 안 됩니다.

## 모델의 핵심

C693은 하나의 새 신경망이 아니라 음성·음악 전문가와 고정 시간/사건 결합의 파이프라인입니다. 원 DF-Arena forward의 중간 표현을 C688 tail과 공유하고, 학습 tail은 File 내부 음성 경로에만 적용합니다. 외부 Voice는 원 DF+Spectra를 유지합니다. 외부 Music은 D239/Fourier/Dasheng/EAT 결합이며, C660 방식으로 그 증거를 File의 직접 음악 입력에도 전달합니다. 최종 File은 원음·분리음의 두 사건 OR 중 최댓값입니다.

공개 검증에서 좋아진 단독 모델을 추가하는 것보다 **이미 계산한 증거가 최종 File까지 제대로 전달되는지**를 고친 C660·C693이 마지막 큰 개선을 만들었습니다. 이후 시도들의 이득과 손실, 목표 미달도 회고에 함께 남겼습니다.

## 가벼운 보관본 검증

```bash
python tools/verify_archive.py
```

Python 표준 라이브러리만 사용합니다. 파일 해시, 원본/주석본 AST 동일성, 금지 대용량 자산, 문서 상대 링크를 확인하며 모델을 import하거나 학습·추론하지 않습니다. 이 검사는 성능 또는 GPU 환경 재현 검증이 아닙니다.

## 비공개 보관 범위

사용자가 2026-09-28 선택한 GitHub 보관 범위는 **소유자용 비공개 저장소** [kmw8123/deepvoice-detection-research](https://github.com/kmw8123/deepvoice-detection-research)입니다. 이는 공개 배포나 타인 초대에 대한 승인이 아닙니다. 대회 기간 중 코드 공유 제한과 제3자 자산 조건 때문에 공개 전환을 자동으로 허용하지 않습니다. [공식 대회 약관](https://dacon.io/competitions/official/236749/overview/agreement)과 [일정](https://dacon.io/competitions/official/236749/overview/schedule)을 확인한 뒤 별도로 판단해야 합니다. 기존 자동 연구 예약은 중지한 상태로 유지합니다.
