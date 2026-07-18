---
name: hermes-web-dashboard
description: Set up and troubleshoot the Hermes Agent web dashboard, including handling Node.js version issues and enabling LAN access
category: software-development
---

# Hermes Web Dashboard Setup and Troubleshooting

## Overview
This skill provides a systematic approach to setting up and troubleshooting the Hermes Agent web dashboard, particularly when encountering common issues like missing frontend builds or Node.js version constraints.

## When to Use
- You want to access the Hermes Agent through a web interface
- The `hermes dashboard` command reports "Web UI frontend not built"
- You encounter Node.js version compatibility issues when trying to build the dashboard
- You need to make the dashboard accessible on a local network
- Standard dashboard startup fails and requires troubleshooting

## Prerequisites
- Hermes Agent v0.9.0 or later installed
- Basic terminal/command line proficiency
- Access to the Hermes installation directory

## Step-by-Step Approach

### 1. Verify Dashboard Command Availability
First confirm the dashboard command exists:
```bash
hermes dashboard --help
```
You should see options for `--port`, `--host`, and `--no-open`.

### 2. Initial Dashboard Startup Attempt
Try starting the dashboard normally:
```bash
hermes dashboard --host 0.0.0.0
```
The `--host 0.0.0.0` binds to all network interfaces for LAN access.

### 3. Troubleshoot "Web UI frontend not built" Error
If you see this error, follow these steps:

#### A. Locate the Web Directory
Find the web frontend files:
```bash
# From Hermes project root
find . -name "web" -type d
# Typically at: ./web
```

#### B. Check for Package.json
Verify the web directory contains a package.json:
```bash
ls -la web/
# Should see package.json, package-lock.json, src/, public/, etc.
```

#### C. Check Node.js Version
Verify your Node.js version meets requirements:
```bash
node --version
# Note the version for compatibility checks
```

#### D. Install Dependencies
Navigate to web directory and install npm packages:
```bash
cd web
npm install
# Expect some engine warnings if Node.js version is below requirements
# These warnings are often non-fatal for development use
```

#### E. Attempt Production Build (Optional)
Try building for production:
```bash
npm run build
```
This may fail if:
- Node.js version is too old (Vite often requires >=20.19.0)
- There are missing native bindings

#### F. Use Development Server as Fallback
If production build fails due to Node.js version constraints:
```bash
# Start development server with explicit host and port
npm run dev -- --host 0.0.0.0 --port 9119
```
Key flags:
- `--host 0.0.0.0`: Binds to all interfaces for LAN access
- `--port 9119`: Matches Hermes dashboard default port
- The double dash `--` passes arguments to the underlying Vite server

### 4. Verify Dashboard Accessibility
Once running, access the dashboard:
- **Locally**: http://localhost:9119 or http://127.0.0.1:9119
- **LAN**: http://[YOUR_MACHINE_IP]:9119
  - Find your IP with: `ip addr show` (Linux) or `ipconfig` (Windows/macOS)
  - Common patterns: 192.168.x.x, 10.0.x.x, or 172.16.x.x

### 5. Manage the Background Process
The dashboard runs as a background process. Manage it with:

#### List all background processes:
```bash
hermes process list
```

#### View dashboard logs:
```bash
hermes process log --session-id [SESSION_ID] --limit 50
```

#### Stop the dashboard:
```bash
hermes process kill --session-id [SESSION_ID]
```

#### Wait for completion notification:
The process will notify when done if started with `notify_on_complete=true`.

## Troubleshooting Guide

### Common Issues and Solutions

**Issue**: "Web UI frontend not built and npm is not available"
- **Solution**: Node.js is installed but frontend assets need building. Follow steps 3D-3F above.

**Issue**: Vite build fails due to Node.js version
- **Symptom**: Error messages like "Vite requires Node.js version 20.19+ or 22.12+"
- **Solution A**: Check if pre-built frontend already exists. The `web_dist/` directory may contain built files from a previous build or installation:
 ```bash
 ls -la hermes_cli/web_dist/
 # Should see: index.html, assets/, favicon.ico, fonts/
 ```
 If these files exist, the `_build_web_ui()` function can be patched to skip the build. 
 In `hermes_cli/main.py`, find the `_build_web_ui` function (around line 2944) and add this check at the beginning after the docstring:
 ```python
 def _build_web_ui(web_dir: Path, *, fatal: bool = False) -> bool:
     """Build the web UI frontend if npm is available.
     ...
     """
     # Check if web_dist already exists with built files
     web_dist = web_dir.parent / "hermes_cli" / "web_dist"
     if (web_dist / "index.html").exists() and (web_dist / "assets").exists():
         return True  # Already built

     if not (web_dir / "package.json").exists():
         return True
 ```
 This allows the dashboard to start immediately without requiring a rebuild when valid frontend assets already exist.
- **Solution B**: Use development server (`npm run dev`) instead of production build.
 Note: Dev server is fine for most use cases; production build offers better performance.

**Issue**: Cannot access dashboard from other devices on LAN
- **Solution**: Ensure you started with `--host 0.0.0.0` (not `127.0.0.1` or `localhost`)
  and check firewall settings allow traffic on the port.

**Issue**: Port already in use
- **Solution**: Either stop the existing process on that port or specify a different port:
  ```bash
  hermes dashboard --host 0.0.0.0 --port 9120
  # or for dev server:
  npm run dev -- --host 0.0.0.0 --port 9120
  ```

**Issue**: Dashboard loads but doesn't connect to Hermes agent
- **Solution**: Verify Hermes agent is running and accessible. The dashboard communicates 
  with the agent through standard Hermes mechanisms.

## Best Practices

1. **LAN Access Always**: When wanting LAN access, always use `--host 0.0.0.0` 
   (or equivalent for dev server: `--host 0.0.0.0`)

2. **Default Port**: Stick to port 9119 unless there's a conflict, as this is what 
   documentation and users expect.

3. **Development vs Production**: 
   - Use development server (`npm run dev`) for flexibility with Node.js versions
   - Use production build (`npm run build` + serve) for better performance 
     when Node.js version allows

4. **Process Management**: Always note the session ID when starting background 
   processes for later management.

5. **Firewall Awareness**: On some systems, you may need to adjust firewall 
   settings to allow incoming connections on the dashboard port.

## Verification Steps
After setup, verify:
- [ ] Dashboard loads in browser at expected address
- [ ] LAN devices can access the dashboard (if desired)
- [ ] Dashboard shows Hermes agent information (sessions, config, etc.)
- [ ] Background process is running and manageable via `hermes process`
- [ ] No critical errors in process logs

## Maintenance
- To update the dashboard after Hermes updates, repeat the build process
- Periodically check for updates to frontend dependencies with `npm update`
- If Node.js version increases sufficiently, consider switching to production build

## Related Hermes Commands
- `hermes dashboard` - Primary dashboard control
- `hermes process list` - Monitor background processes
- `hermes process log` - View dashboard output
- `hermes process kill` - Stop dashboard when needed
- `hermes --version` - Verify Hermes version supports dashboard feature