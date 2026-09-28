# C693 모델 카드

C693은 DACON 236749 딥보이스 탐지 연구의 대표 보관 모델이다. 음성·음악 탐지기와 고정 결합식을 함께 사용하며, 마지막 개선은 DF-Arena의 작은 학습 가능 부분을 **파일 전체의 가짜 여부 판단**에 연결하는 것이었다. 이 저장소는 소스와 연구 설명을 보관한다. 가중치와 실제 학습 오디오는 포함하지 않으므로 저장소만 내려받아 즉시 추론할 수 없다.

## 결과와 보관 기준

| 항목 | C693 | C704 |
|---|---:|---:|
| ADS | 0.8362380952 | 0.8362380952 |
| 최종 평가식의 종합 점수 | 0.8515229365 | 0.8515229365 |
| CPS | 0.9890865079 | 0.9890865079 |

위 수치는 사용자가 보고한 서버 결과다. 동률인 두 제출 중 구조가 더 단순한 C693을 대표로 보관하고 C704는 동률 변형으로 남긴다. 목표 ADS 0.85에는 도달하지 못했다. 연구 종료 때 사용자가 전한 30위는 당시의 보고이며 최종 확정 순위를 별도로 검증한 기록은 아니다. 종합 점수 0.8515를 ADS 0.85 달성으로 해석하면 안 된다.

대회 점수는 `Score = 0.9 × ADS + 0.1 × CPS`다. ADS는 `1 − (0.5 × File EER + 0.2 × Voice EER + 0.3 × Music EER)`, CPS는 Voice/Music Presence AUC를 각각 0.5로 가중한 값이다. 성분 EER은 해당 성분이 존재하는 파일에서 계산한다. 공개 자료의 source authenticity proxy는 이 공식 ADS와 구분한다. [공식 평가 안내](https://dacon.io/competitions/official/236749/overview/evaluation)

## 입력과 출력

오디오 한 파일을 독립적으로 처리해 다음 다섯 확률을 낸다. FAKE가 양성 클래스다. 음성 또는 음악 중 하나라도 AI 생성 성분이면 파일 전체가 FAKE라는 대회 정의를 따른다.

| 출력 | 의미 | C693에서 사용하는 경로 |
|---|---|---|
| `FILE_FAKE_PROB` | 파일 안에 FAKE 성분이 있을 확률 | C688 tail 음성 증거 + 음악 증거의 고정 결합 |
| `VOICE_FAKE_PROB` | 음성 성분이 FAKE일 확률 | 보컬 stem의 원 DF-Arena + Spectra |
| `MUSIC_FAKE_PROB` | 음악 성분이 FAKE일 확률 | dual-Deezer/Fourier/Dasheng/EAT 결합 |
| `VOICE_PRESENT_PROB` | 음성 성분 존재확률 | 원음 PANNs Cnn14 |
| `MUSIC_PRESENT_PROB` | 음악 성분 존재확률 | 원음 PANNs Cnn14 |

원음은 mono 16 kHz로 변환한다. HTDemucs가 별도로 보컬과 반주를 분리하며, 보컬은 음성 경로에, 반주는 SONICS 음악 경로에 사용한다. Fourier, Deezer, Dasheng, EAT는 원음을 사용한다. 파일 내부의 창 선택과 시간 집계만 수행하며 다른 평가 파일의 통계·순위·예측값으로 보정하지 않는다.

## 구성과 역할

| 구성 | 역할 |
|---|---|
| PANNs Cnn14 | 창별 음성·음악 존재확률 및 파일 내 최대값 |
| HTDemucs | 보컬/반주 분리 |
| DF-Arena 1B + Spectra-AASIST3 | 최대 6개의 약 4.04초 창에서 음성 진위 판별 |
| C688 tail | 원 DF-Arena의 마지막 Conformer block과 분류기를 별도 학습한 사본. File 내부 raw/stem 음성 증거만 교체 |
| SONICS | 반주 stem의 최대 12개 5초 창을 판별 |
| C180/C205 Deezer | 동일 원음 창의 두 학습 파생 모델 확률을 1:1 평균하고 음악 존재확률로 집계 |
| Fourier logistic | 전체 원음의 7,167차원 artifact fingerprint를 판별 |
| Dasheng + C151 head | 음악 존재확률이 가장 큰 4초 창의 768차원 표현을 판별 |
| EAT + C593 heads | 최대 6개 4초 창에서 4/8/12층 표현을 독립 head 세 개로 판별 |

EAT의 각 층 표현은 CLS token, patch 평균, patch 모표준편차를 연결한 2,304차원이다. head는 `LayerNorm → Linear(2304,64) → GELU → Linear(64,1)`이며 세 head의 logit 평균에 sigmoid를 적용한다. 창 점수는 같은 파일의 음악 존재확률로 가중 평균한다.

C693은 원 DF-Arena forward에서 마지막 Conformer block의 입력 `[B,202,1280]`을 한 번 캡처해 별도 tail에 전달한다. 추가 1B encoder forward는 없다. 외부 Voice는 원 모델 출력을 유지하고, File 내부 음성 증거에만 tail 출력을 사용한다.

## 핵심 결합식

`σ`는 sigmoid, `L(p)`는 `[1e-6,1-1e-6]`로 제한한 확률의 logit이다. DF의 fake margin과 Spectra의 bonafide logit은 방향이 반대이므로 다음처럼 결합한다.

```text
λ = 0.69183097
voice_window_logit = (DF_fake_margin − λ × Spectra_bonafide_logit) / (1+λ)
R(z) = 0.75 × max(z) + 0.25 × mean(z)
voice_probability = σ(R(voice_window_logits))
```

C688 경로는 이 식의 DF margin만 교체한다. 시간 정렬 증거는 같은 파일에서 겹치는 PANNs 창의 존재확률을 이용한다.

최종 외부 Music은 `D=presence-weighted dual-Deezer`, `F=Fourier`, `H=selected Dasheng`, `E=EAT`를 다음처럼 결합한다.

```text
M = σ(0.43503136907024 × L(D)
    + 0.26957711906879683 × L(F)
    + 0.03959312199821463 × L(H)
    + 0.2557983898627485 × L(E))
```

File은 고정 C51 결합 함수를 raw/stem 두 경로에 적용한다. 각 경로에서 음성 사건 확률 `qV`와 음악 사건 확률 `qM`을 `1−(1−qV)(1−qM)`으로 결합하고 두 경로 중 최대를 선택한다. C660에서 C51의 direct Fourier 인수 자리를 최종 Music `M`으로 교체했으며, C693은 여기에 들어가는 raw/stem 음성 증거를 C688 tail로 교체한다. 기존 triad/aligned music 증거와 계수는 유지한다. 정확한 계수와 계산 순서는 [`src/script.py`](src/script.py)의 `combine_c51_file_fake_score`, `combine_c660_file_fake_score`, `run_inference`에 있다.

코드를 읽을 때 주의할 두 가지가 있다. `deezer_specnn_official_weights.v1.npz`라는 파일명과 달리 실제 첫 Deezer 가중치는 C180 학습 파생물이다. 또한 C346 점수와 이전 File 결과는 중간에 계산되지만 마지막 C596/C660 계산으로 덮어써진다. C29도 로드·계산되지만 최종 direct 계수는 0.0이다. 보관본은 이러한 과거 실행 구조를 그대로 유지한다.

## 학습 계보

C688은 원 DF-Arena 마지막 block/fc5에서 시작했으며 실패한 C687 학습 체크포인트를 이어받지 않았다. 43,137,922개 파라미터만 학습하고 encoder prefix와 BatchNorm 통계/dropout 동작은 고정했다.

speech 자료는 ASV/MLAAD의 real/fake 네 그룹에 각각 64 source, 총 256 source다. 각 source의 clean 및 고정 음악 혼합 view를 사용했다. Native music은 8 artist group의 14 recording이며 raw 3개와 stem 3개 창을 사용했다. native에는 File=0만 부여했고 Voice/Music component 라벨은 만들지 않았다.

한 update는 speech 네 그룹에서 각 한 bag과 native 한 bag으로 구성한다. seed236749, AdamW lr1e-5/wd0.01, gradient clip1.0으로 고정 128 update를 수행했다. speech에는 real/fake 가중 BCE와 원 clean margin의 SmoothL1 보존 항을, native에는 여섯 창 margin의 log-mean-exp에 File=0 BCE를 적용했다. 마지막 update를 사용하며 검증에 따른 checkpoint 선택은 하지 않았다.

기존 음악 경로는 자체 Fourier/C151 logistic head, Deezer C180/C205 미세 조정, frozen EAT 위 C593 head 학습을 계승한다. C593은 4,400 actual view에 고정 6 epoch/1,650 update를 수행했다. 세 head의 총 파라미터는 456,579개다. 학습 출처·정확한 파일/해시·실제 오디오 보존 의무는 [재현성 문서](REPRODUCIBILITY.md)에 연결한다.

## 해석의 한계

공개 검증에는 반복 사용된 패널, 연관된 원천 파일, 작은 source group이 포함되어 있다. 일부 source authenticity proxy는 공식 대회의 다섯 라벨을 갖지 않는다. 따라서 작은 공개 패널의 개선량을 합산해 서버 ADS를 예측하거나 모든 출처에 대한 일반화라고 주장하지 않는다.

과거 clean Windows CPU 직렬 audio-to-CSV 검사는 production Linux/L4 단일 프로세스 또는 1,200파일 시간·메모리 검증과 동일하지 않다. 이후의 사용자 보고 서버 점수와 과거 패키징 당시의 미검증 항목은 서로 다른 시점의 기록으로 보존한다. 이번 보관 작업에서는 추론·학습·평가를 재실행하지 않았다.

연구·비상업 제한이 있는 구성과 학습 자료를 포함한 계보다. 제한 없는 상업 이용이나 수상 산출물의 독점 권리 이전이 해결되었다고 보지 않는다. 자세한 범위는 [제3자 고지](THIRD_PARTY_NOTICES.md)와 [라이선스 정책](LICENSE_POLICY.md)을 따른다.
