#!/usr/bin/env python3
"""Assemble datasets/zh/hard.jsonl from per-item work files.

For each en item index NNNN:
  state_NNNN.txt  -> Chinese state (raw text, real newlines)
  meta_NNNN.json  -> localized question/labels/expected/label_basis/rationale/why_hard/surface_answer
English file supplies id/family/group/source/source_item_id/origin_tier/author_model/split.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EN = os.path.join(ROOT, "datasets", "en", "hard.jsonl")
OUT = os.path.join(ROOT, "datasets", "zh", "hard.jsonl")
FROZEN = "2026-09-26T08:45:26Z"

en = [json.loads(l) for l in open(EN, encoding="utf-8") if l.strip()]
assert len(en) == 32, len(en)

items = []
for i, src in enumerate(en):
    n = f"{i:04d}"
    jpath = os.path.join(HERE, f"state_{n}.json")
    if os.path.exists(jpath):
        st = json.load(open(jpath, encoding="utf-8"))
    else:
        st = open(os.path.join(HERE, f"state_{n}.txt"), encoding="utf-8").read()
        if st.endswith("\n"):
            st = st[:-1]
    meta = json.load(open(os.path.join(HERE, f"meta_{n}.json"), encoding="utf-8"))
    p = src["provenance"]
    approx_tokens = (int(round(len(st) / 1.6)) if isinstance(st, str)
                     else p.get("approx_state_tokens"))
    prov = {
        "approx_state_tokens": approx_tokens,
        "author_model": p.get("author_model"),
        "frozen_utc": FROZEN,
        "label_basis": meta["label_basis"],
        "license": p.get("license"),
        "rationale": meta["rationale"],
        "source": p.get("source") + " (XI-V localized)",
        "source_item_id": p.get("source_item_id"),
        "origin_tier": p.get("origin_tier"),
        "source_kind": "localized",
        "surface_answer": meta.get("surface_answer"),
        "translation_of": src["id"],
        "why_hard": meta["why_hard"],
        "xi_lang": "zh",
        "xi_tier": "hard",
        "reviewed": False,
    }
    question = {"type": src["question"]["type"], "instructions": meta["instructions"]}
    if src["question"].get("criteria") is not None:
        question["criteria"] = meta["criteria"]
    item = {
        "id": f"zh-hard-{i:04d}",
        "family": src["family"],
        "group": src["group"],
        "state": st,
        "question": question,
        "labels": meta["labels"],
        "expected": meta["expected"],
        "split": "public",
        "provenance": prov,
        "difficulty_notes": src.get("difficulty_notes"),
    }
    # sanity: expected in labels, criteria keys == labels
    if src["question"]["type"] == "score":
        assert str(item["expected"]) in item["labels"], (i, item["expected"])
    else:
        assert item["expected"] in item["labels"], (i, item["expected"])
    if src["question"].get("criteria") is not None:
        c = item["question"]["criteria"]
        if src["question"]["type"] == "noul":
            assert set(c.keys()) == {"true", "false"}, (i, set(c))
        elif isinstance(c, dict):
            assert set(c.keys()) == set(item["labels"]), (i, set(c) ^ set(item["labels"]))
        else:
            assert len(c) == len(item["labels"]), i
    # no answer leakage into state
    if isinstance(item["expected"], str) and len(item["expected"]) >= 8 and isinstance(st, str):
        if re.search(re.escape(item["expected"]), st):
            raise SystemExit(f"LEAK item {i}: {item['expected']!r} in state")
    items.append(item)

with open(OUT, "w", encoding="utf-8") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
print("wrote", OUT, len(items), "items")
