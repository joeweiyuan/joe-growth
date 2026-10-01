#!/usr/bin/env python3
"""飞书适配器补丁：修复 post 富文本消息顶层 files 附件被丢弃
先在副本上打补丁 + 真实报文单测，PASS 才写回线上。"""
import json, os, shutil, sys, types, importlib.util, py_compile

LIVE = "/usr/local/lib/hermes-agent/plugins/platforms/feishu/adapter.py"
COPY = "/tmp/adapter_patched.py"
src = open(LIVE, encoding="utf-8").read()

# ---------- 补丁 A1：_to_post_payload 保留媒体容器 ----------
A1_OLD = """    content = candidate.get("content")
    if not isinstance(content, list):
        return {}
    return {"title": str(candidate.get("title", "") or ""), "content": content}"""
A1_NEW = """    content = candidate.get("content")
    if not isinstance(content, list):
        return {}
    projected = {"title": str(candidate.get("title", "") or ""), "content": content}
    # Rich posts carry their attachments in top-level containers (``files``), not
    # inside ``content`` rows. Project them through instead of dropping them —
    # otherwise the attachment is silently lost (2026-10-01 incident).
    for _key in ("files", "images", "image_keys", "img_keys"):
        _value = candidate.get(_key)
        if isinstance(_value, list) and _value:
            projected[_key] = _value
    return projected"""

# ---------- 补丁 A2a：新增收集函数（插在 parse_feishu_post_payload 之前） ----------
A2_ANCHOR = '''def parse_feishu_post_payload(
    payload: Any, *, mentions_map: Optional[Dict[str, FeishuMentionRef]] = None,
) -> FeishuPostParseResult:'''
A2_HELPER = '''def _collect_post_top_level_media(
    resolved: Any, image_keys: List[str], media_refs: List[FeishuPostMediaRef],
) -> None:
    """Collect attachments/images that live OUTSIDE the post content rows.

    A Feishu client sending a rich post with an attachment puts it in a
    top-level ``files`` array (``{"file_key": ..., "file_name": ...,
    "is_folder": false}``) rather than an inline ``media`` element, so walking
    ``content`` alone drops the file silently (observed 2026-10-01: the message
    parsed to text with ``media=0`` while the file sat in ``files``).
    """
    files = resolved.get("files") if isinstance(resolved, dict) else None
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict):
                if item.get("is_folder"):
                    continue
                file_key = str(item.get("file_key", "") or "").strip()
                file_name = str(
                    item.get("file_name") or item.get("title") or item.get("name") or ""
                ).strip()
            elif isinstance(item, str):
                file_key, file_name = item.strip(), ""
            else:
                continue
            if not file_key or any(ref.file_key == file_key for ref in media_refs):
                continue
            media_refs.append(FeishuPostMediaRef(file_key=file_key, file_name=file_name))
    if not isinstance(resolved, dict):
        return
    for key in ("images", "image_keys", "img_keys"):
        values = resolved.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            image_key = item.get("image_key") if isinstance(item, dict) else item
            image_key = str(image_key or "").strip()
            if image_key and image_key not in image_keys:
                image_keys.append(image_key)


''' + A2_ANCHOR

# ---------- 补丁 A2b：解析函数里调用收集 ----------
A2B_OLD = """        if row_text:
            parts.append(row_text)
    return FeishuPostParseResult("""
A2B_NEW = """        if row_text:
            parts.append(row_text)
    _collect_post_top_level_media(resolved, image_keys, media_refs)
    return FeishuPostParseResult("""

# ---------- 补丁 B1：API 兜底（方法插在 _download_feishu_message_resources 之前） ----------
B1_ANCHOR = """    async def _download_feishu_message_resources(
        self, *, message_id: str, normalized: FeishuNormalizedMessage,
    ) -> tuple[List[str], List[str]]:"""
B1_NEW = '''    async def _recover_post_media_refs(
        self, message_id: str,
    ) -> tuple[List[str], List[FeishuPostMediaRef]]:
        """Recover attachments of a rich post from the message API when the event lacks them.

        A ``post`` event may carry only the text rows; the attachment is then
        visible only via ``im/v1/messages/{id}`` (top-level ``files``). Fetch it
        back so the attachment is not silently dropped (2026-10-01 incident).
        """
        if not self._client or not message_id:
            return [], []
        try:
            request = self._build_get_message_request(message_id)
            response = await self._run_blocking(self._client.im.v1.message.get, request)
            if not response or getattr(response, "success", lambda: False)() is False:
                return [], []
            items = getattr(getattr(response, "data", None), "items", None) or []
            if not items:
                return [], []
            raw_content = getattr(getattr(items[0], "body", None), "content", "") or ""
            payload = _load_feishu_payload(raw_content)
            image_keys: List[str] = []
            media_refs: List[FeishuPostMediaRef] = []
            _collect_post_top_level_media(payload, image_keys, media_refs)
            for value in payload.values():  # 也扫各语言分支/post 子对象
                if isinstance(value, dict):
                    _collect_post_top_level_media(value, image_keys, media_refs)
            if media_refs or image_keys:
                logger.info(
                    "[Feishu] Recovered %d attachment(s)/%d image(s) via message API for post %s",
                    len(media_refs), len(image_keys), message_id,
                )
            return image_keys, media_refs
        except Exception:
            logger.warning("[Feishu] Failed to recover post attachments for %s", message_id, exc_info=True)
            return [], []

''' + B1_ANCHOR

# ---------- 补丁 B2：下载流程里调用兜底 ----------
B2_OLD = """        media_urls: List[str] = []
        media_types: List[str] = []

        def _collect(cached_path: str, media_type: str) -> None:
            if cached_path:
                media_urls.append(cached_path)
                media_types.append(media_type)

        for image_key in normalized.image_keys:
            _collect(*await self._download_feishu_image(message_id=message_id, image_key=image_key))
        for ref in normalized.media_refs:"""
B2_NEW = """        media_urls: List[str] = []
        media_types: List[str] = []

        def _collect(cached_path: str, media_type: str) -> None:
            if cached_path:
                media_urls.append(cached_path)
                media_types.append(media_type)

        image_keys = list(normalized.image_keys)
        media_refs = list(normalized.media_refs)
        if normalized.raw_type == "post" and not media_refs and not image_keys:
            extra_images, extra_refs = await self._recover_post_media_refs(message_id)
            image_keys += [key for key in extra_images if key not in image_keys]
            media_refs += extra_refs
        for image_key in image_keys:
            _collect(*await self._download_feishu_image(message_id=message_id, image_key=image_key))
        for ref in media_refs:"""

patched = src
for old, new, tag in ((A1_OLD, A1_NEW, "A1"), (A2_ANCHOR, A2_HELPER, "A2a"),
                      (A2B_OLD, A2B_NEW, "A2b"), (B1_ANCHOR, B1_NEW, "B1"), (B2_OLD, B2_NEW, "B2")):
    if old not in patched:
        print(f"❌ 锚点未命中 {tag}"); sys.exit(1)
    patched = patched.replace(old, new, 1)
    print(f"✓ 补丁 {tag} 已应用")
open(COPY, "w", encoding="utf-8").write(patched)
py_compile.compile(COPY, doraise=True)
print(f"✓ 语法检查通过（{len(patched.splitlines())} 行，原 {len(src.splitlines())} 行）")

# ---------- 单测：真实报文 ----------
def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

sys.path.insert(0, "/usr/local/lib/hermes-agent")
for pkg in ("hermes_plugins", "hermes_plugins.feishu_platform"):
    ns = types.ModuleType(pkg); ns.__path__ = []; sys.modules[pkg] = ns

raw = json.load(open("/tmp/msg_raw.json", encoding="utf-8"))
body_content = raw["body"]["content"]
print("\n=== 单测：真实报文（10:13 那条 post） ===")
print("报文键:", list(json.loads(body_content).keys()))

for label, path in (("原版", LIVE), ("补丁版", COPY)):
    m = load_module(path, f"adapter_{label}")
    r = m.parse_feishu_post_payload(json.loads(body_content))
    print(f"  [{label}] media_refs={len(r.media_refs)}  image_keys={len(r.image_keys)}"
          + (f"  → {r.media_refs[0].file_name}" if r.media_refs else ""))
    if label == "补丁版":
        ok = len(r.media_refs) == 1 and r.media_refs[0].file_name.endswith(".xlsx")
        print("  结果:", "✅ PASS" if ok else "❌ FAIL")
        sys.exit(0 if ok else 1)
