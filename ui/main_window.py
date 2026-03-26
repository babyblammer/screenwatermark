"""
ScreenWatermark Pro - UI Main Window Module (CTk Version)
v8.0 Migration from tkinter to customtkinter
"""

import io
import os
import re
import sys
import threading
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
import mss
import pystray
from PIL import Image, ImageDraw, ImageTk

from core.constants import (BG, PANEL, CARD, CARD2, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, 
                          BORDER, WARN, PREVIEW_W, PREVIEW_H, HISTORY_MAX, FONT, FONT_MONO)
from core.settings import load_settings, save_settings
from core.history import save_history, load_history, _enqueue_save_history, _history_io_q
from core.render import apply_watermark, apply_timestamp
from core.clipboard import copy_image_to_clipboard
from core.font_cache import load_font
from core.wm_cache import invalidate_wm_cache
from core.utils import safe_hex_to_rgb, safe_strftime
from system.hotkeys import HotkeyManager, _preset_label
from system.tray import _make_tray_icon, _win_toast
from system.startup import get_run_at_startup
from system.ipc import _acquire_single_instance, _ipc_server_thread, _SW_IPC_SERVER, _SW_LOCK_FILE, _ipc_pending_show
from ui.overlays import CountdownOverlay, RegionSelector
from ui.history_popup import HistoryPopup
from ui.settings_window import SettingsWindow
import i18n
from i18n import t


class ScreenWatermarkApp(ctk.CTk):
    VERSION = "3.9.1f"

    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("ScreenWatermark Pro")
        self.geometry("620x580")
        self.minsize(620, 580)
        self.maxsize(620, 580)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        
        # Apply CTk styling
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG)
        
        # Load settings
        cfg = load_settings()

        # ── Tkinter vars (still using tk vars for compatibility) ──────────────────
        self.watermark_path    = ctk.StringVar(value=cfg["watermark_path"])
        self.wm_enabled        = ctk.BooleanVar(value=bool(cfg.get("wm_enabled", True)))
        self.wm_position       = ctk.StringVar(value=cfg["wm_position"])
        self.wm_opacity        = ctk.IntVar(value=int(cfg["wm_opacity"]))
        self.wm_scale          = ctk.IntVar(value=int(cfg["wm_scale"]))
        self.wm_mode           = ctk.StringVar(value=cfg.get("wm_mode", "normal"))
        self.ts_enabled        = ctk.BooleanVar(value=bool(cfg["ts_enabled"]))
        self.ts_format         = ctk.StringVar(value=cfg["ts_format"])
        self.ts_position       = ctk.StringVar(value=cfg["ts_position"])
        self.ts_font_size      = ctk.IntVar(value=int(cfg["ts_font_size"]))
        self.ts_color          = ctk.StringVar(value=cfg["ts_color"])
        self.ts_bg_color       = ctk.StringVar(value=cfg["ts_bg_color"])
        self.ts_bg_opacity     = ctk.IntVar(value=int(cfg["ts_bg_opacity"]))
        self.ts_shadow         = ctk.BooleanVar(value=bool(cfg["ts_shadow"]))
        self.ts_bold           = ctk.BooleanVar(value=bool(cfg.get("ts_bold", False)))
        self.ts_outside_canvas = ctk.BooleanVar(value=bool(cfg.get("ts_outside_canvas", False)))
        self.delay_sec         = ctk.IntVar(value=int(cfg["delay_sec"]))
        self.hotkey_fullscreen = ctk.StringVar(value=cfg.get("hotkey_fullscreen","<print_screen>"))
        self.hotkey_region     = ctk.StringVar(value=cfg.get("hotkey_region", "<ctrl>+<shift>+<f9>"))
        _hk_history_raw = cfg.get("hotkey_history", "<ctrl>+<f9>")
        _CONFLICT_HOTKEYS = {"<shift>+<print_screen>", "<ctrl>+<shift>+h>", "<ctrl>+<shift>+h", "<shift>+<f9>", "<ctrl>+<print_screen>"}
        if _hk_history_raw in _CONFLICT_HOTKEYS:
            _hk_history_raw = "<ctrl>+<f9>"
        self.hotkey_history    = ctk.StringVar(value=_hk_history_raw)
        self.capture_mode      = ctk.StringVar(value=cfg.get("capture_mode", "fullscreen"))
        self.run_at_startup    = ctk.BooleanVar(value=bool(cfg.get("run_at_startup", False)))
        self.start_minimized   = ctk.BooleanVar(value=bool(cfg.get("start_minimized", False)))

        # ── State ────────────────────────────────────────────────────────────────
        self.last_image: "Image.Image | None" = None
        self.preview_tk        = None
        self._tray_icon        = None
        self._is_quitting      = False
        self._screenshot_lock  = threading.Lock()
        self._history_lock     = threading.Lock()
        self._countdown_job    = None
        self._autosave_job     = None
        self._preview_job      = None
        self._countdown_overlay: "CountdownOverlay | None" = None
        self._hotkey_mgr       = HotkeyManager()
        self._settings_win: "SettingsWindow | None" = None
        self._history_popup: "HistoryPopup | None"  = None
        self._region: "tuple|None" = None
        self._settings_was_visible: bool = False
        self._settings_was_iconic:  bool = False
        self._main_was_visible: bool = True
        self._main_was_iconic:  bool = False
        self._main_prev_state:  str  = "iconic"

        self._history: deque   = deque(maxlen=HISTORY_MAX)
        self._history_tks: list = []
        self._settings_snapshot: dict = {}
        self._last_notify_time: float = 0.0

        self._hk_recording_active: bool = False

        # Build UI
        self._build_ui()
        self._refresh_snapshot()
        self.after(0, self._deferred_startup)
        self._start_tray()

        # Trace all variables
        all_vars = [
            self.watermark_path, self.wm_enabled, self.wm_position, self.wm_opacity,
            self.wm_scale, self.wm_mode, self.ts_enabled, self.ts_format, self.ts_position,
            self.ts_font_size, self.ts_color, self.ts_bg_color, self.ts_bg_opacity,
            self.ts_shadow, self.ts_bold, self.ts_outside_canvas, self.delay_sec, self.hotkey_fullscreen,
            self.hotkey_region, self.hotkey_history, self.capture_mode,
            self.run_at_startup, self.start_minimized,
        ]
        for v in all_vars:
            v.trace_add("write", lambda *_: self._on_setting_changed())

        self.after(300, self._refresh_live_preview)
        
        _launched_from_startup = "--startup" in sys.argv
        if self.start_minimized.get() and _launched_from_startup:
            self.after(100, self._hide_to_tray)

    # ── P1: Build CTk UI Shell ─────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        self._build_header()
        
        # Main content area with tabs
        self._build_main_content()
        
        # Bottom bar
        self._build_bottom_bar()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, height=44, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        # App icon
        app_icon = ctk.CTkLabel(header, text="📸", font=(FONT, 18), fg_color="transparent")
        app_icon.pack(side="left", padx=12, pady=10)
        
        # App title
        title_label = ctk.CTkLabel(
            header, text="ScreenWatermark Pro",
            font=(FONT, 12, "bold"), text_color=TEXT, fg_color="transparent")
        title_label.pack(side="left", padx=(0, 8), pady=10)
        
        # WM badge (pill style)
        self.wm_indicator = ctk.CTkLabel(
            header, text="WM: ✓", 
            font=(FONT_MONO, 9, "bold"), 
            text_color=SUCCESS, fg_color="#152515",
            corner_radius=20, padx=8, pady=2)
        self.wm_indicator.pack(side="left", padx=8, pady=10)
        self._update_wm_indicator()
        
        # Spacer
        spacer = ctk.CTkFrame(header, fg_color="transparent", width=0)
        spacer.pack(side="left", expand=True, fill="x")
        
        # History button
        self.btn_history = ctk.CTkButton(
            header, text="🕒", font=(FONT, 12),
            fg_color="transparent", hover_color=CARD2, text_color=MUTED,
            corner_radius=6, border_width=1, border_color=BORDER,
            width=36, height=28,
            command=self._show_history_popup)
        self.btn_history.pack(side="right", padx=(0, 8), pady=8)
        
        # Settings button
        self.btn_settings = ctk.CTkButton(
            header, text=f"⚙ {t('settings')}", font=(FONT, 9, "bold"),
            fg_color=ACCENT, hover_color="#7d75ff", text_color="white",
            corner_radius=6, border_width=0, width=90, height=28,
            command=self._open_settings)
        self.btn_settings.pack(side="right", padx=12, pady=8)
    # ── Mode & Helpers ───────────────────────────────────────────────────────

    def _build_main_content(self):
        self.middle_frame = ctk.CTkScrollableFrame(
            self, height=484, fg_color=BG, corner_radius=0,
            scrollbar_button_color=ACCENT, scrollbar_button_hover_color="#7d75ff"
        )
        self.middle_frame.pack(fill="x", padx=10, pady=(8, 0))
        
        self._build_panel_toggle()
        self._build_preview_and_history()
        self._build_watermark_controls()
        self._build_timestamp_controls()

    def _build_panel_toggle(self):
        container = ctk.CTkFrame(self.middle_frame, fg_color=CARD,
                                 corner_radius=9, border_width=1, border_color=BORDER)
        container.pack(anchor="w", padx=0, pady=(0, 8))
        
        self.btn_panel_preview = ctk.CTkButton(
            container, text=f"🖼  {t('preview')}",
            fg_color=ACCENT, hover_color="#7d75ff", text_color="white",
            corner_radius=7, height=28, width=100,
            command=lambda: self._switch_panel("preview"))
        self.btn_panel_preview.pack(side="left", padx=3, pady=3)
        
        hist_container = ctk.CTkFrame(container, fg_color="transparent")
        hist_container.pack(side="left", padx=(0, 3))
        
        self.btn_panel_history = ctk.CTkButton(
            hist_container, text=f"🕒  {t('history')}",
            fg_color="transparent", hover_color=CARD2, text_color=MUTED,
            corner_radius=7, height=28, width=100,
            command=lambda: self._switch_panel("history"))
        self.btn_panel_history.pack(side="left")
        
        self.hist_badge = ctk.CTkLabel(
            hist_container, text="", fg_color=ACCENT2, text_color="white",
            corner_radius=10, font=(FONT_MONO, 8), width=0, height=16, padx=5)
        self.hist_badge.pack(side="left", padx=(4, 0))
        self._update_history_badge()

    def _switch_panel(self, which: str):
        self._panel_mode = which
        if which == "preview":
            self.history_panel_wrap.pack_forget()
            self.preview_wrap.pack(fill="x", pady=(0, 8))
            self.btn_panel_preview.configure(fg_color=ACCENT, text_color="white")
            self.btn_panel_history.configure(fg_color="transparent", text_color=MUTED)
            self._set_accordions_enabled(True)
        else:
            self.preview_wrap.pack_forget()
            self.history_panel_wrap.pack(fill="x", pady=(0, 8))
            self.btn_panel_history.configure(fg_color=ACCENT, text_color="white")
            self.btn_panel_preview.configure(fg_color="transparent", text_color=MUTED)
            self._set_accordions_enabled(False)
            self._render_history_panel()

    def _set_accordions_enabled(self, enabled: bool):
        if enabled:
            for widget in self.wm_accordion.winfo_children():
                widget.configure(state="normal")
            for widget in self.ts_accordion.winfo_children():
                widget.configure(state="normal")
            self.wm_accordion.configure(border_color=BORDER)
            self.ts_accordion.configure(border_color=BORDER)
        else:
            for widget in self.wm_accordion.winfo_children():
                widget.configure(state="disabled")
            for widget in self.ts_accordion.winfo_children():
                widget.configure(state="disabled")
            self.wm_accordion.configure(border_color="#1a1a26")
            self.ts_accordion.configure(border_color="#1a1a26")

    def _update_history_badge(self):
        if not hasattr(self, "hist_badge"):
            return
        with self._history_lock:
            count = len(self._history)
        if count == 0:
            self.hist_badge.configure(text="", fg_color="transparent")
        else:
            self.hist_badge.configure(text=str(count), fg_color=ACCENT2)

    def _build_preview_and_history(self):
        self.preview_wrap = ctk.CTkFrame(
            self.middle_frame, height=180, fg_color=CARD, corner_radius=10,
            border_width=1, border_color=BORDER)
        self.preview_wrap.pack_propagate(False)
        
        preview_inner = ctk.CTkFrame(self.preview_wrap, fg_color="#0c0c18")
        preview_inner.pack(fill="both", expand=True)
        
        self.preview_canvas = tk.Canvas(preview_inner, width=PREVIEW_W, height=PREVIEW_H,
                                        bg="#0c0c18", highlightthickness=0)
        self.preview_canvas.pack(padx=10, pady=10)
        
        self.history_panel_wrap = ctk.CTkFrame(
            self.middle_frame, height=180, fg_color=CARD, corner_radius=10,
            border_width=1, border_color=BORDER)
        self.history_panel_wrap.pack_propagate(False)
        
        hist_topbar = ctk.CTkFrame(self.history_panel_wrap, fg_color="transparent")
        hist_topbar.pack(fill="x", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(hist_topbar, text=t("history_tab_hint"),
                     font=(FONT_MONO, 9), text_color=MUTED, fg_color="transparent").pack(side="left")
        
        ctk.CTkButton(hist_topbar, text=t("clear_history"), font=(FONT, 8),
                      fg_color="transparent", hover_color=BORDER, text_color=MUTED,
                      corner_radius=4, width=70, height=22,
                      command=self._clear_all_history).pack(side="right")
        
        self.history_scroll = ctk.CTkScrollableFrame(
            self.history_panel_wrap, fg_color=BG, scrollbar_button_color=BORDER,
            orientation="horizontal", height=120)
        self.history_scroll.pack(fill="x", padx=12, pady=(0, 8))

    def _render_history_panel(self):
        if not hasattr(self, 'history_scroll'):
            return
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        with self._history_lock:
            entries = list(self._history)
        
        self._update_history_badge()
        
        if not entries:
            ctk.CTkLabel(self.history_scroll, text=t("history_empty"),
                        font=(FONT, 9), text_color=MUTED).pack(pady=40)
            return
        
        for idx, entry in enumerate(reversed(entries)):
            item = ctk.CTkFrame(self.history_scroll, fg_color=CARD2, corner_radius=6)
            item.pack(side="left", padx=4)
            
            img_label = ctk.CTkLabel(item, text="", width=108, height=60)
            img_label.pack()
            
            meta = ctk.CTkLabel(item, text=entry.get("time", "")[:16],
                               font=(FONT_MONO, 8), text_color=MUTED)
            meta.pack(pady=2)

    def _build_bottom_bar(self):
        """P5: Build bottom bar with SplitShotButton."""
        from ui.widgets.shot_buttons import SplitShotButton
        
        bottom_bar = ctk.CTkFrame(self, fg_color=PANEL, height=52, corner_radius=0)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)
        
        # Status on left
        self.status_var = ctk.StringVar(value=f"{t('status_ready')} - {self.hotkey_fullscreen.get()} | {self.hotkey_region.get()} | {self.hotkey_history.get()}")
        ctk.CTkLabel(bottom_bar, textvariable=self.status_var, font=(FONT, 8),
                    text_color=MUTED, fg_color="transparent").pack(side="left", padx=14, pady=16)
        
        # Copy button
        self.btn_copy = ctk.CTkButton(
            bottom_bar, text=t("copy"), font=(FONT, 9, "bold"),
            fg_color=ACCENT2, hover_color="#e05570", text_color="white",
            corner_radius=6, border_width=0, width=70, height=30,
            command=self._copy_to_clipboard, state="disabled")
        self.btn_copy.pack(side="right", padx=6, pady=10)
        
        # Split shot button (P5)
        self.shot_btn = SplitShotButton(
            bottom_bar,
            on_fullscreen=self._trigger_fullscreen,
            on_region=self._trigger_region)
        self.shot_btn.pack(side="right", padx=4, pady=10)
        
        # Legacy btn_shot for compatibility (hidden reference)
        self.btn_shot = self.shot_btn._btn_fullscreen
        
        # History button
        ctk.CTkButton(
            bottom_bar, text="Riwayat", font=(FONT, 8),
            fg_color="transparent", hover_color=BORDER, text_color=MUTED,
            corner_radius=4, border_width=1, border_color=BORDER, width=60, height=26,
            command=self._go_history_tab).pack(side="right", padx=4, pady=10)
        
        # Set initial mode
        self.after(10, self._on_mode_change)
    def _update_wm_indicator(self):
        """Update WM indicator in header."""
        enabled = self.wm_enabled.get()
        has_file = bool(self.watermark_path.get())
        if not enabled:
            self.wm_indicator.configure(text="WM: OFF", text_color=MUTED)
        elif not has_file:
            self.wm_indicator.configure(text="WM: ⚠", text_color=WARN)
        else:
            self.wm_indicator.configure(text="WM: ✓", text_color=SUCCESS)

    def _go_history_tab(self):
        """Switch to history tab."""
        self.tabview.set("Riwayat")



    # ── Snapshot & autosave ───────────────────────────────────────────────────
    def _deferred_startup(self):
        def _load():
            done = threading.Event()
            result: list = []
            def _task():
                result.append(load_history())
                done.set()
            _history_io_q.put((_task, (), {}))
            done.wait(timeout=10)
            entries = result[0] if result else []
            if not self._is_quitting:
                self.after(0, lambda: self._apply_loaded_history(entries))
        threading.Thread(target=_load, daemon=True, name="ScreenWM-HistoryLoad").start()
        self._register_all_hotkeys()

    def _apply_loaded_history(self, entries: list):
        if self._is_quitting: return
        with self._history_lock:
            for entry in entries:
                self._history.append(entry)
        self._render_history()

    def _refresh_snapshot(self):
        self._settings_snapshot = {
            "watermark_path":    self.watermark_path.get(),
            "wm_enabled":        self.wm_enabled.get(),
            "wm_position":       self.wm_position.get(),
            "wm_opacity":        self.wm_opacity.get(),
            "wm_scale":          self.wm_scale.get(),
            "wm_mode":           self.wm_mode.get(),
            "ts_enabled":        self.ts_enabled.get(),
            "ts_format":         self.ts_format.get(),
            "ts_position":       self.ts_position.get(),
            "ts_font_size":      self.ts_font_size.get(),
            "ts_color":          self.ts_color.get(),
            "ts_bg_color":       self.ts_bg_color.get(),
            "ts_bg_opacity":     self.ts_bg_opacity.get(),
            "ts_shadow":         self.ts_shadow.get(),
            "ts_bold":           self.ts_bold.get(),
            "ts_outside_canvas": self.ts_outside_canvas.get(),
            "delay_sec":         self.delay_sec.get(),
            "hotkey_fullscreen": self.hotkey_fullscreen.get(),
            "hotkey_region":     self.hotkey_region.get(),
            "hotkey_history":    self.hotkey_history.get(),
            "capture_mode":      self.capture_mode.get(),
            "run_at_startup":    self.run_at_startup.get(),
            "start_minimized":   self.start_minimized.get(),
        }

    def _on_setting_changed(self):
        if self._hk_recording_active: return
        self._refresh_snapshot()
        if self._autosave_job: self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(800, self._do_autosave)
        if self._preview_job: self.after_cancel(self._preview_job)
        self._preview_job = self.after(350, self._refresh_live_preview)

    def _do_autosave(self):
        self._autosave_job = None
        ok = save_settings(self._settings_snapshot)
        if ok and not self._is_quitting:
            self.status_var.set(t("saved"))
            self.after(2000, self._restore_status)

    def _restore_status(self):
        if not self._is_quitting:
            if self._hk_recording_active: return
            snap = self._settings_snapshot
            self.status_var.set(
                f"Siap — {_preset_label(snap.get('hotkey_fullscreen', self.hotkey_fullscreen.get()))} | "
                f"{_preset_label(snap.get('hotkey_region', self.hotkey_region.get()))} | "
                f"{_preset_label(snap.get('hotkey_history', self.hotkey_history.get()))}")

    # ── Live preview ─────────────────────────────────────────────────────────
    def _refresh_live_preview(self):
        self._preview_job = None
        cfg = self._settings_snapshot.copy()

        def _render() -> "Image.Image":
            pw, ph = PREVIEW_W, PREVIEW_H
            base = Image.new("RGB", (pw, ph), (28, 28, 42))
            d = ImageDraw.Draw(base)
            for x in range(0, pw, 40):
                d.line([(x,0),(x,ph)], fill=(42,42,62), width=1)
            for y in range(0, ph, 40):
                d.line([(0,y),(pw,y)], fill=(42,42,62), width=1)
            try:
                fnt = load_font(8)
                d.text((pw//2 - 36, ph//2 - 6), "AREA SCREENSHOT", font=fnt, fill=(60,60,92))
            except: pass

            wm_path = cfg.get("watermark_path","")
            wm_on = cfg.get("wm_enabled", True)
            if wm_on and not wm_path:
                try:
                    fnt2 = load_font(7)
                    d.text((4, 4), f"[ {t('watermark')}: {t('no_file')} ]", font=fnt2, fill=(120,80,40))
                except: pass
            elif not wm_on:
                try:
                    fnt2 = load_font(7)
                    d.text((4, 4), f"[ {t('watermark')}: {t('off')} ]", font=fnt2, fill=(100,100,100))
                except: pass

            pcfg = cfg.copy()
            pcfg["ts_font_size"] = max(8, int(cfg["ts_font_size"] * (ph/1080) * 2.4))
            pcfg["wm_scale"] = max(5, int(cfg["wm_scale"] * 0.85))
            base = apply_watermark(base, pcfg)
            base = apply_timestamp(base, pcfg)
            return base

        def _bg_render():
            try:
                img = _render()
                if not self._is_quitting:
                    self.after(0, lambda i=img: self._apply_preview(i))
            except Exception as exc:
                print(f"[Preview] render gagal: {exc}", file=sys.stderr)

        threading.Thread(target=_bg_render, daemon=True).start()

    def _apply_preview(self, img: "Image.Image"):
        if self._is_quitting: return
        try:
            if not hasattr(self, 'preview_canvas'): return
            if not self.preview_canvas.winfo_exists(): return
            tk_img = ImageTk.PhotoImage(img)
            self.preview_tk = tk_img
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, image=self.preview_tk, anchor="nw")
        except Exception: pass

    # ── Hotkeys ───────────────────────────────────────────────────────────────
    def _register_all_hotkeys(self):
        def _safe_get(var, slot_name: str) -> str:
            if self._settings_win and self._settings_win.winfo_exists():
                rec = self._settings_win._hk_recorders.get(slot_name)
                if rec and rec.recording:
                    return rec._prev_value
            return var.get()

        self._hotkey_mgr.register("fullscreen", _safe_get(self.hotkey_fullscreen, "Fullscreen"), self._hk_fullscreen)
        self._hotkey_mgr.register("region", _safe_get(self.hotkey_region, "Region"), self._hk_region)
        self._hotkey_mgr.register("history", _safe_get(self.hotkey_history, "History"), self._hk_history)

    def _hk_fullscreen(self):
        if not self._is_quitting:
            self.after(0, self._trigger_fullscreen)

    def _trigger_fullscreen(self):
        self.capture_mode.set("fullscreen")
        self._on_mode_change()
        self._start_screenshot()

    def _hk_region(self):
        if not self._is_quitting:
            self.after(0, self._trigger_region)

    def _trigger_region(self):
        self.capture_mode.set("region")
        self._on_mode_change()
        self._start_screenshot()

    def _hk_history(self):
        if not self._is_quitting:
            self.after(0, self._history_smart_open)

    def _history_smart_open(self):
        state = "normal"
        if state == "normal":
            self.lift(); self.focus_force()
            self.tabview.set("Riwayat")
        else:
            self._show_history_popup()

    def _apply_hotkey_fullscreen(self):
        hk = self.hotkey_fullscreen.get().strip()
        ok = self._hotkey_mgr.register("fullscreen", hk, self._hk_fullscreen)
        self._after_hotkey_apply("fullscreen", hk, ok)

    def _apply_hotkey_region(self):
        hk = self.hotkey_region.get().strip()
        ok = self._hotkey_mgr.register("region", hk, self._hk_region)
        self._after_hotkey_apply("region", hk, ok)

    def _apply_hotkey_history(self):
        hk = self.hotkey_history.get().strip()
        ok = self._hotkey_mgr.register("history", hk, self._hk_history)
        self._after_hotkey_apply("history", hk, ok)

    def _after_hotkey_apply(self, slot: str, hk: str, ok: bool):
        self._refresh_snapshot()
        save_settings(self._settings_snapshot)
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.refresh_hotkey_status()
        msg = f"Hotkey [{slot}]: {'aktif' if ok else 'GAGAL'} — {hk}"
        self.status_var.set(msg)
        self.after(3000, self._restore_status)

    # ── Tray ──────────────────────────────────────────────────────────────────
    def _start_tray(self):
        menu = (
            pystray.MenuItem(t("show_panel"), self._show_window, default=True),
            pystray.MenuItem(t("settings"), lambda icon, item: self.after(0, self._open_settings)),
            pystray.MenuItem(t("exit"), self._quit_app),
        )
        self._tray_icon = pystray.Icon("ScreenWatermark", _make_tray_icon(), t("app_title"), menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        self.withdraw()
        snap = self._settings_snapshot
        if self._tray_icon:
            try:
                msg = (f"FS: {_preset_label(snap.get('hotkey_fullscreen',''))}  "
                       f"| Area: {_preset_label(snap.get('hotkey_region',''))}  "
                       f"| History: {_preset_label(snap.get('hotkey_history',''))}")
                sent = _win_toast(t("run_in_background"), msg, on_click_show=True)
                if not sent:
                    self._tray_icon.notify(msg, t("run_in_background"))
            except: pass

    def _show_window(self, *_):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsWindow(self)
        else:
            self._settings_win.deiconify()
        self._settings_win.lift()
        self._settings_win.attributes("-topmost", True)
        self._settings_win.after(100, lambda: (self._settings_win.attributes("-topmost", False) if self._settings_win and self._settings_win.winfo_exists() else None))
        self._settings_win.focus_force()

    def _show_history_popup(self):
        if self._history_popup and self._history_popup.winfo_exists():
            self._history_popup._render()
            self._history_popup.lift()
            self._history_popup.focus_force()
            return
        self._history_popup = HistoryPopup(self)
        self._history_popup.focus_force()

    def _notify_history_updated(self):
        if self._history_popup and self._history_popup.winfo_exists():
            self._history_popup._render()
        if getattr(self, "_panel_mode", "preview") == "history":
            self._render_history_panel()

    def _quit_app(self, *_):
        if self._is_quitting: return
        self._is_quitting = True
        if self._settings_win and self._settings_win.winfo_exists():
            if hasattr(self._settings_win, "_hk_recorders"):
                for rec in self._settings_win._hk_recorders.values():
                    try:
                        if rec.recording:
                            rec._stop_listener()
                            rec.recording = False
                    except Exception: pass
        for job in [self._autosave_job, self._countdown_job, self._preview_job]:
            if job:
                try: self.after_cancel(job)
                except: pass
        self._autosave_job = self._countdown_job = self._preview_job = None
        save_settings(self._settings_snapshot)
        _enqueue_save_history(self._history)
        _history_io_q.join()
        self._hotkey_mgr.unregister_all()
        try: self._screenshot_lock.release()
        except RuntimeError: pass
        if self._tray_icon:
            threading.Thread(target=self._tray_icon.stop, daemon=True).start()
        self.after(300, self.destroy)

    # ── Screenshot flow ────────────────────────────────────────────────────────
    def _start_screenshot(self):
        if self._is_quitting: return
        if not self._screenshot_lock.acquire(blocking=False): return

        if self._countdown_job:
            self.after_cancel(self._countdown_job); self._countdown_job = None

        self.btn_shot.configure(state="disabled")
        self.btn_copy.configure(state="disabled")

        mode = self._settings_snapshot.get("capture_mode", "fullscreen")
        delay = self._settings_snapshot.get("delay_sec", 0)

        if mode == "region":
            _mstate = self.wm_state()
            self._main_was_visible = (_mstate in ("normal", "zoomed"))
            self._main_was_iconic = (_mstate == "iconic")
            self._main_prev_state = _mstate

            _sstate = self._settings_win.wm_state() if (self._settings_win and self._settings_win.winfo_exists()) else "withdrawn"
            self._settings_was_visible = (_sstate in ("normal", "zoomed"))
            self._settings_was_iconic = (_sstate == "iconic")
            self._settings_prev_state = _sstate

            if self._main_was_visible:
                self.withdraw()
            if self._settings_was_visible:
                self._settings_win.withdraw()

            _delay = 350 if self._main_was_iconic else 250
            self.after(_delay, self._show_region_selector)
        elif delay > 0:
            self._countdown(delay)
        else:
            self._main_prev_state = self.wm_state()
            self.status_var.set(t("taking_screenshot"))
            if self._main_prev_state in ("normal", "zoomed"):
                self.withdraw()
            self.after(200, lambda: threading.Thread(target=self._do_screenshot, args=(None,), daemon=True).start())

    def _show_region_selector(self):
        if self._is_quitting:
            try: self._screenshot_lock.release()
            except RuntimeError: pass
            return
        try:
            RegionSelector(self, on_select=self._on_region_selected, on_cancel=self._on_region_cancelled)
        except Exception as exc:
            print(f"[RegionSelector] gagal: {exc}", file=sys.stderr)
            try: self._screenshot_lock.release()
            except RuntimeError: pass
            self.after(0, self.deiconify)
            self.btn_shot.configure(state="normal")
            self.btn_copy.configure(state="normal" if self.last_image else "disabled")
            self.status_var.set(t("failed_opening_region"))
            self.after(2500, self._restore_status)

    def _on_region_selected(self, x1, y1, x2, y2):
        self._region = (x1, y1, x2, y2)
        self._refresh_snapshot()
        if getattr(self, "_main_was_visible", False):
            _prev = getattr(self, "_main_prev_state", "iconic")
            if _prev == "zoomed":
                self.after(100, lambda: self.state("zoomed"))
            else:
                self.after(100, self.deiconify)
        self._main_was_visible = False
        self._main_was_iconic = False
        self._main_prev_state = "normal"
        if getattr(self, "_settings_was_visible", False):
            if self._settings_win and self._settings_win.winfo_exists():
                self.after(150, self._settings_win.deiconify)
        self._settings_was_visible = False
        self._settings_was_iconic = False
        delay = self._settings_snapshot.get("delay_sec", 0)
        if delay > 0:
            self._countdown(delay)
        else:
            threading.Thread(target=self._do_screenshot, args=((x1,y1,x2,y2),), daemon=True).start()

    def _on_region_cancelled(self):
        self._screenshot_lock.release()
        if getattr(self, "_main_was_visible", False):
            _prev = getattr(self, "_main_prev_state", "iconic")
            if _prev == "zoomed":
                self.after(100, lambda: self.state("zoomed"))
            else:
                self.after(100, self.deiconify)
        self._main_was_visible = False
        self._main_was_iconic = False
        self._main_prev_state = "normal"
        if getattr(self, "_settings_was_visible", False):
            if self._settings_win and self._settings_win.winfo_exists():
                self.after(150, self._settings_win.deiconify)
        self._settings_was_visible = False
        self._settings_was_iconic = False
        self.btn_shot.configure(state="normal")
        self.btn_copy.configure(state="normal" if self.last_image else "disabled")
        self.status_var.set(t("region_canceled"))
        self.after(2000, self._restore_status)

    def _countdown(self, n: int):
        if self._is_quitting:
            self._screenshot_lock.release(); return

        if not hasattr(self, "_countdown_overlay") or self._countdown_overlay is None:
            self._main_prev_state = self.wm_state()
            if self._main_prev_state in ("normal", "zoomed"):
                self.withdraw()
            self._countdown_overlay = CountdownOverlay(self, n, cancel_cb=self._cancel_countdown)
        else:
            self._countdown_overlay.update_count(n)

        if n > 0:
            self.status_var.set(f"{t('countdown_text')} {n}s ({t('cancel_esc')})")
            self._countdown_job = self.after(1000, self._countdown, n - 1)
        else:
            if self._countdown_overlay:
                self._countdown_overlay.close()
                self._countdown_overlay = None
            self._countdown_job = None
            self.status_var.set(t("taking_screenshot"))
            region = self._region if self._settings_snapshot.get("capture_mode") == "region" else None
            threading.Thread(target=self._do_screenshot, args=(region,), daemon=True).start()

    def _cancel_countdown(self, event=None):
        if self._countdown_job:
            self.after_cancel(self._countdown_job)
            self._countdown_job = None
        if hasattr(self, "_countdown_overlay") and self._countdown_overlay:
            try: self._countdown_overlay.close()
            except Exception: pass
            self._countdown_overlay = None
        _prev = getattr(self, "_main_prev_state", "iconic")
        if _prev == "zoomed":
            self.state("zoomed")
        elif _prev == "normal":
            self.deiconify()
        try: self._screenshot_lock.release()
        except RuntimeError: pass
        self.btn_shot.configure(state="normal")
        self.btn_copy.configure(state="normal" if self.last_image else "disabled")
        self.status_var.set(t("countdown_canceled"))
        self.after(2000, self._restore_status)

    def _do_screenshot(self, region: "tuple|None"):
        cfg = self._settings_snapshot.copy()
        try:
            capture_time = datetime.now()
            with mss.mss() as sct:
                if region:
                    x1,y1,x2,y2 = region
                    mon = {"left":x1,"top":y1,"width":x2-x1,"height":y2-y1}
                else:
                    mon = sct.monitors[0]
                raw = sct.grab(mon)
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

            img = apply_watermark(img, cfg)
            img = apply_timestamp(img, cfg, capture_time=capture_time)
            self.last_image = img

            tb, fb = io.BytesIO(), io.BytesIO()
            _th = img.copy(); _th.thumbnail((180, 101), Image.LANCZOS)
            _th.save(tb, "JPEG", quality=85, optimize=True)
            img.save(fb, "PNG", optimize=True, compress_level=6)
            entry = {
                "entry_id": str(uuid.uuid4()),
                "thumb_bytes": tb.getvalue(),
                "full_bytes": fb.getvalue(),
                "timestamp": capture_time,
                "width": img.width,
                "height": img.height,
            }
            with self._history_lock:
                self._history.append(entry)
            _enqueue_save_history(self._history, self._history_lock)

            copy_image_to_clipboard(img)

            if not self._is_quitting:
                self.after(0, self._render_history)
                self.after(0, self._notify_history_updated)
                self.after(0, lambda i=img: self._update_preview_from_screenshot(i))
                self.after(0, lambda: self.status_var.set(t("screenshot_copied")))
                self.after(0, lambda: self.btn_copy.configure(state="normal", fg_color=SUCCESS))
                self.after(2500, lambda: self.btn_copy.configure(fg_color=ACCENT2))
                self.after(3000, self._restore_status)

            if self._tray_icon and not self._is_quitting:
                try:
                    import time as _time
                    _now = _time.monotonic()
                    if _now - self._last_notify_time >= 3.0:
                        self._last_notify_time = _now
                        sent = _win_toast(t("app_title"), t("screenshot_copied"), on_click_show=True)
                        if not sent:
                            self._tray_icon.notify(t("screenshot_copied"), t("app_title"))
                        self._tray_icon.title = f"{t('app_title')}\nTerakhir: {datetime.now().strftime('%H:%M:%S')}"
                except: pass
        except Exception as e:
            err = str(e)
            if not self._is_quitting:
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showerror("Error", t("screenshot_failed").format(err=err)))
                self.after(0, lambda: self.status_var.set(t("status_failed")))
                self.after(0, lambda: self.btn_copy.configure(state="normal" if self.last_image else "disabled"))
                self.after(3000, self._restore_status)
        finally:
            self._screenshot_lock.release()
            if not self._is_quitting:
                if region is None:
                    _prev = getattr(self, "_main_prev_state", "iconic")
                    if _prev in ("normal", "zoomed"):
                        self.after(0, self.deiconify)
                self.after(0, lambda: self.btn_shot.configure(state="normal"))

    def _update_preview_from_screenshot(self, img: "Image.Image"):
        if self._is_quitting: return
        try:
            if not hasattr(self, "preview_canvas"): return
            if not self.preview_canvas.winfo_exists(): return
            thumb = img.copy()
            thumb.thumbnail((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
            bg = Image.new("RGB", (PREVIEW_W, PREVIEW_H), (10, 10, 18))
            ox = (PREVIEW_W - thumb.width) // 2
            oy = (PREVIEW_H - thumb.height) // 2
            bg.paste(thumb, (ox, oy))
            tk_img = ImageTk.PhotoImage(bg)
            self.preview_tk = tk_img
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, image=self.preview_tk, anchor="nw")
        except Exception as exc:
            print(f"[Preview] update gagal: {exc}", file=sys.stderr)

    def _copy_to_clipboard(self):
        if self.last_image is None:
            from tkinter import messagebox
            messagebox.showwarning("Peringatan", t("no_screenshot_yet")); return
        try:
            copy_image_to_clipboard(self.last_image)
            self.status_var.set(t("copied_to_clipboard"))
            self.btn_copy.configure(fg_color=SUCCESS)
            self.after(2000, lambda: self.btn_copy.configure(fg_color=ACCENT2))
            self.after(2500, self._restore_status)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror(t("clipboard_failed"), f"Gagal:\n\n{e}\n\npip install pywin32>=306")

    def _clear_all_history(self):
        if not self._history: return
        from tkinter import messagebox
        if messagebox.askyesno("Konfirmasi", t("clear_history_confirm")):
            with self._history_lock:
                self._history.clear()
            _enqueue_save_history(self._history)
            self._render_history()
            self.status_var.set(t("history_cleared"))
            self.after(2000, self._restore_status)

    def _render_history(self):
        if not hasattr(self, 'history_scroll'): return
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        self._history_tks.clear()

        with self._history_lock:
            entries = list(self._history)

        if hasattr(self, "btn_clear_history") and self.btn_clear_history.winfo_exists():
            self.btn_clear_history.configure(state="normal" if entries else "disabled")

        if not entries:
            ctk.CTkLabel(self.history_scroll, text=t("history_empty"), font=(FONT, 9), text_color=MUTED).pack(pady=40)
            return

        for idx, entry in enumerate(reversed(entries)):
            item = ctk.CTkFrame(self.history_scroll, fg_color=CARD, corner_radius=6)
            item.pack(fill="x", pady=(0, 6), padx=2)
            
            try:
                tk_img = ImageTk.PhotoImage(Image.open(io.BytesIO(entry["thumb_bytes"])))
            except:
                tk_img = None
            if tk_img:
                self._history_tks.append(tk_img)
                ctk.CTkLabel(item, image=tk_img, text="").pack(side="left", padx=(8, 10))

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="y", anchor="n", pady=6)
            
            ctk.CTkLabel(info, text=f"#{len(entries)-idx}", font=(FONT, 11, "bold"), text_color=ACCENT).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{entry['width']} x {entry['height']} px", font=(FONT, 8), text_color=MUTED).pack(anchor="w")
            ctk.CTkLabel(info, text=entry["timestamp"].strftime("%H:%M:%S  %d/%m/%Y"), font=(FONT, 9), text_color=TEXT).pack(anchor="w")

            btn_row = ctk.CTkFrame(info, fg_color="transparent")
            btn_row.pack(anchor="w", pady=(6, 0))
            
            ctk.CTkButton(btn_row, text="Salin", font=(FONT, 8), fg_color=ACCENT, hover_color="#5a52e0",
                          text_color="white", corner_radius=4, width=50, height=24,
                          command=lambda e=entry: self._load_from_history(e)).pack(side="left")
            ctk.CTkButton(btn_row, text="X", font=(FONT, 8), fg_color="transparent", hover_color=BORDER,
                          text_color=MUTED, corner_radius=4, width=24, height=24,
                          command=lambda e=entry: self._delete_history_entry(e)).pack(side="left", padx=(4, 0))

    def _delete_history_entry(self, entry: dict):
        target_id = entry.get("entry_id")
        with self._history_lock:
            new_items = [e for e in self._history if e.get("entry_id") != target_id]
            if len(new_items) == len(self._history): return
            self._history.clear()
            for e in new_items: self._history.append(e)
        _enqueue_save_history(self._history)
        self._render_history()

    def _load_from_history(self, entry: dict):
        try:
            img = Image.open(io.BytesIO(entry["full_bytes"]))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"{t('error_reading_history')}\n{e}"); return
        self.last_image = img
        try:
            copy_image_to_clipboard(img)
            self.status_var.set(t("screenshot_copied"))
            if hasattr(self, 'btn_copy') and self.btn_copy.winfo_exists():
                self.btn_copy.configure(state="normal", fg_color=SUCCESS)
                self.after(2500, lambda: self.btn_copy.configure(fg_color=ACCENT2) if self.btn_copy.winfo_exists() else None)
            self.after(3000, self._restore_status)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Clipboard Error", str(e))

    def _on_mode_change(self):
        if self._settings_win and self._settings_win.winfo_exists():
            try: self._settings_win.region_label.configure(text=self._region_text())
            except: pass
        try:
            mode = self._settings_snapshot.get("capture_mode", "fullscreen")
            lbl = "Fullscreen" if mode == "fullscreen" else "Region"
            self.btn_shot.configure(text=lbl)
        except Exception: pass

    def _region_text(self) -> str:
        if self._region:
            x1,y1,x2,y2 = self._region
            return f"{t('region')}: ({x1},{y1}) -> ({x2},{y2}) [{x2-x1}x{y2-y1}px]"
        return t("area_not_selected")

    def _reset_region(self):
        self._region = None
        self._update_region_display()
        self._refresh_snapshot()

    def _update_region_display(self):
        if hasattr(self, "_settings_win") and self._settings_win and hasattr(self._settings_win, "region_label"):
            try:
                self._settings_win.region_label.configure(text=self._region_text())
            except:
                pass

    def _build_watermark_controls(self):
        from ui.widgets.accordion import CTkAccordion
        self.wm_accordion = CTkAccordion(self.middle_frame, title="💧 Watermark", icon="", open_by_default=True)
        self.wm_accordion.pack(fill="x", pady=(8, 0))
        body = self.wm_accordion.body
        
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(6, 4))
        
        ctk.CTkLabel(row1, text="Enable", font=(FONT, 9), text_color=MUTED).pack(side="left")
        pill_frame = ctk.CTkFrame(row1, fg_color=CARD2, corner_radius=6)
        pill_frame.pack(side="left", padx=6)
        self.wm_on_btn = ctk.CTkButton(pill_frame, text="ON", width=50, height=22,
                                        fg_color=ACCENT, text_color="white",
                                        corner_radius=5, font=(FONT, 9),
                                        command=lambda: self._set_wm_enabled(True))
        self.wm_on_btn.pack(side="left", padx=2, pady=2)
        self.wm_off_btn = ctk.CTkButton(pill_frame, text="OFF", width=50, height=22,
                                         fg_color="transparent", text_color=MUTED,
                                         corner_radius=5, font=(FONT, 9),
                                         command=lambda: self._set_wm_enabled(False))
        self.wm_off_btn.pack(side="left", padx=2, pady=2)
        
        ctk.CTkLabel(row1, text="Mode", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        mode_frame = ctk.CTkFrame(row1, fg_color=CARD2, corner_radius=6)
        mode_frame.pack(side="left", padx=6)
        for lbl, val in [("Normal", "normal"), ("Full", "full"), ("Pattern", "pattern")]:
            is_active = self.wm_mode.get() == val
            ctk.CTkButton(mode_frame, text=lbl, width=60, height=22,
                          fg_color=ACCENT if is_active else "transparent",
                          text_color="white" if is_active else MUTED,
                          corner_radius=5, font=(FONT, 9), border_width=0,
                          command=lambda v=val: self._on_wm_mode_change(v)
                          ).pack(side="left", padx=2, pady=2)
        
        ctk.CTkLabel(row1, text="Opacity", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        self.wm_opacity_slider = ctk.CTkSlider(row1, from_=10, to=100, variable=self.wm_opacity,
                                                  width=70, height=14, fg_color=BORDER, progress_color=ACCENT,
                                                  command=lambda v: self.wm_opacity_lbl.configure(text=f"{int(float(v))}%"))
        self.wm_opacity_slider.pack(side="left", padx=4)
        self.wm_opacity_lbl = ctk.CTkLabel(row1, text=f"{self.wm_opacity.get()}%", font=(FONT_MONO, 9), text_color=ACCENT)
        self.wm_opacity_lbl.pack(side="left")
        
        self.wm_pos_row = ctk.CTkFrame(body, fg_color="transparent")
        self.wm_pos_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(self.wm_pos_row, text="Pos", font=(FONT, 9), text_color=MUTED).pack(side="left")
        for lbl, val in [("\u2199", "bottom-left"), ("\u2198", "bottom-right"), ("\u2196", "top-left"), ("\u2197", "top-right")]:
            is_active = self.wm_position.get() == val
            ctk.CTkButton(self.wm_pos_row, text=lbl, width=36, height=24,
                          fg_color=ACCENT if is_active else CARD2,
                          text_color="white" if is_active else TEXT,
                          corner_radius=4, font=(FONT, 11), border_width=0,
                          command=lambda v=val: (self.wm_position.set(v), self._refresh_wm_controls())
                          ).pack(side="left", padx=2)
        
        self.wm_scale_row = ctk.CTkFrame(body, fg_color="transparent")
        self.wm_scale_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(self.wm_scale_row, text="Scale", font=(FONT, 9), text_color=MUTED).pack(side="left")
        self.wm_scale_slider = ctk.CTkSlider(self.wm_scale_row, from_=5, to=60, variable=self.wm_scale,
                                              width=70, height=14, fg_color=BORDER, progress_color=ACCENT,
                                              command=lambda v: self.wm_scale_lbl.configure(text=f"{int(float(v))}%"))
        self.wm_scale_slider.pack(side="left", padx=4)
        self.wm_scale_lbl = ctk.CTkLabel(self.wm_scale_row, text=f"{self.wm_scale.get()}%", font=(FONT_MONO, 9), text_color=ACCENT)
        self.wm_scale_lbl.pack(side="left")
        
        file_row = ctk.CTkFrame(body, fg_color="transparent")
        file_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(file_row, text="File", font=(FONT, 9), text_color=MUTED).pack(side="left")
        self.wm_path_entry = ctk.CTkEntry(file_row, textvariable=self.watermark_path,
                                           placeholder_text=t("select_file"),
                                           fg_color=BORDER, border_color=BORDER, font=(FONT, 9), height=26)
        self.wm_path_entry.pack(side="left", fill="x", expand=True, padx=(8, 4))
        ctk.CTkButton(file_row, text="...", width=36, height=26, fg_color=BORDER,
                      hover_color="#3a3a5e", text_color=TEXT, corner_radius=4,
                      command=self._pick_watermark).pack(side="left")
        
        self.wm_summary = ctk.CTkLabel(body, text="", font=(FONT_MONO, 9), text_color=MUTED, anchor="w")
        self.wm_summary.pack(fill="x", pady=(4, 0))
        
        self._set_wm_enabled(self.wm_enabled.get())
        self._refresh_wm_controls()
        self._update_wm_summary()
        
        for v in [self.wm_enabled, self.wm_mode, self.watermark_path, self.wm_scale, self.wm_opacity]:
            v.trace_add("write", lambda *_: self._update_wm_summary())

    def _set_wm_enabled(self, enabled: bool):
        self.wm_enabled.set(enabled)
        self.wm_on_btn.configure(fg_color=ACCENT if enabled else "transparent",
                                 text_color="white" if enabled else MUTED)
        self.wm_off_btn.configure(fg_color=ACCENT if not enabled else "transparent",
                                  text_color="white" if not enabled else MUTED)
        self._refresh_wm_controls()
        self._update_wm_summary()

    def _refresh_wm_controls(self):
        enabled = self.wm_enabled.get()
        mode = self.wm_mode.get()
        show_pos = (mode == "normal")
        show_scale = (mode != "full")
        
        if enabled and show_pos:
            self.wm_pos_row.pack(fill="x", pady=(0, 4))
        else:
            self.wm_pos_row.pack_forget()
        
        if enabled and show_scale:
            self.wm_scale_row.pack(fill="x", pady=(0, 4))
        else:
            self.wm_scale_row.pack_forget()

    def _update_wm_summary(self):
        if not hasattr(self, "wm_summary"):
            return
        enabled = self.wm_enabled.get()
        if not enabled:
            self.wm_summary.configure(text="OFF", text_color=ACCENT2)
            return
        
        mode = self.wm_mode.get().capitalize()
        fname = os.path.basename(self.watermark_path.get()) or t("no_file")
        op = f"{self.wm_opacity.get()}%"
        
        if mode == "Full":
            text = f"{mode} · {fname} · {op}"
        else:
            sc = f"{self.wm_scale.get()}%"
            text = f"{mode} · {fname} · {sc} · {op}"
        
        self.wm_summary.configure(text=text, text_color=SUCCESS)

    def _build_timestamp_controls(self):
        from ui.widgets.accordion import CTkAccordion
        self.ts_accordion = CTkAccordion(self.middle_frame, title="🕐 Timestamp", icon="", open_by_default=False)
        self.ts_accordion.pack(fill="x", pady=(8, 0))
        body = self.ts_accordion.body
        
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(6, 4))
        
        ctk.CTkLabel(row1, text="Enable", font=(FONT, 9), text_color=MUTED).pack(side="left")
        pill_frame = ctk.CTkFrame(row1, fg_color=CARD2, corner_radius=6)
        pill_frame.pack(side="left", padx=6)
        self.ts_on_btn = ctk.CTkButton(pill_frame, text="ON", width=50, height=22,
                                        fg_color=ACCENT, text_color="white",
                                        corner_radius=5, font=(FONT, 9),
                                        command=lambda: self._set_ts_enabled(True))
        self.ts_on_btn.pack(side="left", padx=2, pady=2)
        self.ts_off_btn = ctk.CTkButton(pill_frame, text="OFF", width=50, height=22,
                                         fg_color="transparent", text_color=MUTED,
                                         corner_radius=5, font=(FONT, 9),
                                         command=lambda: self._set_ts_enabled(False))
        self.ts_off_btn.pack(side="left", padx=2, pady=2)
        
        ctk.CTkLabel(row1, text="Outside", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        outside_frame = ctk.CTkFrame(row1, fg_color=CARD2, corner_radius=6)
        outside_frame.pack(side="left", padx=6)
        for lbl, val in [("ON", True), ("OFF", False)]:
            is_active = self.ts_outside_canvas.get() == val
            ctk.CTkButton(outside_frame, text=lbl, width=50, height=22,
                          fg_color=ACCENT if is_active else "transparent",
                          text_color="white" if is_active else MUTED,
                          corner_radius=5, font=(FONT, 9), border_width=0,
                          command=lambda v=val: self.ts_outside_canvas.set(v)
                          ).pack(side="left", padx=2, pady=2)
        
        ctk.CTkLabel(row1, text="Pos", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        for lbl, val in [("\u2198", "bottom-right"), ("\u2199", "bottom-left"), ("\u2197", "top-right"), ("\u2196", "top-left")]:
            is_active = self.ts_position.get() == val
            ctk.CTkButton(row1, text=lbl, width=36, height=22,
                          fg_color=ACCENT if is_active else CARD2,
                          text_color="white" if is_active else TEXT,
                          corner_radius=4, font=(FONT, 11), border_width=0,
                          command=lambda v=val: self.ts_position.set(v)
                          ).pack(side="left", padx=2)
        
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 4))
        
        ctk.CTkLabel(row2, text="Font", font=(FONT, 9), text_color=MUTED).pack(side="left")
        self.ts_font_slider = ctk.CTkSlider(row2, from_=10, to=60, variable=self.ts_font_size,
                                              width=70, height=14, fg_color=BORDER, progress_color=ACCENT)
        self.ts_font_slider.pack(side="left", padx=4)
        self.ts_font_lbl = ctk.CTkLabel(row2, text=f"{self.ts_font_size.get()}px", font=(FONT_MONO, 9), text_color=ACCENT)
        self.ts_font_lbl.pack(side="left")
        
        ctk.CTkLabel(row2, text="Color", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        self.ts_color_btn = ctk.CTkButton(row2, text="", width=24, height=24, corner_radius=4,
                                            fg_color=self.ts_color.get(), hover_color=self.ts_color.get(),
                                            command=self._pick_ts_color)
        self.ts_color_btn.pack(side="left", padx=4)
        
        ctk.CTkLabel(row2, text="BG", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(8, 0))
        self.ts_bg_btn = ctk.CTkButton(row2, text="", width=24, height=24, corner_radius=4,
                                         fg_color=self.ts_bg_color.get(), hover_color=self.ts_bg_color.get(),
                                         command=self._pick_ts_bg_color)
        self.ts_bg_btn.pack(side="left", padx=4)
        
        ctk.CTkLabel(row2, text="Bold", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(12, 0))
        self.ts_bold_toggle = ctk.CTkCheckBox(row2, text="", variable=self.ts_bold, width=20, height=22,
                                                fg_color=ACCENT, hover_color=ACCENT)
        self.ts_bold_toggle.pack(side="left")
        
        ctk.CTkLabel(row2, text="Shadow", font=(FONT, 9), text_color=MUTED).pack(side="left", padx=(8, 0))
        self.ts_shadow_toggle = ctk.CTkCheckBox(row2, text="", variable=self.ts_shadow, width=20, height=22,
                                                  fg_color=ACCENT, hover_color=ACCENT)
        self.ts_shadow_toggle.pack(side="left")
        
        self.ts_summary = ctk.CTkLabel(body, text="", font=(FONT_MONO, 9), text_color=MUTED, anchor="w")
        self.ts_summary.pack(fill="x", pady=(4, 0))
        
        self._set_ts_enabled(self.ts_enabled.get())
        self._update_ts_summary()
        
        for v in [self.ts_enabled, self.ts_position, self.ts_font_size, self.ts_color]:
            v.trace_add("write", lambda *_: self._update_ts_summary())

    def _set_ts_enabled(self, enabled: bool):
        self.ts_enabled.set(enabled)
        self.ts_on_btn.configure(fg_color=ACCENT if enabled else "transparent",
                                 text_color="white" if enabled else MUTED)
        self.ts_off_btn.configure(fg_color=ACCENT if not enabled else "transparent",
                                  text_color="white" if not enabled else MUTED)
        self._update_ts_summary()

    def _update_ts_summary(self):
        if not hasattr(self, "ts_summary"):
            return
        enabled = self.ts_enabled.get()
        if not enabled:
            self.ts_summary.configure(text="OFF", text_color=ACCENT2)
            return
        
        pos_map = {"bottom-right": "\u2198", "bottom-left": "\u2199",
                   "top-right": "\u2197", "top-left": "\u2196"}
        pos = pos_map.get(self.ts_position.get(), "\u2198")
        size = f"{self.ts_font_size.get()}px"
        col = self.ts_color.get().upper()
        self.ts_summary.configure(text=f"\u2713 {pos} · {size} · {col}", text_color=SUCCESS)

    def _on_wm_toggle(self):
        self._refresh_wm_controls()
        self._update_wm_summary()
        self._refresh_live_preview()

    def _on_wm_mode_change(self, mode: str):
        self.wm_mode.set(mode)
        invalidate_wm_cache()
        self._refresh_wm_controls()
        self._update_wm_summary()
        self._refresh_live_preview()

    def _on_wm_path_changed(self):
        invalidate_wm_cache()
        self._update_wm_summary()
        self._refresh_live_preview()

    def _pick_watermark(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title=t("select_area"), filetypes=[("Gambar", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("Semua", "*.*")])
        if path: self.watermark_path.set(path)

    def _pick_ts_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.ts_color.get())[1]
        if color:
            self.ts_color.set(color)
            self.ts_color_btn.configure(fg_color=color, hover_color=color)

    def _pick_ts_bg_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.ts_bg_color.get())[1]
        if color:
            self.ts_bg_color.set(color)
            self.ts_bg_btn.configure(fg_color=color, hover_color=color)
