"""
ScreenWatermark Pro - CTk Accordion Widget
Reusable collapsible panel component
"""

import customtkinter as ctk
from core.constants import CARD, CARD2, BORDER, ACCENT, TEXT, MUTED, FONT, FONT_MONO

class CTkAccordion(ctk.CTkFrame):
    def __init__(self, parent, title: str, icon: str = "",
                 open_by_default: bool = False,
                 on_toggle=None, **kwargs):
        super().__init__(parent, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self._open = open_by_default
        self._on_toggle_cb = on_toggle

        self._hdr = ctk.CTkFrame(self, fg_color="transparent", height=38)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)
        self._hdr.bind("<Button-1>", lambda e: self.toggle())

        if icon:
            ctk.CTkLabel(self._hdr, text=icon, fg_color="transparent",
                         font=(FONT, 12)).pack(side="left", padx=(12, 6), pady=8)
        
        self._title_lbl = ctk.CTkLabel(
            self._hdr, text=title, font=(FONT, 11, "bold"),
            text_color=TEXT, fg_color="transparent")
        self._title_lbl.pack(side="left")
        
        self._summary_lbl = ctk.CTkLabel(
            self._hdr, text="", font=(FONT_MONO, 9),
            text_color=MUTED, fg_color="transparent")
        self._summary_lbl.pack(side="right", padx=(0, 8))
        
        self._chevron = ctk.CTkLabel(
            self._hdr, text="▲" if open_by_default else "▼",
            font=(FONT, 9), text_color=MUTED, fg_color="transparent")
        self._chevron.pack(side="right", padx=(0, 6))

        ctk.CTkFrame(self, fg_color=BORDER, height=1,
                     corner_radius=0).pack(fill="x")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        if open_by_default:
            self._body.pack(fill="x", padx=12, pady=(6, 10))

    def toggle(self):
        self._open = not self._open
        if self._open:
            self._body.pack(fill="x", padx=12, pady=(6, 10))
            self._chevron.configure(text="▲")
            self.configure(border_color="#2e2e48")
        else:
            self._body.pack_forget()
            self._chevron.configure(text="▼")
            self.configure(border_color=BORDER)
        if self._on_toggle_cb:
            self._on_toggle_cb(self._open)

    def set_summary(self, text: str):
        self._summary_lbl.configure(text=text)

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body

    @property
    def is_open(self) -> bool:
        return self._open
