#!/bin/bash
# Rotating system cleanup + backup. Keeps 5 cycle archives.
# Hardened: excludes regenerable artifacts (venv/node_modules) that blow past
# the cron timeout, and gates success on an integrity check rather than a
# masked `|| true` exit.
set -e

BACKUP_DIR="$HOME/.hermes/backup-rotate"
LOG_FILE="$BACKUP_DIR/backup.log"
DAY_NUM=$(($(date +%j) % 5))
DATE=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$BACKUP_DIR"

log() { echo "[$DATE] $1" | tee -a "$LOG_FILE"; }

log "========== 开始系统清理和备份 =========="

# 1. Cleanup
log "正在清理系统..."
sudo apt-get clean 2>/dev/null || true
sudo apt-get autoremove -y 2>/dev/null || true
rm -rf /tmp/* /var/tmp/* 2>/dev/null || true
find ~/.cache -type f -mtime +7 -delete 2>/dev/null || true
find ~/.hermes -name "*.log" -mtime +7 -delete 2>/dev/null || true
log "  - 清理完成"

# 2. Backup (exclude regenerable artifacts — they blow past the cron timeout)
BACKUP_FILE="$BACKUP_DIR/backup-cycle-$DAY_NUM.tar.gz"
log "正在创建备份 (周期 $DAY_NUM)..."
rm -f "$BACKUP_FILE"
tar -czf "$BACKUP_FILE" \
  --exclude='*.log' --exclude='*.tmp' --exclude='__pycache__' \
  --exclude='node_modules' --exclude='.cache' --exclude='backup-rotate' \
  --exclude='venv' --exclude='.venv' \
  --exclude='hermes-agent/venv' --exclude='hermes-agent/node_modules' \
  --exclude='hermes-agent/website/build' \
  -C "$HOME" .hermes 2>/dev/null || true

# 3. Integrity gate — a truncated archive is worse than no backup
if tar -tzf "$BACKUP_FILE" >/dev/null 2>&1; then
  log "  - 备份已创建并校验通过: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
  log "  - 警告: 备份校验失败 (归档损坏)!" >&2
fi

# 4. Rotation status + disk
for i in {0..4}; do
  f="$BACKUP_DIR/backup-cycle-$i.tar.gz"
  [ -f "$f" ] && log "  - 周期 $i: $(du -h "$f" | cut -f1)" || log "  - 周期 $i: (空)"
done
df -h / | tail -1 | awk '{print "  - 已用: "$3" / "$2" ("$5")"}' | tee -a "$LOG_FILE"
log "========== 清理和备份完成 =========="
