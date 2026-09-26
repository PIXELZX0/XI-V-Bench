#!/usr/bin/env python3
"""XI-V Bench 1.0 — zh 현지 각색 빌더 (easy / standard).

규칙: builders/LOCALIZATION.md
  - 문항 수·순서 = en 원문과 1:1
  - group = en 값 그대로 복사
  - labels = 같은 개수·같은 순서, expected = 같은 인덱스(의미 동일)
  - state / question.instructions / question.criteria / labels / label_basis = 중국어(간체) 현지 각색
  - provenance: xi_lang="zh", source_kind="localized", translation_of=<en id>, source + " (XI-V localized)"
"""
import datetime as _dt
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# ---------------------------------------------------------------- 공통 라벨 세트
L_ORDER = ["查询物流", "取消订单", "修改地址", "报告破损", "账单问题"]
C_ORDER = {
    "查询物流": "想了解订单的物流状态或送达时间",
    "取消订单": "想要取消一笔订单",
    "修改地址": "想要更改收货地址",
    "报告破损": "收到的商品已损坏",
    "账单问题": "询问扣款、发票或付款问题",
}

L_ASSIST = ["设置闹钟", "播放音乐", "查询天气", "发送消息", "关灯"]
C_ASSIST = {
    "设置闹钟": "设置闹钟或起床时间",
    "播放音乐": "播放歌曲、专辑、歌手或歌单",
    "查询天气": "询问天气或天气预报",
    "发送消息": "给某人发送消息",
    "关灯": "关闭灯光",
}

L_YN = ["否", "是"]
C_FACT = {"否": "文中说明并非如此", "是": "文中确实如此"}
C_POLICY = {"否": "缺少某个必要条件，或存在禁止性规定。", "是": "所有必要条件均已成立，且不存在禁止性规定。"}

L_PAY = ["信用卡", "支付宝", "银行转账", "现金"]
C_PAY = {
    "信用卡": "用信用卡支付或想要用信用卡支付",
    "支付宝": "使用支付宝支付",
    "银行转账": "银行转账或电汇",
    "现金": "现金",
}

L_PRI = ["低", "中", "高", "紧急"]
C_PRI = {"低": "低优先级", "中": "中优先级", "高": "高优先级", "紧急": "紧急或最高优先级"}

L_SIZE = ["S", "M", "L", "XL"]
C_SIZE = {"S": "小号", "M": "中号", "L": "大号", "XL": "加大号"}

L_INTENT2 = ["取消", "退款", "查询进度", "修改地址", "以上都不是"]
C_INTENT2 = {
    "取消": "终止已有的订阅",
    "退款": "退回已收取的款项",
    "查询进度": "了解配送进展",
    "修改地址": "更改收货地址",
    "以上都不是": "以上操作均未被要求",
}

L_LEVEL = ["0", "1", "2", "3"]
C_LEVEL = [
    "无功能受影响，仅为外观问题",
    "单个用户或非核心功能受影响，存在变通办法",
    "大量用户无法使用核心功能，但无数据丢失",
    "已确认不可逆的数据丢失或人身伤害",
]

INSTR_CHOICE_ORDER = "用户这句话表达的是哪一种意图？"
INSTR_FACT = "请仅依据文中陈述的事实作答。"
INSTR_EXTRACT = "顾客提到的是哪种付款方式？"

# ---------------------------------------------------------------- EASY (32)
EASY = [
    # --- intent (order) 00-05
    dict(state="我的包裹到哪儿了？我上周下的单，到现在还没送到。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="查询物流"),
    dict(state="请取消我的订单 #4471，我不需要了。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="取消订单"),
    dict(state="我搬家了，能把订单改寄到朝阳区建国路88号，而不是原来的地址吗？",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="修改地址"),
    dict(state="我收到的杯子到货时已经碎成一片了。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="报告破损"),
    dict(state="为什么同一个订单在我的信用卡账单上被扣了两次款？",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="账单问题"),
    dict(state="我的订单什么时候能送到？物流页面什么都查不到。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ORDER, labels=L_ORDER, expected="查询物流"),
    # --- intent (assistant) 06-11
    dict(state="明天早上6点半叫我起床。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="设置闹钟"),
    dict(state="放一首周杰伦的歌。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="播放音乐"),
    dict(state="北京明天会下雨吗？",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="查询天气"),
    dict(state="给张悦发条消息，说我会晚到十分钟。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="发送消息"),
    dict(state="把卧室的灯关掉。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="关灯"),
    dict(state="定一个早上7点的闹钟。",
         instructions=INSTR_CHOICE_ORDER, criteria=C_ASSIST, labels=L_ASSIST, expected="设置闹钟"),
    # --- fact 12-23
    dict(state="订单 #1182。状态：已于9月3日发货。承运方：顺丰。",
         instructions="该订单是否已发货？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="订单 #1183。状态：尚未发货，等待补货。",
         instructions="该订单是否已发货？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    dict(state="发票 2026-044。金额：120元。付款状态：已全额付清。",
         instructions="该发票是否已付款？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="发票 2026-045。金额：80元。付款状态：未付款，自8月1日起逾期。",
         instructions="该发票是否已付款？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    dict(state="住客档案：李娜。过敏原：花生。饮食：素食。",
         instructions="该住客是否对花生过敏？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="住客档案：王强。过敏原：无。饮食：无限制。",
         instructions="该住客是否对花生过敏？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    dict(state="会议室B：已被销售部预订，时段为14:00至15:00。",
         instructions="会议室B是否在14:00至15:00被预订？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="会议室C：整个下午都空闲，无任何预订。",
         instructions="会议室C今天下午是否被预订？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    dict(state="账户设置：双重验证处于已开启状态。",
         instructions="双重验证是否已开启？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="账户设置：双重验证处于已关闭状态。",
         instructions="双重验证是否已开启？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    dict(state="用户写道：“好的，请帮我订阅电子报。”",
         instructions="用户是否同意订阅电子报？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="是"),
    dict(state="用户写道：“不了，谢谢，我不需要电子报。”",
         instructions="用户是否同意订阅电子报？" + INSTR_FACT, criteria=C_FACT, labels=L_YN, expected="否"),
    # --- extraction (payment) 24-26
    dict(state="我昨天晚上用支付宝付的款。",
         instructions=INSTR_EXTRACT, criteria=C_PAY, labels=L_PAY, expected="支付宝"),
    dict(state="快递员上门时我付现金。",
         instructions=INSTR_EXTRACT, criteria=C_PAY, labels=L_PAY, expected="现金"),
    dict(state="我周一通过银行转账把钱汇过去了。",
         instructions=INSTR_EXTRACT, criteria=C_PAY, labels=L_PAY, expected="银行转账"),
    # --- extraction (priority) 27-29
    dict(state="工单 #88 - 优先级：高 - 二楼打印机卡纸。",
         instructions="该工单标注的是哪个优先级？", criteria=C_PRI, labels=L_PRI, expected="高"),
    dict(state="工单 #89 - 优先级：低 - 请更新我办公桌上的电话标签。",
         instructions="该工单标注的是哪个优先级？", criteria=C_PRI, labels=L_PRI, expected="低"),
    dict(state="工单 #90 - 优先级：紧急 - 生产数据库已宕机。",
         instructions="该工单标注的是哪个优先级？", criteria=C_PRI, labels=L_PRI, expected="紧急"),
    # --- extraction (size) 30-31
    dict(state="请问那件蓝色衬衫能给我拿一件M码的吗？",
         instructions="顾客要的是哪个尺码？", criteria=C_SIZE, labels=L_SIZE, expected="M"),
    dict(state="我要这件夹克，加大码（XL）。",
         instructions="顾客要的是哪个尺码？", criteria=C_SIZE, labels=L_SIZE, expected="XL"),
]

# ---------------------------------------------------------------- STANDARD (32)
INSTR_POLICY = "根据上述规定，所请求的操作是否被允许？未获证实的必要条件视为不满足。"
INSTR_INTENT2 = "请选择用户主要请求的操作。仅仅提及而没有请求不构成意图。"
INSTR_LEVEL = "仅依据已报告的事实评定事件影响等级。应采用有充分依据的最高等级。"

STANDARD = [
    # --- policy 00-11 (noul)
    dict(state="规定：退款需要购物凭证，且购买时间在30天以内。一位顾客于12天前购买，但没有购物凭证。为其办理退款。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="必须同时具备购物凭证且购买不超过30天。该顾客于12天前购买，但无法提供任何购买凭证。可以为他退款吗？",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="规定：试用用户可以导出CSV；导出PDF需要付费套餐。一位试用用户要求导出CSV。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    dict(state="一个试用账户申请导出CSV。规则允许试用用户导出CSV，但PDF仅限付费账户使用。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    dict(state="规定：访客需要有人陪同，除非是已登记的承包商。一位已登记的承包商独自前来。准其入内。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    dict(state="陪同规则对已登记的承包商豁免。这位访客是已登记的承包商，且无人陪同。可以让他进入吗？",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    dict(state="规定：只有当款项已逾期且没有未结争议时，才发送催款提醒。款项已逾期；但有一笔争议尚未结案。发送提醒。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="一张逾期发票上存在未结的争议。发送催款提醒需要同时满足“已逾期”且“无争议”。可以发送提醒吗？",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="规定：员工可以访问本团队的文件。临时停职会覆盖一切访问权限。该员工所属的正是本团队，但他处于停职状态。打开该文件。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="停职会阻断访问，即便是本人团队的文件也一样。一名被停职的员工申请打开本团队的文件。可以打开吗？",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="否"),
    dict(state="规定：在出发前24小时（含整24小时）之前可以免费取消。距离出发还有24小时。免费取消。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    dict(state="距离出发正好还有24小时。免费取消在24小时这一截止点（含）之前均被允许。",
         instructions=INSTR_POLICY, criteria=C_POLICY, labels=L_YN, expected="是"),
    # --- intent 12-23 (choice)
    dict(state="不要取消我的会员。请把重复扣的那笔钱退给我。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="退款"),
    dict(state="让我的订阅保持有效；我只想让第二笔扣款退款。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="退款"),
    dict(state="包裹在哪里？收货地址保持原样就好。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="查询进度"),
    dict(state="请告诉我包裹的进展。不需要修改地址。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="查询进度"),
    dict(state="订单还没有发货。请把它改寄到我的新办公室。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="修改地址"),
    dict(state="请在发货之前把我的收货地址换成办公室地址。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="修改地址"),
    dict(state="这个月之后就别再给我续订了；我不是要退钱。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="取消"),
    dict(state="在下一次续费时终止会员。不要求退款。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="取消"),
    dict(state="你们的退款政策现在讲得清楚多了，谢谢解释。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="以上都不是"),
    dict(state="谢谢，我现在明白退款政策了。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="以上都不是"),
    dict(state="我昨天已经把订单取消了。包裹送到了吗？",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="查询进度"),
    dict(state="取消的事已经办完了。我的问题是货送到了没有。",
         instructions=INSTR_INTENT2, criteria=C_INTENT2, labels=L_INTENT2, expected="查询进度"),
    # --- ordinal 24-31 (score)
    dict(state="图标错位，所有功能都正常。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=0),
    dict(state="所有功能都正常运转，只是有一个图标看起来不太对。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=0),
    dict(state="有一名用户无法下载附件，但可以在浏览器里打开它。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=1),
    dict(state="单个用户下载失败；在线查看附件仍然可用。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=1),
    dict(state="所有客户都无法登录。没有任何记录丢失。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=2),
    dict(state="每一位客户都无法登录，但存储的数据完好无损。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=2),
    dict(state="备份和原始客户记录已被不可逆地删除。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=3),
    dict(state="客户记录已经永久丢失，且没有任何可用的备份。",
         instructions=INSTR_LEVEL, criteria=C_LEVEL, labels=L_LEVEL, expected=3),
]


def build(tier, overrides):
    src = os.path.join(HERE, "datasets", "en", f"{tier}.jsonl")
    out = os.path.join(HERE, "datasets", "zh", f"{tier}.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = [json.loads(l) for l in open(src, encoding="utf-8") if l.strip()]
    assert len(rows) == len(overrides), f"{tier}: {len(rows)} vs {len(overrides)}"

    lines = []
    for i, (en, ov) in enumerate(zip(rows, overrides)):
        # --- 무결성 검사 (labels 개수/순서, expected 인덱스)
        is_score = en["question"]["type"] == "score"
        ek = str(en["expected"]) if is_score else en["expected"]
        zk = str(ov["expected"]) if is_score else ov["expected"]
        assert len(ov["labels"]) == len(en["labels"]), f"{tier}[{i}]: label 개수 불일치"
        assert ek in en["labels"], f"{tier}[{i}]: en expected 결손"
        assert zk in ov["labels"], f"{tier}[{i}]: zh expected 결손"
        ei = en["labels"].index(ek)
        zi = ov["labels"].index(zk)
        assert ei == zi, f"{tier}[{i}]: expected 인덱스 불일치 {ei} != {zi}"
        assert is_score == isinstance(ov["expected"], int), f"{tier}[{i}]: type 불일치"
        if is_score:
            assert ov["expected"] == en["expected"]
            assert ov["criteria"] == C_LEVEL
            assert ov["labels"] == L_LEVEL

        item = {
            "id": f"zh-{tier}-{i:04d}",
            "family": en["family"],
            "group": en["group"],
            "state": ov["state"],
            "question": {
                "criteria": ov["criteria"],
                "instructions": ov["instructions"],
                "type": en["question"]["type"],
            },
            "labels": ov["labels"],
            "expected": ov["expected"],
            "split": "public",
            "provenance": {
                "exclude_reason": None,
                "label_basis": ("答案在文中被明确指出或直接陈述；撰写与复核均在推理前完成"
                                if tier == "easy" else "评判标准明确；复核在推理前完成"),
                "license": "MIT",
                "source": f"{en['provenance']['source']} (XI-V localized)",
                "xi_lang": "zh",
                "xi_tier": tier,
                "source_kind": "localized",
                "source_item_id": en["provenance"].get("source_item_id"),
                "origin_tier": en["provenance"].get("origin_tier"),
                "translation_of": en["id"],
                "reviewed": False,
                "frozen_utc": FROZEN,
            },
            "difficulty_notes": en.get("difficulty_notes"),
        }
        lines.append(json.dumps(item, ensure_ascii=False))

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[zh] {tier}: {len(lines)} 문항 → {out}")


if __name__ == "__main__":
    build("easy", EASY)
    build("standard", STANDARD)
