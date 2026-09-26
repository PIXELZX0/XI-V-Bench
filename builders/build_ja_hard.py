#!/usr/bin/env python3
"""XI-V Bench 1.0 — ja/hard 병합 빌더.

builders/ja_hard_parts/{NNNN}.json (현지 각색 필드) + datasets/en/hard.jsonl (구조/메타)
-> datasets/ja/hard.jsonl (32줄, 영문과 동일 순서, group 동일)

part 스키마:
  {"state_lines": [...]}            # 문자열 state (개행 결합)
  {"state_obj": {...}}              # 구조적 state
  "instructions": str, "criteria": obj|list|null, "labels": [...],
  "expected": <ja label or int>, "label_basis": str
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EN_PATH = os.path.join(ROOT, "datasets", "en", "hard.jsonl")
OUT_PATH = os.path.join(ROOT, "datasets", "ja", "hard.jsonl")
PARTS = os.path.join(HERE, "ja_hard_parts")
FROZEN = "2026-09-26T08:43:00Z"

en = [json.loads(l) for l in open(EN_PATH, encoding="utf-8") if l.strip()]
out = []
problems = []
ratios = []

for i, it in enumerate(en):
    p = os.path.join(PARTS, f"{i:04d}.json")
    if not os.path.exists(p):
        problems.append(f"{i:04d}: part 파일 없음")
        continue
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    if "state_obj" in d:
        state = d["state_obj"]
        st_len = len(json.dumps(state, ensure_ascii=False))
    else:
        state = "\n".join(d["state_lines"])
        st_len = len(state)
    qtype = it["question"]["type"]
    labels = d["labels"]
    if len(labels) != len(it["labels"]):
        problems.append(f"{i:04d}: labels 개수 불일치")
    if qtype in ("choice", "noul"):
        idx = it["labels"].index(it["expected"])
        if labels[idx] != d["expected"]:
            problems.append(f"{i:04d}: expected 위치 불일치 (index {idx})")
        expected = d["expected"]
    else:
        expected = it["expected"]
    crit = d.get("criteria")
    if isinstance(crit, dict):
        if set(crit.keys()) != set(labels):
            problems.append(f"{i:04d}: criteria 키가 labels 와 불일치")
    elif isinstance(crit, list):
        if len(crit) != len(labels):
            problems.append(f"{i:04d}: criteria(리스트) 길이 != labels")
    prov = {
        "xi_lang": "ja",
        "xi_tier": "hard",
        "source_kind": "localized",
        "source": it["provenance"]["source"] + " (XI-V localized)",
        "source_item_id": it["provenance"].get("source_item_id"),
        "license": it["provenance"]["license"],
        "label_basis": d["label_basis"],
        "translation_of": it["id"],
        "reviewed": False,
        "frozen_utc": FROZEN,
    }
    rec = {
        "id": f"ja-hard-{i:04d}",
        "family": it["family"],
        "group": it["group"],
        "state": state,
        "question": {"type": qtype, "instructions": d["instructions"], "criteria": crit},
        "labels": labels,
        "expected": expected,
        "split": "public",
        "difficulty_notes": it.get("difficulty_notes"),
        "provenance": prov,
    }
    out.append(rec)
    en_len = len(it["state"]) if isinstance(it["state"], str) else len(json.dumps(it["state"], ensure_ascii=False))
    ratios.append((i, en_len, st_len, round(st_len / en_len, 2)))
    # 영어 문장 잔존 휴리스틱 (state 안의 40자 이상 연속 ASCII 단어)
    import re
    for m in re.finditer(r"[A-Za-z][A-Za-z ,.'()/-]{40,}", json.dumps(state, ensure_ascii=False)):
        problems.append(f"{i:04d}: state 에 영문 문장 의심 → {m.group(0)[:60]!r}")

if problems:
    print("문제:")
    for x in problems:
        print("  -", x)

if out:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} items -> {OUT_PATH}")

print("\nstate 길이비(ja/en):")
for i, e, j, r in ratios:
    flag = "  <-- 확인" if (r < 0.55 or r > 1.35) else ""
    print(f"  {i:04d} en={e:>6} ja={j:>6} {r}{flag}")
sys.exit(1 if problems else 0)
