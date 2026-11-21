#!/usr/bin/env python3
"""score_v2 验收：门槛层 / 独立板块 / 目标校权重 / C7 校准"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
V2 = os.path.join(SCRIPTS, "score_v2.py")
PROFILE = os.path.join(HERE, "joe_profile_v2.json")
DB = "/tmp/college_test.db"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("✅" if cond else "❌"), name, detail)


def run(*extra):
    args = [sys.executable, V2, "--profile", PROFILE, "--json", *extra]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:", r.stderr[:400])
    return json.loads(r.stdout)


# ---------- 1. 门槛层（Joe vs MIT tier1）
d = run("--school", "mit", "--db", DB)
check("分档 = tier1（录取率 5.25%）", d["tier"] == "tier1_admit_lt10", d["tier"])
check("GPA 门槛未达", d["gate"]["gpa"]["status"] == "fail", str(d["gate"]["gpa"]))
check("GPA 差额 -3.81", abs(d["gate"]["gpa"]["gap"] + 3.81) < 0.05, str(d["gate"]["gpa"]["gap"]))
check("标化门槛未达（4.0 vs 5.5）", d["gate"]["language"]["status"] == "fail", str(d["gate"]["language"]))
check("整体门槛 = fail", d["gate"]["overall"] == "fail")
check("门槛结论提到不可弥补", "不能弥补" in d["gate"]["verdict"])

# ---------- 2. 板块独立评分
b = d["distinction"]["blocks"]
check("竞赛 = 78.0", abs(b["competition"] - 78.0) < 0.3, str(b["competition"]))
check("科创 = 80.0", abs(b["research"] - 80.0) < 0.3, str(b["research"]))
check("体育 = 75.0", abs(b["sports"] - 75.0) < 0.3, str(b["sports"]))
check("四个板块互相独立（值不全等）", len(set(round(v, 1) for v in b.values())) >= 3, str(b))
w = d["distinction"]["weights"]
check("权重和为 1", abs(sum(w.values()) - 1.0) < 1e-6, str(w))

# ---------- 3. C7 校准生效
check("读了 C7", d["distinction"].get("c7") is not None, json.dumps(d["distinction"].get("c7"), ensure_ascii=False))
if d["distinction"].get("c7"):
    check("C7 课外=important", d["distinction"]["c7"]["extracurricular"] == "important")

# ---------- 4. 学校不同 → 权重不同
mit = run("--school", "mit", "--db", DB)
risd = run("--school", "risd", "--db", DB)
check("艺术院校艺术权重 > MIT", risd["distinction"]["weights"]["arts"] > mit["distinction"]["weights"]["arts"],
      f'{risd["distinction"]["weights"]["arts"]:.2f} vs {mit["distinction"]["weights"]["arts"]:.2f}')
check("艺术院校科创权重 < MIT", risd["distinction"]["weights"]["research"] < mit["distinction"]["weights"]["research"])
check("未收录校给出默认画像标注", "default" in run("--school", "unknown_u")["emphasis_source"])

# ---------- 5. 门槛可通过的情形（降低目标档）
lo = run("--tier", "tier4_admit_lt100")
check("tier4 下 GPA 通过", lo["gate"]["gpa"]["status"] == "pass", str(lo["gate"]["gpa"]))
check("tier4 下标化通过", lo["gate"]["language"]["status"] == "pass", str(lo["gate"]["language"]))
check("tier4 整体通过", lo["gate"]["overall"] == "pass")

bad = [r for r in results if not r[1]]
print(f"\n=== {len(results) - len(bad)}/{len(results)} 通过 ===")
if bad:
    print("失败:", [b[0] for b in bad])
sys.exit(1 if bad else 0)
