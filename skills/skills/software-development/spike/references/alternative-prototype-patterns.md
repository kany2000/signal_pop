# Alternative Prototype Patterns

These are the two branches of the older, lighter prototype skill. Use them as specialized sub-patterns when they fit better than the GSD-style spike above.

## Logic Prototype Branch

When the question is **"does this logic / state model feel right?"** — use this branch instead of the full spike workflow.

**Use when:**
- "I'm not sure if this state machine handles the edge case where X then Y."
- "Does this data model actually let me represent the case where..."
- User wants to **press buttons and watch state change**.

**What to build:** A small interactive terminal app that exposes the state model. Keep the logic pure (reducer/state-machine/function set) in a portable module; wrap it in a throwaway TUI shell.

**Key rules:**
- One directory per spike. One command to run.
- Isolate logic in a portable module — the TUI shell is throwaway, the logic module is not.
- Lightweight TUI: clear screen each tick, pretty-print full state, keyboard shortcuts at bottom.
- No tests, no real database (in-memory only), no generalisation.
- Keep logic and TUI separate — the reducer/state-machine must not import console.log, prompts, or terminal escapes.

**Anti-patterns:**
- Adding tests (a prototype that needs tests is no longer a prototype)
- Wiring TUI shell to real mutations (read-only is fine)
- Generalising beyond the one question

## UI Prototype Branch

When the question is **"what should this look like?"** — use this branch instead of the full spike workflow.

**Use when:**
- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- Any scenario where the user would otherwise spend time comparing vague mockups in their head.

**What to build:** Several radically different UI variants on one route, switchable via URL search param (`?variant=A`).

**Key rules:**
- Default 3 variants; max 5. Must differ structurally, not just in colour or copy.
- Fit the project's component library/styling system.
- Sub-shape A (preferred): variants on an existing route via `?variant=` param.
- Sub-shape B (last resort): a throwaway route `/prototype/<name>`.
- Floating switcher bar at the bottom: left/right arrows + variant label. Hidden in production builds.
- Delete variants and switcher after the winner is chosen.

**Anti-patterns:**
- Variants that differ only in colour (that's a tweak, not a prototype)
- Sharing too much layout between variants (each should be independently discardable)
- Promoting variant code directly to production without re-implementing correctly
