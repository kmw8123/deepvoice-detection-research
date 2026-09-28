# Deepvoice Detection Research Archive

This is my source-focused archive of the experiments and best-performing model, **C693**, from the DACON 236749 deepvoice detection competition. I stopped the research on 2026-09-28 and did not rerun training or inference to prepare this archive.

| Result | My recorded server result |
|---|---:|
| Best ADS | **0.8362380952** — C693 / C704 tied |
| Overall score | 0.8515229365 |
| CPS | 0.9890865079 |
| Target ADS | 0.85 — not reached |

I was in 30th place when I stopped; I have not verified the official final ranking. I preserve the simpler C693 as the representative implementation and describe C704 as a variant with the same score.

## Where to start

- **[Complete experiment retrospective](EXPERIMENTS.md)** — I trace the hypotheses, successes, failures, code and validation errors, and changes in direction from the baseline through C753. The final appendix lists evidence paths for 656 C-numbers across 704 directories. These are not 656 training runs.
- **[Best model card](MODEL_CARD.md)** — The separate File / Voice / Music / Presence paths, C688 tail training, and C660's routing of music evidence.
- **[Annotated main inference code](annotated/script.py)** · **[Shared DF tail code](annotated/c693_tail.py)** — Explanatory copies with English comments. A static check compares their executable ASTs with the originals.
- **[Reproducibility and preservation](REPRODUCIBILITY.md)** — The original ZIP, required assets, and why this repository alone cannot run inference.
- **[Third-party components and notices](THIRD_PARTY_NOTICES.md)** · **[License policy](LICENSE_POLICY.md)** — I do not apply a blanket MIT license to the project.

## Included and excluded

`src/` contains ten integration code files copied unchanged from the submission, plus server-specific requirements. `annotated/` contains two main code files with explanatory comments added; `notices/` preserves the original notices; and `provenance/` records hashes of the originals and copies, along with static verification results. `experiment_inventory.json` is a traceability index whose paths are relative to my original workspace.

**I exclude weights, audio, training data, per-file evaluation predictions, feature caches, wheels, and the 7.29 GB submission ZIP.** I also exclude the full upstream model implementations. This repository is therefore not a ready-to-run deployment package. The annotated copies are not byte-identical to the files in the original submission ZIP.

## What the model does

C693 is a pipeline of speech and music specialists with fixed temporal and event aggregation. It shares an intermediate representation from the original DF-Arena forward pass with the C688 tail and uses the trained tail only for the voice evidence inside File. The external Voice output retains the original DF+Spectra combination. The external Music output combines D239/Fourier/Dasheng/EAT, and C660 also routes that evidence into File's direct music input. The final File output is the maximum of the raw-audio and separated-stem event OR scores.

C660 and C693 produced my last substantial improvements by fixing **how evidence already computed by the pipeline reaches the final File output**. Adding individual models that improved on public validation had been less effective. I also record the gains and losses from later attempts and the unmet target in the retrospective.

## Lightweight archive verification

```bash
python tools/verify_archive.py
```

This uses only the Python standard library. It checks file hashes, AST equality between original and annotated code, excluded large assets, and relative documentation links without importing models or running training or inference. It does not validate performance or reproduction in a GPU environment.

## Private archive scope

On 2026-09-28, I chose to keep this GitHub archive in an **owner-only private repository**, [kmw8123/deepvoice-detection-research](https://github.com/kmw8123/deepvoice-detection-research). I have not authorized public distribution or invitations to others. The competition's code-sharing restrictions and third-party asset terms require a separate decision before making it public, with the [official competition agreement](https://dacon.io/competitions/official/236749/overview/agreement) and [schedule](https://dacon.io/competitions/official/236749/overview/schedule) checked at that time. My existing automated research schedules remain stopped.
