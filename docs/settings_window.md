# Settings Window — Widget Behavior Reference
**File:** `ui/settings_window.py`
**Class:** `SettingsWindow(ctk.CTkToplevel)`
**Geometry:** 480 × 520 px, non-resizable
**Opened by:** `ScreenWatermarkApp._open_settings()`

---

## Window-level Behavior

| Event | Behavior |
|---|---|
| Open (first time) | New `SettingsWindow` instance created, lifted to front |
| Open (already exists) | `deiconify()` + `_restore_traces()` + lift to front |
| Close button (X) | `_on_close()` → `_cleanup_traces()` → `withdraw()` (not destroy) |
| Footer Close button | Same as X button |
| ESC key | Not bound — user must click Close |

**Note:** Window is never destroyed after first creation. It is withdrawn and re-shown.

---

## Layout Structure

```
SettingsWindow
├── Header bar (CTkFrame, height=40, fg_color=PANEL)
├── Body (CTkScrollableFrame — scrolls only if content overflows)
│   ├── Startup card
│   ├── Capture card
│   ├── Hotkeys card
│   └── Language card
└── Footer (CTkFrame, height=44, fg_color=PANEL)
    ├── btn_credits
    ├── divider
    ├── btn_reset
    └── btn_close
```

---

## Body Scrollbar

- **Type:** Built into `CTkScrollableFrame`
- **Appears:** Only when content overflows 520px height
- **Width:** 5px max
- **Color:** `ACCENT` (`#6c63ff`)
- **Behavior:** Overlay style — does not reserve space when hidden

---

## Section 1 — Startup Card

**Builder:** `_build_startup_card(parent)`
**Card title:** `t("startup")`

### Widget Table

| Widget ID | Type | Variable | Label |
|---|---|---|---|
| `cb_run_startup` | CTkCheckBox | `app.run_at_startup` | `t("run_at_startup")` |
| `cb_start_minimized` | CTkCheckBox | `app.start_minimized` | `t("start_minimized")` |
| `startup_status_lbl` | CTkLabel | — | Dynamic status text |
| `startup_detail_lbl` | CTkLabel | — | Registry path (Windows) |

### Widget Behaviors

#### `cb_run_startup` — Run at System Startup

- **Var:** `app.run_at_startup` (BooleanVar)
- **On check:** `_on_startup_toggle()` → `set_run_at_startup(True)` [system/startup.py]
- **On uncheck:** `set_run_at_startup(False)`
- **On failure:** Reverts checkbox, shows `messagebox.showwarning()`
- **On success:** `_refresh_startup_status()` updates status label

#### `cb_start_minimized` — Start Minimized to Tray

- **Var:** `app.start_minimized` (BooleanVar)
- **On change:** Saved via autosave trace. Takes effect on next launch with `--startup` flag only.
- **Note:** Has no effect if app is manually launched (not via startup registry)

#### `startup_status_lbl`

| State | Text | Color |
|---|---|---|
| Registered + active | `"✓ Registered in system startup."` | `SUCCESS` |
| Not registered | `"○ Not registered in system startup."` | `MUTED` |

#### `startup_detail_lbl` (Windows only)

- Shows truncated registry command (max 70 chars) when registered
- Hidden when not registered
- Font: `FONT_MONO, 8px`

---

## Section 2 — Capture Card

**Builder:** `_build_capture_card(parent)`
**Card title:** `t("capture")`

### Widget Table

| Widget ID | Type | Variable | Label |
|---|---|---|---|
| `capture_mode_toggle` | Pill (2 CTkButton) | `app.capture_mode` | Fullscreen / Region |
| `region_label` | CTkLabel | — | Current region coords |
| `btn_reset_region` | CTkButton | — | `"↺ Reset"` |
| `delay_slider` | CTkSlider | `app.delay_sec` | — |
| `delay_val_lbl` | CTkLabel | — | `"{n}s"` |
| `ts_format_entry` | CTkEntry | `app.ts_format` | — |

### Widget Behaviors

#### `capture_mode_toggle` — Default Mode

- **Var:** `app.capture_mode` (StringVar: `"fullscreen"` or `"region"`)
- **On change:** `app._on_mode_change()` → updates `region_label`
- **Note:** This sets the DEFAULT mode. Actual capture mode is set when user clicks `btn_fullscreen` or `btn_region` in main window.

#### `region_label` — Saved Region Display

| State | Text |
|---|---|
| No region saved | `"Region: not set (click Region to select)"` |
| Region saved | `"Region: (x1,y1)→(x2,y2)  [WxH px]"` |

#### `btn_reset_region` — Reset Saved Region

- **On click:** `app._reset_region()` → `self._region = None` → status message → label updates
- **Always enabled**

#### `delay_slider` — Capture Delay

- **Var:** `app.delay_sec` (IntVar, 0–10)
- **On change:** Value label shows `"{n}s"`. Saved via autosave.
- **Effect:** When > 0, `CountdownOverlay` shows before capture

#### `ts_format_entry` — Timestamp Format

- **Var:** `app.ts_format` (StringVar)
- **Default:** `"%d/%m/%Y  %H:%M:%S"`
- **On change:** Saved via autosave. Preview re-renders.
- **Preset buttons:** `"DD/MM"` → `"%d/%m/%Y %H:%M:%S"`, `"ISO"` → `"%Y-%m-%d %H:%M"`
- **Error state:** Invalid strftime format → `apply_timestamp()` falls back to `"%Y-%m-%d %H:%M:%S"` silently via `safe_strftime()`

---

## Section 3 — Hotkeys Card

**Builder:** `_build_hotkey_card(parent)`
**Card title:** `t("hotkeys")`
**Type:** Display-only. No interactive controls.

### Widget Table

| Row label | Displays | Source |
|---|---|---|
| `t("fullscreen")` | `_preset_label(app.hotkey_fullscreen.get())` | system/hotkeys.py |
| `t("region")` | `_preset_label(app.hotkey_region.get())` | system/hotkeys.py |
| `t("open_history")` | `_preset_label(app.hotkey_history.get())` | system/hotkeys.py |

- Each hotkey shown as a styled pill label: `fg_color=CARD2, border=BORDER, text_color=ACCENT, font=FONT_MONO`
- Footer note: `"Hotkeys are fixed. App stays in System Tray when window is closed."`
- No edit functionality in this window

---

## Section 4 — Language Card

**Builder:** `_build_language_card(parent)`
**Card title:** `t("language")`

### Widget Table

| Widget ID | Type | Variable | Values |
|---|---|---|---|
| `language_menu` | CTkOptionMenu | `app.ui_language` | `["English", "Indonesian"]` |
| `restart_notice_lbl` | CTkLabel | — | `t("restart_required")` |

### Widget Behaviors

#### `language_menu`

- **Var:** `app.ui_language` (StringVar: `"en"` or `"id"`)
- **On change:** `_on_language_change(selection)` → maps `"English"→"en"`, `"Indonesian"→"id"` → `app.ui_language.set(lang)` → saved via autosave
- **Effect:** Language change applies on next app restart only. Does NOT hot-reload strings.

#### `restart_notice_lbl`

- **Text:** `t("restart_required")` = `"Restart required to apply language change."`
- **Always visible** (not conditional)
- **Style:** `font=FONT_MONO, 9px, text_color=MUTED`

---

## Section 5 — Footer

**Builder:** `_build_ui()` footer section
**Container:** `CTkFrame(fg_color=PANEL, height=44, corner_radius=0)`

### Widget Table

| Widget ID | Type | Label |
|---|---|---|
| `btn_credits` | CTkButton | `t("credits")` |
| `footer_divider` | CTkFrame | — |
| `btn_reset` | CTkButton | `t("reset_default")` |
| `btn_close` | CTkButton | `t("close")` |

### Widget Behaviors

#### `btn_credits`

- **On click:** Opens `CreditsPopup` — see `credits_popup.md`
- **Style:** `fg_color=CARD, border_width=1, border_color=BORDER, text_color=MUTED`

#### `footer_divider`

- `CTkFrame(width=1, height=20, fg_color=BORDER)` — visual separator only

#### `btn_reset` — Reset to Default

- **On click:** `_reset_defaults()` → sets all `app.*` vars to `DEFAULT_SETTINGS` values
- **Resets:** All vars listed in `core/settings.py DEFAULT_SETTINGS`
- **Does NOT reset:** `run_at_startup` (OS-level action), `language` (requires restart)
- **After reset:** Autosave fires → preview re-renders

#### `btn_close`

- **On click:** `_on_close()` → `_cleanup_traces()` → `self.withdraw()`
- **Style:** `fg_color=ACCENT, text_color="white", font=(FONT, 10, "bold")`

---

## Sections NOT in Settings Window (removed in v8.0)

The following cards exist in v3.9.1f but are **removed** in v8.0:

| Removed card | Now located |
|---|---|
| Watermark card (file, mode, opacity, scale, position) | Main window WM accordion |
| Timestamp card (enable, position, font, color, bold, shadow, outside) | Main window TS accordion |

`ts_format` entry is kept in Settings → Capture card (it is an advanced option).
