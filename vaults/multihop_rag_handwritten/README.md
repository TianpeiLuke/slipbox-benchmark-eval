# Hand-written control arm

These 42 notes were written **by hand** against the note contract, without
running the digestion pipeline. They are kept deliberately, as a control.

The pipeline arm lives in `vaults/multihop_rag/` and is produced by
`plan-digestion -> augment -> review -> execute`. Comparing the two isolates a
question the chunk baseline cannot answer: how much of any note-arm advantage
comes from the **note format** (typed, atomic, front-loaded, linked) versus from
**the pipeline that produces it**. A careful writer following the same contract
is the right control for that, because it holds the format fixed and varies only
the method.

They also differ measurably. These notes run about 7.3 per document. The
pipeline's density thresholds — tuned on technical documentation, where a source
page under 1,200 words maps to one note — prescribe roughly 1 to 2 notes for a
1,229-word news article. That gap is itself a finding about genre transfer, and
it is why this arm is labelled control rather than treatment: it is not what the
method produces.

Not scorable on its own terms until the pipeline arm exists to compare against.
