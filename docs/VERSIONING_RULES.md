# Versioning Rules — ScreenWatermark Pro

---

## Version Format

```
  X  .  Y  .  Z  A
  │     │     │  └── Build index (a, b, c, ...)
  │     │     └───── Hotfix version
  │     └─────────── Update version
  └───────────────── Live version
```

Version segments are read left to right. Each segment has different meaning and independent increment rules.

---

## Segment Explanation

### X — Live Version

Major increment indicating architectural changes, platform changes, or fundamental feature changes. Increases when changes significantly differentiate the product from the previous version.

Example: `3.x.x` → `4.0.0`

### Y — Update Version

Increment indicating new features or significant functional changes without altering the application's foundation.

Y is limited to **0–9**. If Y reaches 9 and there's a new update, Y resets to 0 and X increments automatically.

Example: `3.9.x` → `4.0.0` (not `3.10.0`)

### Z — Hotfix Version

Increment indicating bug fixes without new features. Each hotfix cycle starts at `.1` and increments sequentially.

Example: `3.9.0` → `3.9.1` → `3.9.2`

> `Z = 0` means no hotfixes yet for that update.

### A — Build Index

Alphabetic character indicating the build sequence released by the developer within **one release cycle** (same X.Y.Z). Each new build submitted to QA increments one letter, and the alphabet **is retained in public releases**.

- `a` = first build
- `b` = second build
- `c` = third build
- etc.

Builds that pass QA and are released publicly retain the last letter. Alphabet resets to `a` only when X, Y, or Z increments.

---

## Build Index Reset Rules

Build index returns to `a` whenever X, Y, or Z increments:

| Event | Example |
|---|---|
| New hotfix | `3.9.1e` → `3.9.2a` |
| New update (Y < 9) | `3.8.xe` → `3.9.0a` |
| New update (Y = 9) | `3.9.xe` → `4.0.0a` ← Y carry-over to X |
| New live version | `3.x.xe` → `4.0.0a` |

---

## Version Examples

| Version | Meaning |
|---|---|
| `3.9.0a` | Live version 3, 9th update, no hotfix, first build |
| `3.9.1a` | First hotfix of update 3.9, first build |
| `3.9.1e` | First hotfix of update 3.9, 5th build — if this passes QA, `3.9.1e` is the public release |
| `3.9.2a` | Second hotfix of update 3.9, first build — build index resets to a |
| `4.0.0a` | New update when Y = 9 → X increments, Y and Z reset to 0, build index resets to a |

---

## Complete Lifecycle Example

```
3.9.0           ← public release of 9th update

  — bug found —

3.9.1a          ← dev releases first build of hotfix 1, QA tests
3.9.1b          ← still has bug, dev releases second build
3.9.1c          ← still has bug, dev releases third build
3.9.1d          ← still has bug, dev releases fourth build
3.9.1e          ← still has bug, dev releases fifth build  ← current position

3.9.1f          ← next build (awaiting release from developer)

  — all bugs fixed —

3.9.1f          ← 6th build passes QA → this is the public release (letter retained)

  — new bug found —

3.9.2a          ← second hotfix started, build index resets to a
```

---

## Notes

- Alphabet **is always present** in every version, both internal and public release — never removed.
- Public release version is the last build declared stable by QA, with its letter included (e.g., `3.9.1e` not `3.9.1`).
- Number of builds per cycle is unlimited — alphabet continues (`a` → `z`) as needed.
