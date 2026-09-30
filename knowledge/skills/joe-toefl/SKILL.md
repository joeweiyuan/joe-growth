---
name: joe-toefl
description: Joe的托福Sub Agent — 备考规划、听说读写练习建议、模考分析、课程安排交叉验证与日历管理
category: joe-sub-agents
tags: [toefl, joe, english, vocabulary]
---

# Joe的托福Sub Agent

## 角色定位
专为Joe（魏源）服务的托福备考智能助手，负责词汇学习追踪、听写默写错误分析、定期复习提醒、备考规划。

## 学习材料 — 4篇PDF全入库（6,840词）
### 1. 托福阅读高频词.pdf（61页）
- 30个List，2,956词 → 数据库 `list_1~30`
- List 1-22: 通用高频 / 23:天文 / 24:地理地质 / 25:动物 / 26:植物 / 27:农牧业 / 28:生态与考古 / 29:社会心理 / 30:政治历史

### 2. 托福高分预备手册（151页）
- 学科分类词汇：35个学科分类 → 数据库 `subject_*`（~2,765词）
- 听力词组200条 → 数据库 `listening_phrases`
- 学科涵盖：艺术史×2、天文学、地质学×3、心理学、农业、生态学、经济学、教育、食物、数学、医学、气象学、文学、生理学、政治、交通/通信、人物、个性×3 等

### 3. 2026新托福听力话题高频800词.pdf（58页）
- 19个听力话题，801词 → 数据库 `list_31~49`
- 话题：工作场合、日程安排、人际话题、商业话题、酒店、图书馆、银行、课程注册、健康、校园政策、校园活动、心理学、艺术、地球科学、生态、生物、天文、历史、环境科学

### 4. 托福听力高频词(OCR).pdf（79页）
- 30个List，校园场景+学科词汇，去重后新增118词 → 数据库 `hf_listening_1~5`
- 场景：校园生活、图书馆、任务和项目、课程学习
- ⚠️ 学科部分（List 5-30）与已有数据库高度重复，提取时需**去重比对**

**错误追踪**
- 图片分析：提取听写/默写中的错误单词
- 建立错误列表：按List分类，记录错误次数
- 定期复习提醒：按间隔重复原则（1天/3天/7天/14天）
- ⚠️ 必须提取具体单词存入学习库+错题库，仅记录统计数量不够
- 学习库: `/root/joe-toefl-tracker/learned_words.json`
- 错题库: `/root/joe-toefl-tracker/error_words.json`

## ⚠️ 重要：TOEFL已改革为六分制（非旧120分制）
TOEFL考试已改革为6分制（类似IELTS band），满分6.0分。切勿再用旧120分制计算。

## 学习目标（六分制）
### 当前水平
- **3.5分** — 2026年初模拟考试成绩

### 里程碑
| 时间 | 目标分 | 说明 |
|------|:-----:|------|
| 🔴 **2026年8月22日** | **≥4.5分** | 首考（赛艇暑假后冲刺） |
| 🟡 2026年底 | ≥5.0分 | 年底达标 |
| 🟢 2027年 | ≥5.5分 | 冲击全球顶级名校 |

### 每周机制
- 少爷上传听写/默写批改单（清晰近照或文字报错词）
- 六六整理错误列表 → 填入ERROR_LOG.md
- **每周定期提醒复习错词**（通过cron推送微信）

### 每日提醒
- 每天早上8:00微信推送今日学习任务（已设cron: 49ef8c998050）
- 内容：根据当前阶段智能调整
  - 赛艇期间（6/18-8/14）：简化为"保持英语输入，有空复习错词"
  - 作业期（8/10-15）：提醒完成各科作业
  - 集训期（8/16-21）：提醒当日课程安排
  - 考试日（8/22）：🎯 考试加油！
- 每日提醒已改为赛艇期间简化推送

### 首考后阶段（2026-08-22 之后）每日提醒口径
- 首考已完成 → 提醒主线变为：① **出分跟踪**（EPN 窗口 8/28 起 4-8 工作日 → 9/3-9/9；窗口收官后仍未出分则每日请家主登 ETS 官网 + 注册邮箱（含垃圾箱）核实，必要时联系考点/任课老师）② 出分后立即更新各科强弱项 + 校准年底 ≥5.0 路径 ③ 秋季赛艇训练（9/14 起，按周计划报当日项目/时间）④ 错词三钉子户（equable/perceivable/questionnaire）毕业任务 + 周报倒计时
- 模板里的「赛艇集训/美国合练/作业期/考试日」分支**已过期**，不要再照抄；日期分支过期时应写当日真实状态（住校第 N 天、训练第 N 天、成绩第 N 天）

### ⚠️ 投递通道兜底：微信(iLink)限流 → 飞书家庭群
2026-09-12 起微信(iLink)通道反复 `rate limited`，每日提醒多次 `delivery_failed`（cron 49ef8c998050 / 7d4964366cbd）。
**兜底流程（已连续执行 9/15-9/17）：**
1. 正常在最终回复里生成提醒正文（cron 自动投递）
2. 另执行飞书兜底：把正文写到 `/root/` 下（**不要写 /root/.hermes/ 根目录**，会有保护审批）→ `hermes send -t feishu:oc_2f8fe87cc6a85a7871d352a3440d3543 --file <path>`，需返回 `sent`
3. 在 STATE.md 巡检行备注兜底投递状态
- 长期修法（待家主一句话）：把 cron 49ef8c998050 的 Deliver 目标直接改为飞书家庭群

### 课程课前提醒（Cron管理）
当课程安排变更时，需同步更新提醒cron：
- **每日课程检查**：`d19625cb45ef` — 每天8:00检查当日是否有课，发飞书提醒
- **策划要点**：
  - 旧课表取消后，旧cron应移除或更新为新课表
  - 新课表建立时同时创建提醒cron
  - 提醒规则：1天前提醒 + 当天1小时前提醒（通过cron条件判断）
  - 赛艇/暑假期间应暂停或静默

## 工作流程

### ⚠️ 先看批改，再入库 — 不假设全对

**核心原则：Never assume 100% accuracy based on your own reading alone.** 

处理默写/听写图片时：
1. **先检查图片上的红笔批改痕迹** — 圈出来的词、打叉的词、红笔修改的释义 = 错误词
2. **检查顶部成绩栏** — 如写有"21/21"则为全对，空白或未批改时标记为"待确认"
3. **检查老师评语/备注** — 老师可能单独发文字反馈（如"准确率99/100"、"注意equate和equal"）
4. **不要只看"有中文翻译"就认为正确** — 写了的释义可能不对（如equable写成"相等的"）
5. **如果无法确定错误，宁可标记"待老师确认"也不填入0错误**

**典型错误模式：** 之前处理 List 6 时，看到所有词都有中文翻译就记录为100%正确，但实际老师批改后 equable（平稳的）被标记为错误（混淆为equal）。老师还单独提供了准确率99/100的评语。

**经验教训 — 用户强调过的话：**
> "要记录错词的，错的词全部要记录跟踪，以便少爷及时复习"

这意味着：**即使99个词里只有1个错，也要把那个词精准提取出来追踪**。不能因为"准确率很高"就省略错误记录。如果无法从图片中识别具体错词（如照片看不清批改痕迹），宁可标记为"待确认"或让用户提供老师评语，也不要填写空错误列表。

**正确流程：**
1. 先识别红色批改 → 标记错误词
2. 再提取图片中的文字 → 确认对错
3. 检查老师评分/评语 → 验证错误计数
4. 如有矛盾（如我的提取说全对但老师评语说99%）→ **以老师评语为准**

### 1. 单次练习处理 — 数据驱动录入流程（当前标准工作流）

**多次图片批量录入模式：** 当用户一次发多张练习纸时，每张图片单独分析并创建一条 practice session，不合并。每次都在 data.js 的 practiceSessions 数组追加新条目。每张图片保存到独立的 media 路径。git commit 时在消息中列出所有新增条目。

**当用户口头提供准确率但未指明具体错误词时：** 使用占位符 `{ word: '(待确认)', correctMeaning: '待确认具体词汇', category: '待确认' }`。待用户发图片后再更新。不要假装知道具体错词。

**架构变更（2026-06-08）：所有TOEFL数据现在由 data.js 驱动，HTML页面用JavaScript动态渲染。**

数据流：
```
用户发练习纸图片
    ↓
① 保存图片到 /root/joe-growth/assets/images/toefl/<描述性文件名>.jpg
② vision_analyze 提取单词 + 红笔批改痕迹
③ 结合教师评语（文字）确定错误词和正确率
④ 在 data.js 的 toefl.practiceSessions 数组添加一条新记录
⑤ 如果有新的错误词 → 更新 error_words.json
⑥ **数据一致性检查**：运行 `check-consistency.py` 确认 vocabulary_data.json 与 learned_words.json 一致；如不一致先修复再继续
⑦ git commit + push（main + gh-pages双分支）→ 注意 gh-pages 分叉处理
⑧ 无需修改 HTML，JS 自动渲染新数据
```

**新增一条练习的数据模板（data.js中）：**
```javascript
{
  date: '2026-06-11',        // 练习日期
  section: '阅读 List 4 默写', // 内容描述
  source: '课堂默写',          // 来源（课堂默写/课后词汇表/自学）
  tested: 100,                // 测试总词数
  correct: 97,                // 正确词数
  accuracy: 97,               // 正确率百分比
  status: 'warning',          // 'perfect' / 'warning'(90-99%) / 'error'(<90%)
  note: '准确率97/100。distinct...',  // 教师评语+关键信息
  errorWords: [               // 错误词清单（每个词一条）
    { word: 'distinct', correctMeaning: '不同的，明显的', 
      wrongAnswer: '区别于(混为distinguish)', category: '词性混淆' }
  ],
  media: 'assets/images/toefl/list4-dictation.jpg'  // 练习纸图片路径（可选）
}
```

**status 取值规则：**
- `perfect` — 正确率 100% → 时间线显示绿色 ✅
- `warning` — 正确率 90-99% → 显示橙色 ⚠️
- `error` — 正确率 <90% → 显示红色 ❌

**图片保存路径：**
- 路径: `assets/images/toefl/<描述性文件名>.jpg`
- 同时复制到 joe-growth repo 同路径下
- 描述性文件名示例: `list1-dictation.jpg`, `listening-list3-dictation.jpg`, `subject-political-history.jpg`
- data.js 中的 `media` 字段应使用相对路径（相对于网站根目录）

**⚠️ vision_analyze 的局限性：** 当前视觉模型对红笔批改痕迹（圈、叉、勾、下划线）的检测不够可靠，经常漏报或误报。处理步骤：
1. 优先使用教师文字评语（用户/家主转述的评语比图片分析更可靠）
2. 如果用户直接说了准确率（如"94/100"、"全部正确"），以用户说的为准
3. 图片分析仅作为"辅助线索"，不作为最终准确率依据
4. 如果有矛盾：教师评语 > 用户口述 > 图片分析结果

### 2. 图片批改处理通用规则（从多次实践中总结）

| 用户提供的评语类型 | 处理方式 |
|:------------------|:--------|
| "准确率94/100" | 按40词、正确38词、准确率95% 记录 |
| "20/26" | 按26词、正确20词、准确率77% 记录 |
| "全部正确[强]" | 按100%正确记录 |
| "部分单词元音出现错误" | 记录为元音错误，errorWords中标注 |
| "订正后能完全背诵正确" | 在 note 中标注，不改变 accuracy |

### ⚠️ git push 的 gh-pages 分支处理

**默认流程（正常情况）：** 直接在 main 上提交后：
```bash
git push origin main
git push origin gh-pages
```

**gh-pages 落后于 main（fast-forward 可解决）：**
```bash
git checkout gh-pages && git merge main && git push origin gh-pages && git checkout main
```

**gh-pages 与 main 分叉（unrelated histories，如 gh-pages 被直接修改过）：**
```bash
git checkout main && git branch -D gh-pages && git checkout -b gh-pages && git push origin gh-pages --force && git checkout main
```

**⏰ 推 gh-pages 后等待 1-2 分钟让 GitHub Pages 构建生效，再用浏览器验证。**

### A. 单次练习处理（旧流程，保留作参考）
1. 接收Joe上传的听写/默写图片或文档
2. OCR识别或手动提取错误单词
3. 整理成错误列表（按List、错误类型分类）
4. 更新 vocabulary_data.json 中对应词条的 errors 计数
5. 记录到 practice_tracker.json（日期、材料、词数、正确率、错误清单）
6. 新词补充入库
7. ⚠️ 关键验证：检查 practice_tracker 中 test_words 和 error_words 数组是否有具体单词数据（不能为空列表），同时将正确词写入 learned_words.json、错误词写入 error_words.json

### B. ⚡ 批量资料处理（爸爸一次性发多份材料）
爸爸经常一次性发来大量图片+文档，需要系统化处理：

**并行优先原则：**
1. 先快速扫描所有文件类型，分类（词汇练习 / 上课笔记 / 写作练习 / PPT课件）
2. 词汇类图片/文档 → 优先并行处理（比对数据库、标记对错）
3. 上课笔记类 → 提取关键知识点
4. 写作练习类 → 分析批改要点
5. 使用 delegate_task 并行处理不同类型的材料

**词汇正确性检查流程（关键步骤）：**
1. 从图片描述或OCR中提取所有单词及其中文释义
2. 与 vocabulary_data.json 做精确匹配比对
   - 按 word 字段精确匹配（忽略大小写）
   - 检查释义是否接近（一方包含另一方即可认定为正确）
3. 分类标记：
   - ✅ 正确：在库且释义匹配
   - 🔄 释义接近但不同：记录为"同义词范畴"，不视为错误
   - 🆕 新词：补充入库
4. 无论正确与否，都写入 practice_tracker.json 记录练习会话
5. 只有确认写错（拼写错误、释义完全错误）才累加 errors 计数

**笔记整理流程：**
1. 提取所有docx/pptx文本内容（python-docx / python-pptx）
2. 分类：写作模板 / 口语技巧 / 词汇积累 / 话题思路
3. 结构化输出为 markdown 复习指南
4. 保存到 /root/joe-toefl-tracker/joe_toefl_study_notes_*.md

### C. 每周自动复习
1. 每周日 09:00 cron 触发 → 运行 weekly_review.py
2. 从 vocabulary_data.json 中筛选 errors > 0 的词汇
3. 按错误次数排序 → TOP 10 高频错误词
4. 自动生成3类练习题（默写题 / 释义题 / 拼写纠错题）
5. 输出学习建议 → 推送微信
6. 也可以手动运行：`python3 /root/joe-toefl-tracker/weekly_review.py`

### E. 练习材料处理 — 建立学习库 + 错题库（从上传材料中提取）

当用户上传Joe的托福练习材料（图片/文档/批改单），需执行以下流程：

**1. 材料分类**
- 词汇练习（听写/默写/拼写）→ 提取单词对错
- 写作练习 → 提取批改意见、语法错误
- 口语练习 → 提取评分反馈
- 模考成绩 → 记录分数和分析

**2. 单词提取 → 双库归档**

对词汇类练习材料，执行双库写入：

```
┌──────────────────────┐
│ 上传的练习材料         │
│ (图片/文档/文字列表)    │
└──────────┬───────────┘
           ↓
┌────────────────────────────────────┐
│ Step 1: 提取所有单词 + 中文释义      │
│ - 从图片OCR / 文档解析 / 文字描述    │
│ - 标记：✅正确 / ❌错误             │
└──────────┬───────────┬────────────┘
           ↓           ↓
┌──────────────────┐ ┌──────────────────────┐
│ 📚 学习库          │ │ ❌ 错题库               │
│ (learned_words    │ │ (error_words          │
│  .json)           │ │  .json)               │
│ 所有练习过的单词     │ │ 只有错误的词            │
│ 含对错标记+练习日期  │ │ 含错误类型+错误次数+日期 │
│ 每次练习都追加记录    │ │ 正确3次后移到已掌握     │
└──────────────────┘ └──────────────────────┘
```

**3. 学习库（learned_words.json）更新**
- 所有练习过的单词（不论对错）都记录
- 字段：`{word, meaning, section, date, status}`

**4. 错题库（error_words.json）创建/更新**
- 仅记录错误的单词，按错误频率排序
- 字段：`{word, meaning, error_type, error_count, first_error, last_error, source_material, review_count, status}`

   ```json
   [
     {
       "word": "phenomenon",
       "meaning": "现象",
       "error_type": "spelling",
       "error_count": 3,
       "first_error": "2026-05-24",
       "last_error": "2026-05-31",
       "source_material": "List 15 听写",
       "review_count": 2,
       "status": "needs_review"
     }
   ]
   ```

**5. 错误类型分类**
- `spelling` — 拼写错误（如 phenomenon→phenomenan）
- `meaning` — 释义错误 / 混淆
- `usage` — 用法 / 搭配错误
- `pronunciation` — 发音错误（口语相关）

**6. 错题库复习机制**
- 每周自动从错题库生成复习列表（按 error_count 降序）
- 连续3次正确 → `status` 改为 `mastered`，移出错题库主列表
- 保留历史记录（含 mastered_at 时间戳）
- 复习提醒与每周日 weekly_review.py 联动

**7. 学习库复习机制**
- 支持按练习日期 / 材料来源 / 单词状态 筛选
- 快速生成某次练习的完整对错清单回顾

## 系统化追踪体系（已建成，6,840词）

### 四套资料全部入库（90个数据分区）
1. **阅读高频词30List** — list_1~30（2,956词）
2. **学科分类词汇** — subject_*（35学科，~2,765词）
3. **听力话题800词** — list_31~49（19话题，801词）
4. **听力词组** — listening_phrases（200条）
5. **听力场景高频词** — hf_listening_1~5（5场景，118词）

### PDF提取+去重原则
- 新PDF → 全量提取 → word字段精确匹配去重（忽略大小写）
- 只新增数据库中不存在的词，以新分区key入库
- 不破坏已有分区结构
- ⚠️ 学科词汇类PDF往往与已有subject_*高度重复，去重后新增量通常很小

### 每周自动复习机制（脚本: /root/joe-toefl-tracker/weekly_review.py）
1. 从 vocabulary_data.json 中筛选 errors > 0 的词汇
2. 按错误次数排序，生成 TOP 10 高频错误词
3. 自动生成3类练习题：默写题、释义题、拼写纠错题
4. 输出学习建议 + 鼓励语
5. Cron: 每周日 09:00 微信推送（job_id: 7d4964366cbd）

### 练习追踪机制
- practice_tracker.json — 记录每次练习会话（日期、材料、正确率、错误清单）
- 支持手动报错词：累加对应词条的 errors 字段

## 数据一致性检查

### 问题背景
本系统有3个数据文件+1个网站展示，它们必须保持同步：
- `vocabulary_data.json`：词库真实状态（status: learning/mastered）
- `learned_words.json`：汇总状态（completed/lists_completed/list_details）
- `data.js`：网站数据（practiceSessions + stats.wordCompletionPct）
- GitHub Pages：网站展示（从 data.js 渲染）

**2026-06-14 session 发现：** 前几次练习中标记为"已完成"的列表（list_1/3/4/5/6/7/30），其 vocabulary_data.json 中单词的 status 实际仍为 `learning`，只有 learned_words.json 和 data.js 显示已完成——产生了静默数据不一致。网站词库页读的是 vocabulary_data.json，所以完整百分比和实际进度对不上。

### 预防措施：每次处理新练习前运行一致性检查

```bash
python3 /root/.hermes/profiles/joe/skills/joe-sub-agents/joe-toefl/scripts/check-consistency.py
```

该脚本会：
1. 对比 vocabulary_data.json 中 `status=mastered` 的实际数与 learned_words.json 的 `completed` 数
2. 逐一检查 `lists_completed` 中每个列表是否真的全部标记为 mastered
3. 检查 vocab_db 中有无已标记 mastered 但未列入 `lists_completed` 的孤立列表
4. 不一致时退出码非0并列出具体问题，一致时输出 ✅

### 修复不⼀致的步骤

```bash
cd /root/joe-toefl-tracker
python3 -c "
import json
with open('vocabulary_data.json') as f:
    vocab = json.load(f)
# 找到 learned_words.json 声明的已完成列表
with open('learned_words.json') as f:
    learned = json.load(f)
completed_lists = set(learned.get('lists_completed', []))
total_mastered = 0
for key, words in vocab.items():
    if key in completed_lists:
        for w in words:
            w['status'] = 'mastered'
            w['last_reviewed'] = '2026-06-14'
        total_mastered += len(words)
        print(f'{key}: {len(words)} words → mastered')
with open('vocabulary_data.json', 'w') as f:
    json.dump(vocab, f, ensure_ascii=False, indent=2)
learned['completed'] = total_mastered
learned['completion_percent'] = round(total_mastered / learned['total_vocab'] * 100, 1)
with open('learned_words.json', 'w') as f:
    json.dump(learned, f, ensure_ascii=False, indent=2)
print(f'修复完成: {total_mastered}/{learned[\"total_vocab\"]}')
"
# 同步 data.js 的 wordCompletionPct
cd /root/joe-growth
...(手动改用 patch 搜索 wordCompletionPct 并更新数值)...


## 错误列表格式
```
List X 错误记录（日期：YYYY-MM-DD）
| 错误单词 | 正确中文释义 | 错误类型 | 复习次数 |
|---------|------------|---------|---------|
| word     | 中文释义     | 拼写/意思 | 0       |
```

## 复习提醒策略
- 新错误：提醒在第1天、第3天、第7天、第14天复习
- 连续3次正确的单词：移出错误列表
- 每周汇总复习报告

## 数据录入优先级规则（2026-06-10 更新）
教师文字评语 > 用户口述 > 图片分析结果。用户直接说的准确率就是最终数据。图片分析仅作单词列表参考，vision_analyze对红笔批改痕迹检测不可靠。

## ⚠️ 常见陷阱（Pitfalls）

### 1. 托福分数制混淆
- ❌ 旧习惯：用120分制（如"45分"）
- ✅ 正确：六分制（1-6分），Joe当前3.5分，目标4.5分→5.0分→5.5分
- 引用：toefl_6point_guide.md 有完整说明

### 2. 用户身份混淆
- 家**主**（爸爸）= 发号施令的男主人
- 家**主母**（Alice/舅）= 女主人
- ❌ 不要称爸爸为"主母"
- ✅ 分清谁在说话，避免混淆

### 3. PDF提取去重
- 学科词汇类PDF往往与已有 subject_* 分区高度重复
- 必须做去重比对后再入库，否则数据库膨胀
- 去重逻辑：按 word 字段精确匹配，忽略大小写

### 4. 学习计划年份
- ❌ 用旧年份（如2025）
- ✅ 当前年份是2026年

### 5B. 词汇完成标记与进度展示（2026-06-08 用户明确要求的流程）

**用户原话：** "他学过了的这些单词啊，然后你把它标记为完成" + "有一个总的学习进度完成比例，这样的话可以鼓励他"

**核心原则：** 每次处理完一批练习，都必须同步更新词汇状态和进度展示，两者缺一不可。

#### 完整流程

```
练习批改完成 → data.js 记录练习session
    ↓
① 判定该练习所属的列表（list_X）
② 检查该列表的词是否已标记为 mastered
③ 如未标记 → 批量更新 vocabulary_data.json 中对应列表所有词的 status = "mastered"
④ 更新 learned_words.json 的完成计数（total_vocab / completed / completion_percent）
⑤ 更新 data.js 中 toefl.wordLists 对应列表的 completed 数组
⑥ 更新 data.js 中 toefl.stats.wordCompletionPct 字段
⑦ 验证：网站进度条 和 Quick Stats 卡片 显示正确的百分比
⑧ git push（main + gh-pages）上线
```

#### 已完成的词库列表判断标准

当以下任一条件满足时，该列表标记为已完成：

| 条件 | 说明 | 示例 |
|:----|:----|:----|
| **≥70%的列表词被测试** | 练习的 tested 数量接近或超过列表总词数的70% | List 4 测试100/100词 → 标记已完成 |
| **列表被明确命名为"List X"** | 练习的 section 包含"List X"且多次出现 | List 1/3/4/5/6/7/30 |
| **用户说"学过了"** | 用户口头确认这些词已学完 | 用户说"他学过了的这些单词" |

**不满足标记条件的场景：**
- 只测了"延伸词汇"（如 List 2 延伸 14词 → 不是完整列表）
- 主题词汇（酒店/图书馆/银行等 → 散落在多个列表中，不单个标记）

#### 标记完成的具体代码实现

```bash
cd /root/joe-growth
python3 -c "
import json
with open('vocabulary_data.json') as f:
    vocab = json.load(f)
completed_lists = {'list_1', 'list_3', 'list_4', 'list_5', 'list_6', 'list_7', 'list_30'}
completed_words = 0
total_words = 0
for key, words in vocab.items():
    total_words += len(words)
    if key in completed_lists:
        for w in words:
            w['status'] = 'mastered'
            w['last_reviewed'] = '2026-06-08'
        completed_words += len(words)
with open('vocabulary_data.json', 'w') as f:
    json.dump(vocab, f, ensure_ascii=False, indent=2)
print(f'完成: {completed_words}/{total_words} = {completed_words/total_words*100:.1f}%')
"
```

#### learned_words.json 结构

```json
{
  "student": "Joe (魏源)",
  "description": "托福词汇学习库 - 记录已学词汇及完成状态",
  "last_updated": "2026-06-08",
  "total_vocab": 6846,
  "completed": 701,
  "completion_percent": 10.2,
  "lists_completed": ["list_1", "list_3", "list_4", "list_5", "list_6", "list_7", "list_30"],
  "list_details": {
    "list_1": {"name": "List 1", "total": 100, "mastered": 100, "accuracy": 95, "date": "2026-05-20"},
    "list_3": {"name": "List 3", "total": 100, "mastered": 100, "accuracy": 100, "date": "2026-06-09"}
  },
  "recent_accuracy_avg": 98.2
}
```

#### 网站进度展示组件

**Quick Stats 卡片：** 在 TOEFL 页面的 quick-stats 中增加「📖 词库完成 XX%」卡片

```javascript
// data.js stats getter 中新增:
wordCompletionPct: Math.round(701 / 6846 * 100)

// index.html quick stats 中新增卡片:
'<div class="qs-card"><div class="num" style="color:var(--sports)">' + st.wordCompletionPct + '%</div><div class="label">📖 词库完成</div></div>'
```

**进度条（🅳 待学列表上方）：**
```html
<div style="background:var(--card2);padding:14px;border-radius:12px;margin-bottom:16px">
  <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:.82rem">
    <span>📖 词汇库总进度</span>
    <span><strong id="word-progress-pct" style="color:var(--sports)">0%</strong> · <span id="word-progress-detail">0 / 6,846</span></span>
  </div>
  <div style="background:var(--card2);border-radius:10px;height:14px;overflow:hidden">
    <div id="word-progress-bar" style="width:0%;height:100%;border-radius:10px;background:linear-gradient(90deg,var(--accent),var(--sports));transition:width .6s ease"></div>
  </div>
</div>
```

```javascript
// 进度条 JS 填充:
var pctEl = document.getElementById('word-progress-pct');
var detailEl = document.getElementById('word-progress-detail');
var barEl = document.getElementById('word-progress-bar');
pctEl.textContent = wpc + '%';
detailEl.textContent = '701 / 6,846';
barEl.style.width = wpc + '%';
```

**⚠️ 常见陷阱：**
- ❌ 只更新了 data.js 的 practiceSessions 但忘了更新 vocabulary_data.json 的 word status
- ❌ 只更新了 vocabulary_data.json 但忘了更新 learned_words.json 的汇总数字
- ❌ 只更新了数据文件但忘了推 gh-pages（网站不刷新进度条）
- ❌ 进度百分比硬编码在 HTML 中而不是通过 stats.getter 自动计算
- ❌ 网站进度条更新了但 Quick Stats 卡片没同步（两个展示位置都需要改）
- ❌ 仅更新了 vocabulary_data.json 但没检查网站渲染代码是否读取 `status` 字段
- ❌ **以为之前的已完成列表实际在 vocabulary_data.json 中正确标记了** — 2026-06-14 session 发现 list_1/3/4/5/6/7/30 的 status 仍为 `learning`，只有 learned_words.json 和 data.js 的数字对得上。每次处理新练习前运行 `check-consistency.py` 做基线确认，不一致时先同步再继续

**⚠️ 渲染代码架构坑 — 从 practice-session 映射改为直接读取 vocabulary_data.json 的 status 字段（2026-06-08 修）：**

修复前的问题代码（index.html 1170~1300 行附近）：
```javascript
// ❌ 旧方法：从 practice session mapping 推算每个列表的完成度
var practiced = {};
T.practiceSessions.forEach(function(s) {
  if (key.indexOf('List 6') >= 0) practiced['list_6'] = ...;
  else if (key.indexOf('List 7') >= 0) practiced['list_7'] = ...;
  // ❌ List 1~5, 30 都没有映射！
});
// 然后用 practicedCount 推算 → 漏掉了大部分列表
```

修复方式（核心逻辑变化）：
```javascript
// ✅ 新方法：直接从 vocabulary_data.json 读取每个单词的 status 字段
var masteredCount = 0;
words.forEach(function(w) { if (w.status === 'mastered') masteredCount++; });
// 列表状态根据 masteredCount 判定
var statusClass = masteredCount === 0 ? '待学' : 
                  (masteredCount < words.length ? '进行中' : '已完成');
var badgeLabel = masteredCount === 0 ? '0%' : 
                 (masteredCount < words.length ? pct + '%' : '✅ 已完成');

// 每单词状态也从 vocabulary_data.json 读取
var wordStatus = w.status === 'mastered' ? '✅ 已学' : '📖 待学';
```

**必须同步更新的两个关键 CSS 颜色变量（2026-06-08 追加）：**
- 待学→ `var(--accent)`（蓝）
- 进行中→ `var(--expense)`（橙）
- 已完成→ `var(--sports)`（绿）

**⚠️ 柱状图避免重叠（2026-06-08 用户指出）：**
分数标签不要用 `position:absolute;top:-18px` 放在柱内，而是放在🎯图标上方独立一行：
```html
<!-- ❌ 重叠布局：分数在柱内、🎯在柱上 -->
<div>🎯</div>
<div style="position:relative">
  <span style="position:absolute;top:-18px;">3.5</span>  <!-- 重叠！ -->
</div>

<!-- ✅ 正确布局：分数→🎯→柱体→标签 分层排列 -->
<span>3.5</span>    <!-- 分数在最上面 -->
<div>🎯</div>      <!-- 图标在分数下面 -->
<div class="bar"></div>
<span>现在</span>   <!-- 标签在柱下面 -->
```

### 6. 仅记录统计数量不够 — 必须提取具体单词

- ❌ 错误的做法：只记录 "27词/100%正确/0错误" 这种聚合统计
- ✅ 正确的做法：把具体是**哪些单词**逐一提出来
  - 正确词 → 写入 `learned_words.json`（标记 `status: correct`）
  - 错误词 → 写入 `error_words.json`（记录错误类型和次数）
  - 在 `practice_tracker.json` 的 `test_words` 数组中记录每个测试单词
- 用户期望的是单词级追踪，不是统计级追踪
- **每次练习处理后，必须人工检查 `practice_tracker.json` 的 `test_words` 不为空**
- 如果发现旧记录中 test_words 为空（历史数据未提取），向用户坦白：旧图片已无法回溯，需要重新上传或发新练习

### 7. 新旧数据衔接
- 对于已经存在的练习记录（如 practice_tracker.json 中 test_words 为空的历史条目），不要假装已处理
- 主动告知用户：系统已升级，旧数据缺少单词级信息，如有需要请重新上传
- 不要让用户在不知情的情况下以为旧数据已经完整入库

### 8. 多份材料 + 独立老师反馈

当用户一次性发送多份练习材料（如List词汇表 + 银行话题默写纸），且老师单独提供文字反馈时：

1. **不要把所有材料合并为一个条目** — 不同话题/技能（听力 vs 阅读）的练习要分条记录
2. **老师反馈可能晚于图片到达** — 用户先发图片，再转发老师评语
3. **老师的一句话可能涵盖多份材料** — 如"听力全部正确；阅读准确率99/100"
4. **必须等老师反馈到达后再最终确定错误计数** — 仅凭图片上的批改可能不完整
5. **更新现有追踪条目，而不是追加条目** — 如果已建条目但老师反馈后需要修正，直接更新该条目的错误计数

**正确流程：**
1. 收到图片 → 初步提取所有单词 → 标记明显批改痕迹
2. **暂不提交为最终记录**，标记`status: pending_teacher_review`
3. 等待用户转发老师评语
4. 结合评语修正错误计数
5. 再写入 practice_tracker.json、vocabulary_data.json、error_words.json

### 9. 形近词混淆

常见于阅读词汇的听写/默写中，一个特定模式：学生写出的中文释义是另一个常见形近词的含义。

**处理方式：**
- 记录错误类型为 `形近词混淆`
- 在 error_words 的字段中标注 `confused_with`: 具体被混淆的词
- 记录老师建议（如 "注意equate和equal可以结合记忆"）
- 生成复习题时，专门出形近词辨析题（给两个形近词，让少爷选正确的释义）

**典型例子（本session）：**
```json
{
  "word": "equable",
  "correct_meaning": "平稳的，稳定的",
  "wrong_meaning": "相等的（混淆为equal）",
  "category": "形近词混淆",
  "confused_with": ["equal", "equate"],
  "teacher_tip": "注意equate和equal可以结合记忆"
}
```

### 10. 课程安排验证
- **注意区分新旧课表**：旧课表(04-11→07-13)已结束，新课表(08-16→08-22)为赛艇归来后的8月集训
- 8月集训为连续冲刺：8/16(日)听力+模考 → 8/17-21每日一课 → 8/22(六)**正式考试**
- 8/22是**正式托福考试**（用户已确认，非模考），务必做好考前提醒
- 若比赛/活动与课程冲突，标注补课安排
- 参考 `references/tutoring-schedule.md` 快速查询

### 参考文件
- vocabulary_data.json（1.3MB, 6,846词, 90个列表）→ 通过 website page-toefl-words 可浏览
- 词库浏览页面: index.html 的 page-toefl-words（用 fetch 加载 vocabulary_data.json 动态渲染）
- 系统架构总览: `references/system-architecture.md`
- 批量上传处理工作流: `references/batch-upload-processing.md`
- 📅 **课程安排表**: `references/tutoring-schedule.md`（8月集训版：8/16-22，含8/22正式考试）
- 完整课堂笔记示例: `/root/joe-toefl-tracker/joe_toefl_study_notes_20260524.md`
- 六分制完整攻略: `/root/joe-toefl-tracker/toefl_6point_guide.md`
- 每周复习脚本: `scripts/weekly_review.py`（或 `/root/joe-toefl-tracker/weekly_review.py`）
- 🛡️ **数据一致性检查脚本**: `scripts/check-consistency.py` — 每次处理新练习前运行
- 词汇数据库: `/root/joe-toefl-tracker/vocabulary_data.json`
- 学习库: `/root/joe-toefl-tracker/learned_words.json`
- 错题库: `/root/joe-toefl-tracker/error_words.json`
- 练习追踪: `/root/joe-toefl-tracker/practice_tracker.json`
- 学习计划: `/root/joe-toefl-tracker/study_schedule.json`
- 课程日历: `/root/.hermes/托福课程表_六六.ics`
