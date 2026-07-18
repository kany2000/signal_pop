# No-sudo CLI Install Recipes

Reusable patterns for installing dev/agent tooling on a headless Linux box where you
have a normal user shell but no root, and where `pipx` is absent.

## Pattern A — Python tool from a git archive (pipx replacement)

Best when the upstream recommends `pipx install <archive.zip>` but pipx is missing.
A dedicated venv gives the same isolation and survives PEP 668.

```bash
python3 -m venv ~/.agent-reach-venv
~/.agent-reach-venv/bin/pip install -q --upgrade pip
~/.agent-reach-venv/bin/pip install "https://github.com/<owner>/<repo>/archive/main.zip"
~/.agent-reach-venv/bin/<tool> --version
```

Real example (Agent Reach v1.5.0):
```bash
python3 -m venv ~/.agent-reach-venv
~/.agent-reach-venv/bin/pip install "https://github.com/Panniantong/agent-reach/archive/main.zip"
~/.agent-reach-venv/bin/agent-reach install --env=auto
```

## Pattern B — Prebuilt binary, no package manager

Best for official release tarballs (gh CLI, etc.) when `apt`/`snap` is unavailable or
explicitly off-limits.

```bash
ARCH=$(uname -m)   # x86_64 -> amd64 ; aarch64 -> arm64
mkdir -p ~/.agent-reach/bin
# derive VER from https://api.github.com/repos/<owner>/<repo>/releases/latest
curl -fsSL "https://github.com/<owner>/<repo>/releases/download/${VER}/<pkg>_${VER#v}_linux_${ARCH}.tar.gz" -o /tmp/t.tar.gz
tar -xzf /tmp/t.tar.gz -C /tmp
cp /tmp/<pkg>_${VER#v}_linux_${ARCH}/bin/<cmd> ~/.agent-reach/bin/<cmd>
ln -sf ~/.agent-reach/bin/<cmd> ~/.local/bin/<cmd>   # ~/.local/bin already on PATH
<cmd> --version
```

Real example (gh CLI v2.96.0, amd64):
```bash
mkdir -p ~/.agent-reach/bin
curl -fsSL "https://github.com/cli/cli/releases/download/v2.96.0/gh_2.96.0_linux_amd64.tar.gz" -o /tmp/gh.tar.gz
tar -xzf /tmp/gh.tar.gz -C /tmp
cp /tmp/gh_2.96.0_linux_amd64/bin/gh ~/.agent-reach/bin/gh
ln -sf ~/.agent-reach/bin/gh ~/.local/bin/gh
gh --version   # -> gh version 2.96.0
```

## Pitfalls

- **Symlink, don't edit shell rc.** Appending `export PATH=...` to `~/.bashrc`/`~/.profile`
  triggers a consent guard and is hard to revert. `~/.local/bin` is on PATH by default on
  most Linux setups; symlink the binary there. This also survives fresh-shell spawns
  (e.g. a tool's own `doctor`/`launcher` that does not source your rc).
- **Long installs go background.** `agent-reach install --channels=all` and any tool that
  downloads a headless browser (~150 MB) needs >600 s — run with background=true +
  notify_on_complete=true. Foreground calls error at the 900 s ceiling.
- **gh on PATH is required for doctor checks.** The `install` step may report "gh CLI
  install failed" (it tries snap/apt) even though the binary works fine once it's on PATH.
  Symlink it and re-run `doctor` to flip the channel to OK.
