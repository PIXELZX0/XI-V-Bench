#!/usr/bin/env python3
"""XI-V Bench 1.0 — 영어 베이스 세트 생성 (JevBench public 231 → 32/티어 × 3 = 96문항).

규칙:
  - easy ← datasets/public/easy.jsonl(48) / standard ← original.jsonl(72) / hard ← hard.jsonl(111)
  - 각 티어에서 앞 32개를 결정적으로 선택(파일 순서 고정) → group = 영문 id (4개 언어 동일 문항 묶음 키)
  - id = en-<tier>-<0000..>  (00은 원본 파일 순서)
  - provenance 에 xi_lang/xi_tier/source_kind=adapted/원본 출처·라이선스 유지 + label_basis/rationale 보존
"""
import json
import os
import pathlib

SRC = "/tmp/jevbench/datasets/public"
FILES = {"easy": "easy.jsonl", "standard": "original.jsonl", "hard": "hard.jsonl"}
PER_TIER = 32
HERE = pathlib.Path(__file__).resolve().parent.parent


def main():
    for tier, fname in FILES.items():
        rows = [json.loads(l) for l in open(os.path.join(SRC, fname)) if l.strip()]
        picked = rows[:PER_TIER]
        out = HERE / "datasets" / "en" / f"{tier}.jsonl"
        with out.open("w") as f:
            for i, d in enumerate(picked):
                prov = dict(d.get("provenance") or {})
                prov.update({
                    "xi_lang": "en", "xi_tier": tier, "source_kind": "adapted",
                    "source": "JevBench v1.3 public (MIT)",
                    "source_item_id": d["id"],
                    "origin_tier": tier if tier != "standard" else "original",
                    "license": prov.get("license") or "MIT",
                    "translation_of": None,
                    "reviewed": True,
                    "frozen_utc": "2026-09-26T08:00:00Z",
                })
                item = {
                    "id": f"en-{tier}-{i:04d}",
                    "family": d.get("family"),
                    "group": d["id"],                    # 언어 간 동일 문항 키
                    "state": d["state"],
                    "question": d["question"],
                    "labels": d["labels"],
                    "expected": d["expected"],
                    "split": "public",
                    "provenance": prov,
                    "difficulty_notes": d.get("difficulty_notes"),
                }
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"{tier}: {len(picked)} 문항 → {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
