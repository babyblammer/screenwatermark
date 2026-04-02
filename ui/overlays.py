"""
ScreenWatermark Pro - UI Overlays Module
Extracted from Screen Watermark_3.9.1f_HF1.py
Note: These classes use pure tkinter (not CTk) due to overrideredirect() requirement
"""

import tkinter as tk
from core.constants import ACCENT, TEXT, MUTED, BORDER
from system.hotkeys import _ensure_pynput, _pynput_kb
from i18n import t

class CountdownOverlay(tk.Toplevel):
    """
    [GC3-K5] FS-03: Overlay fullscreen transparan menampilkan countdown
    dengan angka besar di tengah layar agar user selalu melihat hitungan mundur.

    Sebelumnya countdown hanya update status_var (label kecil di bottom bar)
    yang mudah terlewat — terutama jika user sudah beralih ke aplikasi lain.

    Desain:
    - Toplevel semi-transparan (alpha ~0.6), background gelap, -topmost True
    - Angka countdown font besar (~120px) di tengah layar
    - Sub-teks "Screenshot dalam..." dan "Esc untuk batal"
    - Dipanggil dari _countdown() di main thread
    - Tutup otomatis saat countdown selesai atau Esc ditekan
    - Main window di-withdraw saat overlay aktif (FS-01 sekaligus tertangani
      untuk path dengan delay)
    """
    def __init__(self, master: "ScreenWatermarkApp", n: int, cancel_cb):
        super().__init__(master)
        self._cancel_cb = cancel_cb
        self._alive     = True

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.72)
        self.attributes("-topmost", True)
        self.configure(bg="#0a0a10")

        # Teks countdown utama
        self._var = tk.StringVar(value=str(n))
        tk.Label(self, textvariable=self._var,
                 font=("Segoe UI", 120, "bold"),
                 bg="#0a0a10", fg="#6c63ff"
                 ).place(relx=0.5, rely=0.42, anchor="center")

        # Sub-teks atas
        tk.Label(self,
                 text=t("countdown_top"),
                 font=("Segoe UI", 18),
                 bg="#0a0a10", fg="#7070a0"
                 ).place(relx=0.5, rely=0.30, anchor="center")

        # Sub-teks bawah
        tk.Label(self,
                 text=t("countdown_bottom"),
                 font=("Segoe UI", 13),
                 bg="#0a0a10", fg="#4a4a6a"
                 ).place(relx=0.5, rely=0.62, anchor="center")

        self.bind("<Escape>", self._on_escape)
        self.focus_force()
        # [GC4-K6] overrideredirect(True) mencegah WM memberi fokus keyboard ke
        # overlay, sehingga bind("<Escape>") tidak pernah ter-trigger.
        # Solusi: pasang pynput global Listener untuk Esc — sama dengan pola
        # yang dipakai RegionSelector._start_esc_listener().
        self._esc_listener = None
        self.after(50, self._start_esc_listener)

    def _start_esc_listener(self):
        """[GC4-K6] Global pynput Listener untuk Escape pada countdown overlay.
        suppress=False — konsisten dengan RegionSelector (tidak trigger UAC)."""
        try:
            _ensure_pynput()
            from pynput.keyboard import Key as _Key
            def _on_press(key):
                if key == _Key.esc:
                    if self._alive:
                        self.after(0, self._on_escape)
                    return False  # stop listener setelah Esc pertama
            self._esc_listener = _pynput_kb.Listener(
                on_press=_on_press, suppress=False)
            self._esc_listener.daemon = True
            self._esc_listener.start()
        except Exception:
            pass  # fallback ke Tkinter bind saja

    def _stop_esc_listener(self):
        if self._esc_listener:
            try: self._esc_listener.stop()
            except Exception: pass
            self._esc_listener = None

    def update_count(self, n: int):
        """Update angka yang tampil. Dipanggil dari main thread setiap detik."""
        if self._alive and self.winfo_exists():
            self._var.set(str(n))

    def close(self):
        """Tutup overlay dari main thread."""
        self._alive = False
        self._stop_esc_listener()
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass

    def _on_escape(self, e=None):
        if not self._alive:
            return
        self._alive = False
        self._stop_esc_listener()
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass
        self._cancel_cb()

# ── Region Selector Overlay ───────────────────────────────────────────────────
class RegionSelector(tk.Toplevel):
    def __init__(self, master, on_select, on_cancel):
        super().__init__(master)
        self.on_select = on_select
        self.on_cancel = on_cancel
        self._start    = None
        self._rect_id  = None
        self._done     = False   # [C3-style guard] pastikan callback hanya dipanggil sekali

        # [003-1] Tidak pakai overrideredirect — itu memblokir keyboard event
        # di Windows karena WM menolak grab pada fullscreen overrideredirect.
        # Gunakan window biasa dengan title bar tersembunyi via attributes.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.attributes("-alpha", 0.25)
        self.attributes("-topmost", True)
        self.configure(bg="#000000")
        # Sembunyikan title bar tanpa overrideredirect
        self.overrideredirect(True)   # tetap pakai tapi hanya setelah window ter-map
        self.update_idletasks()        # paksa window ter-map ke layar dulu

        self.canvas = tk.Canvas(self, bg="#000000",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.create_text(sw//2, sh//2,
            text=t("overlay_region_hint"),
            fill="white", font=("Segoe UI", 14, "bold"),
            justify="center", tags="hint")

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>",        self._on_escape)
        self.canvas.bind("<Escape>", self._on_escape)
        self.focus_set()
        self.focus_force()
        # grab_set untuk mouse — mencegah drag keluar window
        try: self.grab_set()
        except Exception: pass
        # [GC2-fix 002-2] Tunda start esc listener 60ms — beri WM waktu transfer focus
        # ke overlay sebelum pynput mulai intercept. Mencegah Esc bocor ke app lain
        # terutama saat main window dalam state iconic (minimized) sebelumnya.
        self._esc_listener = None
        self.after(60, self._start_esc_listener)

    def _start_esc_listener(self):
        """[003-1] Global pynput Listener untuk Escape.
        [004-3] suppress=False — suppress=True memicu UAC dialog Windows saat
        user klik ke elevated process (Notepad di UAC, Task Manager, dsb)
        karena WH_KEYBOARD_LL hook dianggap mencoba intercept input elevated.
        Trade-off: Escape juga diterima app lain (misal menutup dialog).
        Ini jauh lebih aman daripada memicu "Modify your computer?" UAC prompt.
        _done flag sudah mencegah double-fire dari sisi RegionSelector.
        """
        try:
            _ensure_pynput()
            from pynput.keyboard import Key as _Key
            def _on_press(key):
                if key == _Key.esc:
                    if not self._done:
                        self.after(0, self._on_escape)
                    return False  # stop listener setelah Escape pertama
            # [004-3] suppress=False: tidak memicu UAC prompt
            self._esc_listener = _pynput_kb.Listener(
                on_press=_on_press, suppress=False)
            self._esc_listener.daemon = True
            self._esc_listener.start()
        except Exception:
            pass  # fallback ke Tkinter bind saja

    def _abs(self, ex, ey):
        return self.canvas.winfo_rootx() + ex, self.canvas.winfo_rooty() + ey

    def _on_press(self, e):
        self._start = self._abs(e.x, e.y)
        self.canvas.delete("hint")
        if self._rect_id: self.canvas.delete(self._rect_id)

    def _on_drag(self, e):
        if not self._start: return
        if self._rect_id: self.canvas.delete(self._rect_id)
        ax1, ay1 = self._start
        cx1, cy1 = ax1 - self.canvas.winfo_rootx(), ay1 - self.canvas.winfo_rooty()
        self._rect_id = self.canvas.create_rectangle(
            cx1, cy1, e.x, e.y,
            outline=ACCENT, width=2, fill=ACCENT, stipple="gray25", tags="sel")

    def _on_release(self, e):
        if not self._start or self._done: return
        self._done = True
        self._stop_esc_listener()
        x1, y1 = self._start
        x2, y2 = self._abs(e.x, e.y)
        # [002-1,2] Matikan fullscreen dan release grab sebelum destroy
        try: self.grab_release()
        except Exception: pass
        try:
            self.attributes("-fullscreen", False)
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        try: self.destroy()
        except Exception: pass
        # [GC3-K1] Paksa fokus ke master HANYA jika window tidak iconic.
        # focus_force() pada window iconic di Windows implicitly me-restore window
        # via Win32 SetFocus() karena WM tidak bisa memberi fokus ke minimized window.
        try:
            if self.master.wm_state() == "normal":
                self.master.focus_force()
        except Exception: pass
        if abs(x2-x1) < 10 or abs(y2-y1) < 10:
            self.on_cancel(); return
        self.on_select(min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))

    def _on_escape(self, e=None):
        if self._done: return
        self._done = True
        self._stop_esc_listener()
        self._safe_destroy_and_cancel()

    def _on_escape_global(self):
        """Dipanggil dari pynput thread via after(0,...) — aman untuk Tkinter."""
        self._on_escape()

    def _safe_destroy_and_cancel(self):
        """
        [002-1/004-3] Destroy RegionSelector secara aman dan cepat.
        - grab_release() dulu agar WM tahu window tidak lagi menangkap input.
        - alpha=0 + topmost=False agar window "menghilang" dari layar.
        - Destroy LANGSUNG (tidak pakai delay 30ms) agar WH_KEYBOARD_LL
          hook pynput tidak sempat memicu UAC saat user klik elevated window.
        - Setelah destroy, paksa fokus ke master window agar WM tahu
          siapa penerima input selanjutnya — mencegah Windows mengirim
          fokus ke elevated process.
        """
        try: self.grab_release()
        except Exception: pass
        try:
            self.attributes("-topmost", False)
            self.attributes("-alpha", 0.0)
        except Exception: pass
        # Destroy langsung — tidak ada delay
        try: self.destroy()
        except Exception: pass
        # [GC3-K1] Paksa fokus ke master HANYA jika window tidak iconic.
        # focus_force() pada window iconic di Windows implicitly me-restore window
        # via Win32 SetFocus() — inilah root cause bug 002-1.
        try:
            if self.master.wm_state() == "normal":
                self.master.focus_force()
        except Exception: pass
        self.on_cancel()

    def _stop_esc_listener(self):
        if self._esc_listener:
            try: self._esc_listener.stop()
            except: pass
            self._esc_listener = None

