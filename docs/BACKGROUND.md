Background on the renormalization finding that motivates this repo.

Measured on a paired corpus: the ingestion pipeline maps three source length
distributions (coefficient of variation 0.89 / 1.39 / 1.06) onto notes at
0.33 / 0.33 / 0.18, while total words GREW 1.15x (fan-out 0.7-2.7 notes per
source document). It renormalizes format; it does not compress content.

That matters because the published "consolidation harms" results all measure
LOSSY COMPRESSION, and several of them compare summary-INSTEAD-OF-raw rather
than summary-ALONGSIDE-raw. Their flagship attribution ladder puts single-pass
query-blind compression within a fraction of a point of raw, and attributes the
damage to recursive in-place rewriting instead.
