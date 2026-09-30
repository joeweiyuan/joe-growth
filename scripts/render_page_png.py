#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_page_png.py — 把本地 HTML 渲染成高清全页 PNG，并物理校验"没有被截断"。

为什么存在（2026-09-30 事故）：
  mit-roadmap.html 的 body 固定宽 1680px，但渲染命令用了 --window-size=1280,...
  → 页面右 400px（约 24%）整块被裁掉，发出去才发现。人眼容易漏，故用脚本把关。

用法：
  python3 scripts/render_page_png.py <html路径> <输出png路径> [--dsf 2] [--min-width 1600] [--height 5200]
  python3 scripts/render_page_png.py <png路径> --check-only          # 只校验已有 PNG 是否被截断

退出码：0 = 通过（且已生成/校验）；非 0 = 被截断或渲染失败（禁止发布）。

校验项（任一不过即 FAIL）：
  1. 输出宽度 == 页面 CSS body 宽 × dsf（宽不够 = 右边被裁）
  2. 最右列 & 最左列必须是纯背景色（说明卡片边框都在画面内）
  3. 最底行 & 最上行必须含背景色（说明上下没切到内容）
  4. 非背景内容列的最大 x 必须 <= 宽度 - 2*页面左右留白（卡片右框完整）
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

BG_DEFAULT = (15, 23, 42)  # #0f172a
SNAP_TMP = "/tmp/snap-private-tmp/snap.chromium/tmp"


def parse_body_width(html_path):
    """从 HTML 的 CSS 里抓 body 宽度（px）。找不到返回 None。"""
    src = open(html_path, encoding="utf-8").read()
    m = re.search(r"body\s*\{[^}]*?width\s*:\s*(\d+(?:\.\d+)?)\s*px", src, re.S)
    if m:
        return float(m.group(1))
    m = re.search(r"<body[^>]*style\s*=\s*\"[^\"]*width\s*:\s*(\d+(?:\.\d+)?)\s*px", src)
    return float(m.group(1)) if m else None


def find_shot(name):
    for d in (SNAP_TMP, "/tmp"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    hits = glob.glob(f"/tmp/**/{name}", recursive=True) + glob.glob(f"/root/snap/**/{name}", recursive=True)
    return hits[0] if hits else None


def render(html_path, out_path, dsf, width, height):
    from PIL import Image
    import numpy as np

    width = int(width)
    tmpname = "render_page_png_shot.png"
    for d in (SNAP_TMP, "/tmp"):
        try:
            if os.path.exists(os.path.join(d, tmpname)):
                os.remove(os.path.join(d, tmpname))
        except OSError:
            pass

    prof = "/tmp/cr-prof-render"
    shutil.rmtree(prof, ignore_errors=True)
    cmd = [
        "/snap/bin/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", "--hide-scrollbars", f"--user-data-dir={prof}",
        f"--force-device-scale-factor={dsf}", f"--window-size={width},{height}",
        # ⚠️ 必须传 /tmp/xxx.png：snap 内 /tmp 被映射到私有 tmp（/tmp/snap-private-tmp/snap.chromium/tmp），
        #    传私有 tmp 的绝对路径会写不出去（2026-09-30 踩过）
        f"--screenshot=/tmp/{tmpname}", "file://" + os.path.abspath(html_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("❌ chromium 渲染失败 exit=", r.returncode, r.stderr[-500:])
        return None
    shot = find_shot(tmpname)
    if not shot:
        print("❌ 找不到截图文件")
        return None

    im = Image.open(shot).convert("RGB")
    a = np.array(im)
    bg = np.array(BG_DEFAULT)
    diff = np.abs(a.astype(int) - bg).sum(axis=2)
    rows = (diff > 18).sum(axis=1)
    nz = np.where(rows > 3)[0]
    if len(nz) == 0:
        print("❌ 画面全空")
        return None

    # 内容贴到画面底部 → 页面比视口高，需要更高重渲染
    if int(nz.max()) >= a.shape[0] - 4 and height < 20000:
        new_h = min(20000, int(a.shape[0] / dsf * 1.4) + 400)
        print(f"ℹ️ 内容触底，改用视口高 {new_h} 重渲染")
        return render(html_path, out_path, dsf, width, new_h)

    top = max(0, int(nz.min()) - 20)
    bottom = min(a.shape[0], int(nz.max()) + 21)
    crop = im.crop((0, top, im.width, bottom))
    crop.save(out_path, "PNG", optimize=True)
    print(f"✓ 渲染 {crop.size}  {os.path.getsize(out_path)/1024:.0f}KB  → {out_path}")
    return crop


def check(png_path, expect_width=None, bg=BG_DEFAULT):
    from PIL import Image
    import numpy as np
    ok = True
    im = Image.open(png_path).convert("RGB")
    W, H = im.size
    a = np.array(im)
    b = np.array(bg)
    diff = np.abs(a.astype(int) - b).sum(axis=2)
    colhas = (diff > 18).sum(axis=0)

    # 1) 宽度
    if expect_width and W != expect_width:
        print(f"❌ 宽度 {W} != 期望 {expect_width}（页面被横向裁切）")
        ok = False
    # 2) 左右边列必须是背景
    for name, x in (("最左列", 0), ("最右列", W - 1), ("右-2", W - 2), ("右-5", W - 5)):
        n = int((diff[:, x] > 18).sum())
        if n > 0:
            print(f"❌ {name} (x={x}) 有 {n} 个非背景像素 → 边框/文字贴边，被截断")
            ok = False
    # 3) 上下边行
    for name, y in (("最上行", 0), ("最下行", H - 1)):
        n = int((diff[y, :] > 18).sum())
        if n > 0:
            print(f"❌ {name} (y={y}) 有 {n} 个非背景像素 → 上下被截断")
            ok = False
    # 4) 内容列范围 vs 页面留白
    nzc = np.where(colhas > 3)[0]
    if len(nzc):
        left_pad = int(nzc.min())
        right_pad = int(W - 1 - nzc.max())
        print(f"  留白：左 {left_pad}px / 右 {right_pad}px（内容列 {nzc.min()}–{nzc.max()}）")
        if right_pad < 10:
            print("❌ 右侧留白过小 → 极可能被截断")
            ok = False
    print(("✅ 校验通过：未被截断 " if ok else "❌ 校验失败 ") + f"{png_path} {im.size}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="HTML 路径（渲染）或 PNG 路径（--check-only）")
    ap.add_argument("out", nargs="?", help="输出的 PNG 路径")
    ap.add_argument("--dsf", type=float, default=2)
    ap.add_argument("--height", type=int, default=5200)
    ap.add_argument("--min-width", type=int, default=0, help="渲染宽度下限（CSS px）")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    if args.check_only:
        sys.exit(0 if check(args.target) else 1)

    if not args.out:
        ap.error("渲染模式需要输出 PNG 路径")
    bw = parse_body_width(args.target)
    if bw is None:
        print("⚠️ 未从 CSS 解析到 body width，使用 --min-width 或默认 1680")
        bw = float(args.min_width or 1680)
    width = max(bw, float(args.min_width or 0))
    print(f"📐 页面 body 宽 = {bw:g}px → 渲染窗口宽 {width:g}px × dsf {args.dsf} = {int(width*args.dsf)}px")
    img = render(args.target, args.out, args.dsf, width, args.height)
    if img is None:
        sys.exit(2)
    sys.exit(0 if check(args.out, expect_width=int(width * args.dsf)) else 1)


if __name__ == "__main__":
    main()
