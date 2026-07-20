# Model routing and review

## Roles

- Sol: design contracts; adjudicate ambiguity; verify survivors; merge; review rights and publication.
- Terra: interpret difficult documents, OCR, tables, mixed languages, or source structure.
- Luna: propose records from clean repetitive text after passing the locked gold gate.
- Deterministic code: perform every operation that can be reproduced without judgment.

## Parallel limits

Run at most three workers. Assign one source to exactly one extraction worker for a run. Workers emit isolated shards and never modify shared outputs. The primary Sol agent merges only after all expected shards are READY.

## Gold gate

Freeze thresholds before evaluation. The project default is precision at least 0.90, recall at least 0.80, and unresolved rate at most 0.10. Split labels at the source level so text from one source cannot leak across evaluation partitions.

If Luna fails, route that source class to Terra. Do not weaken the frozen threshold after seeing results; create a new protocol version instead.

## Audit trail

Record exact model identifier when available, prompt version or hash, worker ID, response hash/ID when available, source revision, and final reviewer verdict. LLM reruns are statistical; reproducibility means preserved inputs and responses plus deterministic replay of all post-processing.
