"""
ScreenWatermark Pro - UI History Popup Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import io
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from core.constants import PANEL, CARD, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, BORDER
from core.clipboard import copy_image_to_clipboard
class HistoryPopup(tk.Toplevel):
    """
    Floating window berisi 5 thumbnail riwayat.
    [C3-fix] _copy_entry sekarang cek winfo_exists() sebelum memanggil after().
    """
    THUMB_W = 150; THUMB_H = 84

    def __init__(self, master: "ScreenWatermarkApp"):
        super().__init__(master)
        self.app  = master
        self._tks = []
        self._destroyed = False
        self.title("Riwayat Screenshot")
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._safe_destroy)
        self.bind("<Escape>", lambda e: self._safe_destroy())
        # [004-4] Anti-flicker triple-lock:
        # 1. withdraw(): window tidak di-render WM sama sekali
        # 2. alpha=0: jika WM ignore withdraw, window tetap invisible
        # 3. build + center tanpa render antara (tidak ada update_idletasks di sini)
        # 4. geometry → deiconify → alpha=1 dalam satu sequence
        self.withdraw()
        self.attributes("-alpha", 0.0)
        self._build()
        # Center tanpa update_idletasks (pakai winfo_reqwidth yg sudah ada)
        self._center_no_flash()
        self.attributes("-topmost", True)
        self.deiconify()
        # Restore alpha setelah deiconify — window muncul langsung di posisi benar
        self.after(0, lambda: self.attributes("-alpha", 1.0))

    def _safe_destroy(self):
        if not self._destroyed:
            self._destroyed = True
            self.destroy()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _center_no_flash(self):
        """[004-4] Center tanpa update_idletasks — mencegah partial render flash.
        Pakai winfo_reqwidth/reqheight yang sudah ter-update saat widget di-pack.
        """
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        # reqwidth/reqheight tersedia setelah pack tanpa perlu idletasks
        w = self.winfo_reqwidth() or 600
        h = self.winfo_reqheight() or 300
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL); hdr.pack(fill="x", padx=10, pady=(10,6))
        tk.Label(hdr, text="\U0001f5bc  Riwayat Screenshot",
                 font=("Segoe UI", 11, "bold"), bg=PANEL, fg=ACCENT
                 ).pack(side="left")
        tk.Button(hdr, text="\u2715", bg=PANEL, fg=MUTED, bd=0,
                  font=("Segoe UI", 11), command=self._safe_destroy
                  ).pack(side="right")

        # [m6-fix] Salin history di bawah lock agar iterasi aman
        with self.app._history_lock:
            history = list(self.app._history)

        if not history:
            tk.Label(self, text="Belum ada screenshot.",
                     bg=PANEL, fg=MUTED, font=("Segoe UI", 10)
                     ).pack(pady=24, padx=24)
            return

        grid = tk.Frame(self, bg=PANEL); grid.pack(padx=10, pady=(0,4))

        for i, entry in enumerate(reversed(history)):
            col = tk.Frame(grid, bg=CARD, cursor="hand2", padx=3, pady=4)
            col.grid(row=0, column=i, padx=4, pady=4)

            try:
                thumb = Image.open(io.BytesIO(entry["thumb_bytes"]))
                thumb.thumbnail((self.THUMB_W, self.THUMB_H), Image.LANCZOS)
                bg_img = Image.new("RGB", (self.THUMB_W, self.THUMB_H), (10,10,18))
                bg_img.paste(thumb,
                             ((self.THUMB_W - thumb.width)  // 2,
                              (self.THUMB_H - thumb.height) // 2))
                tk_img = ImageTk.PhotoImage(bg_img)
            except:
                tk_img = None
            self._tks.append(tk_img)

            if tk_img:
                tk.Label(col, image=tk_img, bg=CARD).pack()

            tk.Label(col, text=entry["timestamp"].strftime("%H:%M:%S"),
                     bg=CARD, fg=TEXT, font=("Segoe UI", 10)).pack()
            tk.Label(col, text=f"{entry['width']}\u00d7{entry['height']}",
                     bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack()

            def _click(ev, en=entry, c=col): self._copy_entry(en, c)
            for child in list(col.winfo_children()) + [col]:
                child.bind("<Button-1>", _click)

        tk.Label(self, text="Klik thumbnail untuk menyalin ke clipboard",
                 bg=PANEL, fg=TEXT, font=("Segoe UI", 10)
                 ).pack(pady=(2,8))

    def _render(self):
        """[U3] Refresh konten popup dengan history terbaru tanpa menutup window."""
        if self._destroyed or not self.winfo_exists():
            return
        # Hapus semua widget konten (bukan header)
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self._tks.clear()
        # Rebuild header + grid
        self._build()

    def _copy_entry(self, entry: dict, col: tk.Frame):
        if self._destroyed: return
        try:
            img = Image.open(io.BytesIO(entry["full_bytes"]))
            self.app.last_image = img
            copy_image_to_clipboard(img)
            if col.winfo_exists():
                orig = col.cget("bg")
                col.configure(bg=SUCCESS)
                # [C3-fix] Guard destroy dengan _destroyed flag
                def _restore_and_close():
                    if not self._destroyed:
                        if col.winfo_exists(): col.configure(bg=orig)
                self.after(400, _restore_and_close)
            self.app.status_var.set("Riwayat disalin ke clipboard!")
            # [m5-fix] Cek btn_copy masih exists sebelum config
            try:
                self.app.btn_copy.config(state="normal", bg=SUCCESS)
                self.app.after(2000, lambda: self.app.btn_copy.config(bg=ACCENT2))
            except Exception: pass
            # [C3-fix] Tutup dengan safe_destroy
            self.after(600, self._safe_destroy)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

