# 제3자 출처와 고지

이 연구는 공개 사전학습 모델과 외부 학습 자료를 사용했다. 아래는 원 작업공간에 보존된 출처·라이선스 기록을 정리한 것이다. 이 저장소에는 가중치, 오디오, vendor 모델 구현, wheel을 포함하지 않는다. 출처가 공개되어 있다는 사실만으로 상업 이용·재배포·독점 권리 이전이 모두 허용되는 것은 아니다.

`src/`의 통합 코드도 외부 모델의 수식·인터페이스·파생 모델 계보와 연결된다. `script.py`의 Deezer SpecNN 재구성과 C693/C688 파생 모델을 제한 없는 독립 저작물로 표시하지 않는다. 원문 사본은 `notices/`에 두고, 이 문서의 설명보다 원문 조건을 우선한다.

| 구성 | 출처·고정 버전 | 기록된 조건 및 고지 |
|---|---|---|
| DF-Arena 1B | 원 패키지의 DF-Arena model card·config·provenance | 상류 MIT 부분과 원 기여·변경분의 연구/비상업 제한이 함께 존재. 라이선스 전문과 변경 고지 유지 |
| C688 tail | DF-Arena 마지막 Conformer block/fc5에서 파생한 자체 학습 모델 | 원 DF-Arena 조건을 계승. 원 모델 전체를 자체 개발했다고 표시하지 않음 |
| Spectra-AASIST3 | [lab260/Spectra-AASIST3](https://huggingface.co/lab260/Spectra-AASIST3), revision `bc0ded888080ddad493177bb53aa6f5b95219d7c` | Apache-2.0. 로컬 XLS-R config 사용과 offline loader 변경 고지 유지 |
| SONICS | [awsaf49/sonics](https://github.com/awsaf49/sonics), commit `9156ffad151f797c71556923c4a02fa01fa8fc91` | 구현 MIT. 동봉 고지의 dataset CC-BY-NC-4.0 및 Suno/Udio 관련 추가 조건은 별개로 보존 |
| Deezer/C180/C205 | [deezer/deepfake-detector](https://github.com/deezer/deepfake-detector), commit `edc94ad04b721e4ba59ccfb25e14606ddaa4a78a` | CC-BY-NC-4.0. 원 출처·변경·비상업 조건 유지. 현재 가중치는 자체 학습 파생물이며 Deezer의 보증을 뜻하지 않음 |
| Dasheng | [mispeech/dasheng-base](https://huggingface.co/mispeech/dasheng-base), revision `d29a721c75b996ffa49e2a1f985349d191a4ae5e` | Apache-2.0. frozen 공개 backbone과 자체 C151 head를 구별 |
| EAT | [EAT 연구 저장소](https://github.com/cwx-worst-one/EAT), 사용 checkpoint revision `6eb95936bf1061cacee1c0b89404a1aca9a3c62a` | MIT, Copyright (c) 2024 Wenxi Chen. 원 encoder와 자체 C593 head를 구별 |
| timm | [pytorch-image-models](https://github.com/huggingface/pytorch-image-models), 0.9.12 | Apache-2.0. 원 wheel의 라이선스 고지 보존; 이 보관본에 wheel 없음 |
| torchvision | [pytorch/vision](https://github.com/pytorch/vision), 0.22.1+cu128 | BSD-3-Clause. copyright·조건·면책 고지 유지 |
| PANNs/HTDemucs | 공식 baseline에서 계승한 Cnn14/HTDemucs 자산 | 원 package attribution은 이전 anchor의 고지를 참조. 향후 실제 자산 재배포 시 각 원 출처의 완전한 고지 연결을 확인해야 함 |

## 동봉 원문 사본

- [DF-Arena 라이선스](notices/DF_ARENA_LICENSE.txt), [DF-Arena 변경 고지](notices/DF_ARENA_MODIFICATIONS.md), [C693 파생 모델 provenance](notices/C693_PROVENANCE.md)
- [Deezer CC-BY-NC-4.0](notices/DEEZER_CC_BY_NC_4.0.md), [원 패키지 attribution](notices/ORIGINAL_ATTRIBUTION.md)
- [Spectra Apache-2.0](notices/SPECTRA_APACHE_2.0.txt), [Spectra 변경 고지](notices/SPECTRA_MODIFICATIONS.md)
- [SONICS 고지 전문](notices/SONICS_LICENSE.txt)
- [Dasheng Apache-2.0](notices/DASHENG_APACHE_2.0.txt)
- [EAT MIT](notices/EAT_MIT_LICENSE.txt)
- [torchvision BSD-3-Clause](notices/TORCHVISION_BSD_3_CLAUSE.txt)

원문 사본은 설명용 저장소에 원 출처 고지를 연결하기 위한 것이며, 그 모델·데이터를 함께 배포한다는 뜻은 아니다. 과거 provenance의 미검증 상태나 상대 경로도 당시 기록으로 보존한다.

## 학습 자료의 조건

| 원천 | 보존 기록에서 확인된 구분 |
|---|---|
| ASVspoof | Open Data Commons Attribution License v1.0, attribution과 README |
| MLAAD-tiny | revision `9143e5ea709575ebab6bec52840a1043aada7bb1`; 생성 자료 CC-BY-NC-4.0 + 비상업 notice, 원 real recording은 M-AILABS 고지 |
| Native music | recording마다 다른 Creative Commons attribution. 전체를 단일 CC 버전으로 묶지 않음 |
| ArtifactBench | v1.0.1, CC-BY-NC-4.0; Fourier 등 자체 학습 자료의 일부 |
| FMA | 학습에 사용한 row별 license filtering·attribution 기록 |
| AIME/MusicGen/Kokoro 등 | 데이터·생성 모델·API 조건을 각 provenance와 source license 기록에서 구별 |

이 표는 데이터 재배포 허가 목록이 아니다. 실제 사용 파일·생성 정보·원 부모의 출처를 원 작업공간에서 보존하며, 경량 저장소에는 오디오와 row-level 학습 manifest를 넣지 않는다. 대회 2차 자료 제출에 필요한 실제 학습 파일 보존 의무도 유지된다.

최종 수상 산출물의 상업·독점 양도 가능성은 기존 기록상 `HOLD_CONDITIONAL_NOT_CLEARED`다. 이 저장소를 정리한 것으로 해당 미해결 상태가 해소되지 않는다. 저장소의 배포 범위는 [라이선스 정책](LICENSE_POLICY.md)에 따른다.
