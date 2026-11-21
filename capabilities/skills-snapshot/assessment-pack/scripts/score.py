#!/usr/bin/env python3
"""
score.py — 综合竞争力评分引擎 v1（B5）+ 软实力分级（B3）

设计三原则：
  1. 可解释：每个维度输出「输入 → 计算 → 得分 → 驱动因素 / 短板」
  2. 可配置：权重全在 config/weights.json，代码不写死
  3. 可追踪：--snapshot 落库，--history 看增值

⚠️ 诚实边界：这是**经验模型 v1**，用于结构化诊断与横向对比，**不预测录取结果**。
"""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(os.path.dirname(HERE), "config", "weights.json")
DIM_LABELS = {"academic": "学术", "language": "语言", "depth": "学术深度",
              "leadership": "领导力", "talent": "特长"}


# ---------------------------------------------------------------- 工具
def load_config(path=CONFIG):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def rigor_index(courses, cfg):
    """课程强度：8 门全 AP = 100"""
    w = {"AP": 1.0, "IB_HL": 1.0, "A2": 1.0, "IB_SL": 0.7, "AS": 0.7, "HONORS": 0.5, "REGULAR": 0.3}
    total = 0.0
    for c in courses or []:
        lvl = str(c.get("level", "")).upper().replace(" ", "_")
        total += w.get(lvl, 0.3) * float(c.get("count", 1))
    return clamp(total / 8 * 100)


def level_score(level, cfg):
    return float(cfg["level_scores"].get(str(level).upper(), 20))


def entry_score(entry, cfg):
    """单条经历得分 = 等级分 × 时长系数（0.85 + 0.10×年，封顶 1.25）"""
    base = level_score(entry.get("level"), cfg)
    years = float(entry.get("years", 1) or 1)
    factor = min(1.25, 0.85 + 0.10 * years)
    return clamp(base * factor), factor


def best_block(entries, cfg):
    """取最强一条为主分；额外的 B 级以上经历给广度加分（每条 +2，封顶 +8）"""
    if not entries:
        return 0.0, [], []
    scored = []
    for e in entries:
        s, f = entry_score(e, cfg)
        scored.append((s, f, e))
    scored.sort(key=lambda x: -x[0])
    top = scored[0][0]
    breadth = sum(2 for s, _, e in scored[1:] if level_score(e.get("level"), cfg) >= 60)
    return clamp(top + min(8, breadth)), scored, []


# ---------------------------------------------------------------- 各维度
def dim_academic(p, cfg):
    a = p.get("academic", {}) or {}
    if a.get("pct_avg") is not None:
        pct = float(a["pct_avg"])
    elif a.get("gpa") is not None and a.get("max_gpa"):
        pct = float(a["gpa"]) / float(a["max_gpa"]) * 100
    else:
        return 0.0, {"error": "缺 GPA/百分制"}, ["无成绩数据"], ["补充成绩单"]
    rigor = rigor_index(a.get("courses"), cfg)
    trend = cfg["academic"]["trend_scores"].get(a.get("trend", "flat"), 60)
    c = cfg["academic"]
    score = pct * c["pct_weight"] + rigor * c["rigor_weight"] + trend * c["trend_weight"]
    drivers, weak = [], []
    (drivers if pct >= 85 else weak).append(f"成绩 {pct:.1f}（权重 {c['pct_weight']:.0%}）")
    (drivers if rigor >= 60 else weak).append(f"课程强度 {rigor:.0f}（权重 {c['rigor_weight']:.0%}）")
    (drivers if trend >= 60 else weak).append(f"趋势 {a.get('trend', 'flat')}（权重 {c['trend_weight']:.0%}）")
    return clamp(score), {"pct": round(pct, 2), "rigor": round(rigor, 1), "trend": trend}, drivers, weak


def dim_language(p, cfg):
    l = p.get("language", {}) or {}
    cands = []
    if l.get("toefl6") is not None:
        cands.append(("TOEFL(6分制)", float(l["toefl6"]) / 6 * 100, l["toefl6"]))
    if l.get("ielts") is not None:
        cands.append(("IELTS", float(l["ielts"]) / 9 * 100, l["ielts"]))
    if l.get("sat") is not None:
        cands.append(("SAT", (float(l["sat"]) - 400) / 1200 * 100, l["sat"]))
    if l.get("act") is not None:
        cands.append(("ACT", (float(l["act"]) - 1) / 35 * 100, l["act"]))
    if not cands:
        return 0.0, {"error": "无语言/标化成绩"}, [], ["补语言成绩（托福/雅思）"]
    name, score, raw = max(cands, key=lambda x: x[1])
    drivers = [f"{name} {raw} → 折算 {score:.0f}"] if score >= 70 else []
    weak = [f"{name} {raw} → 折算 {score:.0f}（目标 75+）"] if score < 70 else []
    return clamp(score), {"source": name, "raw": raw, "all": [c[0] for c in cands]}, drivers, weak


def dim_block(p, key, cfg):
    entries = p.get(key) or []
    score, scored, _ = best_block(entries, cfg)
    drivers, weak = [], []
    if scored:
        s, f, e = scored[0]
        label = e.get("name") or e.get("role") or e.get("domain") or "主项"
        (drivers if s >= 60 else weak).append(f"最强项：{label}（{e.get('level')} 级 × 时长系数 {f:.2f} = {s:.0f}）")
        if len(scored) > 1:
            drivers.append(f"另有 {len(scored) - 1} 项经历（广度加分）")
    else:
        weak.append("暂无该维度经历")
    return score, {"entries": len(entries)}, drivers, weak


# ---------------------------------------------------------------- 合成
def effective_weights(cfg, dest, major):
    base = dict(cfg["weights_by_destination"].get(dest, cfg["weights_by_destination"]["us"]))
    tilt = cfg.get("major_tilt", {}).get(major) or {}
    for k, v in tilt.items():
        base[k] = base.get(k, 0) + v
    base = {k: max(1.0, v) for k, v in base.items()}  # 防止负权重
    tot = sum(base.values())
    return {k: v / tot for k, v in base.items()}


def band_of(composite, cfg):
    for b in cfg["bands"]:
        if composite >= b["min"]:
            return b
    return cfg["bands"][-1]


def evaluate(profile, cfg, dest="us", major="stem"):
    dims = {}
    detail = {}
    for d, fn in (("academic", dim_academic), ("language", dim_language)):
        s, info, drv, weak = fn(profile, cfg)
        dims[d], detail[d] = s, {"info": info, "drivers": drv, "weak": weak}
    for d in ("depth", "leadership", "talent"):
        s, info, drv, weak = dim_block(profile, d, cfg)
        dims[d], detail[d] = s, {"info": info, "drivers": drv, "weak": weak}

    w = effective_weights(cfg, dest, major)
    composite = sum(dims[d] * w[d] for d in dims)
    band = band_of(composite, cfg)

    # 边际收益：每个维度补到下一档（+15 分）能带来多少综合分
    gaps = []
    for d, s in dims.items():
        target = min(100.0, s + 15)
        gain = (target - s) * w[d]
        gaps.append({"dimension": d, "label": DIM_LABELS[d], "current": round(s, 1),
                     "weight": round(w[d], 3), "gain_if_plus15": round(gain, 2)})
    gaps.sort(key=lambda x: -x["gain_if_plus15"])

    return {
        "dest": dest, "major": major,
        "dimensions": {k: round(v, 1) for k, v in dims.items()},
        "weights": {k: round(v, 3) for k, v in w.items()},
        "composite": round(composite, 1),
        "band": band["band"], "band_desc": band["desc"],
        "detail": detail,
        "top_actions": gaps[:3],
        "disclaimer": "经验模型 v1：用于结构化诊断与横向对比，不预测录取结果",
    }


# ---------------------------------------------------------------- 目标校对照
def compare_target(result, profile, db_path, slug):
    if not db_path or not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM cds_records WHERE univ_slug=? ORDER BY cds_year DESC LIMIT 1", (slug,)).fetchone()
    conn.close()
    if not row:
        return {"error": f"库中无 {slug} 的 CDS 记录"}
    out = {"school": slug, "cds_year": row["cds_year"], "admission_rate": row["admission_rate"]}
    sat = (profile.get("language") or {}).get("sat")
    if sat and row["sat_math_25"] and row["sat_ebrw_75"]:
        lo = row["sat_math_25"] + row["sat_ebrw_25"]
        hi = row["sat_math_75"] + row["sat_ebrw_75"]
        out["sat_band"] = [lo, hi]
        if sat < lo:
            out["sat_position"] = "低于 25 分位"
        elif sat > hi:
            out["sat_position"] = "高于 75 分位"
        else:
            out["sat_position"] = "处于 25–75 分位之间"
    else:
        out["sat_position"] = "数据不足（缺 SAT 或该校 CDS 标化）"
    return out


# ---------------------------------------------------------------- 快照
def snapshot(result, profile, db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT, grade TEXT, dest TEXT, major TEXT,
        composite REAL, dimensions TEXT, created_at TEXT)""")
    prev = conn.execute("SELECT composite, dimensions FROM assessments ORDER BY id DESC LIMIT 1").fetchone()
    conn.execute("INSERT INTO assessments (student, grade, dest, major, composite, dimensions, created_at) VALUES (?,?,?,?,?,?,?)",
                 ((profile.get("student") or {}).get("name"), (profile.get("student") or {}).get("grade"),
                  result["dest"], result["major"], result["composite"],
                  json.dumps(result["dimensions"], ensure_ascii=False),
                  datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
    conn.close()
    delta = None
    if prev:
        delta = round(result["composite"] - prev[0], 1)
    return {"saved": True, "total_snapshots": n, "delta_vs_previous": delta}


def main():
    ap = argparse.ArgumentParser(description="综合竞争力评分 v1")
    ap.add_argument("--profile", required=True, help="学生档案 JSON")
    ap.add_argument("--dest", default="us", choices=["us", "uk", "ca", "au", "hk", "sg", "eu"])
    ap.add_argument("--major", default="stem", choices=["stem", "business", "humanities", "arts"])
    ap.add_argument("--target", help="目标校 slug（配合 --db）")
    ap.add_argument("--db", help="college.db 路径（CDS 数据）")
    ap.add_argument("--snapshot-db", help="落库做增值追踪")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    a = ap.parse_args()

    cfg = load_config()
    profile = json.load(open(a.profile, encoding="utf-8"))
    res = evaluate(profile, cfg, a.dest, a.major)
    if a.target:
        res["target_compare"] = compare_target(res, profile, a.db, a.target)
    if a.snapshot_db:
        res["snapshot"] = snapshot(res, profile, a.snapshot_db)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print(f"\n{'='*54}")
    print(f"综合竞争力评分：{res['composite']}/100  【{res['band']}】{res['band_desc']}")
    print(f"方向：{res['dest'].upper()} ｜ 专业倾向：{res['major']}")
    print(f"{'='*54}")
    for d, s in res["dimensions"].items():
        w = res["weights"][d]
        bar = "█" * int(s / 5) + "░" * (20 - int(s / 5))
        print(f"{DIM_LABELS[d]:6s} {s:5.1f}  {bar}  权重 {w:.0%}")
    print(f"\n{'='*54}\n可提升项（每补 15 分带来的综合分增益）\n{'='*54}")
    for g in res["top_actions"]:
        print(f"  {g['label']}：当前 {g['current']} → +{g['gain_if_plus15']} 分（权重 {g['weight']:.0%}）")
    print(f"\n⚠️ {res['disclaimer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
