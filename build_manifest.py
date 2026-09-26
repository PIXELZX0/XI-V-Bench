#!/usr/bin/env python3
"""XI-V Bench 1.0 manifest 생성 — 셀 개수·해시·라이선스·언어/티어 통계·길이 통계."""
import collections
import glob
import hashlib
import json
import os
import statistics

LANGS = ("en", "ko", "zh", "ja")
TIERS = ("easy", "standard", "hard")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files, cells, fam = {}, collections.Counter(), collections.Counter()
    qtypes, licenses = collections.Counter(), collections.Counter()
    groups = collections.defaultdict(set)
    chars, n_tok_est = collections.defaultdict(list), []
    total = 0
    for lang in LANGS:
        for tier in TIERS:
            p = f"datasets/{lang}/{tier}.jsonl"
            if not os.path.exists(p):
                continue
            rows = [json.loads(l) for l in open(p) if l.strip()]
            files[p] = {"items": len(rows), "sha256": sha256(p)}
            cells[f"{lang}-{tier}"] = len(rows)
            for r in rows:
                total += 1
                fam[r["family"]] += 1
                qtypes[r["question"]["type"]] += 1
                licenses[r["provenance"]["license"]] += 1
                groups[r["group"]].add(lang)
                st = r["state"] if isinstance(r["state"], str) else json.dumps(r["state"], ensure_ascii=False)
                chars[lang].append(len(st))
                n_tok_est.append(max(1, int(len(st) / 2.6)))  # 거친 토큰 추정치
    full_groups = sum(1 for v in groups.values() if len(v) == len(LANGS))
    man = {
        "name": "XI-V Bench 1.0",
        "version": "1.0",
        "target": "System One models (single-pass decision making)",
        "languages": list(LANGS),
        "tiers": list(TIERS),
        "base_items": 96,
        "total_items": total,
        "cells": dict(sorted(cells.items())),
        "cross_language_groups": {"total": len(groups), "all_four_languages": full_groups},
        "question_types": dict(qtypes),
        "families": dict(sorted(fam.items(), key=lambda kv: -kv[1])),
        "licenses": dict(licenses),
        "state_chars_mean_by_lang": {k: round(statistics.fmean(v), 1) for k, v in chars.items()},
        "files": dict(sorted(files.items())),
        "frozen_utc": "2026-09-26T09:10:00Z",
        "notes": [
            "noul 라벨은 하네스 계약상 no/yes 고정(현지 표현은 criteria/instructions 에 보존)",
            "score 라벨은 레벨 인덱스 문자열 0..n",
            "모든 문항 license=MIT (JevBench public 유래 분은 원 라이선스 계승, 각색 고지 포함)",
        ],
    }
    with open("datasets/manifest.json", "w") as f:
        json.dump(man, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: man[k] for k in ("total_items", "cells", "cross_language_groups",
                                          "question_types", "licenses", "state_chars_mean_by_lang")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
