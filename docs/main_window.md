# Main Window — Widget Behavior Reference
**File:** `ui/main_window.py`
**Class:** `ScreenWatermarkApp(ctk.CTk)`
**Geometry:** 620 × 580 px, locked, non-resizable

---

## Window-level Behavior

| Event | Behavior |
|---|---|
| Launch | Window appears at 620×580. Preview panel active. WM and TS cards always visible. |
| Close button (X) | App hides to tray (`_hide_to_tray()`). Window does NOT quit. |
| Quit | Only via tray → Quit or `_quit_app()`. Saves settings + history before destroy. |
| `--startup` flag | If `start_minimized=True` AND launched via `--startup`, hides to tray immediately. |

---

## Section 1 — Header Bar

**Builder:** `_build_header()`
**Container:** `CTkFrame(fg_color=PANEL, height=44, corner_radius=0)`
**Pack:** `fill="x"` on `self` (CTkApp), before `middle_frame`

### Widget Table

| Widget ID | Type | Variable | Text |
|---|---|---|---|
| `app_icon` | CTkLabel | — | `"📸"` |
| `app_name_lbl` | CTkLabel | — | `t("app_title")` |
| `wm_indicator` | CTkLabel | — | Dynamic |
| `btn_history_icon` | CTkButton | — | `"🕒"` |
| `btn_settings` | CTkButton | — | `f"⚙ {t('settings')}"` |

### Widget Behaviors

#### `wm_indicator` — WM Status Badge

- **File:** `ui/main_window.py`
- **Builder:** `_build_header()` → updated by `_update_wm_indicator()`
- **Triggers:** `wm_enabled` trace + `watermark_path` trace (both in `__init__`)
- **States:**

| Condition | Text | `text_color` | `fg_color` |
|---|---|---|---|
| WM enabled + file set | `t("wm_on")` = `"WM ✓"` | `SUCCESS` `#43e97b` | `#152515` |
| WM enabled + no file | `t("wm_warn")` = `"WM ⚠"` | `WARN` `#f5a623` | `#2a1f08` |
| WM disabled | `t("wm_off")` = `"WM OFF"` | `MUTED` `#5a5a7a` | `#1a1a26` |

- **Error state:** If `watermark_path` points to a file that no longer exists on disk, treat as "no file" → show `WM ⚠`.

#### `btn_history_icon` — History Quick Open

- **File:** `ui/main_window.py`
- **Builder:** `_build_header()`
- **On click:** `_show_history_popup()` — opens `HistoryPopup` CTkToplevel
- **Disabled/enabled:** Always enabled
- **Size:** `width=30, height=30`

#### `btn_settings` — Open Settings

- **File:** `ui/main_window.py`
- **Builder:** `_build_header()`
- **On click:** `_open_settings()` — creates or deiconifies `SettingsWindow`
- **Disabled/enabled:** Always enabled
- **Style:** `fg_color=ACCENT`, `hover_color="#7d75ff"`, `text_color="white"`

---

## Section 2 — Middle Frame (Scrollable)

**Builder:** `_build_ui()`
**Container:** `CTkScrollableFrame(height=484, fg_color=BG, corner_radius=0)`
**Variable:** `self.middle_frame`
**Pack:** `fill="x"` on `self`, after header, before action bar

- Height = 580 − 44 (header) − 52 (action bar) = **484px**
- Scrollbar: appears only when content overflows. Max width 5px. Color `ACCENT`. Overlay style.
- `pack_propagate(False)` is NOT set on `middle_frame` — it grows with content. Children control their own heights.

### Children pack order (top → bottom, strict)

```
① self.panel_toggle          _build_panel_toggle()
② self.preview_wrap          _build_preview_panel()      ← Preview panel
③ self.history_panel_wrap    _build_history_panel()      ← hidden on launch
④ self._wm_card              _build_wm_card()
⑤ self._ts_card              _build_ts_card()
⑥ self.bottom_bar            _build_bottom_bar()         ← Settings, Fullscreen, Region
```

---

## Section 2.1 — Panel Toggle

**Builder:** `_build_panel_toggle(self.middle_frame)`
**Container:** `CTkFrame(fg_color=CARD, corner_radius=9, border_width=1, border_color=BORDER)`
**Variable:** `self.panel_toggle`
**Pack:** `anchor="w", padx=12, pady=(10,0)` inside `middle_frame`

### Widget Table

| Widget ID | Type | Variable | Text |
|---|---|---|---|
| `btn_panel_preview` | CTkButton | — | `f"🖼  {t('preview')}"` |
| `btn_panel_history` | CTkButton | — | `f"🕒  {t('history')}"` |
| `hist_count_badge` | CTkLabel | — | count string or `""` |

### Widget Behaviors

#### `btn_panel_preview`

- **On click:** `_switch_panel("preview")`
- **Active state:** `fg_color=ACCENT, text_color="white"`
- **Inactive state:** `fg_color="transparent", text_color=MUTED`
- **Default on launch:** Active

#### `btn_panel_history`

- **On click:** `_switch_panel("history")`
- **Active/inactive:** Same pattern as preview button (inverse)
- **Default on launch:** Inactive

#### `hist_count_badge`

- **Variable:** `self.hist_count_badge`
- **Updated by:** `_update_history_badge()`
- **Trigger:** Called after every screenshot + after every history delete
- **States:**

| Condition | Text | `fg_color` |
|---|---|---|
| History empty (0 items) | `""` | `"transparent"` |
| 1–5 items | `"1"` … `"5"` | `ACCENT2` `#ff6584` |

#### `_switch_panel(which: str)`

- **"preview":** `history_panel_wrap.pack_forget()` → `preview_wrap.pack(fill="x", padx=12, pady=(0,8))`
- **"history":** `preview_wrap.pack_forget()` → `history_panel_wrap.pack(fill="x", padx=12, pady=(0,8))` → `_render_history_panel()`
- Sets `self._panel_mode = which`

---

## Section 2.2 — Preview Canvas

**Builder:** `_build_preview_panel(self.middle_frame)`
**Container:** `CTkFrame(height=180, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)`
**Variable:** `self.preview_wrap`
**Inner canvas:** `tk.Canvas(width=320, height=180, bg="#0a0a12", highlightthickness=0)`
**Variable:** `self.preview_canvas`
**Pack:** `fill="x", padx=12, pady=(0,8)` inside `middle_frame`

- `self.preview_wrap.pack_propagate(False)` — **mandatory**. Locks height at 180px. Without this CTk shrinks it.
- Canvas is plain `tk.Canvas`, not CTk — CTk has no canvas widget.

### Behaviors

| Event | Behavior |
|---|---|
| Setting var changes | `_on_setting_changed()` → debounce 350ms → `_refresh_live_preview()` |
| `_refresh_live_preview()` | Spawns background thread → renders preview image → `after(0, _apply_preview)` |
| `_apply_preview(img)` | Main thread: `preview_canvas.delete("all")` → `create_image(0,0,image=tk_img)` |
| Screenshot taken | `_update_preview_from_screenshot(img)` — shows actual screenshot thumbnail |
| Manual refresh | `↻ Refresh` button calls `_refresh_live_preview()` directly |

### Edge states

| State | Canvas shows |
|---|---|
| WM enabled + no file set | Grid background + `"[ Watermark: belum dipilih ]"` text in orange |
| WM disabled | Grid background + `"[ Watermark: OFF ]"` text in muted |
| No vars set (fresh launch) | Grid background only |
| After screenshot | Actual screenshot thumbnail, scaled to fit 320×180 |

---

## Section 2.3 — History Panel

**Builder:** `_build_history_panel(self.middle_frame)`
**Container:** `CTkFrame(height=180, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)`
**Variable:** `self.history_panel_wrap`
**Pack:** NOT packed on launch. `_switch_panel("history")` packs it.

- `self.history_panel_wrap.pack_propagate(False)` — **mandatory**. Same reason as preview.

### Internal layout

```
history_panel_wrap
├── top_bar (CTkFrame, height=32)
│   ├── label: "Last 5 screenshots · click to copy"
│   └── btn_clear_all_panel
└── hist_panel_scroll (CTkScrollableFrame, orientation="horizontal")
    └── [thumb frames × 0–5]
```

### Widget Behaviors

#### `btn_clear_all_panel` — Clear All

- **On click:** `_clear_all_history()` — confirms, clears `self._history` deque, saves, re-renders
- **Disabled when:** History is empty (configure `state="disabled"`)

#### Thumbnail frame (per history entry)

- **On click:** `_load_from_history(entry)` — loads image, copies to clipboard, updates status
- **Width:** 108px | **Height:** 88px (60px image + 28px meta)
- **Hover:** border changes to `ACCENT`

#### `_render_history_panel()`

- Clears `hist_panel_scroll` children
- If history empty: shows `"No screenshots yet."` label
- Builds one thumb frame per entry, newest first (left to right)

#### New screenshot while on History panel

- `_notify_history_updated()` detects `self._panel_mode == "history"`
- Calls `_render_history_panel()` + `xview_moveto(0)` (scroll to newest)
- Does NOT switch to Preview panel

---

## Section 2.4 — WM Card

**Builder:** `_build_wm_card(self.middle_frame)`
**Container:** `CTkFrame(fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)`
**Variable:** `self._wm_card`
**Pack:** `fill="x", padx=12, pady=(0,6)` inside `middle_frame`

### Header row widgets

| Widget | Behavior |
|---|---|
| Icon label `💧` | Static, no interaction |
| Title label `"Watermark"` | Static |
| Summary label `self._wm_summary_lbl` | Updated by `_update_wm_summary()` on every `wm_*` var change |

### Summary string format

```python
# WM enabled:
"Normal · Bottom-Left · 70% · 20%"    # Normal mode
"Pattern · 70% · 20%"                   # Pattern mode (no position)
"Full Screen · 70%"                     # Full mode (no scale, no position)

# WM disabled:
"OFF"
```

### Body — Row 1 widgets

#### Mode dropdown (CTkOptionMenu)

- **Var:** `self.wm_mode` (StringVar)
- **Values:** `["Off", "Normal", "Full Screen", "Pattern"]`
- **On change:** `_on_wm_mode_change()` → syncs `wm_enabled` + shows/hides controls

| Mode | `wm_enabled` | Position | Scale | Pattern Gap |
|---|---|---|---|---|
| `Off` | `False` | disabled | disabled | disabled |
| `Normal` | `True` | ✅ enabled | ✅ enabled | disabled |
| `Full Screen` | `True` | disabled | disabled | disabled |
| `Pattern` | `True` | disabled | ✅ enabled | ✅ enabled |

#### Position dropdown (CTkOptionMenu) — only for Normal mode

- **Var:** `self.wm_position` (StringVar)
- **Values:** `["Bottom-Left", "Bottom-Right", "Top-Left", "Top-Right", "Center"]`

#### Opacity slider

- **Var:** `self.wm_opacity` (IntVar, 0–100)
- **On change:** Value label updates. `_on_setting_changed()` fires → preview re-renders after 350ms debounce.

### Body — Row 2 widgets

#### Scale slider (hidden in Full Screen mode)

- **Var:** `self.wm_scale` (IntVar, 5–60)
- **On change:** Value label updates. Preview re-renders.

#### Pattern Gap slider — only for Pattern mode

- **Var:** `self.wm_pattern_gap` (IntVar, 0–100)
- **On change:** Value label updates. Preview re-renders.

#### Path row

- **Label:** Shows `os.path.basename(path)` or `t("no_file")`
- **Browse button:** `_pick_watermark()` → `filedialog.askopenfilename()`
- **Clear button:** `_clear_watermark_path()` → `watermark_path.set("")`

---

## Section 2.5 — TS Card

**Builder:** `_build_ts_card(self.middle_frame)`
**Container:** `CTkFrame(fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)`
**Variable:** `self._ts_card`
**Pack:** `fill="x", padx=12, pady=(0,6)` inside `middle_frame`

### Header row widgets

| Widget | Behavior |
|---|---|
| Icon label `🕐` | Static, no interaction |
| Title label `"Timestamp"` | Static |
| Summary label `self._ts_summary_lbl` | Updated by `_update_ts_summary()` on every `ts_*` var change |

### Summary string format

```python
# TS enabled:
"Outside · 22px · #FFFFFF"

# TS disabled:
"OFF"
```

### Body — Row 1 widgets

#### Enable dropdown (CTkOptionMenu)

- **Var:** `self.ts_enable` (StringVar) + `self.ts_enabled`, `self.ts_outside_canvas` (BooleanVar)
- **Values:** `["Off", "Outside"]`
- **On "Off":** Timestamp disabled. Controls disabled.
- **On "Outside":** Timestamp strip at bottom-right of image.

#### Format dropdown (CTkOptionMenu)

- **Var:** `self.ts_format` (StringVar)
- **Values:** `["DD/MM/YYYY HH:MM:SS", "ISO 8601", "MM/DD/YYYY HH:MM:SS", "YYYY-MM-DD"]`

### Body — Row 2 widgets

#### Font size slider

- **Var:** `self.ts_font_size` (IntVar, 10–60)
- **On change:** Value label updates. Preview re-renders.
- **Note:** Dynamic scaling applied in preview — `dyn_size = max(10, min(base_size, img_w // 50))`. Actual screenshot uses full value.

#### Text color swatch button

- **Var:** `self.ts_color` (StringVar, hex)
- **On click:** `_pick_color()` → `colorchooser.askcolor()`
- **On color selected:** Button `fg_color` updates to new color. Preview re-renders.
- **On cancel:** No change.

---

## Section 3 — Bottom Bar

**Builder:** `_build_bottom_bar()`
**Container:** `CTkFrame(fg_color=PANEL, height=44, corner_radius=0)`
**Variable:** `self.bottom_bar`
**Pack:** `fill="x", side="bottom"` on `self`

### Widget Table

| Widget ID | Type | Variable | Default state |
|---|---|---|---|
| `btn_settings` | CTkButton | — | `state="normal"` |
| `btn_fullscreen` | CTkButton | — | `state="normal"` |
| `btn_region` | CTkButton | — | `state="normal"` |
| `status_lbl` | CTkLabel | `self.status_var` (StringVar) | Ready message |

### Widget Behaviors

#### `btn_settings` — Open Settings

- **On click:** `_open_settings()` — creates or deiconifies `SettingsWindow`
- **Style:** `fg_color="#2a2a3e", hover_color="#3a3a50"`

#### `btn_fullscreen` — Fullscreen Screenshot

- **On click:** `_trigger_fullscreen()` → `capture_mode.set("fullscreen")` → `_start_screenshot()`
- **Disabled during:** Entire screenshot flow
- **Style:** `fg_color=ACCENT, hover_color="#7d75ff"`
- **Hotkey equivalent:** `hotkey_fullscreen` (default: Print Screen)

#### `btn_region` — Region Screenshot

- **On click:** `_trigger_region()` → `capture_mode.set("region")` → `_start_screenshot()`
- **Disabled during:** Entire screenshot flow
- **Style:** `fg_color=ACCENT2, hover_color="#ff7580"`

#### `status_lbl` — Status Bar

- **Var:** `self.status_var` (StringVar)
- **Default text:** `f"Ready — {_preset_label(hotkey_fullscreen)} | {_preset_label(hotkey_region)}"`
- **Updates:**

| Event | Status text |
|---|---|
| Screenshot in progress | `"⏳ Taking screenshot…"` |
| Screenshot success | `"✓ Screenshot copied to clipboard!"` |
| Screenshot failed | `"✕ Screenshot failed."` |
| Countdown active | `"⏳ Screenshot in {n} seconds… (Esc = cancel)"` |
| Countdown cancelled | `"Cancelled."` |
| Settings autosaved | `"✓ Settings saved"` |
| Restores after 3s | Returns to default hotkey summary text |

---

## State Machine — Screenshot Flow

```
User clicks btn_fullscreen / btn_region / presses hotkey
        ↓
_start_screenshot()
  → _set_shot_buttons(False)
  → btn_copy disabled
  → if region mode: show RegionSelector overlay
  → if delay > 0:   show CountdownOverlay
  → else:           withdraw main window → after(120ms) → _do_screenshot()
        ↓
_do_screenshot(region)
  → capture via mss
  → apply_watermark() [core/render.py]
  → apply_timestamp() [core/render.py]
  → copy to clipboard
  → append to self._history
  → _render_history() + _notify_history_updated()
  → status_var update
        ↓
finally:
  → _set_shot_buttons(True)
  → restore main window if needed
```

---

## All `self.*` Variables (main window)

| Variable | Type | Default | Purpose |
|---|---|---|---|
| `watermark_path` | StringVar | `""` | Path to WM image file |
| `wm_enabled` | BooleanVar | `True` | WM on/off toggle |
| `wm_mode` | StringVar | `"normal"` | normal / full / pattern |
| `wm_position` | StringVar | `"bottom-left"` | WM placement |
| `wm_opacity` | IntVar | `70` | WM opacity 0–100 |
| `wm_scale` | IntVar | `20` | WM scale % of width |
| `ts_enabled` | BooleanVar | `True` | TS on/off (internal) |
| `ts_enable` | StringVar | `"Outside"` | TS dropdown display |
| `ts_format` | StringVar | `"%d/%m/%Y  %H:%M:%S"` | strftime format |
| `ts_font_size` | IntVar | `22` | Font size px |
| `ts_color` | StringVar | `"#FFFFFF"` | TS text color |
| `ts_bg_color` | StringVar | `"#000000"` | TS background color |
| `ts_bg_opacity` | IntVar | `60` | TS BG opacity 0–100 |
| `ts_shadow` | BooleanVar | `True` | TS drop shadow |
| `ts_bold` | BooleanVar | `False` | TS bold font |
| `ts_outside_canvas` | BooleanVar | `False` | TS strip outside image |
| `delay_sec` | IntVar | `0` | Capture delay seconds |
| `hotkey_fullscreen` | StringVar | `"<print_screen>"` | Fullscreen hotkey |
| `hotkey_region` | StringVar | `"<ctrl>+<shift>+<f9>"` | Region hotkey |
| `hotkey_history` | StringVar | `"<ctrl>+<f9>"` | History hotkey |
| `capture_mode` | StringVar | `"fullscreen"` | Current mode |
| `run_at_startup` | BooleanVar | `False` | OS startup entry |
| `start_minimized` | BooleanVar | `False` | Start in tray |
| `ui_language` | StringVar | `"en"` | UI language |
| `status_var` | StringVar | ready text | Status bar text |
| `last_image` | Image or None | `None` | Last screenshot |
| `_panel_mode` | str | `"preview"` | Current panel |
| `_wm_acc_open` | bool | `True` | WM accordion state |
| `_ts_acc_open` | bool | `False` | TS accordion state |
| `_history` | deque | empty | Screenshot history |
