# DF-Arena modification notice

The upstream `backbone.py` unconditionally converted a one-dimensional input
to a batch of one with `x.unsqueeze(0)`.  This submission preserves that path
and additionally accepts a two-dimensional `[batch, samples]` tensor.  Batches
contain only deterministic segments from the single evaluation file currently
being processed.  No parameters, labels, or scoring layers were changed.

This notice is retained under Section 2 of the bundled non-commercial license.
