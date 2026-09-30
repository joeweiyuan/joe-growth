# OfferPath 数据库勘察（2026-09-30）

> 研究问题：OfferPath（海外名校升学数据平台）里**哪些数据可用于 Joe 的升学**，以及**我的研究产出如何反哺 OfferPath**
> 勘察方式：本地 PostgreSQL `offerpath` 库 **只读** SELECT（未做任何写操作）
> 数据源：`psql -d offerpath`（14 表）

---

## 一、库表现状（实测行数）

| 表 | 行数 | 说明 |
|----|:----:|------|
| `admissions` | **405** | 各校各年中国/总录取数（核心） |
| `name_aliases` | **260** | 学校中英文别名 |
| `evaluations` | 3 | 升学评估记录（引擎输入/输出） |
| `users` | 1 | — |
| `universities` | **0** | ⚠️ 院校主表（tier/us_news/qs_rank/country/admission_info）为空 |
| `high_schools` / `admission_schools` | **0** | ⚠️ 生源高中维度**本地无数据** |
| `agencies` / `edu_agencies` / `payment_orders` / `favorites` / `data_versions` | 0 | 未启用 |

> 📌 与项目 STATE（2026-06-30：91 校 / 487 高中关联）不一致 → **本地库为部分快照，生产数据不在此**。

## 二、admissions：年份分布（核心资产）

| 年份 | 覆盖校数 | 中国录取累计 | 总录取累计 | 平均置信度 |
|:----:|:-------:|:-----------:|:---------:|:---------:|
| 2020 | 52 | 352 | — | 1.00 |
| 2021 | 59 | 310 | — | 1.00 |
| 2022 | 27 | 257 | — | 1.00 |
| 2023 | 28 | 182 | 23,600 | 1.00 |
| 2024 | 67 | 4,146 | 663,985 | **0.63** |
| 2025 | 48 | 3,631 | 226,867 | **0.71** |
| 2026 | **124** | **7,464** | 117,660 | **0.63** |

**数据源分布（关键风险）**：`whbc_official` 175 ｜ `ghcis_official` 58 ｜ `brave_search` 54 ｜ `public_aggregate` 34 ｜ **`estimated` 27** ｜ **`projected_estimate` 24**
→ ⚠️ **51/405 行（12.6%）为估算/预测值**，引用时必须带 source + confidence，不可当官方事实。

**中国录取累计 TOP15（含别名）**：UCL 1,297 ｜ Cambridge 1,064 ｜ HKBU 1,000 ｜ PolyU 928 ｜ Oxford 897 ｜ UCLA 663 ｜ CityU 644 ｜ Toronto 621 ｜ USC 566 ｜ HKU 525 ｜ **Cornell 498** ｜ KCL 495 ｜ Lingnan 452 ｜ Manchester 450 ｜ Imperial 403

## 三、evaluations：评估引擎的输入形状 ⭐

字段：`grade, gpa, toefl, toefl_listening/reading/writing/speaking, ielts(+4单项), sat, act, ap_scores(jsonb), activities(jsonb), target_major, target_university_id, city` → 输出 `score + recommendations`

**⭐ 这就是 Joe 档案应该维护的数据形状**——我的研究归档按此结构产出，即可**直接被 OfferPath 评估引擎消费**。

⚠️ **口径冲突（重要）**：引擎示例 `toefl=95`（0–120 制），而 Joe 是**六分制 4.0/6**（CEFR B2）→ 需要**标化口径映射表**（六分制 ↔ CEFR ↔ 120 制），否则 Joe 的数据喂进去会失真。

## 四、对 Joe 可复用的 4 项

1. **目标校中国录取规模与趋势**（`admissions`，带 confidence）→ 用于选校合理性判断与「冲/稳/保」分层参考
2. **中英校名对照**（`name_aliases` 260 条）→ 统一我的台账/清单命名，避免"康奈尔/Cornell"混用
3. **评估输入字段清单**（`evaluations` 结构）→ Joe 档案按此维护，未来一键喂评估
4. **缺口反推**：本地缺 `universities`/`high_schools` → **生源高中维度需生产库**；`admission_info` jsonb 字段正好可承接我核实的「标化/DDL/文书/招募」结构化结果

## 五、我的产出如何反哺 OfferPath（4 类）

| 我的归档 | OfferPath 用途 |
|---------|---------------|
| 逐校官方核实台账（每字段带 URL） | 填充 `universities.admission_info` |
| 标化口径映射（六分制/CEFR/120） | 修 `evaluations` 口径兼容 |
| 赛艇履历 + NCAA 简历 + 活动荣誉清单 | 体育招募模块 / 案例材料 |
| 数据纪律（来源+置信度+待核实规则） | 数据质量规范 |

## 六、结论

- **可用**：`admissions`（带 confidence）+ `name_aliases` + `evaluations` 字段设计
- **不可用/缺失**：`universities`、`high_schools`、`admission_schools`（本地 0 行，需生产库）
- **待家主决定**：是否需我把 Joe 的档案（GPA/托福六分制/赛艇/活动）按 `evaluations` 结构整理成**可导入样例**（不含任何编造数据）
