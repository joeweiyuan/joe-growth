---
name: joe-task-dispatch
description: >-
  Joe学业Agent的子Agent任务派发标准模板集。
  主Agent加载此技能后，用其中的模板通过delegate_task派发实际子Agent。
  每个模板包含：终止条件 + 质量标准 + 输出格式 + Maker/Checker工作流。
  解决"子Agent不知道标准"的问题——约束通过context显式注入。
version: 1.0.0
author: 元宝
metadata:
  hermes:
    tags: [joe, sub-agent, dispatch, quality, education]
    related_skills: [maker-checker-workflow, termination-condition, session-memory-management]
---

# Joe 学业子Agent任务派发模板集

## 总原则

每次通过 `delegate_task` 派发子Agent时，context 参数必须包含以下四要素：

```
1. 📋 任务目标（含终止条件）
2. 📐 质量标准（硬约束，不可违反）
3. 📤 输出格式（期望的产物样式）
4. 🔄 工作流步骤（先做什么后做什么）
```

**不给context就派发 = 让子Agent瞎猜 = 质量不可控。**

---

## 模板1：学术报告 Agent

```
delegate_task(
    goal="分析Joe本月学术成绩，生成趋势报告",
    context="""
    ## 📋 任务目标
    分析STATE.md中记录的当前课程成绩，产出月度趋势报告
    终止条件：✅ 全部科目覆盖 + 每科趋势分析 + 下月行动建议
    
    ## 📐 质量标准
    - 数据必须从 /root/.hermes/profiles/joe/STATE.md 读取，不准编造
    - 每科分析 ≤ 200字
    - 建议必须具体可执行（"每天背20个单词"✓ / "加强词汇"✗）
    - 必须包含趋势方向（上升/下降/稳定）
    
    ## 📤 输出格式
    保存到 /root/.hermes/profiles/joe/reports/academic_{date}.md
    格式：| 科目 | 当前分 | 上月分 | 趋势 | 分析 | 建议 |
    
    ## 🔄 工作流
    1. 读 STATE.md 获取当前成绩
    2. 分析趋势
    3. 生成报告
    4. 用 maker-checker-workflow 自检
    5. 更新 STATE.md 标记完成
    
    ## ⚠️ 禁止
    - 不要编造不存在的数据
    - 不要推测没有依据的趋势
    """
)
```

## 模板2：竞赛规划 Agent

```
delegate_task(
    goal="为Joe制定竞赛规划方案",
    context="""
    ## 📋 任务目标
    根据Joe当前年级和兴趣，推荐适合的竞赛并制定备赛时间线
    终止条件：✅ 3个推荐竞赛 + 每个的时间线 + 备赛资源
    
    ## 📐 质量标准
    - 竞赛必须适配Joe当前年级（别推荐超纲的）
    - 每个竞赛给出：名称/适合年级/备赛周期/推荐资源
    - 时间线必须与学年日历兼容（不冲突考试周）
    - 优先推荐有中国赛区的竞赛
    
    ## 📤 输出格式
    保存到 /root/.hermes/profiles/joe/reports/competition_{date}.md
    | 竞赛 | 适合年级 | 备赛周期 | 难度 | 资源推荐 |
    
    ## 🔄 工作流
    1. 读 STATE.md 获取Joe当前年级/兴趣
    2. 研究推荐竞赛
    3. 生成方案
    4. 自检后通知主Agent
    5. 更新 STATE.md
    """
)
```

## 模板3：托福备考 Agent

```
delegate_task(
    goal="生成Joe的托福备考计划",
    context="""
    ## 📋 任务目标
    根据Joe当前英语水平，制定分阶段的托福备考计划
    终止条件：✅ 听说读写四维计划 + 模考时间表 + 每日任务
    
    ## 📐 质量标准
    - 计划必须分阶段（基础→强化→冲刺）
    - 每日任务可执行（不能"每天练2小时"这种空话）
    - 模考频率合理（每月至少1次）
    - 各维度占比根据薄弱项调整
    
    ## 📤 输出格式
    保存到 /root/.hermes/profiles/joe/reports/toefl_{date}.md
    | 阶段 | 周期 | 阅读 | 听力 | 口语 | 写作 | 模考 |
    
    ## 🔄 工作流
    1. 读 STATE.md 获取当前英语水平
    2. 制定计划
    3. 自检后输出
    4. 更新 STATE.md
    """
)
```

## 模板4：兴趣爱好 Agent

```
delegate_task(
    goal="为Joe推荐课外活动和兴趣发展方案",
    context="""
    ## 📋 任务目标
    根据Joe当前兴趣和空闲时间，推荐课外活动和特长培养方案
    终止条件：✅ 3个活动推荐 + 时间安排 + 资源链接
    
    ## 📐 质量标准
    - 活动必须与Joe的已知兴趣匹配
    - 时间投入合理（不与学业冲突）
    - 每个活动给出：内容/投入时间/预期收获
    - 优先推荐学校已有的社团/活动
    
    ## 📤 输出格式
    保存到 /root/.hermes/profiles/joe/reports/interests_{date}.md
    | 活动 | 类型 | 每周时间 | 收获 | 资源 |
    
    ## 🔄 工作流
    1. 读 STATE.md
    2. 推荐活动
    3. 自检后输出
    4. 更新 STATE.md
    """
)
```

## 并行批量派发示例

当需要同时派发多个独立子Agent时：

```
results = delegate_task(tasks=[
    {"goal": "分析Joe本月学术成绩", "context": "学术报告模板...", "toolsets": ["terminal", "file"]},
    {"goal": "制定竞赛规划方案", "context": "竞赛规划模板...", "toolsets": ["terminal", "file", "web"]}
])

# 完成后派Checker验证
for r in results:
    delegate_task(goal="检查子Agent输出质量", context="检查数据真实性/建议可操作性/格式/完整性")
```

## 子Agent工作流总图

```
主Agent
  │
  ├─ 读 STATE.md ── 了解Joe当前状态
  │
  ├─ delegate_task(学术报告) ── 带模板context
  │   └─ [子Agent] 读数据 → 分析 → 写报告 → 自检 → 更新STATE
  │
  ├─ delegate_task(竞赛规划) ── 带模板context  
  │   └─ [子Agent] 调研 → 规划 → 写方案 → 自检 → 更新STATE
  │
  ├─ Checker验证各子Agent产出
  │
  └─ 汇总报告给用户
```

## 关键规则

| 规则 | 说明 |
|------|------|
| 模板必须带全 | context缺一不可：目标+终止条件+质量标准+输出格式+工作流 |
| 数据源必须指定 | 告诉子Agent去哪里读数据（STATE.md），否则自己编 |
| 自检必须执行 | 子Agent产出后先自检，再交回主Agent |
| 并行只限独立任务 | 依赖关系明确时不并行 |
| 写回STATE.md | 子Agent完成必须更新STATE.md，让主Agent知道进度 |
