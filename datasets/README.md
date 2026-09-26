# XI-V Bench 1.0 datasets

배치 규칙 고정:
- 경로: `datasets/<lang>/<tier>.jsonl` (lang ∈ en|ko|zh|ja, tier ∈ easy|standard|hard)
- 한 줄 = 한 문항(JSON). 스키마는 `../schema.json`, 설계는 `../SPEC.md`
- id: `<lang>-<tier>-<4digit>` (예: `ko-hard-0012`)
- 언어·티어는 `provenance.xi_lang` / `provenance.xi_tier` 에도 기록(하네스 호환)
- 교차언어 동일 문항은 `group` 동일값 → 언어 일관성 지표
- 검증: `python ../validate_items.py`
