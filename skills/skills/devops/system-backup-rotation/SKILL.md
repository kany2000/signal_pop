---
name: system-backup-rotation
description: Run, debug, and harden scheduled system backup + cleanup (rotation) scripts. Covers the #1 failure mode — a backup tar that never finishes within the cron/terminal window and leaves a truncated (unreadable) archive.
---

# system-backup-rotation

Run, debug, and harden scheduled system backup + cleanup (rotation) scripts. Covers the #1 failure mode: a backup tar that never finishes within the cron/terminal window and leaves a truncated (unreadable) archive.

## When to use
- Task runs a scheduled backup/cleanup script (e.g. `~/.hermes/scripts/system-backup.sh`).
- Backup tar times out (process killed, `exit 124`), or the archive is left truncated.
- You must verify a backup archive is actually complete before trusting it.

## The core trap
Backup scripts that `tar -czf` an entire home/config dir (e.g. `~/.hermes`) silently pull in **regenerable, gigabyte-scale artifacts**: Python virtualenvs (`venv/`/`.venv/`, ~1.6G), `node_modules/` (~150M+), build dirs. gzip over those routinely **exceeds the 300s cron / terminal foreground timeout**, the process is killed, and the archive is left truncated (unreadable). These artifacts are reinstallable from requirements/lockfiles — never back them up.

## Workflow
1. **Run the script.** If it times out, note where it died. Cleanup (apt/tmp/cache/logs) usually finishes first; the `tar` step is the slow one.
2. **Read the script** to see what it tars and whether `set -e` + `|| true` masks failures.
3. **Audit sizes** to find the bloat:
   `du -sh <dir>/* 2>/dev/null | sort -rh | head -20`
4. **Exclude regenerable artifacts** from the tar command (see `templates/system-backup.sh`). Add `--exclude='venv' --exclude='.venv' --exclude='node_modules'` plus any nested copies like `hermes-agent/venv`.
5. **Patch the LIVE script** — not just the template. The deployed script at `~/.hermes/scripts/system-backup.sh` is what the cron job actually runs. The template is a reference; the real script is the one that executes. Apply the same excludes to the real script.
6. **Re-run in background** if the full tar may exceed the window: terminal `background=true, notify_on_complete=true`. Do NOT rely on a foreground call past ~300s (config caps foreground; some allow 600s).
7. **Verify integrity — always.** `set -e` + `|| true` hides tar failures:
   `tar -tzf "$ARCHIVE" >/dev/null 2>&1 && echo OK || echo TRUNCATED`
8. **Check all cycle archives** — not just the current one. A previous cycle may have been corrupted during a prior timeout and gone undetected.
   ```
   for f in ~/.hermes/backup-rotate/backup-cycle-*.tar.gz; do echo -n "$(basename $f): "; tar -tzf "$f" >/dev/null 2>&1 && echo "OK" || echo "TRUNCATED"; done
   ```

## Pitfalls
- `TAR_EXIT=1` is usually a **warning** (file changed/deleted mid-read), NOT corruption. Trust `tar -tzf` readability over the exit code.
- A truncated archive still reports a `du` size — size alone proves nothing. Always `tar -tzf`.
- `rm -rf /tmp/*` in cleanup is fine in a maintenance window but kills other processes' temp files; acceptable for scheduled jobs.
- Foreground terminal calls cap at ~300s; a full `.hermes`-scale tar needs `background=true` + `notify_on_complete=true`.
- **Do NOT redirect the wrapper's stdout to `/tmp/*.log`.** The script's own `rm -rf /tmp/*` cleanup step deletes that log mid-run, so you lose all status the moment cleanup fires. Use the script's internal log (`~/.hermes/backup-rotate/backup.log`) as the source of truth instead of your wrapper log. If you must capture a wrapper log, write it outside `/tmp` (e.g. `/home/kan/backup-run.log`) or tail the script's internal log to verify completion.

## Reference
- `references/backup-timeout-diagnosis.md` — concrete case study: 4.4G `.hermes`, what bloated it, exact excluded paths, verification output.

## Template
- `templates/system-backup.sh` — robust rotating backup with regenerable-dir excludes + `tar -tzf` integrity gate baked in.
