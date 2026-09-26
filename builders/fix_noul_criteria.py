#!/usr/bin/env python3
"""noul criteria 키 정정 — 하네스 계약: noul 의 criteria 키는 'true'/'false' 만 허용.

(labels 는 확률 키 'no'/'yes', criteria 는 모델이 읽는 선택지 텍스트 키 'true'/'false')
현지 표현은 값 안에 보존한다. 예: criteria["false"] = "아니오 — 조건이 충족되지 않았거나 금지에 해당한다."
"""
import glob
import json

NO_WORDS = ("no", "아니오", "아니요", "아니", "否", "いいえ", "いえ")
YES_WORDS = ("yes", "예", "네", "是", "はい", "응")


def fix(q):
    crit = q.get("criteria")
    if crit is None:
        return False
    if isinstance(crit, list):          # score 유형: 리스트는 그대로
        return False
    if not isinstance(crit, dict):
        return False
    out = {}
    for k, v in crit.items():
        kl = str(k).strip()
        if kl in ("true", "false"):
            out[kl] = v
            continue
        if kl in YES_WORDS or kl.lower() == "true":
            nk = "true"
        elif kl in NO_WORDS or kl.lower() == "false":
            nk = "false"
        else:
            nk = kl  # 알 수 없는 키는 유지(검증기에서 별도 보고)
        sv = str(v)
        if kl not in ("true", "false") and kl not in sv:
            sv = f"{kl} — {sv}"
        out[nk] = sv
    q["criteria"] = out
    return True


def main():
    total = 0
    for path in sorted(glob.glob("datasets/*/*.jsonl")):
        rows = [json.loads(l) for l in open(path) if l.strip()]
        n = 0
        for r in rows:
            if r["question"].get("type") == "noul" and fix(r["question"]):
                n += 1
        if n:
            with open(path, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"{path}: noul criteria 정정 {n}건")
            total += n
    print(f"총 {total}건")


if __name__ == "__main__":
    main()
