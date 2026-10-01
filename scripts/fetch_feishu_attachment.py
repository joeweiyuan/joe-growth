#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_feishu_attachment.py — 取回"被飞书适配器丢弃"的消息附件

为什么需要（2026-10-01 事故）：
  飞书**富文本(post)消息**把附件放在 post 的**顶层 `files` 数组**里
  （如 {"post":{"title":"","content":[[{tag:text,...}]],"files":[{"file_key":...,"file_name":...}]}}）。
  Hermes 的飞书适配器解析 post 时只扫**正文 content 行**内的 file_key，
  未处理顶层 files → 日志出现 `Received raw message type=post` 但 `media=0`，附件静默丢失。
  本脚本绕过适配器，直接用飞书 OpenAPI 取回。

用法：
  python3 scripts/fetch_feishu_attachment.py <message_id> [--out DIR] [--list-only]
  # message_id 形如 om_xxxxxxxx（可从网关日志 "Inbound dm message received: id=om_..." 复制）

行为：
  1) 从 profile 的 .env 读 FEISHU_APP_ID / FEISHU_APP_SECRET（绝不打印值）
  2) 换 tenant_access_token → GET im/v1/messages/{message_id}
  3) 递归收集 file_key / image_key（含顶层 files、content 行内）
  4) 按类型下载 resource（file/image）到 --out 目录（默认 assets/incoming/）

退出码：0 成功（含"该消息确无附件"）；非 0 失败（凭据缺失/接口报错）。
安全：仅打印键名与长度、文件名、字节数；不打印任何密钥/令牌。
"""
import argparse
import json
import os
import sys
import urllib.request

ENV_FILES = ["/root/.hermes/profiles/joe/.env", "/root/.hermes/.env"]
API = "https://open.feishu.cn/open-apis"


def load_env():
    env = {}
    for f in ENV_FILES:
        if not os.path.exists(f):
            continue
        for line in open(f, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def http(url, data=None, headers=None):
    h = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=h, method="POST" if data is not None else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def collect_keys(o, acc, names):
    """递归收集 file_key / image_key，并顺带记录 file_name。"""
    if isinstance(o, dict):
        if isinstance(o.get("file_key"), str) and o["file_key"]:
            acc.append(("file", o["file_key"]))
            if o.get("file_name"):
                names[o["file_key"]] = o["file_name"]
        if isinstance(o.get("image_key"), str) and o["image_key"]:
            acc.append(("image", o["image_key"]))
        for v in o.values():
            collect_keys(v, acc, names)
    elif isinstance(o, list):
        for v in o:
            collect_keys(v, acc, names)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message_id")
    ap.add_argument("--out", default="/root/joe-growth/assets/incoming")
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    env = load_env()
    app_id = env.get("FEISHU_APP_ID") or env.get("LARK_APP_ID")
    app_secret = env.get("FEISHU_APP_SECRET") or env.get("LARK_APP_SECRET")
    if not (app_id and app_secret):
        print("❌ 凭据缺失：需要 FEISHU_APP_ID / FEISHU_APP_SECRET（见 profile 的 .env）")
        return 1
    print(f"凭据: app_id=<len={len(app_id)}> app_secret=<len={len(app_secret)}>")

    tok = http(f"{API}/auth/v3/tenant_access_token/internal",
               {"app_id": app_id, "app_secret": app_secret}).get("tenant_access_token")
    if not tok:
        print("❌ 换取 tenant_access_token 失败")
        return 1
    H = {"Authorization": f"Bearer {tok}"}

    m = http(f"{API}/im/v1/messages/{args.message_id}", headers=H)
    if m.get("code") != 0:
        print(f"❌ 取消息失败 code={m.get('code')} msg={m.get('msg')}")
        return 1
    items = (m.get("data") or {}).get("items") or []
    if not items:
        print("❌ 该消息无内容（可能已撤回/过期）")
        return 1
    it = items[0]
    print(f"msg_type={it.get('msg_type')}")
    raw = (it.get("body") or {}).get("content", "")
    try:
        content = json.loads(raw)
    except Exception:
        content = {}
        print("⚠️ content 非 JSON，已跳过结构化解析")

    acc, names = [], {}
    collect_keys(content, acc, names)
    seen, uniq = set(), []
    for t, k in acc:
        if (t, k) not in seen:
            seen.add((t, k)); uniq.append((t, k))
    print(f"发现资源 {len(uniq)} 个")
    for t, k in uniq:
        print(f"  - {t}: {names.get(k, '(无名)')} key=<len={len(k)}>")
    if not uniq:
        print("ℹ️ 该消息确实不含附件（纯文本/纯表情）")
        return 0
    if args.list_only:
        return 0

    os.makedirs(args.out, exist_ok=True)
    for t, k in uniq:
        url = f"{API}/im/v1/messages/{args.message_id}/resources/{k}?type={'image' if t == 'image' else 'file'}"
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120).read()
        except Exception as e:
            print(f"  ❌ 下载失败 {t}: {type(e).__name__}")
            continue
        name = names.get(k) or f"{t}_{k[-8:]}.bin"
        path = os.path.join(args.out, name)
        with open(path, "wb") as fh:
            fh.write(data)
        print(f"  ✅ {name}  {len(data)} 字节 → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
