# Third-Party Sources and Notices

I used publicly accessible pretrained models and external training data in this research. Below, I summarize the source and license records preserved in my original workspace. This repository excludes weights, audio, vendor model implementations, and wheels. Public availability alone does not establish permission for commercial use, redistribution, or exclusive transfer of rights.

The integration code in `src/` also depends on external model formulas, interfaces, and derivative-model lineages. I do not present the Deezer SpecNN reconstruction in `script.py` or the C693/C688 derivatives as unrestricted independent works. Original notices are preserved in `notices/`; their terms take precedence over the descriptions here.

| Component | Source and pinned version | Recorded terms and notices |
|---|---|---|
| DF-Arena 1B | DF-Arena model card, configuration, and provenance in the original package | Upstream MIT portions coexist with research/noncommercial restrictions on original contributions and modifications. Full license text and modification notices are retained. |
| C688 tail | My trained derivative of DF-Arena's final Conformer block/fc5 | Inherits the original DF-Arena terms. I do not claim to have developed the entire original model. |
| Spectra-AASIST3 | [lab260/Spectra-AASIST3](https://huggingface.co/lab260/Spectra-AASIST3), revision `bc0ded888080ddad493177bb53aa6f5b95219d7c` | Apache-2.0. Notices of the local XLS-R configuration and offline-loader modifications are retained. |
| SONICS | [awsaf49/sonics](https://github.com/awsaf49/sonics), commit `9156ffad151f797c71556923c4a02fa01fa8fc91` | Implementation: MIT. The bundled notice's dataset CC-BY-NC-4.0 terms and additional Suno/Udio conditions are preserved separately. |
| Deezer/C180/C205 | [deezer/deepfake-detector](https://github.com/deezer/deepfake-detector), commit `edc94ad04b721e4ba59ccfb25e14606ddaa4a78a` | CC-BY-NC-4.0. Original attribution, modification notices, and noncommercial terms are retained. The current weights are my trained derivatives and do not imply Deezer's endorsement. |
| Dasheng | [mispeech/dasheng-base](https://huggingface.co/mispeech/dasheng-base), revision `d29a721c75b996ffa49e2a1f985349d191a4ae5e` | Apache-2.0. The frozen public backbone is distinguished from my C151 head. |
| EAT | [EAT research repository](https://github.com/cwx-worst-one/EAT), checkpoint revision used: `6eb95936bf1061cacee1c0b89404a1aca9a3c62a` | MIT, Copyright (c) 2024 Wenxi Chen. The original encoder is distinguished from my C593 heads. |
| timm | [pytorch-image-models](https://github.com/huggingface/pytorch-image-models), 0.9.12 | Apache-2.0. The original wheel's license notices are preserved with it; this archive does not contain the wheel. |
| torchvision | [pytorch/vision](https://github.com/pytorch/vision), 0.22.1+cu128 | BSD-3-Clause. Copyright, conditions, and disclaimer notices are retained. |
| PANNs/HTDemucs | Cnn14/HTDemucs assets inherited from the official baseline | Original package attribution refers to notices in an earlier anchor package. Before any future redistribution of the actual assets, I must verify that complete notices for each original source are linked. |

## Included copies of original notices

- [DF-Arena license](notices/DF_ARENA_LICENSE.txt), [DF-Arena modification notice](notices/DF_ARENA_MODIFICATIONS.md), [C693 derivative-model provenance](notices/C693_PROVENANCE.md)
- [Deezer CC-BY-NC-4.0](notices/DEEZER_CC_BY_NC_4.0.md), [original package attribution](notices/ORIGINAL_ATTRIBUTION.md)
- [Spectra Apache-2.0](notices/SPECTRA_APACHE_2.0.txt), [Spectra modification notice](notices/SPECTRA_MODIFICATIONS.md)
- [Complete SONICS notice](notices/SONICS_LICENSE.txt)
- [Dasheng Apache-2.0](notices/DASHENG_APACHE_2.0.txt)
- [EAT MIT](notices/EAT_MIT_LICENSE.txt)
- [torchvision BSD-3-Clause](notices/TORCHVISION_BSD_3_CLAUSE.txt)

These copies connect the source notices to this explanatory repository; they do not mean that the models or data are distributed alongside it. I preserve unverified statuses and relative paths in historical provenance as records of their original state.

## Training data terms

| Source | Distinctions documented in the preserved records |
|---|---|
| ASVspoof | Open Data Commons Attribution License v1.0, attribution, and README |
| MLAAD-tiny | Revision `9143e5ea709575ebab6bec52840a1043aada7bb1`; generated data: CC-BY-NC-4.0 plus a noncommercial notice; original real recordings: M-AILABS notices |
| Native music | Creative Commons attribution varies by recording; I do not assign a single CC version to the entire collection |
| ArtifactBench | v1.0.1, CC-BY-NC-4.0; part of the training data for my Fourier model and other components |
| FMA | Per-row license-filtering and attribution records for the rows used in training |
| AIME/MusicGen/Kokoro and others | Data, generation-model, and API terms are distinguished in their respective provenance and source-license records |

This table is not a list of permissions to redistribute data. I preserve the files actually used, generation details, and source-parent provenance in my original workspace, while excluding audio and row-level training manifests from this lightweight repository. The obligation to preserve actual training files for the competition's second-round submission also remains.

My existing records mark commercial use and exclusive transfer of final prize-winning deliverables as `HOLD_CONDITIONAL_NOT_CLEARED`. Preparing this archive does not resolve that outstanding status. The repository's distribution scope follows the [license policy](LICENSE_POLICY.md).
