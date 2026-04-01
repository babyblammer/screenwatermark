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
from customtkinter import CTkImage
import tkinter as tk
import mss
import pystray
from PIL import Image, ImageDraw, ImageTk

from core.constants import (BG, PANEL, CARD, CARD2, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, 
                          BORDER, WARN, PREVIEW_W, PREVIEW_H, HISTORY_MAX, FONT, FONT_MONO,
                          DISABLED_BG, DISABLED_TEXT, DROPDOWN_W, DROPDOWN_H)
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
    VERSION = "4.1.0a"

    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("ScreenWatermark Pro")
        self.geometry("620x580")
        self.minsize(620, 580)
        self.maxsize(620, 580)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        
        # High DPI support - enable DPI awareness for Windows
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        
        # Disable CTk automatic scaling to prevent bluriness
        ctk.set_widget_scaling(1.0)
        
        # Apply CTk styling
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG)
        
        # Load settings
        cfg = load_settings()

        # ── Tkinter vars ─────────────────────────────────────────────────────────
        self.watermark_path    = tk.StringVar(value=cfg["watermark_path"])
        self.wm_enabled        = tk.BooleanVar(value=bool(cfg.get("wm_enabled", True)))
        self.wm_position       = tk.StringVar(value=cfg["wm_position"])
        self.wm_opacity        = tk.IntVar(value=int(cfg["wm_opacity"]))
        self.wm_scale          = tk.IntVar(value=int(cfg["wm_scale"]))
        self.wm_pattern_gap    = tk.IntVar(value=int(cfg.get("wm_pattern_gap", 20)))
        self.wm_mode           = tk.StringVar(value=cfg.get("wm_mode", "Normal"))
        self.ts_enabled        = tk.BooleanVar(value=bool(cfg["ts_enabled"]))
        self.ts_enable         = tk.StringVar(value=cfg.get("ts_enable", "Outside"))
        self.ts_format         = tk.StringVar(value=cfg["ts_format"])
        self.ts_format_display = tk.StringVar(value="DD/MM/YYYY HH:MM:SS")
        self.ts_font_size      = tk.IntVar(value=int(cfg["ts_font_size"]))
        self.ts_color          = tk.StringVar(value=cfg["ts_color"])
        self.ts_bg_color       = tk.StringVar(value=cfg["ts_bg_color"])
        self.ts_bg_opacity     = tk.IntVar(value=int(cfg["ts_bg_opacity"]))
        self.ts_shadow         = tk.BooleanVar(value=bool(cfg["ts_shadow"]))
        self.ts_bold           = tk.BooleanVar(value=bool(cfg.get("ts_bold", False)))
        self.ts_outside_canvas = tk.BooleanVar(value=bool(cfg.get("ts_outside_canvas", False)))
        self.delay_sec         = tk.IntVar(value=int(cfg["delay_sec"]))
        self.hotkey_fullscreen = tk.StringVar(value=cfg.get("hotkey_fullscreen","<print_screen>"))
        self.hotkey_region     = tk.StringVar(value=cfg.get("hotkey_region", "<ctrl>+<shift>+<f9>"))
        _hk_history_raw = cfg.get("hotkey_history", "<ctrl>+<f9>")
        _CONFLICT_HOTKEYS = {"<shift>+<print_screen>", "<ctrl>+<shift>+h>", "<ctrl>+<shift>+h", "<shift>+<f9>", "<ctrl>+<print_screen>"}
        if _hk_history_raw in _CONFLICT_HOTKEYS:
            _hk_history_raw = "<ctrl>+<f9>"
        self.hotkey_history    = tk.StringVar(value=_hk_history_raw)
        self.capture_mode      = tk.StringVar(value=cfg.get("capture_mode", "fullscreen"))
        self.run_at_startup    = tk.BooleanVar(value=bool(cfg.get("run_at_startup", False)))
        self.start_minimized   = tk.BooleanVar(value=bool(cfg.get("start_minimized", False)))
        self.ui_language       = tk.StringVar(value=cfg.get("language", "en"))

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
        self._panel_mode: str = "preview"
        self._wm_acc_open: bool = True
        self._ts_acc_open: bool = False

        # Build UI
        self._build_ui()
        self._refresh_snapshot()
        self.after(0, self._deferred_startup)
        self._start_tray()

        # Trace all variables
        all_vars = [
            self.watermark_path, self.wm_enabled, self.wm_position, self.wm_opacity,
            self.wm_scale, self.wm_pattern_gap, self.wm_mode, self.ts_enabled, self.ts_format,
            self.ts_format_display, self.ts_font_size, self.ts_color, self.ts_bg_color, self.ts_bg_opacity,
            self.ts_shadow, self.ts_bold, self.ts_outside_canvas, self.delay_sec, self.hotkey_fullscreen,
            self.hotkey_region, self.hotkey_history, self.capture_mode,
            self.run_at_startup, self.start_minimized,
        ]
        for v in all_vars:
            v.trace_add("write", lambda *_: self._on_setting_changed())

        self.wm_enabled.trace_add("write", lambda *_: self._update_wm_indicator())
        self.watermark_path.trace_add("write", lambda *_: self._update_wm_indicator())
        self.wm_mode.trace_add("write", lambda *_: self._update_wm_indicator())
        self.wm_mode.trace_add("write", lambda *_: self._update_wm_summary())
        self.wm_position.trace_add("write", lambda *_: self._update_wm_summary())

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
            font=(FONT, 13, "bold"), text_color=TEXT, fg_color="transparent")
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
            header, text="🕒", font=(FONT, 13),
            fg_color="transparent", hover_color=CARD2, text_color=MUTED,
            corner_radius=6, border_width=1, border_color=BORDER,
            width=36, height=28,
            command=self._show_history_popup)
        self.btn_history.pack(side="right", padx=(0, 8), pady=8)
    # ── Mode & Helpers ───────────────────────────────────────────────────────

    def _build_main_content(self):
        self.middle_frame = ctk.CTkScrollableFrame(
            self, height=484, fg_color=BG, corner_radius=0,
            scrollbar_button_color=ACCENT, scrollbar_button_hover_color="#7d75ff"
        )
        self.middle_frame.pack(fill="x", pady=(8, 0))
        
        self._build_panel_toggle()
        self._build_preview_and_history()
        self._build_watermark_controls()
        self._build_timestamp_controls()

        self.preview_wrap.pack(fill="x", padx=12, pady=(0, 8))
        self.wm_frame.pack(fill="x", padx=12, pady=(8, 0))
        self.ts_frame.pack(fill="x", padx=12, pady=(8, 0))

    def _build_panel_toggle(self):
        container = ctk.CTkFrame(self.middle_frame, fg_color=CARD,
                                 corner_radius=9, border_width=1, border_color=BORDER)
        container.pack(fill="x", padx=12, pady=(0, 8))
        
        self.btn_panel_preview = ctk.CTkButton(
            container, text=f"🖼  {t('preview')}",
            fg_color=ACCENT, hover_color="#5a52e0", text_color="white",
            corner_radius=6, height=28, width=100,
            command=lambda: self._switch_panel("preview"))
        self.btn_panel_preview.pack(side="left", padx=3, pady=3)
        
        hist_container = ctk.CTkFrame(container, fg_color="transparent")
        hist_container.pack(side="left", padx=(0, 3))
        
        self.btn_panel_history = ctk.CTkButton(
            hist_container, text=f"🕒  {t('history')}",
            fg_color=CARD, hover_color=BORDER, text_color=MUTED,
            corner_radius=6, height=28, width=100,
            border_width=1, border_color=BORDER,
            command=lambda: self._switch_panel("history"))
        self.btn_panel_history.pack(side="left")
        
        self.hist_badge = ctk.CTkLabel(
            hist_container, text="", fg_color=ACCENT2, text_color="white",
            corner_radius=10, font=(FONT_MONO, 10), width=0, height=16, padx=5)
        self.hist_badge.pack(side="left", padx=(4, 0))
        self._update_history_badge()

    def _switch_panel(self, which: str):
        self._panel_mode = which
        if which == "preview":
            self.history_panel_wrap.pack_forget()
            self.preview_wrap.pack(fill="x", padx=12, pady=(0, 8), before=self.wm_frame)
            self.btn_panel_preview.configure(fg_color=ACCENT, text_color="white")
            self.btn_panel_history.configure(fg_color="transparent", text_color=MUTED)
        else:
            self.preview_wrap.pack_forget()
            self.history_panel_wrap.pack(fill="x", padx=12, pady=(0, 8), before=self.wm_frame)
            self.btn_panel_history.configure(fg_color=ACCENT, text_color="white")
            self.btn_panel_preview.configure(fg_color="transparent", text_color=MUTED)
            self._render_history_panel()

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
        
        self.preview_canvas = tk.Canvas(self.preview_wrap, width=PREVIEW_W, height=PREVIEW_H,
                                        bg="#0c0c18", highlightthickness=0)
        self.preview_canvas.pack()
        
        self.history_panel_wrap = ctk.CTkFrame(
            self.middle_frame, height=180, fg_color=CARD, corner_radius=10,
            border_width=1, border_color=BORDER)
        self.history_panel_wrap.pack_propagate(False)
        
        hist_topbar = ctk.CTkFrame(self.history_panel_wrap, fg_color="transparent")
        hist_topbar.pack(fill="x", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(hist_topbar, text=t("history_tab_hint"),
                     font=(FONT_MONO, 10), text_color=MUTED, fg_color="transparent").pack(side="left")
        
        ctk.CTkButton(hist_topbar, text=t("clear_history"), font=(FONT, 13),
                      fg_color=CARD, hover_color=BORDER, text_color=MUTED,
                      corner_radius=6, border_width=1, border_color=BORDER,
                      width=90, height=28,
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
                        font=(FONT, 13), text_color=MUTED).pack(pady=40)
            return
        
        for idx, entry in enumerate(reversed(entries)):
            item = ctk.CTkFrame(self.history_scroll, fg_color=CARD2, corner_radius=6, cursor="hand2")
            item.pack(side="left", padx=4)
            item.bind("<Button-1>", lambda e, ent=entry: self._load_from_history(ent))
            
            img_label = ctk.CTkLabel(item, text="", width=108, height=60, cursor="hand2")
            img_label.bind("<Button-1>", lambda e, ent=entry, itm=item: self._load_from_history(ent, itm))
            img_label.pack()
            
            try:
                thumb_img = Image.open(io.BytesIO(entry["thumb_bytes"]))
                thumb_img = thumb_img.resize((108, 60), Image.LANCZOS)
                ctk_img = CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(108, 60))
                img_label.configure(image=ctk_img, text="")
                img_label._image = ctk_img
            except Exception:
                pass
            
            meta = ctk.CTkLabel(item, text=entry["timestamp"].strftime("%H:%M  %d/%m"),
                               font=(FONT_MONO, 10), text_color=MUTED)
            meta.pack(pady=2)

    def _build_bottom_bar(self):
        """P5: Build bottom bar with SplitShotButton."""
        from ui.widgets.shot_buttons import SplitShotButton
        
        bottom_bar = ctk.CTkFrame(self, fg_color=PANEL, height=52, corner_radius=0)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)
        
        # All buttons use same dimensions: width=90, height=32, corner_radius=6
        btn_width = 90
        btn_height = 32
        btn_padx = 4
        btn_pady = 10
        
        # Split shot button (Fullscreen + Region) - both 90x32
        self.shot_btn = SplitShotButton(
            bottom_bar,
            on_fullscreen=self._trigger_fullscreen,
            on_region=self._trigger_region)
        self.shot_btn.pack(side="right", padx=btn_padx, pady=btn_pady)
        
        # Settings button
        self.btn_settings = ctk.CTkButton(
            bottom_bar, text=f"⚙ {t('settings')}", font=(FONT, 13),
            fg_color=CARD, hover_color=BORDER, text_color=MUTED,
            corner_radius=6, border_width=1, border_color=BORDER,
            width=btn_width, height=btn_height,
            command=self._open_settings)
        self.btn_settings.pack(side="right", padx=btn_padx, pady=btn_pady)
        
        # Set initial mode
        self.after(10, self._on_mode_change)
    def _update_wm_indicator(self):
        """Update WM indicator in header based on mode."""
        mode = self.wm_mode.get()
        has_file = bool(self.watermark_path.get())
        if mode == "Off":
            self.wm_indicator.configure(text=t("wm_off"), text_color=MUTED)
        elif not has_file:
            self.wm_indicator.configure(text=t("wm_warn"), text_color=WARN)
        else:
            self.wm_indicator.configure(text=t("wm_active"), text_color=SUCCESS)

    def _go_history_tab(self):
        """Switch to history tab."""
        self._switch_panel("history")



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
        wm_mode_val = self.wm_mode.get().lower()
        if wm_mode_val == "full screen":
            wm_mode_val = "full"
        
        wm_pos_val = self.wm_position.get().lower()
        
        self._settings_snapshot = {
            "watermark_path":    self.watermark_path.get(),
            "wm_enabled":        self.wm_enabled.get(),
            "wm_position":       wm_pos_val,
            "wm_opacity":        self.wm_opacity.get(),
            "wm_scale":          self.wm_scale.get(),
            "wm_pattern_gap":     self.wm_pattern_gap.get(),
            "wm_mode":           wm_mode_val,
            "ts_enabled":        self.ts_enabled.get(),
            "ts_format":         self.ts_format.get(),
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
            pass

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
                d.text((pw//2 - 36, ph//2 - 6), t("area_screenshot"), font=fnt, fill=(60,60,92))
            except: pass

            wm_path = cfg.get("watermark_path","")
            wm_on = cfg.get("wm_enabled", True)
            if wm_on and not wm_path:
                try:
                    fnt2 = load_font(7)
                    d.text((4, 4), t("wm_file_not_set"), font=fnt2, fill=(120,80,40))
                except: pass
            elif not wm_on:
                try:
                    fnt2 = load_font(7)
                    d.text((4, 4), t("wm_disabled"), font=fnt2, fill=(100,100,100))
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
        state = self.wm_state() if hasattr(self, 'wm_state') else "normal"
        if state == "normal":
            self.lift()
            self.focus_force()
            self._switch_panel("history")
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

        self.shot_btn.set_enabled(False)

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
            self.shot_btn.set_enabled(True)

            

    def _on_region_selected(self, x1, y1, x2, y2):
        self._region = (x1, y1, x2, y2)
        self._refresh_snapshot()
        self.capture_mode.set("fullscreen")
        self._on_mode_change()
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
        self.capture_mode.set("fullscreen")
        self._on_mode_change()
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
        self.shot_btn.set_enabled(True)

        

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
            self._countdown_job = self.after(1000, self._countdown, n - 1)
        else:
            if self._countdown_overlay:
                self._countdown_overlay.close()
                self._countdown_overlay = None
            self._countdown_job = None

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
        self.shot_btn.set_enabled(True)
        if self.delay_sec.get() > 0:
            self.delay_sec.set(0)
            self._refresh_snapshot()
            if self._settings_win and self._settings_win.winfo_exists():
                try:
                    self._settings_win.delay_val_lbl.configure(text="0 s")
                except: pass

        

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
        finally:
            self._screenshot_lock.release()
            if self.delay_sec.get() > 0:
                self.delay_sec.set(0)
                self._refresh_snapshot()
                if self._settings_win and self._settings_win.winfo_exists():
                    try:
                        self._settings_win.delay_val_lbl.configure(text="0 s")
                    except: pass
            if not self._is_quitting:
                if region is None:
                    _prev = getattr(self, "_main_prev_state", "iconic")
                    if _prev in ("normal", "zoomed"):
                        self.after(0, self.deiconify)
                self.after(0, lambda: self.shot_btn.set_enabled(True))

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

    def _clear_all_history(self):
        if not self._history: return
        from tkinter import messagebox
        if messagebox.askyesno(t("confirm"), t("clear_history_confirm")):
            with self._history_lock:
                self._history.clear()
            _enqueue_save_history(self._history)
            self._render_history()

            

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
            ctk.CTkLabel(self.history_scroll, text=t("history_empty"), font=(FONT, 13), text_color=MUTED).pack(pady=40)
            return

        for idx, entry in enumerate(reversed(entries)):
            item = ctk.CTkFrame(self.history_scroll, fg_color=CARD, corner_radius=6, cursor="hand2")
            item.pack(fill="x", pady=(0, 6), padx=2)
            item.bind("<Button-1>", lambda e, ent=entry: self._load_from_history(ent))
            
            try:
                thumb_img = Image.open(io.BytesIO(entry["thumb_bytes"]))
                ctk_img = CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(180, 101))
            except:
                ctk_img = None
            if ctk_img:
                self._history_tks.append(ctk_img)
                thumb_label = ctk.CTkLabel(item, image=ctk_img, text="", cursor="hand2")
                thumb_label.bind("<Button-1>", lambda e, ent=entry, itm=item: self._load_from_history(ent, itm))
                thumb_label.pack(side="left", padx=(8, 10))

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="y", anchor="n", pady=6)
            
            ctk.CTkLabel(info, text=f"#{len(entries)-idx}", font=(FONT, 13, "bold"), text_color=ACCENT).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{entry['width']} x {entry['height']} px", font=(FONT, 13), text_color=MUTED).pack(anchor="w")
            ctk.CTkLabel(info, text=entry["timestamp"].strftime("%H:%M:%S  %d/%m/%Y"), font=(FONT, 13), text_color=TEXT).pack(anchor="w")

            btn_row = ctk.CTkFrame(info, fg_color="transparent")
            btn_row.pack(anchor="w", pady=(6, 0))
            
            ctk.CTkButton(btn_row, text=t("copy_button"), font=(FONT, 13), fg_color=ACCENT, hover_color="#5a52e0",
                          text_color="white", corner_radius=6, width=60, height=28,
                          command=lambda e=entry: self._load_from_history(e)).pack(side="left")
            ctk.CTkButton(btn_row, text=t("delete_button"), font=(FONT, 13), fg_color=CARD, hover_color=BORDER,
                          text_color=MUTED, corner_radius=6, width=28, height=28, border_width=1, border_color=BORDER,
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

    def _load_from_history(self, entry: dict, item=None):
        try:
            img = Image.open(io.BytesIO(entry["full_bytes"]))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"{t('error_reading_history')}\n{e}"); return
        self.last_image = img
        try:
            copy_image_to_clipboard(img)
            if item:
                self._show_copy_feedback(item)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Clipboard Error", str(e))

    def _show_copy_feedback(self, item):
        """Briefly highlight item frame on click (like hover effect)"""
        try:
            original = item.cget("fg_color")
            item.configure(fg_color=BORDER)
            self.after(300, lambda: item.configure(fg_color=original) if item.winfo_exists() else None)
        except:
            pass

    def _on_mode_change(self):
        if self._settings_win and self._settings_win.winfo_exists():
            try: self._settings_win.region_label.configure(text=self._region_text())
            except: pass
        try:
            mode = self._settings_snapshot.get("capture_mode", "fullscreen")
            self.shot_btn.set_mode(mode)
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
        self.wm_frame = ctk.CTkFrame(self.middle_frame, fg_color=CARD, corner_radius=10,
                                      border_width=1, border_color=BORDER)
        
        title_row = ctk.CTkFrame(self.wm_frame, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(title_row, text=f"💧 {t('card_watermark')}", font=(FONT, 14, "bold"), text_color=TEXT).pack(side="left")
        
        self.wm_summary = ctk.CTkLabel(title_row, text="", font=(FONT, 11), text_color=MUTED, anchor="e")
        self.wm_summary.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        content = ctk.CTkFrame(self.wm_frame, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=(0, 8))
        
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))
        row1.grid_columnconfigure(0, weight=0, minsize=70)
        row1.grid_columnconfigure(1, weight=0)
        row1.grid_columnconfigure(2, weight=0, minsize=70)
        row1.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(row1, text=t("label_mode"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.wm_mode_menu = ctk.CTkOptionMenu(row1, 
                                               values=[t("wm_off_mode"), t("wm_normal_mode"), t("wm_full_mode"), t("wm_pattern_mode")],
                                               variable=self.wm_mode, font=(FONT, 13),
                                               fg_color=BORDER, button_color=BORDER, button_hover_color=ACCENT,
                                               dropdown_fg_color=PANEL, text_color=TEXT,
                                               width=DROPDOWN_W, height=DROPDOWN_H,
                                               command=self._on_wm_mode_change)
        self.wm_mode_menu.grid(row=0, column=1, sticky="w", padx=(0, 24))
        
        ctk.CTkLabel(row1, text=t("label_opacity"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=2, sticky="w", padx=(0, 8))
        opacity_slider_frame = ctk.CTkFrame(row1, fg_color="transparent")
        opacity_slider_frame.grid(row=0, column=3, sticky="w")
        self.wm_opacity_slider = ctk.CTkSlider(opacity_slider_frame, from_=10, to=100, variable=self.wm_opacity,
                                                  width=100, height=14, fg_color=BORDER, progress_color=ACCENT,
                                                  command=lambda v: (self.wm_opacity_lbl.configure(text=f"{int(float(v))}%"), self._update_wm_summary()))
        self.wm_opacity_slider.pack(side="left", padx=(0, 4))
        self.wm_opacity_lbl = ctk.CTkLabel(opacity_slider_frame, text=f"{self.wm_opacity.get()}%", font=(FONT_MONO, 11), text_color=TEXT)
        self.wm_opacity_lbl.pack(side="left")
        
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        row2.grid_columnconfigure(0, weight=0, minsize=70)
        row2.grid_columnconfigure(1, weight=0)
        row2.grid_columnconfigure(2, weight=0, minsize=70)
        row2.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(row2, text=t("label_position"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.wm_position_menu = ctk.CTkOptionMenu(row2, 
                                                  values=[t("pos_bottom_left"), t("pos_bottom_right"), t("pos_top_left"), t("pos_top_right"), t("pos_center")],
                                                  variable=self.wm_position, font=(FONT, 13),
                                                  fg_color=BORDER, button_color=BORDER, button_hover_color=ACCENT,
                                                  dropdown_fg_color=PANEL, text_color=TEXT,
                                                  width=DROPDOWN_W, height=DROPDOWN_H,
                                                  command=lambda v: self._update_wm_summary())
        self.wm_position_menu.grid(row=0, column=1, sticky="w", padx=(0, 24))
        
        ctk.CTkLabel(row2, text=t("label_scale"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=2, sticky="w", padx=(0, 8))
        scale_slider_frame = ctk.CTkFrame(row2, fg_color="transparent")
        scale_slider_frame.grid(row=0, column=3, sticky="w")
        self.wm_scale_slider = ctk.CTkSlider(scale_slider_frame, from_=5, to=60, variable=self.wm_scale,
                                              width=100, height=14, fg_color=BORDER, progress_color=ACCENT,
                                              command=lambda v: (self.wm_scale_lbl.configure(text=f"{int(float(v))}%"), self._update_wm_summary()))
        self.wm_scale_slider.pack(side="left", padx=(0, 4))
        self.wm_scale_lbl = ctk.CTkLabel(scale_slider_frame, text=f"{self.wm_scale.get()}%", font=(FONT_MONO, 11), text_color=TEXT)
        self.wm_scale_lbl.pack(side="left")
        
        row3 = ctk.CTkFrame(content, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 6))
        row3.grid_columnconfigure(0, weight=0, minsize=70)
        row3.grid_columnconfigure(1, weight=0)
        row3.grid_columnconfigure(2, weight=0, minsize=70)
        row3.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(row3, text=t("label_path"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        path_frame = ctk.CTkFrame(row3, fg_color=BORDER, corner_radius=4, border_width=0)
        path_frame.pack_propagate(False)
        path_frame.configure(width=DROPDOWN_W, height=DROPDOWN_H)
        path_frame.grid(row=0, column=1, sticky="w", padx=(0, 24))
        self.wm_path_lbl = ctk.CTkLabel(path_frame, text="", font=(FONT, 13), text_color=TEXT,
                                         cursor="hand2", anchor="w", padx=8)
        self.wm_path_lbl.pack(fill="both", expand=True)
        self.wm_path_lbl.bind("<Button-1>", lambda e: self._pick_watermark())
        
        ctk.CTkLabel(row3, text=t("label_pattern_gap"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=2, sticky="w", padx=(0, 8))
        gap_slider_frame = ctk.CTkFrame(row3, fg_color="transparent")
        gap_slider_frame.grid(row=0, column=3, sticky="w")
        self.wm_gap_slider = ctk.CTkSlider(gap_slider_frame, from_=5, to=100, variable=self.wm_pattern_gap,
                                              width=100, height=14, fg_color=BORDER, progress_color=ACCENT,
                                              command=lambda v: (self.wm_gap_lbl.configure(text=f"{int(float(v))}px"), self._update_wm_summary()))
        self.wm_gap_slider.pack(side="left", padx=(0, 4))
        self.wm_gap_lbl = ctk.CTkLabel(gap_slider_frame, text=f"{self.wm_pattern_gap.get()}px", font=(FONT_MONO, 11), text_color=TEXT)
        self.wm_gap_lbl.pack(side="left")
        
        self.watermark_path.trace_add("write", lambda *_: self._update_wm_path_label())
        
        self._update_wm_path_label()
        self._sync_wm_mode_var()
        self._sync_wm_position_var()
        self._refresh_wm_controls()
        self._update_wm_indicator()
        self._update_wm_summary()
    
    def _sync_wm_mode_var(self):
        mode_map = {
            "off": t("wm_off_mode"), "normal": t("wm_normal_mode"),
            "full": t("wm_full_mode"), "pattern": t("wm_pattern_mode"),
            t("wm_off_mode"): t("wm_off_mode"), t("wm_normal_mode"): t("wm_normal_mode"),
            t("wm_full_mode"): t("wm_full_mode"), t("wm_pattern_mode"): t("wm_pattern_mode"),
            "Off": t("wm_off_mode"), "Normal": t("wm_normal_mode"),
            "Full Screen": t("wm_full_mode"), "Pattern": t("wm_pattern_mode"),
        }
        self.wm_mode.set(mode_map.get(self.wm_mode.get(), t("wm_normal_mode")))
        self.wm_enabled.set(self.wm_mode.get() != t("wm_off_mode"))
    
    def _sync_wm_position_var(self):
        pos_map = {
            "bottom-left": t("pos_bottom_left"), "bottom-right": t("pos_bottom_right"),
            "top-left": t("pos_top_left"), "top-right": t("pos_top_right"), "center": t("pos_center"),
            t("pos_bottom_left"): t("pos_bottom_left"), t("pos_bottom_right"): t("pos_bottom_right"),
            t("pos_top_left"): t("pos_top_left"), t("pos_top_right"): t("pos_top_right"), t("pos_center"): t("pos_center"),
            "Bottom-Left": t("pos_bottom_left"), "Bottom-Right": t("pos_bottom_right"),
            "Top-Left": t("pos_top_left"), "Top-Right": t("pos_top_right"), "Center": t("pos_center"),
        }
        self.wm_position.set(pos_map.get(self.wm_position.get(), t("pos_bottom_left")))
    


    def _refresh_wm_controls(self):
        mode = self.wm_mode.get()
        wm_off_mode = t("wm_off_mode")
        wm_normal_mode = t("wm_normal_mode")
        wm_full_mode = t("wm_full_mode")
        wm_pattern_mode = t("wm_pattern_mode")
        is_off = (mode == wm_off_mode or mode == "Off")
        is_normal = (mode == wm_normal_mode or mode == "Normal")
        is_pattern = (mode == wm_pattern_mode or mode == "Pattern")
        is_fullscreen = (mode == wm_full_mode or mode == "Full Screen")
        
        if is_off:
            ctrl_state = "disabled"
            label_color = DISABLED_TEXT
            slider_fg = DISABLED_BG
            path_color = DISABLED_TEXT
            path_cursor = ""
        else:
            ctrl_state = "normal"
            label_color = TEXT
            slider_fg = BORDER
            path_color = TEXT
            path_cursor = "hand2"
        
        self.wm_opacity_slider.configure(state=ctrl_state, fg_color=slider_fg)
        self.wm_opacity_lbl.configure(text_color=label_color)
        self.wm_path_lbl.configure(text_color=path_color, cursor=path_cursor)
        
        if is_normal or is_pattern:
            scale_state = "normal"
            scale_fg = BORDER
            scale_color = TEXT
        else:
            scale_state = "disabled"
            scale_fg = DISABLED_BG
            scale_color = DISABLED_TEXT
        
        self.wm_scale_slider.configure(state=scale_state, fg_color=scale_fg)
        self.wm_scale_lbl.configure(text_color=scale_color)
        
        if is_normal:
            self.wm_position_menu.configure(state="normal",
                                           fg_color=BORDER, button_color=BORDER, text_color=TEXT)
        else:
            self.wm_position_menu.configure(state="disabled",
                                           fg_color=DISABLED_BG, button_color=DISABLED_BG, text_color=DISABLED_TEXT)
        
        if is_pattern:
            gap_state = "normal"
            gap_fg = BORDER
            gap_color = TEXT
        else:
            gap_state = "disabled"
            gap_fg = DISABLED_BG
            gap_color = DISABLED_TEXT
        
        self.wm_gap_slider.configure(state=gap_state, fg_color=gap_fg)
        self.wm_gap_lbl.configure(text_color=gap_color)

    def _update_wm_summary(self):
        if not hasattr(self, "wm_summary"):
            return
        
        mode = self.wm_mode.get()
        wm_off_mode = t("wm_off_mode")
        wm_normal_mode = t("wm_normal_mode")
        wm_full_mode = t("wm_full_mode")
        wm_pattern_mode = t("wm_pattern_mode")
        
        mode_display = {
            wm_off_mode: wm_off_mode, wm_normal_mode: wm_normal_mode,
            wm_full_mode: wm_full_mode, wm_pattern_mode: wm_pattern_mode,
            "Off": wm_off_mode, "Normal": wm_normal_mode,
            "Full Screen": wm_full_mode, "Pattern": wm_pattern_mode,
        }.get(mode, mode)
        op = f"{self.wm_opacity.get()}%"
        
        if mode == wm_off_mode or mode == "Off":
            text = wm_off_mode
            self.wm_summary.configure(text=text, text_color=ACCENT2)
        elif mode == wm_normal_mode or mode == "Normal":
            pos_display = self.wm_position.get()
            sc = f"{self.wm_scale.get()}%"
            text = f"{mode_display} · {pos_display} · {op} · {sc}"
            self.wm_summary.configure(text=text, text_color=TEXT)
        elif mode == wm_pattern_mode or mode == "Pattern":
            sc = f"{self.wm_scale.get()}%"
            gap = f"{self.wm_pattern_gap.get()}px"
            text = f"{mode_display} · {op} · {sc} · {gap}"
            self.wm_summary.configure(text=text, text_color=TEXT)
        else:
            text = f"{mode_display} · {op}"
            self.wm_summary.configure(text=text, text_color=TEXT)

    def _update_wm_path_label(self):
        if not hasattr(self, "wm_path_lbl"):
            return
        
        path = self.watermark_path.get()
        mode = self.wm_mode.get()
        is_normal = (mode == "Normal")
        
        if not path:
            text = t("select_file")
        else:
            text = path
        
        if is_normal:
            color = TEXT
            cursor = "hand2"
        else:
            color = DISABLED_TEXT
            cursor = ""
        
        self.wm_path_lbl.configure(text=text, text_color=color, cursor=cursor)

    def _build_timestamp_controls(self):
        self.ts_frame = ctk.CTkFrame(self.middle_frame, fg_color=CARD, corner_radius=10,
                                      border_width=1, border_color=BORDER)
        
        title_row = ctk.CTkFrame(self.ts_frame, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(title_row, text=f"🕐 {t('card_timestamp')}", font=(FONT, 14, "bold"), text_color=TEXT).pack(side="left")
        
        self.ts_summary = ctk.CTkLabel(title_row, text="", font=(FONT, 11), text_color=MUTED, anchor="e")
        self.ts_summary.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        content = ctk.CTkFrame(self.ts_frame, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=(0, 8))
        
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))
        row1.grid_columnconfigure(0, weight=0, minsize=70)
        row1.grid_columnconfigure(1, weight=0)
        row1.grid_columnconfigure(2, weight=0, minsize=70)
        row1.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(row1, text=t("label_enable"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.ts_enable_menu = ctk.CTkOptionMenu(row1, 
                                                values=[t("ts_off_mode"), t("ts_outside_mode")],
                                                variable=self.ts_enable, font=(FONT, 13),
                                                fg_color=BORDER, button_color=BORDER, button_hover_color=ACCENT,
                                                dropdown_fg_color=PANEL, text_color=TEXT,
                                                width=DROPDOWN_W, height=DROPDOWN_H,
                                                command=self._on_ts_enable_change)
        self.ts_enable_menu.grid(row=0, column=1, sticky="w", padx=(0, 24))
        
        ctk.CTkLabel(row1, text=t("label_format"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.ts_format_menu = ctk.CTkOptionMenu(row1, values=["DD/MM/YYYY HH:MM:SS", "ISO"],
                                                variable=self.ts_format_display, font=(FONT, 13),
                                                fg_color=BORDER, button_color=BORDER, button_hover_color=ACCENT,
                                                dropdown_fg_color=PANEL, text_color=TEXT,
                                                width=DROPDOWN_W, height=DROPDOWN_H,
                                                command=self._on_ts_format_change)
        self.ts_format_menu.grid(row=0, column=3, sticky="w", padx=(0, 0))
        
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 0))
        row2.grid_columnconfigure(0, weight=0, minsize=70)
        row2.grid_columnconfigure(1, weight=0)
        row2.grid_columnconfigure(2, weight=0, minsize=70)
        row2.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(row2, text=t("label_text_color"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.ts_color_btn = ctk.CTkButton(row2, text="", width=24, height=24, corner_radius=4,
                                            fg_color=self.ts_color.get(), hover_color=self.ts_color.get(),
                                            command=self._pick_ts_color)
        self.ts_color_btn.grid(row=0, column=1, sticky="w", padx=(0, 24))
        
        ctk.CTkLabel(row2, text=t("label_font_size"), font=(FONT, 13), text_color=MUTED).grid(row=0, column=2, sticky="w", padx=(0, 8))
        font_slider_frame = ctk.CTkFrame(row2, fg_color="transparent")
        font_slider_frame.grid(row=0, column=3, sticky="w")
        self.ts_font_slider = ctk.CTkSlider(font_slider_frame, from_=10, to=60, variable=self.ts_font_size,
                                              width=100, height=14, fg_color=BORDER, progress_color=ACCENT,
                                              command=lambda v: (self.ts_font_lbl.configure(text=f"{int(float(v))}px"), self._update_ts_summary()))
        self.ts_font_slider.pack(side="left", padx=(0, 4))
        self.ts_font_lbl = ctk.CTkLabel(font_slider_frame, text=f"{self.ts_font_size.get()}px", font=(FONT_MONO, 11), text_color=TEXT)
        self.ts_font_lbl.pack(side="left")
        
        self._sync_ts_enable_var()
        self._refresh_ts_controls()
        self._update_ts_summary()
        
        for v in [self.ts_enable, self.ts_format, self.ts_font_size, self.ts_color]:
            v.trace_add("write", lambda *_: self._update_ts_summary())
        
        self.ts_color.trace_add("write", lambda *_: self._update_ts_color_btn())
        
        self._sync_ts_format_display()

    def _sync_ts_enable_var(self):
        if not self.ts_enabled.get():
            self.ts_enable.set("Off")
        else:
            self.ts_enable.set("Outside")

    def _sync_ts_format_display(self):
        format_to_display = {
            "%d/%m/%Y  %H:%M:%S": "DD/MM/YYYY HH:MM:SS",
            "%Y-%m-%d %H:%M": "ISO"
        }
        display = format_to_display.get(self.ts_format.get(), "DD/MM/YYYY HH:MM:SS")
        self.ts_format_display.set(display)

    def _on_ts_format_change(self, display_value):
        self.ts_format_display.set(display_value)
        display_to_format = {
            "DD/MM/YYYY HH:MM:SS": "%d/%m/%Y  %H:%M:%S",
            "ISO": "%Y-%m-%d %H:%M"
        }
        self.ts_format.set(display_to_format.get(display_value, "%d/%m/%Y  %H:%M:%S"))

    def _on_ts_enable_change(self, value):
        self.ts_enable.set(value)
        ts_off_mode = t("ts_off_mode")
        
        if value == ts_off_mode or value == "Off":
            self.ts_enabled.set(False)
            self.ts_outside_canvas.set(False)
        else:
            self.ts_enabled.set(True)
            self.ts_outside_canvas.set(True)
        
        self._on_setting_changed()
        self._refresh_ts_controls()
        self._update_ts_summary()

    def _refresh_ts_controls(self):
        mode = self.ts_enable.get()
        ts_off_mode = t("ts_off_mode")
        is_disabled = (mode == ts_off_mode or mode == "Off")
        
        if is_disabled:
            ctrl_state = "disabled"
            label_color = DISABLED_TEXT
            slider_fg = DISABLED_BG
        else:
            ctrl_state = "normal"
            label_color = TEXT
            slider_fg = BORDER
        
        self.ts_font_slider.configure(state=ctrl_state, fg_color=slider_fg)
        self.ts_font_lbl.configure(text_color=label_color)
        self.ts_color_btn.configure(state=ctrl_state)

    def _update_ts_summary(self):
        if not hasattr(self, "ts_summary"):
            return
        
        mode = self.ts_enable.get()
        ts_off_mode = t("ts_off_mode")
        
        if mode == ts_off_mode or mode == "Off":
            self.ts_summary.configure(text=ts_off_mode, text_color=ACCENT2)
        else:
            size = f"{self.ts_font_size.get()}px"
            col = self.ts_color.get().upper()
            self.ts_summary.configure(text=f"{mode} · {size} · {col}", text_color=TEXT)

    def _on_wm_toggle(self):
        self._refresh_wm_controls()
        self._update_wm_summary()
        self._refresh_live_preview()

    def _on_wm_mode_change(self, mode: str):
        self.wm_mode.set(mode)
        self.wm_enabled.set(mode != t("wm_off_mode") and mode != "Off")
        invalidate_wm_cache()
        self._refresh_wm_controls()
        self._update_wm_indicator()
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

    def _update_ts_color_btn(self):
        if hasattr(self, "ts_color_btn"):
            color = self.ts_color.get()
            self.ts_color_btn.configure(fg_color=color, hover_color=color)
    
    def _pick_ts_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.ts_color.get())[1]
        if color:
            self.ts_color.set(color)

    def _pick_ts_bg_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.ts_bg_color.get())[1]
        if color:
            self.ts_bg_color.set(color)
            self.ts_bg_btn.configure(fg_color=color, hover_color=color)
