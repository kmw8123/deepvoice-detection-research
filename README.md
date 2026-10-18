# Deepvoice Detection: Speech, Music, and Mixed Audio

I built this project to detect AI-generated speech and music, including recordings that contain both. The central problem was not just choosing strong individual detectors: their evidence also had to survive source separation, time-window aggregation, and the final whole-file decision.

This repository contains my annotated inference code and an experiment retrospective from the DACON 236749 deepvoice detection competition. My best pipeline combines **music-aware speech adaptation, a four-expert music ensemble, and time-aligned event fusion** (C693). I stopped the research on 2026-09-28. Preparing and editing this archive does not restart training or inference.

Historical identifiers such as `C688` are experiment references, not architecture names. I describe each method first and put its identifier in parentheses; original filenames and code symbols retain their identifiers for traceability.

## How the pipeline works

Each file is processed independently and produces five probabilities: whole-file authenticity, voice authenticity, music authenticity, voice presence, and music presence. A file is considered FAKE if either its voice or music component is AI-generated. Vocals count as voice, while instrumental accompaniment counts as music.

| Stage | Method and purpose |
|---|---|
| Find components and time regions | PANNs estimates voice/music presence, and HTDemucs separates vocals from accompaniment. Presence and authenticity windows are aligned within the same file. |
| Detect generated voice | DF-Arena and Spectra provide speech evidence. For the whole-file decision, I also use a music-adapted copy of DF-Arena's final Conformer block and classifier, sharing the original encoder's intermediate representation (C688). |
| Detect generated music | Two fine-tuned Deezer detectors, Fourier artifact features, a Dasheng classifier, and trained heads on frozen EAT features form the reported music ensemble (C596). |
| Make the whole-file decision | Fixed functions turn voice/music evidence into event probabilities. Each raw-audio or separated-stem path combines its events as `1 - (1 - qVoice) * (1 - qMusic)`; the final File score takes the maximum across those paths. |

The reported Voice score still uses the original speech detector. The adapted speech tail affects only the internal voice evidence used for File. Similarly, the reported Music score and File's internal music evidence are related but are not interchangeable. These output distinctions are explained in the [model card](MODEL_CARD.md).

## What changed, and why

My last substantial improvements came from two specific changes:

1. **Route the music ensemble into the whole-file decision.** The File head previously received a standalone Fourier score through one direct input, even though the pipeline had already computed a richer music ensemble. I replaced that one input with the ensemble score while preserving the other music paths and combination coefficients (C660).
2. **Adapt speech detection to real music without replacing the reported Voice output.** I trained only the final Conformer block and classifier of the speech detector using speech examples and real-music negatives (C688). I then shared the original encoder's representation with that adapted tail and used its raw/stem evidence only inside File (C693). This avoided a second full encoder pass and preserved the separate Voice, Music, and Presence outputs.

Neither change is a claim that adding more models always helps. Many later attempts improved a standalone detector or a training metric without improving the final File ranking. The retrospective records those failures, validation limitations, and implementation errors as well as the successful changes.

## Recorded results

| Result | My recorded server result |
|---|---:|
| Best ADS | **0.8362380952** |
| Overall score | 0.8515229365 |
| CPS | 0.9890865079 |
| Target ADS | 0.85 — not reached |

The shared-encoder, music-aware speech pipeline (C693) and a variant replacing one Deezer model inside File (C704) tied. I preserve the simpler shared-encoder pipeline as the representative implementation. I was in 30th place when I stopped; I have not verified the official final ranking. The overall score is not the ADS.

## Read the code and research

- **[Model card](MODEL_CARD.md)** — Architecture, five output paths, combination formulas, training details, and a method-to-experiment reference table.
- **[Complete experiment retrospective](EXPERIMENTS.md)** — Hypotheses, measured gains and losses, failed approaches, and lessons from the official baseline through music-event bag learning (C753). Its appendix indexes 656 experiment identifiers across 704 directories, not 656 training runs.
- **[Main inference walkthrough](annotated/script.py)** — Start with `run_inference`; comments distinguish final outputs from historical intermediate calculations.
- **[Shared-encoder speech adaptation](annotated/c693_tail.py)** — How one encoder pass supplies both the original detector and the adapted final block/classifier.
- **[Multi-depth EAT readouts](annotated/model/c596_eat/c596_runtime.py)** and **[presence-weighted music aggregation](annotated/model/c239/c239_runtime.py)** — How frozen representations, trained heads, and same-file presence weights form music evidence. All ten Python source files have annotated mirrors.
- **[Reproducibility](REPRODUCIBILITY.md)** — Original package hashes, required assets, and what this archive can and cannot reproduce.
- **[Third-party notices](THIRD_PARTY_NOTICES.md)** and **[license policy](LICENSE_POLICY.md)** — Attribution and restrictions; this project does not have a blanket MIT license.

## Archive contents and limitations

`src/` preserves ten original integration code files byte for byte, plus server-specific requirements. `annotated/` mirrors those Python files with explanatory English comments and docstrings. `notices/` preserves original notices; `provenance/` records hashes and static verification results. `experiment_inventory.json` is a traceability index into my original workspace.

**This is a source and research archive, not a ready-to-run deployment package.** I exclude weights, audio, actual training data, per-file evaluation predictions, feature caches, wheels, full upstream implementations, and the 7.29 GB submission ZIP. The original assets remain in my preserved workspace. Annotation changes do not alter the original submission.

Public development panels were repeatedly used and sometimes contain related source recordings. Their results do not establish independent generalization or predict server ADS. I did not rerun the original models or certify a new Linux/GPU environment for this archive.

## Lightweight verification

```bash
python tools/test_archive_ast.py
python tools/verify_archive.py
```

These standard-library checks verify hashes, complete annotation coverage, Python syntax, relative links, and equality of original/annotated code after removing only module, class, and function docstrings from the syntax trees. Executable statements, constants, and runtime messages must remain identical. Comments and docstrings differ intentionally, so byte identity and docstring introspection are not preserved in `annotated/`. These are static checks, not model-performance tests.

## Distribution scope

I initially archived this work privately on 2026-09-28; the repository was publicly visible when I reviewed it on 2026-10-19. Visibility does not resolve third-party restrictions or grant a new license. Original notices, noncommercial conditions, and the unresolved rights-transfer status remain documented in the [license policy](LICENSE_POLICY.md). Research and automated experiment schedules remain stopped.
