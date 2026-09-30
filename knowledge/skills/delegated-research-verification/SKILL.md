---
name: delegated-research-verification
description: Use when 派发子Agent做多目标调研/核实并产出可追溯结论（派发—核验—归一化—Checker—归档—发布）。
category: joe-sub-agents
tags: [delegation, research, verification, maker-checker, evidence]
---

# 多子Agent 研究/核实流水线

> 用途：把「一批目标（学校/竞赛/机构/路径）」的调研核实做成**可追溯产出**，而不是一堆零散结论。
> 适用：升学核实、竞赛/项目调研、机构对比、政策查证——任何「多目标 × 多字段」的并行调研。
> 配套：`joe-task-dispatch`（派发模板）、`maker-checker-workflow`、`termination-condition`

## 触发条件
- 需要同时核实 **≥4 个对象**，每个对象 **≥3 个字段**
- 结论要被拿去决策 → 必须**官方第一手 + 可追溯来源**
- 已有产出（规划/报告/方案）需要独立复核

## 六步流水线

### 1️⃣ 派发（`delegate_task`，≤3 并行）
- **每个子Agent只放 2-3 个对象**：4 个对象 + 网页深挖实测撞 **600s 超时**；拆成 2 个后 84s 完成。
- context 必须带全：目标+终止条件 / 质量标准 / 输出格式 / 工作流，外加三条硬约束：
  1. **官方来源优先**（直接列官方域名），第三方一律标注来源性质
  2. **每字段附来源 URL**；拿不到 → 写 `"待核实（原因）"`，**禁止编造**
  3. **节奏控制**：单对象预算 60-70s；页面超时**跳过该字段标"待核实（页面超时）"，不要重试死等**
  > 不写第 3 条，子Agent会在单个卡死的页面上耗尽整个超时预算。
- 产物落到**固定路径**：`/tmp/research_<topic>.json`（明确 schema）+ 中文 Markdown 摘要（限行数）。
- 要求子Agent标注来源性质三分类：`官方可证` / `媒体报道/第三方` / `个案自述`。

### 2️⃣ 核验产出（**不要相信子Agent的自我总结**）
子Agent说"已完成、JSON 校验通过"，而文件不存在/结构不符，是常见情况。逐项验：
```python
for p in outputs:
    assert os.path.exists(p), p
    d = json.load(open(p, encoding="utf-8"))   # 必须能解析
    # 再抽查关键字段非空（不是 None/空列表）
```

### 3️⃣ 归一化（异构 schema）
同一份 schema 指令下，不同子Agent仍会产出不同结构 → 必须先归一化再入库（配方见 `references/json-normalization-recipe.md`）：
- `schools` 可能是 `list[dict]` / **`dict`（键=对象名）** / `list[str]` → **三种都要兼容**
- 键别名：`school`|`name`|`university`；`source`|`source_url`|`source_secondary`；`status`+`detail`|`value`
- 关键词映射表**按最具体优先排序**——否则 `UNSW Sydney` 会被 `SYDNEY` 抢先命中，对象静默丢失
- 同义字段合并展示（如 `english_proficiency` 与 `test_policy`）
- 写库后**必须回读计数**（`入档 N/M`）；缺项打印出来，不静默通过

### 4️⃣ Checker（Maker/Checker 分离，**必做**）
另派**独立**子Agent审计（不是自己复查自己）。审计提示词与判定 schema 见 `references/checker-audit-checklist.md`。
它稳定抓到的错误类别：
- 🔴 **计划层面的硬冲突**（例：两所私立校的 REA/EA 单选限制 → "同日双申"根本不可行）
- ⚠️ **强度被夸大**（官方 `强烈建议` 被写成 `必须`；`未公布` 被写成具体数值）
- ⚠️ **无来源基准被当官方门槛**（第三方招募/机构基准 → 必须标"经验值"）
- ⚠️ **过简推算**（两点线性外推忽略倒退/训练量/生理非线性 → 改成区间 + 标"经验外推"）
- ⚠️ **URL 假有效**（HTTP 200 只证明域名可通，≠ 仍受理/仍绑该项目）

### 5️⃣ 归档（每次研究必做）
- 报告 → `research/YYYY-MM-DD_<主题>.md`，四段式：①研究问题 ②来源(URL/路径) ③结论 ④**可复用维度**
- 原始 JSON → `research/raw/`（可复现性）
- 登记 `research/_index.json`：来源 / 关键结论 / 可复用维度 / 审计摘要

### 6️⃣ 发布与验证
- public 站（`joeweiyuan/joe-growth`）只放**脱敏**内容；全量原文进**私有 KB**（`corinwe/weiwuji-knowledge-base` → `08-个人成长/少爷/`）
- KB 仓推送纪律：**只 `git add "08-个人成长/少爷"`**，永不 `git add -A`；远端有新提交先 `git pull --rebase`
- 推送后必测：① 分支一致性 `git diff origin/main origin/gh-pages --stat | wc -l` == **0** ② 线上 URL **200**
- **Pages 有 45-60 秒重建延迟** → 刚推完 404/旧内容属正常，等一轮再测再下结论
- 目录级 URL 没有 `index.html` 会 **404** → 要可浏览就补索引页并在主页导航加入口
- `.nojekyll` 缺失时 Jekyll 会忽略下划线开头的文件（如 `_index.json`）
- 用户要"一页图/一页路线图"时：**本地 HTML 渲染成高清 PNG**（不要用图像模型，中文小字会糊）→ 配方见 `references/one-pager-rendering.md`

## 支持文件
- `references/json-normalization-recipe.md` — 异构 JSON 归一化配方（三种顶层结构 / 键别名表 / 映射顺序）
- `references/checker-audit-checklist.md` — Checker 审计提示词骨架 + 判定 schema + 五类稳定命中的错误
- `references/one-pager-rendering.md` — 一页路线图渲染配方 + 内容骨架 + 尺寸核验

## 铁律
1. **兄弟产出必须自己核验** —— 子Agent的 summary 是自报，不是事实
2. 任何"百分比/权重/门槛"没有官方来源 → 标"经验值/无官方依据"，**绝不倒推成官方口径**
3. 案例反推必须声明边界：**无落选对照组 → 不能推因果/权重**（幸存者偏差），并列出"推不出来的"
4. 官方拿不到就写"官网未公布" —— 比编一个数字有价值得多
5. 归档 + 索引 + 原始数据齐了，产出才可复用（本 profile 明确要求供 OfferPath 参考）

## 反例库
- 4 对象/子Agent → 600s 超时白跑一轮；拆 2 对象/子Agent + 节奏预算后 84s 完成
- 子Agent用 `name` 而非约定的 `school`、把 `schools` 写成 dict → 归一化脚本崩（`'str' object has no attribute 'get'`）
- 手写百分号编码 URL 出错 → 用 `urllib.parse.quote` 程序化生成 + 脚本校验全部链接存在
- 生成中文文档的脚本里：HTML 里混 Markdown `**` 不生效、Python 字符串内嵌套双引号会语法错（用「」）、表格单元格里写进字面量 `\n`
