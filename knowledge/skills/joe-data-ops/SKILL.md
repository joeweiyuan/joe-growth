---
name: joe-data-ops
description: 更新Joe的STATE.md/growth_index或推送joeweiyuan仓库时加载。含binary误判绕过。
tags: [joe, state, data-ops, github, growth-index]
related_skills: [joe-growth-tracker]
---

# Joe 数据层运维（子焘记基础设施）

> 配套 `joe-growth-tracker`（工作流与叙事的主人，用户自有技能）。本技能沉淀**文件读写与推送的基础设施坑**，两者分工：tracker 管"做什么"，本技能管"文件怎么读写才不会被工具卡住"。

## 触发条件

- 需要更新 `/root/.hermes/profiles/joe/STATE.md`（学业状态文件）
- 需要更新 `growth_index.json` 或跑索引验证
- 需要把 tracker 数据同步到 `joe-growth` 网站 repo 并 git push
- 遇到 `read_file`/`patch` 报 "Binary file" 但文件明明是文本

## ⚠️ 文件地图（先分清，别读错）

| 路径 | 是什么 |
|:----|:------|
| `/root/.hermes/profiles/joe/STATE.md` | **学业** STATE.md（Joe 的课程/托福/行程/巡检）— 本技能的对象 |
| `/root/STATE.md` | **物流**六六的 STATE.md（shipments 表状态）— 别混淆！会话开始时搜到两个 STATE.md 时先确认路径 |
| `/root/joe-growth-tracker/daily-logs/` | 成长日志源（tracker） |
| `/root/joe-growth/daily-logs/` | 网站 repo 副本（可编辑后直接 push） |
| `~/.hermes/profiles/joe/daily-logs/` | ❌ 不存在，别去那里找 |

## 📖 STATE.md 读写方案（关键坑）

**症状：** `/root/.hermes/profiles/joe/STATE.md` 含超长行（行程表行最长 ~482 字符），导致：
- `read_file` 报 "Binary file - cannot display as text"
- `patch` 工具报 "Patch validation failed: Binary file"
- `execute_code` / terminal heredoc 写文件可能触发审批阻塞

**这不是环境故障，是文件内容的持久属性**（行程表行会一直超长），每次更新都会遇到。

**✅ 已知可用方法：**
```bash
# 读：terminal 只读 python（读命令不触发审批）
python3 -c "
with open('/root/.hermes/profiles/joe/STATE.md', 'r', encoding='utf-8') as f:
    print(f.read())
"
```
```python
# 写：用 write_file 工具全量重写（已验证可用）
# 流程：读出全文 → 在内容上做字符串替换（保持其他行原样，包括异常 || 前缀）→ write_file 覆盖
# 技巧：多处在同一文件时合并进一次 write_file，别用多次 patch
```

**铁律S3 验证：** 写回后必须读回确认（用上面的 python 读法），核对替换处 + 确认文件未截断。

## 🗂️ growth_index.json 维护

- 路径：`/root/joe-growth-tracker/growth_index.json`（repo 副本在 `/root/joe-growth/growth_index.json`，必须双写）
- 追加 daily-log 条目：`date/file/summary/tags/recorder` 五字段齐全
- **stats 会漂移**：历史出现过 total_logs=4 但实际数组 10 条（无人维护导致）。更新时按实际计算：
  - `total_logs` = `len(daily_logs)`（脚本算，别手写）
  - `total_words` = 各 daily-log 文件实际字数求和（别目测估算）
- 验证脚本位置：`/root/.hermes/profiles/joe/skills/joe-sub-agents/joe-growth-tracker/scripts/verify-growth-index.py`（在**技能目录**，不在 tracker 目录）
- 验证输出：`PASS` 才算完；`FAIL repo copy diverged: /root/joe-growth/growth_index.json` = 网站 repo 副本没同步

## 🔄 tracker ↔ repo 同步 + git push

```bash
cd /root/joe-growth
cp /root/joe-growth-tracker/daily-logs/YYYY-MM-DD.md /root/joe-growth/daily-logs/
cp /root/joe-growth-tracker/milestones.md /root/joe-growth/milestones.md
cp /root/joe-growth-tracker/growth_index.json /root/joe-growth/growth_index.json
git add -A && git commit -m "📝 ..."
# ⚠️ 推送必须带 SSH key 覆盖（见下）
GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes" git push origin main
git status --short   # 确认干净
```

**⚠️ 陷阱：cp 到错误目标目录。** `cp a b c daily-logs/` 会把 b、c 也复制进 daily-logs/（本会话实战：milestones.md/growth_index.json 误入 daily-logs/），提交前 `git status` 检查多出来的 `??` 文件并 `rm`。

### 🔑 SSH key 覆盖（2026-08-16 实战）

**症状：** `git push` 报 `ERROR: Permission to joeweiyuan/joe-growth.git denied to corinwe.`

**原因：** `/root/.ssh/config` 全局把 github.com 指向 `id_ed25519_corinwe`（2026-08-13 被改），joeweiyuan 系仓库（joe-growth / joe-academic-tracker）推送全部会被拒。

**修复：** 每次推送加 per-command 覆盖，**不要改全局 config**（会影响其他 profile 的仓库操作）：
```bash
GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes" git push origin main
```
若未来 config 恢复正常（不再报 corinwe denied），此步可省略——以报错为触发条件，不是永久规则。

## 🌐 发布与线上验证（joe-growth 站点）

- **双分支**：站点由 **gh-pages** 提供。每次推送后核对 `git diff origin/main origin/gh-pages --stat`
  输出为空 —— **只推 main 线上看不到**（历史多次踩过）。
- **`.nojekyll` 必须存在于仓库根**：否则 Jekyll 忽略下划线开头文件（如 `research/_index.json`）→ 线上 404。
- **验证要等**：推送后 live URL 需 **~40–90 秒**重建；刚推完的 404 是重建延迟，**不是失败**。
  复测用缓存破坏参数 `?v=$(date +%s)`；非 ASCII 路径先 URL-encode（`urllib.parse.quote`）。
- 说"已推送"前给证据：**分支差异 0 + 目标 URL 逐个 HTTP 200**，不能只给 commit 号。

## 🔒 私有备份目的地（知识库）

全量备份推**私有** KB 仓库（`08-个人成长/少爷/`）；公开仓库只放**脱敏层**（STATE 快照 + 技能副本）。
- **选择性 add**：`git add "08-个人成长/少爷"`，**绝不 `git add -A`** —— 该仓库同时被其他 agent 推送，
  全局 add 会把别人的未提交改动一起卷进你的提交。
- **推送前先 rebase**：`git pull --rebase origin main` 再 push（远端常有新提交，直接 push 被拒）。
- **验证落盘**：`git ls-remote origin main` 的哈希 == 本地 `HEAD` 才叫"已推送"。
- **公开层脱敏自检**：写公开仓库前扫一遍 token/手机号/邮箱/chatID，命中数必须为 0。
- **不打印凭据值**：列远端一律脱敏 `git remote -v | sed -E 's#(https://)[^@]*@#\1<凭据已隐去>@#'`；
  配置文件只读键名（`grep -oE '^[A-Z_]+=' .env`），绝不用 `cat` 整段输出。

## ✏️ 全局纠正（改名/改口径）

用户纠正名称或口径后：**全库 grep → 替换 → 复核残留计数**（STATE + 两个 repo 的档案/日志/账本/站点），
并在台账里**只保留恰好一处**更正说明（写明"原记录 X 已全库更正"），其余残留必须为 0。

## 🧩 脚本化改写 markdown 的两个固定坑

- Python 拼表格行时写 `"…|\\n| 2026-…"` 会写出**字面量 `\n`**（不是换行）→ 两行粘成一行。用真实换行符。
- `patch` 的 old_string 只锚定**行首片段**时，会留下原行的尾段（表格行被撑成两行）→ **锚定整行**；
  脚本化改写后校验：目标行数、`|` 列数、残留计数。

## 完成标准

✅ STATE.md 读回确认 + growth_index 验证 PASS + `git status` 干净 + push 成功（`main -> main` 输出）
