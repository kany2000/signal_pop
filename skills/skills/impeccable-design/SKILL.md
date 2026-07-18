---
name: impeccable-design
description: "Frontend design skill adapted from pbakaus/impeccable. Essential when user asks to design/redesign a website, landing page, dashboard, product UI, or any frontend interface. Covers typography, color, layout, motion, interaction, UX copy, anti-pattern avoidance, and AI-slop detection."
related_skills: [google-workspace, nano-pdf, ocr-and-documents]
---

# Impeccable Design (Hermes Port)

> **Source:** [pbakaus/impeccable](https://github.com/pbakaus/impeccable) — 33.6k ★, Apache 2.0
> 23 commands × 7 domain references × 27 deterministic anti-pattern rules

Use this skill whenever the user asks to design, redesign, critique, polish, or improve a frontend interface. Loads the same anti-pattern rules and design guidance that make Impeccable the leading design skill for AI coding agents.

---

## Design Guidance

### Color

- **Verify contrast.** Body text ≥4.5:1 against background; large text (≥18px or bold ≥14px) ≥3:1. Placeholder text needs 4.5:1 too. The most common failure: muted gray body on tinted near-white.
- **No gray text on colored backgrounds.** Use a darker shade of the background's own hue, or transparency of the text color.
- **Use OKLCH** for all color definitions.
- **Cream/sand/beige body bg is the saturated AI default of 2026.** Don't default to warm-tinted near-white. Pick: a saturated brand color as body, true off-white at chroma 0, or darker mid-tone tinted neutral.
- **Tinted neutrals:** add 0.005–0.015 chroma toward the brand's hue, not default-toward-warm.
- **Dark vs light is not a default.** Write one sentence of physical scene (who uses this, where, under what light). If the sentence doesn't force the answer, it's not concrete enough.
- **Pick a color strategy** before picking colors:
  - *Restrained*: tinted neutrals + one accent ≤10%
  - *Committed*: one saturated color carries 30–60% of surface
  - *Full palette*: 3–4 named roles, each deliberate
  - *Drenched*: the surface IS the color

### Typography

- **Body line length:** 65–75ch
- **Hierarchy:** ≥1.25 ratio between scale steps
- **Font family count:** max 3 (display + body + optional mono)
- **Font pairing:** pair on contrast axis (serif + sans, geometric + humanist), not similar-but-not-identical
- **No all-caps body copy.** Reserve for short labels (≤4 words) and badges
- **Hero display ceiling:** `clamp()` max ≤6rem (~96px)
- **Display letter-spacing floor:** ≥ -0.04em
- Use `text-wrap: balance` on h1–h3, `text-wrap: pretty` on long prose

**Reflex-reject fonts** (training-data defaults to avoid): Fraunces · Newsreader · Lora · Crimson · Playfair Display · Cormorant · Syne · IBM Plex * · Inter · DM * · Outfit · Plus Jakarta Sans · Instrument * · Space *

### Layout

- Vary spacing for rhythm
- **Cards are the lazy answer.** Nested cards are always wrong
- Flexbox for 1D, Grid for 2D
- For responsive grids: `repeat(auto-fit, minmax(280px, 1fr))`
- Build a semantic z-index scale. Never arbitrary 999/9999

### Motion

- Motion must be intentional, not an afterthought
- Don't animate CSS layout properties unless truly needed
- Ease out with exponential curves (quart/quint/expo). **No bounce, no elastic.**
- Every animation needs `@media (prefers-reduced-motion: reduce)` alternative
- Reveal animations must enhance an already-visible default — don't gate content on a class-triggered transition
- Premium motion palette: blur, backdrop-filter, clip-path, mask, shadow/glow

### Interaction

- Dropdowns inside `overflow: hidden` containers will be clipped — use `<dialog>` / popover API or portal
- Never animate `<img>` elements on hover (adds no information, reads as "AI animated this because it could")

### UX Copy

- Every word earns its place. No restated headings, no intros that repeat the title
- **No em dashes.** Use commas, colons, semicolons, periods
- **No marketing buzzwords:** streamline/empower/supercharge/leverage/unleash/seamless/next-generation/cutting-edge
- Button labels: verb + object ("Save changes" beats "OK")
- Link text needs standalone meaning ("View pricing plans" beats "Click here")
- **No aphoristic-cadence body copy** — serious statement followed by punchy short negation

## Absolute Bans (Match-and-Refuse)

If you're about to write any of these, rewrite with different structure:

1. **Side-stripe borders** — `border-left`/`border-right` >1px as accent on cards
2. **Gradient text** — `background-clip: text` + gradient
3. **Glassmorphism as default** — blurs and glass cards decoratively
4. **Hero-metric template** — big number + small label + stats + gradient accent
5. **Identical card grids** — same-sized cards with icon+heading+text
6. **Tiny uppercase tracked eyebrow above EVERY section** ("ABOUT" "PROCESS" "PRICING") — the 2023-era AI scaffold
7. **Numbered section markers as default scaffolding** (01/02/03)
8. **Text overflow** on tablet/mobile — test heading at every breakpoint

## AI Slop Test

If someone could look at this interface and say "AI made that" without doubt, it's failed.

**First-order check:** If someone could guess the theme+palette from the category alone, it's the first training-data reflex.

**Second-order check:** If someone could guess the aesthetic from category-plus-anti-references (e.g. "AI workflow tool that's not SaaS-cream → editorial-typographic"), it's the trap one tier deeper. Rework until both answers are not obvious.

## Command Reference

When the user asks to design/improve something, map their intent to one of these commands and load the matching `reference/<command>.md`:

| Intent | Command | What it does |
|--------|---------|--------------|
| Build full feature | `craft` | Shape-then-build end-to-end |
| Plan before coding | `shape` | Plan UX/UI before code |
| Design critique | `critique` | UX review: hierarchy, clarity, emotional resonance |
| Technical audit | `audit` | a11y, performance, responsive checks |
| Final polish | `polish` | Quality pass before shipping |
| Make bolder | `bolder` | Amplify bland designs |
| Make quieter | `quieter` | Tone down aggressive designs |
| Strip to essence | `distill` | Remove complexity |
| Production-hardening | `harden` | Errors, i18n, edge cases |
| Onboarding/empty states | `onboard` | First-run flows, activation paths |
| Add motion | `animate` | Purposeful animation |
| Add color | `colorize` | Strategic color to monochrome UIs |
| Fix typography | `typeset` | Font hierarchy and sizing |
| Fix layout | `layout` | Spacing, rhythm, visual hierarchy |
| Delight | `delight` | Personality and memorable touches |
| Extreme effects | `overdrive` | Technically extraordinary effects |
| Fix copy | `clarify` | UX copy, labels, error messages |
| Responsive | `adapt` | Multi-device adaptation |
| Performance | `optimize` | UI performance fixes |
| Visual iteration | `live` | In-browser variant exploration |
| Brand assets | `brand` | Generate marketing/social images with Pillow (Buy Me a Coffee covers, GitHub previews, banners) — see `references/brand-assets.md` |
| Project setup | `init` | Gather design context, write PRODUCT.md/DESIGN.md |

## Flow

When the user says "design X" or similar:

1. **Determine register:** brand (design IS product: landing page, portfolio, marketing) vs product (design SERVES product: dashboard, app UI, tool)
2. **Read brand.md or product.md** — non-optional. Each has register-specific rules, bans, and permissions
3. **Define physical scene:** Write one sentence — who uses this, where, under what light, in what mood. This forces dark/light choice, not default
4. **Pick brand voice words:** 3 concrete physical-object words (not "modern/elegant"). Used to select fonts below
5. **Identify command & load its reference:** Map user's intent (craft/shape/critique/audit/polish etc.) and read the matching `reference/<command>.md`
6. **Shape before build:** If building from scratch (`craft`), first run a `shape` phase — present UX/UI plan with visual direction, palette proposal, and font picks. **Get user confirmation before any code.** The only exception is a very brief one-screen request where the user already specified all direction
7. **Font selection:** Check reflex-reject list. Browse with the 3 brand voice words. Reject the first pick if it "looks designy"
8. **Color strategy:** Choose from Restrained / Committed / Full palette / Drenched. Name a real-world reference before picking. Palette IS voice
9. **Understand existing project** (framework, design system, tokens, component library)
10. **Build production-grade code** — not prototypes. Test at every breakpoint for overflow
11. **Slop test:** Run first-order check (category→palette guessable?) and second-order check (category+anti-ref→aesthetic guessable?).

## Pitfalls

- **Loading the register reference is NOT optional.** Skipping brand.md produces generic output. Always load brand.md or product.md
- **Shape confirmation is NOT a green light to code.** It's a green light to refine palette and direction. The gate sequence: shape confirmed → palette/vibe questions answered → direction approved → code
- **Reflex-reject list applies to NEW projects only.** If the existing brand already committed to Inter or Fraunces, identity-preservation wins
- **Unsplash URLs must be verified.** Guessed IDs 404 silently. If you can't verify, pick fewer photos you're sure exist
- **No imagery on an image-led brief is a BUG.** Restaurant/hotel/travel/fashion/portfolio pages need real imagery. "Restraint" is not an excuse
- **Editorial-typographic (serif+italic+drop caps+rules) is ONE aesthetic lane, not the default brand aesthetic** — unless the brief is literally a magazine
- **Light text on dark backgrounds:** add 0.05–0.1 to line-height. Light type reads lighter and needs breathing room

## Templates

- `templates/environmental-landing.html` — Full demo page (brand register, committed color strategy, Sora+Spectral, 4-section scroll, OKLCH palette, responsive). Reference when building new brand landing pages.

- `reference/brand.md` — Brand register (marketing/landing pages, portfolios)
- `reference/product.md` — Product register (dashboards, app UI, tools)
- `reference/craft.md` — Full craft flow (shape→build→polish)
- `reference/shape.md` — UX/UI planning before code
- `reference/polish.md` — Final quality pass
- `reference/audit.md` — Technical audit (a11y, perf, responsive)
- `reference/colorize.md` — Add strategic color
- `reference/typeset.md` — Typography improvement
- `reference/layout.md` — Layout/spacing fixes
- `reference/animate.md` — Motion design
- `reference/clarify.md` — UX copy improvement
- `reference/adapt.md` — Responsive design
- `reference/distill.md` — Simplify design
- `reference/bolder.md` — Amplify design
- `reference/quieter.md` — Tone down design
- `reference/harden.md` — Production hardening
- `reference/onboard.md` — Onboarding/empty states
- `reference/delight.md` — Delightful touches
- `reference/overdrive.md` — Extreme effects
- `reference/init.md` — Project setup
