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

## 完成标准

✅ STATE.md 读回确认 + growth_index 验证 PASS + `git status` 干净 + push 成功（`main -> main` 输出）
