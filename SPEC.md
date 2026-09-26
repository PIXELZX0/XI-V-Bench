# XI-V Bench 1.0 — Design specification (draft v0.1)

**Target**: System One models (fast single-pass decision making — judge in one step without a chain of reasoning)
**Composition**: `Easy` / `Standard` / `Hard` 3 tiers × 4 languages = 12 cells
**Languages**: `en`(English) · `ko`(한국어) · `zh`(中文) · `ja`(日本語)

---

## 1. Item schema (JevBench-compatible + language extension)

```jsonc
{
  "id": "ko-standard-0007",          // {lang}-{tier}-{4digit}
  "lang": "ko",                       // en | ko | zh | ja
  "tier": "standard",                 // easy | standard | hard
  "family": "policy",                 // FAMILIES(routing|adequacy|policy|intent|ordinal|extraction) or HARD_FAMILIES(long_policy|tradeoff|ambiguous|trap|multi_hop|temporal_numeric|adversarial|probability)
  "group": "tr-014",                  // translation/variant item bundle (identifier of the same item across languages) — used for language-consistency measurement
  "state": "<situation/context — instructions, evidence documents, tables, dialogue, etc.>",
  "question": {
    "qtype": "choice",                // choice | score | noul
    "instructions": "Choose the most appropriate option. Report confidence along with your answer.",
    "criteria": {                     // evaluation criteria (optional): decision rule per label — especially important for noul/choice
      "true": "...", "false": "..."
    }
  },
  "labels": ["A", "B", "C", "D"],     // option texts (2–8)
  "expected": "C",                    // correct label
  "provenance": {
    "source_kind": "authored | adapted | translated",
    "source": "XI-V authored / KMMLU / JMMLU / CMMLU / MMLU / CLUE ...",
    "source_item_id": "...",
    "license": "MIT | CC-BY-SA-4.0 | ...",
    "label_basis": "one-line rationale for the answer",
    "translation_of": "en-standard-0007",   // source id, if this is a translated item
    "reviewed": true, "frozen_utc": "2026-09-26T08:00:00Z"
  },
  "split": "public",                  // JevBench convention: public | private (the eval set is public)
  "difficulty_notes": "why this tier (number of reasoning steps, instruction ambiguity, evidence dispersion)"
}
```

**qtype definitions**
- `choice` — one correct label among the labels (default)
- `score` — ordinal/distribution judgment (e.g. emotion intensity, risk level) → the answer is a grade/distribution
- `noul` — yes/no binary judgment (`labels=["no","yes"]`) — these are the probability keys returned by adapters. `question.criteria` keys must be exactly `true`/`false` (the option texts the model reads); localized wording is preserved inside the criteria values and the instructions. An unmet condition is "no".

**Tier definitions (fixed)**
| Tier | Requirement | Instruction length per item | Wrong-answer lure |
|---|---|---|---|
| Easy | the answer is directly verifiable from the context | ~1 sentence | surface-similar labels |
| Standard | 2–3 step combination (condition satisfaction, exclusion rules) | 1–2 paragraphs | labels that satisfy only part of the conditions |
| Hard | evidence dispersed across multiple places in the context + conflicting information / P0.5 trap | long (thousands of tokens) | labels that look correct if only one piece of evidence is seen |

---

## 2. Cell composition (proposed)

| Tier | en | ko | zh | ja | Cell sum | Total |
|---|---|---|---|---|---|---|
| Easy | 32 | 32 | 32 | 32 | 128 | |
| Standard | 32 | 32 | 32 | 32 | 128 | |
| Hard | 32 | 32 | 32 | 32 | 128 | **384** |

- Minimum requirement: each cell ≥ 30 (secures a ±~9%p confidence interval per tier)
- **Cross-language set**: secure 4 language versions of the same item (same `group`) for **Easy 16 / Standard 16 / Hard 16** → enables language-consistency metrics
- The rest is **native authoring** per language (local norms, culture, and policy context, not literal translation)

---

## 3. Scoring (reflecting System One characteristics)

1. **Accuracy**: `overall` / per `tier` / per `lang` / 12 `tier×lang` cells
2. **Confidence quality**: ECE (10-bin), Brier, mean TVD (when a label distribution is reported)
3. **Language consistency (LCS)**: accuracy deviation across languages for items with the same `group`
   - `lang_gap = max_lang(acc) − min_lang(acc)` (group average)
   - Translation robustness: rate of answer disagreement within the same group
4. **Efficiency**: p50/p95 latency, input tokens per item → estimated cost
5. **Composite**: JevBench-style axes (intelligence / calibration / speed / cost) + per-language decomposition
   - `XI-V Score = 0.4·intelligence + 0.3·calibration + 0.15·speed + 0.15·cost` (draft weights)
6. Leaderboard columns (proposed): `model | overall | easy | standard | hard | en | ko | zh | ja | lang_gap↓ | ECE↓ | p50 | score`

---

## 4. Data source mapping (first candidates)

| Language | Easy (direct verification) | Standard (combination) | Hard (dispersed evidence) |
|---|---|---|---|
| en | reuse JevBench easy 48 + own authoring | reuse JevBench original(standard) 72 | reuse JevBench hard 111 |
| ko | KorNLI/NSMC (explicit labels) | KMMLU, KLUE-STS | long policy/contract adaptation, KMMLU-hard |
| zh | CLUE-TNEWS, OCNLI | CMMLU, CLUE-CMNLI/AFQMC | C3 (long reading comprehension) · composite reasoning |
| ja | MARC-ja, JSTS | JNLI, JMMLU | long policy/technical document adaptation |

- Reuse of existing builders: `scripts/build_korean_dataset.py`, `build_mmlu_dataset.py`, `scripts/specs_multilingual.py`(`global_mmlu`, `belebele`, `mmlu_prox`), `scripts/specs_extra.py`(KMMLU·JNLI·CLUE·C3)
- **Training-leak guard**: if a source overlaps with what was used to train XERON (train_items_x10_8192), remove it via `scripts/check_eval_leak.py`
- License: `provenance.license` is required per item; cc-by-nd-4.0 (KMMLU) **forbids modification** → keep as-is

---

## 5. Deliverable layout

```
bench/xi-v-bench-1.0/
├── SPEC.md                     # this document
├── schema.json                 # item schema (for validation)
├── datasets/
│   ├── en/{easy,standard,hard}.jsonl
│   ├── ko/{easy,standard,hard}.jsonl
│   ├── zh/{easy,standard,hard}.jsonl
│   ├── ja/{easy,standard,hard}.jsonl
│   └── manifest.json           # per-cell counts, hashes, license summary
├── builders/                   # per-language collection, localization, and translation scripts
├── run_xi_v_bench.py           # runner (model adapters: laya/XERON local, API)
├── score_xi_v_bench.py         # scoring (tier×lang, ECE, LCS)
└── results/                    # per-model result jsonl + summary json
```

---

## 6. Open questions (owner decision needed)

1. **Item count/composition**: the 32×12=384 plan above vs. reduced (30×12=360) vs. expanded. Whether to increase the Hard share further.
2. **Item source mix**: (a) reuse 231 JevBench English items + new ko/zh/ja, (b) mainly recompose public datasets, (c) author all items newly (highest quality, most time)
3. **Translation method**: should the cross-language set be (i) professional translation (literal) or (ii) localized adaptation (preserve meaning, replace culture)?
4. **Evaluation targets**: is System One defined by XERON (local laya snapshot), or should external API models also be included to form a comparison group?
5. **Whether confidence is mandatory**: require confidence (distribution) for every item vs. accuracy only


---

## 7. Harness compatibility rules (important)

The existing JevBench harness (`/tmp/jevbench`, `jevbench.tasks.Task`) is reused as-is. Therefore:

- `question.type` ∈ `noul | choice | score` (the internal key name is **`type`**, not `qtype`)
- `split` ∈ `public | private` → XI-V uses `public`
- `family` ∈ `FAMILIES`(routing/adequacy/policy/intent/ordinal/extraction) or `HARD_FAMILIES`(long_policy/tradeoff/ambiguous/trap/multi_hop/temporal_numeric/adversarial/probability)
- No answer leakage in `state` (the `expected`/`label`/`ground_truth`/`answer_key` keys are forbidden)
- **Language/tier are recorded in the id prefix + `provenance.xi_lang` / `provenance.xi_tier`** (since they are not fields in the Task dataclass)
- Identical cross-language items share the same value in `group` → enables language-consistency metrics
- The runner keeps the adapter interface as-is: `agent.predict(state, {"decision": {type, instructions, criteria}})`
