# C693: C660 with the frozen C688 File-only DF-Arena tail

2026-09-24. Research/non-commercial derivative, not a new unrestricted license.
The complete original DF-Arena license is retained at model/df_arena_1b/LICENSE.txt
(relative to the ZIP root). Its original contributions and derivatives retain their
non-commercial restriction. All other C660 model licenses remain unchanged.
Final prize/exclusive-transfer/commercial rights are HOLD, not cleared.

## Change and fixed training

The original DF-Arena weights are unchanged. Its last Conformer block input
is captured during the original forward. A separate trained copy of that block
and fc5 supplies only the internal File voice evidence. The external Voice,
Music and both Presence outputs use the original C660 paths. Existing windows,
Spectra fusion, temporal aggregation and C660 File equation remain unchanged.
No second full 1B encoder forward, evaluation-time fitting or cross-file state.

The C688 final-128-update checkpoint is frozen. It was initialized from the
original DF-Arena last block/fc5, not the unsuccessful C687 trained checkpoint.
43,137,922 parameters were trained; all BatchNorm statistics/dropout stayed in
eval mode. Seed 236749, AdamW 1e-5, two deterministic epochs, no checkpoint
selection. Speech uses 256 existing ASV/MLAAD sources, clean and fixed mixed
views. Native music uses 14 recordings from eight artist groups, all six
raw/stem windows. Native supervision is File=0 only; no component labels were
invented. Speech authenticity proxies are not official competition five labels.

The exact retained workspace paths and SHA-256 pins are in C693_DEPLOYMENT.json
at model/ root: C687_TRAIN_PLAN, C688_TRAIN_RESULT, C688_INPUT_REGISTRY and
UPDATE_128. The plan links the C616 source/audio manifests and C683 source/audio
manifests, full encoded parents, actual consumed waveforms and original license
records. All actual final TRAIN audio, parents, manifests and training code are
retained outside this inference ZIP for stage-two reproduction. Metadata does
not replace the actual audio submission obligation.

## Data attribution and restrictions

ASVspoof: Open Data Commons Attribution License v1.0, original attribution and
README retained in source_licenses. MLAAD-tiny revision
9143e5ea709575ebab6bec52840a1043aada7bb1: generated data CC-BY-NC-4.0 plus
NOTICE_NO_COMMERCIAL_USE; original real recordings retain the M-AILABS notice.
Native music: per-recording Creative Commons attribution is preserved through
the original annotation blocks and source manifests; do not assume one uniform
CC version. These data terms do not grant exclusive ownership of upstream data.

## Validation boundaries

Clean Windows CPU serial audio-to-CSV execution passed; it is not production
same-process Linux/L4/1200-file certification. Selected-error improvements do
not estimate population ADS. Broader public source-proxy100 retained EER/AUC,
and known-component40 retained File EER. Neither .85 ADS nor a server gain is
claimed. Only FILE_FAKE_PROB is intended to change.

C660_DEPLOYMENT.json, MODEL_INFO.txt, MODEL_PROVENANCE.md and SHA256SUMS.txt
elsewhere under model/ are preserved historical C660 records. Current C693
inventory is MODEL_MANIFEST.json plus SHA256SUMS_C693.txt; the latter excludes
itself. Development audio, row labels/predictions and evaluation caches are not
runtime assets and are excluded from this ZIP.
