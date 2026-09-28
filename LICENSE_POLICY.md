# Licensing and Publication Scope

I do not apply a new blanket license, such as MIT, to this repository. My research documentation and integration code, parts derived from external models, and third-party notices have different rights and terms. Weights and training data also remain subject to their respective original conditions.

## Current status

On 2026-09-28, I made `kmw8123/deepvoice-detection-research` private and chose to preserve the archive there. Uploads are limited to my owner-only private repository; I have not authorized making it public or inviting others. A private setting does not itself grant permission to share competition materials or redistribute third-party works.

The `COMPETITION_GUARDRAILS.md` in my original workspace records restrictions on private source sharing without separate permission during the competition and on providing competition materials to people without access rights. The end of the competition does not change the rights attached to all external materials. Before publication, invitations, or distribution, I will check both the official terms then in effect and the rights for the specific files involved.

## Archive boundaries

- `src/` contains byte-for-byte copies of the original inference code and retains the original provenance.
- `annotated/` contains explanatory copies with English comments. These do not alter the original models' copyright or terms of use.
- `notices/` preserves original third-party licenses, modification notices, and attribution.
- I exclude weights, audio, feature/prediction arrays, row-level training manifests, vendor model implementations, wheels, and large ZIPs from this repository.
- I preserve the excluded actual training materials, original checkpoints, and ZIPs in my original workspace. Archiving the repository does not mean deleting originals or waiving data-submission obligations.

In particular, DF-Arena's original contributions and derivatives retain research/noncommercial conditions, and the Deezer family inherits CC-BY-NC-4.0. Apache/MIT/BSD notices on other components do not make the entire pipeline available under an unrestricted commercial license. I also distinguish SONICS code terms from its dataset terms. The detailed mapping is in the [third-party notices](THIRD_PARTY_NOTICES.md).

## Changes and attribution

My changes in this archive are code explanations and documentation edits. I do not present them as changes to the original submission ZIP or as new model performance validation. Even when an annotated copy has the same AST as the original, its bytes/hash differ, so I do not present an original source hash as the hash of an annotated copy.

I retain the full license text, copyright, attribution, and modification notices for external works without replacing them with a new license of my own. I distinguish upstream models from the heads I trained and do not imply that the original authors or data providers endorse my results.

The existing C693 record marks rights for final prize-winning deliverables and exclusive transfer as `HOLD_CONDITIONAL_NOT_CLEARED`. This archive therefore does not declare commercial use or exclusive rights transfer to be approved. If I decide on a future publication scope, I will record that decision and its basis separately while retaining the original historical provenance.
