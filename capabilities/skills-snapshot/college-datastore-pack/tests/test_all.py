#!/usr/bin/env python3
"""college-datastore-pack 验收测试：GPA 换算 / CDS 解析 / 入库查询 三条链"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
GPA = os.path.join(SCRIPTS, "gpa_convert.py")
CDS = os.path.join(SCRIPTS, "cds_parse.py")
STORE = os.path.join(SCRIPTS, "store.py")

FIXTURE = """
C. FIRST-TIME, FIRST-YEAR (FRESHMAN) ADMISSION

C1 First-time, first-year (freshman) admission
                        Applied     Admitted    Enrolled
Full-time               20,000      1,050       520
Total                   20,200      1,070       525

C9 Test Scores
SAT Evidence-Based Reading and Writing
25th percentile 700
75th percentile 770
SAT Math
25th percentile 780
75th percentile 800
ACT Composite
25th percentile 33
75th percentile 35

C11 Application Deadlines
Early Action            11/1
Early Decision          11/1
Regular Decision        1/5

G. ANNUAL EXPENSES
Tuition and fees        62,000
Room and board          19,500
"""

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("✅" if cond else "❌"), name, detail)


def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


# ---------- 1. GPA 引擎：Joe 实测 ----------
rc, out, err = run(GPA, "--joe")
d = json.loads(out)
o = d["official"]
check("官方 GPA 复算 = 3.73", abs(o["official_gpa"] - 3.73) < 0.005, f'{o["official_gpa"]}')
check("满绩 = 4.40", abs(o["max_gpa"] - 4.40) < 0.005, f'{o["max_gpa"]}')
check("达成率 = 84.8%", abs(o["achievement_pct"] - 84.8) < 0.05, f'{o["achievement_pct"]}%')
check("折合 4.0（线性）= 3.41", abs(d["normalized"]["gpa_linear"] - 3.41) < 0.01, f'{d["normalized"]["gpa_linear"]}')

# ---------- 2. 单体系换算 ----------
rc, out, _ = run(GPA, "--system", "ib", "--value", "6")
check("IB 6 → 88", abs(json.loads(out)["pct"] - 88) < 0.01)
rc, out, _ = run(GPA, "--system", "alevel", "--value", "A*")
check("A-Level A* → 95", abs(json.loads(out)["pct"] - 95) < 0.01)
rc, out, _ = run(GPA, "--system", "weighted", "--value", "3.73", "--max", "4.40")
check("3.73/4.40 → 84.77", abs(json.loads(out)["pct"] - 84.77) < 0.05)

# ---------- 3. CDS 解析 ----------
tmpdir = tempfile.mkdtemp()
cds_path = os.path.join(tmpdir, "cds.txt")
open(cds_path, "w", encoding="utf-8").write(FIXTURE)
rc, out, err = run(CDS, cds_path)
p = json.loads(out)
check("CDS 覆盖 8/8", p["coverage"] == "8/8", p["coverage"])
check("录取率 5.25%", abs(p["c1_admissions"]["admission_rate"] - 5.25) < 0.01)
check("SAT EBRW 700-770", p["c9_test_scores"]["sat_ebrw_25"] == 700 and p["c9_test_scores"]["sat_ebrw_75"] == 770)
check("SAT Math 780-800", p["c9_test_scores"]["sat_math_25"] == 780 and p["c9_test_scores"]["sat_math_75"] == 800)
check("ACT 33-35", p["c9_test_scores"]["act_25"] == 33 and p["c9_test_scores"]["act_75"] == 35)
check("三个截止日期齐全", len(p["c11_deadlines"]["deadlines"]) == 3, str(p["c11_deadlines"]["deadlines"]))

# ---------- 4. 入库 → 查询 → 导出 ----------
db = os.path.join(tmpdir, "college.db")
meta = os.path.join(tmpdir, "meta.json")
json.dump({"name_cn": "麻省理工学院", "name_en": "MIT", "country": "US"}, open(meta, "w", encoding="utf-8"))
rc, out, err = run(STORE, "--db", db, "ingest", "--univ", "mit", "--year", "2025",
                   "--text", cds_path, "--meta", meta, "--url", "https://example.edu/cds.pdf")
check("入库成功", rc == 0, err[:80])
rc, out, err = run(STORE, "--db", db, "query", "--univ", "mit")
rows = json.loads(out)
check("查询返回 1 条", len(rows) == 1)
check("库内录取率正确", abs(rows[0]["admission_rate"] - 5.25) < 0.01)
csv_path = os.path.join(tmpdir, "out.csv")
rc, out, err = run(STORE, "--db", db, "export", "--out", csv_path)
check("导出 CSV", os.path.exists(csv_path) and len(open(csv_path, encoding="utf-8").read().strip().split("\n")) == 2)

bad = [r for r in results if not r[1]]
print(f"\n=== {len(results) - len(bad)}/{len(results)} 通过 ===")
if bad:
    print("失败:", [b[0] for b in bad])
sys.exit(1 if bad else 0)
