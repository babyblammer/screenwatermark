"""
ScreenWatermark Pro - UI Settings Window Module (CTk Version)
v8.0 Migration from tkinter to customtkinter
"""

import os
import sys

import customtkinter as ctk

from core.constants import BG, PANEL, CARD, CARD2, BORDER, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, WARN
from core.settings import save_settings
from system.hotkeys import _preset_label
from system.startup import set_run_at_startup, get_run_at_startup
from i18n import t

FONT = "Segoe UI"
FONT_MONO = "Consolas"


class SettingsWindow(ctk.CTkToplevel):
    """
    Settings window using CTk.
    v8.0: Removed Watermark and Timestamp cards (now in main window accordions).
    v8.0: Added Language card.
    """
    def __init__(self, master: "ScreenWatermarkApp"):
        super().__init__(master)
        self.app = master
        self.title("Settings")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.lift()
        self.focus_force()

    def _on_close(self):
        self.withdraw()

    def _build_removed_notice(self, parent):
        notice = ctk.CTkFrame(parent, fg_color="#180d0d", corner_radius=7)
        notice.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(notice, text="\u2718  Watermark config  →  main window accordion\n\u2718  Timestamp config  →  main window accordion",
                     font=(FONT_MONO, 9), text_color="#7a3a3a", anchor="w", justify="left"
                     ).pack(padx=12, pady=8)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, height=42, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_title = ctk.CTkLabel(header, text=f"  \u2699  {t('settings')}",
                                    font=(FONT, 13, "bold"), text_color=ACCENT)
        header_title.pack(side="left", padx=14, pady=10)

        self.version_lbl = ctk.CTkLabel(header, text=f"v{self.app.VERSION}",
                                         font=(FONT_MONO, 9), text_color=MUTED)
        self.version_lbl.pack(side="right", padx=12, pady=10)

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG,
                                         scrollbar_button_color=ACCENT,
                                         scrollbar_button_hover_color=ACCENT2)
        scroll.pack(fill="both", expand=True, padx=10, pady=(8, 0))
        
        self._build_removed_notice(scroll)
        self._card(scroll, t("startup"), self._build_startup_card)
        self._card(scroll, t("capture"), self._build_capture_card)
        self._card(scroll, t("hotkeys"), self._build_hotkey_card)
        self._card(scroll, t("language"), self._build_language_card)

        footer = ctk.CTkFrame(self, fg_color=PANEL, height=48, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(footer, text=t("credits"), font=(FONT, 10),
                      fg_color=CARD, text_color=MUTED,
                      hover_color=BORDER, width=80, border_width=1, border_color=BORDER,
                      command=self._open_credits
                      ).pack(side="left", padx=12)
        
        ctk.CTkButton(footer, text=t("reset_default"), font=(FONT, 10),
                      fg_color="transparent", text_color=MUTED,
                      hover_color=PANEL, width=120,
                      command=self._on_reset_default
                      ).pack(side="left", padx=4)

        spacer = ctk.CTkFrame(footer, fg_color=PANEL, width=100)
        spacer.pack(side="left", expand=True)

        ctk.CTkButton(footer, text=t("close"), font=(FONT, 10, "bold"),
                      fg_color=ACCENT, text_color="white", width=80,
                      command=self._on_close
                      ).pack(side="right", padx=12)

    def _card(self, parent, title, fn):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=(0, 8))
        
        title_lbl = ctk.CTkLabel(card, text=title, font=(FONT, 11, "bold"),
                                  text_color=ACCENT)
        title_lbl.pack(anchor="w", padx=12, pady=(10, 4))
        
        sep = ctk.CTkFrame(card, fg_color=BORDER, height=1)
        sep.pack(fill="x", padx=12, pady=(0, 8))
        
        body = ctk.CTkFrame(card, fg_color=CARD)
        body.pack(fill="x", padx=12, pady=(0, 10))
        
        fn(body)

    def _slider_row(self, parent, label, var, from_, to, unit=""):
        row = ctk.CTkFrame(parent, fg_color=CARD)
        row.pack(fill="x", pady=3)
        
        ctk.CTkLabel(row, text=label, font=(FONT, 10), text_color=TEXT,
                     width=100, anchor="w").pack(side="left")
        
        val_lbl = ctk.CTkLabel(row, text=f"{var.get()} {unit}", font=(FONT, 10, "bold"),
                                text_color=ACCENT, width=60, anchor="e")
        val_lbl.pack(side="right")
        
        def update_val(v):
            val_lbl.configure(text=f"{int(float(v))} {unit}")
        
        slider = ctk.CTkSlider(row, from_=from_, to=to, variable=var,
                               progress_color=ACCENT, button_color=ACCENT2,
                               button_hover_color=ACCENT,
                               command=update_val)
        slider.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _on_reset_default(self):
        from core.settings import DEFAULT_SETTINGS
        for key, val in DEFAULT_SETTINGS.items():
            if hasattr(self.app, key):
                var = getattr(self.app, key)
                if hasattr(var, 'set'):
                    var.set(val)
        save_settings(self.app)
        self.app._refresh_snapshot()

    # ── Startup card ─────────────────────────────────────────────────────────
    def _build_startup_card(self, p):
        app = self.app

        actual = get_run_at_startup()
        if actual != app.run_at_startup.get():
            app.run_at_startup.set(actual)
        self._prev_startup = [app.run_at_startup.get()]

        def on_toggle():
            new_val = app.run_at_startup.get()
            ok = set_run_at_startup(new_val)
            if not ok:
                app.run_at_startup.set(self._prev_startup[0])
                from tkinter import messagebox
                messagebox.showwarning("Startup",
                    "Failed to set startup.\nMake sure you have sufficient permissions.",
                    parent=self)
            else:
                self._prev_startup[0] = new_val

        run_cb = ctk.CTkCheckBox(p, text=t("run_at_startup"),
                                  variable=app.run_at_startup,
                                  onvalue=True, offvalue=False,
                                  command=on_toggle)
        run_cb.pack(anchor="w", pady=(0, 4))

        min_cb = ctk.CTkCheckBox(p, text=t("start_minimized"),
                                  variable=app.start_minimized,
                                  onvalue=True, offvalue=False)
        min_cb.pack(anchor="w", pady=(0, 6))

        self.startup_status_lbl = ctk.CTkLabel(p, text="", font=(FONT, 8),
                                                 text_color=MUTED, anchor="w")
        self.startup_status_lbl.pack(anchor="w")
        self._refresh_startup_status()

    def _refresh_startup_status(self):
        if not hasattr(self, "startup_status_lbl"):
            return
        registered = get_run_at_startup()
        if registered:
            self.startup_status_lbl.configure(
                text="\u2713 Registered in system startup.", text_color=SUCCESS)
        else:
            self.startup_status_lbl.configure(
                text="\u25cb Not registered in system startup.", text_color=MUTED)

    # ── Capture card ──────────────────────────────────────────────────────────
    def _build_capture_card(self, p):
        app = self.app

        mode_row = ctk.CTkFrame(p, fg_color=CARD)
        mode_row.pack(fill="x", pady=(0, 6))
        
        ctk.CTkLabel(mode_row, text=t("default_mode") + ":", font=(FONT, 10),
                     text_color=TEXT, anchor="w").pack(side="left")
        
        def on_mode_change(val):
            app.capture_mode.set(val)
        
        mode_opt = ctk.CTkOptionMenu(mode_row, values=["Fullscreen", "Region"],
                                      command=on_mode_change, width=100,
                                      fg_color=BORDER, button_color=ACCENT,
                                      button_hover_color=ACCENT2)
        mode_opt.set("Fullscreen" if app.capture_mode.get() == "fullscreen" else "Region")
        mode_opt.pack(side="left", padx=(8, 0))

        region_row = ctk.CTkFrame(p, fg_color=CARD)
        region_row.pack(fill="x", pady=(0, 4))
        
        self.region_label = ctk.CTkLabel(region_row, text=app._region_text(),
                                          font=(FONT, 9), text_color=TEXT, anchor="w")
        self.region_label.pack(side="left")
        
        ctk.CTkButton(region_row, text="\u21bb Reset", font=(FONT, 8),
                       fg_color=BORDER, text_color=TEXT, hover_color=ACCENT2,
                       width=60, height=24, command=app._reset_region
                       ).pack(side="right")

        self._slider_row(p, t("delay") + ":", app.delay_sec, 0, 10, "s")

        fmt_row = ctk.CTkFrame(p, fg_color=CARD)
        fmt_row.pack(fill="x", pady=(4, 2))
        
        ctk.CTkLabel(fmt_row, text="TS Format:", font=(FONT, 10),
                     text_color=TEXT, anchor="w").pack(side="left")
        
        fmt_entry = ctk.CTkEntry(fmt_row, textvariable=app.ts_format,
                                  width=140, fg_color=BORDER,
                                  border_color=BORDER, font=(FONT, 9))
        fmt_entry.pack(side="left", padx=(8, 4))
        
        for lbl, fmt in [("DD/MM", "%d/%m/%Y %H:%M:%S"), ("ISO", "%Y-%m-%d %H:%M")]:
            def set_fmt(f=fmt):
                app.ts_format.set(f)
            ctk.CTkButton(fmt_row, text=lbl, font=(FONT, 8),
                           fg_color=BORDER, text_color=TEXT, hover_color=ACCENT,
                           width=50, height=24, command=set_fmt
                           ).pack(side="left")

    # ── Hotkey card ──────────────────────────────────────────────────────────
    def _build_hotkey_card(self, p):
        app = self.app

        info_box = ctk.CTkFrame(p, fg_color="#1a1a2e", corner_radius=6)
        info_box.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(info_box, text="\u2328  Active Hotkeys",
                     font=(FONT, 10, "bold"), text_color=ACCENT
                     ).pack(anchor="w", padx=10, pady=6)

        hotkeys = [
            ("Fullscreen Screenshot", app.hotkey_fullscreen),
            ("Region Screenshot", app.hotkey_region),
            ("Open History", app.hotkey_history),
        ]
        
        for label, var in hotkeys:
            row = ctk.CTkFrame(p, fg_color=CARD)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{label} :", font=(FONT, 9),
                         text_color=MUTED, width=140, anchor="w"
                         ).pack(side="left")
            
            disp = _preset_label(var.get())
            ctk.CTkLabel(row, text=disp, font=(FONT_MONO, 10, "bold"),
                         text_color=ACCENT
                         ).pack(side="left", padx=6)

        ctk.CTkLabel(p, text="App continues running in System Tray when window is closed.",
                     font=(FONT, 8), text_color=MUTED, anchor="w"
                     ).pack(anchor="w", pady=(10, 0))

    # ── Language card ─────────────────────────────────────────────────────────
    def _build_language_card(self, p):
        from i18n import get_language, set_language, t as tt
        
        def on_language_change(lang):
            lang_map = {"English": "en", "Indonesian": "id"}
            code = lang_map.get(lang, "en")
            set_language(code)
            from core.settings import load_settings, save_settings
            cfg = load_settings()
            cfg["language"] = code
            save_settings(cfg)
        
        row = ctk.CTkFrame(p, fg_color=CARD)
        row.pack(fill="x", pady=(0, 4))
        
        ctk.CTkLabel(row, text=t("language") + ":", font=(FONT, 10),
                     text_color=TEXT, anchor="w").pack(side="left")
        
        lang = "English" if get_language() == "en" else "Indonesian"
        lang_opt = ctk.CTkOptionMenu(row, values=["English", "Indonesian"],
                                      command=on_language_change, width=120,
                                      fg_color=BORDER, button_color=ACCENT,
                                      button_hover_color=ACCENT2)
        lang_opt.set(lang)
        lang_opt.pack(side="left", padx=(8, 0))
        
        ctk.CTkLabel(p, text="\u2139 " + t("restart_required"),
                     font=(FONT, 8), text_color=MUTED, anchor="w"
                     ).pack(anchor="w")

    def _open_credits(self):
        CreditsPopup(self)


class CreditsPopup(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.app = master.app
        self.title("Credits")
        self.geometry("400xauto")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(master)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self._build_ui()
        self.update_idletasks()
        self.geometry(f"400x{self.winfo_reqheight()}")
        self.lift()
        self.focus_force()

    def _sep(self, parent):
        sep = ctk.CTkFrame(parent, fg_color=BORDER, height=1)
        sep.pack(fill="x", pady=8)

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=BG)
        container.pack(fill="both", expand=True, padx=24, pady=16)

        app_info = ctk.CTkFrame(container, fg_color="transparent")
        app_info.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(app_info, text="ScreenWatermark Pro",
                     font=(FONT, 14, "bold"), text_color=TEXT
                     ).pack()

        ctk.CTkLabel(app_info, text=f"v{self.app.VERSION}",
                     font=(FONT_MONO, 9), text_color=MUTED
                     ).pack()

        ctk.CTkLabel(app_info, text="Screenshot utility with watermark & timestamp overlay",
                     font=(FONT, 9), text_color=MUTED
                     ).pack(pady=(2, 0))

        self._sep(container)

        license_info = ctk.CTkFrame(container, fg_color="transparent")
        license_info.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(license_info, text="© 2026 Pika25 Production",
                     font=(FONT_MONO, 9), text_color=MUTED
                     ).pack()
        ctk.CTkLabel(license_info, text="All rights reserved.",
                     font=(FONT, 9), text_color=MUTED
                     ).pack()
        ctk.CTkLabel(license_info, text="MIT License — Donationware",
                     font=(FONT, 9, "bold"), text_color=ACCENT
                     ).pack(pady=(4, 0))

        self._sep(container)

        team_section = ctk.CTkLabel(container, text="Development Team",
                                    font=(FONT, 10, "bold"), text_color=ACCENT,
                                    anchor="w")
        team_section.pack(fill="x", pady=(0, 8))

        team_rows = [
            ("PM / QAPM", "Gayuh Marga H."),
            ("Developer", "Claudeito Dimitri Anthropocic"),
            ("UI/UX Lead", "Клодейто Димитри Антропосик"),
            ("UI/UX Lead", "Gayuh Marga H."),
            ("QA Lead", "Гаюх Марга Х."),
            ("Quality Assurance", "Rvbxxyn"),
            ("Quality Assurance", "Ahmed Rubion"),
            ("Quality Assurance", "Basmusin · Dimitry Anthropocic"),
        ]

        team_frame = ctk.CTkFrame(container, fg_color="transparent")
        team_frame.pack(fill="x", pady=(0, 8))

        for role, name in team_rows:
            row = ctk.CTkFrame(team_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{role}:", font=(FONT, 9), text_color=MUTED,
                         width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=name, font=(FONT, 9), text_color=TEXT,
                         anchor="w").pack(side="left")

        self._sep(container)

        deps_section = ctk.CTkLabel(container, text="Dependencies",
                                    font=(FONT, 10, "bold"), text_color=ACCENT,
                                    anchor="w")
        deps_section.pack(fill="x", pady=(0, 8))

        deps_text = "pillow ✓   mss ✓   pystray ✓   pynput ✓   pywin32 ✓"
        ctk.CTkLabel(container, text=deps_text,
                     font=(FONT_MONO, 9), text_color=SUCCESS,
                     anchor="w"
                     ).pack(fill="x")

        self._sep(container)

        ctk.CTkButton(container, text="Close", font=(FONT, 10, "bold"),
                      fg_color=ACCENT, text_color="white", width=120,
                      command=self.destroy
                      ).pack(pady=(8, 0))
