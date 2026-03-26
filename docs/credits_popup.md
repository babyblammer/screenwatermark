# Credits Popup — Widget Behavior Reference
**File:** `ui/settings_window.py` (inner class or method) or `ui/credits_popup.py`
**Class:** `CreditsPopup(ctk.CTkToplevel)`
**Opened by:** `SettingsWindow.btn_credits` → `_open_credits()`
**Geometry:** 400 × auto (fits content), centered relative to Settings window

---

## Window-level Behavior

| Event | Behavior |
|---|---|
| Open | Centered on Settings window, lifted to top |
| Close (✕ or button) | `destroy()` |
| ESC key | `destroy()` |
| Click outside | No dismiss (modal behavior via `transient()`) |

---

## Layout Structure

```
CreditsPopup
├── Titlebar: "Credits — ScreenWatermark Pro"  (left-aligned)
├── ── App Info section ──────────────────────  (center-aligned)
│   ├── App name: "ScreenWatermark Pro"
│   ├── Version: "v4.0.0"
│   └── Description: "Screenshot utility with watermark & timestamp overlay"
├── ── Development Team section ──────────────  (left-aligned rows)
│   ├── PM / Design: [name]
│   ├── Developer:   [name]
│   └── QA:          Gayuh Marga H.
├── ── License section ───────────────────────  (center-aligned)
│   └── "MIT License — © 2025 [owner name]"
└── btn_close: "Close"  (centered, bottom)
```

---

## Content Specification

### App Info Section

| Field | Value |
|---|---|
| Section header | `"App Info"` — `font=(FONT, 10, "bold"), text_color=ACCENT` — center-aligned |
| App name | `"ScreenWatermark Pro"` — `font=(FONT, 14, "bold"), text_color=TEXT` — center-aligned |
| Version | `f"v{ScreenWatermarkApp.VERSION}"` — `font=FONT_MONO, text_color=MUTED` — center-aligned |
| Description | `"Screenshot utility with watermark & timestamp overlay"` — `font=(FONT, 10), text_color=MUTED` — center-aligned |

### Development Team Section

| Field | Alignment | Style |
|---|---|---|
| Section header `"Development Team"` | Center | `font=(FONT, 10, "bold"), text_color=ACCENT` |
| Role + Name rows | Left | `font=(FONT, 10), text_color=TEXT` |
| Role label | Left | `text_color=MUTED, width=100` |
| Name label | Left | `text_color=TEXT` |

Team rows (fill in names before release):

| Role | Name |
|---|---|
| PM / Design | `[your name]` |
| Developer | `[programmer name]` |
| QA | `Gayuh Marga H.` |

### License Section

| Field | Value |
|---|---|
| Section header | `"License"` — center-aligned |
| License text | `"MIT License"` — center-aligned, `text_color=MUTED` |
| Copyright | `"© 2025 [owner name]"` — center-aligned, `text_color=MUTED, font=FONT_MONO, 9px` |

---

## Widget Behaviors

### `btn_close` — Close Credits

- **On click:** `self.destroy()`
- **Style:** `fg_color=ACCENT, text_color="white"`
- **Position:** Centered horizontally at bottom, `pady=12`

---

## Alignment Rules

| Section | Header alignment | Content alignment |
|---|---|---|
| App Info | Center | Center |
| Development Team | Center | Left (role + name on same row) |
| License | Center | Center |
| Window title (titlebar) | Left | — |

---

## Implementation Notes

- Use `CTkToplevel.transient(settings_window)` to keep popup above Settings
- Separator lines between sections: `CTkFrame(height=1, fg_color=BORDER)`
- No scrollbar needed — content is short and fixed
- `padx=24, pady=12` on all content sections for consistent breathing room
- Version number reads from `ScreenWatermarkApp.VERSION` constant — do not hardcode
