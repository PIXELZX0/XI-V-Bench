# XI-V Bench 1.0 datasets

Fixed placement rules:
- Path: `datasets/<lang>/<tier>.jsonl` (lang ∈ en|ko|zh|ja, tier ∈ easy|standard|hard)
- One line = one item (JSON). Schema in `../schema.json`, design in `../SPEC.md`
- id: `<lang>-<tier>-<4digit>` (e.g. `ko-hard-0012`)
- Language and tier are also recorded in `provenance.xi_lang` / `provenance.xi_tier` (harness compatibility)
- Identical items across languages share the same `group` value → language-consistency metrics
- Validation: `python ../validate_items.py`
