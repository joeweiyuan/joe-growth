#!/usr/bin/env python3
"""
gpa_convert.py — 跨体系 GPA / 成绩换算引擎

支持体系：AP（学校加权制）· IB（1-7）· A-Level（A*-E）· 普高/美高百分制
输出：百分制等价分、4.0 制（分级/线性双口径）、课程强度指数、达成率

⚠️ 诚实边界：跨体系换算没有全球统一官方表，不同机构口径不同。
   本引擎给出**可解释的映射**，并强制输出口径说明；对外使用必须标注"换算值，非校方原始口径"。
"""
import argparse
import json

# ---------------------------------------------------------------- 映射表
# IB：1-7 → 百分制等价（行业常用口径，非 IBO 官方）
IB_TO_PCT = {7: 97, 6: 88, 5: 78, 4: 68, 3: 58, 2: 48, 1: 38}

# A-Level：等级 → 百分制等价（UCAS Tariff 风格的近似）
ALEVEL_TO_PCT = {"A*": 95, "A": 88, "B": 78, "C": 68, "D": 58, "E": 48, "U": 30}

# AP 考试分（1-5）→ 百分制等价（仅用于"学习成果"表达，非 GPA）
AP_EXAM_TO_PCT = {5: 95, 4: 85, 3: 75, 2: 60, 1: 40}


def ib_to_pct(score):
    s = int(round(float(score)))
    if s not in IB_TO_PCT:
        raise ValueError(f"IB 分数应为 1-7，收到 {score}")
    return IB_TO_PCT[s]


def alevel_to_pct(grade):
    g = str(grade).strip().upper().replace("A *", "A*")
    if g not in ALEVEL_TO_PCT:
        raise ValueError(f"A-Level 等级应为 A*/A/B/C/D/E/U，收到 {grade}")
    return ALEVEL_TO_PCT[g]


def ap_exam_to_pct(score):
    s = int(round(float(score)))
    if s not in AP_EXAM_TO_PCT:
        raise ValueError(f"AP 分数应为 1-5，收到 {score}")
    return AP_EXAM_TO_PCT[s]


def pct_to_gpa4(pct, mode="banded"):
    """百分制 → 4.0 制

    banded（常见美高/认证机构口径）：90-100=4.0, 80-89=3.0, 70-79=2.0, 60-69=1.0
    linear（线性）：pct/100*4
    """
    p = max(0.0, min(100.0, float(pct)))
    if mode == "linear":
        return round(p / 100 * 4, 2)
    if p >= 90:
        return 4.0
    if p >= 80:
        return 3.0
    if p >= 70:
        return 2.0
    if p >= 60:
        return 1.0
    return 0.0


def normalize_weighted_school_gpa(gpa, max_gpa):
    """学校加权制（如 AP 满绩 5 / Pre-AP 4.5 / 非 AP 4）→ 百分制等价

    Joe 实例：3.73 / 4.40 = 84.8%
    """
    if max_gpa <= 0:
        raise ValueError("满绩必须 > 0")
    if gpa > max_gpa + 1e-9:
        raise ValueError(f"GPA {gpa} 超过满绩 {max_gpa}，请检查数据")
    return round(float(gpa) / float(max_gpa) * 100, 2)


def rigor_index(courses):
    """课程强度指数（0-100）：高校实际看的是"修了什么难度的课"

    courses: [{"level": "AP"|"IB_HL"|"IB_SL"|"A2"|"AS"|"Honors"|"Regular", "count": n}]
    权重（经验值）：AP/IB_HL/A2 = 1.0；IB_SL/AS = 0.7；Honors = 0.5；Regular = 0.3
    """
    w = {"AP": 1.0, "IB_HL": 1.0, "A2": 1.0, "IB_SL": 0.7, "AS": 0.7, "HONORS": 0.5, "REGULAR": 0.3}
    total = 0.0
    for c in courses:
        lvl = str(c.get("level", "")).upper().replace(" ", "_")
        if lvl not in w:
            raise ValueError(f"未知课程层级: {c.get('level')}")
        total += w[lvl] * float(c.get("count", 1))
    # 8 门全 AP = 100 分基准
    return round(min(100.0, total / 8 * 100), 1)


def weighted_gpa(courses):
    """按学分加权汇总

    courses: [{"name":..., "pct": 88.5, "credit": 1.0, "level": "AP"}]
    返回：pct_avg / gpa_banded / gpa_linear / credits / rigor
    """
    if not courses:
        raise ValueError("课程列表为空")
    tot_cr = sum(float(c.get("credit", 1)) for c in courses)
    if tot_cr <= 0:
        raise ValueError("总学分必须 > 0")
    pct_avg = sum(float(c["pct"]) * float(c.get("credit", 1)) for c in courses) / tot_cr
    gpa_band = sum(pct_to_gpa4(c["pct"], "banded") * float(c.get("credit", 1)) for c in courses) / tot_cr
    gpa_lin = sum(pct_to_gpa4(c["pct"], "linear") * float(c.get("credit", 1)) for c in courses) / tot_cr
    lv = {}
    for c in courses:
        lvl = c.get("level", "Regular")
        lv[lvl] = lv.get(lvl, 0) + 1
    return {
        "pct_avg": round(pct_avg, 2),
        "gpa_banded": round(gpa_band, 2),
        "gpa_linear": round(gpa_lin, 2),
        "credits": round(tot_cr, 2),
        "rigor_index": rigor_index([{"level": k, "count": v} for k, v in lv.items()]),
    }


def convert(system, value, max_value=None):
    """单值换算 → 百分制"""
    s = system.lower()
    if s == "ib":
        pct, note = ib_to_pct(value), "IB 1-7 → 百分制（行业常用映射，非 IBO 官方）"
    elif s in ("alevel", "a-level", "a_level"):
        pct, note = alevel_to_pct(value), "A-Level 等级 → 百分制（近似 UCAS Tariff）"
    elif s == "ap":
        pct, note = ap_exam_to_pct(value), "AP 考试分 → 百分制（成果表达用，非 GPA 换算）"
    elif s in ("pct", "percentage", "school"):
        pct, note = float(value), "已是百分制"
    elif s in ("weighted", "school_gpa"):
        if max_value is None:
            raise ValueError("weighted 模式需提供 --max 满绩")
        pct, note = normalize_weighted_school_gpa(float(value), float(max_value)), "学校加权 GPA ÷ 满绩 → 百分制"
    else:
        raise ValueError(f"未知体系: {system}")
    return {"input": {"system": system, "value": value, "max": max_value},
            "pct": round(float(pct), 2),
            "gpa4_banded": pct_to_gpa4(pct, "banded"),
            "gpa4_linear": pct_to_gpa4(pct, "linear"),
            "note": note}


# ---------------------------------------------------------------- Joe 实测数据
JOE_COURSES = [
    # 课程, 学校官方 4.x 绩点, 满绩, 学分
    ("AP 微积分 AB", 3.00, 5.0, 1.0),
    ("AP 微观经济", 4.25, 5.0, 1.0),
    ("世界史", 3.08, 4.0, 1.0),
    ("Pre-AP 英语 1", 4.05, 4.5, 1.0),
    ("Pre-AP 生物", 4.17, 4.5, 1.0),
    ("心理学", 3.78, 4.0, 1.0),
    ("西班牙语", 3.16, 4.0, 1.0),
    ("Pre-AP 化学", 4.17, 4.5, 1.0),
    ("艺术", 4.00, 4.0, 0.5),
    ("体育", 4.00, 4.0, 0.25),
]


def joe_case():
    rows = []
    for name, g, mx, cr in JOE_COURSES:
        rows.append({"name": name, "pct": normalize_weighted_school_gpa(g, mx), "credit": cr,
                     "level": "AP" if name.startswith("AP") else ("Honors" if "Pre-AP" in name else "Regular")})
    agg = weighted_gpa(rows)
    cur = sum(g * cr for _, g, _, cr in JOE_COURSES)
    cr_tot = sum(cr for *_, cr in JOE_COURSES)
    return {
        "official": {"sum_gpa_x_credit": round(cur, 3), "credits": cr_tot,
                     "official_gpa": round(cur / cr_tot, 2), "max_gpa": 4.40,
                     "achievement_pct": round(cur / cr_tot / 4.40 * 100, 1)},
        "normalized": agg,
        "per_course": [{"name": r["name"], "pct": r["pct"], "credit": r["credit"]} for r in rows],
    }


def main():
    ap = argparse.ArgumentParser(description="跨体系 GPA 换算")
    ap.add_argument("--system", help="ib | alevel | ap | pct | weighted")
    ap.add_argument("--value")
    ap.add_argument("--max", dest="max_value", type=float, help="weighted 模式的满绩")
    ap.add_argument("--joe", action="store_true", help="用 Joe 的真实成绩跑一遍校验")
    a = ap.parse_args()

    if a.joe:
        print(json.dumps(joe_case(), ensure_ascii=False, indent=2))
        return 0
    if not a.system or a.value is None:
        ap.error("需要 --system 与 --value，或用 --joe")
    print(json.dumps(convert(a.system, a.value, a.max_value), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
