# XI-V Bench 1.0 — 설계 명세 (draft v0.1)

**대상**: System One 모델 (빠른 단일 패스 의사결정 — 추론 연쇄 없이 한 번에 판단)
**구성**: `Easy` / `Standard` / `Hard` 3개 티어 × 4개 언어 = 12개 셀
**언어**: `en`(English) · `ko`(한국어) · `zh`(中文) · `ja`(日本語)

---

## 1. 문항 스키마 (JevBench 호환 + 언어 확장)

```jsonc
{
  "id": "ko-standard-0007",          // {lang}-{tier}-{4digit}
  "lang": "ko",                       // en | ko | zh | ja
  "tier": "standard",                 // easy | standard | hard
  "family": "policy",                 // FAMILIES(routing|adequacy|policy|intent|ordinal|extraction) 또는 HARD_FAMILIES(long_policy|tradeoff|ambiguous|trap|multi_hop|temporal_numeric|adversarial|probability)
  "group": "tr-014",                  // 번역/변형 문항 묶음(언어 간 동일 문항 식별자) — 언어 일관성 측정용
  "state": "<상황/문맥 — 지시·근거 문서, 표, 대화 등>",
  "question": {
    "qtype": "choice",                // choice | score | noul
    "instructions": "가장 알맞은 것을 고르시오. 확신도를 함께 보고하시오.",
    "criteria": {                     // 평가 기준(선택): 라벨별 판정 기준 — noul/choice 에서 특히 중요
      "true": "...", "false": "..."
    }
  },
  "labels": ["A", "B", "C", "D"],     // 선택지 텍스트(2~8개)
  "expected": "C",                    // 정답 라벨
  "provenance": {
    "source_kind": "authored | adapted | translated",
    "source": "XI-V authored / KMMLU / JMMLU / CMMLU / MMLU / CLUE ...",
    "source_item_id": "...",
    "license": "MIT | CC-BY-SA-4.0 | ...",
    "label_basis": "정답 근거 한 줄",
    "translation_of": "en-standard-0007",   // 번역 문항이면 원문 id
    "reviewed": true, "frozen_utc": "2026-09-26T08:00:00Z"
  },
  "split": "public",                  // JevBench 규약: public | private (평가셋은 public)
  "difficulty_notes": "왜 이 티어인가(추론 단계 수, 지시 모호성, 근거 분산도)"
}
```

**qtype 정의**
- `choice` — 라벨 중 정답 하나 (기본)
- `score` — 서수/분포 판단(예: 감정 강도, 위험도) → 정답은 등급/분포
- `noul` — 예/아니오 계열 이진 판정 (`labels=["no","yes"]`), 조건 불충족은 "아니오"

**티어 정의(고정)**
| 티어 | 요구 | 문항당 지시 길이 | 오답 유혹 |
|---|---|---|---|
| Easy | 문맥에서 정답이 직접 확인됨 | ~1문장 | 표면적 유사 라벨 |
| Standard | 2~3단계 결합(조건 충족·제외 규칙) | 1~2단락 | 부분 조건만 만족하는 라벨 |
| Hard | 근거가 문맥 여러 곳에 분산 + 상충 정보/P0.5 함정 | 장문(수천 토큰) | 근거 한 조각만 보면 맞아 보이는 라벨 |

---

## 2. 셀 구성 (제안)

| 티어 | en | ko | zh | ja | 셀 합 | 전체 |
|---|---|---|---|---|---|---|
| Easy | 32 | 32 | 32 | 32 | 128 | |
| Standard | 32 | 32 | 32 | 32 | 128 | |
| Hard | 32 | 32 | 32 | 32 | 128 | **384** |

- 최소 요건: 각 셀 ≥ 30 (tier별 신뢰구간 ±~9%p 확보)
- **교차언어 세트**: 동일 문항의 4개 언어 버전(`group` 동일)을 **Easy 16 / Standard 16 / Hard 16** 확보 → 언어 일관성 지표 계산 가능
- 나머지는 각 언어 **네이티브 저작**(직역이 아닌 현지 규범·문화·정책 맥락)

---

## 3. 채점 (System One 특성 반영)

1. **정확도**: `overall` / `tier별` / `lang별` / `tier×lang` 12셀
2. **확신도 품질**: ECE(10-bin), Brier, mean TVD (라벨 분포 보고 시)
3. **언어 일관성 (LCS)**: 동일 `group` 문항에서 언어 간 정답률 편차
   - `lang_gap = max_lang(acc) − min_lang(acc)` (group 평균)
   - 번역 강건성: 같은 group 내 정답 불일치율
4. **효율**: p50/p95 지연, 문항당 입력 토큰 → 예상 비용
5. **종합**: JevBench 방식의 축(intelligence / calibration / speed / cost) + 언어별 분해
   - `XI-V Score = 0.4·intelligence + 0.3·calibration + 0.15·speed + 0.15·cost` (가중 초안)
6. 리더보드 컬럼(제안): `model | overall | easy | standard | hard | en | ko | zh | ja | lang_gap↓ | ECE↓ | p50 | score`

---

## 4. 데이터 소스 매핑(1차 후보)

| 언어 | Easy (직접 확인) | Standard (결합) | Hard (분산 근거) |
|---|---|---|---|
| en | JevBench easy 48 재사용 + 자체저작 | JevBench original(standard) 72 재사용 | JevBench hard 111 재사용 |
| ko | KorNLI/NSMC(명시 라벨) | KMMLU, KLUE-STS | 장문 정책·계약 각색, KMMLU-hard |
| zh | CLUE-TNEWS, OCNLI | CMMLU, CLUE-CMNLI/AFQMC | C3(장문 독해)·복합 추론 |
| ja | MARC-ja, JSTS | JNLI, JMMLU | 장문 정책·기술문서 각색 |

- 기존 빌더 재사용: `scripts/build_korean_dataset.py`, `build_mmlu_dataset.py`, `scripts/specs_multilingual.py`(`global_mmlu`, `belebele`, `mmlu_prox`), `scripts/specs_extra.py`(KMMLU·JNLI·CLUE·C3)
- **학습 누수 가드**: XERON 학습에 쓰인 소스(train_items_x10_8192)와 겹치면 `scripts/check_eval_leak.py`로 제거
- 라이선스: 문항별 `provenance.license` 필수, cc-by-nd-4.0(KMMLU)은 **개작 금지** → 원형 유지

---

## 5. 산출물 레이아웃

```
bench/xi-v-bench-1.0/
├── SPEC.md                     # 이 문서
├── schema.json                 # 문항 스키마(검증용)
├── datasets/
│   ├── en/{easy,standard,hard}.jsonl
│   ├── ko/{easy,standard,hard}.jsonl
│   ├── zh/{easy,standard,hard}.jsonl
│   ├── ja/{easy,standard,hard}.jsonl
│   └── manifest.json           # 셀별 개수·해시·라이선스 요약
├── builders/                   # 언어별 수집·각색·번역 스크립트
├── run_xi_v_bench.py           # 러너 (모델 어댑터: laya/XERON 로컬, API)
├── score_xi_v_bench.py         # 채점 (tier×lang, ECE, LCS)
└── results/                    # 모델별 결과 jsonl + 요약 json
```

---

## 6. 미결(주인님 결정 필요)

1. **문항 수/구성**: 위 32×12=384안 vs 축소(30×12=360) vs 확대. Hard 비중 더 늘릴지.
2. **문항 출처 비중**: (a) JevBench 231 영어 재사용 + ko/zh/ja 신규, (b) 공개 데이터셋 재구성 위주, (c) 전량 신규 저작(품질 최고·시간 최다)
3. **번역 방식**: 교차언어 세트를 (i) 전문 번역(직역) (ii) 현지 각색(의미 유지, 문화 치환) 중 어느 쪽으로?
4. **평가 대상**: System One = XERON(로컬 laya 스냅샷) 기준인지, 외부 API 모델도 같이 넣어 비교군을 만들지
5. **정답 확신도 필수 여부**: 모든 문항에 확신도(분포) 요구 vs accuracy만


---

## 7. 하네스 호환 규칙 (중요)

기존 JevBench 하네스(`/tmp/jevbench`, `jevbench.tasks.Task`)를 그대로 재사용한다. 따라서:

- `question.type` ∈ `noul | choice | score` (내부 키 이름은 **`type`**, `qtype` 아님)
- `split` ∈ `public | private` → XI-V는 `public`
- `family` ∈ `FAMILIES`(routing/adequacy/policy/intent/ordinal/extraction) 또는 `HARD_FAMILIES`(long_policy/tradeoff/ambiguous/trap/multi_hop/temporal_numeric/adversarial/probability)
- `state`에 정답 누출 금지(`expected`/`label`/`ground_truth`/`answer_key` 키 금지)
- **언어/티어는 id 접두 + `provenance.xi_lang` / `provenance.xi_tier`에 기록** (Task 데이터클래스에 없는 필드이므로)
- 교차언어 동일 문항은 `group`에 같은 값 → 언어 일관성 지표 계산
- 러너는 어댑터 인터페이스 그대로: `agent.predict(state, {"decision": {type, instructions, criteria}})`
