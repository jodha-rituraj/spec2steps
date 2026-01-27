# Project Documentation Guidance

## Purpose
Capture the story of each project in a personable, plain-language document so future you (and teammates) can quickly grasp what was built, why it works the way it does, and what pitfalls to avoid.

## Required doc: `FOR_<yourname>.md`
For every project, add a file named `FOR_<yourname>.md` (example: `FOR_RITURAJ.md`) in the repo root. It should be engaging, not textbook-dry.

### What to cover
- **Overview:** What the project does, in everyday language.
- **Technical architecture:** How the pieces fit together; data/flow diagrams if helpful.
- **Codebase structure:** Key folders/modules and how they connect.
- **Technologies & decisions:** What we used, why we chose them, trade-offs.
- **Bugs & fixes:** Issues we hit, how we debugged and solved them.
- **Pitfalls & guardrails:** Tricky parts, gotchas, and how to avoid future regressions.
- **Lessons learned:** How good engineers think/work here; best practices that emerged.
- **New tech notes:** Quick primers on any new tools/frameworks introduced.

### Tone & style
- Conversational and vivid—use analogies or anecdotes where it helps.
- Favor short sections and bullets over walls of text.
- Include “why” behind decisions, not just the “what”.

### Suggested outline
1) Title + 2–3 sentence elevator pitch
2) Architecture story (how requests/data flow)
3) Folder-by-folder tour (what each area owns)
4) Key decisions (trade-offs, performance, cost, DX)
5) Bugs we met & how we fixed them
6) Pitfalls to watch for next time
7) Lessons and best practices
8) Quickstart links/commands (if relevant)

## How to keep it fresh
- Update after meaningful changes (architecture tweaks, major bug fixes, new dependencies).
- Add a short “Changelog” section at the bottom with date-stamped bullets.

## Quick checklist before you ship
- [ ] `FOR_<yourname>.md` exists in repo root
- [ ] Architecture and codebase sections reflect current state
- [ ] Recent bugs/pitfalls documented with fixes and preventions
- [ ] Tone is readable and engaging, not just raw logs
