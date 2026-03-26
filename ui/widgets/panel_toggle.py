"""
ScreenWatermark Pro - Panel Toggle Widget
Preview/History toggle pill component
"""

import customtkinter as ctk
from core.constants import ACCENT, ACCENT2, TEXT, MUTED, CARD2, BORDER, FONT

class PanelToggle(ctk.CTkFrame):
    def __init__(self, parent, panels: list, command, **kwargs):
        super().__init__(parent, fg_color=CARD2, corner_radius=8,
                         border_width=1, border_color=BORDER, **kwargs)
        self._panels = panels
        self._command = command
        self._active_key = panels[0][1] if panels else ""
        self._btns = {}

        for i, (label, key) in enumerate(panels):
            is_first = (i == 0)
            is_last = (i == len(panels) - 1)
            
            btn = ctk.CTkButton(
                self, text=label, width=80, height=28,
                fg_color=ACCENT if i == 0 else "transparent",
                hover_color=ACCENT if i == 0 else CARD2,
                text_color="white" if i == 0 else MUTED,
                corner_radius=0 if is_first else (0 if is_last else 0),
                font=(FONT, 10), border_width=0,
                command=lambda k=key: self._on_click(k))
            btn.pack(side="left", fill="y")
            self._btns[key] = btn

        self._badge_labels = {}

    def _on_click(self, key: str):
        self.set_active(key)
        self._command(key)

    def set_active(self, key: str):
        self._active_key = key
        for k, btn in self._btns.items():
            if k == key:
                btn.configure(fg_color=ACCENT, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=MUTED)

    def set_badge(self, key: str, count: int):
        if key not in self._btns:
            return
        btn = self._btns[key]
        if hasattr(self, '_badge_labels') and key in self._badge_labels:
            badge = self._badge_labels[key]
            if count > 0:
                badge.configure(text=str(count))
                badge.pack(side="right", padx=(0, 4))
            else:
                badge.pack_forget()
