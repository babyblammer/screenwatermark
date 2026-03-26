"""
ScreenWatermark Pro - Config Rows Widgets
Helper functions for slider, toggle, and color swatch rows
"""

import customtkinter as ctk
from core.constants import CARD, CARD2, BORDER, ACCENT, ACCENT2, TEXT, MUTED, FONT, FONT_MONO

def label(parent, text: str, pack=True) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text=text, font=(FONT, 9),
                       text_color=MUTED, fg_color="transparent")
    if pack:
        lbl.pack(side="left", padx=(0, 3))
    return lbl

def sep(parent) -> ctk.CTkFrame:
    f = ctk.CTkFrame(parent, fg_color=BORDER, width=1, height=18, corner_radius=0)
    f.pack(side="left", padx=5)
    return f

def slider_row(parent, lbl_text: str, var, from_: int, to: int,
               unit: str = "", width: int = 70) -> ctk.CTkLabel:
    label(parent, lbl_text)
    val_lbl = ctk.CTkLabel(parent, text=f"{var.get()} {unit}",
                            font=(FONT_MONO, 9), text_color=ACCENT,
                            fg_color="transparent", width=36)
    ctk.CTkSlider(parent, from_=from_, to=to, variable=var, width=width, height=14,
                  command=lambda v, l=val_lbl, u=unit:
                      l.configure(text=f"{int(float(v))} {u}")
                  ).pack(side="left", padx=(0, 2))
    val_lbl.pack(side="left")
    return val_lbl

def pill_toggle(parent, values: list, default: str,
                command) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(parent, fg_color=CARD2, corner_radius=6,
                          border_width=1, border_color=BORDER)
    frame.pack(side="left", padx=(0, 4))
    btns = {}
    def _click(v):
        for k, b in btns.items():
            b.configure(fg_color=ACCENT if k == v else "transparent",
                        text_color="white" if k == v else MUTED)
        command(v)
    for val in values:
        b = ctk.CTkButton(
            frame, text=val, width=34, height=22,
            fg_color=ACCENT if val == default else "transparent",
            hover_color=CARD2,
            text_color="white" if val == default else MUTED,
            corner_radius=5, font=(FONT, 9),
            command=lambda v=val: _click(v))
        b.pack(side="left", padx=2, pady=2)
        btns[val] = b
    return frame

def color_swatch(parent, var, label_text: str = "") -> tuple:
    swatch = {}
    def _pick():
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=var.get())[1]
        if color:
            var.set(color)
            swatch['btn'].configure(fg_color=color, hover_color=color)
    
    if label_text:
        label(parent, label_text)
    btn = ctk.CTkButton(
        parent, text="", width=22, height=22, corner_radius=4,
        fg_color=var.get(), hover_color=var.get(),
        command=_pick)
    btn.pack(side="left", padx=(0, 4))
    swatch['btn'] = btn
    return btn

def checkbox(parent, text: str, var, command=None) -> ctk.CTkCheckBox:
    cb = ctk.CTkCheckBox(parent, text=text, variable=var,
                         command=command,
                         fg_color=ACCENT, hover_color=ACCENT,
                         border_color=BORDER)
    return cb

def radio_group(parent, options: list, var, command=None) -> list:
    rbs = []
    for lbl, val in options:
        rb = ctk.CTkRadioButton(parent, text=lbl, variable=var, value=val,
                                command=command,
                                fg_color=ACCENT, hover_color=ACCENT,
                                border_color=BORDER)
        rb.pack(side="left", padx=4)
        rbs.append(rb)
    return rbs
