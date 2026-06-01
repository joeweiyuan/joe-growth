#!/usr/bin/env python3
"""
子焘记 GitHub Pages 部署脚本
将 joe-growth-tracker 的最新内容同步到 GitHub Pages 网站
"""
import subprocess, os, json, shutil, glob
from datetime import datetime

REPO_DIR = "/root/joe-growth"
TRACKER_DIR = "/root/joe-growth-tracker"
BRANCH_MAIN = "main"
BRANCH_PAGES = "gh-pages"

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or REPO_DIR)
    if r.returncode != 0:
        print(f"⚠️  {cmd}: {r.stderr.strip()}")
    return r.stdout.strip()

# Step 1: copy latest tracker content into repo as reference
print("📋 同步成长轨迹内容...")
ref_md = os.path.join(REPO_DIR, "references")
os.makedirs(ref_md, exist_ok=True)

# Copy curated narratives
for f in glob.glob(os.path.join(TRACKER_DIR, "curated", "*.md")):
    shutil.copy2(f, os.path.join(ref_md, os.path.basename(f)))
    print(f"  复制 curated/{os.path.basename(f)}")

# Copy themes
for f in glob.glob(os.path.join(TRACKER_DIR, "themes", "*.md")):
    shutil.copy2(f, os.path.join(ref_md, os.path.basename(f)))
    print(f"  复制 themes/{os.path.basename(f)}")

# Copy milestones
if os.path.exists(os.path.join(TRACKER_DIR, "milestones.md")):
    shutil.copy2(os.path.join(TRACKER_DIR, "milestones.md"), os.path.join(ref_md, "milestones.md"))
    print("  复制 milestones.md")

# Copy daily logs
daily_target = os.path.join(REPO_DIR, "daily-logs")
os.makedirs(daily_target, exist_ok=True)
for f in glob.glob(os.path.join(TRACKER_DIR, "daily-logs", "*.md")):
    shutil.copy2(f, os.path.join(daily_target, os.path.basename(f)))
    print(f"  复制 daily-logs/{os.path.basename(f)}")

# Copy growth_index.json
if os.path.exists(os.path.join(TRACKER_DIR, "growth_index.json")):
    shutil.copy2(os.path.join(TRACKER_DIR, "growth_index.json"), os.path.join(REPO_DIR, "growth_index.json"))
    print("  复制 growth_index.json")

# Step 2: git add & commit
print("\n📦 提交更改...")
run(f"git add -A")
diff = run("git diff --cached --stat")
if diff:
    run(f'git commit -m "📝 自动同步 {datetime.now().strftime("%Y-%m-%d %H:%M")}"')
    print(f"  已提交: {diff}")

    # Step 3: push main branch
    print("\n🚀 推送 main 分支...")
    result = run("git push origin main")
    print(f"  {result}")

    # Step 4: deploy gh-pages (checkout orphan, copy index.html, push)
    print("\n🌐 部署 gh-pages...")
    run(f"git branch -D {BRANCH_PAGES} 2>/dev/null || true")
    run(f"git checkout --orphan {BRANCH_PAGES}")
    run("git rm -rf . 2>/dev/null || true")
    # Copy just the site files
    for f in ["index.html", "README.md"]:
        src = os.path.join(REPO_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(REPO_DIR, f))
    run("git add index.html README.md")
    run(f'git commit -m "deploy: {datetime.now().strftime("%Y-%m-%d %H:%M")}"')
    run(f"git push origin {BRANCH_PAGES} --force")
    run("git checkout main")
    print("✅ gh-pages 部署完成！")
else:
    print("  无变更，跳过推送")
    run("git checkout main 2>/dev/null || true")

print(f"\n✅ 同步完成！")
print(f"🌐 https://joeweiyuan.github.io/joe-growth/")
