# History Popup — Widget Behavior Reference
**File:** `ui/history_popup.py`
**Class:** `HistoryPopup(ctk.CTkToplevel)`
**Opened by:** `ScreenWatermarkApp._show_history_popup()` or hotkey `hotkey_history`
**Geometry:** Auto-sized, centered on screen

---

## Window-level Behavior

| Event | Behavior |
|---|---|
| Open (not already open) | New `HistoryPopup` created, centered, lifted |
| Open (already open) | `_render()` refreshes content, `lift()` brings to front |
| Close button (✕) | `_safe_destroy()` |
| ESC key | `_safe_destroy()` |
| New screenshot while open | `_render()` called via `_notify_history_updated()` — auto-refreshes without closing |
| `_destroyed` guard | All callbacks check `self._destroyed` before acting |

---

## Layout Structure

```
HistoryPopup
├── Header bar
│   ├── title: "🖼 Screenshot History"
│   └── btn_close (✕)
├── Grid (if history has items)
│   └── [thumb columns × 0–5, newest first left]
└── Footer label: "Click thumbnail to copy to clipboard"

OR

└── Label: "No screenshots yet." (if history empty)
```

---

## Widget Behaviors

### Header

#### Close button `"✕"`

- **On click:** `_safe_destroy()`
- **Style:** `bg=PANEL, fg=MUTED, bd=0`

### Thumbnail column (per entry)

Each thumbnail is a `CTkFrame` column containing:

| Element | Content |
|---|---|
| Thumbnail image | Scaled to 150×84, black letterbox background |
| Time label | `entry["timestamp"].strftime("%H:%M:%S")` |
| Size label | `f"{width}×{height}"` |

#### Thumbnail click behavior

- **Any click on column or image:** `_copy_entry(entry, col)`
  1. Loads full image from `entry["full_bytes"]`
  2. Sets `app.last_image = img`
  3. `copy_image_to_clipboard(img)`
  4. Column briefly flashes `SUCCESS` color
  5. `app.status_var.set("History copied to clipboard!")`
  6. `app.btn_copy` → enabled + `SUCCESS` color → restores after 2s
  7. Window closes after 600ms

#### Error state (thumbnail load fails)

- Image thumbnail renders as blank/black area
- Click still attempts to load full image
- If full image fails: `messagebox.showerror()`

---

## State: History Empty

- Grid not rendered
- Single label shown: `"No screenshots yet."`, `fg=MUTED`
- Close button still works
