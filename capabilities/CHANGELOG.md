# 📜 能力包升级日志

## v1.1 — 2026-09-30
**新增两项机制**（家主指令："研究分析的数据每次都存档归纳好" + "每轮备份所有东西并推送知识库"）

- 🔬 **研究归档域** `research/`：规范（4 段式 + 来源必标 + confidence）+ 机器可读索引 `_index.json` + 首份报告（OfferPath 数据勘察）
- 📚 **知识库备份机制** `scripts/backup_kb.sh`：① 本地全量快照（tar.gz，保留 20 份）② 脱敏知识库层推送（STATE 快照 + 12 专属技能 + README）→ main & gh-pages
- ⚠️ **隐私边界**：`joe-growth` 为 public 仓库 → 敏感内容（token/手机号/邮箱/chatID）一律脱敏后推送；**全量备份待私有仓库**
- 🛡️ 教训入库：不要把含凭据的 remote URL 直接打印（本轮勘察时误打印 2 个 token，已建议轮换）

## v1.0 — 2026-09-30
**首版封装**（由家主指令："把各方面能力合理封装成能力/技能包，可复用、可持续升级"）

- 建立 4 层能力架构：交付层 / 能力层（9 域）/ 数据层 / 规则层
- 新增 `capability_index.json`（机器可读索引，9 域 × 技能/资产/触发词/验证/交付）
- 新增 `PACKAGING-STANDARD.md`（封装规范 8 必备字段 + 升级检查清单 + 反例库）
- 新增技能 `joe-capability-pack`（能力包入口，含复用与升级协议）
- 收录现状：11 个 joe 专属技能 + 2 个 OfferPath 技能 + 通用能力（日历/文档/OCR/多模态/子Agent）
- 登记约束：用户自有技能（created_by=None）不可由后台 curator 修改 → 需 `hermes curator adopt` 或新建伞级技能

### 同日并入的能力变更
- 🎓 升学域新建（`admissions/` 9 文件 + `joe-admissions` 技能）→ 补齐升学能力缺口
- 🎯 托福域：成绩落档（MyBest 4.0/6）+ 老师名更正（Vincent）+ 课程排定（每周日 20:30-22:30）
