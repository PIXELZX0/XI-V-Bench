#!/usr/bin/env python3
"""XI-V Bench 1.0 채점 — 티어×언어 12셀 + ECE/Brier + 언어 일관성(LCS).

사용:
  python score_xi_v_bench.py <results_prefix> [--items-root .] [--json out.json]
results_prefix 는 run_xi_v_bench.py 가 만든 `<prefix>.results.jsonl` 의 prefix.
"""
import argparse
import collections
import json
import math
import os
import statistics

LANGS = ("en", "ko", "zh", "ja")
TIERS = ("easy", "standard", "hard")
BINS = 10


def load_items(root):
    items = {}
    for lang in LANGS:
        for tier in TIERS:
            p = os.path.join(root, "datasets", lang, f"{tier}.jsonl")
            if not os.path.exists(p):
                continue
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        d = json.loads(line)
                        items[d["id"]] = d
    return items


def ece_top_label(pairs, bins=BINS):
    """pairs: [(confidence, correct_bool)] → (ECE, Brier_multiclass_placeholder)"""
    if not pairs:
        return None, None
    buckets = collections.defaultdict(list)
    for conf, hit in pairs:
        b = min(bins - 1, int(conf * bins))
        buckets[b].append((conf, hit))
    n = len(pairs)
    ece = 0.0
    for b, rows in buckets.items():
        acc = sum(1 for _, h in rows if h) / len(rows)
        conf = sum(c for c, _ in rows) / len(rows)
        ece += len(rows) / n * abs(acc - conf)
    return ece, None


def brier_multiclass(probs, labels, expected):
    if not probs:
        return None
    total = 0.0
    for lab in labels:
        y = 1.0 if lab == expected else 0.0
        p = float(probs.get(lab, 0.0))
        total += (p - y) ** 2
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("--items-root", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    items = load_items(args.items_root)
    recs = []
    with open(f"{args.prefix}.results.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))

    cells = collections.defaultdict(lambda: {"n": 0, "ok": 0, "correct": 0, "calib": [], "brier": [],
                                             "lat": [], "in_tok": []})
    overall = {"n": 0, "ok": 0, "correct": 0, "calib": [], "brier": [], "lat": [], "in_tok": []}
    by_id_correct, by_id_lang = {}, {}

    for r in recs:
        it = items.get(r["task_id"])
        if it is None:
            continue
        lang = it["provenance"]["xi_lang"]
        tier = it["provenance"]["xi_tier"]
        for bucket in (cells[(lang, tier)], cells[("ALL", tier)], cells[(lang, "ALL")], overall):
            bucket["n"] += 1
            if r.get("ok"):
                bucket["ok"] += 1
            if r.get("correct"):
                bucket["correct"] += 1
            if r.get("latency_s") is not None:
                bucket["lat"].append(r["latency_s"])
            it_tok = (r.get("usage") or {}).get("input_tokens")
            if isinstance(it_tok, (int, float)):
                bucket["in_tok"].append(it_tok)
        probs = r.get("probs") or {}
        if probs:
            top = max(probs, key=lambda k: float(probs[k]))
            conf = float(probs[top])
            hit = bool(r.get("correct"))
            cells[(lang, tier)]["calib"].append((conf, hit))
            cells[("ALL", tier)]["calib"].append((conf, hit))
            cells[(lang, "ALL")]["calib"].append((conf, hit))
            overall["calib"].append((conf, hit))
            b = brier_multiclass(probs, it["labels"], it["expected"])
            if b is not None:
                for bucket in (cells[(lang, tier)], cells[("ALL", tier)], cells[(lang, "ALL")], overall):
                    bucket["brier"].append(b)
        by_id_correct[r["task_id"]] = bool(r.get("correct"))
        by_id_lang[r["task_id"]] = lang

    def summarize(b):
        n = b["n"] or 1
        ece, _ = ece_top_label(b["calib"])
        return {
            "n": b["n"],
            "ok": b["ok"],
            "accuracy": round(b["correct"] / n, 4),
            "coverage": round(b["ok"] / n, 4),
            "ece": round(ece, 4) if ece is not None else None,
            "brier": round(statistics.fmean(b["brier"]), 4) if b["brier"] else None,
            "latency_p50_s": round(statistics.median(b["lat"]), 3) if b["lat"] else None,
            "latency_p95_s": round(sorted(b["lat"])[int(0.95 * (len(b["lat"]) - 1))], 3) if b["lat"] else None,
            "mean_input_tokens": round(statistics.fmean(b["in_tok"]), 1) if b["in_tok"] else None,
        }

    # 언어 일관성 (교차언어 group)
    groups = collections.defaultdict(dict)   # group -> {lang: correct}
    for tid, corr in by_id_correct.items():
        g = (items.get(tid) or {}).get("group")
        if g:
            groups[g][by_id_lang[tid]] = corr
    full = {g: v for g, v in groups.items() if len(v) == len(LANGS)}
    lcs = None
    if full:
        agree = sum(1 for v in full.values() if len(set(v.values())) == 1) / len(full)
        gaps = []
        for v in full.values():
            accs = [1.0 if x else 0.0 for x in v.values()]
            gaps.append(max(accs) - min(accs))
        lcs = {
            "groups_full": len(full),
            "all_langs_agree": round(agree, 4),
            "mean_maxmin_gap": round(statistics.fmean(gaps), 4),
            "lang_acc": {lg: round(sum(1 for v in full.values() if v[lg]) / len(full), 4)
                         for lg in LANGS if all(lg in v for v in full.values())},
        }

    out = {
        "overall": summarize(overall),
        "by_tier": {t: summarize(cells[("ALL", t)]) for t in TIERS},
        "by_lang": {lg: summarize(cells[(lg, "ALL")]) for lg in LANGS},
        "cells": {f"{lg}-{t}": summarize(cells[(lg, t)]) for lg in LANGS for t in TIERS},
        "language_consistency": lcs,
    }
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
