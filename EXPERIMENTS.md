# Deepvoice 탐지 연구: 전체 시행착오와 최종 기록

작성일: 2026-09-28 · 대상: DACON 236749 딥보이스 탐지 경진대회 · 상태: 연구 종료, 보관용 회고

## 1. 결과와 이 문서의 읽는 법

최고 사용자 보고 서버 ADS는 **0.8362380952**로, **C693과 C704가 동점**이었다. C704는 Deezer 경로를 한 번 더 바꾼 변형이므로, 이 보관본의 대표 구현은 더 단순한 **C693**이다. 총점 0.8515229365와 ADS 0.8362380952는 다른 수치다. **목표 ADS 0.85에는 도달하지 못했다.** 사용자는 연구를 종료하면서 30위로 마무리한다고 알려 주었으며, 이는 종료 시점의 사용자 보고이지 공식 최종 순위 인증이 아니다.

이 문서는 초기 베이스라인부터 C753까지 보존 기록을 연결한 하나의 회고다. 새로운 실험을 수행하지 않았다. 모델을 바꾼 이유, 공개 자료에서 실제로 관측한 효과, 서버 결과, 반례와 코드·평가 오류, 다음 접근으로 옮긴 이유를 함께 기록했다.

| 읽을 부분 | 내용 |
|---|---|
| 2장 | V1–C349: 초기 모델·포렌식 특징·File 결합·실제 전문가 학습 |
| 3장 | C350–C660: 공동 File, 시간 학습, EAT, 검증 재설계와 증거 전달 경로 |
| 4장 | C660–C753: 최고 C693, 후속 회귀, 보존 학습과 마지막 event 학습 |
| 5장 | 전체 시행착오에서 남긴 결론 |
| 부록 A | 보존된 C-번호별 원 작업공간 경로와 대표 근거 색인 |

최고 모델의 정확한 구조·가중치·출력 역할은 [MODEL_CARD.md](MODEL_CARD.md), 주석 코드는 [annotated/script.py](annotated/script.py), 실행 원본 소스 사본은 [src/script.py](src/script.py)에 있다. 이 저장소에는 거대한 제출 ZIP이나 모델 가중치·오디오가 없다. [재현 범위](REPRODUCIBILITY.md)와 [권리 고지](THIRD_PARTY_NOTICES.md)를 함께 읽어야 한다.

### 측정과 기록의 구분

- **서버 점수:** 사용자가 제공한 제출 화면과 그 화면을 옮긴 보존 보고서의 집계값이다. 이 정리에서 비공개 평가 데이터, 개별 예측·정답, 최신 리더보드를 열어 확인하지 않았다.
- **공개 평가:** 외부 공개 자료로 만든 로컬 개발/확인 패널이다. 같은 부모의 crop·codec·혼합 반복을 독립 음원으로 세지 않는다.
- **source-proxy:** 출처의 REAL/FAKE를 대리 라벨로 사용한 지표다. 공식 File/Voice/Music/Presence 정답과 동의어가 아니다.
- **OOF:** 명시한 학습 층과 분할에만 적용된다. 결합기만 제외해서 학습한 OOF가 상류 음향 모델까지 미관측이었다는 뜻은 아니다.
- **진단 경계:** EER를 설명하는 ROC 경계이지 제출 ZIP에 고정 임계값을 넣었다는 뜻이 아니다.
- **완료/실패/준비:** 학습 완료, 추론 완료, 성능 개선, 실행 전 오류, 권리 HOLD, 미실행 계획을 따로 기록한다.

파일시스템에는 최고 번호 C753까지 **656개의 C-식별자, 704개 관련 디렉터리**가 남아 있다. 이 숫자는 완료한 학습 횟수가 아니다. 초기 V 계열, 조사·감사·특징 추출·패키징·중단된 계획도 별도 기록이다. 본문은 의사결정에 영향을 준 주요 흐름을 설명하며, 부록은 작은 시도까지 추적할 수 있도록 보존 경로를 열거한다. 삭제된 원 기록을 복원하거나 모든 번호의 실행 여부를 새로 인증했다는 뜻은 아니다.

### 끝까지 남은 한계

공개 검증을 반복해서 보며 구조를 선택했으므로 선택 편향이 남는다. 서버와 공개 지표의 차이를 숨은 생성기 비율로 역산해 최적화하지 않았고, 특정 조합의 서버 점수 상승을 보편적 일반화로 주장하지 않는다. 일부 코드·전처리 오류는 실제로 찾아 정정했으나 모든 성능 실패가 코드 오류 때문이었다는 증거도 없다.

실제 학습 파일·부모·체크포인트·실패 기록·최선 ZIP은 원 작업공간에 남겼다. 이 문서나 SHA 색인은 실제 학습 데이터 보존 의무를 대신하지 않는다. 권리 이전 및 가중치 재배포의 미해결 사항은 그대로 남는다.


## 2. 초기 연구 — 공식 베이스라인에서 C349까지

이 절은 2026-08-27~2026-09-10의 보존 기록을 바탕으로, 모델을 바꾼 이유와 실제 결과, 실패 뒤 방향 전환을 재구성한 회고다. C번호는 학습 횟수가 아니다. 조사, 데이터 취득, 구현 감사, 수식 재생, 실제 학습, 패키징이 같은 번호 체계에 섞여 있으며, 번호가 크다는 이유로 그만큼 독립 실험을 했다고 계산하지 않는다. 아래 `공개`는 외부 공개 자료로 구성한 로컬 평가이고, `서버`는 사용자가 전달한 DACON 제출 결과다. 공개 ADS proxy를 서버 ADS와 같은 측정으로 취급하지 않는다.

당시 공개 development200은 원천40개/10쌍을 조합한 4초120개와 8초80개, 모노 WAV 패널이었다. Music160 역시 독립160곡이 아니다. 같은 자료를 후보 설계와 선택에 반복 사용했으므로 source-group OOF라도 새 독립 확인셋은 아니다. 당시 `lockbox`라는 이름도 DACON 비공개 평가가 아니라 공개 합성 패널의 내부 분할을 뜻한다. 이후 반복 사용하거나 학습에 편입된 분할은 그 상태에 맞게 해석한다.

근거: `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`의 「5. 서버 데이터 추측보다 먼저 확인된 개발셋의 빈틈」, `docs/RESEARCH_RESUME_STATUS_2026-09-06.md`의 마지막 주석.

### 2.1 검증 가능한 서버 이정표

초기 반올림 화면 값은 원문 정밀도를 유지했다. C241→C349처럼 한 출력만 바뀐 경우와, Music 변경이 File로도 전달된 경우를 구분해야 한다. 여러 출력이 바뀐 ADS만으로 성분별 절대 EER을 복원할 수 없다.

| 단계 | 제출에서 달라진 핵심 | 서버 총점 | 서버 ADS | 결과 근거 |
|---|---|---:|---:|---|
| V1 | DF/SONICS 음악 결합, File probabilistic OR | .69332 | .66046 | `docs/EXPERIMENT_RETROSPECTIVE_AND_CLEANUP_2026-09-01.md`, §3 |
| V2 | DF+Spectra Voice, SONICS alpha5s Music, File MAX | .72092 | .69112 | 위 문서 §3, `docs/SOLUTION_V2.md` §1~4 |
| V3 | selector·pooling·시간정렬·gamma120 동시 변경 | .7104943651 | .6795396825 | 회고 §3~4 |
| temporal-only | File의 동시간 presence×fake | .7182872222 | .6881984127 | 회고 §3~4 |
| selector-only | PANNs 상위창 선택 | .7186586508 | .6886111111 | 회고 §3~4 |
| gamma-only | raw gamma120 음악 | .7062015079 | .6747698413 | 회고 §3~4 |
| pooling-only | Voice logit .75max+.25mean | .7226300794 | .6930238095 | 회고 §3~5 |
| V5 | SONICS:Deezer:Fourier=2:3:3 | .7966872222 | .7753095238 | 회고 §11, 서버14분29초 |
| C2 | File monotone calibrated OR | 약 .80491 | 약 .78445 | `docs/C2_FILE_FUSION_LEADERBOARD_RESULT_2026-09-02.md`, 「서버 결과」 |
| C2+EnvSDD10% | File 확률 고정 혼합 | .8027300794 | .7820238095 | `docs/FAST_LEADERBOARD_PROBES_2026-09-03.md`, 결과표 |
| C2+EnvSDD20% | File 확률 고정 혼합 | .7966872222 | .7753095238 | 위 문서 결과표 |
| 최초 C3 | aligned File | 실행 실패 | — | 위 문서 「C3 aligned File-fusion」 |
| C3 복구본 | 같은 파일 nearest interval fallback | .8090943651 | .7890952381 | `docs/C3_ALIGNED_NEAREST_LEADERBOARD_RESULT_2026-09-04.md`, §1 |
| C8 | C3 내부 Music event를 외부 Music으로 노출 | .8090943651 | .7890952381 | 초기 회고 §14, C3와 표시값 동점 |
| C29 | LPC residual을 classical 음악에 추가 | .8106372222 | .7908095238 | 초기 회고 §15, 서버19분03초 |
| C51 | File 음악 head에 직접 Fourier/C29 입력 | .8185443651 | .7995952381 | `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`, §2 |
| C52 | File을 C3 계열로 복귀 | .8121800794 | .7925238095 | 위 문서 §2 |
| C58 | C52에 raw/stem Fourier routing | .8121800794 | .7925238095 | 위 문서 §2 |
| C71 | 짧은 구간 raw/stem consensus | .8106372222 | .7908095238 | `docs/RESEARCH_RESUME_STATUS_2026-09-07.md`, 「C71 서버 결과」 |
| C159 | 선택4초 Dasheng과 최종 Music 50:50 | .7992586508 | .7781666667 | `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md`, 첫 절 |
| C190 | C51 내부 Deezer를 추가 학습 전문가로 교체 | .8265800794 | .8085238095 | `docs/C190_TO_C212_RESEARCH_2026-09-08.md`, §1 |
| C212 | 두 Deezer 및 작은 내부 Dasheng 역할 | .8281229365 | .8102380952 | `docs/RESEARCH_RESUME_STATUS_2026-09-09.md`, 「확인된 서버 결과」 |
| C241 | presence 가중 Deezer+File 원음 Voice 보완 | .8292157937 | .811452381 | `docs/RESEARCH_RESUME_C241_SERVER_2026-09-09.md`, 첫 단락 |
| C349 | 외부 Music만 C346 고정 비중 | .8330729365 | .8157380952 | `docs/C349_C346_MUSIC_ONLY_REPORT_2026-09-09.md`, 서버 결과 추가 |

V3 이후 위 제출의 CPS 기록은 .9890865079다. C2는 약 .98908 표시값만 남는다. C46은 초기 회고에 패키징까지 기술돼 있고 후속 서버 변화 감사에서 C29 대비 ADS +.003786, C46→C51 +.005000이 확인된다. 여기서는 원 화면의 전체 점수 자릿수를 새로 만들어 표에 채우지 않았다. 서버 자료의 일반적인 한계는 사용자 제공 값이라는 점과 개별 예측·정답·서버 업로드 SHA가 별도로 없다는 점이다.

근거: `docs/SERVER_SCORE_CHANGES_AND_NEXT_MODEL_EVIDENCE_2026-09-10.md`의 「1. 어느 출력이 점수를 움직였는가」.

### 2.2 V1~V3: 모델 역할과 시간 집계를 먼저 배웠다

공식 베이스라인은 PANNs로 Voice/Music 존재, HTDemucs로 성분 분리, DF-Arena1B로 진위를 판정했다. V1은 음악 전문가 SONICS beta5s를 넣었지만, 반주 DF와 SONICS를 근거 없이 동일 logit 비중으로 섞고 원음 SONICS까지 File OR에 넣었다. 서버 실행은 됐으나 ADS .66046이었다. 당시 CPS .98908의 추가 총점 여지는 약 .0011뿐이므로 authenticity가 우선이라는 판단이 나왔다.

V2는 입력과 전문가 역할을 분리했다. 반주의 음성용 DF 및 raw Music 보조 경로를 제거하고, SONICS alpha5s를 반주에 사용했다. Voice에는 DF와 Spectra-AASIST3를 결합했다. 공개17도메인 2,001,847발화 점수에서 DF/Spectra/고정 결합의 macro EER은 3.5359%/1.4461%/.9266%, leave-one-domain-out 결합은 .9871%였다. 계수 .6918309709189366은 이 공개 자료로 정했다. 다만 이는 원음 첫 창의 공개 점수 검증으로, Demucs·전화·노래·혼합 파형 실험을 대신하지 않았다. File은 공식 MAX로 복귀했고 서버 ADS .69112가 됐다.

V3는 짧은 발화 누락, max 오탐, 서로 다른 시점의 presence/fake peak 곱, 장문맥 음악 모델이라는 네 가설을 동시에 구현했다. PANNs 상위4창+양끝2창, Voice .75max+.25mean, 동시간 File 결합, raw SONICS gamma120이었다. 서버 ADS .6795396825로 후퇴했으므로 한 변경씩 분리했다. 네 ablation 중 pooling만 .6930238095로 올라 이후 기반이 됐다. gamma120은 4~60초를120초 입력으로 채우며 원음 가짜음성을 Music으로 읽을 가능성이 있었지만, 이 설명을 서버에서 확정된 원인으로 단정할 수는 없다.

후속 pooling 감사의 .63 최소점과 .75의 EER 차이는 .002419 percentage point였고, 재그룹화 최적값은 .61~.77로 움직였다. 더 중요한 9/10 정정은 이 실험이 독립 발화 점수를 묶은 synthetic pseudo-file이라는 점이다. 실제 인접창·Demucs·전화·부분위조를 추론한 결과가 아니며, 예전 scenario 동등가중 설명도 실제40/30/30과 달랐다. 서버에서 유효했던 .75 구현은 보존하되 보편 최적계수라는 주장은 철회해야 한다.

근거: `docs/SOLUTION_V1.md` §2~5, `docs/SOLUTION_V2.md` §2~4, 초기 회고 §4~5, `docs/VOICE_POOLING_EVIDENCE_SCOPE_CORRECTION_2026-09-10.md` 전문.

### 2.3 V4 주변 탐색과 V5: 음악 전문가 다양성이 첫 큰 전환이었다

V4라는 이름의 ArtifactNet 준비 폴더는 존재하지만 실제 승격·제출된 V4라고 쓰면 틀린다. raw ArtifactNet은 pure-music macro EER .10/AUC .9625였으나 음성 혼합 wideband EER .25~.325, 전화 근사 .325~.375로 약해졌다. Demucs 반주에 적용하면 pure-music EER .05에도 speech-only accompaniment20개 전부에서 .5 이상을 출력했다. 반주 분리가 새 artifact와 음성 누출을 만들 수 있음을 드러낸 사례다. raw Music 교체는 기존 SONICS보다 macro EER .510417→.368056으로 개선됐지만 절대·전화 조건 gate를 넘지 못했다. 고정/조건부 결합은 EER 추가 개선0, temporal median은 전체 숫자 .15에도 crossfit EER 개선0이었다.

SONICS alpha/beta/gamma 결합은 macro EER .443743→.414730이지만 AUC .601166→.582602, micro EER .439803→.450329로 악화했다. 공개 외부 음성 모델도 조사했으나 라이선스·실행경로·용량 또는 보완성 증거가 부족했다. SONAR는 훗날 실제300개 AUC .570044/EER .466667까지 측정됐지만 fairseq→Transformers 변환의 수치 동등성이 미확정이다. 따라서 공식 모델 전체의 성능 실패라고 확장해서는 안 된다.

V5의 Fourier는 초기에 기각한 공개 fakeprint checkpoint와 별개로 직접 학습했다. 공개 fake300+권리 필터 real320의620원천에서 길이·codec 변형6,696행, 7,167차원 특징을 만들고 원천 분리6fold에서 logistic C=.01을 선택했다. 단독 OOF provider-condition macro EER/AUC .163649/.883275였다. Deezer SpecNN은 공식 오래된 checkpoint를 pickle-free NPZ로 내보내 오프라인 추론 경로를 재현했다. SONICS 반주, Deezer 원음 스펙트럼, Fourier 원음 잔차의 2:3:3 logit 결합을 공개620원천×4조건/2,480행과184개 사전 후보의 grouped/nested 검증으로 정했다.

기존 SONICS→triad의 공개 macro EER .264171→.151980, nested stitched .163324였다. MUSAN source-shift EER .254444→.165000, 실제 Demucs clean120 fold-macro .25→.116667도 개선됐다. 서버 ADS는 pooling .6930238095→V5 .7753095238, +.0822857143으로 초기 최대 도약이었다. 모델별 score 상관 .3325~.5282와 서로 다른 입력 표현은 보완성의 공개 근거이지만, 개선량을 Music/File에 나눠 인과적으로 귀속할 수는 없다.

이 과정에는 학습 전 provenance 오류를 막은 시행착오도 있었다. ArtifactBench shard044를 실제 REAL이라고 여겼으나 Udio AI17행이어서 격리했다. FMA materializer의 shard/generator/REJECT 처리, 실제 ZIP geometry를 수정한 뒤에야 자료를 생성했다. 이는 성능 실패와 구분할 데이터·구현 오류다. 실제 최종 학습 파일과 부모·변형은 보존했으며 manifest만으로 파일 제출을 대체하지 않는다.

근거: 초기 회고 §6~8, §11, `research/c369_early_candidate_failure_audit/C369_EARLY_CANDIDATE_FAILURE_AUDIT_2026-09-10.md` §2.

### 2.4 C1~C13과 v7~v25: File 결합 개선, 그리고 조기 시험으로의 전환

V5 이후 C0=공식 MAX, C1=무학습 soft-OR, C2=비음수 calibrated-OR를 공개200에서 비교했다. File EER은 .1851648352/.1703296703/.1554945055였다. C1은 AUC·순차 조건·bootstrap 실패, C2는 bootstrap .7438964844와 최악 cell 악화 .05 때문에 엄격 승격 기준에 실패했다. 그러나 C2 제한 서버 시험은 ADS 약 .78445로 개선됐다. 작은 개발셋의 gate가 서버 일반화를 완벽히 판정하지 못한다는 사례이지, gate를 사후 PASS로 바꿀 이유는 아니다.

C3는 global과 같은 파일 시간정렬 evidence를 함께 썼다. 최초 evaluator는 실제 feature schema3에 schema2를 요구해 C3를 실행하지 못했다. 동결 receipt는 `c3_available=false`로 남기고 별도 사후 진단을 실시했다. File EER .1296703297로 C2보다 좋아졌지만 sequential/temporal macro .15→.20, bootstrap .89990234375로 연구 gate는 실패했다. 최초 서버에서는 `C3 found no interval overlap`로 종료됐다. 겹치는 창이 없으면 같은 파일 안에서 interval gap→center gap→원 index 순으로 최근접 창을 고르는 결정적 fallback을 추가했고, 계수는 유지했다. 복구본 서버 ADS .7890952381은 실행 오류 복구와 성능 확인을 함께 이뤘다.

EnvSDD는 새로운 환경음 진위 증거를 기대했으나 CPython·토치·loader·파일 접근·ABI 관련 준비가 길어졌다. AudioMosaic도 그 후속 경로에 종속됐다. 여러 버전의 정적 준비나 import 성공을 모델 학습 횟수로 세지 않는다. C2+EnvSDD .10/.20은 공개 최적화가 아닌 사전 고정 탐색 비중이었고 서버 ADS .7820238095/.7753095238로 모두 하락했다. 추가 alpha 탐색을 종료했고 사용자 지시에 따라 EnvSDD/AudioMosaic를 중단했다. 9/3부터는 실제1음원→소배치 성능을 먼저 보는 방향을 명시했다.

그 뒤 작은 후보들은 다음처럼 구분된다.

| 후보/가설 | 공개에서 실제 본 결과 | 판단의 범위 |
|---|---|---|
| C4 raw Voice 특징 추가 | File EER .1296703→.1445055 | 같은 raw 정보를 새 File 보정 입력으로 넣는 방식 실패 |
| C5 음악 전문가를 독립 입력으로 분해 | Music .30→.2875, File .1296703→.1445055 | 성분 개선이 File 이득으로 남지 않음 |
| C6 WavLM-OC 보완 | File/Voice EER 동점, AUC만 소폭 상승 | 오류 보완 약함, 계수 재탐색 안 함 |
| C7/C8 event를 외부 성분 출력으로 노출 | C7 Voice .05→.075; C8 Music .30→.2625 | C8는 C7 후 사후 격리, 엄격 gate 실패; 서버 C3 동점 |
| C9 조건부 Music | Music EER .30, C8 .2625보다 약함 | 기존200에서 조건 재조정 중단 |
| C10 C8/C5/V5 동일가중 logit 평균 | EER .275, AUC .78015625 | AUC 개선만 남음; 3자 평균이 정확한 수식 |
| C12 event max | File .1296703→.1445055 | 기존 점수 재조합의 이득 없음 |
| real-only PPCA32 | 실제REAL226 fit, small24 EER .5/AUC .486111 | 실행 성공 후 신호 실패 |
| C13 CQT-Cepstrum CNN | small40 EER .35, C8 .20 | 초기 선형 Fourier와 다른 모델임을 확인 후 실제 기각 |
| AFSS/QAMO | RADAR24 EER 각각 .5/.5 | 실제 strict-load·forward 성공, 작은 패널 성능 및 권리 한계 |
| AntiDeepfake-Small | RADAR24 .25, ITW20 File .40(C2 .30) | 이 ITW 수치를 Voice 진위 성능으로 일반화하지 않음 |
| EfficientAT presence | 2,212행 CPS .9888334505→.9882881955 | 초기 ABI 준비 실패 뒤 실제 완주, PANNs 유지 |

Nes2Net-X는 후속 감사에서 중요한 target 해석 오류가 확인됐다. ITW20의 Voice는 전부 REAL이고 파일 FAKE는 음악에서 왔다. File EER .50은 실제 결과지만 Voice EER은 한 클래스여서 정의할 수 없다. “Voice 일반화 실패”로 확대했던 해석을 정정한다. RADAR24 EER .25와 권리 문제는 별개의 약점으로 남는다. raw 음성을 다시 쓰는 아이디어 전체가 기각된 것도 아니다. 훗날 C232는 raw/stem의 기존 event 확률 max라는 다른 결합으로 일부 이득을 얻었다.

근거: `research/v6_file_fusion_itw/FULL_400_V4_2_DEVELOPMENT_RESULT_AUDIT_2026-09-02.md` §6~8; `docs/FAST_LEADERBOARD_PROBES_2026-09-03.md`; `docs/C3_FOLLOWUP_AND_C8_NEXT_SUBMISSION_2026-09-04.md`; `research/v22_c3_residual_scout/C10_MUSIC_FIXED_LOGIT_CONSENSUS_DECISION_2026-09-04.md`; `research/v17_afss_fast_probe_v0_1/AFSS_FAST_PROBE_REJECTION_2026-09-03.md`; `research/v18_qamo_fast_probe_v0_1/QAMO_BATCH24_STOP_2026-09-03.md`; `research/v19_antideepfake_small_fast_probe_v0_1/ANTIDEEPFAKE_SMALL_FAST_GATE_DECISION_2026-09-04.md`; C369 감사 §1~3.

### 2.5 C26~C52: 작은 포렌식 특징의 성공과 결합 경로의 중요성

위상·coherence(C27)는 Fourier 단독 EER .326389→.298611의 신호가 있었으나 triad 전면 교체는 .215278→.229167로 나빠졌다. 초기 allfit score leakage·cross-fold pair 통계 문제를 수정했고, sentinel 중단 뒤에도 추가 실제 탐색평가가 존재한다. C28 multiscale292는 overlap .55→.35 개선, clean .50 동점이었지만 clean AUC .545→.4975 때문에 당시 기준에서 종료됐다. 두 후보를 미실행 또는 무신호라고 정리하면 부분 성과를 잃는다.

C29는 16/8/4kHz LPC 예측 잔차441차원의 logistic head다. 중앙4초를 읽으며 전체 파일의 모든 창을 처리하는 모델은 아니다. 첫 fold clean/overlap EER .40/.35, 독립 fold1 .2450/.2236이었다. Fourier와 고정50:50 logit 결합은 fold1 clean .1168→.0955, overlap .1382→.0955였으나 fold0에서는 C29 단독보다 나빴다. 전체620원천×clean/overlap=1,240실제 입력으로 최종 head를 학습했고 서버 ADS .7908095238로 C3 대비 +.0017142857이었다.

C46은 서버 값으로 비중을 맞추지 않고 공개 source-held folds1~5의10cell에서 alpha {0,.25,.5,.75,1}을 비교했다. alpha .25의 macro EER .1476381254가 .50의 .1607864302보다 낮아 Fourier .75/LPC .25로 고정했다. 이것은 classical 슬롯의 OOF 근거이며 전체 Music160 또는 서버 EER이 아니다. 10cell 중6개 개선·2동점·2악화가 공존했다.

C31~C34는 새 encoder 없이 C3의 시간 모양·순위·EER 경계 잔차를 학습하는 연속 가설이었다. C31은 temporal-partial File EER .283333→.216667이지만 전체 .1296703297→.1406593407로 악화했다. C32 shape-only 순위 잔차, C33 boundary-weighted 순위 잔차, C34 EER-boundary 잔차는 전체 EER .1296703297 동점이었다. AUC는 조금 올라가도 C33/C34의 temporal-partial EER은 .30으로 나빠졌다. 네 후보 모두 `STOP_NO_RECOMMENDED_SUBMISSION_ZIP`이며 시간 구조를 학습했다는 사실과 전체 EER 개선을 구분한다. 근거는 각 `research/v31_temporal_c3_residual_probe/`, `research/v32_temporal_c3_shape_rank/`, `research/v33_temporal_c3_boundary_rank/`, `research/v34_temporal_c3_eer_boundary/`의 `*_PUBLIC_DEVELOPMENT_RESULT.v1.json`에 있는 `c3_outer_oof`, `candidate_outer_oof`, `status`다.

동시에 실행한 대안들은 다음과 같다. C30 SONICS384+Deezer128 frozen 표현은 Windows selector 오류를 우회한 뒤 clean/overlap EER .416667, overlap AUC .569444로 실제 종료했다. C35 LPC 다중 crop은 Music .35→.3625로 악화했다. C36 LPC 직접 File과 C37 Fourier 직접 File은 각200/200 공개 분할에서 모두 EER .3703296703이었다. C38 MERT-v0의 mean+std1536 head는 all EER .375, C39 소형 logmel CNN은 학습 정확도 거의1에도 held EER .55로 과적합했다. C40 Sara wav2vec2는 대부분 spoof1에 포화돼24행 EER .416667이었다. C41 CLAP은 overlap EER .35로 gate 실패, C42 공개 GTZAN/Suno CNN은 AUC .333125/EER .625로 실패했고 임의 부호 반전도 하지 않았다. C43 SONAR는 이전 실패 checkpoint와 동일하여 재실행하지 않았다. C44 Eliya Base는 RADAR24 AUC .958333에도 EER .166667로 기존 OC .083333보다 약했다. C45 Echoes는 REAL 음원0, 불완전 reference 매핑·권리 자료 때문에 학습 전 중단했다. C47 재검색은 동일 실패/HOLD 또는 실행 가능한 근거 부족으로 다운로드·추론 없이 끝났다.

C48은 바뀐 C46 음악 점수에 옛 C3 File 계수를 유지한 불일치를 점검해 File EER .1703296703→.1554945055를 얻었지만 bootstrap .383301로 보류했다. C49 직접6입력 File은 의도한 C46 대신 C3를 기준으로 비교한 오류가 있었다. 올바른 C46로 정정해도 후보 EER .189011로 악화였으므로 성공 모델을 숨긴 오류는 아니었다. C50의8입력 계획은 변하는 보고서 SHA/크기를 실행 필수조건에 묶어 막혔고 C51 뒤 취소돼 fit·EER0회다. 성능 실패가 아닌 미평가로 남긴다.

C51은 File 음악-event head에 C46 global Music, presence, aligned Music, raw Fourier, raw C29의 다섯 logit을 전달했다. 공개 File EER .1703296703→.1445054945, bootstrap .6154785156였다. final 직접 C29 slope는0이지만 C29는 global/aligned 안에 남았다. 주된 변화는 raw Fourier가 다른 음악 전문가와 먼저 섞여 약해지지 않도록 File에 직접 전달된 점이다. 서버 ADS .7995952381로 이 계보의 새 기준점이 됐다. 반대로 C52는 File을3입력 C3 방식으로 돌리고 File용 classical도 raw Fourier로 복귀시켜 서버 ADS .7925238095로 나빠졌다. “C51 보존 개선”이라는 설명은 부정확하며, 여러 기존 정보가 바뀐 후보였다.

근거: 초기 회고 §14~16; `research/c369_early_candidate_failure_audit/C369_EARLY_CANDIDATE_FAILURE_AUDIT_2026-09-10.md` §4~5; `research/c370_c29_c51_retrospective/C370_PROMISING_CANDIDATE_CODE_AUDIT_2026-09-10.md`; `submission_c51_uncompressed_file_music_src/C51_SUBMISSION_HANDOFF_2026-09-05.md`; `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md` §2~3.

### 2.6 C53~C159: 작은 개발셋, 새 점수의 희석, 검증·제출 불일치

이 구간은 temporal Fourier, component calibration, local raw/stem consensus, presence/layout routing, raw Spectra/Voice 보완, 음악 해상도, stem 누출 완화, LBP texture 등으로 갈라졌다. 각 번호를 새로운 대형 모델 학습으로 세면 안 된다. C61~C88의 다수는 기존 점수·구간·특징의 배치와 결합을 바꾸는 가설이다. C71/C75는 공개 File 개선이 남았지만 bootstrap이 약했다. C71은 정확 Fourier vectorization으로60초30호출 약9배 속도를 얻은 뒤 재검토·패키징했고 공개 File EER .144505→.114835였으나 서버 ADS .7908095238로 C51보다 낮았다.

C58은 C52와 서버 동점이었지만 공개 캐시 재생에서 File200개 모두 바뀌고 최대 차이 .27569,539순위쌍 변화가 있었다. 연결이 죽은 버그라는 증거는 없었다. 실제 문제는 연구에서는 routed 입력에 맞춰 head를 재학습했으나 ZIP은 옛 C3 계수를 썼다는 계약 불일치다. 후속 C108에서 절차를 맞춰도 새 원천에서 oldC58와 music-event 순위가 같아 수정 재제출 근거를 얻지 못했다. 연구·배포 불일치를 인정하되 그것이 서버 실패의 유일한 원인이라고 하지 않는다.

LBP472(C95)는6provider×2view 평균 EER .228753→.186764였다. codec·길이·overlap7,316뷰 증강(C100)은6provider×3view .222400→.173016으로 나아졌다. 그러나 C101에서 실제200에 적용하면 classical EER .2875→.2625여도 최종 File/Music EER은 같았다. C102가 직접 여섯 번째 File 입력으로 쓰면200개 확률이 바뀌고56오류쌍을 고치는 대신52쌍을 새로 깨뜨려 EER의 FP10/FN19가 유지됐다. LBP가 여러 결합을 지나는 logit 민감도 상한 약 .0386, global/aligned music 상관 .9563은 정보 희석과 중복의 구조적 근거였다. 그렇지만 전체 music-present160의 LBP AUC .493750도 확인돼 결합만 탓할 수 없었다.

C90은 같은 목표의 학습 패널을400행으로 늘려 File EER .1445055→.1554945로 악화했다. C114/C118/C120 부분·국소 학습, C125 LPC 원천 추가, C126 직접 LBP File, C130 Deezer128 head 전이도 최종 이득을 확보하지 못했다. 특히 C131 기존 Music160에서 .325→.475인데 C132 별도64에서는 .315341→.223011이었다. 새 패널의 좋은 결과로 기존 혼합 조건 붕괴를 덮지 않았다. C134 독립 File, C135 real-only, C137 비선형 음악, C138 새 REAL source 학습도 EER 기준에서 전체 개선이 없었다.

C159는 frozen Dasheng+자체 C151 head를 PANNs가 고른4초에 적용해 최종 Music과50:50 평균했다. 공개 Music160 .325→.2875, 별도 음악 source-proxy .315341→.184659였지만 독립160/64원천이 아니었고 혼합·일부 원천 악화와 bootstrap95%구간0 포함이 남았다. 서버 ADS .7781666667로 C51 대비 -.0214285714였다. 네 출력 보존 전제에서는 Music EER 약 .0714285713 악화다. 실행 성공과 일반화 성공을 혼동한 제출 권고 실패로 기록했으며 단순 alpha 수정으로 이어가지 않았다.

근거: `docs/RESEARCH_RESUME_STATUS_2026-09-06.md`, `docs/RESEARCH_RESUME_STATUS_2026-09-07.md`, `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md` §2~5, `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md` 첫 두 절.

### 2.7 C162~C241: 실제 자료와 전문가를 학습하고, 쓰이는 위치를 바꿨다

C159 이후 frozen 표현의 head 반복만으로는 부족하다고 보고 Deezer 마지막 Conv+dense/output을 학습했다. C166 기존 자료, C169 MusicGen60원천 추가, C174 Fourier+LPC source expansion, C178 고정 평균은 일부 held 개선에도 C51 공개 전체를 이기지 못했다. C171 segment mean→max는 Music160 .425→.3625와 순차 .30→.15의 이득 대신 overlap .50→.55와 새 원천 오탐을 만들었다. 시간상 짧은 fake 희석과 REAL 최대값 오탐이 함께 존재했다.

같은 음악에서 음성을 바꿨을 때 Music 점수가 움직이는 C175 음량통제16개 실험을 근거로, REAL/FAKE 음악 양쪽에 합성 음성을 대칭 추가했다. Kokoro stock8을 생성하고 음악764×2채널=1,528실제 파일을 만들었다. C180은 train3,690/held766으로 실제 tail 학습했다. oldheld500 EER .32393→.28405, 새held266 .39097→.34580이었지만 공개 Music160 .3875로 C51 .325보다 약했다. 음성 교체 signed평균은 줄어도 절댓값 평균은 .09035→.11551로 악화했으므로 불변성 확보라고 주장하지 않았다. raw용 모델에 Demucs 반주만 넣은 C181도 proxy EER .375→.75였다.

전환은 단독 모델의 최종50% 혼합이 아니라 기존 전문가 내부 역할 교체에서 나왔다. C190은 C51 구조의 Deezer를 증강 학습 C180으로 바꾸고 직접 Fourier와 시간 정보는 보존해 서버 ADS .8085238095를 얻었다. C205는 같은3,690자료로9epoch 추가 학습해 held766 .3093→.2259였다. 그러나 단독 교체 C208은 Music .300→.2875에도 File .1445→.1555로 악화했다. C210은 같은 창의 C180/C205 확률을 반반 평균했고 C209는 간접 C29 자리의 작은 Dasheng 역할을 시험했다. 둘을 실제 결합한 C212는 Music .25, File OOF .140659였고 서버 .8102380952였다. 유효 logit 비중은 SONICS25%, dual Deezer37.5%, Fourier28.125%, Dasheng9.375%였으며 직접 File C29는 보존됐다.

C211 더 깊은 convolution 학습, C222 국소 라벨 학습, C223 전화 Fourier, C226/C228 순위손실은 EER 개선을 확보하지 못했다. C229 음량 표준화는 File 악화, C231 촘촘한 Fourier는 File 일부 이득과 Music .25→.275 손실이 충돌했다. C238 신경 codec 복원·토큰요약81차원 head는 held64 .21875→.46875로 약했다. 실행한 학습과 성능 실패를 남기고 추가 대규모 확대는 하지 않았다.

C241에서는 PANNs 음악 존재확률로 Deezer 창 평균을 가중한 C239와, 원음/분리음성의 기존 voice-event 중 큰 값을 File에만 쓰는 C232를 결합했다. 공개 Music160 .25→.2375, 순차 Music .20→.10, File200 .140659→.129670이었다. 별도16 File은 .25 동점이며 bootstrap95%구간은0을 포함했다. 각각의 File 개선폭이 결합에서 더해졌다는 근거는 없었다. 서버 ADS .811452381,26분02초로 소폭 개선됐다.

근거: `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md` 후속 완료 절; `docs/C190_TO_C212_RESEARCH_2026-09-08.md` §3~7; `docs/RESEARCH_RESUME_STATUS_2026-09-09.md`; `docs/C241_RESEARCH_AND_SUBMISSION_2026-09-09.md`.

### 2.8 C242~C349: 추가 학습의 반복 실패 뒤, 외부 Music과 File 결합을 분리했다

C241 이후에는 source-paired JS, provider 균형, 더 깊은 CNN, codec 증강, 원천/시간 crop 확대, MuQ·MERT·PANNs·Spectra 표현, SONICS 적응, real-only density, 비선형 head, 긴 시간 관측 등 여러 축을 실제로 검토했다. 아래는 동일 baseline과 비교 범위가 확인된 대표 결과다. 모두 공개 결과이며 서로 다른 행의 수치를 평균하거나 서버 예상치로 더하지 않는다.

| 시도 | 실제 관측과 종료 이유 |
|---|---|
| C246/C249 paired-JS | held766 EER .225889 동점; 실제280 최종 Music/File도 동점 |
| C248 presence 열 제거 | old File .129670→.114835지만 별도 File16 .25→.291667 악화 |
| C245 codec token histogram | held64 .21875→.53125, 작은 표현 실패 |
| C251 MuQ source expansion | TRAIN3690/held766, EER .276809(C205 .225889); MusicGen 일부 보완만 남음 |
| C255 MuQ 직접 File | held File .264915, old200 전이 .429670; 목표별 head가 필요해도 성능 충분하지 않음 |
| C265/C267/C278 MuQ MLP·규제선택·RBF | MLP .302823, RBF .289816; TRAIN-only 규제선택도 C=.01 유지 |
| C269/C272 SONICS tail | raw held .468590→.349938, 최종 File .129670→.144505 악화 |
| C274/C276/C277 | 마지막2conv, 새MusicArena32, 시간crop2524를 각각 시험; held .232392/.232392/.245399로 기준 .225889 열세 |
| C285 scratch residual CNN | held .484295, 학습상 개선과 source 일반화 괴리 |
| C290 REAL-only SpecNF | REAL1734뷰4epoch, held .398160; 정상 density/논문 재현 주장도 제한 |
| C291 MP3/Opus 증강 | TRAIN7380, 원held .225889→.238896; 확장codec held .224540→.231043 |
| C293/C297 SONICS stem/full fine-tune | 소형 stem held EER .5 동점; full fine-tune held64 .46875로 C205 .21875 열세 |
| C294/C295/C299 표현 진단 | PANNs .40625; Spectra 마지막160D .21875 동점이나 원 scalar와 순위 동일; 중간6층 .46875 |
| C301/C330 REAL 원천 확대 | 73곡/65곡 추가 후 held .232392/.235091; 단순 자료 증가 효과 없음 |
| C331/C334/C344 | 같은자료 추가9epoch .232392, BN통계 교정 .267608, matched SAM .229694 vs PLAIN .225889 |
| C329 MERT-v1 | held64 .4375; 기존v0와 다른 checkpoint를 실제 시험했으나 전체 열세 |
| C335/C338 dense Deezer | 단독 .235385→.202564에도 최종 Music 동점; aligned/event는 악화 또는 복원만 |
| C336/C339 연속4초 문맥 | 기존6개의 .78초 창 대신 연속4초; 무적응/소형적응 모두 held64 .25, 기준 .21875보다 약함 |

이 시기의 구현 수정도 기록을 정리할 때 사라지면 안 된다. C269는 원 SONICS의 pad 후 표준편차 정규화를 smoke에서 빠뜨린 것을 fit 전에 발견해 캐시를 새로 생성했다. C274는 학습 실패가 아니라 단일클래스 NaN의 JSON 저장 실패였고 저장 예측으로 보고서를 복구했다. C295는 모든 feature가 다르고 원 logit 재생도 일치했지만 TRAIN 표현의 top2 주성분이97.02%여서 새 head가 실제 새로운 순위를 만들지 못했다. C334의 BN shape·JSON 오류도 보존했으나 정상 계산 뒤 성능 악화라는 결론은 유지했다. 문서의 준비/실행중 문장을 최종 실패 기록보다 우선하면 중복 실험을 하게 된다.

마지막 변화는 전문가를 더 추가하기보다 이미 달라진 S/D/F/H 비중을 공개 자료로 다시 학습한 C342/C346이었다. C342 nested OOF는 Music160 .2375→.2625, File200 .129670→.144505로 실패했다. 다만 heldfold Music4동점/1개선의 신호를 바탕으로 사후 제한 전이 진단 C346을 허용했다. Music160에서 균등5fold, lambda {.01,.1,1}, 평균EER 최소·동점 강정규화로 lambda .1을 정하고 전체160에 한 번 fit했다. S/D/F/H 고정 비중은 약 0/.4752857123/.3127043354/.2120099524였다. 이160은 이제 실제 계수 학습 자료여서 final head의 독립 성능으로 보고하지 않는다.

동결 비중의 전이는 C254128에서 Music-source EER .21875→.1875, novel64 .235384615385→.124102564103, C14916 .375→.25였다. 그러나 C254 short-partial .4375는 동점이고8source block 중2개는 악화했다. novel45초의 EER0은 REAL3/FAKE7의10행뿐이다. C149 실제 File16은 .25 동점이며 음악-event proxy는 .25→.375로 악화했다. C254 실제 길이는4초32개+12초96개로, 예전4/8초 설명을 정정했다. novel/C149 및 C254 사이 공유 부모도 있어 독립208원천이라고 부를 수 없다.

그래서 C349는 외부 `MUSIC_FAKE_PROB`만 새 비중으로 계산하고 File에는 원 C241의 global/aligned 음악값을 유지했다. SONICS 비중이 외부 Music에서 거의0이어도 File의 SONICS 경로는 제거하지 않았다. 이 범위 선택은 공개 결과를 본 뒤의 판단이며 독립 확증은 아니다. 실제 모든 모델→CSV 직렬 CPU 검증과 네 출력 exact 보존을 확인한6.23GB ZIP을 만들었고 서버는25분46초, ADS .8157380952로 C241 대비 약 +.0042857142였다. 이는 File에 외부 Music의 최적 비중을 그대로 이식할 필요가 없다는 실전 사례다. 당시 목표 .83에는 못 미쳤고 이후 연구로 이어졌다.

근거: `docs/RESEARCH_RESUME_C241_SERVER_2026-09-09.md`의 각 완료 절; `docs/C349_C346_MUSIC_ONLY_REPORT_2026-09-09.md`의 「공개 결과 — 개선과 반례를 함께 보존」 및 서버 결과 추가.

### 2.9 이 구간에서 보존해야 할 해석

가장 큰 초기 성과는 V5의 독립 음악 관측, C2/C3의 File 결합, C51의 직접 Fourier, C190/C212의 학습 전문가와 내부 역할, C241의 관측 구간, C349의 출력별 결합 분리였다. 반대로 새 모델 단독 개선은 최종 조합의 개선을 보장하지 않았고, 파일 수 증가는 독립 원천 증가와 달랐다. 새 확률이 실제 CSV에 반영돼도 EER이 같을 수 있었으며, 그 사실을 연결 버그로 단정하지 않았다.

초기 `telephone_g711` 이름은 실제8k 전화대역을 뜻하지 않았다. 원 development200은16kHz PCM μ-law encode/decode만 수행했다. 후속 true8k 패널과 나눠 보고해야 하며 실제 통신망 일반화를 입증하지 않는다. 공개17domain voice 점수도200만개 보존 WAV나 실제 혼합 검증을 뜻하지 않는다. 코드 오류, 권리/재현성 중단, 미평가, 실제 성능 실패, 부분 신호, 제한 제출 성공을 각각 남겨야 시행착오 기록이 재사용 가능해진다.

근거: `docs/DEVELOPMENT_CHANNEL_SEMANTICS_CORRECTION_2026-09-10.md`; `docs/VOICE_POOLING_EVIDENCE_SCOPE_CORRECTION_2026-09-10.md`; `docs/PAST_EXPERIMENT_IMPLEMENTATION_AUDIT_2026-09-10.md`; `docs/SERVER_SCORE_CHANGES_AND_NEXT_MODEL_EVIDENCE_2026-09-10.md`.

## 3. C350–C660 — 모델의 개선을 최종 File 판단까지 전달하기

이 구간의 중심 질문은 “어떤 탐지기를 더 학습할 것인가”에서 “이미 얻은 탐지 신호가 최종 판단의 어느 단계에서 사라지는가”로 바뀌었다. C349를 기준으로 공동 File 판별기, 음성 모델 적응, 음악 원천 확장, 부분 위조 학습, 시간 attention, EAT 표현과 대형 모델을 차례로 시험했다. 실제 학습과 공개 검증까지 완료한 후보 중에도 최종 결합에서는 동률이거나 악화하는 경우가 많았다. 최종적으로 C660은 새 신경망을 추가하지 않고 기존 음악 증거가 File에 전달되는 입력 한 곳을 바꾸어 사용자 보고 서버 ADS를 C596의 0.8174523810에서 0.8274523810으로 올렸다.

여기의 공개 EER은 대체로 음악 또는 음성의 **원천 진위를 대리 정답으로 삼은 개발 지표**다. 보컬과 반주의 성분 정답이 모두 확정된 대회 지표, 공식 ADS, 서버 성능과 동일하지 않다. `OOF`도 어떤 모델을 어떤 원천 단위로 제외했는지에 따라 의미가 다르다. 음향 모델 전체가 미관측인 검증과 고정된 음향 점수 위의 결합기만 원천을 제외해 학습한 검증을 구별했다. 숫자가 큰 패널도 같은 부모의 반복 변형일 수 있으므로 아래에서는 행 수와 실제 원천 수를 함께 적는다.

### 3.1 C413: 좋은 작은 공동 판별기가 기존 구조를 대체할 충분한 증거는 아니었다

C350 이후에는 C349의 외부 Music 개선과 별개로 남아 있던 File 오류를 줄이려 했다. 여러 전역·시간·음성 사건 결합을 거쳐 C412는 10개 고정 특징에서 음성 사건과 음악 사건을 함께 학습하는 12계수 모델이 됐다. Voice와 Music의 BCE를 유지하고 File BCE만 class/source 균형을 반영한 pairwise logistic ranking으로 바꿨다. 이는 불연속 EER 자체를 직접 최적화한 방법은 아니며, REAL보다 FAKE의 File 점수가 높도록 유도한 순위 목적함수였다.

공개200은 ITW 음성20개, MUSAN-RFM 실제 음악10개, ArtifactBench 생성 음악10개의 총40부모에서 나온 10 source-pair × 20변형이었다. 가짜 음악은 Udio, MusicGen Large, Suno의 두 태그, Riffusion을 포함했다. component-only·동시혼합·순차·4+4초 two-phase, wide·16k μ-law 조건을 구성했고, 각 outer fold의 학습160과 평가40 사이 음악·음성 부모 SHA 교집합은 0이었다. 그러나 화자·작곡가·상류 사전학습 전체의 독립성이나, 같은200에서 반복한 방법 선택의 편향까지 제거한 것은 아니었다.

C412의 File EER은 source-pair OOF에서 C349 0.129670330 → 0.114835165였다. 실제 작은16개에서는 0.25 동률, 별도8개에서는 0.50 → 0.25였다. 반면 10 source-pair를 묶어 재표집한 개선량의 95% 구간은 −0.022609890에서 +0.078021978로 0을 포함했다. 전체 OOF의 10개 오류를 고치면서 7개 새 오류를 만들었고, 한 source-pair는 EER 0 → 0.109890으로 나빠졌다. 작은 패널의 개선은 실제였지만 넓은 일반화 증거는 약했다.

C413은 원 C349에 Nes2Net/WavLM singing 모델과 이 공동 head를 붙이고 **외부 File만 교체**한 제출이었다. 실행 감사상 새 값은 실제 출력에 연결되어 있었다. 그러나 C349의 같은 시각 진위·존재를 함께 요약한 aligned Voice/Music, raw/stem 사건의 hard-max를 새 affine head가 똑같이 보존하는 구조는 아니었다. Fourier와 전역 Presence가 모두 사라졌다고 설명하는 것도 부정확하다. 그 특징들은 남았지만 사건 입력·학습 목표·점수 척도·비선형 집계가 함께 바뀌었다.

사용자 제공 서버 결과는 ADS **0.8003809524**, 총점 0.8192515079로 C349보다 ADS 0.0153571428 낮았다. 이 실패는 “Nes가 실행되지 않았다”가 아니라 공개에서 고른 전면 교체가 서버로 전이되지 않았다는 관측이다. 서버의 숨은 생성기나 혼합 비율을 알아낸 결과는 아니다. 이후 회고의 기준은 새 모델의 개별 지표뿐 아니라, 원 구조가 지키던 강한 한쪽 증거와 시간 관계를 무엇으로 대체했는지 확인하는 것이 됐다.

근거: `research/c412_pairwise_joint_file/C412_RESULT_REPORT_2026-09-10.md`, `SOURCEPAIR_UNCERTAINTY_2026-09-10.md`; `docs/C413_RESEARCH_AND_SUBMISSION_2026-09-10.md`; `docs/C414_C413_FAILURE_AND_VALIDATION_RESET_2026-09-10.md`.

### 3.2 C414–C446: 실제 표현 학습도 출처와 최종 역할을 넘어서야 했다

C413 뒤에는 출력 조합만 바꾸는 데서 벗어나 표현 자체를 학습했다. C414는 C205 Deezer의 전체 CNN을 갱신하며 여섯 음성·채널 조건을 억제하는 gradient reversal 보조목표를 넣었다. 696음악 원천의 실제4,176파형, 3epoch·3,132update를 완료했다. 첫 convolution의 gradient와 변경, GRL 부호, 저장·복원, held 비사용도 확인했다. 그럼에도 held766/133원천 EER은 **0.225889 → 0.241594**로 나빠졌다. 훈련 BCE 감소와 조건 보조학습만으로 불변 표현이나 일반화를 얻었다고 주장할 수 없었다. 자료 균형과 전체층 갱신도 함께 바뀌었으므로 GRL 하나를 실패 원인으로 확정하지 않았다.

C417은 SONICS 전체 encoder를 File OR 목표로 학습했다. 744원천·4,464파형, 4epoch·2,232update를 완료했지만 File EER은 0.318566이었다. 깨끗한 음악만으로 동일 정답을 비교하면 C205의 EER 0.199359보다 C417의 0.300641이 나빴다. 실제 음악에 Kokoro 가짜 음성을 더해 File 점수가 오르는 방향은 과제와 맞지만, 실제 LibriSpeech 음성도 REAL 파일의 점수를 높였다. 합성 음성 held는 같은 Kokoro의 다른 네 음원에 불과해 새 TTS/VC 전체로 일반화한 근거도 아니었다.

음성 축도 같은 교훈을 남겼다. AASIST를 Pocket 조건에 적응한 C422는 자체 held에서 이득이 있었지만 C423의 RADAR24 EER 0.50 → 0.666667, ITW40 0.10 → 0.15로 회귀했다. C430은 Wav2Vec2 마지막 두 층과 head를 여러 생성기 자료로 학습했다. 832쌍의 wide/phone·REAL/FAKE 3,328행을 4epoch 학습한 최종 모델은 미학습 ASV 공격160에서 0.075였지만 ITW40은 0.40, RADAR24는 0.50이었다. C426의 해당 값은 0.025, 0.10, 0.50이었다. 추가 MLAAD 생성기를 배운 효과는 새 DEV에 일부 남았지만 다른 출처까지 보편적으로 좋아지지는 않았다. 원 encoder를 동결한 C435/C436 선형 대조도 ITW를 0.30으로 회복했을 뿐 ASV 0.0875, RADAR 0.50, MLAAD40 0.30으로 범용 교체 근거를 만들지 못했다.

C445는 더 좁고 실제 배포와 가까운 가설이었다. 혼합 원음 대신 Demucs vocals를 학습하고 clean 음성도 함께 보존하도록 Spectra의 마지막 block23만 적응했다. 실제 TRAIN96, 별도 DEV80에서 분리 음성 EER **0.05 → 0**, clean 0 유지라는 결과를 얻었다. 하지만 C446에서 같은 학습 block을 실제 C349 raw/stem·시간·File 결합에 넣자 8파일 EER/AUC는 0.50/0.625 동률이었다. 두 REAL 혼합 파일의 음성 사건과 File 의심 점수는 오히려 올랐다. 작은 DEV의 성공은 지우지 않되, 그것을 최종 File 개선으로 승격하지 않은 사례다.

근거: `research/c414_adversarial_full_training/C414_RESULT_AND_FAILURE_2026-09-10.md`; `research/c417_sonics_file_training/C417_RESULT_AND_LIMITS_2026-09-10.md`; `research/c423_aasist_cross_generator_probe/C423_RESULT_AND_FAILURE_2026-09-10.md`; `research/c433_c430_final_external/C433_C434_FINAL_FINDINGS_2026-09-11.md`; `research/c436_frozen_probe_external/C435_C436_FINAL_FINDINGS_2026-09-11.md`; `research/c445_spectra_stem_adaptation/C445_RESULT_AND_LIMITS_2026-09-11.md`; `research/c446_spectra_stem_file_transfer/C446_RESULT_AND_STOP_2026-09-11.md`.

### 3.3 C465: 새 생성기 학습은 성공했지만 짧은 사건의 증거가 희석됐다

음악 학습의 기본 자료는 631곡에서 파생한 3,690행이었다. REAL은 FMA273곡과 MUSAN24곡, FAKE는 334곡이었다. 같은 고정4초 음악에 clean, 실제 음성 혼합, Kokoro 합성 음성 혼합과 전화 변형을 적용했다. 학습 질량은 클래스→identity→view 균등이었으며 생성기 균등은 아니었다. FAKE 음악에서는 Suno 네 bucket과 Yue가 큰 비중을 차지했다. outer766은 133곡의 변형이며 FAKE78곡 중 DiffRhythm50곡은 TRAIN에 없었다. 그러므로 완전한 generator-held도, 동일 분포 평가도 아니었다. 3,690행을 3,690개의 새 음악으로 이해하면 자료 다양성을 크게 과장하게 된다.

C461은 C205의 판단을 같은 기존 입력에서 증류해 held766 EER을 0.225889 → 0.190674로 낮췄다. C465는 여기에 AIME Riffusion48개 × 여섯 조건=288행을 추가했다. 합계 TRAIN3,978행/679곡, 12epoch·5,976update였고 기존 입력에만 C205 teacher를 적용했다. 새 생성기의 오답까지 강제로 보존하지 않도록 새288행은 BCE만 사용했다. 별도 Riffusion16곡의96변형에 재사용 REAL314행을 붙인 EER은 C205 **0.247611 → 0.001592**였다. 가까운 새 생성기에서 강한 학습 효과가 있었지만, 새로운 REAL 검증도 아니고 모든 생성기에 대한 보증도 아니었다.

기존766 EER은 C461과 0.190674 동률이었다. 실제 C349의 C205 슬롯으로 옮긴 C466은 Music160 0.25 → 0.2375, File200 0.129670 동률, novel64 0.124103 동률이었다. 별도16음악 부모의128변형 C467에서는 외부 Music EER 0.1875 동률이었다. 12초 안 가짜 음악2초를 교체하고 실제 음성을 겹친 조건의 외부 Music EER은 0.4375로 남았다. 새 생성기 단독에서 보인 큰 개선을 최종 제출 점수에 더할 수 없는 이유가 구체화됐다.

저장된 창별 점수 감사에서는 Deezer가 사건을 전혀 못 본 것이 아니었다. 2초 삽입 구간 안에 두 창이 들어가 사건의 78%를 읽었고, 대응 REAL/FAKE 쌍의 국소 순위도 C205 9/16 → C465 11/16으로 좋아졌다. 하지만 C180과 평균하고 전체 창을 Presence로 집계한 뒤에는 9/16, 최종 외부 Music은 10/16이었다. 한 예에서는 국소 C465가 REAL 0.357189/FAKE 0.784186이었지만, 최종 Music은 0.163674/0.156255로 순서가 뒤집혔다. 역방향 Fourier와 사건 밖 창을 고른 Dasheng이 결합에 함께 작용했다. 반대로 국소 판별부터 틀리는 부모도 남았다. 따라서 문제는 관측 누락·집계 희석·국소 판별 오류가 함께 있는 것이며 pooling 변경 하나가 모든 실패를 해결한다고 단정할 수 없었다.

근거: `research/c566_eat_lastblock/C566_PUBLIC_TRAINING_COVERAGE_AUDIT.md`; `research/c461_deezer_teacher_preservation/C461_RESULT_AND_LIMITS_2026-09-11.md`; `research/c465_riffusion_expansion_kd/C465_FREEZE.md`, `C465_RESULT_AND_LIMITS_2026-09-11.md`; `research/c466_c465_music_transfer/C466_RESULT_AND_NEXT_2026-09-11.md`; `research/c467_c465_broader_transfer/C467_RESULT_AND_LIMITS_2026-09-11.md`, `C467_PARTIAL_WINDOW_DIAGNOSIS_2026-09-11.md`.

### 3.4 C473–C547: 부분 위조와 시간 attention, 그리고 원 교사 보존

C473은 C465 특징을 동결하고 4,545파라미터 시간 head를 학습했다. 기존3,978행에 실제 편집한1,024행을 더했다. 같은 위치를 편집한 REAL 대조(RR), REAL 배경에 2초 FAKE를 넣은 RF, 연속 REAL/FAKE와 전화 조건이 포함됐다. local occupancy와 max-logit bag을 함께 감독했다. 5,002행/5,976update를 완료했지만 새 held256 전체의 이득이 부분 위조의 일관된 이득은 아니었다. partial128 EER은 C465 max 0.296875보다 C473 0.3125가 나빴다. 반면 C475에서 C180과 고정 결합하자 Music160 0.25 → 0.2125, novel64 0.124103 → 0.078462의 보완성은 나타났다.

C488은 경계 보조학습을 더해 새 held256 EER을 0.199219 → 0.179688로 개선했다. 주된 이득은 연속 음악에서 왔으며 부분 wide는 0.25 → 0.3125로 손실이었다. 병행한 새로운 특징 학습도 만능은 아니었다. C493의 fresh 주파수 패턴 분류기는 기존766 EER 0.477792, C497의 위상 CNN은 0.334233이었고, 마스킹·mixup을 더한 C499는 0.382454였다. C497의 훈련 BCE가 거의0으로 내려갔다는 사실은 held 일반화의 증거가 아니었다. scratch 선형 스펙트럼 LCNN인 C549도 실제7,380파형 학습을 마쳤으나 outer766 EER 0.351044로 기준0.225889보다 약했다. 새40의 별도 신호가 있더라도 전체 교체는 정당화되지 않았다.

C520은 평균과 최댓값의 절충을 고정 규칙으로 고르지 않고 **학습 가능한 gated attention**으로 구했다. frozen C465 특징과 원 logit, 시간 convolution, 경계 보조 head를 쓰는 5,651파라미터 구조였다. 동일5,002행을 12epoch·5,976update 학습하고 파일 안 유효 창들의 local logit을 attention으로 가중합했다. 이 연산은 기존 Presence 가중 확률 평균과 다르다. 마지막 수치 검사에서 FP32 batch-shape 차이로 logit 오차가 2.384e-6이 되어 중단했지만, 확률 차이는 4.47e-8, invalid padding 영향은0이었다. 체크포인트를 재학습하지 않고 단일 파일 경로로 평가를 복구했다. 수치 검사의 중단과 실제 성능 실패를 분리한 기록이다.

C532는 C349의 외부 Music에서 C205 절반을 C465+C520 bag으로 교체했다. 나머지 전문가와 기존 C346 배합계수, File·Voice·Presence는 유지했다. 공개 Music160은 0.25 → 0.2125, novel64는 0.124103 → 0.045641, extra128은 0.1875 동률이었다. 그러나 overlap은 0.30 → 0.40으로 나빠졌다. 정상 서버 실행 뒤 사용자 보고 ADS는 **0.8123095238**로 C349보다 낮았다. 원 C205 직접 판단이 사라졌고, 새 점수의 시간 집계·척도·다른 전문가와의 오류 관계가 달라졌는데 옛 결합계수를 그대로 적용한 것이 확인 가능한 구조적 차이였다. 이것을 서버 회귀의 유일한 원인으로 확정하지는 않았다.

C536은 원 C205의 창별 판단과 파일 확률평균을 attention 학습에 직접 증류했다. 단독 all862 EER은 C520 0.172666 → C536 0.197266으로 나빠졌지만, 고정 최종 조합에서는 extra128이 0.1875 → 0.15625로 좋아지고 overlap 손실 일부를 회복했다. 단독 EER만으로 후보를 버려도 잘못될 수 있다는 반례다. 이를 Music-only로 패키징한 C547의 사용자 보고 ADS는 **0.8131666667**이었다. C532보다는 조금 좋았지만 C349를 넘지 못했다. 교사를 보존하는 학습, 입력을 보존하는 결합, 실제 정답을 보존하는 결과는 각각 별도로 확인해야 했다.

근거: `research/c473_diverse_longbag_training/C473_FINAL_RESULT.md`; `research/c488_boundary_auxiliary/C488_RESULT.md`; `research/c493_robust_fourier_training/C493_RESULT_AND_FAILURE.md`; `research/c497_phase_cnn_training/C497_RESULT_AND_FAILURE.md`; `research/c499_regularized_phase_training/C499_RESULT_AND_FAILURE.md`; `research/c549_linear_spectrum_lcnn/C549_RESULT_AND_NEXT_DECISION.md`; `research/c520_learned_temporal_pool/C520_FREEZE.md`, `C520_FINAL_PARITY_FAILURE_2026-09-12.md`; `research/c532_c520_music_submission/C532_PUBLIC_EVIDENCE_AND_HANDOFF.md`; `research/c533_c532_postmortem/AUDIT.md`; `research/c536_c205_teacher_attention/C536_C537_RESULT_AND_LIMITS.md`; `research/c548_c547_postmortem/C548_SERVER_RESULT_AND_SCOPE.md`.

### 3.5 C548: 검증의 독립성을 다시 셌다

C547 이후 감사는 공개 개선을 세 번의 독립 성공처럼 해석하기 어렵다는 사실을 확인했다. Music160은 C346 최종 결합기의 실제 학습 자료였다. novel64와 extra128도 새로운 모델에 한 번만 쓴 확인군이 아니었다. 정확 SHA 대조에서 **extra128의 음악 부모16개 전부가 novel64에도 있었고, novel64의35행이 그 부모에서 나왔다.** extra128은 8음악쌍/16부모, REAL artist7명과 추가 음성2부모의 변형이며 공유 음성을 포함하면 부모 그래프가 하나의 연결군이었다.

검증 범위 역시 길이·코덱·채널을 완전히 교차하지 못했다. Music160은 4/8초 mono WAV와 과거16k μ-law였고, extra128은 4/12초·true8k 전화와 일정 RMS 혼합이었다. novel64에는 실제45초와 FLAC가 있었지만 FLAC는 복제 dual-mono였고 native stereo나 최종 MP3 검증을 대신하지 못했다. “긴 음원을 전혀 보지 않았다”도 틀렸지만 “여러 포맷을 포괄했다” 역시 지나친 설명이었다.

이후 기존200/64/128/16은 회귀와 원인 진단용으로 명시하고, 새 원천의 학습·배합 선택·확인 역할을 먼저 고정하는 방향으로 전환했다. 같은 부모의 변형 수를 늘리는 것, 동일 생성기의 새 곡을 추가하는 것, 미관측 생성기를 검증하는 것은 다른 작업이었다. source-authenticity proxy와 실제 음악·음성 성분 라벨도 분리했다. 이 재정비가 서버 점수 상승을 보장하지는 않지만, 공개 지표의 의미를 더 정확히 제한했다.

근거: `research/c548_c547_postmortem/VALIDATION_RESET_FINDINGS.md`와 그 문서가 참조하는 `C548_MANIFEST_COVERAGE_CHECK.json`.

### 3.6 C572–C596: EAT는 새 표현을 주었고, 역할 설계가 성패를 갈랐다

C564에서는 공개 EAT-base의 원본 자산과 revision·라이선스·의존성을 확인했다. 이를 이미 성공한 탐지 가중치로 취급하지 않고 frozen head와 마지막 block 적응을 실제로 검증했다. C572는 C566에서 출발해 새 음악97개와 sparse 음악·실제 음성 조건을 추가했다. 원3,690+582=4,272행/728음악, 2epoch·1,068update였다. outer766 단독 EER은 C566 0.220492 → C572 0.235091로 나빠졌지만, 같은 multiwindow extra128에서는 **0.3125 → 0.203125**로 크게 좋아졌다.

그러나 C572를 기존 Deezer 슬롯의 1/4로 넣는 고정 방식은 최종 Music EER 0.1875 동률에 그쳤다. partial2초 조건은 C349 0.4375, C572 단독0.3125였는데 결합은0.50으로 더 나빴다. 좋은 새 모델의 신호를 기존 입력 한 곳에 작게 넣는 것만으로 전달할 수 없다는 분명한 사례였다. C575는 EAT를 독립된 네 번째 logit 입력으로 두고 D239·Fourier·Dasheng과 공개304에서 결합했다. 새72부모의 중앙4초/최대60초144행을 9 source-group fold로 나눴고, 기존Music160은 모든 fold 학습에 남았다. 따라서 새144 성적은 **결합기 수준의 group-held**였다.

C575의 새144 EER은 C349 0.180556 → 0.152778, fresh40은0.10 → 0.05, extra128은0.1875 → 0.171875였다. factorial16은0.25 → 0.375로 회귀했다. C577 제출의 사용자 보고 ADS는 C349와 **0.8157380952 동점**이었다. 동일 점수는 미실행 증거가 아니었다. 공개 old160에서는 EER와 AUC까지 같았지만160개 확률이 모두 바뀌었고, 올바른 REAL–FAKE 순서269쌍 손실과269쌍 개선이 상쇄됐다. 집계 점수 동률과 출력 동일을 구별해야 했다.

C583은 동일 위치의 REAL 편집 대조와 2초 FAKE 치환·실제 음성 자료를 더해4,400행을2epoch·1,100update 학습했다. multi128 단독 EER은 C572 0.203125 → **0.140625**였고 전체 경계에서8개를 고치며 새 오류는0이었다. 다만 목표 partial 하위 EER은0.3125 동률이었다. 독립 전문가로 결합한 C584는 extra128 전체0.140625를 얻었으나 partial은0.4375로 다시 약해졌다. C586은 fresh40 EER0이라는 결과까지 갖고 제출됐지만 사용자 보고 ADS **0.8131666667**로 회귀했다. 작은 새 패널의 완벽한 순위도 서버 우위를 보장하지 못했다.

C593은 적응 block 대신 원 frozen EAT의 **4/8/12층**에서 CLS·patch 평균·모집단 표준편차를 뽑고, 세 독립 작은 head의 logit을 평균했다. 같은4,400행을6epoch·1,650update 학습했다. outer766 EER은 C583 0.210184 → **0.165767**로 좋아졌다. extra128에서는 각 조건 EER이 동률 또는 개선인데도 전체 EER은0.140625 →0.1875로 나빴다. 조건 내부 순위가 좋아도 조건 사이 점수 정렬이 나빠질 수 있다는 사례다.

C594는 이 raw C593을 같은304행·9fold 방식으로 독립 결합했다. 새144 EER은0.125, extra128은0.140625, fresh40은0.05, novel64는0.078462, factorial16은0.25였다. C349 대비 다섯 패널이 동률 또는 개선이었지만 C584의 fresh40 EER0은 잃었다. 원천군집 bootstrap의 모든95% 구간은0을 포함했다. 이를 외부 Music-only C596으로 제출한 뒤 사용자 보고 ADS는 **0.8174523810**, C349 대비 약+0.001714286이었다. 이 작은 실제 이득이 C593 표현의 보완성을 지지했지만 frozen 방식이 모든 fine-tuning보다 낫다는 일반 법칙은 아니었다.

근거: `research/c564_eat_base/C564_ACQUIRED_ASSETS.md`; `research/c572_eat_sparse_music/C572_FREEZE.md`, `C572_OUTER_RESULT_AND_LIMITS.md`, `C572_MULTIWINDOW_RESULT_AND_KEEP.md`; `research/c575_eat_independent_expert/C575_GROUPHELD_RESULT_AND_LIMITS.md`; `research/c577_c575_submission/ROOT_PUBLIC_DECISION.md`; `research/c578_c577_result_audit/C577_EQUAL_SCORE_PUBLIC_COUNTEREXAMPLES_AND_LIMITS.md`; `research/c583_eat_matched_splice/C583_TRANSFER_RESULT_AND_NEXT.md`; `research/c584_splice_eat_expert/C584_INITIAL_RESULT_AND_NEXT.md`; `research/c593_eat_depth_augmented/C593_FREEZE.md`, `C593_TRANSFER_RESULT_AND_NEXT.md`; `research/c594_depth_augmented_expert/RESULT_AND_NEXT.md`, `C594_CLUSTER_UNCERTAINTY.md`; `docs/C586_C596_SERVER_RESULTS_2026-09-14.md`.

### 3.7 C596–C651: 더 강한 단독 모델과 더 좋은 최종 출력은 여전히 달랐다

후속 표현 연구도 실제 이득을 만들었다. C630은 같은4,400행과 목적을 유지하면서 frozen EAT-large의8/16/24층을 썼다. 단독 multi128 EER은 C593 0.1875 →0.125, outer766은0.165767 →0.126747이었다. 마지막 block까지 적응한 C631은 multi128 AUC를0.932617 →0.957031로 올렸지만 전체 EER은0.125 동률, 전체 EER 경계에서 틀린16파일도 같았다. C646 시간 MIL은 partial 조건을0.25 →0.1875로 낮췄으나 전체0.125로 동률이고 다른 연속·overlap 조건에서는 기존 최종 조합에 뒤졌다.

사용자의 구조 재검토 지시에 따라 단독 모델을 최종 Music으로 직접 쓰는 비교도 수행했다. C633의 C630 직접 교체는 extra128에서 최종 C594의0.140625 →0.125로 좋았지만 새144에서는 **0.125 →0.222222**로 크게 악화했다. 기존18오류 중6개를 고치면서20개 새 오류를 만들었다. 따라서 기존 조합을 무조건 유지해야 한다는 결론도, 강한 단독 모델이면 바로 최종 역할을 맡길 수 있다는 결론도 근거가 부족했다. 무엇을 보존하고 어떤 원천에서 잃는지 같은 입력으로 직접 비교해야 했다.

근거: `research/c630_eat_large_depth/RESULT_AND_LIMITS.md`; `research/c631_eat_large_lastblock/RESULT_AND_LIMITS.md`; `research/c633_standalone_direct/RESULT_AND_LIMITS.md`; `research/c646_large_temporal_mil/RESULT_AND_LIMITS.md`; `docs/RESEARCH_STRUCTURE_RESET_2026-09-15.md`.

### 3.8 C652–C660: 전체 File 진단이 모델 추가보다 큰 변화를 만들었다

C652는 과거 fold별 예측과 실제 배포 상수를 구별해 C596의 완성된 File 경로를 다시 읽었다. 이미 학습에 노출된200행에서 File EER은0.12967033이었고, 진단 경계의 REAL 오탐9개 모두 내부 음악 사건만으로도 경계를 넘었다. 그러나 Presence를 무조건1로 만들거나 raw/stem 중 한쪽을 없애는 진단은 더 많은 정답을 잃었다. 정답을 주입한 oracle 분석도 가능한 모델 성능으로 취급하지 않았다.

전체 경로를 실제로 실행한 C654의 새40에서는 File EER0.15에 비해 외부 Music의 같은 원천 진위 EER은0.05였다. 오탐3개는 음성 사건만 충분한 경우, 음악 사건만 충분한 경우, 둘은 경계 아래지만 OR 뒤 넘은 경우로 갈렸다. C653의 ASV8발화 clean/실제 반주16개에서는 File·Voice EER0을 지켰지만 REAL 음성에 반주를 더하면 내부 음악 사건 때문에 File 의심 점수가 올랐다. 반면 FAKE 음성은 raw 점수가 약해져도 stem이 강한 증거를 보존했다. stem 삭제나 음악 단독 판단이라는 간단한 처방은 두 결과를 함께 설명하지 못했다.

더 넓은 진단에서는 원천400개를 개발300/확인100으로 나누려 했고, 당시 정상 확보378개 가운데 **진단280개(REAL130/FAKE150)**를 먼저 고정했다. 점수를 보고 대체한 것이 아니라 확보 가능성에 따른 범위 제한이었다. 중앙10초를 C596 전체 경로로 읽었고, 초반8개의 중앙 처리시간은18.94분, 계산시간의90.39%가 DF phase였다. 모델 로드 재사용만으로 대부분의 비용을 없앨 수 없었다. 이후 구조 대안은 이 느린 추론을 다시 반복하기보다 보존된 중간값으로 비교했다. 잠금 확인 자료는 후보 확정 전 개발에 사용하지 않았다.

C658은 두 사건 OR를 max로 바꾸거나, 외부 Music×Presence를 직접 File에 연결하는 소수의 고정안을 비교했다. OR→max는 진단280 EER0.139231 →0.10718로 좋았지만 기존200은0.12967 →0.15549로 나빴고, two-phase는0.20 →0.30으로 회귀했다. C659는 기존 음악 사건의 global 입력만 외부 Music으로 바꿨다. 새40에서는0.15 →0.10이었으나 진단280은0.139231 →0.146410, two-phase는0.20 →0.283333이었다. 모두 단순 실행 오류가 아니라 측정된 이득과 손실이었다.

C660은 더 좁은 입력을 바꿨다. File 음악 사건에는 기존 global/aligned 음악 근거 외에 Fourier 단독 logit이 별도 직접 입력으로 들어갔다. **그 직접 Fourier 입력만 이미 계산된 C596 외부 Music으로 교체**하고 계수, aligned/global 음악, Presence, raw/stem Voice max와 최종 OR를 유지했다. Fourier 자체는 여러 음악 경로 안에 남았다. 새 모델·fit·신경망 호출·서버 점수 기반 계수 선택은 없었다.

| 별도로 해석해야 하는 공개 패널 | C596 File 계열 EER | C660 EER | 의미 |
|---|---:|---:|---|
| 개발 source-proxy280 | 0.139231 | 0.078462 | 후보를 고른 진단 자료 |
| 개발 source-proxy40 | 0.150000 | 0.050000 | 반복 사용한 작은 대리 정답 자료 |
| 노출160, 외부 Music 점수 존재 | 0.180909 | 0.138182 | 학습·개발 노출 자료, 전체200 아님 |
| 위160 중 File 정답 명확한110 | 0.063333 | 0.063333 | 중첩 부분집합, 독립 추가 성공 아님 |
| 고정 후 별도 확인100 | 0.140000 | 0.020000 | FMA50/AIME50,35출처군의 한 번 비교 |

확인100은 원래 진단 출처군과 분리했고 후보를 고정한 뒤 전부 평가했다. 각 모델 경계에서14오류 →2오류, 13개 수정/1개 손실이었으며 AUC는0.96 →0.9972였다. 군집 bootstrap의 EER 감소95% 구간은[0.0321,0.1883]였다. 그러나 FMA/AIME의 출처와 진위가 연결되어 있고 성분 정답은 미확정이므로 공식 ADS나 서버 성공 확률로 환산하지 않았다. 한 번 사용한 뒤에는 더 이상 미사용 확인군이라고 부르지 않았다. 별도 음성·순차혼합16개에서는 EER0을 지켰지만 REAL File 점수는 평균0.070159 올라 정답 여유가 줄었다.

C660 ZIP은 6,603,310,574바이트로 완성됐고 원 C596의 가중치·requirements와 무거운 추론 경로는 동일했다. 실제 공개116입력의 로드→전처리→직렬 추론→CSV와 파일별 독립성·보존 출력 검사를 통과했다. 이는 Windows CPU 직렬 증거이며 Linux/L4 한 프로세스 전체 검증을 새로 수행한 것은 아니었다. 이후 사용자가 제공한 서버 결과는 총점 **0.8436157937 / ADS 0.8274523810 / CPS 0.9890865079**, 실행26분15초였다. C596보다 ADS 약0.01000 개선되어, 이미 학습한 음악 신호의 File 전달 경로를 바로잡는 변경이 해당 평가에서 유효했음을 확인했다. 공개 EER 감소량을 서버 ADS에 합산한 기대값은 사용하지 않았다.

근거: `research/c652_c596_full_diagnosis/RESULT_AND_NEXT.md`; `research/c653_c596_matched_panel/FULL16_INTERPRETATION.md`; `research/c654_c596_fresh_file/FULL40_RESULT_AND_NEXT.md`; `research/c657_c596_ten_second_pilot/SMALL8_INTERPRETATION_AND_NEXT.md`, `LARGE280_SCOPE.md`; `research/c658_file_structure_2x2/RESULT_AND_NEXT.md`; `research/c659_preserved_music_input/RESULT_AND_LIMITS.md`; `research/c660_direct_music_evidence/RESULT_AND_LIMITS.md`, `C660_FROZEN_CONFIRMATION_PLAN.md`; `docs/C660_CONFIRMATION_AND_SUBMISSION_2026-09-19.md`; `docs/C660_SERVER_RESULT_AND_NEXT_2026-09-20.md`.

### 3.9 공개 측정과 사용자 제공 서버 결과를 분리한 기록

아래는 공개 검증에서 계산한 값이 아니라 보존 보고서가 사용자 제공 제출 화면으로 기록한 집계값이다. 서버의 개별 예측·정답이나 성분별 EER를 직접 얻은 기록이 아니다. 제출 파일명이 표시된 화면과 로컬 후보의 연결에도 보고서별 한계가 있으므로 “비공개 평가를 직접 감사했다”는 표현을 쓰지 않는다. 기간 전체의 최종 최고점·순위는 후속 구간에서 별도로 다룬다.

| 후보 | 의도한 변경 출력 | 사용자 보고 ADS | 사용자 보고 총점 | CPS |
|---|---|---:|---:|---:|
| C349 기준 | Music | 0.8157380952 | 0.8330729365 | 0.9890865079 |
| C413 | File | 0.8003809524 | 0.8192515079 | 0.9890865079 |
| C532 | Music | 0.8123095238 | 0.8299872222 | 0.9890865079 |
| C547 | Music | 0.8131666667 | 0.8307586508 | 0.9890865079 |
| C577 | Music | 0.8157380952 | 0.8330729365 | 0.9890865079 |
| C586 | Music | 0.8131666667 | 0.8307586508 | 0.9890865079 |
| C596 | Music | 0.8174523810 | 0.8346157937 | 0.9890865079 |
| C660 | File | 0.8274523810 | 0.8436157937 | 0.9890865079 |

CPS가 같고 다른 네 출력 보존 계약이 실제 서버에서도 성립했다는 전제하에 변화의 역할을 설명할 수는 있다. 그러나 이 집계값으로 서버의 생성기·채널·길이 비율, 개별 라벨 또는 오류를 역산해 다음 계수를 맞추지는 않았다. C596 서버 시간에는 보존 문서 간 26분53초/26분35초의 상충 기재가 있다. 점수와 달리 이 시간은 회고의 비교 근거에서 제외하며, 두 기록을 임의로 같은 값으로 고쳐 쓰지 않는다.

### 3.10 이 구간이 남긴 실험 설계상의 교훈

첫째, **학습 완료·실행 검증·성능 개선은 별개**였다. C414의 전체 CNN gradient, C430의 strict load, C520의 저장 모델 복구, C549의 실제 학습은 작업이 실행됐다는 근거다. 그것이 일반화를 보장하지 않았다. 반대로 수치 허용치나 로그 저장 실패 때문에 끝난 모델을 학습 실패로 취급하거나 처음부터 다시 돌리는 것도 피해야 했다. 실제1음원→작은 batch→고정 성능 측정을 일찍 수행하고 완료된 특징·점수·체크포인트를 재사용하는 방식이 제한된 CPU·RAM 환경에서 특히 중요했다.

둘째, **전문가의 역할과 결합 위치가 모델 선택만큼 중요**했다. 같은 EAT가 Deezer의 작은 일부일 때, 독립 전문가일 때, 외부 Music일 때, File 사건의 직접 입력일 때 효과가 달랐다. 외부 Music이 좋아져도 File 내부 음악 사건은 그대로일 수 있었다. File/Voice/Music 출력은 이름만 다른 같은 확률이 아니며, 실제 배포 수식과 같은 경로로 측정해야 했다. 좋은 단독 모델 여러 개의 개선 폭을 더해 예상 ADS를 만드는 방법은 근거가 없었다.

셋째, **전체 EER·조건별 EER·오류 교환을 함께 보아야** 했다. C593처럼 모든 조건 안의 EER이 동률·개선인데 전체는 악화할 수 있고, C577처럼 EER/AUC가 같아도 확률과 순위는 크게 달라질 수 있다. 오류를 고친 수만 보고 새로 잃은 정답을 숨기면 보완성의 실체를 알기 어렵다. 보고서의 ROC 경계는 설명 도구였으며 제출 임계값으로 옮기지 않았다.

넷째, **파일 수보다 독립 원천과 노출 이력이 중요**했다. 766행은133곡, 128행은8음악쌍의 변형이었다. 분할이 exact SHA에서 깨끗해도 artist·speaker·prompt·상류 사전학습 독립을 모두 보증하지는 못했다. 검증을 반복 관찰한 뒤 구조를 고르면 그 자료는 개발 자료다. C548의 부모 중복 확인과 C660 후보 고정 후 확인100은 이 점을 실험 운영에 반영한 중요한 변화였다.

마지막으로 모든 시도는 출처·버전·라이선스와 실제 학습파일 보존 기록을 남기는 범위에서 진행됐다. 공개 비영리 연구 사용 판단과 최종 수상 산출물의 독점적 권리 이전은 별도 문제였고, 여러 계보의 권리 HOLD는 이 구간에서 포괄 해소되지 않았다. 이 회고에 모델·음원이나 파일별 검증 예측을 포함하지 않는 이유도 성능 설명과 제3자 자산 재배포를 분리하기 위해서다. 실험 당시의 계획·초안은 완료 결과로, 공개 proxy는 공식 ADS로, 사용자가 보고한 순위는 공식 최종 순위로 바꾸어 서술하지 않는다.

## 4. C660 이후: 좋아진 것은 무엇이고, 왜 더 이상 오르지 않았나

### 4.1 C660 → C693: 정보가 전달되는 경로를 고친 두 번의 상승

C660의 서버 ADS는 **0.8274523810**이었다. C596의 0.8174523810에서 +0.0100000000이다. 새 전문가를 추가한 것이 아니라, 이미 계산한 외부 Music 앙상블의 증거가 File 내부로 전달되도록 직접 Fourier 입력 슬롯을 교체한 변화였다. 여러 전문가가 알아낸 FAKE 증거가 최종 결합에 충분히 도달하지 않는다는 정량 진단이 유효했다.

C682는 원음 음성 경로의 커버리지를 바꿨지만 서버 ADS가 C660과 같았다. 이 동점만으로 서버가 해당 출력을 무시했다거나 특정 유형이 없었다고 결론 내릴 수 없다. EER은 확률값 전체의 변화량이 아니라 순위와 오류 경계에 반응한다.

다음에는 File 내부 음성 경로를 살폈다. 원 DF-Arena가 실제 음악을 FAKE 음성 증거로 읽는 공개 자료의 오류를 억제하되 실제 위조 음성 탐지를 보존하려 했다. 초기 C687은 부족한 native-music 노출과 보존 성능 때문에 탈락했다. C688은 ASV/MLAAD × REAL/FAKE 네 음성 그룹과 native-music을 매 update에 포함하는 고정 학습으로 변경했다. 원 모델 전체를 다시 학습하지 않고 마지막 Conformer 블록과 분류기를 학습했다.

검증 결과는 패널의 성격과 함께 해석했다.

| 공개 평가 | 관측 | 한계 |
|---|---|---|
| C689 known40 | File EER 0.05 보존 | 반복 사용한 소규모 공개 자료 |
| C691 오류선택 41 | 설명용 임계값 오류 22→17; REAL 오탐 6개 회복·새 손실 1개, 순위쌍 72개 개선·2개 손실 | 오류를 골라 만든 source-proxy 패널이며 일반 오류율이 아님 |
| C692 source-proxy 100 | EER 0.02 / AUC 0.9972 보존; 순위쌍 3개 개선·3개 손실 | File/Voice/Music의 완전한 공식 정답이 아님 |

C693은 이 학습 tail을 **File 내부 원음/분리음 음성 판단에만** 사용했다. 원 DF encoder의 중간 표현을 공유하여 비싼 전체 encoder를 두 번 실행하지 않았다. 외부 Voice에는 원 DF를 그대로 사용했고, 외부 Music과 두 Presence도 유지했다. C660의 음악 전달 경로 역시 유지했다.

사용자 제공 서버 결과는 **ADS 0.8362380952**, 총점 0.8515229365, CPS 0.9890865079, 26분 53초였다. C660 대비 ADS +0.0087857142다. 구현상 바뀐 출력은 File뿐이라는 점과 집계 점수의 상승은 확인할 수 있지만, 서버의 개별 파일 오류나 유형별 구성은 알 수 없다.

로컬 깨끗한 Windows 환경에서는 실제 음원 → 음악 → DF → Spectra의 직렬 smoke test와 CSV 출력을 확인했다. 기록된 전체 출력 최대 차이는 약 3.05e-8이다. 이것을 Linux/L4의 모든 파일·최대 메모리 재현까지 검증한 것으로 확대하지 않는다. 사용자 서버 제출 완료 사실과 로컬 실행 검증의 범위는 별개다.

근거: `docs/C660_SERVER_RESULT_AND_NEXT_2026-09-20.md`, `docs/C693_SERVER_RESULT_AND_NEXT_2026-09-24.md`, `docs/C693_FILE_VOICE_ADAPTATION_2026-09-24.md`.

### 4.2 C704·C710·C722: 단독 지표 개선이 배포 조합의 개선은 아니었다

C704는 File 내부 Deezer 쌍을 C180+C205에서 C180+C465로 바꿨다. 외부 Music은 바꾸지 않았다. 서버 결과는 C693과 **정확히 같은 ADS**였다. C709의 공개 자료 추적에서는 변화가 단계마다 줄어들었다. C465−C205 평균 절대 차이 약 0.07997이 평균 혼합 후 0.03999, presence 집계 후 0.03909, qMusic에서 0.01129, File에서 0.00973이었다. known40의 400개 REAL–FAKE 순위쌍은 모두 그대로였고, retention100에서는 일부 순위 개선이 있었지만 EER은 0.02 그대로였다. 따라서 ‘변경이 실제 적용되지 않았다’가 아니라 **변경은 전달됐으나 EER 경계를 충분히 바꾸지 못했다**는 설명이 공개 측정과 부합한다. 숨은 서버 데이터의 구성에 대한 증명은 아니다.

C710은 평균의 영향을 없애고 C465를 단독으로 넣었다. 선택 오류 패널의 EER은 크게 좋아졌지만 개선이 Riffusion에 편중되었고, 다른 조건에는 퇴행 경고가 있었다. 서버 ADS는 **0.8353809524**로 하락했다. C180과의 평균은 단순한 희석이 아니라 보완 역할을 하고 있었을 가능성이 있다. 단독 모델 개선 폭을 최종 ADS 개선으로 환산할 수 없다는 사례다.

C722는 File 음성 경로의 raw/stem `max`를 평균으로 바꿨다. known40·오류 패널·일부 혼합 자료는 좋아졌으나 retention100 EER이 **0.02→0.04**로 나빠졌다. 서버 ADS도 **0.8341666667**로 하락했다. 당시에는 이미 공개 검증에 보존 실패가 드러나 있었다. 이 결과를 오직 ‘서버 분포가 예상과 달랐다’로 설명하면 안 된다. 제출 판단에서 보존 패널의 경고를 충분히 반영하지 못한 것도 실패 원인이었다.

C723의 내부 Spectra 변경도 EER 동률·AUC 하락으로 기각했다. 이후에는 기존 최고 C693을 고정 대조군으로 두고, 얻은 정답뿐 아니라 잃은 정답과 순위쌍을 함께 기록하는 방향으로 바꿨다.

근거: `docs/C704_SERVER_TIE_AND_NEXT_2026-09-25.md`, `docs/C710_SERVER_REGRESSION_AND_LESSON_2026-09-26.md`, `docs/C722_SERVER_FAILURE_AND_RESEARCH_RESET_2026-09-27.md`.

### 4.3 C724–C728: 모델 문제와 평가 해석 문제를 분리

C724 순수 음성 40개에서는 C660과 C693의 관련 경로가 모두 EER 0 / AUC 1이었다. 이것은 음성 문제가 전혀 없다는 뜻이 아니라 해당 작은 공개 패널에서 오류를 찾지 못했다는 뜻이다. 일부 자료 이름에 telephone/G711이 있었지만 실제 입력은 다른 crop의 16 kHz µ-law였다. 실제 8 kHz 대역 제한 전화 음성과 동일시할 수 없고, crop과 codec의 인과 효과도 분리되지 않았다.

C725 혼합 12개도 두 버전 모두 0/1이었다. 과거 two-phase EER 0.20은 현재 C660이 아니라 old C349/C51의 수치였다. 같은 입력과 현재 계산 경로로 다시 확인한 C660 clear60은 EER 0.10 / AUC 0.9788889, two-phase20은 0.10 / 0.94였다. **틀린 baseline을 고치는 것은 새 모델의 성능 개선이 아니다.**

C726은 잔여 오류를 골라 두 파일만 진단했다. C693에서도 REAL File 0.851193 > FAKE File 0.698159의 잘못된 순위가 남았다. 원음/분리음 DF 증거, 정렬, presence 가중, event 집계에서 양성 증거가 약해지는 지점을 관찰했다. 오류선택 2개로 일반 EER이나 ADS를 보고하지 않았다. 이 과정의 첫 버전은 원 DF margin 재생 오차 1.1444e-5가 1e-5 허용치를 넘어 중단됐다. 입력·모델 검사 후 별도 버전에서 margin과 확률을 함께 검증하도록 검토했으며, RAM 중단이나 서버 성능 실패와 구분했다.

C727은 보존된 실제 TRAIN 네 개를 조사했다. 두 FAKE의 qVoice가 원 경로 대비 0.853052→0.779118, 0.700059→0.435671로 약해졌고, 특히 분리음 DF margin의 손실이 컸다. C728은 overlap16 + partial16의 실제 TRAIN 32개, 96개 창으로 넓혔다. FAKE BCE는 0.112436→0.196296으로 악화했지만 REAL BCE는 0.126069→0.072920으로 개선됐다. overlap FAKE 8개 중 7개, partial FAKE 8개 중 3개가 악화했다. ‘모든 부분위조가 악화했다’는 주장과는 다르다.

partial FAKE의 첫 창은 대부분 REAL이고 FAKE가 600 sample만 포함되는 경우가 있다. 파일의 FAKE 라벨을 모든 창에 그대로 복제하면 잘못된 학습 목표가 된다. 이후에는 배포 시점의 시간 집계를 포함한 **파일/bag 단위 손실**을 검토했다.

### 4.4 C729–C742: 보존 제약과 작은 head의 한계

| 계열 | 실제 변경과 TRAIN 관측 | 공개 전이 / 결정 |
|---|---|---|
| C729 | C688 마지막 block+fc5를 16 update. 새 32개 BCE 0.134608→0.108496 개선 | old speech 오류 68→74, 반대 방향 최대 drift 0.329683 > 0.10, native File 상승도 예산 초과. 공개 전이 전에 기각 |
| C730–C733 | frozen C688의 CLS 692개를 저장하고 fc5 2,562개 파라미터만 학습. old 오류 68→66, 새 BCE 0.132018 | known40 EER 0.05 동률; error41 EER 0.343137 동률·AUC 하락. strict-gain 실패로 기각 |
| C734–C736 | bias/block 고정, 1,280차원 contrast 변화로 paired ranking 학습. native REAL은 감소, 새 BCE 미세 개선 | known/error EER 동률. TRAIN 순위 손실이 미세 개선해도 실제 순위 교정은 없었음 |
| C737–C739 | clean→mix 교사 증거 복구와 보존 제약을 검토 | 수치/사전 기준 실패. C739의 복구 9.69는 고정 기준 10 미달. 사후 기준 완화로 구제하지 않음 |
| C740–C742 | 고정 644 TRAIN 보존 제약 아래 mixed source-proxy BCE 최적화. old 오류 68→47(21 회복/0 손실), mix 오류 62→42 | known EER 동률·AUC 0.9925→0.9875; error EER 동률·AUC 소폭 개선. 필수 EER 이득이 없어 기각 |

C729는 약한 one-sided retention 손실을 한 번씩 준다고 이후 update의 drift까지 보장되는 것은 아니라는 점을 보여줬다. `max(raw, stem)`는 승자 경로에만 gradient가 흐르므로 두 경로가 동시에 개선된다고도 말할 수 없다. block과 head를 함께 바꿨으므로 실패를 block 하나의 탓으로 단정하지 않았다.

C731/C734의 변화가 작았다는 이유만으로 모든 head-only 접근이 불가능하다고 결론 내리지 않았다. C740은 실제 TRAIN 오류를 상당히 고쳤지만 공개 전이에서 필요한 순위 교정으로 이어지지 않았다. 이는 단순히 학습량이 적었다는 설명보다 **목표 함수·지원 자료·최종 결합 경로의 불일치**를 다시 볼 근거였다. 반복 사용된 공개 패널이므로 통과하더라도 독립 holdout 성공이라고 부르지 않는다.

코드 운영 오류도 따로 보존했다. C741 V1의 relative/absolute 경로 receipt 비교 실패는 NN 실행 전 검증 오류였고, V2에서 경로·크기·SHA를 엄격히 해석하는 방식으로 교정했다. 학습·모델·성능 기준을 바꾼 것이 아니었다. 기각 후보의 과거 checkpoint를 골라 다시 내거나 LR/alpha를 사후 탐색하지 않았다.

근거: `research/c729_deployed_event_tail/RESULT_AND_NEXT.md`, `research/c731_fc5_only_deployed_event/TRAIN_AUDIT_DECISION.md`, `research/c734_pair_rank_contrast/TRAIN_AUDIT_DECISION.md`, `research/c740_bounded_mix_classification/TRAIN_AUDIT_DECISION.md`, `research/c742_c740_late_transfer/RESULT_AND_NEXT.md`.

### 4.5 C743–C753: 음악 readout과 event 목표를 직접 학습했지만 전이는 실패

C742의 경로 진단에서는 일부 선택 FAKE 오류의 qMusic이 판단을 지배하는 반면 qVoice는 매우 낮았다. 음악 증거를 직접 개선할 필요를 시사하지만 source-proxy 라벨만으로 개별 성분의 진위를 확정하거나 서버 구성비를 추론한 것은 아니다.

C743/C744는 원 EAT의 보존된 특징과 추가 native 72부모의 144파생뷰를 사용하여 마지막 Linear 195개 파라미터만 6 epoch, 1,704 update 학습했다. 새 자료 BCE는 0.706226→0.677582였지만 old 교사 SmoothL1 0.012252가 0.01 기준을 넘고, 새 REAL BCE 상승도 +0.016517로 +0.01 예산을 넘었다. 기각했다. 모든 확률이 올라간 관측을 곧바로 ‘bias 하나가 원인’이라고 단정하지는 않았다.

C745는 bias를 고정하고 192개 contrast 변화에 REAL 보존 제약을 걸었다. TRAIN 수치 기준을 통과했지만 공개 known/error EER은 동률이라 기각했다. C748/C749는 File에 직접 들어가는 잔차 readout을 시험했으나 TRAIN32 EER 0.0625 / AUC 0.9921875 동률, 순위쌍 교정 0이었다. 아주 작은 BCE 감소만으로 대규모 후속 평가나 제출을 진행하지 않았다.

C751은 선택 기준을 고정한 실제 음악 네 출처에서 DF 잔여 오류가 반복되는지 확인했다. 원 DF의 raw OR stem 오류 그룹 3개가 C688에서는 0개였다. 사전 확대 조건인 현재 오류 그룹 ≥2에 못 미쳐, 오류가 나올 때까지 데이터를 더 찾거나 학습을 진행하지 않았다.

C752/C753은 기존 Music source-authenticity 점수가 아닌 **Music-event bag 자체**를 학습하는 마지막 접근이었다. C752가 원 EAT의 200개 파일/280창 특징을 추출했고(전체 단계에서 성공 4창 재사용·276창 새 추출), C753이 그 특징을 재사용했다. PANN presence와 정확한 창 overlap, robust top 집계를 포함한 193개 readout 파라미터를 5 source fold로 학습했다. 공개 구성·event 라벨과 nullable 성분 마스크는 그대로 두고 모르는 성분 정답을 proxy로 채우지 않았다. File200은 구성·출처 기준 70 REAL / 130 FAKE이며, 대회의 공식 정답이 아니다.

| 마지막 C753 평가 | 고정 historical matched5(C479) | 새 event readout |
|---|---:|---:|
| pooled Music-event EER | 0.2145833333 | 0.2604166667 |
| pooled Music-event AUC | 0.864479 | 0.819479 |
| 구성·출처 File EER | 0.1296703297 | 0.1296703297 |
| 구성·출처 File AUC | 0.939890 | 0.926923 |

일부 overlap/partial에서는 이득이 있었지만 pure music 및 다른 혼합 조건의 손실이 더 컸다. 5 fold 실행·노출·저장 복원 검사는 정상이며 RAM 중단 때문에 나온 결과가 아니다. 원 warm bias 연산 순서의 FP32 차이는 별도 V2로 정확히 보존하여 교정했고 허용오차를 늘려 넘기지 않았다. 최종 all200 학습, 새 제출 ZIP, 후속 공개 전이는 진행하지 않았다.

**사용자가 2026-09-28 연구 종료를 요청했다.** 자동 재개 예약을 중지했고 연구·학습은 재개하지 않았다. 이후의 작업은 이 기록과 최고 모델의 소스 보존이다. C753 이후 아이디어는 실행 결과가 아니므로 성과 목록에 넣지 않는다.

## 5. 전체 시행착오에서 남긴 결론

1. **단독 탐지기보다 최종 출력까지의 경로를 먼저 검증해야 했다.** C660과 C693의 실제 서버 상승은 증거 전달과 제한된 내부 경로 개선에서 나왔다. 반대로 단독 모델 EER 개선을 더하면 예상 ADS가 된다는 계산은 성립하지 않는다.
2. **확률이 달라졌다는 것과 EER이 좋아졌다는 것은 다르다.** 단계별 변화량, REAL–FAKE 순위쌍, 새로 얻은/잃은 정답을 같이 봐야 한다. 서버 동점은 숨은 데이터의 유형 부재나 구현 무시를 증명하지 않는다.
3. **개발 자료가 늘어도 독립성이 늘어난 것은 아니었다.** 동일 부모의 crop/codec/혼합 변형은 같은 출처다. repeated OOF, 오류선택 패널, 학습에 기소비된 공개 자료를 fresh holdout이라고 부르지 않는다.
4. **모르는 라벨은 모르는 상태로 남겨야 한다.** 음원의 REAL/FAKE 출처 proxy와 File/Voice/Music/event/presence 정답은 다르다. 부분위조의 파일 라벨을 모든 창에 복사하는 것도 잘못된 감독 신호가 될 수 있다.
5. **보존 실패는 제출을 멈출 충분한 이유였다.** C722는 공개 retention 악화가 이미 있었고 서버도 하락했다. 한 패널의 큰 이득으로 다른 패널의 손실을 가리는 선택은 위험했다.
6. **실행 무결성과 모델 성능을 별개로 기록해야 했다.** 경로 pin, FP32 연산 순서, historical baseline 혼동 같은 오류는 실제로 발견했다. 그러나 그것만으로 수백 번의 모든 실패를 코드 탓으로 돌릴 수 없다. 정정 후에도 전이 실패한 모델은 실패로 남겼다.
7. **자원 사용도 연구 설계의 일부였다.** 원 encoder 공유, cached prefix/CLS, 작은 head와 strict resume로 불필요한 반복을 줄였다. 긴 작업은 실제 시작·진행 증거와 실측 ETA를 확인한 뒤 자동 재개했고, 최종 종료 후에는 예약도 중지했다.
8. **대회 점수와 권리 문제를 분리해야 했다.** 목표 ADS 0.85는 달성하지 못했다. 자료·모델의 비영리 사용 허용이 코드 공개·가중치 재배포·수상 시 권리 이전을 자동으로 허용하지 않는다. 이 저장소는 그 권리를 새로 부여하지 않는다.

가장 중요한 개선점은 다음 프로젝트에서 먼저 고칠 프로세스다. 부모/출처 단위로 잠근 검증을 일찍 만들고, 처음부터 실제 제출 계산 경로를 평가하며, 구성요소별 라벨 범위를 명시하고, 새 후보의 이득·손실·자원·권리를 하나의 사전 기준으로 판단하는 것이다. 이것은 이번 미달 결과를 성공으로 바꾸는 설명이 아니라, 실패를 반복하지 않기 위한 기록이다.

## 부록 A. 보존된 C-번호 연구 기록 색인

2026-09-28 파일시스템 스냅샷에서 **656개 C-번호 / 704개 디렉터리**를 찾았다. 최고 번호는 C753다.
이는 완료한 학습 횟수가 아니다. 번호에는 설계, 자료 준비, 코드 감사, 특징 추출, 실패, 평가, 패키징도 포함된다. V1~V5 및 기타 이름의 초기 연구는 본문에서 별도로 다룬다.
아래 경로는 보존된 원 작업공간을 추적하기 위한 상대 경로이며, 대용량 원 기록 전체를 이 저장소에 업로드했다는 뜻이 아니다. JSON 색인에는 대표 기록의 크기와 SHA-256도 포함한다.

| 번호 | 보존된 연구/단계 디렉터리 | 대표 근거 파일(원 작업공간) |
|---|---|---|
| C56 | `research/c56_fourier_moe` | `research/c56_fourier_moe/C56_STOP_REPORT.md` |
| C63 | `research/c63_fourier_extratrees` | `research/c63_fourier_extratrees/C63_STOP_REPORT.md` |
| C89 | `research/c89_joint_fourier_lpc_head` | `research/c89_joint_fourier_lpc_head/C89_STOP_REPORT_2026-09-06.md` |
| C90 | `research/c90_r400_training_expansion_eval`<br>`research/c90_r400_training_expansion_smoke` | `research/c90_r400_training_expansion_eval/C90_R400_FAILURE_REPORT_2026-09-06.md`<br>`research/c90_r400_training_expansion_smoke/C90_R400_EIGHT_FILE_COST_RESULT.v0_1.json` |
| C91 | `research/c91_materialized_nonfourier_novelty_audit` | `research/c91_materialized_nonfourier_novelty_audit/C91_PHASE_SCALAR_C51_FEATURE_FAILURE_REPORT_2026-09-06.md` |
| C92 | `research/c92_joint_head_dev_probe` | `research/c92_joint_head_dev_probe/C92_STOP_REPORT_2026-09-06.md` |
| C93 | `research/c93_file_frontier_audit` | `research/c93_file_frontier_audit/C93_NEW_SIGNAL_RECOMMENDATION_2026-09-06.md` |
| C94 | `research/c94_c51_error_forensics` | `research/c94_c51_error_forensics/C94_C51_FILE_BOTTLENECK_REPORT_2026-09-06.md` |
| C95 | `research/c95_lbp_texture_early` | `research/c95_lbp_texture_early/C95_EARLY_RESULT.json` |
| C96 | `research/c96_lbp_c51_fusion`<br>`research/c96_lbp_dev_probe` | `research/c96_lbp_c51_fusion/C96_C51_LBP_SIX_FEATURE_FREEZE_2026-09-06.md`<br>`research/c96_lbp_dev_probe/C96_EARLY_STOP_REPORT_2026-09-06.md` |
| C97 | `research/c97_lbp_c51_runtime_probe`<br>`research/c97_lbp_fixed_ensemble` | `research/c97_lbp_c51_runtime_probe/C97_RUNTIME_PROXY_FAILURE_REPORT_2026-09-06.md`<br>`research/c97_lbp_fixed_ensemble/C97_DEV24_RESULT.json` |
| C98 | `research/c98_training_source_gap` | `research/c98_training_source_gap/C98_LOCAL_PROVIDER_COVERAGE_AUDIT_2026-09-06.md` |
| C99 | `research/c99_lbp_uncompressed_file` | `research/c99_lbp_uncompressed_file/C99_LBP_UNCOMPRESSED_FILE_FAILURE_REPORT_2026-09-06.md` |
| C100 | `research/c100_lbp_augmentation` | `research/c100_lbp_augmentation/C100_AUGMENTATION_RESULT.json` |
| C101 | `research/c101_augmented_lbp_dev`<br>`research/c101_augmented_lbp_runtime` | `research/c101_augmented_lbp_dev/C101_DEV200_LBP_CACHE.json`<br>`research/c101_augmented_lbp_runtime/C101_RUNTIME_PROXY_RESULT.v0_1.json` |
| C102 | `research/c102_augmented_lbp_uncompressed_file` | `research/c102_augmented_lbp_uncompressed_file/C102_C51_LBP_RESULT.v0_1.json` |
| C103 | `research/c103_c52_c58_score_audit` | `research/c103_c52_c58_score_audit/C103_C52_C58_IDENTICAL_SERVER_SCORE_AUDIT_2026-09-07.md` |
| C104 | `research/c104_c51_architecture_audit` | `research/c104_c51_architecture_audit/C104_C51_ARCHITECTURE_AUDIT_2026-09-07.md` |
| C105 | `research/c105_candidate_ensemble_diagnostic` | `research/c105_candidate_ensemble_diagnostic/C105_FIXED_MEAN_RESULT.v0_1.json` |
| C106 | `research/c106_public_panel_coverage` | `research/c106_public_panel_coverage/C106_PUBLIC_PANEL_COVERAGE.json` |
| C107 | `research/c107_validation_extension_sources` | `research/c107_validation_extension_sources/ACQUISITION_FREEZE.v1.json` |
| C108 | `research/c108_c58_matched_refit` | `research/c108_c58_matched_refit/C108_RESULT.v0_1.json` |
| C109 | `research/c109_shared_music_runtime` | `research/c109_shared_music_runtime/C109_ONE_FILE_RECEIPT.json` |
| C110 | `research/c110_voice_cpu_smoke` | `research/c110_voice_cpu_smoke/C110_ONE_VOICE_RESULT.json` |
| C111 | `research/c111_public_duration_codec_stress` | `research/c111_public_duration_codec_stress/C111_MATERIALIZATION_RESULT_2026-09-07.md` |
| C112 | `research/c112_temporal_duplicate_audit` | `research/c112_temporal_duplicate_audit/C112_TEMPORAL_DUPLICATE_AUDIT_2026-09-07.md` |
| C113 | `research/c113_novel_music_scores` | `research/c113_novel_music_scores/C113_MUSIC_1.json` |
| C114 | `research/c114_partial_label_feasibility` | `research/c114_partial_label_feasibility/C114_FOLD0_RESULT.json` |
| C115 | `research/c115_fma_new_real_sources` | `research/c115_fma_new_real_sources/C115_SOURCE_RESULT_2026-09-07.md` |
| C116 | `research/c116_probability_pool` | `research/c116_probability_pool/C116_RESULT.json` |
| C117 | `research/c117_fma_validation_audio` | `research/c117_fma_validation_audio/C117_MATERIALIZATION_RESULT_2026-09-07.md` |
| C118 | `research/c118_partial_lbp` | `research/c118_partial_lbp/C118_FOLD0_RESULT.json` |
| C119 | `research/c119_fresh_probability_pool` | `research/c119_fresh_probability_pool/C119_FRESH_RESULT_2026-09-07.md` |
| C120 | `research/c120_local_one_second_lbp` | `research/c120_local_one_second_lbp/C120_FOLD0_RESULT.json` |
| C121 | `research/c121_music_arena_training_feasibility` | `research/c121_music_arena_training_feasibility/C121_RAW_AUDIO_ACQUISITION_RESULT_2026-09-07.md` |
| C122 | `research/c122_music_arena_source_expansion` | `research/c122_music_arena_source_expansion/C122_FIRST_FOLD_REPORT_2026-09-07.md` |
| C123 | `research/c123_source_expansion_diagnostic` | `research/c123_source_expansion_diagnostic/C123_DIAGNOSTIC_REPORT_2026-09-07.md` |
| C124 | `research/c124_voice_bottleneck` | `research/c124_voice_bottleneck/C124_EXISTING_EVIDENCE_SUMMARY.json` |
| C125 | `research/c125_lpc_source_expansion` | `research/c125_lpc_source_expansion/C125_RESULT.json` |
| C126 | `research/c126_c51_source_expanded_lbp` | `research/c126_c51_source_expanded_lbp/C126_C51_LBP_RESULT.v0_1.json` |
| C127 | `research/c127_c51_direct_deezer` | `research/c127_c51_direct_deezer/C127_C51_DEEZER_RESULT.v0_1.json` |
| C128 | `research/c128_deezer128_source_probe` | `research/c128_deezer128_source_probe/C128_FIRST_FOLD_REPORT_2026-09-07.md` |
| C129 | `research/c129_deezer128_novel_diagnostic` | `research/c129_deezer128_novel_diagnostic/C129_DIAGNOSTIC_REPORT_2026-09-07.md` |
| C130 | `research/c130_deezer128_c51_fusion` | `research/c130_deezer128_c51_fusion/C130_RESULT_REPORT_2026-09-07.md` |
| C131 | `research/c131_equal_external_music_ensemble` | `research/c131_equal_external_music_ensemble/C131_FAILURE_REPORT_2026-09-07.md` |
| C132 | `research/c132_c51_deezer128_fixed_music_novel` | `research/c132_c51_deezer128_fixed_music_novel/C132_RESULT_REPORT_2026-09-07.md` |
| C133 | `research/c133_source_gap_feasibility` | `research/c133_source_gap_feasibility/C133_LOCAL_METADATA_RESULT.json` |
| C134 | `research/c134_eer_first_independent_file` | `research/c134_eer_first_independent_file/C134_RESULT_REPORT_2026-09-07.md` |
| C135 | `research/c135_real_only_deezer` | `research/c135_real_only_deezer/C135_EER_FIRST_REPORT_2026-09-07.md` |
| C136 | `research/c136_source_resolution` | `research/c136_source_resolution/C136_HOLD_REASON_CLARIFICATION_2026-09-08.md` |
| C137 | `research/c137_independent_kernel_music` | `research/c137_independent_kernel_music/C137_RESULT_REPORT_2026-09-07.md` |
| C138 | `research/c138_musan_deezer_source_repair` | `research/c138_musan_deezer_source_repair/C138_EER_FIRST_REPORT_2026-09-07.md` |
| C139 | `research/c139_exact_fourier_fast_hull` | `research/c139_exact_fourier_fast_hull/C139_RESULT.json` |
| C140 | `research/c140_c71_protocol_and_bootstrap` | `research/c140_c71_protocol_and_bootstrap/C140_PROTOCOL_AND_RISK_REPORT_2026-09-07.md` |
| C141 | `research/c141_c71_runtime_parity` | `research/c141_c71_runtime_parity/C141_PARITY_REPORT_2026-09-07.md` |
| C142 | `research/c142_clean_e2e_launcher` | `research/c142_clean_e2e_launcher/C142_ACTUAL_SERIAL_E2E_2026-09-07.md` |
| C143 | `research/c143_c71_novel_music_event` | `research/c143_c71_novel_music_event/C143_RESULT.json` |
| C144 | `research/c144_c71_final_zip_audit` | `research/c144_c71_final_zip_audit/C144_RESULT.json` |
| C145 | `research/c145_fresh_model_search` | `research/c145_fresh_model_search/C145_FRESH_MODEL_SEARCH_2026-09-08.md` |
| C146 | `research/c146_mixed_component_sources` | `research/c146_mixed_component_sources/C146_SOURCE_DESIGN_2026-09-08.md` |
| C147 | `research/c147_full_file_probe_plan` | `research/c147_full_file_probe_plan/C147_MINIMAL_FULL_FILE_PLAN_2026-09-08.md` |
| C148 | `research/c148_deezer_channel_training` | `research/c148_deezer_channel_training/C148_RESULT_REPORT_2026-09-08.md` |
| C149 | `research/c149_full_file_factorial_probe` | `research/c149_full_file_factorial_probe/C149_ACTUAL_FILE_RESULT_2026-09-08.md` |
| C150 | `research/c150_helmholtz_smoke` | `research/c150_helmholtz_smoke/C150_RAW768_1_RESULT.json` |
| C151 | `research/c151_dasheng_music_training` | `research/c151_dasheng_music_training/C151_RESULT_REPORT_2026-09-08.md` |
| C152 | `research/c152_published_head_raw_variant` | `research/c152_published_head_raw_variant/C152_EARLY_RESULT_STOP_2026-09-08.md` |
| C153 | `research/c153_paired_music_invariance` | `research/c153_paired_music_invariance/C153_RESULT_REPORT_2026-09-08.md` |
| C154 | `research/c154_official_rights_comparison` | `research/c154_official_rights_comparison/ROOT_MUSICGEN_RESEARCH_DECISION_2026-09-08.md` |
| C155 | `research/c155_fixed_probability_complement` | `research/c155_fixed_probability_complement/C155_RESULT.json` |
| C156 | `research/c156_musicgen_source_feasibility` | `research/c156_musicgen_source_feasibility/AIME_SURVEY_SOURCE_PROMPT_CROSSWALK.json` |
| C157 | `research/c157_music_presence_window` | `research/c157_music_presence_window/C157_RESULT.json` |
| C159 | `research/c159_general_music_window`<br>`research/c159_submission` | `research/c159_general_music_window/C159_RESULT_AND_RUNTIME_HANDOFF_2026-09-08.md`<br>`research/c159_submission/C159_ACTUAL_SERIAL_PREFLIGHT_2026-09-08.md` |
| C160 | `research/c160_file_scale_transfer` | `research/c160_file_scale_transfer/C160_VOICE_TO_FILE_SCALE_AUDIT_2026-09-08.md` |
| C161 | `research/c161_conditional_voice_calibration` | `research/c161_conditional_voice_calibration/C161_FAILURE_REPORT_2026-09-08.md` |
| C162 | `research/c162_musicgen_crosswalk` | `research/c162_musicgen_crosswalk/AIME_PINNED_PARQUET_TREE.json` |
| C163 | `research/c163_c159_failure_forensics` | `research/c163_c159_failure_forensics/C163_C159_SOURCE_CONFOUNDING_2026-09-08.md` |
| C164 | `research/c164_lowlevel_training_feasibility` | `research/c164_lowlevel_training_feasibility/C164_SINGLE_NEXT_EXPERIMENT_2026-09-08.md` |
| C165 | `research/c165_deezer_tail_smoke` | `research/c165_deezer_tail_smoke/C165_RESULT_AND_API_2026-09-08.md` |
| C166 | `research/c166_deezer_tail_control` | `research/c166_deezer_tail_control/C166_RESULT_AND_REUSE_2026-09-08.md` |
| C167 | `research/c167_musicgen_source_expansion` | `research/c167_musicgen_source_expansion/C167_FULL80_RESULT_2026-09-08.md` |
| C168 | `research/c168_musicgen_training_views` | `research/c168_musicgen_training_views/C168_ACTUAL_AUDIO_MANIFEST.json` |
| C169 | `research/c169_deezer_musicgen_tail` | `research/c169_deezer_musicgen_tail/C169_RESULT_AND_HANDOFF_2026-09-08.md` |
| C171 | `research/c171_deezer_segment_readout` | `research/c171_deezer_segment_readout/C171_C166_RESULT.json` |
| C172 | `research/c172_fourier_source_expansion_feasibility` | `research/c172_fourier_source_expansion_feasibility/C172_FEASIBILITY_RESULT.json` |
| C173 | `research/c173_voice_nuisance_diagnostic` | `research/c173_voice_nuisance_diagnostic/C173_RESULT.json` |
| C174 | `research/c174_joint_musicgen_training` | `research/c174_joint_musicgen_training/C174_RESULT_AND_LIMITATIONS_2026-09-08.md` |
| C175 | `research/c175_volume_control_voice_probe` | `research/c175_volume_control_voice_probe/C175_CONTROLLED_RESULT_2026-09-08.md` |
| C176 | `research/c176_kokoro_nuisance_feasibility` | `research/c176_kokoro_nuisance_feasibility/C176_FEASIBILITY_AND_BOUNDARY_2026-09-08.md` |
| C177 | `research/c177_kokoro_music_nuisance` | `research/c177_kokoro_music_nuisance/C177_ACTUAL_GENERATION_RESULT_2026-09-08.md` |
| C178 | `research/c178_c169_c174_fixed_mean` | `research/c178_c169_c174_fixed_mean/C178_RESULT.json` |
| C179 | `research/c179_fakevoice_music_views` | `research/c179_fakevoice_music_views/C179_MATERIALIZATION_RESULT_2026-09-08.md` |
| C180 | `research/c180_deezer_fakevoice_invariance` | `research/c180_deezer_fakevoice_invariance/C180_RESULT_AND_HANDOFF_2026-09-08.md` |
| C181 | `research/c181_component_input_probe` | `research/c181_component_input_probe/C181_RESULT.json` |
| C182 | `research/c182_c180_fixed_complement` | `research/c182_c180_fixed_complement/C182_RESULT.json` |
| C183 | `research/c183_c51_submission_lineage` | `research/c183_c51_submission_lineage/C183_ASSET_LINEAGE.json` |
| C184 | `research/c184_c51_public_strengths` | `research/c184_c51_public_strengths/C184_RESULT.json` |
| C185 | `research/c185_strength_hypotheses` | `research/c185_strength_hypotheses/C185_C51_STRENGTHS_AND_REPEAT_BOUNDARIES_2026-09-08.md` |
| C186 | `research/c186_c51_deezer_expert_swap` | `research/c186_c51_deezer_expert_swap/C186_EXTENSION80_RESULT.json` |
| C187 | `research/c187_c51_expert_ablation` | `research/c187_c51_expert_ablation/C187_RESULT_AND_LIMITATIONS_2026-09-08.md` |
| C188 | `research/c188_c51_controlled_nuisance` | `research/c188_c51_controlled_nuisance/C188_RESULT_AND_LIMITATIONS_2026-09-08.md` |
| C189 | `research/c189_c186_oof_transfer` | `research/c189_c186_oof_transfer/C189_RESULT.json` |
| C190 | `research/c190_c186_submission_probe` | `research/c190_c186_submission_probe/C190_COMPATIBILITY_RESULT.json` |
| C191 | `research/c191_temporal_expert_routing` | `research/c191_temporal_expert_routing/C191_FIXED_ROUTING_RESULT_2026-09-08.md` |
| C192 | `research/c192_layout_oracle_diagnostic` | `research/c192_layout_oracle_diagnostic/C192_ORACLE_RESULT.json` |
| C193 | `research/c193_conditional_expert_calibration` | `research/c193_conditional_expert_calibration/C193_RESULT.json` |
| C194 | `research/c194_c190_server_evidence` | `research/c194_c190_server_evidence/C194_DURATION_LAYOUT_MINIPANEL_PLAN.md` |
| C195 | `research/c195_c190_music_error_map` | `research/c195_c190_music_error_map/C195_RESULT.json` |
| C196 | `research/c196_component_training_feasibility` | `research/c196_component_training_feasibility/C196_ACTUAL_STEM_1_RESULT.json` |
| C197 | `research/c197_component_held32_evaluation`<br>`research/c197_matched_stem_tail` | `research/c197_component_held32_evaluation/C197_HELD32_REPORT_2026-09-08.md`<br>`research/c197_matched_stem_tail/C197_RESULT.json` |
| C198 | `research/c198_duration_layout_crossed_panel` | `research/c198_duration_layout_crossed_panel/C198_ACTUAL48_HANDOFF.md` |
| C199 | `research/c199_local_music_training_design` | `research/c199_local_music_training_design/C199_TIME_GEOMETRY_AND_LOCAL_LABEL_DESIGN_2026-09-08.md` |
| C200 | `research/c200_crossed_music_inference` | `research/c200_crossed_music_inference/C200_RESULT_AND_REUSE_2026-09-08.md` |
| C202 | `research/c202_deezer_dense_coverage` | `research/c202_deezer_dense_coverage/C202_INITIAL_RESULT_2026-09-08.md` |
| C204 | `research/c204_small_raw_expert_transfer` | `research/c204_small_raw_expert_transfer/C204_RESULT_1.json` |
| C205 | `research/c205_c180_continued_tail` | `research/c205_c180_continued_tail/C205_RESULT_2026-09-08.md` |
| C206 | `research/c206_direct_deezer_duplicate_review` | `research/c206_direct_deezer_duplicate_review/C206_PRIOR_DIRECT_DEEZER_FILE_EVIDENCE_2026-09-08.md` |
| C207 | `research/c207_continued_deezer_file_head` | `research/c207_continued_deezer_file_head/C207_MATCHED_HEAD_RESULT_2026-09-08.md` |
| C208 | `research/c208_continued_expert_transfer` | `research/c208_continued_expert_transfer/C208_RESULT_1.json` |
| C209 | `research/c209_dasheng_internal_expert` | `research/c209_dasheng_internal_expert/C209_RESULT_AND_ROLE_DIFFERENCE_2026-09-08.md` |
| C210 | `research/c210_deezer_fixed_dual_expert` | `research/c210_deezer_fixed_dual_expert/C210_RESULT_AND_LIMITATIONS_2026-09-08.md` |
| C211 | `research/c211_full_backbone_finetune` | `research/c211_full_backbone_finetune/C211_FIRST_TWO_RESULT.json` |
| C212 | `research/c212_internal_dual_expert_combination` | `research/c212_internal_dual_expert_combination/C212_RESULT_AND_TRADEOFF_2026-09-08.md` |
| C213 | `research/c213_full_backbone_transfer` | `research/c213_full_backbone_transfer/C213_RESULT_1.json` |
| C214 | `research/c214_c212_submission` | `research/c214_c212_submission/C214_ACTUAL8_PARITY_RESULT.json` |
| C215 | `research/c215_file_bottleneck` | `research/c215_file_bottleneck/C215_RESULT.json` |
| C216 | `research/c216_voice_model_feasibility` | `research/c216_voice_model_feasibility/C216_VOICE_SCOUT_2026-09-09.md` |
| C217 | `research/c217_local_music_label_design` | `research/c217_local_music_label_design/C217_LOCAL_MUSIC_LABEL_DESIGN_2026-09-09.md` |
| C218 | `research/c218_temporal_dasheng` | `research/c218_temporal_dasheng/C218_INITIAL_RESULTS_2026-09-09.md` |
| C220 | `research/c220_telephone_music_expert_feasibility` | `research/c220_telephone_music_expert_feasibility/C220_FEASIBILITY_RESULT.json` |
| C221 | `research/c221_c218_crossed_transfer` | `research/c221_c218_crossed_transfer/C221_REPORT_2026-09-09.md` |
| C222 | `research/c222_masked_music_training` | `research/c222_masked_music_training/C222_RESULT_AND_STOP_2026-09-09.md` |
| C223 | `research/c223_phone_fourier_training` | `research/c223_phone_fourier_training/C223_RESULT.json` |
| C224 | `research/c224_temporal_file_only` | `research/c224_temporal_file_only/C224_PUBLIC_EVIDENCE.json` |
| C225 | `research/c225_dasheng_window_batch` | `research/c225_dasheng_window_batch/C225_FREEZE_2026-09-09.md` |
| C226 | `research/c226_pairwise_tail` | `research/c226_pairwise_tail/C226_RESULT.json` |
| C227 | `research/c227_rank_expert_transfer` | `research/c227_rank_expert_transfer/C227_TRANSFER_FREEZE_2026-09-09.md` |
| C228 | `research/c228_global_pairwise_tail` | `research/c228_global_pairwise_tail/C228_RESULT.json` |
| C229 | `research/c229_deezer_gain_audit` | `research/c229_deezer_gain_audit/C229_RESULT_AND_STOP_2026-09-09.md` |
| C230 | `research/c230_independent_music_forensics_scout` | `research/c230_independent_music_forensics_scout/C230_ASSET_PROPOSAL.json` |
| C231 | `research/c231_fourier_input_audit` | `research/c231_fourier_input_audit/C231_AUDIT_AND_RESULT_2026-09-09.md` |
| C232 | `research/c232_raw_voice_file_rescue` | `research/c232_raw_voice_file_rescue/C232_RESULT.json` |
| C233 | `research/c233_raw_voice_factorial` | `research/c233_raw_voice_factorial/C233_ACTUAL16_RESULT_2026-09-09.md` |
| C234 | `research/c234_dac16_first_signal` | `research/c234_dac16_first_signal/C234_RESULT.json` |
| C235 | `research/c235_component_branch_complement` | `research/c235_component_branch_complement/C235_RESULT_AND_DECISION_2026-09-09.md` |
| C236 | `research/c236_additional_file_panel` | `research/c236_additional_file_panel/C236_INVENTORY_RESULT.json` |
| C237 | `research/c237_raw_voice_submission_probe` | `research/c237_raw_voice_submission_probe/c237_overlay.py` |
| C238 | `research/c238_dac16_authenticity_first_signal` | `research/c238_dac16_authenticity_first_signal/C238_FAILURE_REPORT_2026-09-09.md` |
| C239 | `research/c239_deezer_presence_pool` | `research/c239_deezer_presence_pool/C239_RESULT.json` |
| C240 | `research/c240_c239_runtime_smoke` | `research/c240_c239_runtime_smoke/C240_ACTUAL_RESULT_8.json` |
| C241 | `research/c241_submission` | `research/c241_submission/C241_DECISION_AND_FREEZE.md` |
| C242 | `research/c242_c241_bottleneck` | `research/c242_c241_bottleneck/C242_RESULT.json` |
| C243 | `research/c243_independent_music_candidate` | `research/c243_independent_music_candidate/C243_ASSET_PROPOSAL.json` |
| C244 | `research/c244_deezer_generalization_plan` | `research/c244_deezer_generalization_plan/C244_CACHED_PAIR_DIAGNOSTIC.json` |
| C245 | `research/c245_dac_token_probe` | `research/c245_dac_token_probe/C245_FAILURE_REPORT_2026-09-09.md` |
| C246 | `research/c246_deezer_paired_consistency` | `research/c246_deezer_paired_consistency/C246_RESULT.json` |
| C247 | `research/c247_muq_first_signal` | `research/c247_muq_first_signal/C247_RESULT.json` |
| C248 | `research/c248_presence_confound_ablation` | `research/c248_presence_confound_ablation/C248_RESULT_AND_RECOVERY_2026-09-09.md` |
| C249 | `research/c249_paired_expert_transfer` | `research/c249_paired_expert_transfer/C249_RESULT_AND_STOP_2026-09-09.md` |
| C250 | `research/c250_provider_balanced_deezer` | `research/c250_provider_balanced_deezer/C250_RESULT.json` |
| C251 | `research/c251_muq_source_expansion` | `research/c251_muq_source_expansion/C251_RESULT.json` |
| C252 | `research/c252_dual_view_sonics` | `research/c252_dual_view_sonics/C252_RESULT_AND_STOP_2026-09-09.md` |
| C253 | `research/c253_muq_independent_file_feasibility` | `research/c253_muq_independent_file_feasibility/C253_READ_ONLY_FEASIBILITY_2026-09-09.md` |
| C254 | `research/c254_broader_music_transfer` | `research/c254_broader_music_transfer/C254_INPUT_PANEL_RESULT_2026-09-09.md` |
| C255 | `research/c255_muq_direct_file_head` | `research/c255_muq_direct_file_head/C255_RESULT_AND_HANDOFF_2026-09-09.md` |
| C256 | `research/c256_voice_conditioned_sonics` | `research/c256_voice_conditioned_sonics/C256_CROSS48_RESULT.json` |
| C257 | `research/c257_broader_music_baseline` | `research/c257_broader_music_baseline/C257_RESULT_AND_REUSE_2026-09-09.md` |
| C258 | `research/c258_muq_public_transfer` | `research/c258_muq_public_transfer/C258_RESULT_1.json` |
| C259 | `research/c259_anyfake_boundary_supervision` | `research/c259_anyfake_boundary_supervision/C259_RESULT_AND_STOP_2026-09-09.md` |
| C260 | `research/c260_music_weighted_spectrum` | `research/c260_music_weighted_spectrum/C260_RESULT_AND_STOP_2026-09-09.md` |
| C261 | `research/c261_lofcz_fakeprint_probe` | `research/c261_lofcz_fakeprint_probe/C261_FIRST_SIGNAL_REPORT_2026-09-09.md` |
| C262 | `research/c262_lofcz_cnn_probe` | `research/c262_lofcz_cnn_probe/C262_FIRST_RESULT_AND_LIMITS_2026-09-09.md` |
| C263 | `research/c263_official_minfilter_music_head` | `research/c263_official_minfilter_music_head/C263_FIRST1_RESULT.json` |
| C264 | `research/c264_cnn_classical_slot` | `research/c264_cnn_classical_slot/C264_NEW128_RESULT.json` |
| C265 | `research/c265_muq_nonlinear_head_design` | `research/c265_muq_nonlinear_head_design/C265_RESULT_AND_FAILURE_NOTE_2026-09-09.md` |
| C266 | `research/c266_muq_classical_slot` | `research/c266_muq_classical_slot/C266_RESULT_AND_STOP_2026-09-09.md` |
| C267 | `research/c267_muq_train_only_regularization` | `research/c267_muq_train_only_regularization/C267_RESULT.json` |
| C268 | `research/c268_sonics_tail_smoke` | `research/c268_sonics_tail_smoke/C268_RESULT.json` |
| C269 | `research/c269_sonics_raw_tail_adaptation` | `research/c269_sonics_raw_tail_adaptation/C269_FIRST_HELD_RESULT_AND_HANDOFF_2026-09-09.md` |
| C270 | `research/c270_sonics5_geometry_scout` | `research/c270_sonics5_geometry_scout/C270_ACTUAL_RESULT_AND_FAILURE_NOTE_2026-09-09.md` |
| C271 | `research/c271_training_coverage_inventory` | `research/c271_training_coverage_inventory/C271_READ_ONLY_RESULT_2026-09-09.md` |
| C272 | `research/c272_adapted_raw_sonics_transfer` | `research/c272_adapted_raw_sonics_transfer/C272_RESULT_AND_STOP_2026-09-09.md` |
| C273 | `research/c273_music_arena_new32` | `research/c273_music_arena_new32/C273_RESULT_AND_ATTRIBUTION_2026-09-09.md` |
| C274 | `research/c274_deezer_last_two_blocks` | `research/c274_deezer_last_two_blocks/C274_RESULT_AND_FAILURE_NOTE_2026-09-09.md` |
| C275 | `research/c275_training_time_coverage` | `research/c275_training_time_coverage/C275_ACTUAL_AUDIO_1.json` |
| C276 | `research/c276_music_arena_expanded_tail` | `research/c276_music_arena_expanded_tail/C276_RESULT_AND_STOP_2026-09-09.md` |
| C277 | `research/c277_deezer_time_coverage` | `research/c277_deezer_time_coverage/C277_RESULT.json` |
| C278 | `research/c278_muq_kernel` | `research/c278_muq_kernel/C278_RESULT.json` |
| C279 | `research/c279_deezer_bag_loss` | `research/c279_deezer_bag_loss/C279_RESULT_AND_FAILURE_NOTE_2026-09-09.md` |
| C280 | `research/c280_sonics_short_no_padding` | `research/c280_sonics_short_no_padding/C280_RESULT_AND_STOP_2026-09-09.md` |
| C281 | `research/c281_independent_expert_review` | `research/c281_independent_expert_review/C281_READ_ONLY_REVIEW_2026-09-09.md` |
| C282 | `research/c282_input_representation_audit` | `research/c282_input_representation_audit/C282_READ_ONLY_AUDIT_2026-09-09.md` |
| C283 | `research/c283_musicdet_cpu_feasibility` | `research/c283_musicdet_cpu_feasibility/C283_READ_ONLY_FEASIBILITY_2026-09-09.md` |
| C284 | `research/c284_joint_deezer_muq` | `research/c284_joint_deezer_muq/C284_RESULT_AND_STOP_2026-09-09.md` |
| C285 | `research/c285_raw_spectral_residual_cnn` | `research/c285_raw_spectral_residual_cnn/C285_RESULT_AND_STOP_2026-09-09.md` |
| C286 | `research/c286_adapted_joint_embedding` | `research/c286_adapted_joint_embedding/C286_RESULT_AND_TRANSFER_2026-09-09.md` |
| C287 | `research/c287_musicdet_real_smoke` | `research/c287_musicdet_real_smoke/C287_ACTUAL_SMOKE_RESULT_2026-09-09.md` |
| C288 | `research/c288_codec_training_gap` | `research/c288_codec_training_gap/C288_AUDIT_AND_SINGLE_PROPOSAL_2026-09-09.md` |
| C289 | `research/c289_joint_public_transfer` | `research/c289_joint_public_transfer/C289_RESULT_AND_STOP_2026-09-09.md` |
| C290 | `research/c290_musicdet_real_fullfit` | `research/c290_musicdet_real_fullfit/C290_RESULT_AND_FAILURE_NOTE_2026-09-09.md` |
| C291 | `research/c291_deezer_lossy_codec_training` | `research/c291_deezer_lossy_codec_training/C291_RESULT_AND_FAILURE_2026-09-09.md` |
| C292 | `research/c292_stem_sonics_smoke` | `research/c292_stem_sonics_smoke/C292_RESULT_AND_NEXT_2026-09-09.md` |
| C293 | `research/c293_stem_training_pilot` | `research/c293_stem_training_pilot/C293_RESULT_AND_STOP_2026-09-09.md` |
| C294 | `research/c294_panns_current_sources` | `research/c294_panns_current_sources/C294_RESULT_AND_STOP_2026-09-09.md` |
| C295 | `research/c295_spectra_music_probe` | `research/c295_spectra_music_probe/C295_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C296 | `research/c296_forensic_rbf` | `research/c296_forensic_rbf/C296_RESULT_AND_STOP_2026-09-09.md` |
| C297 | `research/c297_sonics_full_encoder_pilot` | `research/c297_sonics_full_encoder_pilot/C297_RESULT_AND_STOP_2026-09-09.md` |
| C298 | `research/c298_fma_train_artist_expansion` | `research/c298_fma_train_artist_expansion/C298_RESULT_2026-09-09.md` |
| C299 | `research/c299_spectra_layer6_music` | `research/c299_spectra_layer6_music/C299_RESULT_AND_STOP_2026-09-09.md` |
| C300 | `research/c300_muq_layer6_probe` | `research/c300_muq_layer6_probe/C300_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C301 | `research/c301_fma_artist_mass_expansion` | `research/c301_fma_artist_mass_expansion/C301_RESULT_AND_FAILURE_2026-09-09.md` |
| C302 | `research/c302_new_generator_sources` | `research/c302_new_generator_sources/C302_EIGHT_LFS_EXAMPLES.json` |
| C303 | `research/c303_dasheng_current_sources` | `research/c303_dasheng_current_sources/C303_RESULT_AND_TRANSFER_2026-09-09.md` |
| C304 | `research/c304_dasheng_tail_pilot` | `research/c304_dasheng_tail_pilot/C304_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C305 | `research/c305_music_arena_ace8` | `research/c305_music_arena_ace8/C305_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C306 | `research/c306_dasheng_h_slot_transfer` | `research/c306_dasheng_h_slot_transfer/C306_RESULT_AND_COUNTEREXAMPLES_2026-09-09.md` |
| C307 | `research/c307_dasheng_full_tail_training` | `research/c307_dasheng_full_tail_training/C307_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C308 | `research/c308_ace_source_expansion` | `research/c308_ace_source_expansion/C308_ACQUISITION_COMPLETION_2026-09-09.md` |
| C309 | `research/c309_h_slot_influence` | `research/c309_h_slot_influence/C309_RESULT.json` |
| C310 | `research/c310_music_voice_snr` | `research/c310_music_voice_snr/C310_RESULT_AND_FAILURE_2026-09-09.md` |
| C311 | `research/c311_deezer_uniform_weight_soup` | `research/c311_deezer_uniform_weight_soup/C311_RESULT_AND_FAILURE_2026-09-09.md` |
| C312 | `research/c312_ace_generator_exposure` | `research/c312_ace_generator_exposure/C312_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C313 | `research/c313_group_dro_feasibility` | `research/c313_group_dro_feasibility/C313_TRAIN_RISK_RESULT.json` |
| C315 | `research/c315_ace_expert_transfer` | `research/c315_ace_expert_transfer/C315_RESULT_AND_NO_EER_GAIN_2026-09-09.md` |
| C316 | `research/c316_epochwise_group_risk` | `research/c316_epochwise_group_risk/C316_RESULT_AND_FAILURE_2026-09-09.md` |
| C317 | `research/c317_partial_music_mil_feasibility` | `research/c317_partial_music_mil_feasibility/C317_DUPLICATE_REVIEW_AND_MINIMUM_PROPOSAL.md` |
| C318 | `research/c318_fma_medium_artist_feasibility` | `research/c318_fma_medium_artist_feasibility/C318_METADATA_ACQUISITION.json` |
| C319 | `research/c319_uniform_probability_ensemble` | `research/c319_uniform_probability_ensemble/C319_RESULT_AND_FAILURE_2026-09-09.md` |
| C320 | `research/c320_train_only_nmf` | `research/c320_train_only_nmf/C320_RESULT_AND_FAILURE_2026-09-09.md` |
| C321 | `research/c321_partial_music_noisy_or` | `research/c321_partial_music_noisy_or/C321_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C322 | `research/c322_fma_medium_electronic17` | `research/c322_fma_medium_electronic17/C322_ACQUISITION_RESULT_AND_TRAIN_VALUE_2026-09-09.md` |
| C323 | `research/c323_deezer_full_backbone_duplicate_check` | `research/c323_deezer_full_backbone_duplicate_check/C323_PRIOR_ACTUAL_TRAINING_NOTE_2026-09-09.md` |
| C324 | `research/c324_partial_music_local_replay` | `research/c324_partial_music_local_replay/C324_RESULT_AND_TRADEOFFS_2026-09-09.md` |
| C325 | `research/c325_fma_scope_metadata` | `research/c325_fma_scope_metadata/C325_SCOPE_METADATA.json` |
| C326 | `research/c326_fma_large_diverse_source_plan` | `research/c326_fma_large_diverse_source_plan/C326_METADATA_INDEX_RESULT_2026-09-09.md` |
| C327 | `research/c327_mert_v1_standalone_feasibility` | `research/c327_mert_v1_standalone_feasibility/C327_READ_ONLY_FEASIBILITY_2026-09-09.md` |
| C328 | `research/c328_joint_deezer_fakeprint` | `research/c328_joint_deezer_fakeprint/C328_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C329 | `research/c329_mert_v1_first_signal` | `research/c329_mert_v1_first_signal/C329_RESULT_AND_FAILURE_2026-09-09.md` |
| C330 | `research/c330_diverse_real_training` | `research/c330_diverse_real_training/C330_RESULT_AND_LIMITS_2026-09-09.md` |
| C331 | `research/c331_c205_plus9_control` | `research/c331_c205_plus9_control/C331_RESULT_AND_CONTROL_LIMITS_2026-09-09.md` |
| C332 | `research/c332_partial_expert_transfer` | `research/c332_partial_expert_transfer/C332_RESULT_AND_LIMITATIONS_2026-09-09.md` |
| C333 | `research/c333_deezer_coverage_audit` | `research/c333_deezer_coverage_audit/C333_COVERAGE_AND_DUPLICATE_AUDIT_2026-09-09.md` |
| C334 | `research/c334_train_only_last_bn` | `research/c334_train_only_last_bn/C334_RESULT_AND_FAILURES_2026-09-09.md` |
| C335 | `research/c335_c241_dense_coverage` | `research/c335_c241_dense_coverage/C335_RESULT_AND_NO_GO_2026-09-09.md` |
| C336 | `research/c336_deezer_continuous_context` | `research/c336_deezer_continuous_context/C336_RESULT_AND_LIMITS_2026-09-09.md` |
| C337 | `research/c337_c205_preserving_deezer_slots` | `research/c337_c205_preserving_deezer_slots/C337_RESULT_AND_NO_STRONG_GAIN_2026-09-09.md` |
| C338 | `research/c338_dense_global_sparse_aligned` | `research/c338_dense_global_sparse_aligned/C338_RESULT_AND_STOP_2026-09-09.md` |
| C339 | `research/c339_deezer_continuous_tail_pilot` | `research/c339_deezer_continuous_tail_pilot/C339_RESULT_AND_STOP_2026-09-09.md` |
| C340 | `research/c340_checkpoint_relative_panel_feasibility` | `research/c340_checkpoint_relative_panel_feasibility/C340_FEASIBILITY_2026-09-09.md` |
| C342 | `research/c342_current_expert_simplex` | `research/c342_current_expert_simplex/C342_RESULT_AND_NO_GO_2026-09-09.md` |
| C343 | `research/c343_calibration_rights_scope` | `research/c343_calibration_rights_scope/C343_SCOPE_CONCLUSION_2026-09-09.md` |
| C344 | `research/c344_sam_tail_feasibility` | `research/c344_sam_tail_feasibility/C344_MATCHED_RESULT_AND_LIMITS_2026-09-09.md` |
| C345 | `research/c345_joint_features_hgb` | `research/c345_joint_features_hgb/C345_RESULT_AND_STOP_2026-09-09.md` |
| C346 | `research/c346_single_weight_transfer` | `research/c346_single_weight_transfer/C346_RESULT_AND_LIMITS_2026-09-09.md` |
| C347 | `research/c347_single_weight_extra80` | `research/c347_single_weight_extra80/C347_RESULT_AND_LIMITS_2026-09-09.md` |
| C348 | `research/c348_single_weight_runtime` | `research/c348_single_weight_runtime/ROOT_C349_MUSIC_ONLY_DECISION_2026-09-09.md` |
| C349 | `research/c349_c346_submission_stage` | `research/c349_c346_submission_stage/C349_MUSIC_ONLY_SCOPE_2026-09-09.md` |
| C350 | `research/c350_music_only_prebuild_review` | `research/c350_music_only_prebuild_review/C350_INDEPENDENT_REVIEW_2026-09-09.md` |
| C351 | `research/c351_current_expert_file_event` | `research/c351_current_expert_file_event/C351_RESULT_AND_NO_PROMOTION_2026-09-10.md` |
| C352 | `research/c352_voice_branch_review` | `research/c352_voice_branch_review/C352_RESULT_AND_BOUNDED_SCOUT_2026-09-10.md` |
| C353 | `research/c353_validation_coverage` | `research/c353_validation_coverage/C353_ADDITIONAL_FILE_CACHE_UPDATE_2026-09-10.md` |
| C354 | `research/c354_probability_pool` | `research/c354_probability_pool/C354_RESULT_AND_STOP_2026-09-10.md` |
| C355 | `research/c355_joint_logit_calibration` | `research/c355_joint_logit_calibration/C355_RESULT_AND_STOP_2026-09-10.md` |
| C356 | `research/c356_crossed8_full_file` | `research/c356_crossed8_full_file/C356_ACTUAL_FULL_FILE8_REPORT_2026-09-10.md` |
| C357 | `research/c357_joint_file_loss` | `research/c357_joint_file_loss/C357_RESULT_AND_STOP_2026-09-10.md` |
| C358 | `research/c358_channel_observability` | `research/c358_channel_observability/C358_CHANNEL_RESULT.json` |
| C359 | `research/c359_pella_frozen_probe` | `research/c359_pella_frozen_probe/C359_STEM16_RESULT_AND_NO_GO_2026-09-10.md` |
| C360 | `research/c360_signed_music_logit` | `research/c360_signed_music_logit/C360_RESULT_AND_STOP_2026-09-10.md` |
| C361 | `research/c361_linear_margin_music` | `research/c361_linear_margin_music/C361_RESULT_AND_STOP_2026-09-10.md` |
| C362 | `research/c362_singing_nes2net_checkpoint` | `research/c362_singing_nes2net_checkpoint/C362_FIRST1_RESULT_AND_NEXT_INPUT_PLAN_2026-09-10.md` |
| C363 | `research/c363_file_global_only` | `research/c363_file_global_only/C363_RESULT_AND_LIMITS_2026-09-10.md` |
| C364 | `research/c364_log_presence_event` | `research/c364_log_presence_event/C364_RESULT_AND_HANDOFF_2026-09-10.md` |
| C365 | `research/c365_ctrsvdd_test8` | `research/c365_ctrsvdd_test8/C365_ACQUISITION_RESULT.json` |
| C366 | `research/c366_ctrsvdd_voice_baseline` | `research/c366_ctrsvdd_voice_baseline/C366_FINAL8_BASELINE_REPORT_2026-09-10.md` |
| C367 | `research/c367_failed_file_path_audit` | `research/c367_failed_file_path_audit/C367_AUDIT_HARNESS_NOTE.md` |
| C368 | `research/c368_c159_implementation_audit` | `research/c368_c159_implementation_audit/C368_RESULT.json` |
| C369 | `research/c369_early_candidate_failure_audit` | `research/c369_early_candidate_failure_audit/C369_EARLY_CANDIDATE_FAILURE_AUDIT_2026-09-10.md` |
| C370 | `research/c370_c29_c51_retrospective` | `research/c370_c29_c51_retrospective/C370_C50_LATER_DUPLICATE_NOTE_2026-09-10.md` |
| C372 | `research/c372_ctrsvdd_additional32` | `research/c372_ctrsvdd_additional32/C372_NES32_RESULT_REPORT_2026-09-10.md` |
| C373 | `research/c373_server_change_evidence` | `research/c373_server_change_evidence/C373_AGGREGATE_DELTAS.json` |
| C374 | `research/c374_nes_voice_event` | `research/c374_nes_voice_event/C374_FIRST8_RESULT_AND_HANDOFF_2026-09-10.md` |
| C376 | `research/c376_nes_voice_window` | `research/c376_nes_voice_window/C376_SELECTED200_RESULT_AND_HANDOFF_2026-09-10.md` |
| C377 | `research/c377_nes_singing_mix_stress` | `research/c377_nes_singing_mix_stress/C377_RESULT_REPORT_2026-09-10.md` |
| C378 | `research/c378_voice_presence_normalized_max` | `research/c378_voice_presence_normalized_max/RESULT_AND_FAILURE_2026-09-10.md` |
| C379 | `research/c379_mixed_singing_baseline` | `research/c379_mixed_singing_baseline/C379_df_RESULT_1.json` |
| C380 | `research/c380_nes_raw_mix8` | `research/c380_nes_raw_mix8/C380_RESULT_REPORT_2026-09-10.md` |
| C381 | `research/c381_joint_voice_event` | `research/c381_joint_voice_event/C381_FINAL_TRANSFER16_REPORT_2026-09-10.md` |
| C382 | `research/c382_nes_two_window_coverage` | `research/c382_nes_two_window_coverage/C382_TWO_WINDOW_SCORE_RESULT.json` |
| C383 | `research/c383_joint_voice_music_event` | `research/c383_joint_voice_music_event/C383_RESULT_REPORT_2026-09-10.md` |
| C384 | `research/c384_voice_context_music` | `research/c384_voice_context_music/RESULT_AND_STOP_2026-09-10.md` |
| C385 | `research/c385_c349_dense_music_only` | `research/c385_c349_dense_music_only/RESULT_AND_STOP_2026-09-10.md` |
| C386 | `research/c386_joint_voice_bag` | `research/c386_joint_voice_bag/C386_RESULT_REPORT_2026-09-10.md` |
| C387 | `research/c387_direct_joint_component_file` | `research/c387_direct_joint_component_file/C387_RESULT_REPORT_2026-09-10.md` |
| C388 | `research/c388_conditional_voice_bag` | `research/c388_conditional_voice_bag/RESULT_AND_STOP_2026-09-10.md` |
| C389 | `research/c389_nes_penultimate` | `research/c389_nes_penultimate/C389_FIRST8_TECHNICAL_REPORT_2026-09-10.md` |
| C390 | `research/c390_v7_speech_revisit` | `research/c390_v7_speech_revisit/C390_RAW40_RESULT_AND_HANDOFF_2026-09-10.md` |
| C391 | `research/c391_nes_embedding_voice_event` | `research/c391_nes_embedding_voice_event/TRANSFER_RESULT_AND_HOLD_2026-09-10.md` |
| C392 | `research/c392_logit_contrast` | `research/c392_logit_contrast/C392_REPORT_2026-09-10.md` |
| C393 | `research/c393_new_music_asset_search` | `research/c393_new_music_asset_search/C393_NEW_MUSIC_ASSET_SEARCH_2026-09-10.md` |
| C394 | `research/c394_same_window_voice_agreement` | `research/c394_same_window_voice_agreement/RESULT_AND_STOP_2026-09-10.md` |
| C395 | `research/c395_mixed_stem8` | `research/c395_mixed_stem8/C395_RESULT_AND_HANDOFF_2026-09-10.md` |
| C396 | `research/c396_pella_mixed8` | `research/c396_pella_mixed8/C396_RESULT_AND_HANDOFF_2026-09-10.md` |
| C397 | `research/c397_deezer_lowband_input` | `research/c397_deezer_lowband_input/C397_ACTUAL_RESULT_2026-09-10.md` |
| C398 | `research/c398_cpu4_readonly_first1` | `research/c398_cpu4_readonly_first1/C398_ACTUAL_RESULT_2026-09-10.md` |
| C399 | `research/c399_joint_event_regularization` | `research/c399_joint_event_regularization/RESULT_AND_STOP_2026-09-10.md` |
| C400 | `research/c400_pella_public200` | `research/c400_pella_public200/C400_RESULT_AND_HANDOFF_2026-09-10.md` |
| C401 | `research/c401_pella_joint_file` | `research/c401_pella_joint_file/RESULT_AND_STOP_2026-09-10.md` |
| C402 | `research/c402_pella_conditional_voice` | `research/c402_pella_conditional_voice/RESULT_AND_LIMITS_2026-09-10.md` |
| C403 | `research/c403_pella_channel_observability` | `research/c403_pella_channel_observability/C403_CACHE_REVIEW_2026-09-10.md` |
| C404 | `research/c404_fixed_input_gated_lowband` | `research/c404_fixed_input_gated_lowband/C404_C349_APPROXIMATE_RESULT.json` |
| C405 | `research/c405_temporal_joint_file_review` | `research/c405_temporal_joint_file_review/C405_FIXED_INPUT_REVIEW_2026-09-10.md` |
| C406 | `research/c406_pella_temporal_coverage` | `research/c406_pella_temporal_coverage/C406_FIRST8_RESULT_AND_LIMITS_2026-09-10.md` |
| C407 | `research/c407_temporal_joint_file` | `research/c407_temporal_joint_file/RESULT_AND_HOLD_2026-09-10.md` |
| C408 | `research/c408_symmetric_gated_lowband` | `research/c408_symmetric_gated_lowband/C408_TRANSFER24_REPORT_2026-09-10.md` |
| C409 | `research/c409_c356_nes_transfer` | `research/c409_c356_nes_transfer/C409_ACTUAL_FILE8_REPORT_2026-09-10.md` |
| C410 | `research/c410_file_soft_error` | `research/c410_file_soft_error/C410_ACTUAL16_RESULT.json` |
| C411 | `research/c411_fixed_objective_ensemble` | `research/c411_fixed_objective_ensemble/C411_RESULT.json` |
| C412 | `research/c412_pairwise_joint_file` | `research/c412_pairwise_joint_file/C412_RESULT_REPORT_2026-09-10.md` |
| C413 | `research/c413_joint_file_submission` | `research/c413_joint_file_submission/C413_CURRENT_STAGE.json` |
| C414 | `research/c414_adversarial_full_training`<br>`research/c414_training_pilot_design` | `research/c414_adversarial_full_training/C414_RESULT_AND_FAILURE_2026-09-10.md`<br>`research/c414_training_pilot_design/POST_C414_PAIRED_DAC_DECISION_2026-09-10.md` |
| C415 | `research/c415_paired_decoder_tcn` | `research/c415_paired_decoder_tcn/C415_RESULT_AND_FAILURE_2026-09-10.md` |
| C416 | `research/c416_deezer_ocsoftmax` | `research/c416_deezer_ocsoftmax/C416_RESULT_AND_NEXT_2026-09-10.md` |
| C417 | `research/c417_sonics_file_training` | `research/c417_sonics_file_training/C417_RESULT_AND_LIMITS_2026-09-10.md` |
| C418 | `research/c418_c417_file_transfer` | `research/c418_c417_file_transfer/C418_RESULT_AND_FAILURE_2026-09-10.md` |
| C419 | `research/c419_pocket_stock_voice` | `research/c419_pocket_stock_voice/C419_FIRST1_RESULT.json` |
| C420 | `research/c420_file_voice_data_design` | `research/c420_file_voice_data_design/C420_DESIGN_NOTE_2026-09-10.md` |
| C421 | `research/c421_aasist_training_pilot` | `research/c421_aasist_training_pilot/C421_RESULT.json` |
| C422 | `research/c422_aasist_pocket_adaptation` | `research/c422_aasist_pocket_adaptation/C422_RESULT_AND_LIMITS_2026-09-10.md` |
| C423 | `research/c423_aasist_cross_generator_probe` | `research/c423_aasist_cross_generator_probe/C423_RESULT_AND_FAILURE_2026-09-10.md` |
| C424 | `research/c424_wav2vec_base_training` | `research/c424_wav2vec_base_training/C424_RESULT.json` |
| C425 | `research/c425_asvspoof_multigenerator` | `research/c425_asvspoof_multigenerator/C425_CACHED_METADATA_RESULT.json` |
| C426 | `research/c426_wav2vec_multigenerator_training` | `research/c426_wav2vec_multigenerator_training/C426_DEV240_STEP512_RESULT.json` |
| C427 | `research/c427_wav2vec_external_probe` | `research/c427_wav2vec_external_probe/C427_RESULTS_AND_C426_CONTINUATION_2026-09-10.md` |
| C428 | `research/c428_wav2vec_full_external` | `research/c428_wav2vec_full_external/C428_RESULT_AND_NEXT_DATA_2026-09-11.md` |
| C429 | `research/c429_mlaad_training_data` | `research/c429_mlaad_training_data/C429_SELECTION_DECISION_2026-09-11.md` |
| C430 | `research/c430_wav2vec_expanded_training` | `research/c430_wav2vec_expanded_training/C430_DEV_STEP512_RESULT.json` |
| C431 | `research/c431_wav2vec_expanded_external` | `research/c431_wav2vec_expanded_external/C431_RESULT_1.json` |
| C432 | `research/c432_c426_on_mlaad_dev` | `research/c432_c426_on_mlaad_dev/C432_RESULT_1.json` |
| C433 | `research/c433_c430_final_external` | `research/c433_c430_final_external/C433_RESULT_1.json` |
| C434 | `research/c434_c430_final_mlaad_dev` | `research/c434_c430_final_mlaad_dev/C434_RESULT_1.json` |
| C435 | `research/c435_frozen_wav2vec_probe` | `research/c435_frozen_wav2vec_probe/C435_RESULT.json` |
| C436 | `research/c436_frozen_probe_external` | `research/c436_frozen_probe_external/C436_RESULT_1.json` |
| C437 | `research/c437_c363_crossed_replay` | `research/c437_c363_crossed_replay/C437_RESULT_AND_STOP_2026-09-11.md` |
| C438 | `research/c438_pella_music_invariance` | `research/c438_pella_music_invariance/C438_RESULT_AND_LIMITS_2026-09-11.md` |
| C439 | `research/c439_pella_layer_invariance` | `research/c439_pella_layer_invariance/C439_RESULT_AND_LIMITS_2026-09-11.md` |
| C440 | `research/c440_spectra_tail_invariance` | `research/c440_spectra_tail_invariance/C440_RESULT_AND_LIMITS_2026-09-11.md` |
| C441 | `research/c441_spectra_block_file_transfer` | `research/c441_spectra_block_file_transfer/C441_RESULT_AND_STOP_2026-09-11.md` |
| C442 | `research/c442_spectra_stem_baseline` | `research/c442_spectra_stem_baseline/C442_RESULT_AND_NEXT_2026-09-11.md` |
| C443 | `research/c443_spectra_music_complement` | `research/c443_spectra_music_complement/C443_RESULT_AND_LIMITS_2026-09-11.md` |
| C444 | `research/c444_spectra_music_fifth_expert` | `research/c444_spectra_music_fifth_expert/C444_RESULT_AND_LIMITS_2026-09-11.md` |
| C445 | `research/c445_spectra_stem_adaptation` | `research/c445_spectra_stem_adaptation/C445_RESULT_AND_LIMITS_2026-09-11.md` |
| C446 | `research/c446_spectra_stem_file_transfer` | `research/c446_spectra_stem_file_transfer/C446_RESULT_AND_STOP_2026-09-11.md` |
| C447 | `research/c447_clean_teacher_stem_distillation` | `research/c447_clean_teacher_stem_distillation/C447_RESULT_AND_STOP_2026-09-11.md` |
| C448 | `research/c448_clean_teacher_file_transfer` | `research/c448_clean_teacher_file_transfer/C448_RESULT.json` |
| C449 | `research/c449_nonvoice_spectra_probe` | `research/c449_nonvoice_spectra_probe/C449_RESULT_AND_LIMITS_2026-09-11.md` |
| C450 | `research/c450_nonvoice_aligned_file_transfer` | `research/c450_nonvoice_aligned_file_transfer/C450_C450B_CACHE_PARITY_STOPS_2026-09-11.md` |
| C451 | `research/c451_presence_file20` | `research/c451_presence_file20/C451_RESULT.json` |
| C452 | `research/c452_singing_presence_preservation` | `research/c452_singing_presence_preservation/C452_RESULT_AND_LIMITS_2026-09-11.md` |
| C453 | `research/c453_three_state_voice_head` | `research/c453_three_state_voice_head/C453_RESULT.json` |
| C454 | `research/c454_three_state_cached_transfer` | `research/c454_three_state_cached_transfer/C454_RESULT.json` |
| C455 | `research/c455_file_branch_oracle_diagnostic` | `research/c455_file_branch_oracle_diagnostic/C455_DIAGNOSIS_2026-09-11.md` |
| C456 | `research/c456_oof_music_global_transfer` | `research/c456_oof_music_global_transfer/C456_RESULT_AND_LIMITS_2026-09-11.md` |
| C457 | `research/c457_generator_balanced_tail` | `research/c457_generator_balanced_tail/C457_RESULT_AND_STOP_2026-09-11.md` |
| C458 | `research/c458_balanced_music_transfer` | `research/c458_balanced_music_transfer/C458_FREEZE.md` |
| C459 | `research/c459_public_inner_optimization` | `research/c459_public_inner_optimization/C459_RESULT_AND_LIMITS_2026-09-11.md` |
| C460 | `research/c460_c459_music_transfer` | `research/c460_c459_music_transfer/C460_RESULT_280.json` |
| C461 | `research/c461_deezer_teacher_preservation` | `research/c461_deezer_teacher_preservation/C461_RESULT_AND_LIMITS_2026-09-11.md` |
| C462 | `research/c462_c461_music_transfer` | `research/c462_c461_music_transfer/C462_RESULT_AND_NEXT_2026-09-11.md` |
| C463 | `research/c463_aime_riffusion_source_expansion` | `research/c463_aime_riffusion_source_expansion/C463_ROOT_LIMITED_RESEARCH_DECISION.md` |
| C464 | `research/c464_riffusion_six_views` | `research/c464_riffusion_six_views/C464_ACTUAL_AUDIO_MANIFEST.json` |
| C465 | `research/c465_riffusion_expansion_kd` | `research/c465_riffusion_expansion_kd/C465_RESULT_AND_LIMITS_2026-09-11.md` |
| C466 | `research/c466_c465_music_transfer` | `research/c466_c465_music_transfer/C466_RESULT_AND_NEXT_2026-09-11.md` |
| C467 | `research/c467_c465_broader_transfer` | `research/c467_c465_broader_transfer/C467_RESULT_AND_LIMITS_2026-09-11.md` |
| C468 | `research/c468_aime_audioldm2_source_expansion` | `research/c468_aime_audioldm2_source_expansion/C468_ROOT_LIMITED_RESEARCH_DECISION.md` |
| C469 | `research/c469_audioldm2_six_views` | `research/c469_audioldm2_six_views/C469_ACTUAL_AUDIO_MANIFEST.json` |
| C470 | `research/c470_audioldm2_expansion_kd` | `research/c470_audioldm2_expansion_kd/C470_RESULT_AND_LIMITS_2026-09-11.md` |
| C471 | `research/c471_c470_music_transfer` | `research/c471_c470_music_transfer/C471_RESULT_AND_DECISION.md` |
| C472 | `research/c472_longbag_temporal_head` | `research/c472_longbag_temporal_head/C472_RESULT_AND_NEXT.md` |
| C473 | `research/c473_diverse_longbag_training` | `research/c473_diverse_longbag_training/C473_AUDIO_RESULT_1280.json` |
| C474 | `research/c474_max_readout_screen` | `research/c474_max_readout_screen/C474_RESULT.json` |
| C475 | `research/c475_c473_music_transfer` | `research/c475_c473_music_transfer/C475_RESULT.md` |
| C476 | `research/c476_localized_tail_kd` | `research/c476_localized_tail_kd/C476_RESULT.json` |
| C477 | `research/c477_c476_music_transfer` | `research/c477_c476_music_transfer/C477_RESULT.md` |
| C478 | `research/c478_separate_music_experts` | `research/c478_separate_music_experts/ROOT_C478_RETAINED_RESEARCH_DECISION.md` |
| C479 | `research/c479_preserved_file_music_head` | `research/c479_preserved_file_music_head/ROOT_C479_RETAINED_RESEARCH_DECISION.md` |
| C480 | `research/c480_file_error_attribution` | `research/c480_file_error_attribution/C480_RESULT.json` |
| C481 | `research/c481_focal_music_tail` | `research/c481_focal_music_tail/ROOT_C481_DECISION.md` |
| C482 | `research/c482_c481_music_transfer` | `research/c482_c481_music_transfer/C482_RESULT.md` |
| C484 | `research/c484_focal_scale_transfer` | `research/c484_focal_scale_transfer/C484_RESULT.json` |
| C485 | `research/c485_earlier_focal_encoder` | `research/c485_earlier_focal_encoder/ROOT_C485_FULL_DECISION.md` |
| C486 | `research/c486_complementary_music_branches` | `research/c486_complementary_music_branches/C486_RESULT.json` |
| C487 | `research/c487_c485_music_transfer` | `research/c487_c485_music_transfer/C487_RESULT.md` |
| C488 | `research/c488_boundary_auxiliary` | `research/c488_boundary_auxiliary/C488_RESULT.json` |
| C489 | `research/c489_robust_fourier_probe` | `research/c489_robust_fourier_probe/C489_FIRST1_RESULT.json` |
| C490 | `research/c490_c488_music_transfer` | `research/c490_c488_music_transfer/C490_RESULT.md` |
| C491 | `research/c491_training_frame_pool_replay` | `research/c491_training_frame_pool_replay/C491_RESULT.md` |
| C492 | `research/c492_logshift_train8` | `research/c492_logshift_train8/C492_RESULT.json` |
| C493 | `research/c493_robust_fourier_training` | `research/c493_robust_fourier_training/C493_RESULT_AND_FAILURE.md` |
| C494 | `research/c494_c493_diagnostic` | `research/c494_c493_diagnostic/C494_READONLY_AUDIT.md` |
| C495 | `research/c495_logshift_training_diagnostic` | `research/c495_logshift_training_diagnostic/C495_RESULT.json` |
| C496 | `research/c496_phase_cnn_smoke` | `research/c496_phase_cnn_smoke/C496_RESULT.json` |
| C497 | `research/c497_phase_cnn_training` | `research/c497_phase_cnn_training/C497_RESULT_AND_FAILURE.md` |
| C498 | `research/c498_augmentation_smoke` | `research/c498_augmentation_smoke/C498_RESULT.json` |
| C499 | `research/c499_regularized_phase_training` | `research/c499_regularized_phase_training/C499_RESULT_AND_FAILURE.md` |
| C500 | `research/c500_disjoint_time_coverage` | `research/c500_disjoint_time_coverage/C500_METADATA_PLAN.json` |
| C501 | `research/c501_temporal_coverage_tail` | `research/c501_temporal_coverage_tail/C501_RESULT_AND_LIMITS_2026-09-12.md` |
| C502 | `research/c502_c501_music_transfer` | `research/c502_c501_music_transfer/C502_RESULT_AND_LIMITS_2026-09-12.md` |
| C503 | `research/c503_next_direction` | `research/c503_next_direction/C490_ACTION_REVIEW.md` |
| C505 | `research/c505_temporal_teacher_preservation` | `research/c505_temporal_teacher_preservation/C505_RESULT.json` |
| C506 | `research/c506_lfcc_density` | `research/c506_lfcc_density/C506_RESULT_AND_LIMITS_2026-09-12.md` |
| C507 | `research/c507_gap_coverage` | `research/c507_gap_coverage/C507_GEOMETRY_RESULT.json` |
| C508 | `research/c508_c505_music_transfer` | `research/c508_c505_music_transfer/C505_RESULT_AND_LIMITS.md` |
| C509 | `research/c509_anchor_gap_transfer` | `research/c509_anchor_gap_transfer/C509_RESULT_AND_LIMITS_2026-09-12.md` |
| C510 | `research/c510_background_diversity` | `research/c510_background_diversity/FEASIBILITY.md` |
| C511 | `research/c511_diverse_background_audio` | `research/c511_diverse_background_audio/C511_AUDIO_RESULT_1.json` |
| C512 | `research/c512_temporal_pair_ensemble` | `research/c512_temporal_pair_ensemble/C512_RESULT_AND_LIMITS.md` |
| C513 | `research/c513_diverse_background_features` | `research/c513_diverse_background_features/C513_RESULT_1.json` |
| C514 | `research/c514_background_balanced_temporal` | `research/c514_background_balanced_temporal/C514_RESULT_AND_LIMITS.md` |
| C515 | `research/c515_c514_music_transfer` | `research/c515_c514_music_transfer/C515_RESULT_AND_LIMITS.md` |
| C516 | `research/c516_voice_partial_features` | `research/c516_voice_partial_features/C516_RESULT_AND_LIMITS_2026-09-12.md` |
| C517 | `research/c517_temporal_runtime` | `research/c517_temporal_runtime/C517_RESULT_C505_1.json` |
| C518 | `research/c518_partial_voice_temporal` | `research/c518_partial_voice_temporal/C518_RESULT_AND_LIMITS_2026-09-12.md` |
| C519 | `research/c519_temporal_candidate_transfer` | `research/c519_temporal_candidate_transfer/C519_C518_RESULT_1.json` |
| C520 | `research/c520_learned_temporal_pool` | `research/c520_learned_temporal_pool/C520_RESULT.json` |
| C521 | `research/c521_voice_teacher_temporal` | `research/c521_voice_teacher_temporal/C521_RESULT.json` |
| C522 | `research/c522_temporal_music_submission` | `research/c522_temporal_music_submission/C522_PACKAGING_REUSE_PLAN.md` |
| C523 | `research/c523_voice_prefix` | `research/c523_voice_prefix/C523_ATTEMPT_1789192420708857100.json` |
| C524 | `research/c524_c521_music_transfer` | `research/c524_c521_music_transfer/C524_C521_RESULT_1.json` |
| C525 | `research/c525_fixed_temporal_ensemble` | `research/c525_fixed_temporal_ensemble/C525_RESULT.json` |
| C526 | `research/c526_joint_voice_temporal` | `research/c526_joint_voice_temporal/C526_RESULT_AND_LIMITS_2026-09-12.md` |
| C527 | `research/c527_c526_music_transfer` | `research/c527_c526_music_transfer/C527_C526_RESULT_1.json` |
| C528 | `research/c528_c445_voice_transfer` | `research/c528_c445_voice_transfer/C528_RESULT_AND_LIMITS.md` |
| C529 | `research/c529_voice_attention_teacher` | `research/c529_voice_attention_teacher/C529_RESULT_AND_TRANSFER_2026-09-12.md` |
| C530 | `research/c530_c529_music_transfer` | `research/c530_c529_music_transfer/C530_C529_RESULT_1.json` |
| C531 | `research/c531_attention_runtime` | `research/c531_attention_runtime/C531_RESULT_C520_1.json` |
| C532 | `research/c532_c520_music_submission` | `research/c532_c520_music_submission/C532_CODE_ONLY_CHECK.json` |
| C533 | `research/c533_c532_postmortem` | `research/c533_c532_postmortem/C533_RESULT.json` |
| C534 | `research/c534_next_training` | `research/c534_next_training/PROPOSAL.md` |
| C535 | `research/c535_preserved_dual_attention_calibration` | `research/c535_preserved_dual_attention_calibration/C535_RESULT_AND_LIMITS.md` |
| C536 | `research/c536_c205_teacher_attention` | `research/c536_c205_teacher_attention/C536_C537_RESULT_AND_LIMITS.md` |
| C537 | `research/c537_c536_music_transfer` | `research/c537_c536_music_transfer/C537_C536_RESULT_1.json` |
| C538 | `research/c538_pointwise_attention` | `research/c538_pointwise_attention/C538_C539_RESULT_AND_LIMITS.md` |
| C539 | `research/c539_c538_music_transfer` | `research/c539_c538_music_transfer/C539_C538_RESULT_1.json` |
| C540 | `research/c540_c205_frozen_features` | `research/c540_c205_frozen_features/ROOT_C540_C541_RETAINED_RESEARCH_DECISION.md` |
| C541 | `research/c541_c205_temporal_attention` | `research/c541_c205_temporal_attention/C541_C542_RESULT_AND_LIMITS.md` |
| C542 | `research/c542_c541_music_transfer` | `research/c542_c541_music_transfer/C542_C541_RESULT_1.json` |
| C543 | `research/c543_c536_file_event` | `research/c543_c536_file_event/C543_RESULT_AND_LIMITS.md` |
| C544 | `research/c544_c536_preserved_dual_calibration` | `research/c544_c536_preserved_dual_calibration/C544_RESULT_AND_LIMITS.md` |
| C545 | `research/c545_c543_file_transfer` | `research/c545_c543_file_transfer/C545_RESULT_AND_LIMITS.md` |
| C546 | `research/c546_presence_conditioned_attention` | `research/c546_presence_conditioned_attention/C546_RESULT_AND_LIMITS.md` |
| C547 | `research/c547_c536_music_submission` | `research/c547_c536_music_submission/ROOT_C547_PROBE_DECISION.md` |
| C548 | `research/c548_c547_postmortem` | `research/c548_c547_postmortem/C548_SERVER_RESULT_AND_SCOPE.md` |
| C549 | `research/c549_linear_spectrum_lcnn` | `research/c549_linear_spectrum_lcnn/C549_RESULT_AND_NEXT_DECISION.md` |
| C550 | `research/c550_fresh40_canonical` | `research/c550_fresh40_canonical/C550_C205_PASS_1.json` |
| C551 | `research/c551_c549_internal_expert` | `research/c551_c549_internal_expert/C551_RESULT_AND_STOP.md` |
| C552 | `research/c552_c549_gain_invariance` | `research/c552_c549_gain_invariance/C552_RESULT_AND_LIMITS.md` |
| C553 | `research/c553_c552_internal_expert` | `research/c553_c552_internal_expert/C553_RESULT_AND_STOP.md` |
| C554 | `research/c554_joint_music_scores` | `research/c554_joint_music_scores/C554_CACHE408.json` |
| C555 | `research/c555_joint_calibration_sources` | `research/c555_joint_calibration_sources/C555_ACQUISITION_RESULT.md` |
| C556 | `research/c556_joint_score_acquisition` | `research/c556_joint_score_acquisition/ROOT_INFERENCE_SCOPE.md` |
| C557 | `research/c557_expanded_music_calibration`<br>`research/c557_source_balanced_fusion` | `research/c557_source_balanced_fusion/C557_RESULT_AND_NEXT.md` |
| C558 | `research/c558_fine_presence` | `research/c558_fine_presence/C558_RESULT_AND_STOP.md` |
| C559 | `research/c559_context2s` | `research/c559_context2s/C559_SMOKE.json` |
| C560 | `research/c560_context2s_tail` | `research/c560_context2s_tail/C560_RESULT_AND_NEXT.md` |
| C561 | `research/c561_train_bn_recalibration` | `research/c561_train_bn_recalibration/C561_RESULT_AND_STOP.md` |
| C562 | `research/c562_newsource_weak_bag` | `research/c562_newsource_weak_bag/C562_RESULT_AND_NEXT.md` |
| C563 | `research/c563_separate_source_head` | `research/c563_separate_source_head/C563_RESULT_AND_STOP.md` |
| C564 | `research/c564_eat_base` | `research/c564_eat_base/ROOT_ACQUISITION_AND_SMOKE_SCOPE.md` |
| C565 | `research/c565_eat_music_head` | `research/c565_eat_music_head/C565_COMPLEMENTARITY_RESULT_AND_LIMITS.md` |
| C566 | `research/c566_eat_lastblock` | `research/c566_eat_lastblock/C566_COMPLEMENTARITY_RESULT_AND_LIMITS.md` |
| C567 | `research/c567_diverse_voice_music` | `research/c567_diverse_voice_music/C567_MATERIALIZATION_RESULT_AND_LIMITS.md` |
| C568 | `research/c568_eat_diverse_voice` | `research/c568_eat_diverse_voice/C568_COMPLEMENTARITY_RESULT_AND_LIMITS.md` |
| C569 | `research/c569_eat_deezer_role` | `research/c569_eat_deezer_role/C568_DQUARTER_RESULT_AND_STOP.md` |
| C570 | `research/c570_music_source_expansion` | `research/c570_music_source_expansion/C570_METADATA_RESULT_AND_DEFER.md` |
| C571 | `research/c571_sparse_realvoice_views` | `research/c571_sparse_realvoice_views/C571_ACTUAL_RESULT.md` |
| C572 | `research/c572_eat_sparse_music` | `research/c572_eat_sparse_music/C572_MULTIWINDOW_RESULT_AND_KEEP.md` |
| C573 | `research/c573_joint_event_data` | `research/c573_joint_event_data/C573_METADATA_RESULT.md` |
| C574 | `research/c574_eat_joint_events` | `research/c574_eat_joint_events/C574_FILE200_RESULT_AND_FAILURE_EXPLANATION.md` |
| C575 | `research/c575_eat_independent_expert` | `research/c575_eat_independent_expert/C575_GROUPHELD_RESULT_AND_LIMITS.md` |
| C576 | `research/c576_music_newfamilies` | `research/c576_music_newfamilies/ROOT_ACQUISITION_SCOPE.md` |
| C577 | `research/c577_c575_submission` | `research/c577_c575_submission/ROOT_PUBLIC_DECISION.md` |
| C578 | `research/c578_c577_result_audit` | `research/c578_c577_result_audit/C577_EQUAL_SCORE_PUBLIC_COUNTEREXAMPLES_AND_LIMITS.md` |
| C579 | `research/c579_newfamily_views` | `research/c579_newfamily_views/ROOT_DATA_SCOPE.md` |
| C580 | `research/c580_eat_newfamilies` | `research/c580_eat_newfamilies/C580_OUTER_RESULT_AND_LIMITS.md` |
| C581 | `research/c581_dual_eat_expert` | `research/c581_dual_eat_expert/C581_RESULT_AND_TRANSFER_FAILURE.md` |
| C582 | `research/c582_matched_splice_voice` | `research/c582_matched_splice_voice/ROOT_DATA_SCOPE.md` |
| C583 | `research/c583_eat_matched_splice` | `research/c583_eat_matched_splice/C583_OUTER_RESULT_AND_LIMITS.md` |
| C584 | `research/c584_splice_eat_expert` | `research/c584_splice_eat_expert/C584_INITIAL_RESULT_AND_NEXT.md` |
| C585 | `research/c585_preserved_file_eat` | `research/c585_preserved_file_eat/C585_RESULT_AND_LIMITS.md` |
| C586 | `research/c586_c584_submission` | `research/c586_c584_submission/ROOT_PUBLIC_DECISION.md` |
| C587 | `research/c587_eat_supcon` | `research/c587_eat_supcon/C587_RESULT.json` |
| C588 | `research/c588_shifted_splice_train` | `research/c588_shifted_splice_train/ROOT_DATA_SCOPE.md` |
| C589 | `research/c589_eat_local_aux` | `research/c589_eat_local_aux/C589_TRANSFER_RESULT_AND_NEXT.md` |
| C590 | `research/c590_eat_attentive_pool` | `research/c590_eat_attentive_pool/C590_TRANSFER_RESULT_AND_NEXT.md` |
| C591 | `research/c591_eat_depth_pool` | `research/c591_eat_depth_pool/C591_TRANSFER_RESULT_AND_NEXT.md` |
| C592 | `research/c592_eat_depth_heads` | `research/c592_eat_depth_heads/C592_TRANSFER_RESULT_AND_NEXT.md` |
| C593 | `research/c593_eat_depth_augmented` | `research/c593_eat_depth_augmented/C593_TRANSFER_RESULT_AND_NEXT.md` |
| C594 | `research/c594_depth_augmented_expert` | `research/c594_depth_augmented_expert/RESULT_AND_NEXT.md` |
| C595 | `research/c595_preserved_event_residual` | `research/c595_preserved_event_residual/RESULT_AND_LIMITS.md` |
| C596 | `research/c596_c594_submission` | `research/c596_c594_submission/ROOT_PUBLIC_DECISION.md` |
| C597 | `research/c597_next_strategy` | `research/c597_next_strategy/RELATED_CHALLENGE_METHODS.md` |
| C598 | `research/c598_file_error_floor` | `research/c598_file_error_floor/C598_RESULT_AND_LIMITS.md` |
| C599 | `research/c599_eat_lasttwo` | `research/c599_eat_lasttwo/C599_TRANSFER_RESULT_AND_NEXT.md` |
| C600 | `research/c600_matched_pair_head` | `research/c600_matched_pair_head/RESULT_AND_NEXT.md` |
| C601 | `research/c601_voice_presence_feasibility` | `research/c601_voice_presence_feasibility/C601_DEVELOPMENT32_RESULT_AND_LIMITS.md` |
| C602 | `research/c602_silero_file_presence` | `research/c602_silero_file_presence/C602_RESULT_AND_NO_GO.md` |
| C603 | `research/c603_complementary_voice_music` | `research/c603_complementary_voice_music/RESULT_AND_NO_GO.md` |
| C604 | `research/c604_voice_presence_pool` | `research/c604_voice_presence_pool/C604_RESULT.json` |
| C605 | `research/c605_voice_event_consistency` | `research/c605_voice_event_consistency/C605_RESULT.json` |
| C606 | `research/c606_singing_voice_pool` | `research/c606_singing_voice_pool/C606_RESULT_AND_LIMITS.md` |
| C607 | `research/c607_eat_speech_authenticity` | `research/c607_eat_speech_authenticity/C607_RESULT_AND_TRANSFER_2026-09-14.md` |
| C608 | `research/c608_deezer_prefix_skip` | `research/c608_deezer_prefix_skip/RESULT_AND_LIMITS.md` |
| C609 | `research/c609_crossed_file_transfer` | `research/c609_crossed_file_transfer/C609_RESULT.json` |
| C610 | `research/c610_eat_covariance_head` | `research/c610_eat_covariance_head/RESULT_AND_LIMITS.md` |
| C611 | `research/c611_eat_speech_raw_stem` | `research/c611_eat_speech_raw_stem/ROOT_SCOPE.md` |
| C612 | `research/c612_temporal_complementarity` | `research/c612_temporal_complementarity/RESULT_AND_LIMITS.md` |
| C613 | `research/c613_eat_deezer_teacher` | `research/c613_eat_deezer_teacher/RESULT_AND_LIMITS.md` |
| C614 | `research/c614_temporal_long_gate` | `research/c614_temporal_long_gate/RESULT_AND_LIMITS.md` |
| C615 | `research/c615_eat_file_authenticity` | `research/c615_eat_file_authenticity/RESULT_AND_LIMITS.md` |
| C616 | `research/c616_eat_speech_augmentation` | `research/c616_eat_speech_augmentation/ROOT_DATA_SCOPE.md` |
| C617 | `research/c617_eat_augmented_speech` | `research/c617_eat_augmented_speech/RESULT_AND_LIMITS.md` |
| C618 | `research/c618_eat_lora_scope` | `research/c618_eat_lora_scope/RESULT_AND_LIMITS.md` |
| C619 | `research/c619_clean_feature_reconstruction` | `research/c619_clean_feature_reconstruction/RESULT_AND_LIMITS.md` |
| C620 | `research/c620_eat_music_lora` | `research/c620_eat_music_lora/RESULT_AND_LIMITS.md` |
| C621 | `research/c621_music_phase_margin` | `research/c621_music_phase_margin/RESULT_AND_LIMITS.md` |
| C622 | `research/c622_eat_local_max` | `research/c622_eat_local_max/RESULT_AND_LIMITS.md` |
| C623 | `research/c623_spectra_augmentation` | `research/c623_spectra_augmentation/RESULT_AND_LIMITS.md` |
| C624 | `research/c624_c623_voice_transfer` | `research/c624_c623_voice_transfer/RESULT_AND_LIMITS.md` |
| C625 | `research/c625_deezer_fir_adaptation` | `research/c625_deezer_fir_adaptation/RESULT_AND_LIMITS.md` |
| C626 | `research/c626_deezer_hann_fir` | `research/c626_deezer_hann_fir/RESULT_AND_LIMITS.md` |
| C627 | `research/c627_eat_tf_graph` | `research/c627_eat_tf_graph/RESULT_AND_LIMITS.md` |
| C628 | `research/c628_fixed_graph_complement` | `research/c628_fixed_graph_complement/C628_RESULT.json` |
| C629 | `research/c629_eat_depth_diverse` | `research/c629_eat_depth_diverse/RESULT_AND_LIMITS.md` |
| C630 | `research/c630_eat_large_depth` | `research/c630_eat_large_depth/RESULT_AND_LIMITS.md` |
| C631 | `research/c631_eat_large_lastblock` | `research/c631_eat_large_lastblock/RESULT_AND_LIMITS.md` |
| C632 | `research/c632_large_music_expert` | `research/c632_large_music_expert/RESULT_AND_LIMITS.md` |
| C633 | `research/c633_standalone_direct` | `research/c633_standalone_direct/RESULT_AND_LIMITS.md` |
| C634 | `research/c634_train_ecdf` | `research/c634_train_ecdf/RESULT_AND_LIMITS.md` |
| C635 | `research/c635_c631_source144` | `research/c635_c631_source144/RESULT_AND_LIMITS.md` |
| C636 | `research/c636_deezer_fourier_bilinear` | `research/c636_deezer_fourier_bilinear/RESULT_AND_LIMITS.md` |
| C637 | `research/c637_joint_state_file` | `research/c637_joint_state_file/RESULT_AND_LIMITS.md` |
| C638 | `research/c638_joint_state_aligned` | `research/c638_joint_state_aligned/RESULT_AND_LIMITS.md` |
| C639 | `research/c639_monotone_music` | `research/c639_monotone_music/RESULT_AND_LIMITS.md` |
| C640 | `research/c640_monotone_tree_file` | `research/c640_monotone_tree_file/RESULT_AND_LIMITS.md` |
| C641 | `research/c641_independent_eat_triad` | `research/c641_independent_eat_triad/RESULT_AND_LIMITS.md` |
| C642 | `research/c642_large_diverse` | `research/c642_large_diverse/RESULT_AND_LIMITS.md` |
| C643 | `research/c643_large_linear` | `research/c643_large_linear/RESULT_AND_LIMITS.md` |
| C644 | `research/c644_linear_source144` | `research/c644_linear_source144/RESULT_AND_LIMITS.md` |
| C645 | `research/c645_linear_window_max` | `research/c645_linear_window_max/RESULT_AND_LIMITS.md` |
| C646 | `research/c646_large_temporal_mil` | `research/c646_large_temporal_mil/RESULT_AND_LIMITS.md` |
| C647 | `research/c647_temporal_source144` | `research/c647_temporal_source144/RESULT_AND_LIMITS.md` |
| C648 | `research/c648_disagreement_mixture` | `research/c648_disagreement_mixture/RESULT_AND_LIMITS.md` |
| C649 | `research/c649_monotone_music_tree` | `research/c649_monotone_music_tree/RESULT_AND_LIMITS.md` |
| C650 | `research/c650_conditional_average` | `research/c650_conditional_average/RESULT_AND_LIMITS.md` |
| C651 | `research/c651_conditional_transfer` | `research/c651_conditional_transfer/ROOT_SCOPE.md` |
| C652 | `research/c652_c596_full_diagnosis` | `research/c652_c596_full_diagnosis/RESULT_AND_NEXT.md` |
| C653 | `research/c653_c596_matched_panel` | `research/c653_c596_matched_panel/C653_CPU4_RESULT_1.json` |
| C654 | `research/c654_c596_fresh_file` | `research/c654_c596_fresh_file/FIRST8_RESULT_AND_EXPANSION.md` |
| C655 | `research/c655_fresh_parent_inventory` | `research/c655_fresh_parent_inventory/C655_INVENTORY.json` |
| C656 | `research/c656_large_diagnosis_sources` | `research/c656_large_diagnosis_sources/FMA_065753_UNAVAILABLE_REPORT.md` |
| C657 | `research/c657_c596_ten_second_pilot` | `research/c657_c596_ten_second_pilot/C657_CPU4_RESULT_1.json` |
| C658 | `research/c658_file_structure_2x2` | `research/c658_file_structure_2x2/RESULT_AND_NEXT.md` |
| C659 | `research/c659_preserved_music_input` | `research/c659_preserved_music_input/RESULT_AND_LIMITS.md` |
| C660 | `research/c660_direct_music_evidence` | `research/c660_direct_music_evidence/RESULT_AND_LIMITS.md` |
| C661 | `research/c661_c660_labeled_confirmation` | `research/c661_c660_labeled_confirmation/RESULT_AND_LIMITS.md` |
| C662 | `research/c662_c660_source_confirmation100` | `research/c662_c660_source_confirmation100/RESULT_AND_LIMITS.md` |
| C663 | `research/c663_music_event_semantics` | `research/c663_music_event_semantics/RESULT_AND_LIMITS.md` |
| C664 | `research/c664_c660_remaining_paths` | `research/c664_c660_remaining_paths/RESULT_AND_LIMITS.md` |
| C665 | `research/c665_eat_temporal_event` | `research/c665_eat_temporal_event/RESULT_AND_LIMITS.md` |
| C666 | `research/c666_aligned_music_evidence` | `research/c666_aligned_music_evidence/RESULT_AND_LIMITS.md` |
| C667 | `research/c667_local_ensemble_event` | `research/c667_local_ensemble_event/RESULT_AND_LIMITS.md` |
| C668 | `research/c668_direct_input_calibration` | `research/c668_direct_input_calibration/RESULT_AND_LIMITS.md` |
| C669 | `research/c669_c660_silero_voice` | `research/c669_c660_silero_voice/RESULT_AND_LIMITS.md` |
| C670 | `research/c670_c669_transfer` | `research/c670_c669_transfer/RESULT_AND_LIMITS.md` |
| C671 | `research/c671_bounded_direct_experts` | `research/c671_bounded_direct_experts/RESULT_AND_LIMITS.md` |
| C672 | `research/c672_presence_agreement` | `research/c672_presence_agreement/RESULT_AND_LIMITS.md` |
| C673 | `research/c673_voice_joint_event` | `research/c673_voice_joint_event/RESULT_AND_LIMITS.md` |
| C674 | `research/c674_bounded_music_transfer` | `research/c674_bounded_music_transfer/RESULT_AND_LIMITS.md` |
| C675 | `research/c675_broad_music_head` | `research/c675_broad_music_head/C675_RESULT_AND_LIMITS.md` |
| C676 | `research/c676_local_music_bag` | `research/c676_local_music_bag/RESULT_AND_LIMITS.md` |
| C677 | `research/c677_component_known_temporal` | `research/c677_component_known_temporal/C677_RESULT_1.json` |
| C678 | `research/c678_broad_voice_reliability` | `research/c678_broad_voice_reliability/RESULT_AND_LIMITS.md` |
| C679 | `research/c679_time_local_voice_bag` | `research/c679_time_local_voice_bag/RESULT_AND_LIMITS.md` |
| C680 | `research/c680_file_supervision_masks` | `research/c680_file_supervision_masks/RESULT_AND_LIMITS.md` |
| C681 | `research/c681_voice_coverage` | `research/c681_voice_coverage/RESULT_AND_NEXT_2026-09-21.md` |
| C682 | `research/c682_raw_voice_coverage` | `research/c682_raw_voice_coverage/RESULT_AND_NEXT_2026-09-21.md` |
| C683 | `research/c683_vocal_domain_coverage` | `research/c683_vocal_domain_coverage/RESULT_AND_LIMITS.md` |
| C684 | `research/c684_ordered_voice_identity` | `research/c684_ordered_voice_identity/RESULT_AND_LIMITS.md` |
| C685 | `research/c685_joint_c3_pool` | `research/c685_joint_c3_pool/RESULT_AND_LIMITS.md` |
| C686 | `research/c686_uncompressed_voice_experts` | `research/c686_uncompressed_voice_experts/RESULT_AND_LIMITS.md` |
| C687 | `research/c687_df_native_music_adaptation` | `research/c687_df_native_music_adaptation/EARLY_RESULT_AND_TRAINING_DIAGNOSIS.md` |
| C688 | `research/c687_df_native_music_adaptation/c688_stratified` | `research/c687_df_native_music_adaptation/c688_stratified/C688_TRAIN_RESULT.json` |
| C689 | `research/c687_df_native_music_adaptation/c689_retention` | `research/c687_df_native_music_adaptation/c689_retention/RESULT_AND_NEXT.md` |
| C690 | `research/c687_df_native_music_adaptation/c690_native_confirmation` | `research/c687_df_native_music_adaptation/c690_native_confirmation/FINAL_RESULT_AND_LIMITS.md` |
| C691 | `research/c687_df_native_music_adaptation/c691_error_controls` | `research/c687_df_native_music_adaptation/c691_error_controls/FINAL_RESULT_AND_LIMITS.md` |
| C692 | `research/c687_df_native_music_adaptation/c692_source_retention100` | `research/c687_df_native_music_adaptation/c692_source_retention100/FINAL_RESULT_AND_LIMITS.md` |
| C693 | `research/c687_df_native_music_adaptation/c693_package_integration` | `research/c687_df_native_music_adaptation/c693_package_integration/ROOT_SCOPE.md` |
| C694 | `research/c694_c693_residual_diagnosis` | `research/c694_c693_residual_diagnosis/COMPOUND_RESULT_AND_LIMITS.md` |
| C695 | `research/c687_df_native_music_adaptation/c695_final_train_diagnosis` | `research/c687_df_native_music_adaptation/c695_final_train_diagnosis/RESULT_AND_NEXT.md` |
| C696 | `research/c687_df_native_music_adaptation/c696_stem_training_support` | `research/c687_df_native_music_adaptation/c696_stem_training_support/RESULT_AND_NEXT.md` |
| C697 | `research/c687_df_native_music_adaptation/c697_matched_stem_training` | `research/c687_df_native_music_adaptation/c697_matched_stem_training/RESULT_AND_NEXT.md` |
| C698 | `research/c698_native_time_local_bag` | `research/c698_native_time_local_bag/ROOT_SCOPE.md` |
| C699 | `research/c699_conditional_local_eat` | `research/c699_conditional_local_eat/RESULT_AND_LIMITS.md` |
| C700 | `research/c700_temporal_coherence_scout` | `research/c700_temporal_coherence_scout/RESULT_AND_NEXT.md` |
| C701 | `research/c687_df_native_music_adaptation/c701_native_source_expansion` | `research/c687_df_native_music_adaptation/c701_native_source_expansion/RESULT_FIRST4_AND_DECISION.md` |
| C702 | `research/c687_df_native_music_adaptation/c702_native_deployment_diagnosis` | `research/c687_df_native_music_adaptation/c702_native_deployment_diagnosis/RESULT_AND_LIMITS.md` |
| C703 | `research/c703_c693_internal_voice_max` | `research/c703_c693_internal_voice_max/RESULT_AND_DECISION.md` |
| C704 | `research/c704_c465_current_music_reuse`<br>`research/c687_df_native_music_adaptation/c704_clean_e2e_v1` | `research/c704_c465_current_music_reuse/FULL_RESULT_AND_PACKAGE_DECISION.md`<br>`research/c687_df_native_music_adaptation/c704_clean_e2e_v1/C704_CLEAN_RECEIPT.json` |
| C705 | `research/c687_df_native_music_adaptation/c705_deployed_native_continuation` | `research/c687_df_native_music_adaptation/c705_deployed_native_continuation/RESULT_AND_NEXT.md` |
| C706 | `research/c706_c465_direct_file` | `research/c706_c465_direct_file/FULL41_RESULT_AND_RETENTION_PLAN.md` |
| C707 | `research/c707_baseline_deezer_direct` | `research/c707_baseline_deezer_direct/C707_REPORTING_CORRECTION.json` |
| C708 | `research/c708_c704_package_candidate` | `research/c708_c704_package_candidate/CLEAN_EXECUTION_RESULT.md` |
| C709 | `research/c709_c704_signal_audit` | `research/c709_c704_signal_audit/RESULT_AND_LIMITS.md` |
| C710 | `research/c710_c465_unaveraged_internal`<br>`research/c687_df_native_music_adaptation/c710_clean_e2e_v1` | `research/c710_c465_unaveraged_internal/OLD160_RESULT_AND_LIMITS.md`<br>`research/c687_df_native_music_adaptation/c710_clean_e2e_v1/C710_CLEAN_RECEIPT.json` |
| C711 | `research/c711_c710_package_candidate` | `research/c711_c710_package_candidate/C710_STAGE_RECEIPT.json` |
| C712 | `research/c712_window_positive_union` | `research/c712_window_positive_union/RESULT_AND_DECISION.md` |
| C713 | `research/c713_external_voice_dual_view` | `research/c713_external_voice_dual_view/RESULT_AND_DECISION.md` |
| C714 | `research/c714_external_spectra_voice` | `research/c714_external_spectra_voice/RESULT_AND_DECISION.md` |
| C715 | `research/c715_external_spectra_voice_candidate` | `research/c715_external_spectra_voice_candidate/ROOT_SCOPE.md` |
| C716 | `research/c716_external_voice_consensus` | `research/c716_external_voice_consensus/RESULT_AND_DECISION.md` |
| C717 | `research/c717_c623_matched_stem_diagnosis` | `research/c717_c623_matched_stem_diagnosis/NEXT_DECISION.md` |
| C718 | `research/c718_external_native_spectra` | `research/c718_external_native_spectra/RESULT_AND_DECISION.md` |
| C719 | `research/c719_spectra_fused_objective` | `research/c719_spectra_fused_objective/C719_RESULT.json` |
| C720 | `research/c720_external_fused_spectra_voice` | `research/c720_external_fused_spectra_voice/RESULT_AND_DECISION.md` |
| C721 | `research/c721_c693_crossed8`<br>`research/c687_df_native_music_adaptation/c721_crossed8` | `research/c721_c693_crossed8/RESULT_AND_NEXT_STEP.md`<br>`research/c687_df_native_music_adaptation/c721_crossed8/C721_MUSIC_RESULT_1.json` |
| C722 | `research/c722_voice_view_mean`<br>`research/c687_df_native_music_adaptation/c722_package_integration` | `research/c722_voice_view_mean/RESULT_AND_DECISION.md`<br>`research/c687_df_native_music_adaptation/c722_package_integration/BUILD_SCOPE.md` |
| C723 | `research/c723_c623_internal_stem` | `research/c723_c623_internal_stem/RESULT_AND_DECISION.md` |
| C724 | `research/c724_c693_channel_diagnosis`<br>`research/c687_df_native_music_adaptation/c724_channel_diagnosis` | `research/c724_c693_channel_diagnosis/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c724_channel_diagnosis/C724_RESULT_1.json` |
| C725 | `research/c725_c693_clear_mixed_diagnosis`<br>`research/c687_df_native_music_adaptation/c725_clear_mixed_diagnosis` | `research/c725_c693_clear_mixed_diagnosis/BASELINE_CORRECTION_AND_RESIDUAL_DECISION.md`<br>`research/c687_df_native_music_adaptation/c725_clear_mixed_diagnosis/C725_RESULT_1.json` |
| C726 | `research/c726_c693_residual_pair`<br>`research/c687_df_native_music_adaptation/c726_residual_pair`<br>`research/c687_df_native_music_adaptation/c726_residual_pair_v2` | `research/c726_c693_residual_pair/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c726_residual_pair/C726_PREPARE.json`<br>`research/c687_df_native_music_adaptation/c726_residual_pair_v2/C726_RESULT_1.json` |
| C727 | `research/c727_positive_event_train_probe`<br>`research/c687_df_native_music_adaptation/c727_positive_event_train_probe`<br>`research/c687_df_native_music_adaptation/c727_positive_event_train_probe_v2` | `research/c727_positive_event_train_probe/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c727_positive_event_train_probe/C727_PREPARE.json`<br>`research/c687_df_native_music_adaptation/c727_positive_event_train_probe_v2/C727_RESULT_1.json` |
| C728 | `research/c728_deployed_event_train_features`<br>`research/c687_df_native_music_adaptation/c728_deployed_event_train_features` | `research/c728_deployed_event_train_features/FULL32_ROOT_DECISION.md`<br>`research/c687_df_native_music_adaptation/c728_deployed_event_train_features/C728_RESULT_1.json` |
| C729 | `research/c729_deployed_event_tail`<br>`research/c687_df_native_music_adaptation/c729_deployed_event_tail`<br>`research/c687_df_native_music_adaptation/c729_deployed_event_tail_v2` | `research/c729_deployed_event_tail/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c729_deployed_event_tail/C729_INPUT_REGISTRY.json`<br>`research/c687_df_native_music_adaptation/c729_deployed_event_tail_v2/C729_ROOT_AUDIT_DECISION.json` |
| C730 | `research/c730_frozen_c688_cls`<br>`research/c687_df_native_music_adaptation/c730_frozen_c688_cls` | `research/c730_frozen_c688_cls/ROOT_SCOPE_DRAFT.md`<br>`research/c687_df_native_music_adaptation/c730_frozen_c688_cls/C730_RESULT_1.json` |
| C731 | `research/c731_fc5_only_deployed_event`<br>`research/c687_df_native_music_adaptation/c731_fc5_only_deployed_event` | `research/c731_fc5_only_deployed_event/TRAIN_AUDIT_DECISION.md`<br>`research/c687_df_native_music_adaptation/c731_fc5_only_deployed_event/C731_ROOT_AUDIT_DECISION.json` |
| C732 | `research/c732_c731_transfer`<br>`research/c687_df_native_music_adaptation/c732_c731_transfer` | `research/c732_c731_transfer/RESULT_AND_LATE_DECISION.md`<br>`research/c687_df_native_music_adaptation/c732_c731_transfer/RESULT_1.json` |
| C733 | `research/c733_c731_late_transfer`<br>`research/c687_df_native_music_adaptation/c733_c731_late_transfer` | `research/c733_c731_late_transfer/RESULT_AND_REJECTION.md` |
| C734 | `research/c734_pair_rank_contrast`<br>`research/c687_df_native_music_adaptation/c734_pair_rank_contrast` | `research/c734_pair_rank_contrast/TRAIN_AUDIT_DECISION.md`<br>`research/c687_df_native_music_adaptation/c734_pair_rank_contrast/C734_ROOT_AUDIT_DECISION.json` |
| C735 | `research/c735_c734_transfer`<br>`research/c687_df_native_music_adaptation/c735_c734_transfer` | `research/c735_c734_transfer/RESULT_AND_LATE_DECISION.md`<br>`research/c687_df_native_music_adaptation/c735_c734_transfer/RESULT_1.json` |
| C736 | `research/c736_c734_late_transfer`<br>`research/c687_df_native_music_adaptation/c736_c734_late_transfer` | `research/c736_c734_late_transfer/RESULT_AND_NEXT.md` |
| C737 | `research/c737_clean_mix_restore`<br>`research/c687_df_native_music_adaptation/c737_clean_mix_restore` | `research/c737_clean_mix_restore/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c737_clean_mix_restore/C737_TRAIN_RESULT.json` |
| C738 | `research/c738_min_norm_restore`<br>`research/c687_df_native_music_adaptation/c738_min_norm_restore` | `research/c738_min_norm_restore/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c738_min_norm_restore/C738_SOLVE_RESULT.json` |
| C739 | `research/c739_bounded_restore`<br>`research/c687_df_native_music_adaptation/c739_bounded_restore` | `research/c739_bounded_restore/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c739_bounded_restore/C739_ROOT_AUDIT_DECISION.json` |
| C740 | `research/c740_bounded_mix_classification`<br>`research/c687_df_native_music_adaptation/c740_bounded_mix_classification`<br>`research/c687_df_native_music_adaptation/c740_bounded_mix_classification_v2` | `research/c740_bounded_mix_classification/TRAIN_AUDIT_DECISION.md`<br>`research/c687_df_native_music_adaptation/c740_bounded_mix_classification/C740_SOLVE_RESULT.json`<br>`research/c687_df_native_music_adaptation/c740_bounded_mix_classification_v2/C740_ROOT_AUDIT_DECISION.json` |
| C741 | `research/c741_c740_transfer`<br>`research/c687_df_native_music_adaptation/c741_c740_transfer`<br>`research/c687_df_native_music_adaptation/c741_c740_transfer_v2` | `research/c741_c740_transfer/RESULT_AND_LATE_DECISION.md`<br>`research/c687_df_native_music_adaptation/c741_c740_transfer/STOP_1790510229581096300.json`<br>`research/c687_df_native_music_adaptation/c741_c740_transfer_v2/RESULT_1.json` |
| C742 | `research/c742_c740_late_transfer`<br>`research/c687_df_native_music_adaptation/c742_c740_late_transfer` | `research/c742_c740_late_transfer/RESULT_AND_NEXT.md` |
| C743 | `research/c743_frozen_eat_train144`<br>`research/c687_df_native_music_adaptation/c743_frozen_eat_train144`<br>`research/c687_df_native_music_adaptation/c743_frozen_eat_train144_v2` | `research/c743_frozen_eat_train144/ROOT_SCOPE_DRAFT.md`<br>`research/c687_df_native_music_adaptation/c743_frozen_eat_train144/C743_INPUT_REGISTRY.json`<br>`research/c687_df_native_music_adaptation/c743_frozen_eat_train144_v2/RESULT_1.json` |
| C744 | `research/c744_eat_last_linear`<br>`research/c687_df_native_music_adaptation/c744_eat_last_linear_v2` | `research/c744_eat_last_linear/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c744_eat_last_linear_v2/C744_TRAIN_RESULT.json` |
| C745 | `research/c745_eat_constrained_readout`<br>`research/c687_df_native_music_adaptation/c745_eat_constrained_readout` | `research/c745_eat_constrained_readout/TRAIN_AUDIT_DECISION.md`<br>`research/c687_df_native_music_adaptation/c745_eat_constrained_readout/C745_ROOT_AUDIT_DECISION.json` |
| C746 | `research/c746_c745_eat_transfer`<br>`research/c687_df_native_music_adaptation/c746_c745_eat_transfer` | `research/c746_c745_eat_transfer/RESULT_AND_LATE_DECISION.md`<br>`research/c687_df_native_music_adaptation/c746_c745_eat_transfer/RESULT_1.json` |
| C747 | `research/c747_c745_eat_late_transfer`<br>`research/c687_df_native_music_adaptation/c747_c745_eat_late_transfer` | `research/c747_c745_eat_late_transfer/RESULT_AND_NEXT.md` |
| C748 | `research/c748_exact_file_train_eat`<br>`research/c687_df_native_music_adaptation/c748_exact_file_train_eat` | `research/c748_exact_file_train_eat/RESULT_AND_TRAINING_HANDOFF.md`<br>`research/c687_df_native_music_adaptation/c748_exact_file_train_eat/RESULT_1.json` |
| C749 | `research/c749_direct_file_residual`<br>`research/c687_df_native_music_adaptation/c749_direct_file_residual` | `research/c749_direct_file_residual/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c749_direct_file_residual/C749_SOLVE_RESULT.json` |
| C750 | `research/c750_exact_file_safety_eat` | `research/c750_exact_file_safety_eat/ROOT_SCOPE_DRAFT.md` |
| C751 | `research/c751_native_support_pilot`<br>`research/c687_df_native_music_adaptation/c751_native_support_pilot` | `research/c751_native_support_pilot/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c751_native_support_pilot/C751_DIAGNOSE_1.json` |
| C752 | `research/c752_music_event_train_eat`<br>`research/c687_df_native_music_adaptation/c752_music_event_train_eat` | `research/c752_music_event_train_eat/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c752_music_event_train_eat/RESULT_1.json` |
| C753 | `research/c753_music_event_bag_readout`<br>`research/c687_df_native_music_adaptation/c753_music_event_bag_readout`<br>`research/c687_df_native_music_adaptation/c753_music_event_bag_readout_v2` | `research/c753_music_event_bag_readout/RESULT_AND_NEXT.md`<br>`research/c687_df_native_music_adaptation/c753_music_event_bag_readout/C753_INPUT_REGISTRY.json`<br>`research/c687_df_native_music_adaptation/c753_music_event_bag_readout_v2/C753_OOF_RESULT.json` |
