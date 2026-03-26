"""
ScreenWatermark Pro - Main Entry Point
v8.0 with CTk Migration
"""

import sys
import threading

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from core.settings import load_settings
import i18n
cfg = load_settings()
i18n.set_language(cfg.get("language", "en"))

from system.ipc import _acquire_single_instance, _ipc_server_thread, _SW_IPC_SERVER, _SW_LOCK_FILE, _ipc_pending_show
from ui.main_window import ScreenWatermarkApp

if __name__ == "__main__":
    _is_first, _ipc_port = _acquire_single_instance()
    
    if not _is_first:
        sys.exit(0)
    
    _app_ref = []
    if _SW_IPC_SERVER is not None:
        t = threading.Thread(
            target=_ipc_server_thread,
            args=(_SW_IPC_SERVER, _app_ref),
            daemon=True, name="ScreenWM-IPC")
        t.start()
    
    app = ScreenWatermarkApp()
    _app_ref.append(app)
    
    if _ipc_pending_show.is_set():
        _ipc_pending_show.clear()
        app.after(0, app._show_window)
    
    app.mainloop()
    
    try:
        _SW_LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
