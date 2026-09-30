#!/usr/bin/env bash
# 每轮备份（双目的地）
#   ① 本地全量快照 tar.gz（保留 20 份）
#   ② public: joe-growth/knowledge/（脱敏知识库层）→ 供网站/OfferPath 公开参考
#   ③ private: weiwuji-knowledge-base/08-个人成长/少爷/（全量，含 STATE 原文）
# 用法：bash scripts/backup_kb.sh
set -euo pipefail
TS=$(date +%Y%m%d_%H%M)
PROF=/root/.hermes/profiles/joe
REPO=/root/joe-growth
KBREPO=/root/weiwuji-knowledge-base
KB="$KBREPO/08-个人成长/少爷"
BK=/root/backups/joe
mkdir -p "$BK"

echo "=== ① 本地全量快照 $TS ==="
STAGE=$(mktemp -d)
mkdir -p "$STAGE"/{state,skills,repos}
cp "$PROF/STATE.md" "$STAGE/state/" 2>/dev/null || true
cp -r "$PROF/skills/joe-sub-agents" "$STAGE/skills/" 2>/dev/null || true
cp -r "$REPO"/{capabilities,research,admissions,daily-logs,references,milestones.md,awards.md,expense-ledger.md,data.js} "$STAGE/repos/" 2>/dev/null || true
cp "$PROF/cron/jobs.json" "$STAGE/state/" 2>/dev/null || true
tar -czf "$BK/joe_backup_$TS.tar.gz" -C "$STAGE" . && rm -rf "$STAGE"
echo "  → $BK/joe_backup_$TS.tar.gz ($(du -h "$BK/joe_backup_$TS.tar.gz" | cut -f1))"
ls -1t "$BK"/joe_backup_*.tar.gz | tail -n +21 | xargs -r rm -f

echo "=== ② public 脱敏层 → joe-growth/knowledge/ ==="
PK="$REPO/knowledge"; mkdir -p "$PK/skills"
sed -E 's/[0-9]{11}/[已脱敏-手机号]/g; s/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[已脱敏-邮箱]/g; s/oc_[a-z0-9]{20,}/[已脱敏-chatID]/g; s/o9cq[A-Za-z0-9]+/[已脱敏-openid]/g; s/ghp_[A-Za-z0-9]+/[已脱敏-token]/g' \
    "$PROF/STATE.md" > "$PK/STATE_snapshot.md"
for s in "$PROF"/skills/joe-sub-agents/*/; do
  [ -f "$s/SKILL.md" ] || continue
  n=$(basename "$s"); mkdir -p "$PK/skills/$n"; cp "$s/SKILL.md" "$PK/skills/$n/SKILL.md"
done
cat > "$PK/README.md" <<'EOM'
# 📚 Joe 知识库（公开层）
> 自动备份（`scripts/backup_kb.sh`）。本目录：STATE 快照（**已脱敏**）+ 专属技能副本 + README。
> 仓库内其他层：`../capabilities/`（能力包）· `../research/`（研究归档）· `../admissions/`（升学档案）· `../daily-logs/`（成长日志）
> 🔒 **全量备份（含 STATE 原文）在私有仓库** `corinwe/weiwuji-knowledge-base` → `08-个人成长/少爷/`
EOM
echo "  → $PK ($(du -sh "$PK" | cut -f1), $(find "$PK" -type f | wc -l) 文件)"

echo "=== ③ private 全量 → weiwuji-knowledge-base/08-个人成长/少爷/ ==="
if [ -d "$KBREPO/.git" ]; then
  mkdir -p "$KB/skills"
  cp "$PROF/STATE.md" "$KB/STATE.md"
  rm -rf "$KB"/{capabilities,research,admissions,daily-logs,references}
  cp -r "$REPO"/{capabilities,research,admissions,daily-logs,references} "$KB/" 2>/dev/null || true
  for f in milestones.md awards.md expense-ledger.md data.js; do cp "$REPO/$f" "$KB/$f" 2>/dev/null || true; done
  cp "$KBREPO/技能库/skills/joe-sub-agents"/*.md "$KB/skills/" 2>/dev/null || true
  for s in "$PROF"/skills/joe-sub-agents/*/; do
    [ -f "$s/SKILL.md" ] || continue
    n=$(basename "$s"); mkdir -p "$KB/skills/$n"; cp "$s/SKILL.md" "$KB/skills/$n/SKILL.md"
  done
  cat > "$KB/README.md" <<'EOM'
# 👦 少爷（Joe / 魏源）· 全量备份

> **私有全量备份**：由 `joe-growth/scripts/backup_kb.sh` 每轮自动写入
> 上游主库：`joeweiyuan/joe-growth`（公开层）+ `/root/.hermes/profiles/joe/`（本地 STATE/技能）
> 内容：`STATE.md`（原文，未脱敏）· `capabilities/`（能力包）· `research/`（研究归档，含供 OfferPath 参考的数据）· `admissions/`（升学档案）· `daily-logs/`（成长日志）· `milestones/awards/expense-ledger/data.js` · `skills/`（专属技能 12 个）
> ⚠️ 本目录**含敏感信息**，仅限私有仓库；网站（public Pages）**不从本目录取数**
EOM
  echo "  → $KB ($(du -sh "$KB" | cut -f1), $(find "$KB" -type f | wc -l) 文件)"
else
  echo "  ⚠️ 跳过：$KBREPO 非 git 仓库"
fi

echo "=== 完成 ==="
echo "推送 public: cd $REPO && git add -A && git commit -m '...' && git push"
echo "推送 private: cd $KBREPO && git add -A && git commit -m '...' && git push"
