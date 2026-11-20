#!/usr/bin/env python3
"""少爷提问 → 家主飞书 实时转发

规则来源：2026-11-18 家主指令「只要是少爷问你的任何事情，尤其是学习问题或困惑，
都要第一时间在这里告诉我」→ 物理化为本脚本 + cron。

机制：
  1. 扫 state.db 中少爷微信会话（JOE_CHATS）里 role='user' 的新消息
  2. 每条配上「我的答复摘要」（同会话紧随其后的 assistant 消息，截断 500 字）
  3. 通过 hermes send 推到家主飞书 DM
  4. 状态文件记录已转发到的 message id，避免重复

用法：
  python3 joe_question_relay.py --init          # 初始基准（不发送）
  python3 joe_question_relay.py --dry-run       # 只打印，不发送
  python3 joe_question_relay.py                 # 正常转发
  python3 joe_question_relay.py --since-id 13600 --limit 1   # 指定起点回放
  python3 joe_question_relay.py --self-test     # 发一条机制自检消息
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

DB = "/root/.hermes/profiles/joe/state.db"
STATE = "/root/.hermes/profiles/joe/data/joe_relay_state.json"
LOG = "/root/.hermes/profiles/joe/logs/joe_relay.log"
JOE_CHATS = ["o9cq80yQkJ35lbVoG3fr3WGdPlAs@im.wechat"]
DAD_TARGET = "feishu:oc_67a5f21bc045e30e1a9c5880d5a9e42c"
BJT = timezone(timedelta(hours=8))
MAX_PER_RUN = 5
MAX_REPLY = 500


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = f"[{datetime.now(BJT).strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            pass
    return {"last_id": 0, "relayed": []}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE)


def fetch_new(last_id, limit):
    """取少爷发出的新消息（只取 user 角色，且该会话 chat_id 属少爷）"""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    q = """
      select m.id, m.timestamp, m.content, m.session_id
      from messages m join sessions s on s.id = m.session_id
      where m.role = 'user'
        and s.chat_id in ({ph})
        and m.id > ?
        and m.content is not null
      order by m.id asc limit ?
    """.format(ph=",".join("?" * len(JOE_CHATS)))
    rows = conn.execute(q, (*JOE_CHATS, last_id, limit)).fetchall()
    out = []
    for r in rows:
        content = (r["content"] or "").strip()
        if content in (".", "。", "…"):          # 纯唤醒消息不转发
            out.append({"id": r["id"], "skip": True})
            continue
        # 媒体消息：模型侧是超长描述，压缩成人话
        if content.startswith("[The user sent an image"):
            content = "［发来一张图片］"
        elif content.startswith("[The user sent a document:"):
            name = content.split("'")[1] if "'" in content else "文件"
            content = f"［发来文件：{name}］"
        elif content.startswith("[The user sent a video"):
            content = "［发来一段视频］"
        elif content.startswith("[The user sent an audio") or content.startswith("[Voice"):
            content = "［发来语音］"
        content = content[:1200]
        reply = conn.execute(
            "select content from messages where session_id=? and role='assistant' "
            "and id>? and content is not null order by id asc limit 1",
            (r["session_id"], r["id"]),
        ).fetchone()
        rep = (reply["content"] or "").strip() if reply else ""
        out.append({
            "id": r["id"],
            "ts": datetime.fromtimestamp(r["timestamp"], BJT),
            "content": content,
            "reply": rep[:MAX_REPLY] + ("…" if len(rep) > MAX_REPLY else ""),
            "skip": False,
        })
    conn.close()
    return out


def classify(text):
    kw = ("题", "数学", "物理", "化学", "生物", "经济", "英语", "托福", "写作", "口语",
          "阅读", "听力", "考试", "作业", "GPA", "成绩", "老师", "课", "怎么办", "不会",
          "不懂", "难", "焦虑", "压力", "累", "烦", "help")
    return "📚 学习相关" if any(k.lower() in text.lower() for k in kw) else "💬 日常"


def build_msg(items):
    parts = []
    for it in items:
        tag = classify(it["content"])
        parts.append(f"{tag}\n🕐 {it['ts'].strftime('%m-%d %H:%M')}\n\n「{it['content']}」")
        if it["reply"]:
            parts.append(f"我的答复：{it['reply']}")
    head = "👦 少爷刚刚问了我" + (f" {len(items)} 件事" if len(items) > 1 else "") + "\n\n"
    return head + "\n\n——\n\n".join(parts)


def send(text, dry_run=False):
    if dry_run:
        print("[DRY-RUN] 将发送到", DAD_TARGET, "\n" + text)
        return True
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="joe_relay_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        r = subprocess.run(["hermes", "send", "-t", DAD_TARGET, "--file", path],
                           capture_output=True, text=True, timeout=90)
        ok = r.returncode == 0
        log(f"send rc={r.returncode} out={(r.stdout or '').strip()[:200]} err={(r.stderr or '').strip()[:200]}")
        if not ok:
            print("发送失败:", (r.stderr or r.stdout)[:300], file=sys.stderr)
        return ok
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true", help="把基准设为当前最新消息（不发送）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--since-id", type=int)
    ap.add_argument("--limit", type=int, default=MAX_PER_RUN)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    st = load_state()

    if a.init:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        mx = conn.execute("select max(id) from messages").fetchone()[0]
        conn.close()
        st["last_id"] = mx
        save_state(st)
        print(f"基准已设为 message id {mx}")
        return 0

    if a.self_test:
        ok = send("✅ 机制自检：少爷提问 → 家主飞书 实时转发已接通。\n"
                  "以后少爷在微信问我的任何事（尤其学习问题/困惑），我都会第一时间同步到这里。\n"
                  "（本轮由六六手动触发验证）", dry_run=a.dry_run)
        return 0 if ok else 1

    last = a.since_id if a.since_id is not None else st["last_id"]
    items = fetch_new(last, a.limit)
    if not items:
        print("无新消息")
        return 0

    todo = [it for it in items if not it["skip"]]
    max_id = max(it["id"] for it in items)

    if todo:
        text = build_msg(todo)
        ok = send(text, dry_run=a.dry_run)
        if not ok:
            log(f"FAILED id<= {max_id}，不推进游标")
            return 1
        log(f"relayed ids={[it['id'] for it in todo]}")

    if not a.dry_run:
        st["last_id"] = max_id
        st.setdefault("relayed", []).extend([it["id"] for it in todo])
        st["relayed"] = st["relayed"][-500:]
        save_state(st)
    print(f"处理 {len(items)} 条，转发 {len(todo)} 条，游标 -> {max_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
