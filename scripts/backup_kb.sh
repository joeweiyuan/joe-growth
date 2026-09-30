#!/usr/bin/env bash
# 每轮备份：① 本地全量快照(tar.gz) ② 知识库层同步到 joe-growth（脱敏）
# 用法：bash scripts/backup_kb.sh
set -euo pipefail
TS=$(date +%Y%m%d_%H%M)
PROF=/root/.hermes/profiles/joe
REPO=/root/joe-growth
BK=/root/backups/joe
mkdir -p "$BK"

echo "=== ① 本地全量快照 $TS ==="
STAGE=$(mktemp -d)
mkdir -p "$STAGE"/{state,skills,repos}
cp "$PROF/STATE.md" "$STAGE/state/" 2>/dev/null || true
cp -r "$PROF/skills/joe-sub-agents" "$STAGE/skills/" 2>/dev/null || true          # 我的专属技能
cp -r "$REPO"/{capabilities,research,admissions,daily-logs,milestones.md,awards.md,expense-ledger.md,data.js} "$STAGE/repos/" 2>/dev/null || true
cp "$PROF/cron/jobs.json" "$STAGE/state/" 2>/dev/null || true                      # cron 定义
tar -czf "$BK/joe_backup_$TS.tar.gz" -C "$STAGE" . && rm -rf "$STAGE"
echo "  → $BK/joe_backup_$TS.tar.gz ($(du -h "$BK/joe_backup_$TS.tar.gz" | cut -f1))"
ls -1t "$BK"/joe_backup_*.tar.gz | tail -n +21 | xargs -r rm -f    # 保留最近 20 份

echo "=== ② 知识库层（脱敏）同步 → joe-growth/knowledge ==="
KB="$REPO/knowledge"; mkdir -p "$KB/skills"
# STATE 快照：脱敏邮箱/手机号/微信ID/cron ID
sed -E 's/[0-9]{11}/[已脱敏-手机号]/g; s/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[已脱敏-邮箱]/g; s/oc_[a-z0-9]{20,}/[已脱敏-chatID]/g; s/o9cq[A-Za-z0-9]+/[已脱敏-openid]/g; s/ghp_[A-Za-z0-9]+/[已脱敏-token]/g' \
    "$PROF/STATE.md" > "$KB/STATE_snapshot.md"
for s in "$PROF"/skills/joe-sub-agents/*/; do
  [ -f "$s/SKILL.md" ] || continue
  n=$(basename "$s"); mkdir -p "$KB/skills/$n"; cp "$s/SKILL.md" "$KB/skills/$n/SKILL.md"
done
cat > "$KB/README.md" <<'EOM'
# 📚 Joe 知识库（Knowledge Base）
> 每轮自动备份（`scripts/backup_kb.sh`）。本目录含：STATE 快照（已脱敏）+ 专属技能副本。
> 仓库内其他知识层：`../capabilities/`（能力包）· `../research/`（研究归档）· `../admissions/`（升学档案）· `../daily-logs/`（成长日志）
> 完整含敏感信息的全量备份保存在服务器本地 `~/backups/joe/`（不进公开仓库）。
EOM
echo "  → $KB ($(du -sh "$KB" | cut -f1), $(find "$KB" -type f | wc -l) 文件)"
echo "=== 完成。推送请执行：cd $REPO && git add -A && git commit -m '📚 备份+知识库同步' && git push ==="
