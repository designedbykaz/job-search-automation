# Figma Make prototype — reference only

## What this folder is

These files are the output of a Figma Make prototype generated during v2 planning. They exist here purely as a **visual and structural reference** for the Flask + Bootstrap + HTMX rebuild.

They represent what the UI should look like and how the screens are organised. They do not represent what the UI is actually built in.

## What this folder is not

This is not source code. It is not imported by anything. It is not executed. It is not part of the build. The real application lives in `ui/` at the repo root.

## Rules for any agent reading this folder

If you are Claude Code, Cursor, or any other AI agent working on this project, treat this folder as **read-only reference material** and follow these rules:

1. **Do not copy files from this folder into the actual app.** The real app uses a completely different stack (Flask, Jinja2 templates, Bootstrap 5.3, HTMX). Do not paste TSX into HTML files. Do not try to wire the React components up.

2. **Do not import from this folder anywhere in `ui/`.** Nothing in `ui/` should reference this path.

3. **Do not install the dependencies that these files imply.** No React, no Tailwind, no shadcn, no Vite, no Node.js tooling.

4. **Do not attempt to run these files.** They are not a runnable project. They exist as standalone snapshots.

5. **Do not port the theme.css custom properties directly.** Bootstrap 5.3's default theme is close enough to the intended look. Small overrides live in `ui/static/css/app.css`.

6. **Do not treat cluster names or sample data in these files as authoritative.** The Figma Make prototype invented cluster names (`product_management`, `service_design`, `design_systems`, etc.) that do not exist in the real pipeline. The canonical cluster list lives in `config/keywords.py`:

   - `nhs_healthcare`
   - `ux_design`
   - `data_analytics`
   - `technical_engineering`
   - `digital_marketing`
   - `project_ops`
   - `edtech`

   Use those names. Not the invented ones.

7. **Do not treat model names in `Settings.tsx` as authoritative.** The prototype hardcoded stale Claude model names. The real app reads the current model from the `CLAUDE_MODEL` environment variable.

## What to use this folder for

Do read these files when you need to:

- Understand how a screen is visually laid out (sidebar placement, top bar content, card grouping, spacing rhythm)
- Understand the intended interactions (which buttons appear where, what happens when a row is clicked, what the two states of the Run page look like)
- Understand the copy and tone of UI labels, empty states, and button text
- Understand the hierarchy of information on each screen

## What's in here

Nine TypeScript/React files from the Figma Make prototype, plus one CSS file:

- `App.tsx` — shows the route structure
- `Layout.tsx` — the sidebar + top bar shell
- `Dashboard.tsx` — the landing screen
- `Run.tsx` — pre-run config and in-run log states
- `Jobs.tsx` — the jobs table and detail pane
- `Content.tsx` — the content file manager
- `Prompts.tsx` — the prompt editor with test panel
- `Templates.tsx` — the CV template manager
- `Settings.tsx` — the settings screen
- `theme.css` — the OKLCH colour palette and CSS variables the prototype used

## Translation reference

When looking at these files, here is roughly how the original stack maps to what the real app is built in:

| Figma Make prototype | Real app |
|---|---|
| React component (`.tsx`) | Jinja2 template (`.html`) |
| `useState` hooks | HTMX partial swaps or Flask session state |
| Tailwind utility classes | Bootstrap 5.3 utility classes |
| `lucide-react` icons | Bootstrap Icons |
| React Router | Flask routes |
| `components/ui/*` (shadcn) | Direct Bootstrap components |
| Vite dev server | Flask dev server on `127.0.0.1:5000` |

## When this folder can be deleted

Once the v2 rebuild has reached visual parity with the prototype and the real app is running confidently, this folder can be removed from the repo. Until then, keep it around as a reference point during design reviews.

---

*If you are an agent and you find yourself about to do something with these files other than reading them: stop and re-read this README.*
