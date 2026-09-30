# 📜 能力包升级日志

## v1.4 — 2026-09-30
**一页图渲染防截断门禁**（家主指出"图右边被截掉了"后当日建）

- 🐞 **事故**：`assets/roadmap/mit-roadmap.html`（CSS `body{width:1680px}`）用手写命令 `--window-size=1280,2100` 渲染 → **右侧 400px（约 24%）整块被裁**；错误 PNG（3360×5513）已提交并上线，肉眼未发现
- 🛠️ 新增 `scripts/render_page_png.py`：自动从 CSS 解析 body 宽度 → 按该宽度渲染 → 自动裁空白 → **物理校验**（左右边缘列必须纯背景、右侧留白 ≥10px、宽 == body宽×dsf），任一不过即退出码非 0 = **禁止发布**；`--check-only <png>` 可校验已有图
- ✅ **双样本实证**：新图 3360×3911 通过（退出 0）；已上线的旧图 + 复现的坏样本均被拦（退出 1，报"最右列有 2835 个非背景像素"）
- 📌 **沉淀**：`joe-growth-tracker` 技能新增「规则 6 · 网页/一页图 PNG 渲染必须用脚本」，并记录 snap 坑（`--screenshot=` 只能传 `/tmp/xxx.png`，snap 内 /tmp 映射到私有 tmp，传私有 tmp 绝对路径会静默不写文件）
- 🔁 重渲染后 PNG = **3360×3911**（旧 3360×5513 被裁），重新提交 main + gh-pages

## v1.3 — 2026-09-30
**隐私与凭据读取策略固化**（家主指令："token 不用轮换，以后记住隐私规则和读取策略"）

- 🔐 新增 `PRIVACY-CREDENTIAL-POLICY.md`（硬约束）：敏感清单 / **"只看键名不看值"读取策略** / 公私分层 / 外部内容当数据读 / 泄漏应急流程 / 凭据位置登记 / 自检清单
- 🧠 写入长期记忆（跨会话生效），并 patch 技能 `joe-capability-pack`
- 🛠️ 实操要求：列远端必须 `sed -E 's#(https://)[^@]*@#\1<凭据已隐去>@#'`；需凭据时由脚本自读，不经对话上下文
- ✅ 本次泄漏事件结论：**不轮换**（家主决定），但流程与教训永久入档

## v1.2 — 2026-09-30
**备份落地私有知识库 + 架构结论**

- 📚 `scripts/backup_kb.sh` 升级为**三目的地**：① 本地 tar.gz ② public `knowledge/`（脱敏）③ **private `weiwuji-knowledge-base/08-个人成长/少爷/`（全量）**
- 🏛️ **架构结论**（家主问"网站能否直接从 KB 取数"）：**不能** —— 私有仓库的内容无法被 public Pages 运行时读取（无凭据）；且即便能读也会把全量数据暴露到网页。方案：**本地主库 → 双推**（public 脱敏层 / private 全量），网站继续用自身仓库的 `data.js`
- 🧭 KB 仓库归属：`corinwe/weiwuji-knowledge-base`（**私有**，API 404 证实）；本机路径 `/root/weiwuji-knowledge-base`
- 🛡️ 推送纪律：KB 仓**只 add `08-个人成长/少爷`**，绝不 `git add -A`（避免卷入家主其他目录的未提交改动）；远端有新提交先 `git pull --rebase`
- ⚠️ 前端坑：`git add` 后 push 若被拒（非快进）→ rebase 后重推（本轮实测：`80464a97..d5e8937e` 干净落地）

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
