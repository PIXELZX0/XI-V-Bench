#!/usr/bin/env python3
"""XI-V Bench 1.0 — hard 티어 한국어 현지 각색 빌더.

입력: datasets/en/hard.jsonl (32문항)
출력: datasets/ko/hard.jsonl (32문항, 영문과 동일 순서)
자료: ko_hard/state/<NNNN>.txt (한국어 상태문) + ko_hard_data.py (지시·라벨·기준·근거)

규칙(LOCALIZATION.md): id/group/family/split/difficulty_notes 유지, labels 동수·동순서,
expected 동일 인덱스, question.type 유지, provenance = localized/ko/hard.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from ko_hard_data import ITEMS, LABEL_BASIS_KO  # noqa: E402

FROZEN = "2026-09-26T08:50:00Z"
STATE_DIR = HERE / "ko_hard" / "state"


def approx_tokens(text):
    n = len(text) if isinstance(text, str) else len(json.dumps(text, ensure_ascii=False))
    return max(1, round(n / 1.9))


def load_state(idx):
    """상태문 로드. 파일이 '{' 또는 '['로 시작하면 JSON 구조체로 파싱한다."""
    p = STATE_DIR / f"{idx:04d}.txt"
    text = p.read_text(encoding="utf-8").strip("\n")
    if text[:1] in ("{", "["):
        return json.loads(text)
    return text


def build(idx, en, spec):
    lmap = spec.get("labels") or {}
    qtype = en["question"]["type"]
    state = load_state(idx)

    labels = [lmap.get(l, l) for l in en["labels"]]
    exp_en = en["expected"]
    expected = exp_en if qtype == "score" else lmap.get(exp_en, exp_en)

    q = {"type": qtype, "instructions": spec["instructions"]}
    crit = spec.get("criteria")
    if crit is not None:
        if isinstance(crit, dict):
            q["criteria"] = {lmap.get(k, k): v for k, v in crit.items()}
        else:
            q["criteria"] = list(crit)

    prov = dict(en.get("provenance") or {})
    prov.update({
        "xi_lang": "ko",
        "xi_tier": "hard",
        "source_kind": "localized",
        "source": str(prov.get("source") or "") + " (XI-V localized)",
        "license": prov.get("license") or "MIT",
        "label_basis": spec.get("label_basis") or LABEL_BASIS_KO,
        "translation_of": en["id"],
        "reviewed": False,
        "frozen_utc": FROZEN,
        "approx_state_tokens": approx_tokens(state),
    })
    if "surface_answer" in prov:
        prov["surface_answer"] = lmap.get(prov["surface_answer"], prov["surface_answer"])
    if spec.get("rationale"):
        prov["rationale"] = spec["rationale"]
    if spec.get("why_hard"):
        prov["why_hard"] = spec["why_hard"]

    return {
        "id": f"ko-hard-{idx:04d}",
        "family": en["family"],
        "group": en["group"],
        "state": state,
        "question": q,
        "labels": labels,
        "expected": expected,
        "split": en["split"],
        "provenance": prov,
        "difficulty_notes": en.get("difficulty_notes"),
    }


def main():
    partial = "--partial" in sys.argv
    en_rows = [json.loads(l) for l in open(ROOT / "datasets" / "en" / "hard.jsonl", encoding="utf-8") if l.strip()]
    missing = [i for i in range(len(en_rows)) if i not in ITEMS]
    if missing and not partial:
        sys.exit(f"메타 누락 인덱스: {missing}")
    idxs = [i for i in range(len(en_rows)) if i in ITEMS]
    out_rows = [build(i, en_rows[i], ITEMS[i]) for i in idxs]
    out = ROOT / "datasets" / "ko" / "hard.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(out_rows)} 문항 → {out.relative_to(ROOT)}")
    bad = 0
    for i, ko in zip(idxs, out_rows):
        en = en_rows[i]
        assert ko["group"] == en["group"], i
        assert len(ko["labels"]) == len(en["labels"]), i
        assert ko["question"]["type"] == en["question"]["type"], i
        assert ko["expected"] in ko["labels"] or ko["question"]["type"] == "score", i
        if isinstance(en["state"], str):
            a, b = len(en["state"]), len(ko["state"])
            # 문자수는 한국어가 영어보다 2배 이상 조밀하므로, 정보량 비교는 추정 토큰수로 한다.
            ta, tb = a / 4.0, b / 1.7
            tr = tb / ta
            flag = "" if 0.80 <= tr <= 1.30 else "  <== 토큰 길이 이탈"
            if flag:
                bad += 1
            print(f"  {i:02d} en_chars={a:6d} ko_chars={b:6d} c_ratio={b/a:.2f} tok_ratio={tr:.2f}{flag}")
    print("토큰 길이 이탈:", bad)


if __name__ == "__main__":
    main()
