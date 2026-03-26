"""
ScreenWatermark Pro - System Hotkeys Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import sys
import threading

HOTKEY_PRESETS = [
    ("Print Screen",          "<print_screen>"),
    ("Shift+F9",              "<shift>+<f9>"),
    ("Ctrl+F9",               "<ctrl>+<f9>"),
    ("Ctrl+Print Screen",     "<ctrl>+<print_screen>"),
    ("Ctrl+Shift+F9",         "<ctrl>+<shift>+<f9>"),
    ("Shift+Print Screen",    "<shift>+<print_screen>"),
    ("Ctrl+Shift+F10",        "<ctrl>+<shift>+<f10>"),
    ("Ctrl+Shift+F11",        "<ctrl>+<shift>+<f11>"),
    ("Ctrl+Shift+F12",        "<ctrl>+<shift>+<f12>"),
    ("Ctrl+Shift+S",          "<ctrl>+<shift>+s"),
    ("Ctrl+Shift+R",          "<ctrl>+<shift>+r"),
    ("Ctrl+Shift+H",          "<ctrl>+<shift>+h"),
    ("Ctrl+Shift+X",          "<ctrl>+<shift>+x"),
    ("Ctrl+Alt+S",            "<ctrl>+<alt>+s"),
    ("Ctrl+Alt+F",            "<ctrl>+<alt>+f"),
    ("Ctrl+Alt+P",            "<ctrl>+<alt>+p"),
    ("F9",                    "<f9>"),
    ("F10",                   "<f10>"),
    ("F11",                   "<f11>"),
    ("F12",                   "<f12>"),
]

_PRESET_LABEL = {v: k for k, v in HOTKEY_PRESETS}

def _preset_label(pynput_val: str) -> str:
    return _PRESET_LABEL.get(pynput_val.strip().lower(), pynput_val)

def _preset_value(label: str) -> str:
    for k, v in HOTKEY_PRESETS:
        if k == label:
            return v
    return label

_pynput_kb    = None
_HK_MOD_NAMES = None

def _ensure_pynput():
    global _pynput_kb, _HK_MOD_NAMES
    if _pynput_kb is not None:
        return
    from pynput import keyboard as _kb
    _pynput_kb = _kb
    _HK_MOD_NAMES = frozenset({
        _kb.Key.ctrl,  _kb.Key.ctrl_l,  _kb.Key.ctrl_r,
        _kb.Key.shift, _kb.Key.shift_l, _kb.Key.shift_r,
        _kb.Key.alt,   _kb.Key.alt_l,   _kb.Key.alt_r,  _kb.Key.alt_gr,
        _kb.Key.cmd,   _kb.Key.cmd_l,   _kb.Key.cmd_r,
    })


class HotkeyManager:
    def __init__(self):
        self._callbacks = {}
        self._listener = None
        self._active_slots = set()
        self._lock = threading.Lock()

    def _rebuild(self):
        if self._listener:
            try:
                self._listener.stop()
            except: pass
            self._listener = None
        if not self._callbacks:
            return
        mapping = {hk: cb for hk, (slot, cb) in self._callbacks.items()}
        try:
            new_listener = _pynput_kb.GlobalHotKeys(mapping)
            new_listener.daemon = True
            self._listener = new_listener
        except Exception as e:
            print(f"[HotkeyManager] rebuild gagal: {e}", file=sys.stderr)
            self._listener = None
            return
        self._start_listener = new_listener

    def register(self, slot: str, hotkey_str: str, callback) -> bool:
        if not hotkey_str.strip(): return False
        _ensure_pynput()
        with self._lock:
            self._callbacks = {hk: (s, cb) for hk, (s, cb) in self._callbacks.items()
                               if s != slot}
            self._callbacks[hotkey_str] = (slot, callback)
            self._active_slots.add(slot)
            self._start_listener = None
            self._rebuild()
            ok = self._listener is not None
        if hasattr(self, "_start_listener") and self._start_listener:
            try: self._start_listener.start()
            except Exception: pass
            self._start_listener = None
        return ok

    def unregister(self, slot: str):
        with self._lock:
            self._callbacks = {hk: (s, cb) for hk, (s, cb) in self._callbacks.items()
                               if s != slot}
            self._active_slots.discard(slot)
            self._start_listener = None
            self._rebuild()
        if hasattr(self, "_start_listener") and self._start_listener:
            try: self._start_listener.start()
            except Exception: pass
            self._start_listener = None

    def unregister_all(self):
        with self._lock:
            self._callbacks.clear()
            self._active_slots.clear()
            if self._listener:
                try: self._listener.stop()
                except: pass
                self._listener = None

    def is_active(self, slot: str) -> bool:
        with self._lock:
            return slot in self._active_slots


class HotkeyRecorder:
    _SPECIAL = None

    def __init__(self, slot_name, var, entry, apply_btn, status_lbl,
                 app, settings_win, apply_fn):
        self.slot_name = slot_name
        self.var = var
        self.entry = entry
        self.apply_btn = apply_btn
        self.status_lbl = status_lbl
        self.app = app
        self.settings_win = settings_win
        self.apply_fn = apply_fn
        self._recording_event = threading.Event()
        self.is_last_focused = False
        self._listener = None
        self._prev_value = var.get()
        self._mods_held = set()
        self._pending_value = None

    @property
    def recording(self) -> bool:
        return self._recording_event.is_set()

    @recording.setter
    def recording(self, value: bool):
        if value:
            self._recording_event.set()
        else:
            self._recording_event.clear()

    def start(self):
        self.is_last_focused = True
        for other_slot, rec in self.settings_win._hk_recorders.items():
            if rec is not self:
                rec.is_last_focused = False
                if rec.recording:
                    rec.cancel_if_recording(skip_reregister=True)

        if self.recording:
            self._stop_listener()

        self._prev_value = self.var.get()
        self._mods_held = set()
        self.recording = True

        if self.entry.winfo_exists():
            self.entry.config(state="normal", bg="#1a2a1a", fg="#43e97b")

        self.app._hk_recording_active = True
        self.var.set("recording...")

        self.app._hotkey_mgr.unregister_all()
        _ensure_pynput()
        self._listener = _pynput_kb.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def cancel_if_recording(self, skip_reregister: bool = False):
        if not self.recording:
            return
        self.recording = False
        self._stop_listener()
        self.app._hk_recording_active = False
        self._pending_value = None
        self.var.set(self._prev_value)
        if self.entry.winfo_exists():
            self.entry.config(state="readonly", bg="#252535", fg="#6c63ff")
        if self.apply_btn.winfo_exists():
            self.apply_btn.config(bg="#6c63ff", fg="white", text="Terapkan")
        if not skip_reregister:
            self.app._register_all_hotkeys()

    def manual_apply(self):
        if self.recording:
            self.cancel_if_recording()
            return
        if self._pending_value is not None:
            self._pending_value = None
            if self.entry.winfo_exists():
                self.entry.config(state="readonly", bg="#252535", fg="#6c63ff")
            self.apply_fn()
            self.app._register_all_hotkeys()
        else:
            self.apply_fn()
            self.app._register_all_hotkeys()
        if self.apply_btn.winfo_exists():
            self.apply_btn.config(bg="#43e97b", fg="white", text="Active")
            self.apply_btn.after(1800,
                lambda: self.apply_btn.config(bg="#6c63ff", fg="white", text="Terapkan")
                        if self.apply_btn.winfo_exists() else None)
        try:
            if self.settings_win.winfo_exists():
                self.settings_win.refresh_hotkey_status()
        except Exception:
            pass

    def apply_preset(self, hk: str):
        if self.recording:
            self.recording = False
            self._stop_listener()
            self.app._hk_recording_active = False
        self._mods_held = set()
        self._pending_value = hk
        self.app._hk_recording_active = True
        try:
            self.var.set(hk)
        finally:
            self.app._hk_recording_active = False
  
