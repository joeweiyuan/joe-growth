---
name: joe-admissions
description: Use when 处理Joe升学申请（选校/时间线/文书/招募）。
category: joe-sub-agents
tags: [joe, admissions, application, recruiting, essay, timeline]
---

# 🎓 Joe 升学模块（Admissions Agent）

> 模块目录：`/root/joe-growth/admissions/`（双副本：`joe-growth/` + `joe-growth-tracker/`）
> 建档 2026-09-30：补齐"升学能力缺口"（此前只有碎片文档，无体系）

## 触发条件
- 家主问及：选校清单、申请时间线、文书素材、体育招募、推荐信、申请季任务、夏校规划
- 标化/活动/奖项需要"转成申请口径"
- 季度检查点（触发词："检查升学时间线"）

## 模块结构（8 文件 + README）
| 文件 | 作用 |
|------|------|
| `00-升学总档.md` | 目标/画像/差距基线（strategy 文档升级版） |
| `01-选校清单.md` | 分层选校 + 招募校 + 要求/DDL 核实表 |
| `02-时间线.md` | 2026Q4→2029 倒排 + 季度检查 |
| `03-标化规划.md` | 托福/SAT 节点与目标 |
| `04-活动与荣誉清单.md` | Common App 口径（Honors/Activities） |
| `05-文书素材库.md` | Story Bank：事件→主题→可用题目 |
| `06-体育招募.md` | 教练联系表/邮件模板/材料清单 |
| `07-推荐信策略.md` | 人选/时间/素材包 |
| `08-申请季看板.md` | 阶段任务与状态 |

## 工作流

### A. 选校调研（新增一所学校）
1. 先查**官方**（校官网 / Common App / CDS）→ 标化政策、DDL、补充文书、赛艇招募流程
2. 结果回填 `01-选校清单.md` 核实表，**每行标来源**
3. 未核实的一律写"待核实"，**禁止编造要求或 DDL**
4. 可引用 OfferPath 数据库（119校/4,709条）做录取画像参考，标注"参考，非官方"

### B. 时间线维护（季度检查）
1. 读 `02-时间线.md` → 逐项对照 STATE.md 实际进展
2. 标记完成/顺延/逾期，更新状态
3. 输出家主简报（≤10 行）

### C. 文书素材提炼
1. 素材源：`daily-logs/`（45篇）、`themes/`、`milestones.md`、`references/why-offerpath-matters-to-joe.md`
2. 写入 `05-文书素材库.md`：事件 / 主题 / 可用题目 / **来源文件**
3. 原则：具体细节 > 形容词；**孩子口吻**（禁止 AI/成人腔）；失败类素材优先

### D. 体育招募
1. 材料：2km 成绩（PB 7:24.1 / 12月目标 7:20.0）、NCAA 简历、比赛视频、成绩单、奖项
2. 教练名单**只能来自官方渠道**（校队官网/招募表），空表待填，**不许编造教练姓名**
3. 邮件模板见 `06-体育招募.md`；发信前需家主确认

## 🔒 铁律（本模块）
1. **学校要求 / DDL / 录取数据必须官方核实**，未核实写"待核实"——不编造
2. 策略建议标注**依据 + 时效性**；重大决策由**家主 + 顾问**拍板
3. 更新后：双副本同步 → 推送 GitHub（main + gh-pages）→ 读回/线上验证
4. 数字来源：GPA→Academic Tracker；标化→STATE.md；奖项→awards.md；赛艇→赛艇总档案

## ⏳ 待家主确认
- 目标校范围（仅 MIT/斯坦福 or 美本 Top20 铺开 or 加英国/香港）
- 顾问（Penny老师/Corin）的角色分工
- 更新节奏（默认季度）

## 相关资产
- 赛艇总档案：`references/rowing-master-profile.md`
- OfferPath 平台：`http://43.162.92.9:3000/`（详见 `offerpath-agents` 技能）
- NCAA 简历：`assets/Rowing_Resume_JoeWei_Filled.docx`
- 原始规划：`strategy-mit-stanford.md`（2026-06-08）
