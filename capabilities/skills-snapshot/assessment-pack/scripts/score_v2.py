#!/usr/bin/env python3
"""
score_v2.py — 两层评估模型（门槛层 + 独立区分层）

核心逻辑（2026-11-21 家主定调）：
  任何体系的升学 = ① 先看 GPA → ② 再看标化 → ③ 最后看竞赛/科创/艺术/体育加分项
  加分项权重 = 目标大学的重视程度（可用 CDS C7 官方数据校准）

与 v1 的差别：
  v1 把五个维度混成一个总分（会掩盖门槛失败）
  v2 门槛层与区分层**分开**：
    - 门槛层：GPA / 标化 → 通过与否（加分项不能弥补门槛）
    - 区分层：4 个板块各自独立评分，再按目标校权重合成「区分分」
      （区分分仅用于同校横向比较，不与门槛混算）
"""
import argparse
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.join(os.path.dirname(HERE), "config")
TARGETS = os.path.join(CFG_DIR, "targets.json")

BLOCK_LABELS = {"competition": "竞赛", "research": "科创", "arts": "艺术", "sports": "体育"}
LEVEL = {"S": 100, "A": 80, "B": 60, "C": 40, "D": 20}


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def load_targets(path=TARGETS):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 门槛层
def pick_tier(cfg, admission_rate, tier=None):
    if tier:
        return tier, cfg["tiers"][tier]
    for name, t in sorted(cfg["tiers"].items(), key=lambda kv: kv[1]["admission_rate_max"]):
        if admission_rate is not None and admission_rate <= t["admission_rate_max"]:
            return name, t
    return "tier4_admit_lt100", cfg["tiers"]["tier4_admit_lt100"]


def gate_item(value, threshold, unit="", tolerance=0.0):
    if value is None:
        return {"value": None, "threshold": threshold, "status": "unknown", "gap": None,
                "note": "缺数据，无法判定"}
    gap = round(float(value) - float(threshold), 2)
    if gap >= 0:
        status = "pass"
    elif gap >= -abs(tolerance):
        status = "borderline"
    else:
        status = "fail"
    return {"value": round(float(value), 2), "threshold": threshold, "gap": gap,
            "status": status, "unit": unit}


def gate_layer(profile, tier_cfg):
    a = profile.get("academic", {}) or {}
    l = profile.get("language", {}) or {}
    pct = a.get("pct_avg")
    if pct is None and a.get("gpa") is not None and a.get("max_gpa"):
        pct = float(a["gpa"]) / float(a["max_gpa"]) * 100
    gpa_item = gate_item(pct, tier_cfg["gpa_pct_min"], "分", tolerance=3)
    lang_item = gate_item(l.get("toefl6"), tier_cfg["toefl6_min"], "/6", tolerance=0.5)
    sat_item = gate_item(l.get("sat"), tier_cfg["sat_min"], "", tolerance=60) if l.get("sat") else None

    items = [gpa_item, lang_item] + ([sat_item] if sat_item else [])
    known = [i for i in items if i["status"] != "unknown"]
    if any(i["status"] == "fail" for i in known):
        overall = "fail"
    elif any(i["status"] == "borderline" for i in known):
        overall = "borderline"
    elif known:
        overall = "pass"
    else:
        overall = "unknown"

    return {
        "gpa": gpa_item,
        "language": lang_item,
        "sat": sat_item,
        "overall": overall,
        "verdict": {
            "pass": "门槛达标：可以进入区分层竞争",
            "borderline": "门槛边缘：先把短板补到线上，再谈加分项",
            "fail": "门槛未达：加分项不能弥补（体育招募等特殊通道除外）",
            "unknown": "数据不足，无法判定门槛",
        }[overall],
    }


# ---------------------------------------------------------------- 区分层
def block_score(entries, cfg_mult=1.0):
    """单板块独立评分：最强项 × 时长系数 + 广度加分（封顶 8）"""
    if not entries:
        return 0.0, {"entries": 0, "top": None, "breadth_bonus": 0}
    scored = []
    for e in entries:
        base = LEVEL.get(str(e.get("level", "D")).upper(), 20)
        years = float(e.get("years", 1) or 1)
        factor = min(1.25, 0.85 + 0.10 * years)
        scored.append((base * factor, e, factor))
    scored.sort(key=lambda x: -x[0])
    top = scored[0][0]
    breadth = min(8, sum(2 for s, e, _ in scored[1:] if LEVEL.get(str(e.get("level", "D")).upper(), 20) >= 60))
    score = clamp((top + breadth) * cfg_mult)
    return score, {"entries": len(entries), "top": scored[0][1].get("name") or scored[0][1].get("domain"),
                   "top_level": scored[0][1].get("level"), "duration_factor": round(scored[0][2], 2),
                   "breadth_bonus": breadth}


def emphasis_for(cfg, school, country="us"):
    em = cfg.get("school_emphasis", {})
    if school and school in em:
        return dict(em[school]), f"school:{school}"
    if school:
        # 未收录的学校 → 给默认画像（明确标注）
        key = "_default_uk" if country == "uk" else "_default_research"
        return dict(em[key]), f"default:{key}（未收录该校，使用研究型大学默认画像）"
    return dict(em["_default_research"]), "default:_default_research"


def c7_adjust(conn, school, emphasis):
    """用 CDS C7 官方重视程度微调非学术板块"""
    if not conn or not school:
        return emphasis, None
    try:
        rows = conn.execute("SELECT factor, importance FROM cds_factors WHERE univ_slug=?", (school,)).fetchall()
    except sqlite3.Error:
        return emphasis, None
    if not rows:
        return emphasis, None
    imp = {r[0]: r[1] for r in rows}
    cfg = load_targets()
    mult_cfg = cfg["c7_multiplier"]
    # 竞赛/科创 ≈ Extracurricular + Talent；艺术/体育 ≈ Talent
    m_extra = mult_cfg.get(imp.get("extracurricular", "important"), 0.8)
    m_talent = mult_cfg.get(imp.get("talent", "important"), 0.8)
    adj = dict(emphasis)
    adj["competition"] = emphasis["competition"] * ((m_extra + m_talent) / 2)
    adj["research"] = emphasis["research"] * m_extra
    adj["arts"] = emphasis["arts"] * m_talent
    adj["sports"] = emphasis["sports"] * m_talent
    return adj, {"source": "CDS C7", "extracurricular": imp.get("extracurricular"),
                 "talent": imp.get("talent"),
                 "note": "C7 只给「非学术因素整体重视度」，板块内分配仍为经验配置"}


def distinction_layer(profile, emphasis, c7_note=None):
    blocks = {}
    detail = {}
    for key in ("competition", "research", "arts", "sports"):
        score, info = block_score(profile.get(key) or [])
        blocks[key] = round(score, 1)
        detail[key] = info

    weights = {k: max(0.0, float(emphasis.get(k, 0))) for k in blocks}
    tot = sum(weights.values()) or 1.0
    weights = {k: v / tot for k, v in weights.items()}
    composite = sum(blocks[k] * weights[k] for k in blocks)

    ranked = sorted(blocks.items(), key=lambda kv: -kv[1])
    return {
        "blocks": blocks,
        "weights": {k: round(v, 3) for k, v in weights.items()},
        "weighted_score": round(composite, 1),
        "strongest": BLOCK_LABELS[ranked[0][0]],
        "weakest": BLOCK_LABELS[ranked[-1][0]],
        "detail": detail,
        "c7": c7_note,
        "note": "板块分独立，不参与门槛判定；加权分仅用于同校横向比较",
    }


# ---------------------------------------------------------------- 输出
def render(result):
    g = result["gate"]
    print(f"\n{'='*56}")
    print(f"目标：{result['school'] or '（未指定）'} ｜ 分档：{result['tier']}")
    print(f"{'='*56}")
    print("【第一层 · 门槛】")
    for name in ("gpa", "language", "sat"):
        it = g.get(name)
        if not it:
            continue
        icon = {"pass": "✅", "borderline": "🟡", "fail": "🔴", "unknown": "⚪"}[it["status"]]
        label = {"gpa": "GPA（百分制）", "language": "标化（托福6分制）", "sat": "SAT"}[name]
        v = "-" if it["value"] is None else it["value"]
        print(f"  {icon} {label:18s} {v}  / 线 {it['threshold']}{it.get('unit','')}  差 {it['gap']}")
    print(f"  → {g['verdict']}")

    d = result["distinction"]
    print("\n【第二层 · 加分项（各自独立评分）】")
    for k, v in d["blocks"].items():
        bar = "█" * int(v / 5) + "░" * (20 - int(v / 5))
        print(f"  {BLOCK_LABELS[k]:4s} {v:5.1f}  {bar}  本校权重 {d['weights'][k]:.0%}")
    print(f"  → 加权区分分 {d['weighted_score']}（仅同校横向比较）")
    print(f"  → 最强：{d['strongest']} ｜ 最弱：{d['weakest']}")
    if d.get("c7"):
        print(f"  → C7 校准：课外 {d['c7']['extracurricular']} ｜ 天赋 {d['c7']['talent']}")
    print(f"\n⚠️ {result['disclaimer']}")


def main():
    ap = argparse.ArgumentParser(description="两层评估模型 v2")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--school", help="目标校 slug（如 mit）")
    ap.add_argument("--country", default="us", choices=["us", "uk", "ca", "au", "hk", "sg"])
    ap.add_argument("--tier", help="强制指定分档（如 tier2_admit_lt25）")
    ap.add_argument("--db", help="college.db（读 CDS 录取率与 C7）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cfg = load_targets()
    profile = json.load(open(a.profile, encoding="utf-8"))

    conn = sqlite3.connect(a.db) if (a.db and os.path.exists(a.db)) else None
    admission_rate = None
    if conn and a.school:
        try:
            row = conn.execute(
                "SELECT admission_rate FROM cds_records WHERE univ_slug=? ORDER BY cds_year DESC LIMIT 1",
                (a.school,)).fetchone()
            admission_rate = row[0] if row else None
        except sqlite3.Error:
            pass

    tier_name, tier_cfg = pick_tier(cfg, admission_rate, a.tier)
    gate = gate_layer(profile, tier_cfg)

    emphasis, src = emphasis_for(cfg, a.school, a.country)
    emphasis, c7_note = c7_adjust(conn, a.school, emphasis)
    dist = distinction_layer(profile, emphasis, c7_note)

    result = {
        "school": a.school, "tier": tier_name, "admission_rate": admission_rate,
        "emphasis_source": src,
        "gate": gate,
        "distinction": dist,
        "disclaimer": "v2 经验模型：门槛线按录取率分档，板块权重靠经验配置+C7微调；用于诊断与排序，不预测录取",
    }
    if conn:
        conn.close()

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        render(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
