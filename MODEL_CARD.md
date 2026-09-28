# C693 Model Card

C693 is the representative model I preserve from my DACON 236749 deepvoice detection research. It combines speech and music detectors using fixed formulas. My final improvement connected a small trainable part of DF-Arena to **the decision about whether the whole file is fake**. This repository preserves source code and research documentation. It excludes weights and the actual training audio, so downloading the repository alone is not enough to run inference.

## Results and choice of archived model

| Metric | C693 | C704 |
|---|---:|---:|
| ADS | 0.8362380952 | 0.8362380952 |
| Overall competition score | 0.8515229365 | 0.8515229365 |
| CPS | 0.9890865079 | 0.9890865079 |

These are the server results I recorded. Of the two tied submissions, I preserve the simpler C693 as the representative model and retain C704 as a tied variant. I did not reach my target ADS of 0.85. I was in 30th place when I stopped; I have not independently verified the official final ranking. An overall score of 0.8515 does not mean that ADS reached 0.85.

The competition score is `Score = 0.9 × ADS + 0.1 × CPS`. ADS is `1 − (0.5 × File EER + 0.2 × Voice EER + 0.3 × Music EER)`, and CPS weights the Voice and Music Presence AUCs equally at 0.5 each. Component EER is calculated only on files containing that component. I distinguish source-authenticity proxies on public data from this official ADS. [Official evaluation guide](https://dacon.io/competitions/official/236749/overview/evaluation)

## Inputs and outputs

The pipeline processes each audio file independently and produces five probabilities. FAKE is the positive class. Under the competition definition, the whole file is FAKE if either its voice or music component is AI-generated.

| Output | Meaning | C693 path |
|---|---|---|
| `FILE_FAKE_PROB` | Probability that the file contains a FAKE component | Fixed combination of C688 tail voice evidence and music evidence |
| `VOICE_FAKE_PROB` | Probability that the voice component is FAKE | Original DF-Arena + Spectra on the vocal stem |
| `MUSIC_FAKE_PROB` | Probability that the music component is FAKE | Dual-Deezer/Fourier/Dasheng/EAT combination |
| `VOICE_PRESENT_PROB` | Probability that a voice component is present | PANNs Cnn14 on the original audio |
| `MUSIC_PRESENT_PROB` | Probability that a music component is present | PANNs Cnn14 on the original audio |

The original audio is converted to mono at 16 kHz. HTDemucs separately extracts vocals and accompaniment: vocals feed the voice path, and accompaniment feeds the SONICS music path. Fourier, Deezer, Dasheng, and EAT use the original audio. Window selection and temporal aggregation operate within each file; no adjustment uses statistics, ranks, or predictions from other evaluation files.

## Components and roles

| Component | Role |
|---|---|
| PANNs Cnn14 | Per-window voice/music presence probabilities and their within-file maxima |
| HTDemucs | Vocal/accompaniment separation |
| DF-Arena 1B + Spectra-AASIST3 | Voice authenticity detection on up to six windows of approximately 4.04 seconds |
| C688 tail | A separately trained copy of the original DF-Arena's final Conformer block and classifier; replaces only the raw/stem voice evidence inside File |
| SONICS | Detection on up to twelve 5-second windows from the accompaniment stem |
| C180/C205 Deezer | A 1:1 average of two trained derivatives on the same original-audio windows, aggregated using music presence probabilities |
| Fourier logistic | Classification of a 7,167-dimensional artifact fingerprint from the full original audio |
| Dasheng + C151 head | Classification of the 768-dimensional representation of the 4-second window with the highest music presence probability |
| EAT + C593 heads | Three independent heads classify representations from layers 4/8/12 on up to six 4-second windows |

Each EAT layer representation has 2,304 dimensions, concatenating the CLS token, patch mean, and patch population standard deviation. Each head is `LayerNorm → Linear(2304,64) → GELU → Linear(64,1)`. A sigmoid is applied to the mean logit of the three heads. Window scores are averaged with weights from music presence probabilities in the same file.

C693 captures the final Conformer block's `[B,202,1280]` input once during the original DF-Arena forward pass and passes it to the separate tail. It does not run an additional 1B encoder forward pass. The external Voice output keeps the original model's result; only the voice evidence inside File uses the tail output.

## Main combination formulas

Here, `σ` is the sigmoid, and `L(p)` is the logit of a probability clipped to `[1e-6,1-1e-6]`. DF's fake margin and Spectra's bonafide logit have opposite directions, so they are combined as follows:

```text
λ = 0.69183097
voice_window_logit = (DF_fake_margin − λ × Spectra_bonafide_logit) / (1+λ)
R(z) = 0.75 × max(z) + 0.25 × mean(z)
voice_probability = σ(R(voice_window_logits))
```

The C688 path replaces only the DF margin in this formula. Temporally aligned evidence uses presence probabilities from overlapping PANNs windows in the same file.

The final external Music output combines `D=presence-weighted dual-Deezer`, `F=Fourier`, `H=selected Dasheng`, and `E=EAT` as follows:

```text
M = σ(0.43503136907024 × L(D)
    + 0.26957711906879683 × L(F)
    + 0.03959312199821463 × L(H)
    + 0.2557983898627485 × L(E))
```

File applies the fixed C51 combination function to both raw and stem paths. Each path combines the voice event probability `qV` and music event probability `qM` as `1−(1−qV)(1−qM)`, then File takes the maximum across the two paths. In C660, I replaced C51's direct Fourier argument with the final Music score `M`; in C693, I replaced the raw/stem voice evidence passed into that structure with the C688 tail. The existing triad/aligned music evidence and coefficients remain unchanged. The exact coefficients and operation order are in `combine_c51_file_fake_score`, `combine_c660_file_fake_score`, and `run_inference` in [`src/script.py`](src/script.py).

Two historical details matter when reading the code. Despite the filename `deezer_specnn_official_weights.v1.npz`, the first Deezer weights are a trained C180 derivative. Also, the C346 score and earlier File results are calculated as intermediate values, then overwritten by the final C596/C660 calculations. C29 is loaded and evaluated too, but its final direct coefficient is 0.0. I preserve this historical execution structure in the archive.

## Training lineage

I initialized C688 from the original DF-Arena final block/fc5, without continuing from the failed C687 training checkpoint. I trained only 43,137,922 parameters, keeping the encoder prefix, BatchNorm statistics, and dropout behavior fixed.

The speech data contains 64 sources in each of four ASV/MLAAD real/fake groups, for 256 sources in total. I used a clean view and a fixed music-mixed view of each source. Native music consists of 14 recordings from eight artist groups, with three raw and three stem windows per recording. I assigned only File=0 to native music and did not create Voice/Music component labels.

Each update contains one bag from each of the four speech groups and one native bag. I ran a fixed 128 updates with seed 236749, AdamW at lr 1e-5/wd 0.01, and gradient clipping at 1.0. For speech, I used real/fake-weighted BCE and a SmoothL1 term to preserve the original clean margin. For native music, I applied File=0 BCE to the log-mean-exp of the six window margins. I used the final update without validation-based checkpoint selection.

The existing music path inherits my Fourier/C151 logistic heads, Deezer C180/C205 fine-tuning, and C593 heads trained on frozen EAT. C593 ran for a fixed six epochs/1,650 updates on 4,400 actual views. Its three heads contain 456,579 parameters in total. The [reproducibility document](REPRODUCIBILITY.md) links training sources, exact files/hashes, and the requirement to preserve the actual audio.

## Interpretation limits

My public validation includes repeatedly used panels, related source files, and small source groups. Some source-authenticity proxies do not have the competition's five official labels. I therefore do not add together gains on small public panels to predict server ADS or claim generalization across all sources.

The earlier clean Windows CPU serial audio-to-CSV check is not equivalent to validation of the production Linux/L4 single-process path or its time and memory use over 1,200 files. I preserve the later server scores I recorded and the items still unverified at packaging time as records from different dates. I did not rerun inference, training, or evaluation for this archive.

This lineage includes components and training data subject to research/noncommercial restrictions. I do not consider unrestricted commercial use or exclusive transfer of rights in prize-winning deliverables to be cleared. The detailed scope is set out in the [third-party notices](THIRD_PARTY_NOTICES.md) and [license policy](LICENSE_POLICY.md).
