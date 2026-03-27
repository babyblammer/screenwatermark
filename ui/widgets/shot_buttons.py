"""
ScreenWatermark Pro - Split Shot Button Widget
Fullscreen + Region split button component
"""

import customtkinter as ctk
from core.constants import ACCENT, ACCENT2, TEXT, CARD2, BORDER, FONT

class SplitShotButton(ctk.CTkFrame):
    def __init__(self, parent, on_fullscreen, on_region, **kwargs):
        super().__init__(parent, fg_color=CARD2, corner_radius=8,
                         border_width=1, border_color=BORDER, **kwargs)
        self._on_fullscreen = on_fullscreen
        self._on_region = on_region
        self._enabled = True

        self._btn_fullscreen = ctk.CTkButton(
            self, text="Fullscreen", width=95, height=30,
            fg_color=ACCENT, hover_color="#5a52e0",
            text_color="white", font=(FONT, 10, "bold"),
            corner_radius=6, border_width=0,
            command=self._on_fullscreen_click)
        self._btn_fullscreen.pack(side="left", padx=(6, 3), pady=6)

        self._btn_region = ctk.CTkButton(
            self, text="Region", width=95, height=30,
            fg_color="#32324e", hover_color="#3a3a5e",
            text_color=TEXT, font=(FONT, 10, "bold"),
            corner_radius=6, border_width=0,
            command=self._on_region_click)
        self._btn_region.pack(side="left", padx=(3, 6), pady=6)

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
        if mode == "fullscreen":
            self._btn_fullscreen.configure(fg_color=ACCENT, text_color="white")
            self._btn_region.configure(fg_color="#32324e", text_color=TEXT)
        else:
            self._btn_fullscreen.configure(fg_color="#32324e", text_color=TEXT)
            self._btn_region.configure(fg_color=ACCENT, text_color="white")
