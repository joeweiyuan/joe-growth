# 规则：少爷提问必报家主（Joe Question Relay）

> 立规：2026-11-20 家主指令
> 「只要是少爷问你的任何事情，尤其是学习问题或困惑等，都要第一时间在这里告诉我。」

## 一、规则本体

| 项 | 内容 |
|:----|:----|
| **触发** | 少爷（Joe / 魏源）在微信向我提出任何问题 |
| **重点** | 学习问题、学业困惑、情绪/压力、师生关系、考试焦虑 —— 最高优先 |
| **动作** | **第一时间**把「少爷原话 + 我的答复摘要」同步到家主飞书 DM |
| **时限** | 10 分钟内（cron 每 10 分钟扫描） |
| **例外** | 纯唤醒消息（`.` `。` `…`）不转发；无实质内容的表情不转发 |

## 二、物理实现（不是靠自觉）

| 组件 | 位置 |
|:----|:----|
| 转发脚本（唯一来源） | `/root/joe-growth/scripts/joe_question_relay.py` |
| Cron 入口（薄封装，防双副本漂移） | `/root/.hermes/profiles/joe/scripts/joe_question_relay_entry.py` |
| 定时任务 | cron `5e5fb1be8b71` · `every 10m` · `no_agent` |
| 游标状态 | `/root/.hermes/profiles/joe/data/joe_relay_state.json`（`last_id`，防重复） |
| 运行日志 | `/root/.hermes/profiles/joe/logs/joe_relay.log` |
| 数据源 | `state.db` → `messages` ⋈ `sessions`，`chat_id = o9cq80yQkJ35lbVoG3fr3WGdPlAs@im.wechat` |
| 推送目标 | `feishu:oc_67a5f21bc045e30e1a9c5880d5a9e42c`（家主 DM） |

## 三、消息格式

```
👦 少爷刚刚问了我 N 件事

📚 学习相关 / 💬 日常
🕐 11-20 21:15

「原话」

——

我的答复：<答复摘要，≤500 字>
```

## 四、运维

```bash
python3 /root/joe-growth/scripts/joe_question_relay.py --dry-run      # 看会发什么
python3 /root/joe-growth/scripts/joe_question_relay.py --init         # 重置基准（不回放）
python3 /root/joe-growth/scripts/joe_question_relay.py --self-test    # 通道自检
python3 /root/joe-growth/scripts/joe_question_relay.py --since-id N   # 指定起点回放
```

## 五、边界

- **只转发，不代答**：答复仍由我在小少爷侧完成，家主侧只做知情。
- **不改少爷的数据**：转发是只读操作（`state.db` 以 `mode=ro` 打开）。
- **失败不推进游标**：发送失败时游标不动，下一轮重试，不丢消息。
- **纯唤醒消息不转**：避免 `"."` 类保活消息刷屏。
