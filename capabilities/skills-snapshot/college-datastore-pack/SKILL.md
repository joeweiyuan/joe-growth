---
name: college-datastore-pack
description: "Use when 建院校库/CDS/标化分布/GPA 换算。"
version: 1.0.0
author: 六六
license: MIT
metadata:
  hermes:
    tags: [college, cds, common-data-set, sat, act, gpa, datastore, offerpath]
    requires_tools: [terminal, read_file, write_file, web]
    editorial_name: "院校数据底座"
    editorial_description: "CDS 结构化解析 + 标化分布入库 + 跨体系 GPA 换算；每条数据带来源与 sha256，缺字段不猜"
---

# 院校数据底座（college-datastore-pack）

> 填补 OfferPath 的三个数据缺口：**A1 CDS 字段结构化 / A4 标化分布库 / A5 费用库 + B1 跨体系 GPA**

## 何时用
- 要把某校的 Common Data Set（PDF）变成可用字段
- 要算「这个学生相当于美本 4.0 制的多少」（AP/IB/A-Level/普高）
- 要给选校匹配引擎准备 录取率/标化分布/截止日/学费

## 三件工具（都已实跑验收）

### 1️⃣ `scripts/gpa_convert.py` — 跨体系换算
```bash
python3 scripts/gpa_convert.py --joe                      # Joe 实测（3.73/4.40 → 84.8%）
python3 scripts/gpa_convert.py --system ib --value 6      # → 88 分
python3 scripts/gpa_convert.py --system alevel --value A*  # → 95 分
python3 scripts/gpa_convert.py --system weighted --value 3.73 --max 4.40
```
输出：百分制等价 / 4.0 分级 / 4.0 线性 / 课程强度指数（rigor_index）

> ⚠️ 跨体系换算**没有全球官方表**；本工具输出必须标注「换算值，非校方原始口径」。

### 2️⃣ `scripts/cds_parse.py` — CDS 结构化
```bash
pdftotext -layout CDS2025.pdf cds.txt
python3 scripts/cds_parse.py cds.txt --meta meta.json
```
抽取 8 项：录取率（C1）· SAT EBRW 25/75 · SAT Math 25/75 · ACT 25/75（C9）· ED/EA/RD 截止日（C11）· 学费/食宿（G/H）
**每项带原文片段做证据；抽不到就返回 null 并列入 missing——不猜。**

### 3️⃣ `scripts/store.py` — 入库与查询（SQLite）
```bash
python3 scripts/store.py init
python3 scripts/store.py ingest --univ mit --year 2025 --text cds.txt --meta meta.json --url https://...
python3 scripts/store.py query --univ mit
python3 scripts/store.py export --out colleges.csv
```

## 数据契约
```
universities(slug PK, name_en, name_cn, country, city, us_news, qs_rank)
cds_records(univ_slug, cds_year, applied, admitted, enrolled, admission_rate,
            sat_ebrw_25/75, sat_math_25/75, act_25/75,
            ed/ea/rd_deadline, tuition, room_board,
            coverage, missing_fields, source_url, source_sha256, parsed_at)
sources(univ_slug, cds_year, url, sha256, fetched_at)
```

## 🔴 质量门
1. **每条 CDS 必须带 `source_url` + `sha256`** → 可溯源、可复现
2. **`missing_fields` 不为空时不得对外发布该行**（先补录）
3. 标化值域校验：SAT 200–800、ACT 1–36，超出即拒收
4. 同年同校唯一：`UNIQUE(univ_slug, cds_year)`，重跑覆盖不重复
5. 换算口径必须随值输出，禁止只给数字

## 与 OfferPath 现有库的对接
现有 `universities(id, name, name_cn, tier, us_news, qs_rank, country, city)` **缺 CDS 字段**：
- 建议新增 `cds_records` 表（本包 schema 直接可用）
- `universities.id` ↔ 本包 `slug` 做映射即可，不破坏现有 MVP
- `evaluations.score` 的单分值 → 建议拆为「维度分 + 综合分」，用本包 GPA 输出做学术维度输入

## 验收
`tests/test_all.py` → **17/17 通过**（GPA 4 项 + 单体系 3 项 + CDS 6 项 + 入库导出 4 项）
