#!/usr/bin/env python3
"""XI-V Bench 1.0 문항 검증기.

검사 항목:
  1) 파일 위치 = datasets/<lang>/<tier>.jsonl 이고 각 행의 id/lang/tier/provenance 가 일치
  2) JevBench Task 규약(question.type / split / labels / expected 포함관계 / state 정답 누출 금지)
  3) id 중복 금지, 셀별 개수 집계, group(교차언어) 일관성 요약, 라이선스 집계
사용: python validate_items.py [--root .]
"""
import argparse
import collections
import json
import os
import re
import sys

LANGS = ("en", "ko", "zh", "ja")
TIERS = ("easy", "standard", "hard")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--strict", action="store_true", help="경고도 실패로 처리")
    args = ap.parse_args()

    sys.path.insert(0, "/tmp/jevbench")
    try:
        from jevbench.tasks import Task
        has_harness = True
    except Exception:
        has_harness = False
        print("[warn] jevbench 하네스(/tmp/jevbench) 없음 → 규약 검사 축소")

    counts = collections.Counter()
    ids = {}
    groups = collections.defaultdict(set)
    licenses = collections.Counter()
    errors, warns = [], []

    for lang in LANGS:
        for tier in TIERS:
            path = os.path.join(args.root, "datasets", lang, f"{tier}.jsonl")
            if not os.path.exists(path):
                warns.append(f"missing file: datasets/{lang}/{tier}.jsonl")
                continue
            digits = 0
            with open(path) as f:
                for ln, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    where = f"datasets/{lang}/{tier}.jsonl:{ln}"
                    try:
                        d = json.loads(line)
                    except Exception as e:
                        errors.append(f"{where}: JSON 파싱 실패 {e}")
                        continue
                    for key in ("id", "family", "state", "question", "labels", "expected", "split", "provenance"):
                        if key not in d:
                            errors.append(f"{where}: 필수 키 누락 {key}")
                    i = d.get("id", "")
                    if not i.startswith(f"{lang}-{tier}-"):
                        errors.append(f"{where}: id 접두 불일치 ({i})")
                    prov = d.get("provenance") or {}
                    if prov.get("xi_lang") != lang:
                        errors.append(f"{where}: provenance.xi_lang={prov.get('xi_lang')!r} != {lang}")
                    if prov.get("xi_tier") != tier:
                        errors.append(f"{where}: provenance.xi_tier={prov.get('xi_tier')!r} != {tier}")
                    if not prov.get("license"):
                        errors.append(f"{where}: license 누락")
                    if i in ids:
                        errors.append(f"{where}: id 중복 ({i}, 이전 {ids[i]})")
                    ids[i] = where
                    digits += 1
                    if d.get("group"):
                        groups[d["group"]].add(lang)
                    licenses[prov.get("license", "?")] += 1
                    if has_harness:
                        try:
                            Task.from_dict(d).validate()
                        except Exception as e:
                            errors.append(f"{where}: JevBench 규약 위반 {e}")
                    st = d.get("state")
                    exp = d.get("expected")
                    # 짧은 라벨("no"/"M"/"low")은 문맥상 자연 등장하므로 8자 이상만 누출 신호로 본다.
                    if isinstance(st, str) and isinstance(exp, str) and len(exp) >= 8:
                        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(exp) + r"(?![A-Za-z0-9_])", st):
                            warns.append(f"{where}: state 에 정답 문자열({exp!r})이 등장 — 누출 검토")
            counts[(lang, tier)] = digits

    print("=== 셀별 문항 수 ===")
    print("      " + "".join(f"{t:>10}" for t in TIERS) + f"{'합':>10}")
    for lang in LANGS:
        row = [counts[(lang, t)] for t in TIERS]
        print(f"{lang:>5} " + "".join(f"{v:>10}" for v in row) + f"{sum(row):>10}")
    print("      " + "".join(f"{sum(counts[(l, t)] for l in LANGS):>10}" for t in TIERS)
          + f"{sum(counts.values()):>10}")
    print(f"\n총 문항: {sum(counts.values())}")
    full = [g for g, ls in groups.items() if len(ls) == 4]
    print(f"교차언어 group(4개 언어 전부): {len(full)}개 / group 총 {len(groups)}개")
    print(f"라이선스: {dict(licenses)}")
    if warns:
        print(f"\n경고 {len(warns)}건:")
        for w in warns[:15]:
            print("  -", w)
    if errors:
        print(f"\n오류 {len(errors)}건:")
        for e in errors[:25]:
            print("  -", e)
    ok = not errors and (not args.strict or not warns)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
