#!/usr/bin/env python3
"""noul 라벨 정규화 — 하네스 계약(labels=["no","yes"], 확률 키 yes/no)에 맞춘다.

현지 각색된 noul 라벨(예: ["아니오","예"], ["否","是"], ["いいえ","はい"])을
["no","yes"]로 되돌리고, 현지 표현은 criteria 설명문과 instructions 안내문에 보존한다.
(라벨을 현지어로 두면 어댑터가 반환하는 {"yes","no"} 확률 키와 대조에 실패해 전부 오답 처리됨)
"""
import json
import glob
import os

NO_WORDS = {"no", "아니오", "아니요", "아니", "否", "いいえ", "いえ"}
YES_WORDS = {"yes", "예", "네", "是", "はい", "응"}
HINT = {
    "en": " Answer with exactly `no` or `yes`.",
    "ko": " 출력은 정확히 `no` 또는 `yes` 로 하십시오.",
    "zh": " 输出必须为 `no` 或 `yes`。",
    "ja": " 出力は `no` または `yes` としてください。",
}


def canon(word, labels):
    if word in labels and word not in ("no", "yes"):
        return word
    return None


def main():
    changed = 0
    for path in sorted(glob.glob("datasets/*/*.jsonl")):
        lang = path.split(os.sep)[1]
        rows = [json.loads(l) for l in open(path) if l.strip()]
        touched = 0
        for r in rows:
            q = r["question"]
            if q.get("type") != "noul":
                continue
            labels = r["labels"]
            if labels == ["no", "yes"]:
                continue
            # 현지 표현 → no/yes 매핑 (위치가 아니라 의미 기준)
            loc = {}
            for w in labels:
                wl = w.strip()
                if wl in NO_WORDS:
                    loc[wl] = "no"
                elif wl in YES_WORDS:
                    loc[wl] = "yes"
                else:
                    raise ValueError(f"{r['id']}: noul 라벨 판별 불가 {wl!r}")
            if sorted(loc.values()) != ["no", "yes"]:
                raise ValueError(f"{r['id']}: noul 라벨 매핑 실패 {labels}")
            exp = r["expected"]
            r["expected"] = loc.get(str(exp).strip(), exp)
            if r["expected"] not in ("no", "yes"):
                raise ValueError(f"{r['id']}: expected 매핑 실패 {exp!r}")
            # criteria 키 매핑 + 현지 표현 보존
            crit = q.get("criteria")
            if isinstance(crit, dict):
                nc = {}
                for k, v in crit.items():
                    nk = loc.get(str(k).strip(), k)
                    if nk in ("no", "yes") and str(k).strip() != nk and str(k).strip() not in str(v):
                        v = f"{str(k).strip()} — {v}"
                    nc[nk] = v
                q["criteria"] = nc
            r["labels"] = ["no", "yes"]
            # instructions 에 출력 토큰 명시
            ins = q.get("instructions", "")
            if "`no`" not in ins and "`yes`" not in ins:
                q["instructions"] = ins.rstrip() + HINT.get(lang, HINT["en"])
            prov = r.setdefault("provenance", {})
            prov["noul_label_normalized"] = True
            prov["noul_label_original"] = labels
            touched += 1
        if touched:
            with open(path, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"{path}: noul {touched}건 정규화")
            changed += touched
    print(f"총 {changed}건 정규화")


if __name__ == "__main__":
    main()
