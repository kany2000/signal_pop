# Cronjob Fix: Missing Skills Cause Code-Printing Failure

## The Bug

A weather cronjob was set up but kept outputting raw Python code:
```
<tool_code>
print(skill_view("chinese-city-weather-wttr"))
</tool_code>
```

The `last_status` showed `ok` — the job ran without crashing, but produced wrong output.

## Root Cause

The cronjob was created with a prompt instructing the model to use a skill, but **no skill was actually attached** to the job. Without the skill's tool definitions in context, the model had no way to call the skill — it just printed the code literal.

## Diagnostic Steps

1. **Check the output file** — the smoking gun:
   ```bash
   cat ~/.hermes/cron/output/<job_id>/*.md | tail -50
   ```
   Look for `<tool_code>`, `print(skill_view(...))`, or similar Python code in the output.

2. **Check if skills are attached**:
   ```bash
   cronjob list
   ```
   The `skills` field will be `[]` or missing.

## The Fix

```python
cronjob(
    action="update",
    job_id="<job_id>",
    skills=["chinese-city-weather-wttr"]
)
```

## Prevention

When creating any cronjob that:
- Queries APIs (weather, news, stocks)
- Uses Hermes tools
- Needs specialized skill context

Always attach the skill at creation time:
```python
cronjob(
    action="create",
    name="my_job",
    prompt="...",
    skills=["required-skill"],
    schedule="0 7 * * *"
)
```

## Related

- `chinese-city-weather-wttr` skill — for weather cronjobs
- Cronjob output directory: `~/.hermes/cron/output/<job_id>/`
