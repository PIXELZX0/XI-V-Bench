# XI-V Bench 1.0

**System One 모델용 다국어 의사결정 벤치마크** — 한 번의 패스로 결정을 내리는 모델(빠른 직관형)을 측정한다.
추론 연쇄·도구 왕복·자기검증 없이, 주어진 상태와 지시만으로 **정답 라벨 + 확신도**를 내야 한다.

| 항목 | 값 |
|---|---|
| 티어 | `easy` · `standard` · `hard` |
| 언어 | `en` · `ko` · `zh` · `ja` |
| 문항 수 | **384** (32문항 × 3티어 × 4언어) |
| 교차언어 세트 | **96 그룹** (4개 언어 전부 동일 문항) |
| 문항 유형 | `choice` 208 · `noul` 136 · `score` 40 |
| 라이선스 | MIT (JevBench public 유래 문항 포함, 각색 고지) |

## 무엇을 측정하나

1. **정확도** — overall / 티어별 / 언어별 / 12셀
2. **확신도 품질** — ECE(10-bin), Brier (모델이 확률 분포를 보고하는 경우)
3. **언어 일관성(LCS)** — 같은 문항의 4개 언어 버전에서 언어 간 정답 일치율·최대최소 격차·언어별 정답률
4. **효율** — p50/p95 지연, 문항당 입력 토큰

티어 정의
- `easy`: 문맥에서 정답이 직접 확인됨
- `standard`: 2~3단계 결합(조건 충족·제외 규칙)
- `hard`: 근거가 문맥 여러 곳에 분산 + 상충 정보/부분 조건 함정 (장문 컨텍스트 포함)

## 레이아웃

```
datasets/<lang>/<tier>.jsonl   # 문항 (한 줄 = 한 문항, UTF-8 JSON)
datasets/manifest.json         # 셀 개수·해시·라이선스·통계
schema.json                    # 문항 스키마
SPEC.md                        # 설계·채점·소스 명세
builders/                      # 문항 생성·현지 각색·정규화 스크립트
validate_items.py              # 문항 검증(셀 개수·id 중복·정답 누출·하네스 규약)
run_xi_v_bench.py              # 러너 (JevBench 하네스 재사용)
score_xi_v_bench.py            # 채점(tier×lang + ECE/Brier + LCS)
```

## 빠른 시작

```bash
python3 validate_items.py                      # 384문항 / 12셀 / PASS 확인

# 러너: JevBench 하네스(MIT, github.com/fstandhartinger/jevbench)를 /tmp/jevbench 에 둔다
git clone --depth 1 https://github.com/fstandhartinger/jevbench.git /tmp/jevbench

python3 run_xi_v_bench.py <모델_스냅샷_경로> <표시이름> results/<이름> --wide
python3 score_xi_v_bench.py results/<이름> --json results/<이름>.summary.json
```

`--wide` 는 head 폭이 인코더 폭과 다른 스냅샷(예: encoder 1536 / head 1024)을 로드할 때 필요하다.

## 문항 규약 (요약)

- `id` = `<lang>-<tier>-<4digit>`, `group` = 교차언어 동일 문항 키
- `question.type` ∈ `noul | choice | score`
- **`noul` 라벨은 반드시 `["no","yes"]`** (현지 표현은 `question.criteria`·`instructions`에 보존)
- `score` 라벨은 레벨 인덱스 문자열 `["0","1",…]`
- `split` = `public`
- `state` 안에 정답을 노출하지 않는다
- 상세: [`SPEC.md`](SPEC.md), [`builders/LOCALIZATION.md`](builders/LOCALIZATION.md)

## 리더보드 (초판)

| 모델 | overall | easy | standard | hard | en | ko | zh | ja | lang_gap↓ | ECE↓ |
|---|---|---|---|---|---|---|---|---|---|---|
| _측정 예정_ | | | | | | | | | | |

## 인용 / 출처

- 영어 베이스 문항 96개는 **JevBench v1.3 public**(MIT)에서 발췌·각색했다. 각 문항에 원본 id·라이선스·출처를 `provenance`에 명시한다.
- 한국어·중국어·일본어 문항은 동일 문항의 **현지 각색(localized)** 이며, 인물·회사·통화·날짜·법규·관행을 해당 언어권 맥락으로 치환했다(직역 아님). `provenance.source_kind="localized"`, `translation_of`로 원문을 추적할 수 있다.
- `## License` — MIT. JevBench 유래 문항은 원 라이선스(MIT)와 저작자 표시를 유지한다.
