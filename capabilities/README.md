# 🧩 能力包 · Joe 学业成长助手（v1.0）

> 建档：2026-09-30 ｜ 维护：六六（普罗米修斯）｜ 所有者：家主 Corin
> 目的：把能力强项**封装成体系**，做到 **随时复用 + 持续升级**
> 🔗 [Academic Tracker](https://joeweiyuan.github.io/joe-academic-tracker/) ｜ [子焘记](https://joeweiyuan.github.io/joe-growth/)
> 🤖 机器可读索引：`capability_index.json`（供未来会话/cron 直接读取）

---

## 一、能力分层（4 层）

```
┌─ 交付层 ────────────────────────────────────────────┐
│ 飞书家庭群 · 飞书私聊 · 微信 · GitHub Pages · .ics · 文档 │
├─ 能力层（9 大域） ──────────────────────────────────┤
│ 🎓升学  📚学术  📖托福  🚣赛艇  🏆成长叙事          │
│ 💰费用  📅日历  🚀OfferPath  ⚙️运维质量              │
├─ 数据层 ───────────────────────────────────────────┤
│ STATE.md · joe-growth(网站) · joe-growth-tracker(源) │
│ joe-academic-tracker · joe-toefl-tracker · tengtu    │
├─ 规则层 ───────────────────────────────────────────┤
│ 事实优先 · 禁编造 · Maker≠Checker · 终止条件 · 双副本 │
└────────────────────────────────────────────────────┘
```

## 二、9 大能力域（技能 → 资产 → 触发词）

| # | 域 | 技能 | 核心资产 | 触发词（说这些我就调用） |
|:-:|----|------|---------|------------------------|
| 1 | 🎓 升学申请 | `joe-admissions` | `admissions/`（9 文件） | 选校 / 时间线 / 文书素材 / 招募 / 推荐信 / **检查升学时间线** |
| 2 | 📚 学术 GPA | `joe-academic-report` · `academic-report-analysis` | Academic Tracker 站 | 成绩单 / GPA / 学期报告 |
| 3 | 📖 托福标化 | `joe-toefl` · `toefl-mock-exam-analysis` | 词库 6,846 词 · 模考双口径 | 模考 / 托福成绩 / 错词 / 备考 / Vincent 课 |
| 4 | 🚣 赛艇体育 | （growth 域内） | 赛艇总档案 · 训练日历 .ics · NCAA 简历 | 训练 / 比赛 / 测功仪 / 招募简历 |
| 5 | 🏆 成长叙事 | `joe-growth-tracker` | 45+ 日志 · 里程碑 · 奖项 · 主题库 | 记录一天 / 照片视频 / 周记 / 里程碑 |
| 6 | 💰 费用账本 | `joe-expense-bookkeeping` | 双账本 · data.js · 支出页 | 记账 / 学费 / 累计投入 |
| 7 | 📅 日历提醒 | `calendar-schedule` | 2 份 .ics · 4 个 cron | 排课 / 日历 / 提醒 |
| 8 | 🚀 OfferPath | `offerpath-agents` · `offerpath-verification` | 平台 + PG 数据库 | OfferPath / 录取数据 / 创业 |
| 9 | ⚙️ 运维质量 | `joe-data-ops` · `joe-academic-state-ops` · `maker-checker-workflow` · `termination-condition` · `joe-task-dispatch` | STATE.md · 本目录 | 更新 / 推送 / 验证 / 派子任务 |

## 三、如何复用（3 种方式）

1. **说触发词** → 我自动加载对应技能 + 资产
2. **点名能力包** → "用升学包帮我…" / "跑托福包"
3. **机器调用** → 未来会话/cron 读 `capability_index.json`（域→技能→文件→验证→交付）

## 四、如何持续升级（4 步环）

```
变更内容 → 双副本同步(joe-growth + tracker) → push main & gh-pages → 线上/读回验证 → 更新版本号+CHANGELOG
```

- **版本号**：本包 `vX.Y`；每次结构性变更升版并写入 `CHANGELOG.md`
- **新增能力**：按 `PACKAGING-STANDARD.md` 声明必备字段，登记进 `capability_index.json`
- **用户自有技能**（`created_by=None`：joe-toefl / joe-growth-tracker / offerpath-agents 等）：后台 curator **不能自动改**，需 `hermes curator adopt <name>` 后编辑，或新建伞级技能承载新经验（本包即此模式）
- **季度盘点**：每季度检查"新增 / 失效 / 待升级"

## 五、质量闸门（所有能力域共用）

1. **事实优先** — 每个数字可追溯到 STATE / 原件 / 官方来源
2. **禁止编造** — 没有依据就写"待核实/暂无"
3. **Maker ≠ Checker** — 产出者与检查者分离
4. **终止条件** — 先定义可测量的"做完"
5. **双副本 + 线上实测** — 改一处 → 同步所有副本 → 推送 → 实测

## 七、研究归档 & 知识库备份（v1.1）

- 🔬 **研究归档**：`research/`（索引 `_index.json`）。每次研究/分析归档为「问题 + 来源 + 结论 + 可复用维度」，标注 confidence，**供 OfferPath 直接参考**
- 📚 **知识库备份（三目的地）**：`scripts/backup_kb.sh`
  - ① 本地全量 tar.gz → `~/backups/joe/`（保留 20 份）
  - ② **public 脱敏层** → `joe-growth/knowledge/`（STATE 快照 + 12 技能）→ 网站/OfferPath 可公开参考
  - ③ **private 全量** → `corinwe/weiwuji-knowledge-base` → `08-个人成长/少爷/`（STATE 原文 + 能力包 + research + admissions + daily-logs + 技能）
  - ⚠️ 仓库为 public：**禁止推送 token/手机号/邮箱/chatID**（脚本对公开层自动脱敏）
  - 🏛️ **架构结论**：public 网站**不能**从私有 KB 取数 → 走「本地主库 → 双推」；网站数据由自身仓库提供
  - 🛡️ KB 推送只 `git add 08-个人成长/少爷`，远端有新提交先 `git pull --rebase`

## 八、当前缺口（待补）

- ⏳ 招募名单（需官方渠道建）
- ⏳ "美本 Top20"具体名单 + 澳洲"前三"口径（待家主圈定）
- ⏳ 上课提醒（Vincent 课每周日 20:30-22:30）是否需要 cron
