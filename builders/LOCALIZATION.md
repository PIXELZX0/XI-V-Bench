# XI-V Bench 1.0 — localization rules

Input: `datasets/en/{easy,standard,hard}.jsonl` (32 items each, 96 items total)
Output: `datasets/<lang>/<tier>.jsonl` (ko | zh | ja) — **keep the item count and order 1:1 with the source**

## Must-follow rules
1. `id` = `<lang>-<tier>-<NNNN>` (same 4-digit index as the English item)
2. `group` = **copy the English source `group` value verbatim** (cross-language identical-item key — never change it)
3. `labels` = **the same count and the same order** as the source; express each entry in the target language
4. `expected` = the label with the **same meaning / same index** as the source answer
5. `question.type` = same as the source (`noul` | `choice` | `score`)
6. `state` = **localized**. Keep the same decision structure and the same answer rationale, but replace people, companies, products, currencies, dates, laws, practices, and units with the context of the relevant locale. **No literal translation.**
   - Information volume and sentence count equivalent to the source (long Hard-tier text stays long; length within −20% ~ +30% of the source)
   - Keep the trap / wrong-answer lure structure intact (options that look correct if only one piece of evidence is seen)
7. `question.instructions`, `question.criteria` = localized (criteria keys must match the labels)
8. Keep `family`, `split`("public"), `difficulty_notes`
9. `provenance`: update `xi_lang`·`xi_tier`, `source_kind="localized"`, `translation_of="<English id>"`,
   `source` keeps the source attribution + ` (XI-V localized)`, `license` keeps the source license (currently MIT),
   `label_basis` in the local language, `reviewed=false`, `frozen_utc` = generation time (UTC ISO8601)
10. Output: JSONL, one item per line, UTF-8, `ensure_ascii=False`

## Forbidden
- Exposing the answer word directly inside `state`, or marking the answer (underline, asterisk)
- Missing or extra items, order changes, changing the meaning of `group`·`expected`
- Residual English source sentences (proper nouns, code, numbers, and quotations are exceptions)

## Completion condition
```bash
python3 validate_items.py      # RESULT: PASS, 32/32/32 for that language's cells
```
