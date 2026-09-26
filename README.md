# XI-V Bench 1.0

**A multilingual decision benchmark for System One models** — it measures models that decide in a single pass (fast, intuitive).
Without a chain of reasoning, tool round-trips, or self-verification, the model must produce a **correct label + confidence** from the given state and instructions alone.

| Item | Value |
|---|---|
| Tiers | `easy` · `standard` · `hard` |
| Languages | `en` · `ko` · `zh` · `ja` |
| Items | **384** (32 items × 3 tiers × 4 languages) |
| Cross-language set | **96 groups** (all 4 languages share the identical items) |
| Question types | `choice` 208 · `noul` 136 · `score` 40 |
| License | MIT (includes items derived from JevBench public, with adaptation notice) |

## What it measures

1. **Accuracy** — overall / per tier / per language / 12 cells
2. **Confidence quality** — ECE (10-bin), Brier (when the model reports a probability distribution)
3. **Language consistency (LCS)** — for the 4 language versions of the same item: cross-language agreement rate, max−min gap, and per-language accuracy
4. **Efficiency** — p50/p95 latency, input tokens per item

Tier definitions
- `easy`: the answer is directly verifiable from the context
- `standard`: 2–3 step combination (condition satisfaction, exclusion rules)
- `hard`: evidence dispersed across multiple places in the context + conflicting information / partial-condition traps (includes long-context items)

## Layout

```
datasets/<lang>/<tier>.jsonl   # items (one line = one item, UTF-8 JSON)
datasets/manifest.json         # cell counts, hashes, licenses, statistics
schema.json                    # item schema
SPEC.md                        # design, scoring, and source specification
builders/                      # item generation, localization, and normalization scripts
validate_items.py              # item validation (cell counts, duplicate ids, answer leakage, harness contract)
run_xi_v_bench.py              # runner (reuses the JevBench harness)
score_xi_v_bench.py            # scoring (tier×lang + ECE/Brier + LCS)
```

## Quick start

```bash
python3 validate_items.py                      # confirm 384 items / 12 cells / PASS

# Runner: place the JevBench harness (MIT, github.com/fstandhartinger/jevbench) at /tmp/jevbench
git clone --depth 1 https://github.com/fstandhartinger/jevbench.git /tmp/jevbench

python3 run_xi_v_bench.py <model_snapshot_path> <display_name> results/<name> --wide
python3 score_xi_v_bench.py results/<name> --json results/<name>.summary.json
```

`--wide` is required when loading a snapshot whose head width differs from the encoder width (e.g. encoder 1536 / head 1024).

## Item contract (summary)

- `id` = `<lang>-<tier>-<4digit>`, `group` = the key identifying the same item across languages
- `question.type` ∈ `noul | choice | score`
- **`noul` labels must be exactly `["no","yes"]`** — these are the probability keys returned by adapters. `question.criteria` keys must be exactly `true`/`false` (the option texts the model reads), and localized wording is preserved inside the criteria values and `instructions`.
- `score` labels are level index strings `["0","1",…]`
- `split` = `public`
- Do not expose the answer inside `state`
- Details: [`SPEC.md`](SPEC.md), [`builders/LOCALIZATION.md`](builders/LOCALIZATION.md)

## Leaderboard (first edition)

| Model | overall | easy | standard | hard | en | ko | zh | ja | lang_gap↓ | ECE↓ |
|---|---|---|---|---|---|---|---|---|---|---|
| XERON-1.0 (encoder 1536×44, head 1024×4, 1.329B) | 0.5495 | 0.8203 | 0.5234 | 0.3047 | 0.6146 | 0.5104 | 0.5000 | 0.5729 | 0.4688 | 0.0848 |
| _JevBench-derived English core (96 items, different bench)_ | 0.5541 | 0.9375 | 0.5556 | 0.3874 | — | — | — | — | — | 0.1101 |

XERON-1.0 details: 384/384 items answered (coverage 1.0), overall ECE 0.0848, Brier 0.5394, p50 latency 1.03 s, mean input 664 tokens.
Language consistency: 96 cross-language groups, all-languages-agree 0.5312, mean max−min gap 0.4688 (en 0.6146 · ja 0.5729 · ko 0.5104 · zh 0.5000).
Per-tier: easy 0.8203 · standard 0.5234 · hard 0.3047. Full per-cell JSON: [`results/xeron-1.0.summary.json`](results/xeron-1.0.summary.json).

## Citation / sources

- The 96 English base items were excerpted and adapted from **JevBench v1.3 public** (MIT). Each item records the original id, license, and source in `provenance`.
- The Korean, Chinese, and Japanese items are **localized** versions of the same items: people, companies, currencies, dates, laws, and practices were replaced with the context of the relevant locale (not literal translations). You can trace the source item via `provenance.source_kind="localized"` and `translation_of`.
- `## License` — MIT. Items derived from JevBench retain the original license (MIT) and attribution.
