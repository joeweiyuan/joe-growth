# OfferPath 院校数据集（六六 → 云策）

> **固定位置，请以此为准，不要再复制到别处。**
> 生成方：六六（joe profile）｜ 使用方：云策（dad profile）/ OfferPath MVP
> 只读消费：**六六写，云策读**（避免双写冲突）

---

## 1. 位置

```
/root/shared/offerpath/
├── college.db              ← SQLite 权威库（VACUUM 单文件，无 WAL 依赖）
├── schema.sql              ← 建表语句（可直接搬 Postgres）
├── manifest.json           ← 版本 / 行数 / 校验和 / 各校质量
├── README.md               ← 本文件（数据契约）
├── check.py                ← 完整性自检（云策可随时跑）
└── exports/
    ├── universities.csv/.json
    ├── cds_records.csv/.json
    ├── cds_factors.csv/.json
    └── cds_sources.csv/.json
```

CSV 为 **UTF-8 BOM**，Excel 双击可直接打开；JSON 供程序接入。

---

## 2. 四张表

### `universities` — 院校主表
| 字段 | 类型 | 说明 |
|:--|:--|:--|
| `slug` | TEXT PK | 稳定标识（`mit` / `harvard`），**对接用这个，不要用中文名** |
| `name_en` / `name_cn` | TEXT | 英文 / 中文名 |
| `country` | TEXT | 默认 US |
| `city` | TEXT | 城市 |
| `us_news` / `qs_rank` | INT | 排名（可空） |

### `cds_records` — CDS 年度快照（核心）
| 字段 | 说明 |
|:--|:--|
| `univ_slug` + `cds_year` | **唯一键**，同一校同年只一行（重跑覆盖） |
| `applied` / `admitted` / `enrolled` | C1 三人数 |
| `admission_rate` | 录取率 %（= admitted / applied） |
| `sat_ebrw_25` / `sat_ebrw_75` | SAT 阅读写作 25/75 分位 |
| `sat_math_25` / `sat_math_75` | SAT 数学 25/75 分位 |
| `act_25` / `act_75` | ACT 综合 25/75 分位 |
| `ed_deadline` / `ea_deadline` / `rd_deadline` | 截止日期 |
| `tuition` / `room_board` | 学费 / 食宿（美元） |
| `quality` | **整行质量**：`ok` / `partial` / `unparsed` |
| `quality_note` | 分区块质量 JSON，如 `{"c1":"ok","c9":"ok","c7":"suspicious"}` |
| `source_url` / `parsed_at` | 来源与解析时间（可溯源） |

### `cds_factors` — C7 录取因素重视度（官方）
| 字段 | 说明 |
|:--|:--|
| `univ_slug` + `cds_year` + `factor` | 唯一键 |
| `factor` | 19 个因素之一：`rigor` `gpa` `test_scores` `essay` `recommendation` `extracurricular` `talent` `character` … |
| `importance` | `very_important` / `important` / `considered` / `not_considered` |
| `quality` | `ok` 才可用于权重计算 |

### `cds_sources` — 采集台账
`slug` / `url` / `last_status` / `last_error` / `updated_at` —— 每个学校最后一次抓取结果。

---

## 3. ⚠️ 质量标记怎么用（最重要的一条）

| 标记 | 含义 | 产品侧动作 |
|:--|:--|:--|
| `ok` | 解析可信 | **可直接用于评分/展示** |
| `suspicious` | 结构完整但取值异常 | 展示但标注「待复核」，**不进模型** |
| `partial` | 部分区块缺失 | 只用 `ok` 的区块，其余留空 |
| `unparsed` | 没解析出来 | **必须当作「无数据」，绝不可当作 0** |

> 例：Caltech 的 C9（标化）是 `unparsed` —— 若当 0 处理，会把学校算成「标化极低」，结论完全相反。

每条记录还带 `quality_note`（分区块），支持更细粒度判断：

```json
{"c1": "ok", "c9": "unparsed", "c7": "unparsed"}
```

---

## 4. 怎么读

### SQLite
```python
import sqlite3
conn = sqlite3.connect("/root/shared/offerpath/college.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("""
    SELECT slug, name_cn, admission_rate, sat_math_75, act_75, quality
    FROM universities u JOIN cds_records r ON r.univ_slug = u.slug
    WHERE r.quality = 'ok'
""").fetchall()
```

### 命令行
```bash
sqlite3 -header -column /root/shared/offerpath/college.db \
  "SELECT univ_slug, cds_year, admission_rate, quality FROM cds_records ORDER BY admission_rate;"
```

### 完整性与版本
```bash
python3 /root/shared/offerpath/check.py        # 校验和 + 行数 + manifest 比对
```

### 导入 Postgres（云策现有库）
```bash
psql -d offerpath -c "\copy cds_records FROM 'exports/cds_records.csv' CSV HEADER"
```
> 建议在云策库里新建 `cds_records` / `cds_factors` 两张表，**不改动现有 `universities`**，
> 用 `slug` 做映射，避免破坏已上线的 MVP。

---

## 5. 刷新机制

- **谁生成**：六六（`python3 /root/joe-growth/scripts/publish_dataset.py`）
- **何时**：新增/修正学校后立即重发；建议每次发版前跑一次
- **幂等**：`UNIQUE(univ_slug, cds_year)`，重跑覆盖不重复
- **版本**：`manifest.json.version`（`YYYYMMDD.HHMM`）+ `college.db` 的 sha256
- **变更通告**：`manifest.json.schools[]` 里能看到每校当前质量与备注

---

## 6. 当前覆盖（4 校）

| slug | 录取率 | 质量 | 说明 |
|:--|--:|:--|:--|
| stanford | 3.61% | **ok** | C1/C9/C7 全绿，可直接用 |
| harvard | 4.18% | partial | C7 标 suspicious，待复核 |
| mit | 4.55% | partial | HTML 版，C7 抓不到 |
| caltech | 2.57% | partial | PDF 编码损坏，C9/C7 unparsed |

> 覆盖率正在扩（目标 124 校）。每次扩充会更新 `manifest.json`，云策按文件 mtime 判断即可。

---

## 7. 不要做的事

1. ❌ 不要把 `unparsed` 当 0 参与计算
2. ❌ 不要直接写这个目录（需要新字段/新表 → 找六六改 schema）
3. ❌ 不要用中文名做 join 键（有重名风险，用 `slug`）
4. ❌ 不要缓存超过一个版本（以 `manifest.json.version` 为准）
