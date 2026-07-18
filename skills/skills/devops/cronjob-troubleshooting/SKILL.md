---
name: cronjob-troubleshooting
description: Systematic approach to debug failing cronjobs using the cronjob CLI
trigger: When a scheduled cronjob is failing, not running, or producing unexpected results
---

## Steps

1. **Check cronjob status**
   ```bash
   cronjob list
   ```
   Look for the job and note its `last_status`, `last_run_at`, and `next_run_at`.

2. **Inspect recent logs**
   ```bash
   cronjob logs [job_id]
   ```
   Check for error messages, connection failures, timeouts, or exceptions. Use `-n` to limit lines: `cronjob logs [job_id] -n 50`.

3. **Manually trigger the job**
   ```bash
   cronjob run [job_id]
   ```
   This runs the job immediately, bypassing the schedule. Use `-f` to run in foreground if supported.

4. **Wait and verify execution**
   - Check `cronjob list` again to see if `last_run_at` updated.
   - If still not updated, wait a few seconds and re-check (some jobs may have processing delay).

5. **Examine the job output**
   - Locate the output file (usually in `/var/cronjobs/[job_id]/output.*` or as defined by the job config).
   - Read the latest output: `head -n 50 /var/cronjobs/[job_id]/output.json` or similar.
   - Validate the content structure and data.

6. **Diagnose the cause** based on logs and output:
   - **Connection error**: Network/API unreachable; check internet access, proxy, firewall, API endpoint availability.
   - **Timeout**: Job taking too long; consider increasing timeout or optimizing.
   - **Permission error**: Check file/directory permissions.
   - **Missing dependencies**: Verify required tools/libraries are installed.
   - **Configuration issue**: Review job parameters, environment variables.

7. **Apply a fix**:
   - For temporary network issues, manual rerun often resolves.
   - For persistent issues, adjust retry count, timeout, or schedule.
   - If API rate limiting, implement caching or exponential backoff.

## Pitfalls

- The `last_status` in `cronjob list` may be stale; always check logs for actual error details.
- Manual triggers may succeed even if scheduled runs fail due to differing environment (e.g., network conditions at different times).
- Some cronjob systems store logs separately; ensure you are viewing the correct job's logs.
- **Job outputs raw Python/tool code instead of results**: The job is missing required `skills`. Without skills attached, the model has no tool context and falls back to printing code. Fix: `cronjob update <job_id> --skills "skill-name"`. Always attach skills at job creation when the job needs API calls or Hermes tools.
- Connection errors may be transient; consider increasing retry count or adding circuit breaker logic.
- **venv vs system Python path**: If a Python script works interactively but fails in cron with `ModuleNotFoundError`, the cron subprocess may be resolving a different `python3` than your shell. Check `which python3` in your terminal vs the cron environment's Python. The hermes-agent venv Python (`/home/kan/.hermes/hermes-agent/venv/bin/python3`) has all dependencies; system Python (`/usr/bin/python3`) may not. Always use absolute paths in cron job scripts: `/home/kan/.hermes/hermes-agent/venv/bin/python3` or ensure the script uses `#!/home/kan/.hermes/hermes-agent/venv/bin/python3`.
- **Output file path confusion**: Cron output files saved locally may not match where the script actually wrote them. Check both `~/.hermes/cron/output/<job_id>/` (cron agent output) and the script's actual `$OUTPUT_DIR` (the working directory the script writes to).
- **Timeout may leave corrupted/partial output artifacts**: A `Command timed out` exit_code=124 means the process was killed mid-operation. The script may have written an incomplete file before dying (e.g., a partial `.tar.gz` that `gzip -t` will report as "unexpected end of file"). After any timeout, always verify output file integrity explicitly:
  ```bash
  gzip -t /path/to/output.tar.gz
  tar -tzf /path/to/output.tar.gz | head -5  # list contents to confirm completeness
  ```
  A file being present does NOT mean it's valid — compare file size against historical baseline.
- **Historical baseline for file sizes**: When verifying backup outputs, know what "normal" looks like (e.g., ~640MB for a full hermes backup vs 317MB for a truncated one). If a backup shrinks dramatically between runs without explanation, suspect truncation.
- **Python module available in shell but not in cron**: If `pip show <module>` shows it installed but `python3 -c "import <module>"` fails in cron context, the cron subprocess is using a different Python interpreter. Run `python3 -c "import sys; print(sys.executable)"` to confirm which Python is being used.
- **Schedule misalignment with upstream producers**: Cron jobs that consume files produced by other agents/processes must run AFTER the upstream output is ready. Example: if "马小v" produces videos at ~10:00, a 08:00 cron will always find nothing; 10:30 works. Always align cron timing with the actual delivery SLA of upstream producers, not just "morning" or "daily". When multiple agents coordinate (虾小图出稿 → 马小v出片 → 分发), map the full chain and set each cron 30–60 min after its dependency.

## Verification

After applying a fix:
1. Run `cronjob run [job_id]` again.
2. Confirm output is valid and contains expected data.
3. Check `cronjob list` to ensure status reflects success.
4. Monitor the next scheduled run to confirm stability.