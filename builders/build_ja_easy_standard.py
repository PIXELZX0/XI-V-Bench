#!/usr/bin/env python3
"""XI-V Bench 1.0 — 日本語(ja) 현지 각색: easy + standard (각 32문항, 총 64).

입력: datasets/en/{easy,standard}.jsonl
출력: datasets/ja/{easy,standard}.jsonl
규칙: builders/LOCALIZATION.md
  - 순서·문항 수 1:1, group 원문 그대로
  - state/instructions/criteria/labels/provenance.label_basis = 일본어 현지 각색
  - 하네스 호환: noul = labels ["no","yes"] + criteria 키 {"false","true"} (jevbench 고정 규약)
              score = labels ["0"..."3"] + expected 정수 (서수 인덱스)
  - provenance: xi_lang=ja, source_kind=localized, translation_of=<en id>, reviewed=false
"""
import json
import os
import pathlib
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent.parent
EN = HERE / "datasets" / "en"
JA = HERE / "datasets" / "ja"

# 하네스 고정 토큰: LayaLocalAdapter 가 noul 에 대해 probs {"yes","no"} 를 반환하고
# score_task 가 task.labels 와 키 집합을 정확히 대조한다. 라벨을 현지어로 바꾸면
# 그 셀의 모든 noul 문항이 invalid/오답이 된다 → 라벨은 반드시 ["no","yes"] 유지.
# はい/いいえ 는 criteria 값 안에서 일본어로 명시해 문항은 일본어로 완결시킨다.
BINARY_LABELS = ["no", "yes"]
BINARY_CRITERIA = {
    "false": "本文ではそうではないと述べられている（いいえ）",
    "true": "本文ではそうであると述べられている（はい）",
}
BINARY_CRITERIA_POLICY = {
    "false": "条件が欠けている、または禁止規定が適用される（いいえ）",
    "true": "必要な条件がすべて満たされ、禁止規定は適用されない（はい）",
}
BINARY_INSTR_FACT = "本文に示された事実のみに基づいて答えてください。"
BINARY_INSTR_POLICY = ("記載された規定の下で、求められている行為は許可されますか。"
                       "証明されていない必要条件は満たされていないものとして扱ってください。")
SCORE_LABELS = ["0", "1", "2", "3"]
SCORE_CRITERIA = [
    "機能は損なわれていない。見た目だけの問題",
    "利用者1名、または重要でない機能が損なわれたが、回避手段がある",
    "多数の利用者が中核機能を利用できず、データ損失はない",
    "回復不能なデータ損失、または身体的な危害が確認された",
]
SCORE_INSTR = ("報告された事実のみに基づいてインシデントの影響度を評定してください。"
               "完全に裏付けられる最も高いレベルを用いてください。")

LB_EASY = "正解は本文に明示されている。推論前に作成・レビュー済み"
LB_STD = "明示的な評価基準。推論前にレビュー済み"

# ---------------------------------------------------------------- easy (32)
INTENT_A_LABELS = ["注文の追跡", "注文のキャンセル", "配送先の変更", "破損の報告", "請求に関する問い合わせ"]
INTENT_A_CRIT = {
    "注文の追跡": "注文が今どこにあるか、いつ届くかを知りたい",
    "注文のキャンセル": "注文をキャンセルしたい",
    "配送先の変更": "配送先住所を変更したい",
    "破損の報告": "壊れた品・破損した品が届いた",
    "請求に関する問い合わせ": "請求・請求書・支払いについて尋ねている",
}
INTENT_B_LABELS = ["アラーム設定", "音楽再生", "天気", "メッセージ送信", "照明を消す"]
INTENT_B_CRIT = {
    "アラーム設定": "アラームや起床時刻を設定する",
    "音楽再生": "曲・アルバム・アーティスト・プレイリストを再生する",
    "天気": "天気や予報を尋ねる",
    "メッセージ送信": "誰かにメッセージを送る",
    "照明を消す": "照明を消す",
}
PAY_LABELS = ["クレジットカード", "PayPal", "銀行振込", "現金"]
PAY_CRIT = {
    "クレジットカード": "クレジットカードで支払った、または支払いたい",
    "PayPal": "PayPal",
    "銀行振込": "銀行振込・口座振替",
    "現金": "現金",
}
PRIO_LABELS = ["低", "中", "高", "緊急"]
PRIO_CRIT = {"低": "優先度：低", "中": "優先度：中", "高": "優先度：高", "緊急": "優先度：緊急・重大"}
SIZE_LABELS = ["S", "M", "L", "XL"]
SIZE_CRIT = {"S": "Sサイズ（小）", "M": "Mサイズ（中）", "L": "Lサイズ（大）", "XL": "XLサイズ（特大）"}

EASY = [
    # --- intent A ---
    dict(state="荷物はどこにありますか。先週注文したのに、まだ届いていません。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="注文の追跡"),
    dict(state="注文番号4471をキャンセルしてください。もう必要ありません。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="注文のキャンセル"),
    dict(state="引っ越しました。旧住所ではなく、東京都渋谷区神南1-2-3 に配送してもらえますか。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="配送先の変更"),
    dict(state="届いたマグカップが粉々に割れていました。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="破損の報告"),
    dict(state="1件の注文なのに、クレジットカードの明細で二重に引き落とされているのはなぜですか。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="請求に関する問い合わせ"),
    dict(state="注文はいつ届きますか。追跡ページには何も表示されません。",
         labels=INTENT_A_LABELS, crit=INTENT_A_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="注文の追跡"),
    # --- intent B ---
    dict(state="明日の朝6時30分に起こしてください。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="アラーム設定"),
    dict(state="米津玄師をかけて。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="音楽再生"),
    dict(state="明日の東京は雨が降りますか。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="天気"),
    dict(state="田中さんに10分遅れるとメッセージを送って。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="メッセージ送信"),
    dict(state="寝室の電気を消して。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="照明を消す"),
    dict(state="朝7時にアラームを設定して。",
         labels=INTENT_B_LABELS, crit=INTENT_B_CRIT, instructions="このメッセージが表す意図はどれですか。",
         expected="アラーム設定"),
    # --- fact (noul) ---
    dict(state="注文番号1182。ステータス：9月3日に発送済み。配送業者：ヤマト運輸。",
         instructions="注文は発送済みですか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="注文番号1183。ステータス：未発送、入荷待ち。",
         instructions="注文は発送済みですか。" + BINARY_INSTR_FACT, expected="no"),
    dict(state="請求書 2026-044。金額：12,000円。支払状況：全額支払済み。",
         instructions="請求書は支払済みですか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="請求書 2026-045。金額：8,000円。支払状況：未払い、8月1日から延滞。",
         instructions="請求書は支払済みですか。" + BINARY_INSTR_FACT, expected="no"),
    dict(state="宿泊客プロフィール：佐藤 真理。アレルギー：落花生。食事制限：ベジタリアン。",
         instructions="宿泊客は落花生にアレルギーがありますか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="宿泊客プロフィール：鈴木 健太。アレルギー：なし。食事制限：なし。",
         instructions="宿泊客は落花生にアレルギーがありますか。" + BINARY_INSTR_FACT, expected="no"),
    dict(state="会議室B：営業部が14時から15時まで予約済み。",
         instructions="会議室Bは14時から15時まで予約されていますか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="会議室C：午後はずっと空き、予約なし。",
         instructions="会議室Cは今日の午後、予約されていますか。" + BINARY_INSTR_FACT, expected="no"),
    dict(state="アカウント設定：二要素認証が有効になっています。",
         instructions="二要素認証は有効ですか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="アカウント設定：二要素認証が無効になっています。",
         instructions="二要素認証は有効ですか。" + BINARY_INSTR_FACT, expected="no"),
    dict(state="利用者の記述：「はい、メールマガジンに登録してください。」",
         instructions="利用者はメールマガジンの購読に同意しましたか。" + BINARY_INSTR_FACT, expected="yes"),
    dict(state="利用者の記述：「いいえ、結構です。メールマガジンは不要です。」",
         instructions="利用者はメールマガジンの購読に同意しましたか。" + BINARY_INSTR_FACT, expected="no"),
    # --- extraction ---
    dict(state="昨夜 PayPal で支払いました。",
         labels=PAY_LABELS, crit=PAY_CRIT, instructions="顧客が挙げている支払方法はどれですか。",
         expected="PayPal"),
    dict(state="配達員が来たら現金で支払います。",
         labels=PAY_LABELS, crit=PAY_CRIT, instructions="顧客が挙げている支払方法はどれですか。",
         expected="現金"),
    dict(state="月曜日に銀行振込で送金しました。",
         labels=PAY_LABELS, crit=PAY_CRIT, instructions="顧客が挙げている支払方法はどれですか。",
         expected="銀行振込"),
    dict(state="チケット #88 - 優先度：高 - 2階のプリンターが紙詰まりを起こしています。",
         labels=PRIO_LABELS, crit=PRIO_CRIT, instructions="チケットに記載された優先度はどれですか。",
         expected="高"),
    dict(state="チケット #89 - 優先度：低 - 内線電話のラベルを更新してください。",
         labels=PRIO_LABELS, crit=PRIO_CRIT, instructions="チケットに記載された優先度はどれですか。",
         expected="低"),
    dict(state="チケット #90 - 優先度：緊急 - 本番データベースが停止しています。",
         labels=PRIO_LABELS, crit=PRIO_CRIT, instructions="チケットに記載された優先度はどれですか。",
         expected="緊急"),
    dict(state="青いシャツのMサイズをいただけますか。",
         labels=SIZE_LABELS, crit=SIZE_CRIT, instructions="顧客が求めているサイズはどれですか。",
         expected="M"),
    dict(state="ジャケットはXLサイズ（特大）が必要です。",
         labels=SIZE_LABELS, crit=SIZE_CRIT, instructions="顧客が求めているサイズはどれですか。",
         expected="XL"),
]

# ------------------------------------------------------------ standard (32)
INTENT_S_LABELS = ["解約", "返金", "配送状況の確認", "配送先の変更", "該当なし"]
INTENT_S_CRIT = {
    "解約": "現在のサブスクリプションを終了させる",
    "返金": "すでに請求された金額を返してもらう",
    "配送状況の確認": "配送の進み具合を知りたい",
    "配送先の変更": "配送先住所を変更する",
    "該当なし": "これらのいずれの行為も求められていない",
}
INTENT_S_INSTR = "主として求められている行為を1つ選んでください。要望を伴わない言及だけでは意図とは見なしません。"

STANDARD = [
    # --- policy (noul) ---
    dict(state="規定：返金にはレシートと、購入から30日以内であることが必要です。"
               "ある顧客は12日前に購入しましたが、レシートがありません。返金を実行する。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="レシートと、購入から30日以内という2つの条件が必要です。"
               "購入は12日前ですが、購入を証明するものがありません。返金できますか。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="規定：トライアル利用者はCSVを出力できますが、PDFには有料プランが必要です。"
               "トライアル利用者がCSVを求めています。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    dict(state="トライアルアカウントがCSV出力を求めています。"
               "規約上トライアルでもCSVは可能ですが、PDFは有料アカウントに限られます。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    dict(state="規定：来訪者は、登録済みの協力会社員でない限り付き添いが必要です。"
               "登録済みの協力会社員が1人で来ました。入館させる。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    dict(state="付き添いの規則には、登録済みの協力会社員は適用除外です。"
               "この来訪者は、付き添いのいない登録済みの協力会社員です。入館できますか。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    dict(state="規定：督促状は、支払いが延滞しており、かつ係争中でない場合にのみ送付します。"
               "支払いは延滞していますが、係争中です。督促状を送る。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="延滞している請求書について係争中です。"
               "督促には、延滞であることと、係争がないことの両方が必要です。督促は許可されますか。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="規定：職員は自分の所属チームのファイルにアクセスできます。"
               "一時的な停職処分は、すべてのアクセスに優先します。"
               "その職員はチームの責任者ですが停職中です。ファイルを開く。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="停職処分は、自分のチームのファイルへのアクセスも遮断します。"
               "停職中の職員が、自分の所属チームのファイルを求めています。開けますか。",
         instructions=BINARY_INSTR_POLICY, expected="no", crit=BINARY_CRITERIA_POLICY),
    dict(state="規定：予約は出発の24時間前まで（ちょうど24時間前を含む）無料でキャンセルできます。"
               "出発までちょうど24時間です。無料でキャンセルする。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    dict(state="出発までちょうど24時間あります。"
               "無料キャンセルは、その24時間の期限まで、あるいはそれ以前なら可能です。",
         instructions=BINARY_INSTR_POLICY, expected="yes", crit=BINARY_CRITERIA_POLICY),
    # --- intent ---
    dict(state="会員を解約しないでください。二重に請求された分を返金してください。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="返金"),
    dict(state="サブスクリプションは有効なままにしてください。2回目の請求分だけ返金してほしいです。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="返金"),
    dict(state="荷物はどこにありますか。配送先住所はそのままでお願いします。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送状況の確認"),
    dict(state="荷物の配送状況を教えてください。住所の変更は不要です。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送状況の確認"),
    dict(state="注文はまだ発送されていません。新しい勤務先に送ってください。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送先の変更"),
    dict(state="発送前に、配送先住所を勤務先の住所に変更してください。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送先の変更"),
    dict(state="今月以降、サブスクリプションの更新を止めてください。返金は求めていません。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="解約"),
    dict(state="次回の更新で会員を終了してください。返金はいりません。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="解約"),
    dict(state="返金規定がよく分かりました。説明してくれてありがとうございます。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="該当なし"),
    dict(state="ありがとうございます。返金の規定が分かりました。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="該当なし"),
    dict(state="昨日キャンセルしました。荷物はもう届きましたか。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送状況の確認"),
    dict(state="キャンセルは済んでいます。私の質問は、荷物が届いたかどうかです。",
         labels=INTENT_S_LABELS, crit=INTENT_S_CRIT, instructions=INTENT_S_INSTR, expected="配送状況の確認"),
    # --- ordinal (score) ---
    dict(state="アイコンの位置がずれています。すべての機能は正常に動作します。", expected=0),
    dict(state="すべての機能は正常に動作します。アイコンの見た目だけがおかしいです。", expected=0),
    dict(state="利用者1名が添付ファイルをダウンロードできませんが、ブラウザーでは開けます。", expected=1),
    dict(state="利用者1名だけがダウンロードに失敗しますが、添付ファイルをオンラインで閲覧することは可能です。", expected=1),
    dict(state="すべての顧客がサインインできません。記録の損失はありません。", expected=2),
    dict(state="すべての顧客がログインできませんが、保存されたデータは無傷のままです。", expected=2),
    dict(state="バックアップと顧客の原本記録が、回復不能な形で削除されました。", expected=3),
    dict(state="顧客記録は永久に失われ、残っているバックアップもありません。", expected=3),
]


def build(tier, ja_items):
    src = EN / f"{tier}.jsonl"
    with open(src, encoding="utf-8") as f:
        en_items = [json.loads(l) for l in f if l.strip()]
    assert len(en_items) == 32, f"{tier}: en 문항 수 {len(en_items)}"
    assert len(ja_items) == 32, f"{tier}: ja 문항 수 {len(ja_items)}"
    frozen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for idx, (en, ja) in enumerate(zip(en_items, ja_items)):
        qtype = en["question"]["type"]
        if qtype == "noul":
            labels = list(BINARY_LABELS)
            crit = ja.get("crit", BINARY_CRITERIA)
        elif qtype == "score":
            labels = list(SCORE_LABELS)
            crit = list(SCORE_CRITERIA)
        else:  # choice
            labels = list(ja["labels"])
            crit = dict(ja["crit"])
        instructions = ja.get("instructions", SCORE_INSTR if qtype == "score" else en["question"]["instructions"])
        # --- 검증용 단언 ---
        assert len(labels) == len(en["labels"]), f"{en['id']}: 라벨 개수 불일치"
        if qtype == "score":
            assert isinstance(ja["expected"], int), f"{en['id']}: score expected 는 정수여야 함"
            assert str(ja["expected"]) in labels, f"{en['id']}: expected 레벨이 labels 에 없음"
        else:
            assert ja["expected"] in labels, f"{en['id']}: expected 가 labels 에 없음"
        if qtype == "choice":
            assert set(crit.keys()) == set(labels), f"{en['id']}: criteria 키 ≠ labels"
        elif qtype == "noul":
            assert set(crit.keys()) == set(en["question"]["criteria"].keys()) == {"false", "true"}
        else:
            assert len(crit) == len(en["question"]["criteria"])
        prov = {
            "exclude_reason": None,
            "label_basis": LB_EASY if tier == "easy" else LB_STD,
            "license": en["provenance"]["license"],
            "source": en["provenance"]["source"] + " (XI-V localized)",
            "xi_lang": "ja",
            "xi_tier": tier,
            "source_kind": "localized",
            "source_item_id": en["provenance"].get("source_item_id"),
            "origin_tier": en["provenance"].get("origin_tier"),
            "translation_of": en["id"],
            "reviewed": False,
            "frozen_utc": frozen,
        }
        item = {
            "id": f"ja-{tier}-{idx:04d}",
            "family": en["family"],
            "group": en["group"],
            "state": ja["state"],
            "question": {"criteria": crit, "instructions": instructions, "type": qtype},
            "labels": labels,
            "expected": ja["expected"],
            "split": "public",
            "provenance": prov,
            "difficulty_notes": en.get("difficulty_notes"),
        }
        out.append(item)
    return out


def main():
    JA.mkdir(parents=True, exist_ok=True)
    for tier, items in (("easy", EASY), ("standard", STANDARD)):
        rows = build(tier, items)
        p = JA / f"{tier}.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[ja] wrote {p} ({len(rows)} items)")


if __name__ == "__main__":
    main()
