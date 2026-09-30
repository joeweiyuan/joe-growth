---
name: joe-academic-state-ops
description: 更新STATE.md内容/托福模考数据累计/大考冲刺清单时加载。curator可编辑扩展层。
category: joe-sub-agents
tags: [joe, state, toefl, mock, checklist, curator-managed]
---

# Joe 学业状态数据运维（curator 可编辑扩展层）

> 本技能是 **joe-data-ops**（STATE.md 读写/推送基础设施）与 **toefl-mock-exam-analysis**（模考分析 8 步工作流）的 curator 可编辑配套层。那两个技能为用户自有（created_by=None，后台 curator 无法 patch），本技能沉淀它们的**实战补充**：
> - joe-data-ops → 文件读写/推送基础设施坑（binary 误判、SSH key、growth_index）
> - toefl-mock-exam-analysis → 模考分析工作流（PDF→门户→双口径→沉淀 8 步）
> - **本技能 → 内容级更新技巧 + 累计数据 + 考前清单模式**

## 触发条件
- 更新 STATE.md 的**内容**（当前水平/关键数据/巡检记录，非基础设施层）
- 第二次及以后的托福模考数据沉淀 / 跨模考对比
- 首考或大考前的冲刺清单生成（最后一次模考结束后）

## 📣 交付口径："记录一下"＝要全家可见就投家庭群

- 家主说"记录一下"／"让全家都能看"时，产出必须投递到飞书家庭群（`hermes send -t feishu:oc_2f8fe87cc6a85a7871d352a3440d3543`，消息内写 `MEDIA:<path>` 即发附件）；**只写本地 STATE/daily-log/文件不算交付**（曾被家主纠正：“你没有记录到飞书日志里面，让我们全家都能看吗？”）。
- 投递后把返回的 `message_id` 写进当天 daily-log 作凭据（可追溯）。
- 日程/日历类产出同时归口 `calendar-schedule`；该技能为用户自有，补规则需先 `hermes curator adopt calendar-schedule`。

## 🗺️ STATE.md 文件定位（2026-09-09 实战）

搜 `STATE.md` 会命中多个同名文件，**Joe 的会话状态文件固定是 `/root/.hermes/profiles/joe/STATE.md`**：
- `/root/STATE.md` = Alice/物流（liuliu）会话状态（在途票/联系人）——**不是 Joe 的**，读错会把物流数据当学业状态
- `/root/tengtu|offerpath-miniapp|jinjian/docs/STATE.md` = 其他项目，无关
- 判断法：任务主体是 Joe → 直接读 `/root/.hermes/profiles/joe/STATE.md`，不要用全盘搜索的第一个命中

## 📸 会议/截图数据入库工作流（2026-09-09 光剑队会实战）

家主常直接甩会议截图（训练计划/出勤表/目标表/成绩单），无文字说明。入库标准流程：

1. **数字二次核对**：先整图 vision_analyze 读全表，再对该学生所在行 zoom 放大核对（vision_analyze region 参数）。两遍一致才入库；不一致以放大结果为准并记录
2. **多口径冲突不吞**：两个来源数字打架（例：教练表7月队测 7:27.2 vs 家庭记录收官PB 7:24.1）→ **两个都记、各自标源**，加 ⚠️待确认并问家主/教练——禁止悄悄二选一
3. **写入三件套**：STATE.md（📊关键数据 bullet + 🕒巡检记录行 + 域 section）→ 域总档案 → 今日 daily-log
4. **域总档案（master dossier）模式**：跨会话复用的域数据建 canonical 档于 `/root/joe-growth-tracker/references/<域>-master-profile.md`，镜像到 `/root/joe-growth/references/`；表内每个数字带「来源」列，头部声明"无源数字禁止入档"。实例：`rowing-master-profile.md`（成绩时间线/赛事/目标/出勤/待确认）
5. **🔴 发布路径红线**：`/root/joe-growth-tracker` **没有独立 .git**——在其目录跑 git 会上溯到 `/root/.git`（= corinwe/liuliu-smart-logistics 物流仓库），commit/push 会污染物流仓库（2026-09-09 实测误提交，`git reset --mixed HEAD~1` 撤销；push 因分支名不匹配被拒未到远端）。**Joe 内容发布只从 `/root/joe-growth`（joeweiyuan/joe-growth，独立 .git）操作**，SSH 用 `GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes"`
6. **推送后验证**：`git ls-remote origin main` 与本地 HEAD 一致才算落地（例：3006595 == 3006595 ✅）

## 💰 家族培养费用记账（expense-ledger 更新）

家主口述费用（"给少爷续了 X 费 Y 元，记下入账"）时按此走。完整命令/校验清单见 `references/expense-ledger-update.md`。

1. **先查重，再入账**：老账本常留「约X万/年」「TBD」的**估算**条目，新实付可能与它重叠（年费估算¥10万 vs 本学期半年费¥4万；托福估算¥2.4万 vs 实付¥2.3万）。**宁可少记，绝不重复记**——按不重复口径入账，把假设写成账本备注 + `⚠️ 待确认` 行 + 回报家主一句可改，别把有重叠风险的数直接累加。
2. **落笔前先 `date` 确认当天**：会话会跨天，凭印象写日期必错（曾把 9/13 记成 9/11，污染账本/日志/提交）。所有带日期的记录（ledger、daily-log、STATE 行、.ics）先跑 `date '+%F %A'`。
3. **四处同步，缺一即漏**：①`expense-ledger.md`**双副本**（`/root/joe-growth-tracker/` 源 + `/root/joe-growth/` 网站副本，不会自动同步→改网站副本后 `cp` 覆盖源）②`data.js` 年份金额（页面自动求和，注释里的算式一并改）③`index.html` 支出页明细行（**静态 HTML，非 data-driven，必须手加行**；页面合计须=行加总，发现历史漏列行顺手补齐）④当日 `daily-logs/`。
4. **发布必须合并到 gh-pages**：网站由 `gh-pages` 分支承载，只推 main 线上不会变 → `git checkout gh-pages && git merge main && git push origin gh-pages`（**merge 不用 reset**：gh-pages 可能有 main 没有的提交），随后 `curl` 线上 URL 复核数字，再切回 main。
5. **只从 `/root/joe-growth` 跑 git**：tracker 目录无 `.git`，命令会上溯污染 `/root` 的物流仓库（见下条红线）。
6. **澄清超时不悬空**：`clarify` 10 分钟无应答时，按不重复口径先入账 + 显式标注假设，等家主回来一句修正即可；不要因为等确认而把"记下入账"的指令搁置。

## 📖 STATE.md 内容级更新 — patch 锚点陷阱（2026-08-21 实战）

**症状：** 巡检记录表（🕒 自动化巡检记录）大量行以相似文本开头（如多行都是"每日托福提醒（冲刺集训）"），直接拿"某一行"做 patch old_string 会命中 3+ 行 → 报 `Found 3 matches for old_string`。

**✅ 解法：old_string 必须拼上行尾之后的唯一锚点（下一节标题）**
```text
old: "| 2026-08-20 | 每日托福提醒（冲刺集训） | ... | 已推送提醒 |\n\n## 🇺🇸 美国名校赛艇夏令营 · 完整行程表"
new: 同一行 + 新增行们 + 原标题
```
新增行插在锚点行之后、标题之前。**下一节的标题是天然唯一锚点**，比行内容可靠。

**另一个坑：** STATE.md 表格行前缀有 `|` 与 `||` 两种（历史遗留），复制 old_string 时保留原样，不要"规范化"。

## 🧪 更新后验证（铁律S3）
- 读回：`grep -n "关键词" STATE.md`，确认**3 处都改到**——当前水平行 / 关键数据区 / 巡检记录
- 数字逐个对照原始来源（PDF / 门户），禁止凭记忆补
- 记忆里若有对应过时数值（如"当前3.5"），同步 replace，防止下次会话引用 stale 数字

## 📊 托福模考双口径数据累计
第二次模考起，把每次模考的双口径（老师分/系统机评）追加进 `references/toefl-dual-source-mock-data.md` 累计库。未来分析直接查累计表看趋势，不用回翻旧会话。当前已入库：8/16、8/19 两次。

## 📋 大考冲刺清单模式（考前夜 + 考试日）
最后一次模考结束后，生成**"考前夜只做N件事 + 考试日三句话"**清单，而不是又一张练习打卡表。原则：
- 考前夜**不做新题**：只看方法笔记 + 避坑清单（聚焦模考暴露的具体错误）
- 每科只写"考场 1 个最高性价比动作"（如：写作写完留 2 分钟自查拼写 = 机评 1 分）
- 附考试物品清单 + 早睡提醒
- 已有实例：`reports/2026-08-21_首考考前夜_行动清单.md`

## 陷阱
- ❌ 拿相似表格行做 patch old_string → 多行命中报错；必须锚定下一节标题
- ❌ STATE.md 更新后不动 memory 里的过时数值 → 下个会话引用 stale 数据
- ❌ 只更新 STATE.md 不建 daily-log / 不推 GitHub — 沉淀必须全链路（文档+STATE+日志+推送）
- ❌ 在 joe-growth-tracker 目录下跑 git commit/push → 上溯到 /root 物流仓库，污染 liuliu；发布一律走 /root/joe-growth
- ❌ 截图数据只 vision 读一遍就入库 → 关键行必须放大二核；两口径冲突只记一个 → 必须双记+标源+待确认
- ❌ 用全盘搜索到的第一个 STATE.md → 可能读到物流状态；Joe 固定 `/root/.hermes/profiles/joe/STATE.md`
- ❌ 记账只改账本一处 → `data.js`/`index.html` 不同步，线上仍是旧总额；`index.html` 明细行是静态 HTML，必须手加
- ❌ 只推 main 不合并 gh-pages → 线上看不到任何更新（gh-pages 才是部署分支）
- ❌ 凭会话印象写日期 → 跨天必错；带日期的记录先 `date`
- ❌ 估算条目与新增实付不查重就累加 → 重复计费（先查重叠、按不重复口径入账并留 ⚠️待确认）

## 参考文件
- `references/toefl-dual-source-mock-data.md` — 托福模考双口径累计数据（8/16 + 8/19）与跨模考趋势解读法
- `references/expense-ledger-update.md` — 家族培养费用记账完整流程（查重口径 / 四处同步 / gh-pages 发布 / 校验清单 / 分类代码）
