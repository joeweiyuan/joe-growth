#!/usr/bin/env python3
"""assessment-pack 验收：评分引擎 / 权重切换 / 目标对照 / 快照增值"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
SCORE = os.path.join(SCRIPTS, "score.py")
PROFILE = os.path.join(HERE, "joe_profile.json")

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("✅" if cond else "❌"), name, detail)


def run(*args):
    r = subprocess.run([sys.executable, SCORE, *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def evaluate(*extra):
    rc, out, err = run("--profile", PROFILE, "--json", *extra)
    if rc != 0:
        print(err)
    return json.loads(out)


# ---------- 1. 基准分数（回归锚点）
d = evaluate("--dest", "us", "--major", "stem")
check("US/STEM 综合分 = 77.0", abs(d["composite"] - 77.0) < 0.6, f'{d["composite"]}')
check("五个维度齐全", set(d["dimensions"]) == {"academic", "language", "depth", "leadership", "talent"})
check("权重和为 1", abs(sum(d["weights"].values()) - 1.0) < 1e-6)
check("维度均在 0–100", all(0 <= v <= 100 for v in d["dimensions"].values()), str(d["dimensions"]))
check("学术分 = 78.2", abs(d["dimensions"]["academic"] - 78.2) < 0.3, f'{d["dimensions"]["academic"]}')
check("语言分 = 66.7（托福 4.0/6）", abs(d["dimensions"]["language"] - 66.67) < 0.5)
check("有可解释明细", all("info" in d["detail"][k] for k in d["dimensions"]))
check("有 top_actions", len(d["top_actions"]) == 3, str([a["label"] for a in d["top_actions"]]))

# ---------- 2. 方向权重差异（英本学术权重更高、领导力更低）
uk = evaluate("--dest", "uk", "--major", "stem")
check("UK 学术权重 > US", uk["weights"]["academic"] > d["weights"]["academic"],
      f'{uk["weights"]["academic"]:.2f} vs {d["weights"]["academic"]:.2f}')
check("UK 领导力权重 < US", uk["weights"]["leadership"] < d["weights"]["leadership"],
      f'{uk["weights"]["leadership"]:.2f} vs {d["weights"]["leadership"]:.2f}')

# ---------- 3. 专业倾向影响（艺术生特长权重更高）
arts = evaluate("--dest", "us", "--major", "arts")
check("艺术倾向特长权重 > STEM", arts["weights"]["talent"] > d["weights"]["talent"],
      f'{arts["weights"]["talent"]:.2f} vs {d["weights"]["talent"]:.2f}')

# ---------- 4. 缺数据的诚实处理
tmpdir = tempfile.mkdtemp()
empty = os.path.join(tmpdir, "empty.json")
json.dump({"student": {"name": "T", "grade": "9"}}, open(empty, "w", encoding="utf-8"))
rc, out, err = run("--profile", empty, "--json")
e = json.loads(out)
check("缺成绩 → 学术 0 且不崩溃", e["dimensions"]["academic"] == 0)
check("缺语言 → 给出补语言建议", any("语言" in w for w in e["detail"]["language"]["weak"]))

# ---------- 5. 目标校对照（有 CDS 库）
db = "/tmp/college_test.db"
if os.path.exists(db):
    t = evaluate("--dest", "us", "--major", "stem", "--target", "mit", "--db", db)
    tc = t.get("target_compare") or {}
    check("目标校对照返回录取率", tc.get("admission_rate") == 5.25, str(tc.get("admission_rate")))
    check("缺 SAT 时如实说明", "数据不足" in str(tc.get("sat_position")))
    t2 = evaluate("--dest", "us", "--major", "stem", "--target", "nonexistent", "--db", db)
    check("无此校 → 报错不编造", "error" in (t2.get("target_compare") or {}))
else:
    print("（跳过目标校对照：缺 /tmp/college_test.db）")

# ---------- 6. 快照与增值
snap_db = os.path.join(tmpdir, "a.db")
s1 = evaluate("--dest", "us", "--major", "stem", "--snapshot-db", snap_db)
s2 = evaluate("--dest", "us", "--major", "stem", "--snapshot-db", snap_db)
check("首次快照无 delta", s1["snapshot"]["delta_vs_previous"] is None)
check("二次快照 delta = 0", s2["snapshot"]["delta_vs_previous"] == 0.0, str(s2["snapshot"]))
check("快照累计 2 条", s2["snapshot"]["total_snapshots"] == 2)

bad = [r for r in results if not r[1]]
print(f"\n=== {len(results) - len(bad)}/{len(results)} 通过 ===")
if bad:
    print("失败:", [b[0] for b in bad])
sys.exit(1 if bad else 0)
