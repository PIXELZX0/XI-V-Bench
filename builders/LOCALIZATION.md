# XI-V Bench 1.0 — 현지 각색(localization) 규칙

입력: `datasets/en/{easy,standard,hard}.jsonl` (각 32문항, 총 96문항)
출력: `datasets/<lang>/<tier>.jsonl` (ko | zh | ja) — **문항 수·순서를 원문과 1:1로 유지**

## 반드시 지킬 것
1. `id` = `<lang>-<tier>-<NNNN>` (영문과 동일한 4자리 인덱스)
2. `group` = 영문 원문의 `group` 값 **그대로 복사** (교차언어 동일 문항 키 — 절대 변경 금지)
3. `labels` = 원문과 **같은 개수·같은 순서**, 각 항목을 해당 언어로 표현
4. `expected` = 원문 정답과 **같은 의미/같은 인덱스**의 라벨
5. `question.type` = 원문 그대로 (`noul` | `choice` | `score`)
6. `state` = **현지 각색**. 같은 결정 구조·같은 정답 근거를 유지하되 인물·회사·제품·통화·날짜·법규·관행·단위를 해당 언어권 맥락으로 치환한다. **직역 금지.**
   - 정보량·문장 수는 원문과 동등 (hard 티어의 장문은 장문으로 유지, 길이 원문 대비 −20% ~ +30%)
   - 함정/오답 유혹 구조(근거 한 조각만 보면 맞아 보이는 선택지)는 그대로 살린다
7. `question.instructions`, `question.criteria` = 현지어로 각색 (criteria의 키는 라벨과 일치해야 함)
8. `family`, `split`("public"), `difficulty_notes` 유지
9. `provenance`: `xi_lang`·`xi_tier` 갱신, `source_kind="localized"`, `translation_of="<영문 id>"`,
   `source` 는 원문 표기 유지 + ` (XI-V localized)`, `license` 는 원문 라이선스 유지(현재 MIT),
   `label_basis` 는 현지어로, `reviewed=false`, `frozen_utc` 는 생성 시각(UTC ISO8601)
10. 출력: JSONL, 한 줄에 한 문항, UTF-8, `ensure_ascii=False`

## 금지
- `state` 안에 정답 단어를 직접 노출하거나 정답에 표시(밑줄·별표)를 남기는 것
- 문항 누락/추가, 순서 변경, `group`·`expected` 의미 변경
- 영어 원문 문장 잔존 (고유명사·코드·수치·인용은 예외)

## 완료 조건
```bash
python3 validate_items.py      # RESULT: PASS, 해당 언어 셀 32/32/32
```
