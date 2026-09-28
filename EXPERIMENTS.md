# Deepvoice Detection Research: Experiments, Failures, and Final Results

Written: 2026-09-28 · Competition: DACON 236749 Deepvoice Detection · Status: Research concluded; archival retrospective

## 1. Results and how to read this report

My highest recorded server ADS was **0.8362380952**, a tie between **C693 and C704**. C704 made one additional change to the Deezer path, so I chose the simpler **C693** as the representative implementation in this archive. The overall score of 0.8515229365 is distinct from the ADS of 0.8362380952. **I did not reach my target ADS of 0.85.** I was in 30th place when I stopped the research; I have not independently verified the official final ranking.

I compiled this retrospective from the records I retained, from the initial baseline through C753. I did not run new experiments to prepare it. I record why I changed each model, what I actually measured on public data, the server results, counterexamples, implementation and evaluation errors, and why I moved to the next approach.

| Section | Coverage |
|---|---|
| 2 | V1–C349: Initial models, forensic features, File fusion, and expert-model training |
| 3 | C350–C660: Joint File prediction, temporal learning, EAT, validation redesign, and evidence routing |
| 4 | C660–C753: The best C693 model, subsequent regressions, retention training, and the final event-learning approach |
| 5 | Lessons from the full sequence of experiments |
| Appendix A | Original workspace paths and representative evidence for the retained C-number records |

The exact structure, weights, and output roles of my best model are described in [MODEL_CARD.md](MODEL_CARD.md). The annotated code is in [annotated/script.py](annotated/script.py), and the unchanged inference-source copy is in [src/script.py](src/script.py). This repository does not contain the large submission ZIP, model weights, or audio. Read the [reproducibility scope](REPRODUCIBILITY.md) and [third-party notices](THIRD_PARTY_NOTICES.md) alongside this report.

### Distinguishing measurements from records

- **Server scores:** Aggregate values from my retained submission screenshots and the reports transcribed from them. I did not access private evaluation data, per-file predictions or labels, or a live leaderboard while preparing this archive.
- **Public evaluations:** Local development and checking panels built from externally available public data. Crops, codecs, and mixtures derived from the same parent are not independent source recordings.
- **Source proxy:** A metric using a source's REAL/FAKE status as a proxy label. It is not synonymous with official File, Voice, Music, or Presence ground truth.
- **OOF:** Out-of-fold separation applies only to the explicitly named training layer and split. Training a fusion head out of fold does not mean the upstream acoustic model never saw the source.
- **Diagnostic boundary:** An ROC boundary used to explain EER, not a fixed decision threshold added to the submission ZIP.
- **Completed, failed, or prepared:** I distinguish completed training, completed inference, measured improvement, pre-execution errors, rights-related HOLD decisions, and plans that were never executed.

The retained filesystem contains **656 C identifiers across 704 related directories**, with C753 as the highest identifier. This is not a count of completed training runs. The initial V series, investigations, audits, feature extraction, packaging, and abandoned plans also have their own records. The main text covers the decisions that shaped the project; the appendix lists retained paths so smaller trials can also be traced. I have not reconstructed deleted records or newly certified the execution status of every identifier.

### Limitations that remain

I repeatedly consulted public validation results when selecting architectures, so selection bias remains. I did not optimize by reverse-engineering hidden generator proportions from the difference between public and server metrics, and I do not treat a server gain for one configuration as universal generalization. I found and corrected some genuine implementation and preprocessing errors, but I have no evidence that every performance failure was caused by code.

I retained the actual training files, parents, checkpoints, failure records, and best submission ZIP in the original workspace. Neither this report nor a SHA index replaces the obligation to preserve actual training data. Unresolved rights-transfer and weight-redistribution conditions remain unresolved.

## 2. Early research — from the official baseline to C349

I reconstructed this retrospective from the records I preserved for 2026-08-27 through 2026-09-10, focusing on why I changed models, what actually happened, and how I changed direction after failures. C numbers are not training-run counts. Research, data acquisition, implementation audits, formula replay, actual training, and packaging share the same numbering system; a higher number does not mean I ran that many independent experiments. Below, `public` means local evaluation on externally available public material, and `server` means my recorded DACON submission results. I do not treat a public ADS proxy as the same measurement as server ADS.

At that time, public development200 was a mono WAV panel comprising 120 four-second and 80 eight-second examples assembled from 40 sources/10 pairs. Music160 likewise did not contain 160 independent tracks. I repeatedly used the same material to design and select candidates, so even source-group OOF was not a new independent confirmation set. The name `lockbox` also referred to an internal split of a public synthetic panel, not DACON's private evaluation data. I interpret splits subsequently reused or incorporated into training according to their actual status.

Evidence: Section 5, "Gaps in the Development Set Identified Before Speculating About Server Data," in `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`, and the final note in `docs/RESEARCH_RESUME_STATUS_2026-09-06.md`.

### 2.1 Verifiable Server Milestones

I retained the original precision of the early rounded display values. Changes affecting only one output, such as C241 to C349, must be distinguished from Music changes that also propagated into File. ADS changes involving multiple outputs do not let me reconstruct absolute EER for each component.

| Stage | Main submission change | Server total score | Server ADS | Result evidence |
|---|---|---:|---:|---|
| V1 | DF/SONICS Music fusion, probabilistic OR for File | .69332 | .66046 | `docs/EXPERIMENT_RETROSPECTIVE_AND_CLEANUP_2026-09-01.md`, Section 3 |
| V2 | DF+Spectra Voice, SONICS alpha5s Music, MAX for File | .72092 | .69112 | Same document, Section 3; `docs/SOLUTION_V2.md`, Sections 1-4 |
| V3 | Simultaneous changes to selector, pooling, temporal alignment, and gamma120 | .7104943651 | .6795396825 | Retrospective, Sections 3-4 |
| temporal-only | Contemporaneous presence x fake for File | .7182872222 | .6881984127 | Retrospective, Sections 3-4 |
| selector-only | Selection of the highest-scoring PANNs windows | .7186586508 | .6886111111 | Retrospective, Sections 3-4 |
| gamma-only | Raw gamma120 Music | .7062015079 | .6747698413 | Retrospective, Sections 3-4 |
| pooling-only | Voice logit .75max+.25mean | .7226300794 | .6930238095 | Retrospective, Sections 3-5 |
| V5 | SONICS:Deezer:Fourier=2:3:3 | .7966872222 | .7753095238 | Retrospective, Section 11; server runtime 14m29s |
| C2 | Monotone calibrated OR for File | Approximately .80491 | Approximately .78445 | `docs/C2_FILE_FUSION_LEADERBOARD_RESULT_2026-09-02.md`, "Server Results" |
| C2+EnvSDD10% | Fixed probability mixture for File | .8027300794 | .7820238095 | `docs/FAST_LEADERBOARD_PROBES_2026-09-03.md`, results table |
| C2+EnvSDD20% | Fixed probability mixture for File | .7966872222 | .7753095238 | Same document, results table |
| Initial C3 | Aligned File | Execution failed | — | Same document, "C3 Aligned File Fusion" |
| Repaired C3 | Nearest-interval fallback within the same file | .8090943651 | .7890952381 | `docs/C3_ALIGNED_NEAREST_LEADERBOARD_RESULT_2026-09-04.md`, Section 1 |
| C8 | Exposed C3's internal Music event as the external Music output | .8090943651 | .7890952381 | Early retrospective, Section 14; tied C3 at the displayed precision |
| C29 | Added LPC residuals to classical Music features | .8106372222 | .7908095238 | Early retrospective, Section 15; server runtime 19m03s |
| C51 | Direct Fourier/C29 inputs to the File Music head | .8185443651 | .7995952381 | `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`, Section 2 |
| C52 | Reverted File to the C3 family | .8121800794 | .7925238095 | Same document, Section 2 |
| C58 | Added raw/stem Fourier routing to C52 | .8121800794 | .7925238095 | Same document, Section 2 |
| C71 | Raw/stem consensus over short intervals | .8106372222 | .7908095238 | `docs/RESEARCH_RESUME_STATUS_2026-09-07.md`, "C71 Server Results" |
| C159 | 50:50 mixture of Dasheng on a selected four-second segment and final Music | .7992586508 | .7781666667 | `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md`, opening section |
| C190 | Replaced Deezer inside C51 with a further-trained expert | .8265800794 | .8085238095 | `docs/C190_TO_C212_RESEARCH_2026-09-08.md`, Section 1 |
| C212 | Two Deezer models and a small internal role for Dasheng | .8281229365 | .8102380952 | `docs/RESEARCH_RESUME_STATUS_2026-09-09.md`, "Confirmed Server Results" |
| C241 | Presence-weighted Deezer plus raw-audio Voice supplementation for File | .8292157937 | .811452381 | `docs/RESEARCH_RESUME_C241_SERVER_2026-09-09.md`, opening paragraph |
| C349 | Fixed C346 weights for external Music only | .8330729365 | .8157380952 | `docs/C349_C346_MUSIC_ONLY_REPORT_2026-09-09.md`, server-results addendum |

The recorded CPS for the submissions above from V3 onward is .9890865079. Only the approximate displayed value .98908 remains for C2. The early retrospective documents C46 through packaging, and a later audit of server-score changes confirms ADS +.003786 from C29 to C46 and +.005000 from C46 to C51. I have not invented additional digits for the original total-score display to fill the table. The general limitations of the server evidence are that these are my recorded server results, without separate per-file predictions, labels, or SHA hashes identifying the server uploads.

Evidence: Section 1, "Which Outputs Moved the Score," in `docs/SERVER_SCORE_CHANGES_AND_NEXT_MODEL_EVIDENCE_2026-09-10.md`.

### 2.2 V1-V3: I First Learned About Model Roles and Temporal Aggregation

The official baseline used PANNs for Voice/Music presence, HTDemucs for component separation, and DF-Arena1B for authenticity. In V1, I added the Music expert SONICS beta5s, but mixed accompaniment DF and SONICS with equal logit weights without supporting evidence, and also included raw-audio SONICS in File OR. The server run succeeded, but ADS was .66046. With CPS already .98908, the remaining possible total-score gain from CPS was only about .0011, which led me to prioritize authenticity.

For V2, I separated the inputs and the experts' roles. I removed the voice-oriented DF path on accompaniment and the auxiliary raw Music path, and applied SONICS alpha5s to accompaniment. For Voice, I combined DF and Spectra-AASIST3. On public scores for 2,001,847 utterances across 17 domains, macro EER was 3.5359%/1.4461%/.9266% for DF/Spectra/the fixed combination; leave-one-domain-out fusion achieved .9871%. I chose the coefficient .6918309709189366 from these public data. However, this validated public first-window scores on raw audio; it did not replace waveform experiments involving Demucs, telephone channels, singing, or mixtures. I returned File to the official MAX rule, and server ADS reached .69112.

In V3, I implemented four hypotheses at once: missed short utterances, false positives from max pooling, multiplication of presence/fake peaks from different times, and a long-context Music model. The changes were the top four PANNs windows plus two endpoint windows, Voice .75max+.25mean, contemporaneous File fusion, and raw SONICS gamma120. Server ADS fell to .6795396825, so I separated the changes. Of the four ablations, only pooling improved ADS, to .6930238095, and became the subsequent baseline. Padding 4-60 seconds to gamma120's 120-second input might have caused it to interpret fake speech in raw audio as Music, but I cannot present that explanation as a cause established by server evidence.

In a later pooling audit, the EER difference between the minimum at .63 and the implemented .75 was .002419 percentage point, and regrouping moved the optimum between .61 and .77. The more important correction on September 10 was that this experiment used synthetic pseudo-files assembled from independent utterance scores. It was not inference on actual adjacent windows, Demucs outputs, telephone audio, or partial fakes. The earlier description of equally weighted scenarios also differed from the actual 40/30/30 weighting. I preserved the .75 implementation that had worked on the server, while withdrawing the claim that it was a universally optimal coefficient.

Evidence: `docs/SOLUTION_V1.md`, Sections 2-5; `docs/SOLUTION_V2.md`, Sections 2-4; early retrospective, Sections 4-5; the full `docs/VOICE_POOLING_EVIDENCE_SCOPE_CORRECTION_2026-09-10.md`.

### 2.3 Exploration Around V4 and V5: Diversity Among Music Experts Produced the First Major Change

An ArtifactNet preparation folder named V4 exists, but it would be incorrect to describe V4 as an actually promoted and submitted version. Raw ArtifactNet achieved pure-music macro EER .10/AUC .9625, but weakened to EER .25-.325 on wideband speech mixtures and .325-.375 under a telephone approximation. Applied to Demucs accompaniment, it achieved pure-music EER .05 yet output at least .5 for all 20 speech-only accompaniment examples. This showed that accompaniment separation could introduce new artifacts and speech leakage. Replacing raw Music improved macro EER from .510417 to .368056 relative to SONICS, but failed the absolute and telephone-condition gates. Fixed/conditional fusion produced zero additional EER improvement. Temporal median had an overall figure of .15, but zero crossfit EER improvement.

Combining SONICS alpha/beta/gamma improved macro EER from .443743 to .414730, while worsening AUC from .601166 to .582602 and micro EER from .439803 to .450329. I also investigated publicly available external Voice models, but lacked sufficient evidence on licensing, execution paths, size, or complementarity. I later measured SONAR on 300 actual examples, obtaining AUC .570044/EER .466667, but numerical equivalence of the fairseq-to-Transformers conversion remained unconfirmed. I therefore cannot generalize that result into a performance failure of the official model as a whole.

I trained V5's Fourier model myself, separately from the public fakeprint checkpoint I had rejected earlier. From 620 sources—300 public fakes plus 320 rights-filtered real sources—I produced 6,696 rows of duration/codec variants with 7,167-dimensional features and selected logistic C=.01 using six source-separated folds. Standalone OOF provider-condition macro EER/AUC was .163649/.883275. I exported Deezer SpecNN's official older checkpoint to pickle-free NPZ and reproduced its offline inference path. I selected a 2:3:3 logit combination of SONICS accompaniment, Deezer raw-audio spectra, and Fourier raw-audio residuals through grouped/nested validation over 620 public sources x four conditions/2,480 rows and 184 prespecified candidates.

Public macro EER improved from .264171 for the existing SONICS model to .151980 for the triad, with nested stitched EER .163324. MUSAN source-shift EER also improved from .254444 to .165000, and fold-macro EER on 120 actual clean Demucs examples improved from .25 to .116667. Server ADS increased from pooling's .6930238095 to V5's .7753095238, a gain of +.0822857143 and the largest early jump. Pairwise model-score correlations of .3325-.5282 and different input representations provided public evidence of complementarity, but they do not let me causally allocate the gains between Music and File.

This phase also included mistakes that I caught before training with incorrect provenance. I initially treated ArtifactBench shard044 as actual REAL material, but it contained 17 Udio AI rows, so I quarantined it. I generated the material only after fixing the FMA materializer's shard/generator/REJECT handling and its assumptions about the actual ZIP geometry. These were data and implementation errors, distinct from performance failures. I preserved the files actually used in final training along with their parents and variants; manifests do not substitute for submitting the actual files.

Evidence: early retrospective, Sections 6-8 and 11; `research/c369_early_candidate_failure_audit/C369_EARLY_CANDIDATE_FAILURE_AUDIT_2026-09-10.md`, Section 2.

### 2.4 C1-C13 and v7-v25: Better File Fusion and a Shift Toward Early Testing

After V5, I compared C0=official MAX, C1=untrained soft OR, and C2=nonnegative calibrated OR on the public 200-example panel. File EER was .1851648352/.1703296703/.1554945055. C1 failed the AUC, sequential-condition, and bootstrap criteria; C2 failed the strict promotion criteria because its bootstrap result was .7438964844 and its worst-cell deterioration was .05. Nevertheless, a limited C2 server test improved ADS to approximately .78445. This illustrated that a small development set's gates could not perfectly judge server generalization; it did not justify retroactively changing the gate to PASS.

C3 used both global evidence and temporally aligned evidence within the same file. The initial evaluator required feature schema2 although the actual features used schema3, so it could not run C3. I left the frozen receipt at `c3_available=false` and performed a separate post hoc diagnostic. File EER improved over C2 to .1296703297, but sequential/temporal macro EER worsened from .15 to .20 and the bootstrap result was .89990234375, so the research gate failed. The first server run terminated with `C3 found no interval overlap`. I added a deterministic fallback: when no windows overlapped, it chose the nearest window within the same file by interval gap, then center gap, then original index. I kept the coefficients unchanged. The repaired version's server ADS of .7890952381 confirmed both recovery from the execution error and the resulting performance.

I expected EnvSDD to supply new authenticity evidence from environmental sound, but preparation involving CPython, Torch, loaders, file access, and ABI issues became protracted. AudioMosaic also depended on that follow-on path. Static preparation across multiple versions or a successful import does not count as model training. The C2+EnvSDD .10/.20 weights were exploratory values fixed in advance, not optimized on public data, and both reduced server ADS, to .7820238095/.7753095238. I ended further alpha searches and stopped EnvSDD/AudioMosaic. From September 3, I explicitly adopted the approach of testing one actual audio file and then a small batch before further development.

I distinguish the subsequent small candidates as follows.

| Candidate/hypothesis | Actual public result | Scope of the conclusion |
|---|---|---|
| C4 added raw Voice features | File EER .1296703→.1445055 | Reusing the same raw information as new File-correction inputs failed |
| C5 separated Music experts into independent inputs | Music .30→.2875, File .1296703→.1445055 | Component improvement did not survive as a File gain |
| C6 WavLM-OC supplementation | File/Voice EER tied, only a small AUC increase | Weak error complementarity; I did not search coefficients again |
| C7/C8 exposed events as external component outputs | C7 Voice .05→.075; C8 Music .30→.2625 | C8 was isolated post hoc after C7 and failed the strict gate; tied C3 on the server |
| C9 conditional Music | Music EER .30, worse than C8's .2625 | I stopped adjusting conditions on the existing 200 examples |
| C10 equal-weight logit mean of C8/C5/V5 | EER .275, AUC .78015625 | Only the AUC gain remained; a three-way average is the exact formula |
| C12 event max | File .1296703→.1445055 | No gain from recombining existing scores |
| REAL-only PPCA32 | Fit on 226 actual REAL examples, small24 EER .5/AUC .486111 | Execution succeeded, but the signal failed |
| C13 CQT-Cepstrum CNN | small40 EER .35, C8 .20 | I actually rejected it after confirming it was a different model from the early linear Fourier model |
| AFSS/QAMO | RADAR24 EER .5/.5, respectively | Actual strict-load and forward passes succeeded; small-panel performance and rights limitations remained |
| AntiDeepfake-Small | RADAR24 .25, ITW20 File .40 (C2 .30) | I do not generalize this ITW figure into Voice-authenticity performance |
| EfficientAT presence | 2,212-row CPS .9888334505→.9882881955 | It completed after the initial ABI preparation failure; I kept PANNs |

A later audit identified an important target-interpretation error for Nes2Net-X. All Voice in ITW20 was REAL, and the FAKE file labels came from Music. File EER .50 was an actual result, but Voice EER was undefined because there was only one class. I corrected the interpretation that had expanded this into a "Voice generalization failure." RADAR24 EER .25 and rights issues remained separate weaknesses. Nor did this reject the entire idea of reusing raw Voice. Later, C232 obtained some gains through a different combination: taking the maximum of existing raw/stem event probabilities.

Evidence: `research/v6_file_fusion_itw/FULL_400_V4_2_DEVELOPMENT_RESULT_AUDIT_2026-09-02.md`, Sections 6-8; `docs/FAST_LEADERBOARD_PROBES_2026-09-03.md`; `docs/C3_FOLLOWUP_AND_C8_NEXT_SUBMISSION_2026-09-04.md`; `research/v22_c3_residual_scout/C10_MUSIC_FIXED_LOGIT_CONSENSUS_DECISION_2026-09-04.md`; `research/v17_afss_fast_probe_v0_1/AFSS_FAST_PROBE_REJECTION_2026-09-03.md`; `research/v18_qamo_fast_probe_v0_1/QAMO_BATCH24_STOP_2026-09-03.md`; `research/v19_antideepfake_small_fast_probe_v0_1/ANTIDEEPFAKE_SMALL_FAST_GATE_DECISION_2026-09-04.md`; C369 audit, Sections 1-3.

### 2.5 C26-C52: Small Forensic Features Worked, but Their Fusion Path Mattered

Phase/coherence features (C27) showed a signal, improving standalone Fourier EER from .326389 to .298611, but replacing the full triad worsened EER from .215278 to .229167. I fixed the initial allfit-score leakage and cross-fold pair-statistics issues, and additional actual exploratory evaluations exist even after the sentinel stop. C28 multiscale292 improved overlap EER from .55 to .35 and tied clean EER at .50, but I stopped it under the criteria then in force because clean AUC fell from .545 to .4975. Describing either candidate as unexecuted or entirely without signal would erase these partial results.

C29 was a logistic head over 441 dimensions of LPC prediction residuals at 16/8/4kHz. It read the central four seconds; it did not process every window across an entire file. Its first-fold clean/overlap EER was .40/.35, and independent fold1 EER was .2450/.2236. A fixed 50:50 logit combination with Fourier improved fold1 clean EER from .1168 to .0955 and overlap EER from .1382 to .0955, but was worse than C29 alone on fold0. I trained the final head on all 620 sources x clean/overlap=1,240 actual inputs. Server ADS reached .7908095238, +.0017142857 over C3.

For C46, I compared alpha {0,.25,.5,.75,1} across 10 cells in public source-held folds1-5 rather than fitting weights to server scores. Alpha .25 had macro EER .1476381254, lower than .50's .1607864302, so I fixed Fourier at .75 and LPC at .25. This was OOF evidence for the classical slot, not an EER for all of Music160 or the server. Of the 10 cells, six improved, two tied, and two worsened.

C31-C34 were successive hypotheses that learned residuals from C3's temporal shape, ranking, and EER boundary without adding an encoder. C31 improved temporal-partial File EER from .283333 to .216667, but worsened overall EER from .1296703297 to .1406593407. C32 shape-only ranking residuals, C33 boundary-weighted ranking residuals, and C34 EER-boundary residuals all tied overall EER at .1296703297. Although AUC increased slightly, temporal-partial EER worsened to .30 for C33/C34. All four candidates were marked `STOP_NO_RECOMMENDED_SUBMISSION_ZIP`; learning temporal structure must be distinguished from improving overall EER. The evidence is in `c3_outer_oof`, `candidate_outer_oof`, and `status` in the `*_PUBLIC_DEVELOPMENT_RESULT.v1.json` files under `research/v31_temporal_c3_residual_probe/`, `research/v32_temporal_c3_shape_rank/`, `research/v33_temporal_c3_boundary_rank/`, and `research/v34_temporal_c3_eer_boundary/`, respectively.

I also ran the following alternatives during this period. C30's frozen SONICS384+Deezer128 representation reached an actual stopping result after I worked around a Windows selector error: clean/overlap EER .416667 and overlap AUC .569444. C35 multi-crop LPC worsened Music from .35 to .3625. Direct-to-File LPC in C36 and direct-to-File Fourier in C37 each produced EER .3703296703 on their respective public 200/200 splits. C38's MERT-v0 mean+std1536 head had overall EER .375; C39's small logmel CNN overfit, with held EER .55 despite training accuracy near 1. C40 Sara wav2vec2 saturated near spoof1 on most examples and had 24-row EER .416667. C41 CLAP failed the gate with overlap EER .35. C42, a public GTZAN/Suno CNN, failed with AUC .333125/EER .625, and I did not arbitrarily reverse its sign. C43 SONAR was the same checkpoint that had already failed, so I did not rerun it. C44 Eliya Base had RADAR24 AUC .958333 but EER .166667, weaker than the existing OC's .083333. I stopped C45 Echoes before training because it had zero REAL audio files, incomplete reference mappings, and incomplete rights documentation. C47's renewed search ended without downloading or inference because the results were the same failed/HOLD candidates or lacked sufficient evidence for an executable path.

C48 investigated the mismatch caused by retaining old C3 File coefficients after changing Music scores in C46. File EER improved from .1703296703 to .1554945055, but I held it because the bootstrap result was .383301. C49's direct six-input File experiment mistakenly compared against C3 instead of the intended C46. Correcting the reference to C46 still left the candidate worse at EER .189011, so the error did not conceal a successful model. C50's eight-input plan was blocked because execution prerequisites depended on a report SHA/size that kept changing. I canceled it after C51, with zero fits and zero EER evaluations. I record it as unevaluated, not a performance failure.

C51 passed five logits to the File Music-event head: C46 global Music, presence, aligned Music, raw Fourier, and raw C29. Public File EER improved from .1703296703 to .1445054945, with bootstrap .6154785156. The final direct C29 slope was 0, but C29 remained inside global/aligned inputs. The main change was feeding raw Fourier directly to File so that its evidence was not weakened by prior fusion with other Music experts. Server ADS .7995952381 made C51 the new reference point in this lineage. In contrast, C52 returned File to the three-input C3 method and also returned its File-side classical input to raw Fourier, worsening server ADS to .7925238095. Describing it as an "improvement that preserved C51" was inaccurate; it changed several existing information paths.

Evidence: early retrospective, Sections 14-16; `research/c369_early_candidate_failure_audit/C369_EARLY_CANDIDATE_FAILURE_AUDIT_2026-09-10.md`, Sections 4-5; `research/c370_c29_c51_retrospective/C370_PROMISING_CANDIDATE_CODE_AUDIT_2026-09-10.md`; `submission_c51_uncompressed_file_music_src/C51_SUBMISSION_HANDOFF_2026-09-05.md`; `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`, Sections 2-3.

### 2.6 C53-C159: A Small Development Set, Dilution of New Scores, and Validation/Submission Mismatches

This phase branched into temporal Fourier, component calibration, local raw/stem consensus, presence/layout routing, raw Spectra/Voice supplementation, Music resolution, stem-leakage mitigation, LBP texture, and related ideas. Each number must not be counted as a newly trained large model. Many C61-C88 hypotheses changed the arrangement and fusion of existing scores, intervals, and features. C71/C75 retained public File gains, but their bootstrap evidence was weak. I reconsidered and packaged C71 after exact Fourier vectorization delivered roughly a ninefold speedup for 30 calls over 60 seconds. Public File EER improved from .144505 to .114835, but server ADS .7908095238 was below C51.

C58 tied C52 on the server, yet public cache replay changed all 200 File probabilities, with maximum difference .27569 and 539 changed ranking pairs. There was no evidence of a disconnected-path bug. The actual problem was a contract mismatch: research retrained the head for routed inputs, while the ZIP used the old C3 coefficients. Even after I aligned the procedures in C108, music-event rankings on new sources were identical to oldC58, so I obtained no basis for a corrected resubmission. I acknowledge the research/deployment mismatch without claiming it was the sole cause of the server failure.

LBP472 (C95) improved mean EER across six providers x two views from .228753 to .186764. Codec, duration, and overlap augmentation to 7,316 views (C100) improved the six-provider x three-view result from .222400 to .173016. However, applying it to the actual 200 examples in C101 improved classical EER from .2875 to .2625 while leaving final File/Music EER unchanged. Using it as a direct sixth File input in C102 changed all 200 probabilities and corrected 56 erroneous pairs, but broke 52 new pairs, leaving the EER-point counts at FP10/FN19. An approximately .0386 upper bound on LBP's logit sensitivity through multiple fusion stages, together with global/aligned Music correlation .9563, provided structural evidence of dilution and redundancy. Nevertheless, LBP AUC on all 160 music-present examples was .493750, so I could not blame fusion alone.

C90 expanded the training panel for the same target to 400 rows, worsening File EER from .1445055 to .1554945. Partial/local training in C114/C118/C120, added LPC sources in C125, direct LBP File in C126, and Deezer128 head transfer in C130 also failed to secure a final gain. In particular, C131 worsened the existing Music160 result from .325 to .475, while C132 improved a separate 64-example panel from .315341 to .223011. I did not let a good result on a new panel conceal the collapse on the existing mixture conditions. Independent File in C134, REAL-only modeling in C135, nonlinear Music in C137, and training on new REAL sources in C138 produced no overall EER improvement either.

C159 applied frozen Dasheng plus my C151 head to a four-second segment selected by PANNs, then averaged it 50:50 with final Music. Public Music160 improved from .325 to .2875, and a separate Music source proxy improved from .315341 to .184659. However, these were not 160/64 independent sources; mixture and some source conditions worsened, and the 95% bootstrap interval included 0. Server ADS was .7781666667, -.0214285714 relative to C51. Assuming the other four outputs were preserved, this implied approximately .0714285713 deterioration in Music EER. I recorded this as a failed submission recommendation that confused successful execution with successful generalization, and did not follow it with a simple alpha adjustment.

Evidence: `docs/RESEARCH_RESUME_STATUS_2026-09-06.md`; `docs/RESEARCH_RESUME_STATUS_2026-09-07.md`; `docs/C51_FUSION_AND_RESEARCH_DIRECTION_AUDIT_2026-09-07.md`, Sections 2-5; the first two sections of `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md`.

### 2.7 C162-C241: I Trained Experts on Actual Material and Changed Where I Used Them

After C159, I concluded that repeatedly training heads on frozen representations was insufficient and trained Deezer's final convolution plus dense/output layers. C166 on existing material, C169 with 60 additional MusicGen sources, C174's Fourier+LPC source expansion, and C178's fixed average failed to beat C51 on the full public evaluation despite some held-out gains. Changing segment aggregation from mean to max in C171 improved Music160 from .425 to .3625 and sequential EER from .30 to .15, but worsened overlap from .50 to .55 and introduced false positives on new sources. Both dilution of temporally short fakes and REAL false positives from maximum aggregation were present.

In the 16-example, volume-controlled C175 experiment, Music scores moved when I changed the speech over the same music. Based on that evidence, I added synthetic speech symmetrically to both REAL and FAKE music. I generated Kokoro stock8 and created 764 music examples x two channels=1,528 actual files. C180 performed actual tail training with train3,690/held766. It improved oldheld500 EER from .32393 to .28405 and newheld266 from .39097 to .34580, but public Music160 EER .3875 was weaker than C51's .325. The signed mean effect of speech replacement decreased, but the mean absolute effect worsened from .09035 to .11551, so I did not claim invariance. C181, which fed only Demucs accompaniment to a model intended for raw audio, also worsened proxy EER from .375 to .75.

The turning point came from replacing an existing expert's internal role rather than giving a standalone model a final 50% blend. C190 replaced Deezer within the C51 structure with the augmentation-trained C180, preserving direct Fourier and temporal information, and reached server ADS .8085238095. C205 trained for nine additional epochs on the same 3,690 examples, improving held766 EER from .3093 to .2259. However, its standalone replacement in C208 improved Music from .300 to .2875 while worsening File from .1445 to .1555. C210 averaged C180/C205 probabilities equally within the same window, while C209 tested a small Dasheng role in the indirect C29 slot. C212 actually combined both changes, achieving Music .25, File OOF .140659, and server ADS .8102380952. Effective logit weights were SONICS25%, dual Deezer37.5%, Fourier28.125%, and Dasheng9.375%, while direct File C29 was preserved.

Deeper convolution training in C211, local-label training in C222, telephone Fourier in C223, and ranking losses in C226/C228 did not secure EER improvements. C229's volume normalization worsened File. C231's denser Fourier sampling produced some File gains at the cost of Music worsening from .25 to .275. C238's 81-dimensional head over neural-codec reconstruction and token summaries was weak, worsening held64 from .21875 to .46875. I retained the records of actual training and performance failure without expanding those approaches substantially further.

C241 combined C239, which weighted the Deezer window average by PANNs Music-presence probabilities, with C232, which used the larger of the existing raw-audio/separated-Voice events for File only. Public Music160 improved from .25 to .2375, sequential Music from .20 to .10, and File200 from .140659 to .129670. The separate File16 panel tied at .25, and the 95% bootstrap interval included 0. There was no evidence that the individual File improvements added together in the combination. Server ADS improved slightly to .811452381, with runtime 26m02s.

Evidence: follow-on completion sections in `docs/C159_SERVER_FAILURE_AND_RESTART_2026-09-08.md`; `docs/C190_TO_C212_RESEARCH_2026-09-08.md`, Sections 3-7; `docs/RESEARCH_RESUME_STATUS_2026-09-09.md`; `docs/C241_RESEARCH_AND_SUBMISSION_2026-09-09.md`.

### 2.8 C242-C349: After Repeated Failures in Further Training, I Separated External Music Fusion from File Fusion

After C241, I actually examined source-paired JS, provider balancing, deeper CNNs, codec augmentation, expanded sources/temporal crops, MuQ/MERT/PANNs/Spectra representations, SONICS adaptation, REAL-only density, nonlinear heads, and longer temporal observations. The table below lists representative results for which the baseline and comparison scope were established. All are public results; I do not average numbers across different rows or add them together as an expected server gain.

| Attempt | Actual observation and reason for stopping |
|---|---|
| C246/C249 paired JS | held766 EER tied at .225889; final Music/File on 280 actual examples also tied |
| C248 removed the presence column | old File .129670→.114835, but separate File16 worsened .25→.291667 |
| C245 codec-token histogram | held64 .21875→.53125; the small representation failed |
| C251 MuQ source expansion | TRAIN3690/held766, EER .276809 (C205 .225889); only some MusicGen complementarity remained |
| C255 MuQ direct File | held File .264915, transfer to old200 .429670; performance was insufficient even if target-specific heads were needed |
| C265/C267/C278 MuQ MLP, regularization selection, and RBF | MLP .302823, RBF .289816; TRAIN-only regularization selection also retained C=.01 |
| C269/C272 SONICS tail | raw held .468590→.349938, but final File worsened .129670→.144505 |
| C274/C276/C277 | Tested the last two convolutions, new MusicArena32, and 2,524 temporal crops, respectively; held .232392/.232392/.245399, all weaker than the .225889 baseline |
| C285 residual CNN from scratch | held .484295; training improvements did not transfer to source generalization |
| C290 REAL-only SpecNF | Four epochs over 1,734 REAL views, held .398160; claims of normal density modeling or paper reproduction were also limited |
| C291 MP3/Opus augmentation | TRAIN7380, original held .225889→.238896; expanded codec held .224540→.231043 |
| C293/C297 SONICS stem/full fine-tuning | Small stem panel held EER tied at .5; full fine-tuning held64 .46875, weaker than C205 .21875 |
| C294/C295/C299 representation diagnostics | PANNs .40625; Spectra's final 160D tied at .21875 but had the same ranking as its original scalar; six intermediate layers .46875 |
| C301/C330 REAL source expansion | After adding 73/65 tracks, held .232392/.235091; simply adding material did not help |
| C331/C334/C344 | Nine more epochs on the same material .232392, BN-statistics correction .267608, matched SAM .229694 versus PLAIN .225889 |
| C329 MERT-v1 | held64 .4375; I actually tested a different checkpoint from the earlier v0, but it was weaker overall |
| C335/C338 dense Deezer | Despite standalone .235385→.202564, final Music tied; aligned/event paths worsened or only recovered |
| C336/C339 continuous four-second context | Replaced the existing six .78-second windows with four continuous seconds; both unadapted and lightly adapted versions had held64 .25, weaker than baseline .21875 |

Implementation corrections from this period must also survive the retrospective. In C269, I discovered before fitting that the smoke test omitted the original SONICS normalization by standard deviation after padding, so I regenerated the cache. C274 was not a training failure; JSON saving failed on a single-class NaN, and I recovered the report from saved predictions. In C295, all features differed and replay matched the original logit, but the top two principal components of the TRAIN representation explained 97.02%, so the new head did not actually create a new ranking. I also retained C334's BN-shape and JSON errors, but the conclusion remained that performance worsened after correct computation. Treating earlier "preparing" or "running" statements as more authoritative than the final failure records would lead to duplicate experiments.

The final change was C342/C346, where I retrained the already-changed S/D/F/H weights on public material rather than adding another expert. C342 nested OOF failed: Music160 worsened from .2375 to .2625 and File200 from .129670 to .144505. However, a signal of four ties and one improvement across held-fold Music results led me to allow the limited post hoc transfer diagnostic C346. On Music160, I used five equal folds and lambda {.01,.1,1}, selecting lambda .1 by minimum mean EER with stronger regularization as the tie-break, then fitted once on all 160 examples. Fixed S/D/F/H weights were approximately 0/.4752857123/.3127043354/.2120099524. These 160 examples had now become actual coefficient-training material, so I do not report them as independent performance evidence for the final head.

Transfer of the frozen weights improved Music-source EER on C254128 from .21875 to .1875, on novel64 from .235384615385 to .124102564103, and on C14916 from .375 to .25. However, C254 short-partial tied at .4375, and two of eight source blocks worsened. EER0 for novel 45-second audio came from only 10 rows: three REAL and seven FAKE. Actual File16 on C149 tied at .25, while its Music-event proxy worsened from .25 to .375. C254's actual durations were 32 four-second and 96 twelve-second examples, correcting the earlier four/eight-second description. Shared parents also existed between novel/C149 and C254, so these cannot be called 208 independent sources.

For that reason, C349 computed only the external `MUSIC_FAKE_PROB` with the new weights and kept C241's original global/aligned Music values for File. Although SONICS had nearly zero weight in external Music, I did not remove the SONICS path inside File. I chose this scope after viewing public results; it was not independent confirmation. I built a 6.23GB ZIP after actual serial CPU validation from all models through CSV and exact-preservation checks for the other four outputs. The server runtime was 25m46s, and ADS .8157380952 was approximately +.0042857142 over C241. This was a practical example of why the best external Music weights did not have to be transplanted unchanged into File. It remained below my target of .83 at the time, and I continued the research.

Evidence: the individual completion sections in `docs/RESEARCH_RESUME_C241_SERVER_2026-09-09.md`; "Public Results—Preserving Both Improvements and Counterexamples" and the server-results addendum in `docs/C349_C346_MUSIC_ONLY_REPORT_2026-09-09.md`.

### 2.9 Interpretations I Need to Preserve from This Period

My largest early gains came from V5's independent Music observations, C2/C3's File fusion, C51's direct Fourier input, C190/C212's trained experts and their internal roles, C241's observation intervals, and C349's separate fusion by output. Conversely, improving a new model alone did not guarantee improvement in the final combination, and a larger file count was not the same as more independent sources. New probabilities could reach the actual CSV while EER stayed unchanged; I did not automatically interpret that as a disconnected-path bug.

The early name `telephone_g711` did not mean an actual 8k telephone band. Original development200 performed only 16kHz PCM mu-law encoding/decoding. I must report it separately from the later true8k panel; it does not establish generalization to real telecommunications networks. The public 17-domain Voice scores also do not represent two million preserved WAV files or actual mixture validation. Preserving the distinctions among code errors, rights/reproducibility stops, unevaluated plans, actual performance failures, partial signals, and limited submission successes is what makes this record of trial and error reusable.

Evidence: `docs/DEVELOPMENT_CHANNEL_SEMANTICS_CORRECTION_2026-09-10.md`; `docs/VOICE_POOLING_EVIDENCE_SCOPE_CORRECTION_2026-09-10.md`; `docs/PAST_EXPERIMENT_IMPLEMENTATION_AUDIT_2026-09-10.md`; `docs/SERVER_SCORE_CHANGES_AND_NEXT_MODEL_EVIDENCE_2026-09-10.md`.

## 3. C350–C660 — carrying model improvements through to the final File decision

During this period, my central question shifted from “Which detector should I train next?” to “Where do the detection signals I already have disappear before the final decision?” Starting from C349, I tested a joint File classifier, voice-model adaptation, broader music sources, partial-fake training, temporal attention, EAT representations, and larger models. Many candidates that completed actual training and public validation still tied or regressed in the final combination. Ultimately, C660 added no new neural network: I changed one input through which existing music evidence reached File, raising my recorded server ADS from C596's 0.8174523810 to 0.8274523810.

The public EER values here are generally **development metrics using the authenticity of a music or voice source as a proxy label**. They are not equivalent to competition metrics with confirmed component labels for both vocals and accompaniment, official ADS, or server performance. The meaning of `OOF` also depends on which model excluded which source units. I distinguished validation in which the entire acoustic model had not seen the evaluated sources from validation in which only a combiner over fixed acoustic scores excluded those sources during training. Even a large panel can consist of repeated transformations of the same parents, so I report both row counts and actual source counts below.

### 3.1 C413: A Good Small Joint Classifier Was Not Sufficient Evidence to Replace the Existing Structure

After C350, I tried to reduce File errors that remained despite C349's improvements to the external Music output. After several combinations of global, temporal, and voice-event evidence, C412 became a 12-coefficient model that jointly learned voice and music events from 10 fixed features. I retained Voice and Music BCE and replaced only File BCE with pairwise logistic ranking balanced by class and source. This did not directly optimize discontinuous EER; it was a ranking objective encouraging a higher File score for FAKE than for REAL.

The public200 panel comprised 10 source pairs × 20 transformations from 40 parents: 20 ITW voice sources, 10 MUSAN-RFM real music sources, and 10 ArtifactBench generated music sources. The fake music included Udio, MusicGen Large, two Suno tags, and Riffusion. I constructed component-only, simultaneous-mixture, sequential, and 4+4-second two-phase conditions in wide and 16k μ-law forms. Within each outer fold, there was no overlap in music or voice parent SHA between the 160 training rows and 40 evaluation rows. This did not establish complete independence of speakers, composers, or upstream pretraining, nor did it remove selection bias from repeatedly choosing methods on the same 200 rows.

C412's source-pair OOF File EER improved from C349's 0.129670330 to 0.114835165. It tied at 0.25 on an actual small16 panel and improved from 0.50 to 0.25 on a separate8 panel. However, the 95% interval for improvement from resampling the 10 source pairs as clusters ranged from −0.022609890 to +0.078021978 and included zero. Across the OOF predictions, it corrected 10 errors but introduced 7 new ones, and one source pair worsened from EER 0 to 0.109890. The improvements on the small panels were measured, but the evidence for broad generalization was weak.

For the C413 submission, I attached the Nes2Net/WavLM singing model and this joint head to the original C349 and **replaced only the external File output**. An execution audit confirmed that the new values reached the actual output. However, the new affine head did not preserve exactly the same structure as C349's aligned Voice/Music evidence, which summarized authenticity and presence at the same time positions, or its hard-max over raw/stem events. It would also be inaccurate to say that Fourier and global Presence disappeared entirely. Those features remained, but event inputs, the training objective, score scales, and nonlinear aggregation changed together.

My recorded server result was ADS **0.8003809524** and total score 0.8192515079, an ADS decrease of 0.0153571428 from C349. This failure showed that the wholesale replacement selected on public data did not transfer to the server; it was not evidence that “Nes did not run.” It did not reveal the server's hidden generators or mixture proportions. From that point on, I assessed not only each new model's individual metrics but also what replaced the strong evidence from either branch and the temporal relationships preserved by the original structure.

Evidence: `research/c412_pairwise_joint_file/C412_RESULT_REPORT_2026-09-10.md`, `SOURCEPAIR_UNCERTAINTY_2026-09-10.md`; `docs/C413_RESEARCH_AND_SUBMISSION_2026-09-10.md`; `docs/C414_C413_FAILURE_AND_VALIDATION_RESET_2026-09-10.md`.

### 3.2 C414–C446: Actual Representation Learning Still Had to Transfer Across Sources and Into Its Final Role

After C413, I moved beyond output combinations and trained the representations themselves. C414 updated the full C205 Deezer CNN with a gradient-reversal auxiliary objective intended to suppress six voice/channel conditions. I completed training on 4,176 actual waveforms from 696 music sources, with 3 epochs and 3,132 updates. I also checked the gradient and weight changes in the first convolution, the GRL sign, saving and restoring, and non-use of held data. Even so, EER on held766/133 sources worsened from **0.225889 to 0.241594**. A falling training BCE and condition-based auxiliary learning did not establish invariant representations or generalization. Because data balance and full-layer updating also changed, I did not identify GRL alone as the cause of failure.

C417 trained the entire SONICS encoder with a File OR objective. It completed 4 epochs and 2,232 updates on 4,464 waveforms from 744 sources, but File EER was 0.318566. Comparing identical labels on clean music alone, C417's EER of 0.300641 was worse than C205's 0.199359. Increasing File scores when Kokoro fake voice was added to real music was consistent with the task, but real LibriSpeech voice also raised the scores of REAL files. The synthetic-voice held set contained only four other recordings from the same Kokoro system, so it did not establish generalization across new TTS/VC systems.

The voice branch yielded the same lesson. C422, which adapted AASIST to Pocket conditions, improved on its own held set but regressed in C423: RADAR24 EER went from 0.50 to 0.666667 and ITW40 from 0.10 to 0.15. C430 trained the last two Wav2Vec2 layers and its head on data from multiple generators. Its final model, trained for 4 epochs on 3,328 wide/phone and REAL/FAKE rows from 832 pairs, achieved 0.075 on 160 unseen ASV-attack examples, but 0.40 on ITW40 and 0.50 on RADAR24. The corresponding C426 values were 0.025, 0.10, and 0.50. Some benefit from learning additional MLAAD generators remained on new DEV data, but it did not improve all other sources. The C435/C436 linear controls with the original encoder frozen recovered ITW only to 0.30; ASV 0.0875, RADAR 0.50, and MLAAD40 0.30 did not support a general replacement.

C445 tested a narrower hypothesis closer to actual deployment. I adapted only Spectra's final block23 to train on Demucs vocals instead of mixed raw audio while retaining clean voice examples. With an actual TRAIN96 and separate DEV80, separated-voice EER improved from **0.05 to 0**, while clean-voice EER remained 0. However, when I inserted the same trained block into C349's actual raw/stem, temporal, and File combination in C446, EER/AUC on 8 files tied at 0.50/0.625. Voice-event and File suspicion scores actually rose for two REAL mixture files. I preserved the success on the small DEV set without promoting it to a claim of final File improvement.

Evidence: `research/c414_adversarial_full_training/C414_RESULT_AND_FAILURE_2026-09-10.md`; `research/c417_sonics_file_training/C417_RESULT_AND_LIMITS_2026-09-10.md`; `research/c423_aasist_cross_generator_probe/C423_RESULT_AND_FAILURE_2026-09-10.md`; `research/c433_c430_final_external/C433_C434_FINAL_FINDINGS_2026-09-11.md`; `research/c436_frozen_probe_external/C435_C436_FINAL_FINDINGS_2026-09-11.md`; `research/c445_spectra_stem_adaptation/C445_RESULT_AND_LIMITS_2026-09-11.md`; `research/c446_spectra_stem_file_transfer/C446_RESULT_AND_STOP_2026-09-11.md`.

### 3.3 C465: Learning a New Generator Succeeded, but Evidence From Short Events Was Diluted

The base music-training data contained 3,690 rows derived from 631 tracks. REAL comprised 273 FMA tracks and 24 MUSAN tracks; FAKE comprised 334 tracks. I applied clean, real-voice mixture, Kokoro synthetic-voice mixture, and telephone transformations to the same fixed 4-second music excerpts. Training weight was equalized by class, then identity, then view, rather than by generator. Four Suno buckets and Yue accounted for a large share of the fake music. outer766 contained transformations of 133 tracks, and 50 DiffRhythm tracks among its 78 FAKE tracks were absent from TRAIN. It was therefore neither a fully generator-held evaluation nor an evaluation with an identical distribution. Treating the 3,690 rows as 3,690 new pieces of music would greatly overstate data diversity.

C461 distilled C205's decisions on the same existing inputs, reducing held766 EER from 0.225889 to 0.190674. C465 added 48 AIME Riffusion sources × six conditions, or 288 rows. The total was TRAIN3,978 rows/679 tracks, trained for 12 epochs and 5,976 updates, with the C205 teacher applied only to the existing inputs. The new 288 rows used BCE alone so that the teacher's mistakes on the new generator would not be forcibly preserved. On 96 transformations of 16 separate Riffusion tracks combined with 314 reused REAL rows, EER improved from C205's **0.247611 to 0.001592**. This showed a strong learning effect on closely related examples from the new generator, but it was neither new REAL validation nor a guarantee across all generators.

EER on the existing766 tied C461 at 0.190674. In C466, which moved C465 into the C205 slot of the actual C349 pipeline, Music160 improved from 0.25 to 0.2375, while File200 tied at 0.129670 and novel64 tied at 0.124103. On C467's 128 transformations from 16 separate music parents, external Music EER tied at 0.1875. External Music EER remained 0.4375 under the condition that replaced 2 seconds within a 12-second clip with fake music and overlaid real voice. This made it clearer why I could not add the large improvement on the new generator alone to an expected final submission score.

An audit of saved window scores showed that Deezer had not entirely missed the event. Two windows fell within the 2-second insertion and covered 78% of the event, while the local ranking of matched REAL/FAKE pairs improved from C205's 9/16 to C465's 11/16. However, after averaging with C180 and aggregating all windows with Presence, that became 9/16, and the final external Music output achieved 10/16. In one example, local C465 scores were REAL 0.357189/FAKE 0.784186, but final Music scores were 0.163674/0.156255, reversing the order. Oppositely directed Fourier evidence and Dasheng's selection of a window outside the event both contributed to the combination. Other parents still failed at the local classification stage. The problem therefore involved missing observations, aggregation dilution, and local classification errors together; I could not conclude that one pooling change would solve every failure.

Evidence: `research/c566_eat_lastblock/C566_PUBLIC_TRAINING_COVERAGE_AUDIT.md`; `research/c461_deezer_teacher_preservation/C461_RESULT_AND_LIMITS_2026-09-11.md`; `research/c465_riffusion_expansion_kd/C465_FREEZE.md`, `C465_RESULT_AND_LIMITS_2026-09-11.md`; `research/c466_c465_music_transfer/C466_RESULT_AND_NEXT_2026-09-11.md`; `research/c467_c465_broader_transfer/C467_RESULT_AND_LIMITS_2026-09-11.md`, `C467_PARTIAL_WINDOW_DIAGNOSIS_2026-09-11.md`.

### 3.4 C473–C547: Partial Fakes, Temporal Attention, and Preservation of the Original Teacher

C473 froze C465 features and trained a temporal head with 4,545 parameters. I added 1,024 actually edited rows to the existing 3,978 rows. These included REAL controls edited at the same positions (RR), 2-second FAKE insertions into REAL backgrounds (RF), continuous REAL/FAKE examples, and telephone conditions. I jointly supervised local occupancy and a max-logit bag. Training completed on 5,002 rows with 5,976 updates, but the overall benefit on the new held256 did not translate into consistent gains on partial fakes. partial128 EER was worse for C473 at 0.3125 than for C465 max at 0.296875. In contrast, a fixed combination with C180 in C475 showed complementarity: Music160 improved from 0.25 to 0.2125 and novel64 from 0.124103 to 0.078462.

C488 added boundary auxiliary learning, improving new held256 EER from 0.199219 to 0.179688. Most of the gain came from continuous music, while partial wide regressed from 0.25 to 0.3125. Parallel efforts to learn new features were not universal solutions either. C493's fresh frequency-pattern classifier achieved 0.477792 on the existing766, C497's phase CNN achieved 0.334233, and C499 with masking and mixup achieved 0.382454. The fact that C497's training BCE fell almost to 0 did not establish held generalization. C549, a linear-spectrum LCNN trained from scratch, also completed training on 7,380 actual waveforms but achieved outer766 EER 0.351044, weaker than the 0.225889 baseline. Even with a distinct signal on the new40, a wholesale replacement was not justified.

C520 learned the tradeoff between mean and maximum through **trainable gated attention** instead of choosing a fixed rule. It had 5,651 parameters and used frozen C465 features, the original logit, temporal convolution, and a boundary auxiliary head. I trained it on the same 5,002 rows for 12 epochs and 5,976 updates, then used attention to form a weighted sum of local logits over valid windows within each file. This operation differs from the existing Presence-weighted average of probabilities. The final numerical check stopped because an FP32 batch-shape difference produced a logit error of 2.384e-6, but the probability difference was 4.47e-8 and the effect of invalid padding was 0. I recovered evaluation through the single-file path without retraining the checkpoint. This record separates a stop triggered by a numerical check from an actual performance failure.

C532 replaced the C205 half of C349's external Music computation with the C465+C520 bag. I retained the other experts, the existing C346 combination coefficients, and File, Voice, and Presence. Public Music160 improved from 0.25 to 0.2125 and novel64 from 0.124103 to 0.045641, while extra128 tied at 0.1875. However, overlap worsened from 0.30 to 0.40. After a successful server run, my recorded ADS was **0.8123095238**, below C349. A verifiable structural difference was that the original C205's direct decision had disappeared, while the new score's temporal aggregation, scale, and error relationships with other experts had changed, yet I had retained the old combination coefficients. I did not establish this as the sole cause of the server regression.

C536 directly distilled the original C205's window decisions and file-level probability average into attention training. Its standalone all862 EER worsened from C520's 0.172666 to C536's 0.197266, but in the fixed final combination, extra128 improved from 0.1875 to 0.15625 and some overlap losses were recovered. This was a counterexample to discarding candidates based solely on standalone EER. I packaged it as the Music-only C547, whose recorded server ADS was **0.8131666667**. It was slightly better than C532 but did not exceed C349. Training that preserves a teacher, a combination that preserves inputs, and outcomes that preserve correct decisions each required separate verification.

Evidence: `research/c473_diverse_longbag_training/C473_FINAL_RESULT.md`; `research/c488_boundary_auxiliary/C488_RESULT.md`; `research/c493_robust_fourier_training/C493_RESULT_AND_FAILURE.md`; `research/c497_phase_cnn_training/C497_RESULT_AND_FAILURE.md`; `research/c499_regularized_phase_training/C499_RESULT_AND_FAILURE.md`; `research/c549_linear_spectrum_lcnn/C549_RESULT_AND_NEXT_DECISION.md`; `research/c520_learned_temporal_pool/C520_FREEZE.md`, `C520_FINAL_PARITY_FAILURE_2026-09-12.md`; `research/c532_c520_music_submission/C532_PUBLIC_EVIDENCE_AND_HANDOFF.md`; `research/c533_c532_postmortem/AUDIT.md`; `research/c536_c205_teacher_attention/C536_C537_RESULT_AND_LIMITS.md`; `research/c548_c547_postmortem/C548_SERVER_RESULT_AND_SCOPE.md`.

### 3.5 C548: Reassessing Validation Independence

The audit after C547 showed that I could not readily interpret the public improvements as three independent successes. Music160 had been actual training data for the C346 final combiner. novel64 and extra128 were not confirmation sets used only once for a new model either. An exact SHA comparison showed that **all 16 music parents in extra128 also appeared in novel64, and 35 novel64 rows came from those parents.** extra128 contained transformations of 8 music pairs/16 parents, 7 REAL artists, and 2 additional voice parents. Including the shared voice sources made the parent graph a single connected component.

Validation coverage also did not fully cross duration, codec, and channel. Music160 contained 4/8-second mono WAV and the earlier 16k μ-law conditions; extra128 contained 4/12-second clips, true8k telephone audio, and mixtures with fixed RMS. novel64 included actual 45-second audio and FLAC, but the FLAC was duplicated dual-mono and did not substitute for native stereo or final MP3 validation. Saying that I had “never tested long audio” would be wrong, but saying that I had “covered multiple formats comprehensively” would also overstate the evidence.

I subsequently designated the existing200/64/128/16 as regression and diagnostic data and moved toward fixing the training, combination-selection, and confirmation roles of new sources in advance. Increasing the number of transformations of the same parents, adding new tracks from the same generator, and validating an unseen generator were different activities. I also separated source-authenticity proxies from actual music/voice component labels. This reset did not guarantee higher server scores, but it set more accurate limits on what the public metrics meant.

Evidence: `research/c548_c547_postmortem/VALIDATION_RESET_FINDINGS.md` and its referenced `C548_MANIFEST_COVERAGE_CHECK.json`.

### 3.6 C572–C596: EAT Added a New Representation, and Its Assigned Role Shaped the Outcome

In C564, I verified the original public EAT-base assets, revision, license, and dependencies. I did not treat them as already successful detection weights; I actually evaluated a frozen head and final-block adaptation. Starting from C566, C572 added 97 new music sources plus sparse-music and real-voice conditions. The original 3,690+582 became 4,272 rows/728 music sources, trained for 2 epochs and 1,068 updates. Standalone outer766 EER worsened from C566's 0.220492 to C572's 0.235091, but on the same multiwindow extra128 it improved substantially from **0.3125 to 0.203125**.

However, the fixed approach of assigning C572 one quarter of the existing Deezer slot only tied final Music EER at 0.1875. In the partial2-second condition, C349 scored 0.4375 and standalone C572 scored 0.3125, yet their combination was worse at 0.50. This was a clear example of how a good new model's signal did not necessarily survive being inserted as a small share of an existing input. C575 instead made EAT an independent fourth logit input and combined it with D239, Fourier, and Dasheng on public304. I divided 144 rows from 72 new parents, each represented by a central 4-second excerpt and audio up to 60 seconds, into 9 source-group folds; the existing Music160 remained in training for every fold. Thus, the new144 results were **group-held at the combiner level**.

C575's new144 EER improved from C349's 0.180556 to 0.152778, fresh40 from 0.10 to 0.05, and extra128 from 0.1875 to 0.171875. factorial16 regressed from 0.25 to 0.375. My recorded server ADS for the C577 submission **tied C349 at 0.8157380952**. An equal score was not evidence that the model had not run. On public old160, even EER and AUC were identical, but all 160 probabilities changed: the loss of 269 correctly ordered REAL–FAKE pairs was offset by improvement in 269 other pairs. I had to distinguish a tie in aggregate metrics from identical outputs.

C583 added REAL editing controls at matched positions, 2-second FAKE replacements, and real-voice data, training on 4,400 rows for 2 epochs and 1,100 updates. Standalone multi128 EER improved from C572's 0.203125 to **0.140625**, correcting 8 errors at the overall operating boundary without introducing any new errors. However, the targeted partial subset EER tied at 0.3125. Combined as an independent expert, C584 achieved 0.140625 overall on extra128, but partial weakened again to 0.4375. I submitted C586 with a fresh40 EER of 0, yet my recorded server ADS regressed to **0.8131666667**. Even perfect ranking on a small new panel did not guarantee an advantage on the server.

Instead of an adapted block, C593 extracted CLS, patch means, and population standard deviations from **layers 4/8/12** of the original frozen EAT and averaged the logits of three independent small heads. I trained it on the same 4,400 rows for 6 epochs and 1,650 updates. outer766 EER improved from C583's 0.210184 to **0.165767**. On extra128, each condition's EER tied or improved, yet overall EER worsened from 0.140625 to 0.1875. This showed that ranking within conditions can improve while score alignment between conditions worsens.

C594 combined this raw C593 as an independent expert using the same 304-row, 9-fold procedure. EER was 0.125 on new144, 0.140625 on extra128, 0.05 on fresh40, 0.078462 on novel64, and 0.25 on factorial16. All five panels tied or improved relative to C349, but C584's fresh40 EER of 0 was lost. Every 95% interval from source-cluster bootstrap included zero. After I submitted it as the external Music-only C596, my recorded server ADS was **0.8174523810**, approximately +0.001714286 over C349. This small measured gain supported the complementarity of the C593 representation, but it did not establish a general rule that freezing is superior to every form of fine-tuning.

Evidence: `research/c564_eat_base/C564_ACQUIRED_ASSETS.md`; `research/c572_eat_sparse_music/C572_FREEZE.md`, `C572_OUTER_RESULT_AND_LIMITS.md`, `C572_MULTIWINDOW_RESULT_AND_KEEP.md`; `research/c575_eat_independent_expert/C575_GROUPHELD_RESULT_AND_LIMITS.md`; `research/c577_c575_submission/ROOT_PUBLIC_DECISION.md`; `research/c578_c577_result_audit/C577_EQUAL_SCORE_PUBLIC_COUNTEREXAMPLES_AND_LIMITS.md`; `research/c583_eat_matched_splice/C583_TRANSFER_RESULT_AND_NEXT.md`; `research/c584_splice_eat_expert/C584_INITIAL_RESULT_AND_NEXT.md`; `research/c593_eat_depth_augmented/C593_FREEZE.md`, `C593_TRANSFER_RESULT_AND_NEXT.md`; `research/c594_depth_augmented_expert/RESULT_AND_NEXT.md`, `C594_CLUSTER_UNCERTAINTY.md`; `docs/C586_C596_SERVER_RESULTS_2026-09-14.md`.

### 3.7 C596–C651: A Stronger Standalone Model Still Did Not Necessarily Produce Better Final Outputs

Subsequent representation research also produced measured gains. C630 used frozen EAT-large layers 8/16/24 while retaining the same 4,400 rows and objective. Standalone multi128 EER improved from C593's 0.1875 to 0.125, and outer766 from 0.165767 to 0.126747. C631, which also adapted the final block, raised multi128 AUC from 0.932617 to 0.957031, but overall EER tied at 0.125 and the same 16 files were wrong at the overall EER boundary. C646 temporal MIL reduced EER in the partial condition from 0.25 to 0.1875, but tied overall at 0.125 and trailed the existing final combination in other continuous and overlap conditions.

As part of my decision to reconsider the architecture, I also compared using a standalone model directly as the final Music output. C633's direct C630 replacement improved extra128 from the final C594's 0.140625 to 0.125, but substantially worsened new144 from **0.125 to 0.222222**. It corrected 6 of the existing 18 errors while introducing 20 new ones. The evidence therefore did not support either always preserving the existing combination or assigning a strong standalone model the final role immediately. I needed direct comparisons on the same inputs to identify what was preserved and which sources suffered losses.

Evidence: `research/c630_eat_large_depth/RESULT_AND_LIMITS.md`; `research/c631_eat_large_lastblock/RESULT_AND_LIMITS.md`; `research/c633_standalone_direct/RESULT_AND_LIMITS.md`; `research/c646_large_temporal_mil/RESULT_AND_LIMITS.md`; `docs/RESEARCH_STRUCTURE_RESET_2026-09-15.md`.

### 3.8 C652–C660: Diagnosing the Complete File Path Produced a Larger Change Than Adding Models

C652 distinguished historical fold predictions from actual deployment constants and revisited C596's complete File path. File EER was 0.12967033 on 200 rows already exposed during training, and all 9 REAL false positives at the diagnostic boundary crossed it on internal music-event evidence alone. However, diagnostic variants that forced Presence to 1 or removed either the raw or stem branch lost more correct decisions. I also did not treat oracle analyses using injected ground truth as achievable model performance.

On C654's new40, with the full path actually executed, File EER was 0.15 while external Music EER against the same source-authenticity labels was 0.05. The 3 false positives represented three different cases: voice-event evidence alone was sufficient, music-event evidence alone was sufficient, or both were below the boundary but crossed it after OR. In C653's 16 clean/real-accompaniment examples from 8 ASV utterances, File and Voice EER remained 0, but adding accompaniment to REAL voice increased File suspicion because of the internal music event. For FAKE voice, by contrast, the stem retained strong evidence even when the raw score weakened. Simple remedies such as deleting the stem or judging solely from music could not explain both findings together.

For a broader diagnosis, I intended to split 400 sources into 300 development and 100 confirmation sources. Among the 378 successfully acquired at that time, I first fixed **280 diagnostic sources (130 REAL/150 FAKE)**. This was a limitation imposed by availability, not replacement after observing scores. I processed the central 10 seconds through the full C596 path. Median processing time for the first 8 was 18.94 minutes, and the DF phase accounted for 90.39% of computation time. Reusing loaded models alone could not remove most of the cost. I therefore compared subsequent structural alternatives using preserved intermediate values rather than repeating this slow inference. I did not use the locked confirmation data for development before fixing a candidate.

C658 compared a small number of fixed alternatives: replacing the OR of the two events with max, or connecting external Music×Presence directly to File. OR→max improved diagnostic280 EER from 0.139231 to 0.10718, but worsened the existing200 from 0.12967 to 0.15549 and two-phase from 0.20 to 0.30. C659 replaced only the existing music event's global input with external Music. It improved new40 from 0.15 to 0.10, but worsened diagnostic280 from 0.139231 to 0.146410 and two-phase from 0.20 to 0.283333. These were measured gains and losses, not simple execution errors.

C660 changed a narrower input. In addition to the existing global/aligned music evidence, the File music event had a separate direct input containing the standalone Fourier logit. I **replaced only that direct Fourier input with the already computed C596 external Music output**, retaining the coefficients, aligned/global music, Presence, raw/stem Voice max, and final OR. Fourier itself remained in several music paths. There was no new model, fit, neural-network call, or selection of coefficients based on server scores.

| Public panels requiring separate interpretation | C596 File-related EER | C660 EER | Meaning |
|---|---:|---:|---|
| Development source-proxy280 | 0.139231 | 0.078462 | Diagnostic data used to select the candidate |
| Development source-proxy40 | 0.150000 | 0.050000 | Repeatedly used small panel with proxy labels |
| Exposed160 with external Music scores available | 0.180909 | 0.138182 | Data exposed during training/development; not the full200 |
| 110 of the above160 with unambiguous File labels | 0.063333 | 0.063333 | Overlapping subset, not an additional independent success |
| Separate confirmation100 after candidate freeze | 0.140000 | 0.020000 | One comparison on FMA50/AIME50 from 35 source groups |

I separated confirmation100 from the original diagnostic source groups and evaluated all of it after fixing the candidate. Errors at each model's operating boundary fell from 14 to 2, with 13 corrections and 1 loss, while AUC improved from 0.96 to 0.9972. The 95% interval for EER reduction from cluster bootstrap was [0.0321,0.1883]. However, source and authenticity were linked through FMA/AIME, and component labels were unconfirmed, so I did not convert this result into official ADS or a probability of server success. After this use, I no longer described the set as unused confirmation data. On a separate16 of voice and sequential mixtures, EER remained 0, but REAL File scores rose by 0.070159 on average, reducing the margin for correct decisions.

I completed the C660 ZIP at 6,603,310,574 bytes, with the original C596 weights, requirements, and heavy inference path unchanged. It passed an actual load→preprocess→serial inference→CSV run on 116 public inputs, along with checks for per-file independence and preservation of the other outputs. This was evidence from serial Windows CPU execution; I did not newly perform a complete single-process Linux/L4 validation. My subsequently recorded server result was total score **0.8436157937 / ADS 0.8274523810 / CPS 0.9890865079**, with a runtime of 26 minutes 15 seconds. The approximately 0.01000 ADS improvement over C596 confirmed that correcting the path carrying already learned music signals into File was effective in that evaluation. I did not construct an expected server ADS by adding public EER reductions to it.

Evidence: `research/c652_c596_full_diagnosis/RESULT_AND_NEXT.md`; `research/c653_c596_matched_panel/FULL16_INTERPRETATION.md`; `research/c654_c596_fresh_file/FULL40_RESULT_AND_NEXT.md`; `research/c657_c596_ten_second_pilot/SMALL8_INTERPRETATION_AND_NEXT.md`, `LARGE280_SCOPE.md`; `research/c658_file_structure_2x2/RESULT_AND_NEXT.md`; `research/c659_preserved_music_input/RESULT_AND_LIMITS.md`; `research/c660_direct_music_evidence/RESULT_AND_LIMITS.md`, `C660_FROZEN_CONFIRMATION_PLAN.md`; `docs/C660_CONFIRMATION_AND_SUBMISSION_2026-09-19.md`; `docs/C660_SERVER_RESULT_AND_NEXT_2026-09-20.md`.

### 3.9 Keeping Public Measurements Separate From My Recorded Server Results

The values below were not calculated through public validation. They are aggregate results preserved in my reports from my submission-screen records. They are not records of directly obtaining individual server predictions, labels, or component-level EER. Each report also has limits on linking the filename shown on a submission screen to a local candidate, so I do not describe this as “directly auditing the private evaluation.” The highest score and ranking over the full period are addressed separately in the subsequent section of the history.

| Candidate | Intended changed output | My recorded server ADS | My recorded server total | CPS |
|---|---|---:|---:|---:|
| C349 baseline | Music | 0.8157380952 | 0.8330729365 | 0.9890865079 |
| C413 | File | 0.8003809524 | 0.8192515079 | 0.9890865079 |
| C532 | Music | 0.8123095238 | 0.8299872222 | 0.9890865079 |
| C547 | Music | 0.8131666667 | 0.8307586508 | 0.9890865079 |
| C577 | Music | 0.8157380952 | 0.8330729365 | 0.9890865079 |
| C586 | Music | 0.8131666667 | 0.8307586508 | 0.9890865079 |
| C596 | Music | 0.8174523810 | 0.8346157937 | 0.9890865079 |
| C660 | File | 0.8274523810 | 0.8436157937 | 0.9890865079 |

I can explain the role of the changes under the assumptions that CPS was unchanged and that the contract to preserve the other four outputs also held on the actual server. However, I did not reverse-engineer generator, channel, or duration proportions, individual labels, or errors from these aggregates to fit subsequent coefficients. Preserved documents conflict on C596's server runtime, giving 26 minutes 53 seconds and 26 minutes 35 seconds. Unlike the scores, I exclude this runtime from retrospective comparisons and do not arbitrarily rewrite the two records as the same value.

### 3.10 Experimental-Design Lessons From This Period

First, **completed training, verified execution, and improved performance were separate outcomes**. C414's full-CNN gradients, C430's strict load, C520's recovery of a saved model, and C549's actual training were evidence that the work ran. They did not guarantee generalization. Conversely, I also needed to avoid treating a completed model as a training failure, or restarting from scratch, because of a numerical tolerance or log-saving failure. Running one actual audio file, then a small batch, then fixed performance measurements early, and reusing completed features, scores, and checkpoints, was especially important with limited CPU and RAM.

Second, **an expert's role and its position in the combination mattered as much as model selection**. The same EAT had different effects when used as a small part of Deezer, an independent expert, external Music, or a direct input to the File event. External Music could improve while the internal music event in File remained unchanged. File, Voice, and Music were not the same probability with different names; I had to measure them through the same paths as the actual deployment formulas. Adding together improvements from several good standalone models to predict ADS had no evidential basis.

Third, **I needed to examine overall EER, condition-level EER, and error tradeoffs together**. As in C593, EER could tie or improve within every condition while worsening overall. As in C577, probabilities and rankings could change substantially even when EER/AUC tied. Counting corrected errors while hiding newly lost correct decisions obscures the actual complementarity. ROC operating boundaries in the reports were explanatory tools; I did not transfer them into submission thresholds.

Fourth, **independent sources and exposure history mattered more than file counts**. The 766 rows represented 133 tracks; the 128 rows were transformations of 8 music pairs. Even a split clean under exact SHA matching did not guarantee independence of artists, speakers, prompts, or upstream pretraining. Once I repeatedly observed validation results to choose a structure, those data became development data. C548's identification of overlapping parents and C660's confirmation100 after candidate freeze were important changes that put this principle into practice.

Finally, I carried out these experiments while retaining source, version, license, and actual training-file records. Permission for public noncommercial research use and exclusive rights transfer for final prize deliverables were separate issues, and the rights HOLDs affecting several lineages were not comprehensively resolved during this period. I also exclude models, audio, and per-file validation predictions from this retrospective to keep performance reporting separate from redistribution of third-party assets. I do not recast experimental plans or drafts as completed results, public proxies as official ADS, or my recorded rankings as an official final ranking.

## 4. After C660: What improved, and why progress stalled

### 4.1 C660 → C693: Two gains from correcting the evidence paths

C660 achieved a server ADS of **0.8274523810**, an increase of +0.0100000000 over C596's 0.8174523810. I did not add another expert. I replaced the direct Fourier input slot so the evidence already computed by the external Music ensemble could reach the internal File path. My quantitative diagnosis—that FAKE evidence detected by several experts was not reaching the final fusion strongly enough—proved useful.

C682 changed coverage in the original-audio voice path, but its server ADS tied C660. That tie does not establish that the server ignored the output or that a particular type of audio was absent. EER responds to ordering and the error boundary, not to the total magnitude of probability changes.

I next examined the internal File voice path. I wanted to suppress errors in which the original DF-Arena model treated real music as evidence of fake speech, while retaining detection of genuinely manipulated speech. I rejected the initial C687 because its native-music exposure and retention performance were insufficient. For C688, I switched to a fixed training schedule that included the four ASV/MLAAD × REAL/FAKE speech groups and native music in every update. I trained the final Conformer block and classifier rather than retraining the entire original model.

I interpreted each validation result in the context of the panel that produced it.

| Public evaluation | Observation | Limitation |
|---|---|---|
| C689 known40 | File EER preserved at 0.05 | A small, repeatedly used public panel |
| C691 error-selected 41 | Errors at the diagnostic threshold fell from 22 to 17; 6 REAL false positives recovered, 1 new loss; 72 rank pairs improved and 2 worsened | An error-selected source-proxy panel, not a general error-rate estimate |
| C692 source-proxy 100 | EER 0.02 / AUC 0.9972 preserved; 3 rank pairs improved and 3 worsened | Not complete official File/Voice/Music ground truth |

In C693, I applied the learned tail **only to the original-audio and separated-audio voice decisions inside File**. I shared the intermediate representation from the original DF encoder, avoiding a second run of the expensive full encoder. I kept the original DF model for the external Voice output, and preserved external Music and both Presence outputs. I also retained C660's music-evidence routing.

My recorded server result was **ADS 0.8362380952**, overall score 0.8515229365, CPS 0.9890865079, and a runtime of 26 minutes 53 seconds. That was an ADS gain of +0.0087857142 over C660. I can establish that only the File output changed in the implementation and that the aggregate score increased. I cannot identify the server's per-file errors or its proportions of audio types from that result.

In a clean local Windows environment, I checked a serial smoke test from an actual audio file through music inference, DF, Spectra, and CSV output. The recorded maximum difference across the final outputs was about 3.05e-8. I do not extend that check into a claim that all files and peak memory were reproduced on Linux/L4. My completed server submission and the scope of my local execution checks are separate pieces of evidence.

Evidence: `docs/C660_SERVER_RESULT_AND_NEXT_2026-09-20.md`, `docs/C693_SERVER_RESULT_AND_NEXT_2026-09-24.md`, `docs/C693_FILE_VOICE_ADAPTATION_2026-09-24.md`.

### 4.2 C704, C710, and C722: Better standalone metrics did not mean a better deployed combination

C704 replaced the internal File Deezer pair, C180+C205, with C180+C465. I left external Music unchanged. Its server ADS was **exactly the same as C693's**. In C709's public-data trace, the effect shrank at each stage: a mean absolute C465−C205 difference of about 0.07997 became 0.03999 after averaging, 0.03909 after presence aggregation, 0.01129 at qMusic, and 0.00973 at File. All 400 REAL–FAKE rank pairs in known40 remained unchanged. Some pairs improved in retention100, but its EER remained 0.02. The public measurements therefore support **a change that propagated but did not move the EER boundary enough**, rather than a change that never took effect. They do not prove the composition of the hidden server data.

C710 removed the averaging step and used C465 alone. EER improved sharply on the selected-error panel, but the gains were concentrated in Riffusion, with regression warnings in other conditions. Server ADS fell to **0.8353809524**. Averaging with C180 may have provided complementary evidence rather than merely diluting C465. This was another example of why I could not convert a standalone model's improvement directly into an expected final ADS gain.

C722 replaced the raw/stem `max` in the File voice path with a mean. It improved known40, the error panel, and some mixed-audio data, but retention100 EER worsened from **0.02 to 0.04**. Server ADS also fell, to **0.8341666667**. The retention failure had already appeared in public validation. I should not explain the result solely as a mismatch with the server distribution: I also failed to give the retention-panel warning enough weight when deciding to submit.

I rejected C723's internal Spectra change because EER tied while AUC declined. From then on, I used the best C693 model as a fixed control and recorded lost correct decisions and rank pairs alongside recovered ones.

Evidence: `docs/C704_SERVER_TIE_AND_NEXT_2026-09-25.md`, `docs/C710_SERVER_REGRESSION_AND_LESSON_2026-09-26.md`, `docs/C722_SERVER_FAILURE_AND_RESEARCH_RESET_2026-09-27.md`.

### 4.3 C724–C728: Separating model weaknesses from evaluation mistakes

On C724's 40 pure-speech files, all relevant paths in C660 and C693 had EER 0 / AUC 1. That means I found no errors on that small public panel, not that the models had no speech-related weaknesses. Some source names included telephone/G711, but the actual inputs were 16 kHz µ-law with different crops. They were not equivalent to genuinely 8 kHz band-limited telephone speech, and the causal effects of cropping and codec were not isolated.

C725's 12 mixed-audio files also produced 0/1 for both versions. The historical two-phase EER of 0.20 belonged to old C349/C51, not current C660. Rechecking the same inputs with the current computation path gave C660 clear60 EER 0.10 / AUC 0.9788889, and two-phase20 0.10 / 0.94. **Correcting a mistaken baseline is not a new model improvement.**

For C726, I selected just two residual-error files for diagnosis. C693 still ranked the REAL file at 0.851193 above the FAKE file at 0.698159. I examined where positive evidence weakened across raw/stem DF evidence, alignment, presence weighting, and event aggregation. I did not report a general EER or ADS from two error-selected files. The first implementation stopped because an original-DF margin replay difference of 1.1444e-5 exceeded the 1e-5 tolerance. After checking the input and model, I reviewed a separate version designed to check both margins and probabilities. I distinguished this numerical replay issue from a RAM stop or a server-performance failure.

C727 inspected four retained actual TRAIN files. For its two FAKE files, qVoice weakened from the original path's 0.853052 to 0.779118 and from 0.700059 to 0.435671, with particularly large losses in the separated-audio DF margins. C728 expanded the diagnosis to 32 actual TRAIN files—overlap16 plus partial16—and 96 windows. FAKE BCE worsened from 0.112436 to 0.196296, while REAL BCE improved from 0.126069 to 0.072920. Seven of eight overlap FAKE files and three of eight partial FAKE files worsened. This is not the same as saying that all partially manipulated files worsened.

The first window of a partial FAKE file can be mostly REAL, with only 600 FAKE samples. Copying the file's FAKE label to every window would create an incorrect training target. I therefore investigated **file/bag-level losses** that included the temporal aggregation used at deployment.

### 4.4 C729–C742: Retention constraints and the limits of small heads

| Family | Actual change and TRAIN observation | Public transfer / decision |
|---|---|---|
| C729 | 16 updates to C688's final block+fc5; new32 BCE improved from 0.134608 to 0.108496 | Old-speech errors rose from 68 to 74, maximum opposite-direction drift was 0.329683 > 0.10, and native File increases exceeded budget. I rejected it before public transfer. |
| C730–C733 | Cached 692 CLS vectors from frozen C688 and trained only fc5's 2,562 parameters; old errors fell from 68 to 66 and new BCE reached 0.132018 | Known40 EER tied at 0.05; error41 EER tied at 0.343137 with lower AUC. I rejected it for failing the strict-gain requirement. |
| C734–C736 | Fixed bias/block and trained a 1,280-dimensional contrast change with paired ranking; native REAL scores decreased and new BCE improved slightly | Known/error EER tied. Tiny improvements in TRAIN ranking loss produced no actual rank corrections. |
| C737–C739 | Investigated clean→mix teacher-evidence recovery under retention constraints | Numerical or predefined acceptance checks failed. C739 recovered 9.69 against a fixed requirement of 10; I did not relax the criterion after seeing the result. |
| C740–C742 | Optimized mixed source-proxy BCE under 644 fixed TRAIN retention constraints; old errors fell from 68 to 47 (21 recoveries, 0 losses), and mix errors from 62 to 42 | Known EER tied while AUC fell from 0.9925 to 0.9875; error EER tied while AUC improved slightly. I rejected it because the required EER gain was absent. |

C729 showed that applying a weak one-sided retention loss once does not guarantee protection against drift from later updates. The `max(raw, stem)` operation sends gradients only through the winning path, so I could not claim that both paths improved simultaneously. Because I changed the block and head together, I did not attribute the failure to the block alone.

I did not conclude that all head-only approaches were impossible just because C731/C734 made small changes. C740 corrected many actual TRAIN errors, but those gains did not translate into the rank corrections needed in public transfer. That result pointed me back to **mismatches between the objective, the supporting data, and the final fusion path**, rather than simply too little training. These were repeatedly used public panels, so even a pass would not have been success on an independent holdout.

I also retained implementation failures separately. C741 V1's relative-versus-absolute receipt-path comparison failed before any neural-network execution. V2 corrected it by resolving and checking the path, size, and SHA strictly; it did not change the training, model, or performance criteria. I did not rescue rejected candidates by selecting an earlier checkpoint or searching LR/alpha after the evaluation.

Evidence: `research/c729_deployed_event_tail/RESULT_AND_NEXT.md`, `research/c731_fc5_only_deployed_event/TRAIN_AUDIT_DECISION.md`, `research/c734_pair_rank_contrast/TRAIN_AUDIT_DECISION.md`, `research/c740_bounded_mix_classification/TRAIN_AUDIT_DECISION.md`, `research/c742_c740_late_transfer/RESULT_AND_NEXT.md`.

### 4.5 C743–C753: Direct music-readout and event learning still failed to transfer

C742's path diagnosis showed qMusic dominating some selected FAKE errors while qVoice was very low. This suggested a need to improve music evidence directly. Source-proxy labels, however, did not establish the authenticity of individual components or reveal server dataset proportions.

C743/C744 used retained original-EAT features and 144 derived views from 72 additional native parents to train only 195 last-Linear parameters for 6 epochs and 1,704 updates. New-data BCE improved from 0.706226 to 0.677582, but old-teacher SmoothL1 reached 0.012252, above the 0.01 limit. The increase in new REAL BCE, +0.016517, also exceeded its +0.01 budget. I rejected the model. Although all probabilities increased, I did not treat that observation alone as proof that a single bias term caused the failure.

C745 fixed the bias and constrained 192 contrast changes to preserve REAL behavior. It passed the TRAIN numerical checks, but public known/error EER tied, so I rejected it. C748/C749 tested a residual readout injected directly into File, but TRAIN32 EER 0.0625 / AUC 0.9921875 tied, with zero rank-pair corrections. I did not use a tiny BCE reduction to justify a large follow-up evaluation or submission.

C751 checked whether residual DF errors recurred across four real-music sources selected by a fixed rule. The original DF had errors in three groups under the raw OR stem criterion; C688 had none. This failed the predefined expansion condition of at least two current-error groups. I did not keep looking for data until an error appeared or proceed to training.

C752/C753 was my final approach: learning the **Music-event bag itself**, rather than another Music source-authenticity score. C752 extracted original-EAT features for 200 files / 280 windows, reusing 4 successful windows and extracting 276 new ones in the full stage. C753 reused those features. I trained 193 readout parameters over 5 source folds, incorporating PANN presence, exact window overlap, and robust top aggregation. I preserved the public construction/event labels and nullable component masks instead of filling unknown component labels with proxies. File200 contained 70 REAL and 130 FAKE files by construction/source labeling, not official competition ground truth.

| Final C753 evaluation | Fixed historical matched5 (C479) | New event readout |
|---|---:|---:|
| Pooled Music-event EER | 0.2145833333 | 0.2604166667 |
| Pooled Music-event AUC | 0.864479 | 0.819479 |
| Construction/source File EER | 0.1296703297 | 0.1296703297 |
| Construction/source File AUC | 0.939890 | 0.926923 |

Some overlap/partial conditions improved, but losses in pure music and other mixed conditions outweighed them. The five-fold execution, exposure, and save/restore checks passed; this was not a result caused by a RAM interruption. I corrected the FP32 operation-order difference in the original warm bias through a separate V2 that preserved the exact calculation, rather than loosening the tolerance. I did not run a final all200 fit, create another submission ZIP, or continue public transfer.

**I ended the research on 2026-09-28.** I stopped the automatic-resume schedule and did not restart research or training. The work after that point was limited to this retrospective and preservation of the best model's source. Ideas after C753 are not executed results, so I do not list them as achievements.

## 5. Lessons from the full sequence of experiments

1. **I needed to verify the path to the final output before adding standalone detectors.** The actual server gains from C660 and C693 came from evidence routing and targeted internal-path improvements. Adding standalone EER gains does not yield an expected ADS gain.
2. **Different probabilities do not necessarily mean better EER.** I needed stage-by-stage changes, REAL–FAKE rank pairs, and newly gained/lost correct decisions together. A server tie does not prove that an audio type was absent from the hidden data or that the implementation was ignored.
3. **More development examples did not necessarily mean more independent evidence.** Crops, codecs, and mixtures from the same parent share their source. Repeated OOF, error-selected panels, and previously consumed public training material are not fresh holdouts.
4. **Unknown labels needed to stay unknown.** Source REAL/FAKE proxies differ from File, Voice, Music, event, and presence labels. Copying a partially manipulated file's label to every window can also create incorrect supervision.
5. **A retention failure was enough reason not to submit.** C722 had already worsened public retention before its server score fell. A large gain on one panel could conceal a meaningful loss on another.
6. **I needed separate records for execution integrity and model performance.** I found real issues involving path pins, FP32 operation order, and historical-baseline confusion. They do not justify attributing every failure across hundreds of stages to code. Models that still failed to transfer after correction remained failures in my record.
7. **Resource use was part of the research design.** Shared encoders, cached prefixes/CLS, small heads, and strict resume reduced unnecessary repetition. For long jobs, I checked actual startup and progress, estimated completion from measured speed, and used scheduled resumption. I stopped that schedule when I ended the research.
8. **Competition scores and rights clearance were separate questions.** I did not reach ADS 0.85. Permission for noncommercial use of data or models does not automatically permit code publication, weight redistribution, or transfer of rights upon winning. This repository grants no new rights to those assets.

The most important improvements now concern how I would organize the next project: establish parent/source-separated validation early, evaluate the real submission computation path from the start, make each component's label scope explicit, and judge a candidate's gains, losses, resource cost, and rights against predefined criteria. This does not turn the missed target into a success; it records how I intend to avoid repeating the same failures.

## Appendix A. Index of retained C-number research records

I found **656 C identifiers across 704 directories** in the filesystem snapshot of 2026-09-28. The highest identifier was C753.
This is not a count of completed training runs: the identifiers also cover design, data preparation, code audits, feature extraction, failures, evaluation, and packaging. I discuss V1–V5 and other early work with different names separately in the main text.
The paths below are relative paths into the retained original workspace. They do not mean that the complete underlying records or large assets have been uploaded to this repository. The JSON inventory also includes sizes and SHA-256 hashes for representative evidence files.

| Identifier | Retained research/stage directories | Representative evidence files (original workspace) |

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
