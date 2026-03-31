"""
ScreenWatermark Pro - Split Shot Button Widget
Fullscreen + Region split button component
"""

import customtkinter as ctk
from core.constants import ACCENT, ACCENT2, TEXT, MUTED, CARD, CARD2, BORDER, FONT

class SplitShotButton(ctk.CTkFrame):
    def __init__(self, parent, on_fullscreen, on_region, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_fullscreen = on_fullscreen
        self._on_region = on_region
        self._enabled = True
        self._current_mode = "fullscreen"

        self._btn_fullscreen = ctk.CTkButton(
            self, text="Fullscreen", width=90, height=32,
            fg_color=ACCENT, hover_color=BORDER,
            text_color="white", font=(FONT, 13),
            corner_radius=6, border_width=1, border_color=ACCENT,
            command=self._on_fullscreen_click)
        self._btn_fullscreen.pack(side="left", padx=(0, 2), pady=0)

        self._btn_region = ctk.CTkButton(
            self, text="Region", width=90, height=32,
            fg_color=CARD, hover_color=BORDER,
            text_color=MUTED, font=(FONT, 13),
            corner_radius=6, border_width=1, border_color=BORDER,
            command=self._on_region_click)
        self._btn_region.pack(side="left", padx=2, pady=0)

    def _on_fullscreen_click(self):
        if self._enabled:
            self._on_fullscreen()

    def _on_region_click(self):
        if self._enabled:
            self._on_region()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        state = "normal" if enabled else "disabled"
        self._btn_fullscreen.configure(state=state)
        self._btn_region.configure(state=state)

    def set_mode(self, mode: str):
        self._current_mode = mode
        if mode == "fullscreen":
            self._btn_fullscreen.configure(fg_color=ACCENT, text_color="white", border_width=0)
            self._btn_region.configure(fg_color=CARD, text_color=MUTED, border_width=1, border_color=BORDER)
        else:
            self._btn_fullscreen.configure(fg_color=CARD, text_color=MUTED, border_width=1, border_color=BORDER)
            self._btn_region.configure(fg_color=ACCENT, text_color="white", border_width=0)
