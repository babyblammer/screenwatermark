# Overlays — Widget Behavior Reference
**File:** `ui/overlays.py`
**Classes:** `CountdownOverlay`, `RegionSelector`

> ⚠️ Both classes use pure `tk.Toplevel` — NOT `ctk.CTkToplevel`.
> `overrideredirect(True)` requires plain tkinter. Do not migrate these to CTk.

---

## CountdownOverlay

**Class:** `CountdownOverlay(tk.Toplevel)`
**Opened by:** `ScreenWatermarkApp._countdown(n)` when `delay_sec > 0`

### Window properties

| Property | Value |
|---|---|
| Geometry | Full screen (`winfo_screenwidth × winfo_screenheight`) |
| `overrideredirect` | `True` (no OS titlebar or border) |
| Alpha | `0.72` (semi-transparent dark) |
| Background | `#0a0a10` |
| Always on top | `True` |

### Layout

```
CountdownOverlay (fullscreen)
├── Sub-label top:    "Screenshot in…"        (Segoe UI 18, MUTED)
├── Countdown number: "3" / "2" / "1"         (Segoe UI 120 bold, ACCENT)
└── Sub-label bottom: "Press Esc to cancel"   (Segoe UI 13, dim)
```

### Behaviors

#### Countdown number label

- **Variable:** `self._var` (StringVar)
- **Updated by:** `update_count(n)` called every second from `app._countdown()`
- **Values:** Decrements from `delay_sec` → 1 → 0 (triggers screenshot at 0)

#### Esc to cancel

- **Bind:** `self.bind("<Escape>", self._on_escape)` + pynput global listener
- **Why pynput:** `overrideredirect(True)` prevents WM from giving keyboard focus → tkinter `<Escape>` bind alone does not work
- **Listener starts:** `after(50ms)` post-render
- **On Esc:** `close()` → `app._cancel_countdown()`

#### `close()`

- Sets `self._alive = False`
- Stops pynput listener
- `destroy()` if window still exists

#### `_on_escape()`

- Called from both tkinter bind and pynput listener
- Guarded by `self._alive` flag to prevent double-fire

---

## RegionSelector

**Class:** `RegionSelector(tk.Toplevel)`
**Opened by:** `ScreenWatermarkApp._show_region_selector()`

### Window properties

| Property | Value |
|---|---|
| Geometry | Full screen |
| `overrideredirect` | `True` |
| Alpha | `0.25` (dark semi-transparent) |
| Background | `#000000` |
| Always on top | `True` |
| Cursor | `crosshair` |

### Layout

```
RegionSelector (fullscreen)
└── Canvas (fills window)
    ├── Hint text: "Click and drag to select area\nEscape = Cancel"
    └── Selection rect (drawn on drag)
```

### Behaviors

#### Mouse press (`<ButtonPress-1>`)

- Records `self._start = (abs_x, abs_y)` (screen coordinates)
- Clears hint text from canvas

#### Mouse drag (`<B1-Motion>`)

- Draws/redraws selection rectangle on canvas
- Rectangle: `outline=ACCENT, width=2, fill=ACCENT, stipple="gray25"`

#### Mouse release (`<ButtonRelease-1>`)

- Computes selected region `(x1, y1, x2, y2)` in screen coordinates
- If selection < 10px in either dimension → `on_cancel()` (too small, ignore)
- Otherwise → `on_select(min_x, min_y, max_x, max_y)`
- `_done` flag prevents double-fire

#### Esc to cancel

- Same dual-mechanism as `CountdownOverlay`: tkinter bind + pynput listener
- Listener starts after `60ms` delay (lets WM transfer focus first)
- On Esc → `_safe_destroy_and_cancel()`

#### `_safe_destroy_and_cancel()`

1. `grab_release()` — release mouse grab
2. `attributes("-topmost", False)` + `attributes("-alpha", 0.0)` — visually disappear immediately
3. `destroy()` — no delay
4. `focus_force()` to master (only if master is not iconic — prevents spurious window restore)
5. `on_cancel()`

#### Callbacks

| Callback | When called | Signature |
|---|---|---|
| `on_select` | Valid region selected | `on_select(x1, y1, x2, y2)` |
| `on_cancel` | Esc pressed or region too small | `on_cancel()` |
