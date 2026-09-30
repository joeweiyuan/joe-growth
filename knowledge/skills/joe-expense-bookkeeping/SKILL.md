---
name: joe-expense-bookkeeping
description: Use when recording Joe's expenses/ledger or publishing joe-growth content (main + gh-pages).
category: joe-sub-agents
tags: [joe, expense, ledger, accounting, gh-pages]
---

# Joe 培养费用记账 SOP

## 触发
- 家主口述新开支要"记下入账"（学费 / 托福课 / 赛艇费 / 集训 / 机票 …）
- 家主核对"XX月缴的XX费有记录吗"

## 数据链路：改一处必须同步 6 处（否则线上/账本互相矛盾）
| # | 位置 | 要点 |
|:-:|------|------|
| 1 | `expense-ledger.md` | **双副本**：`/root/joe-growth/expense-ledger.md`（权威，有 git）+ `/root/joe-growth-tracker/expense-ledger.md`（源区，**无独立 .git**，用 `cp` 同步） |
| 2 | `/root/joe-growth/data.js` | `expenses.years` 年份金额（页面自动求和）+ 上方注释写算式 |
| 3 | `/root/joe-growth/index.html` | **支出页明细是静态 HTML**：手改明细行 + `expense-year-YYYY` + `expense-grand-total` + `stat-expense-total` + `badge-expense-total` |
| 4 | `daily-logs/YYYY-MM-DD.md` | 双副本（growth + tracker） |
| 5 | `STATE.md` 巡检记录 | 追加一行台账（时间/事项/结果/操作，含 commit 号）——补账但无法追溯来源是记账事故 |
| 6 | 推送 | `main` **和** `gh-pages`——**线上站点读 gh-pages**，只推 main 线上不变 |

推送（注意 SSH 专用 key）：
```bash
cd /root/joe-growth
GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes" git push origin main
git checkout gh-pages && git merge main --no-edit -m "同步部署" && \
  GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes" git push origin gh-pages
git checkout main
```

## 入账前必做：防重复计费三步
1. **查重**：读账本 + `git log -S"<金额>"` + `grep -rn 关键词 daily-logs/` + `session_search` → 该笔是否已记？与已有条目是否重叠？
2. **定口径**：金额含糊（家主常说"2万3左右"）→ 记录时写明口径；口径不明时**先按"不重复计"入账 + 账本备注标注待确认**，并在回复中请家主确认（宁可少记，不可重复记）
3. **回报**：明确告知"已记/未记"+ 凭据（文件名+日期+来源），不要凭记忆回答

## 已确认口径（勿重复计）
- **赛艇年费 ¥100,000 = 家付两个半年 × ¥40,000（¥8万）+ 学校补贴 ¥20,000**；每学期续的 ¥40,000 **已含在内**，不得另加；**学校补贴不单列**（账本仍按 ¥100,000 记）
- 学费按学年记（如 2026-2027 10年级 ¥300,000）；**缴纳月份**家主未说则不臆造，先问
- **托福 4-8月分两笔**：4月第一次 `¥18,000+` / 7月底补款 `¥7,000+`，合计约 `¥25,000`（含8月集训、不单列）；此前记的「4-7月 ¥24,000」估算与单笔 ¥23,000 **均已撤销**
- **近似值写法**：家主说「18000多」「2万3左右」→ 账本写 `¥18,000+` / `约¥25,000`，**不得凑成精确数**（铁律S1）；回复中主动提出"要精确请给确数"

## 验证（铁律S3，做完必须验）
1. python 复算：年份数组求和 → 与页面显示 `¥x万+`（= floor(total/10000)）一致
2. `diff` 两副本账本必须完全一致
3. 线上实测：`curl -s https://joeweiyuan.github.io/joe-growth/index.html | grep -o "¥x万+\|金额"`（CDN 约 30-60s 生效）

## 陷阱
- **会话可能跨日**：入账日期以实时 `date` 为准，勿沿用上一条消息的日期（曾把 9/13 记成 9/11）；**已写错的日期要回改全部产物**（账本行/说明、`git mv` 日志文件名、STATE 台账）并重新推送两个分支——错日期留在线上等于数据不实
- `/root/joe-growth-tracker` **无独立 .git**，在其目录跑 git 会上溯到 /root 的物流仓库 → 只 `cp` 同步，绝不从该目录 commit/push
- `gh-pages` 可能长期落后 main（历史欠账）→ 用 `git merge main` 合并（保留 gh-pages 独有提交，勿强推覆盖）
- 页面明细行原可能少列项目（总额含但可见行缺）→ 顺手补齐使"页内加总 == 总额"
- **批量改账本/HTML 用带断言的脚本**：写 `/tmp/*.py`，每处替换断言 `count==1`（未唯一命中立即中止），改完再 `grep` 残留旧数字（如 `grep -c "703,452\|¥337万"` 应为 0）；**不要用无断言的 `sed -i` 批量替换**
- 临时脚本/中转文件写 `/tmp` 或仓库内；**不要写 `/root/.hermes/` 根目录**（受保护路径，触发人工审批，无人应答即失败）
- 数值口径未定就先按「不重复计」入账并在账本 `## 📝 说明` 标注「待确认（影响总额）」；家主确认后把该条改成 ✅ 已确认，别让旧标注留在账本里
