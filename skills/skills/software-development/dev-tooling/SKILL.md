---
name: dev-tooling
description: Install, upgrade, check versions, and resolve dependency conflicts for developer CLI tools (npm global packages, pip packages, MCP servers, language runtimes).
platforms: [linux, macos, windows]
---

# Dev Tooling Setup & Maintenance

## Playwright Browser Download Timeout

`playwright install chromium` downloads ~175MB. On slower connections can timeout at 120-300s.

**Symptoms:**
- Error: `Executable doesn't exist at /home/kan/.cache/ms-playwright/chromium-...`
- Download hangs at X% for minutes

**Solutions (try in order):**

1. **Install only chromium** (faster than all 4 browsers):
   ```bash
   playwright install chromium
   ```

2. **Use system Chrome** (skip Playwright's browser download):
   ```python
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       b = p.chromium.launch(channel='chrome', ...)  # uses system google-chrome
   ```
   Requires `google-chrome-stable`. Usually faster and avoids the ~175MB download.

3. **Resume interrupted download**:
   ```bash
   rm -rf ~/.cache/ms-playwright/chromium-*
   playwright install chromium
   ```

4. **Set explicit timeout env var** (for pip install that triggers browser download):
   ```bash
   PLAYWRIGHT_BROWSERS_DOWNLOAD_TIMEOUT=500000 pip install notebooklm-py[browser]
   ```

## Install a Global CLI Tool

### npm global
```bash
npm i -g <package>            # install
npm update -g <package>       # upgrade
npm list -g --depth=0          # list installed
```
If `npm list` hangs or version mismatch with binary report, check binary location:
```bash
which <cmd>
```
If pip-installed package shadows an npm package (e.g. two different hermes-agent paths), re-install cleanly in the right venv.

### pip / Python packages
```bash
pip install <package>              # install
pip install --upgrade <package>    # upgrade
pip show <package> | grep Version  # version
pip list | grep <package>          # quick check
```
Always upgrade inside the project venv, not globally:
```bash
source .venv/bin/activate
pip install --upgrade <package>
```

### Version mismatch detection (common pitfall)
Tools often report different versions from different sources. Always verify by:
1. Reading installed package metadata: `pip show <pkg> | grep Version`
2. Reading the binary's own version: `hermes --version` or `codegraph --version`
3. Reading git HEAD tag: `git describe --tags`
All three should agree; if not, reinstall cleanly.

### Dependency conflict awareness
`pip install --upgrade` may produce dependency conflicts (e.g. `moviepy 2.2.1 requires pillow<12.0`). These are warnings, not errors — installation still succeeds. Only intervene if the conflicting package is actually imported at runtime.

## Install an npm-based CLI (no Node.js required)

Many modern CLI tools (CodeGraph, etc.) bundle their own Node runtime:
```bash
npm i -g @publisher/package-name   # installs binary + bundled runtime
```
No need to have Node.js installed on the target system.

## Verify a Tool Works

After install/upgrade:
```bash
<cmd> --version
<cmd> status   # or equivalent health check
```
For index-based tools (CodeGraph), verify DB exists and stats look right:
```bash
<cmd> status   # shows files/nodes/edges counted
```

## Upgrade Workflow

```bash
# 1. Check current
<cmd> --version

# 2. Check available (if tool supports it)
<cmd> upgrade --check

# 3. Upgrade
npm update -g <pkg>    # for npm global
pip install --upgrade <pkg>   # for pip

# 4. Verify
<cmd> --version
```

## Common Patterns

### pip upgrade with dependency conflicts
Run anyway — warnings are informational. Only fix if runtime import errors appear.

### npm global path issues
After `npm i -g`, new terminal may be needed for PATH to pick up the binary. Or run via `npx <pkg>` without install.

### Version mismatch between pip and git
If `pip show` and `hermes --version` disagree, the pip package was installed in a different venv than the git checkout is using. Reinstall in the correct venv.

## Headless / No-sudo Installs

When `pipx` is missing, a dedicated venv is the drop-in replacement for a pipx-style
single-tool install. Let the tool's own bootstrap be the authority, then run its CLI
from that venv:

```bash
python3 -m venv ~/.agent-reach-venv
source ~/.agent-reach-venv/bin/activate
pip install https://github.com/<owner>/<repo>/archive/main.zip   # sdist/wheel URL
~/.agent-reach-venv/bin/<tool> --version
```

For a prebuilt CLI binary (e.g. gh CLI, when the installer can't apt/snap), download the
official tarball, extract, copy the binary into a tool dir, and **symlink into an
already-on-PATH user dir** rather than editing shell rc:

```bash
mkdir -p ~/.agent-reach/bin
curl -fsSL <release-url>.tar.gz -o /tmp/t.tar.gz
tar -xzf /tmp/t.tar.gz -C /tmp
cp /tmp/<pkg>/bin/<cmd> ~/.agent-reach/bin/<cmd>
ln -sf ~/.agent-reach/bin/<cmd> ~/.local/bin/<cmd>   # ~/.local/bin is already on PATH
<cmd> --version
```

The dedicated venv path (`~/.agent-reach-venv/bin/<tool>`) also survives PEP 668
(externally-managed-environment) because it's an isolated venv, not the system Python.

### Pitfall — do NOT edit shell profile to set PATH
Appending `export PATH=...` to `~/.bashrc` / `~/.profile` trips a consent guard and is
messier to undo. Prefer symlinking the binary into an existing PATH dir (`~/.local/bin`
on Linux is almost always present and on PATH). A symlink also works when the tool's
`doctor`/launcher spawns a fresh shell that does not source your rc.

## References

- `references/codegraph-setup.md`
- `references/external-mcp-server-setup.md`
- `references/no-sudo-cli-install.md` — no-sudo prebuilt-binary + venv install recipes (gh CLI, pipx-as-venv) — CodeGraph-specific init workflow and benchmark data
- `references/external-mcp-server-setup.md` — Installing binary MCP servers via install.sh + registering with Hermes (`hermes mcp add --command`)