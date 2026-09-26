#!/usr/bin/env python3
"""XI-V Bench 1.0 러너 — JevBench 하네스를 그대로 재사용한다.

사용:
  python run_xi_v_bench.py <model_path_or_endpoint> <label> <out_prefix> \
      [--langs en,ko,zh,ja] [--tiers easy,standard,hard] [--wide] [--threads 4]

  --wide  : head_size != encoder width 인 XERON 스냅샷(예: 1024 head)에 필요한 laya 패치 적용
결과: <out_prefix>.results.jsonl (+ .raw/ , .ledger.jsonl)
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "scripts"))

LANGS = ("en", "ko", "zh", "ja")
TIERS = ("easy", "standard", "hard")


def patch_wide_head():
    """laya 의 build_model 을 head_size 지원 버전으로 교체 (wide head 스냅샷용)."""
    import laya.agent as LA
    import laya.common as LC
    from model_xeron import build_wide_model

    orig = LC.build_model

    def _patched(cfg, encoder_dir=None, **kwargs):
        hs = int(cfg.get("head_size") or 0)
        if hs:
            return build_wide_model(cfg, encoder_dir, head_layers=cfg.get("head_layers", 2),
                                    head_size=hs, dropout=cfg.get("dropout", 0.1) or 0.1)
        return orig(cfg, encoder_dir, **kwargs)

    LC.build_model = _patched
    LA.build_model = _patched
    LA._verify_compatibility = lambda *a, **k: None
    print("[xi-v] patched laya for wide heads", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("label")
    ap.add_argument("out_prefix")
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--tiers", default=",".join(TIERS))
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="셀당 최대 문항 수(디버그)")
    ap.add_argument("--harness", default="/tmp/jevbench")
    args = ap.parse_args()

    if args.wide:
        patch_wide_head()

    sys.path.insert(0, args.harness)
    from jevbench.adapters import LayaLocalAdapter
    from jevbench.budget import Ledger
    from jevbench.runner import Runner
    from jevbench.tasks import Task

    langs = args.langs.split(",")
    tiers = args.tiers.split(",")
    tasks = []
    for lang in langs:
        for tier in tiers:
            p = os.path.join(HERE, "datasets", lang, f"{tier}.jsonl")
            if not os.path.exists(p):
                print(f"[xi-v] skip (없음): {lang}/{tier}")
                continue
            n = 0
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tasks.append(Task.from_dict(json.loads(line)))
                    n += 1
                    if args.limit and n >= args.limit:
                        break
            print(f"[xi-v] {lang}/{tier}: {n} 문항", flush=True)
    if not tasks:
        sys.exit("문항이 없습니다 — datasets/<lang>/<tier>.jsonl 를 먼저 채우세요.")
    print(f"[xi-v] 총 {len(tasks)} 문항", flush=True)

    # preflight: 하네스 규약(질문 빌드)을 먼저 통과시켜 스키마 오류로 러너가 중단되는 일을 막는다
    from jevbench.adapters.base import build_question
    bad = []
    for t in tasks:
        try:
            build_question(t)
        except Exception as e:  # noqa: BLE001
            bad.append((t.id, f"{type(e).__name__}: {str(e)[:200]}"))
    if bad:
        print(f"[xi-v] PREFLIGHT FAIL {len(bad)}건 — 실행 중단")
        for tid, err in bad[:12]:
            print("  -", tid, err)
        sys.exit(1)
    print(f"[xi-v] preflight OK ({len(tasks)} 문항 규약 통과)", flush=True)

    ad = LayaLocalAdapter(endpoint=args.model, model=args.label, threads=args.threads)
    t0 = time.perf_counter()
    ad.load()
    print(f"[xi-v] model loaded in {time.perf_counter()-t0:.1f}s", flush=True)
    for t in tasks[:2]:
        ad.run(t)
    runner = Runner(ad, Ledger(f"{args.out_prefix}.ledger.jsonl"), f"{args.out_prefix}.raw")
    t0 = time.perf_counter()
    recs = runner.run_all(tasks, progress_every=25, results_path=f"{args.out_prefix}.results.jsonl")
    ok = sum(1 for r in recs if r["ok"])
    print(f"[xi-v] done {ok}/{len(recs)} ok in {time.perf_counter()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
