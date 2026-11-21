#!/usr/bin/env python3
"""
cds_parse.py — Common Data Set（CDS）结构化解析器

输入：CDS 的纯文本（PDF 先经 `pdftotext -layout`，或学校官网 HTML 转文本）
输出：结构化 JSON（录取统计 / 标化分布 / 截止日期 / 费用），**每项带原文行号与命中片段**

原则：找不到就返回 null + 记入 missing，**绝不猜**。
"""
import argparse
import json
import re

# ---------------------------------------------------------------- 通用工具
def _num(s):
    s = s.replace(",", "").replace("%", "").strip()
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def _find_line(lines, *patterns, window=None):
    """返回 (行号, 行文本)；window 用于在命中行之后若干行内找"""
    for i, line in enumerate(lines):
        for p in patterns:
            if re.search(p, line, re.I):
                return i, line
    return None, None


# ---------------------------------------------------------------- 各区块
def parse_c1(lines):
    """C1 申请/录取/入读人数 → 录取率"""
    res = {"applied": None, "admitted": None, "enrolled": None, "admission_rate": None,
           "evidence": {}}
    idx, line = _find_line(lines, r"C1\b.*(First-time|freshman).*(admission|admissions)",
                           r"First-time, first-year.*admission")
    if idx is None:
        # 退化：找含 Applied/Admitted/Enrolled 的连续段
        idx, _ = _find_line(lines, r"^\s*Applied\s+Admitted\s+Enrolled")
        if idx is None:
            idx, _ = _find_line(lines, r"Applied.*Admitted.*Enrolled")
    if idx is None:
        return res

    block = "\n".join(lines[idx:idx + 12])
    # 形式 A：三列数字（Total / Men / Women），允许中间有 "Full-time" 等前缀
    m = re.search(r"Applied\s+Admitted\s+Enrolled[^\n]*\n[^\n]*?([\d,]+)\s+([\d,]+)\s+([\d,]+)", block)
    if m:
        res.update(applied=_num(m.group(1)), admitted=_num(m.group(2)), enrolled=_num(m.group(3)))
        res["evidence"]["counts"] = {"line": idx + 1, "snippet": m.group(0)[:120]}
    else:
        # 形式 B：Applied 5,500 / Admitted 300 ... 逐项
        for key, pat in (("applied", r"Applied[^0-9]{0,40}([\d,]+)"),
                         ("admitted", r"Admitted[^0-9]{0,40}([\d,]+)"),
                         ("enrolled", r"Enrolled[^0-9]{0,40}([\d,]+)")):
            mm = re.search(pat, block, re.I)
            if mm:
                res[key] = _num(mm.group(1))
                res["evidence"][key] = {"line": idx + 1, "snippet": mm.group(0)[:100]}
    if res["applied"] and res["admitted"]:
        res["admission_rate"] = round(res["admitted"] / res["applied"] * 100, 2)
    return res


def parse_c9(lines):
    """C9 标化分布（25/75 百分位）

    CDS 原文常见排版：标签一行、25th/75th 另起行 → 先把区块压平再匹配。
    """
    res = {"sat_ebrw_25": None, "sat_ebrw_75": None, "sat_math_25": None, "sat_math_75": None,
           "act_25": None, "act_75": None, "evidence": {}}

    # 截取 C9 区块（到下一个 C10 / C12 / D 段为止）
    start = None
    for i, line in enumerate(lines):
        if re.search(r"C9\b.*(Test Scores|SAT|ACT)", line, re.I) or re.match(r"^\s*C9\b", line):
            start = i
            break
    if start is None:
        return res
    end = len(lines)
    for j in range(start + 1, min(len(lines), start + 120)):
        if re.match(r"^\s*(C1[0-9]|D\s*\.|D[0-9])\b", lines[j]):
            end = j
            break
    block = re.sub(r"\s+", " ", " ".join(lines[start:end]))

    def grab(label_pat, lo, hi):
        """在标签后按 '25th percentile X ... 75th percentile Y' 抓取，并做值域校验"""
        pat = (label_pat +
               r".{0,140}?25\s*(?:th|st)?\s*percentile\D{0,12}(\d{1,4})" +
               r".{0,100}?75\s*(?:th|st)?\s*percentile\D{0,12}(\d{1,4})")
        m = re.search(pat, block, re.I)
        if not m:
            return None, None, None
        a, b = int(m.group(1)), int(m.group(2))
        if not (lo <= a <= hi and lo <= b <= hi) or a > b:
            return None, None, f"out-of-range: {a},{b}"
        return float(a), float(b), m.group(0)[:160]

    a, b, ev = grab(r"(?:Evidence[- ]Based Reading and Writing|EBRW)", 200, 800)
    if a is not None:
        res.update(sat_ebrw_25=a, sat_ebrw_75=b)
        res["evidence"]["sat_ebrw"] = {"section": "C9", "snippet": ev}

    a, b, ev = grab(r"(?:SAT\s*Math)", 200, 800)
    if a is not None:
        res.update(sat_math_25=a, sat_math_75=b)
        res["evidence"]["sat_math"] = {"section": "C9", "snippet": ev}

    a, b, ev = grab(r"(?:ACT\s*Composite)", 1, 36)
    if a is not None:
        res.update(act_25=a, act_75=b)
        res["evidence"]["act"] = {"section": "C9", "snippet": ev}
    return res


def parse_c11(lines):
    """C11 截止日期（ED/EA/RD）"""
    res = {"deadlines": {}, "evidence": {}}
    idx, _ = _find_line(lines, r"C11\b.*(Deadlines|Application)", r"Deadlines")
    start = idx if idx is not None else 0
    block = "\n".join(lines[start:start + 40])
    pats = {
        "ED": r"(Early Decision|ED)\b[^\n]{0,60}?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
        "EA": r"(Early Action|EA)\b[^\n]{0,60}?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
        "RD": r"(Regular Decision|RD)\b[^\n]{0,60}?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
    }
    for k, p in pats.items():
        m = re.search(p, block, re.I)
        if m:
            res["deadlines"][k] = m.group(2)
            res["evidence"][k] = {"line": start + 1, "snippet": m.group(0)[:120]}
    return res


def parse_c7(lines):
    """C7 录取因素重视程度（官方）

    表头四档：Very Important / Important / Considered / Not Considered
    返回 {factor_key: importance}
    """
    res = {"factors": {}, "evidence": {"section": "C7"}}
    start = None
    for i, line in enumerate(lines):
        if re.search(r"C7\b.*(Relative importance|importance of each)", line, re.I) or \
           re.search(r"Relative importance of each", line, re.I):
            start = i
            break
    if start is None:
        return res

    end = len(lines)
    for j in range(start + 1, min(len(lines), start + 90)):
        if re.match(r"^\s*(C8|D\s*\.|D[0-9])\b", lines[j]):
            end = j
            break

    # 表头列位置
    header = ""
    for j in range(start, min(end, start + 6)):
        if re.search(r"Very Important", lines[j], re.I) or re.search(r"Important\s+Considered", lines[j], re.I):
            header = lines[j]
            break
    cols = {}
    if header:
        for key, pat in (("very_important", r"Very\s+Important"),
                         ("important", r"(?<!Very\s)\bImportant\b"),
                         ("considered", r"Considered"),
                         ("not_considered", r"Not\s+Considered")):
            m = re.search(pat, header, re.I)
            if m:
                cols[key] = m.start()

    FACTORS = {
        "rigor": r"Rigor of secondary school record",
        "class_rank": r"Class rank",
        "gpa": r"Academic GPA",
        "test_scores": r"Standardized test scores",
        "essay": r"Application essay",
        "recommendation": r"Recommendation",
        "interview": r"Interview",
        "extracurricular": r"Extracurricular activities",
        "talent": r"Talent/ability",
        "character": r"Character/personal qualities",
        "first_gen": r"First generation",
        "alumni": r"Alumni/ae relation",
        "geography": r"Geographical residence",
        "state_residency": r"State residency",
        "religion": r"Religious affiliation",
        "race": r"Racial/ethnic status",
        "volunteer": r"Volunteer work",
        "work": r"Work experience",
        "interest": r"Level of applicant.s interest",
    }

    for j in range(start, end):
        line = lines[j]
        for key, pat in FACTORS.items():
            if key in res["factors"]:
                continue
            if re.search(pat, line, re.I):
                marks = [m.start() for m in re.finditer(r"[X✓✔]", line)]
                if not marks:
                    continue
                pos = marks[0]
                level = None
                if cols:
                    # 归到最近的列
                    best = min(cols.items(), key=lambda kv: abs(kv[1] - pos))
                    level = best[0]
                res["factors"][key] = level or "marked"
    return res


def parse_cost(lines):
    """G/H 区块：学费与食宿"""
    res = {"tuition": None, "room_board": None, "evidence": {}}
    idx, _ = _find_line(lines, r"(Tuition and fees|Tuition & fees)", r"Tuition")
    if idx is not None:
        seg = "\n".join(lines[idx:idx + 8])
        m = re.search(r"Tuition and fees[^\d]{0,60}([\d,]+)", seg, re.I)
        if m:
            res["tuition"] = _num(m.group(1))
            res["evidence"]["tuition"] = {"line": idx + 1, "snippet": m.group(0)[:120]}
    idx2, _ = _find_line(lines, r"(Room and board|Room & board)")
    if idx2 is not None:
        seg = "\n".join(lines[idx2:idx2 + 6])
        m = re.search(r"Room and board[^\d]{0,60}([\d,]+)", seg, re.I)
        if m:
            res["room_board"] = _num(m.group(1))
            res["evidence"]["room_board"] = {"line": idx2 + 1, "snippet": m.group(0)[:120]}
    return res


# ---------------------------------------------------------------- 主流程
def parse(text, meta=None):
    lines = text.splitlines()
    out = {
        "meta": meta or {},
        "c1_admissions": parse_c1(lines),
        "c9_test_scores": parse_c9(lines),
        "c11_deadlines": parse_c11(lines),
        "c7_factors": parse_c7(lines),
        "costs": parse_cost(lines),
    }
    # 汇总缺失字段（给人工补录用，不自动填）
    missing = []
    if out["c1_admissions"]["admission_rate"] is None:
        missing.append("admission_rate")
    for k in ("sat_ebrw_25", "sat_ebrw_75", "sat_math_25", "sat_math_75", "act_25", "act_75"):
        if out["c9_test_scores"][k] is None:
            missing.append(k)
    if not out["c11_deadlines"]["deadlines"]:
        missing.append("deadlines")
    if out["costs"]["tuition"] is None:
        missing.append("tuition")
    out["missing"] = missing
    out["coverage"] = f"{8 - len(missing)}/8"
    return out


def main():
    ap = argparse.ArgumentParser(description="CDS 结构化解析")
    ap.add_argument("text_file")
    ap.add_argument("--meta", help="JSON 元数据（校名/年份/来源 URL）")
    a = ap.parse_args()
    text = open(a.text_file, encoding="utf-8", errors="ignore").read()
    meta = json.load(open(a.meta, encoding="utf-8")) if a.meta else {}
    print(json.dumps(parse(text, meta), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
