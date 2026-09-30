---
name: toefl-mock-exam-analysis
description: 模考成绩分析 — 双评分源对照、门户数据提取、沉淀成长路径。收到模考PDF/链接时用。
category: joe-sub-agents
tags: [toefl, mock-exam, analysis, joe]
---

# 托福模考成绩分析（双评分源工作流）

专为Joe（魏源）托福模考反馈设计的分析工作流。2026-08-16模考首次确立。

## 触发条件
- 用户发来模考成绩PDF / 机构门户链接（如"8/16托福全科模考反馈"）
- 首考（8/22）后复盘成绩
- 任何需要"模考分数 → 成长记录"的沉淀

## ⚠️ 核心原则：双评分源对照，禁止只信一套

培训机构通常有**两套评分**，差异可能很大：

| 来源 | 形态 | 特点 |
|------|------|------|
| 老师人工评分 | PDF/纸质反馈 | 综合表现评估，一般偏宽松 |
| 系统机评 | 门户 tporesult 网页 | 答题正确率+机器判分，**与真实考场最接近** |

**2026-08-16 实测差异（关键参考）：**
- 听力 4.5 vs 4.5 ✅ 一致 ｜ 阅读 4 vs 4 ✅ 一致
- 写作 4-4.5 vs **3.5** ⚠️ 系统偏低
- 口语 4 vs **2** 🔴 差2分，差距最大

**处理规则：**
1. 两套分都要留档，不二选一
2. 最终以老师分为主、系统分为对照
3. 系统口语分显著低于老师分 → 标注"机评风险大，真实考场（机评）是最大变量"⚠️
4. 所有数字必须能从PDF原文或门户页面追溯，禁止凭记忆补数字（铁律S1）

## 工作流（8步）

1. **提取PDF文本**：`pdftotext -layout "file.pdf" -`；失败用 python pypdf fallback。注意 read_file 可能把PDF识别为binary报错，用 terminal 处理
2. **读 STATE.md** 对照基线（如年初3.5 → 目标4.5）
3. **抓门户**（用户给链接时）：browser_navigate + browser_snapshot（动态页面等渲染）
   - 抓取：CEFR总评/折算分 → 分科成绩+等级 → 逐题型正确率表 → 知识点稳定度表 → Top High Errors → Analysis逐题（可选）
4. **交叉分析**：强项 / 🔴重灾区 / 方法问题vs词汇问题 → 冲刺优先级
5. **存原始参考文档**：`reports/YYYY-MM-DD_托福模考_系统原始数据参考.md` + 复制到 `/root/joe-growth-tracker/references/`
6. **更新 STATE.md**：当前水平列（双口径）+ 关键数据区（附参考文档路径），patch后grep读回验证
7. **创建成长日志**：`joe-growth/daily-logs/YYYY-MM-DD.md`（同步到 `joe-growth-tracker/daily-logs/`）→ git push main（用 `GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_github -o IdentitiesOnly=yes"`，见memory SSH陷阱）
8. **交付**：分析文档+冲刺打卡表（reports/），飞书回复附 `MEDIA:<path>`

## 门户页面结构（chaoxixuezhang.cn tporesult.html）

完整字段说明 → `references/mock-exam-portal-data.md`

关键区块：
- **总评**：CEFR（如 3.5/6、B1）+ 折算分（65/120）+ 正确/错误数（听37/10、读32/18）
- **逐题型正确率表**：找<50%的🔴重灾区（如学术阅读10%、听力学术讲座2仅38%）
- **知识点稳定度表**：Easily Confused（0%）=硬伤；Relatively Stable（70%+）=强项
- **Top High Errors**：方法问题 vs 词汇问题的判断证据
- Comment标签通常无内容（"The teacher has not added comments~"），教师点评以PDF为准

## 分析框架（2026-08-16实例）

- **强项识别**：听答选择93%、听力推断86%、完成句子100% → 能力已达标，保持手感
- **重灾区**：学术阅读10%（1/9）、听力学术讲座2 38% → 学术词汇+长难句瓶颈
- **方法问题 > 词汇问题**（阅读Top Errors典型模式）：忽略not/only/except限定词、回文找错位置只凭关键词、凭印象作答不回文 → **方法问题4天可练，比背单词见效快**，冲刺策略优先技巧训练
- **双口径解读**：老师4.2 vs 系统3.5 → "真实成绩大概率介于两者之间"，冲4.5需啃硬骨头而非靠感觉

## 陷阱
- ❌ 只信老师分（PDF）不看系统分 — 真实考场是机评，口语会被系统压分
- ❌ 把"口语4分"当安全区 — 系统2分才是考场风险视角
- ❌ 门户链接用 read_file/curl 直接读 — 动态页面必须 browser_navigate 等JS渲染
- ❌ 只更新STATE.md不建日志/不推GitHub — 沉淀必须全链路（文档+STATE+日志+推送）
- ❌ 忘记附MEDIA路径 — 飞书用户需要文件本身

## 参考文件
- `references/mock-exam-portal-data.md` — 门户页面结构详解 + 2026-08-16实例数据快照
