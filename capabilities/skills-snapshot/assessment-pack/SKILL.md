---
name: assessment-pack
description: "Use when 学生评估/竞争力评分/软实力分级。"
version: 1.0.0
author: 六六
license: MIT
metadata:
  hermes:
    tags: [assessment, scoring, rubric, competitiveness, offerpath, evaluation]
    requires_tools: [terminal, read_file, write_file]
    editorial_name: "评估与评分技能包"
    editorial_description: "五维竞争力评分（学术/语言/深度/领导力/特长）+ 软实力 S-D 分级 + 权重按国家/专业切换 + 快照增值追踪"
---

# 评估与评分技能包（assessment-pack）

> 对应 OfferPath 缺口 **B5 综合竞争力评分 + B3 软实力分级**

## 何时用
- 要回答「这个孩子现在什么水平、差在哪」
- 要做学生前后对比（增值）、同侪对标
- 要给选校匹配引擎提供输入分

## 一、五维模型
| 维度 | 来源 | 算法 |
|:--|:--|:--|
| **学术** | GPA/百分制 + 课程强度 + 趋势 | `0.60×成绩 + 0.25×强度 + 0.15×趋势` |
| **语言** | 托福(6分制)/雅思/SAT/ACT | 归一化到 0–100，取最高项 |
| **学术深度** | 竞赛/科研/项目 | `等级分 × 时长系数`，取最强项 + 广度加分 |
| **领导力** | 职位/创办/影响 | 同上 |
| **特长** | 体育/艺术 | 同上 |

### 权重按「方向 × 专业」切换（配置驱动）
| 方向 | 学术 | 深度 | 领导力 | 特长 | 语言 |
|:--|:--:|:--:|:--:|:--:|:--:|
| 美国 | 35% | 20% | 15% | 15% | 15% |
| 英国 | 45% | 25% | 5% | 10% | 15% |
| 港/新 | 45% | 15% | 10% | 10% | 20% |

再叠加专业倾向：STEM 加学术/深度；商科加领导力；人文加语言/深度；**艺术大幅加特长（+12）**。

## 二、软实力分级（B3）
五档 **S/A/B/C/D**，锚点见 `references/soft_strength_rubric.md`：
- 竞赛按**该赛事实际晋级率**定档，不按名字响不响
- 科研三红线：买来的不算 / 挂名不算 / 解释不了方法不算
- 时长系数 `0.85 + 0.10×年`（封顶 1.25）→ **奖励持续性，不奖励堆数量**
- 广度只 +2/条，封顶 +8（防刷活动）

## 三、用法
```bash
python3 scripts/score.py --profile student.json --dest us --major stem
python3 scripts/score.py --profile s.json --dest uk --major business --json
python3 scripts/score.py --profile s.json --target mit --db college.db     # 目标校对照
python3 scripts/score.py --profile s.json --snapshot-db assess.db          # 落库增值
```

输入档案格式示例：`tests/joe_profile.json`

## 四、输出三原则
1. **可解释**：每维给「输入 → 计算 → 得分 → 驱动/短板」
2. **可配置**：权重全在 `config/weights.json`，改配置不改代码
3. **可追踪**：`--snapshot-db` 落库，下次自动算 delta

## 五、校准路径（v1 → v2）
当前是**经验权重**；手上有了真实录取结果后：
1. 收集 200+ 学生档案 + 录取结果
2. 逻辑回归/梯度提升拟合各维度权重
3. 用 AUC/校准曲线验证，替换 weights.json
> 在此之前，输出必须带「经验模型，不预测录取」声明。

## 六、边界
- ❌ 不做「录取概率百分比」宣传（合规红线）
- ❌ 不用单一总分评价孩子（五维必须同时展示）
- ❌ 缺数据时返回 0 并说明，不估算

## 验收
`tests/test_score.py` → **19/19 通过**（基准分/权重切换/缺数据/目标对照/快照增值）
