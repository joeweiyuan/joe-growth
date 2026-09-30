---
name: joe-capability-pack
description: Use when 复用/升级Joe的能力包与技能索引。
category: joe-sub-agents
tags: [joe, capability, index, packaging, upgrade]
---

# 🧩 Joe 能力包（Capability Pack）v1.0

> 定位：Joe 学业成长助手的**能力入口**——把 9 大能力域封装成体系，支持随时复用与持续升级
> 资产目录：`/root/joe-growth/capabilities/`（双副本：`joe-growth/` + `joe-growth-tracker/`）
> 机器可读索引：`capabilities/capability_index.json`

## 触发条件
- 家主问"你有哪些能力/技能""某个能力怎么用"
- 需要**新增能力包**或**升级现有能力**
- 季度能力盘点
- 需要跨能力域协同（如"升学+赛艇+托福"联动）

## 四层架构
```
交付层：飞书家庭群 · 飞书私聊 · 微信 · GitHub Pages · .ics · 文档
能力层（9域）：🎓升学 📚学术 📖托福 🚣赛艇 🏆成长 💰费用 📅日历 🚀OfferPath ⚙️运维
数据层：STATE.md · joe-growth(网站) · joe-growth-tracker(源) · joe-academic-tracker · joe-toefl-tracker · tengtu
规则层：事实优先 · 禁编造 · Maker≠Checker · 终止条件 · 双副本同步
```

## 9 大能力域（技能 → 触发词）
| 域 | 技能 | 触发词 |
|----|------|--------|
| 🎓 升学 | `joe-admissions` | 选校/时间线/文书素材/招募/推荐信/检查升学时间线 |
| 📚 学术 | `joe-academic-report` `academic-report-analysis` | 成绩单/GPA/学期报告 |
| 📖 托福 | `joe-toefl` `toefl-mock-exam-analysis` | 模考/托福成绩/错词/备考/Vincent课 |
| 🚣 赛艇 | （growth 域内） | 训练/比赛/测功仪/招募简历 |
| 🏆 成长 | `joe-growth-tracker` | 记录一天/照片视频/周记/里程碑 |
| 💰 费用 | `joe-expense-bookkeeping` | 记账/学费/累计投入 |
| 📅 日历 | `calendar-schedule` | 排课/日历/提醒 |
| 🚀 OfferPath | `offerpath-agents` `offerpath-verification` | OfferPath/录取数据/创业 |
| ⚙️ 运维 | `joe-data-ops` `joe-academic-state-ops` `maker-checker-workflow` `termination-condition` `joe-task-dispatch` | 更新/推送/验证/派子任务 |

## 工作流

### A. 调用能力（复用）
1. 读 `capabilities/capability_index.json` → 定位域 → 拿到 技能/资产/验证方式
2. 加载对应技能（skill_view）→ 按其 SOP 执行
3. 按其"验证"字段验证，按"交付"字段投递

### B. 新增能力包（封装）
1. 按 `capabilities/PACKAGING-STANDARD.md` 声明 **8 必备字段**（名称/触发词/技能/数据源/工作流/验证/交付/升级记录）
2. 建技能（`skill_manage create`）+ 资产目录（双副本）
3. 登记进 `capability_index.json` + 写 `CHANGELOG.md`
4. 验证清单逐项打勾后推送

### C. 升级现有能力
1. 改内容 → 双副本同步 → push main → merge gh-pages → 线上/读回验证
2. 版本号 + `CHANGELOG.md`；若涉及旧名称/口径 → **全库 grep 残留并同步改**

## 🔒 铁律
1. **禁止编造**：无来源的数字/名称/截止日 → 写"待核实"
2. 双副本必须一致；发布只从 `/root/joe-growth` 推送（`joe-growth-tracker` 无独立 .git，禁 push）
3. 用户自有技能（`created_by=None`：joe-toefl / joe-growth-tracker / offerpath-agents 等）后台 curator 不能改 → `hermes curator adopt <name>` 或新建伞级技能
4. 质量闸门：事实优先 / 禁编造 / Maker≠Checker / 终止条件 / 线上实测

## 反例库（详见 PACKAGING-STANDARD.md）
- tracker 目录 push → 污染物流仓库
- 默认 open() 读写 .ics → 吃掉 CRLF
- 把推测当事实（Penny老师）
- 记账重复计（半年费含在年费内）
- 只改一处就交差 → 必须全库同步
