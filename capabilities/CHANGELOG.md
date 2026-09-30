# 📜 能力包升级日志

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
