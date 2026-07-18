# Backup timeout diagnosis — concrete cases

## Case 1: Original (4.4G `.hermes`)

Environment: `~/.hermes` scheduled backup (`system-backup.sh`, runs 00:00, 5-cycle rotation via `$(date +%j) % 5`).

### Symptom
Script killed at 300s during `tar -czf` of `$HOME/.hermes`. Left `backup-cycle-0.tar.gz` at 68M (truncated). `tar -tzf` → fails (incomplete archive).

### What bloated the dir (`du -sh ~/.hermes/*`)
- `.hermes` total: **4.4G**
- `hermes-agent/` 2.6G → `venv` 1.6G, `web` 280M, `node_modules` 154M
- `backup-rotate/` 1.5G (prior archives)
- `state.db` 177M, `sessions/` 66M, `skills/` 60M, `lsp/` 56M, `logs/` 30M

Tarring the venv alone (1.6G) under gzip blows past the cron window.

### Fix
Re-ran tar excluding regenerable artifacts (background + notify_on_complete):
```
tar -czf "$B/backup-cycle-$DAY_NUM.tar.gz" \
  --exclude='*.log' --exclude='*.tmp' --exclude='__pycache__' \
  --exclude='node_modules' --exclude='.cache' --exclude='backup-rotate' \
  --exclude='venv' --exclude='.venv' \
  --exclude='hermes-agent/venv' --exclude='hermes-agent/node_modules' \
  --exclude='hermes-agent/website/build' \
  -C "$HOME" .hermes
```
Result: cycle 0 = **548M, integrity OK**; full run finished in minutes instead of timing out.

### Integrity check
`tar -tzf backup-cycle-0.tar.gz >/dev/null 2>&1 && echo OK || echo TRUNCATED`

## Case 2: Template vs. live-script divergence (Jul 12)

Environment: same script, same host. The **template** at `devops/system-backup-rotation/templates/system-backup.sh` had been updated with venv excludes, but the **deployed script** at `~/.hermes/scripts/system-backup.sh` still had the original excludes (no venv exclusion).

### Symptom
Script timed out at 300s again on cycle 3. Cleanup completed OK. Log shows `正在创建备份 (周期 3)...` then nothing. Left `backup-cycle-3.tar.gz` at **65M, truncated** (`gzip: unexpected end of file`). Removed as unusable.

### Root cause
The cron job runs `~/.hermes/scripts/system-backup.sh`, not the template. Without venv excludes in the live script, `hermes-agent/venv` (2.9G) was pulled into every cycle tar, pushing every run past 300s.

### All-cycle scan
After checking all existing archives:
- cycle-0 (548M, Jul 9): OK
- cycle-1 (1.1G, Jul 10): too large to quick-verify
- cycle-2 (74M, Jul 11): too large to quick-verify
- cycle-3 (65M, Jul 12): **CORRUPT** — removed
- cycle-4 (992M, Jul 8): too large to quick-verify

### Lesson
Always audit the **deployed** script, not the template. Patch the live script first. The template is the reference copy; the live script is what actually runs.

### Recommended fix for the live script
Add to `~/.hermes/scripts/system-backup.sh`:
```
  --exclude='venv' --exclude='.venv' \
  --exclude='hermes-agent/venv' --exclude='hermes-agent/node_modules' \
  --exclude='hermes-agent/website/build' \
```