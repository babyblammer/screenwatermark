"""
ScreenWatermark Pro - System Startup Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import os
import sys
from pathlib import Path

def _get_startup_script_path() -> str:
    """Return path absolut script yang sedang berjalan."""
    if getattr(sys, "frozen", False):
        return sys.executable          # PyInstaller exe
    return os.path.abspath(sys.argv[0])

def _get_pythonw_path() -> str:
    """
    [B2-fix] Return path absolut ke pythonw.exe (tanpa console window).

    Prioritas:
    1. sys.executable sudah pythonw.exe → pakai langsung.
    2. Cari pythonw.exe di direktori yang sama dengan sys.executable.
    3. Fallback ke sys.executable (python.exe) — console window muncul tapi tetap jalan.
    """
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        return exe  # sudah benar
    pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return exe  # fallback: python.exe

def _win_startup_approved_path():
    """Return path ke sub-key StartupApproved/Run di HKCU (Windows only)."""
    return r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"

def _win_build_cmd(script: str) -> str:
    """
    [B2-fix] Bangun command string untuk registry Run key.
    Kedua komponen (pythonw dan script) memakai path absolut dan di-quote.
    [APP-1-fix] Tambah --startup agar app tahu ini diluncurkan otomatis,
    bukan klik manual — sehingga start_minimized hanya berlaku saat startup.
    """
    if script.endswith((".py", ".pyw")):
        pythonw = _get_pythonw_path()
        return f'"{pythonw}" "{script}" --startup'
    return f'"{script}" --startup'

def set_run_at_startup(enable: bool) -> bool:
    """
    Daftarkan/hapus app dari startup OS. Return True jika berhasil.

    Windows -- menulis ke DUA key:
      1. HKCU/.../Run                 : command yang dijalankan
      2. HKCU/.../StartupApproved/Run : flag enabled/disabled (dibaca Task Manager)
         [B1-fix] Tanpa ini, user bisa disable via Task Manager dan kode kita
         tidak akan pernah mengetahuinya (Run key tetap ada tapi app tidak jalan).
    """
    app_name = "ScreenWatermarkPro"
    script   = _get_startup_script_path()
    try:
        if sys.platform == "win32":
            import winreg
            run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            if enable:
                cmd = _win_build_cmd(script)
                # 1. Tulis ke Run key
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path,
                                    0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                # 2. Tulis ke StartupApproved\Run — 12 byte, byte[0]=0x02 = enabled
                #    Pakai CreateKey agar bisa buat sub-key jika belum ada.
                sa_path = _win_startup_approved_path()
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sa_path) as sa_key:
                    approved = bytes([0x02, 0x00, 0x00, 0x00,
                                      0x00, 0x00, 0x00, 0x00,
                                      0x00, 0x00, 0x00, 0x00])
                    winreg.SetValueEx(sa_key, app_name, 0, winreg.REG_BINARY, approved)
                # [GC3-LOG] Log registry write agar QA bisa verify tanpa buka regedit
                print(f"[Startup] SET registry OK", file=sys.stderr)
                print(f"[Startup]   Key  : HKCU\\{run_path}\\{app_name}", file=sys.stderr)
                print(f"[Startup]   Cmd  : {cmd}", file=sys.stderr)
                print(f"[Startup]   SA   : HKCU\\{sa_path}\\{app_name} = 0x02 (enabled)",
                      file=sys.stderr)
            else:
                # 1. Hapus dari Run key
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path,
                                    0, winreg.KEY_SET_VALUE) as key:
                    try: winreg.DeleteValue(key, app_name)
                    except FileNotFoundError: pass
                # 2. Hapus dari StartupApproved\Run
                sa_path = _win_startup_approved_path()
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sa_path,
                                        0, winreg.KEY_SET_VALUE) as sa_key:
                        try: winreg.DeleteValue(sa_key, app_name)
                        except FileNotFoundError: pass
                except FileNotFoundError:
                    pass  # key StartupApproved\Run belum ada — tidak apa-apa
                # [GC3-LOG] Log registry delete
                print(f"[Startup] DELETE registry OK", file=sys.stderr)
                print(f"[Startup]   Dihapus dari HKCU\\{run_path}\\{app_name}",
                      file=sys.stderr)
            return True

        elif sys.platform == "darwin":
            plist_dir  = Path.home() / "Library" / "LaunchAgents"
            plist_file = plist_dir / f"com.screenwatermark.{app_name}.plist"
            plist_dir.mkdir(parents=True, exist_ok=True)
            if enable:
                cmd = [sys.executable, script, "--startup"] if script.endswith(".py") else [script, "--startup"]
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.screenwatermark.{app_name}</string>
  <key>ProgramArguments</key><array>
    {"".join(f"<string>{c}</string>" for c in cmd)}
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>"""
                plist_file.write_text(plist_content, encoding="utf-8")
            else:
                plist_file.unlink(missing_ok=True)
            return True

        else:  # Linux XDG autostart
            autostart_dir  = Path.home() / ".config" / "autostart"
            desktop_file   = autostart_dir / f"{app_name}.desktop"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            if enable:
                # [B7-fix] Quote path agar spasi di nama user/direktori tidak memecah argumen.
                # Freedesktop spec mengizinkan double-quote di field Exec=.
                if script.endswith((".py", ".pyw")):
                    exec_line = f'"{sys.executable}" "{script}"'
                else:
                    exec_line = f'"{script}"'
                # [S21-fix] Freedesktop spec: karakter '%' di Exec= adalah prefix
                # field codes (%u, %f, dll). Literal '%' harus di-escape ke '%%'.
                exec_line = exec_line.replace("%", "%%")
                # [APP-1-fix] Tambah --startup agar app tahu ini auto-launch
                exec_line = exec_line.rstrip() + " --startup"
                desktop_file.write_text(
                    f"[Desktop Entry]\nType=Application\nName={app_name}\n"
                    f"Exec={exec_line}\nHidden=false\nNoDisplay=false\n"
                    f"X-GNOME-Autostart-enabled=true\n",
                    encoding="utf-8")
            else:
                desktop_file.unlink(missing_ok=True)
            return True

    except Exception as exc:
        print(f"[Startup] Gagal: {exc}", file=sys.stderr)
        return False

def get_run_at_startup() -> bool:
    """
    Cek apakah app sudah terdaftar DAN diaktifkan di startup OS.

    Windows — cek TIGA hal:
      1. Nama ada di Run key.
      2. Path script di value masih cocok dengan lokasi script saat ini [B5-fix].
      3. StartupApproved/Run: tidak ada entry = dianggap enabled;
         ada entry dengan byte[0] != 0x02 = disabled oleh Task Manager [B1-fix].
    """
    app_name = "ScreenWatermarkPro"
    script   = _get_startup_script_path()
    try:
        if sys.platform == "win32":
            import winreg
            run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            # 1. Cek Run key — ambil value sekaligus
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path) as key:
                    val, _ = winreg.QueryValueEx(key, app_name)
            except FileNotFoundError:
                return False  # belum terdaftar sama sekali

            # 2. [B5-fix] Verifikasi path script saat ini ada di dalam value
            #    Bandingkan case-insensitive (Windows path case-insensitive)
            if script.lower() not in val.lower():
                # [GC3-LOG] Log stale path agar QA tahu kenapa status "belum terdaftar"
                print(f"[Startup] GET: stale entry — path saat ini tidak cocok.",
                      file=sys.stderr)
                print(f"[Startup]   Registry : {val}", file=sys.stderr)
                print(f"[Startup]   Script   : {script}", file=sys.stderr)
                return False  # stale entry dari path lama

            # 3. [B1-fix] Cek StartupApproved\Run
            #    Jika key/entry tidak ada → Windows anggap enabled → return True
            #    Jika ada → byte[0] harus 0x02 (enabled)
            sa_path = _win_startup_approved_path()
            _sa_status = "tidak ada (default=enabled)"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sa_path) as sa_key:
                    try:
                        sa_val, _ = winreg.QueryValueEx(sa_key, app_name)
                        # sa_val adalah bytes — byte pertama menentukan status
                        if isinstance(sa_val, (bytes, bytearray)) and len(sa_val) > 0:
                            _sa_status = f"0x{sa_val[0]:02x}"
                            if sa_val[0] != 0x02:
                                # [GC3-LOG] Task Manager menonaktifkan startup
                                print(f"[Startup] GET: disabled oleh Task Manager "
                                      f"(SA byte[0]={_sa_status})", file=sys.stderr)
                                return False  # disabled oleh Task Manager
                    except FileNotFoundError:
                        pass  # entry tidak ada = enabled by default
            except FileNotFoundError:
                pass  # key StartupApproved\Run tidak ada = enabled by default

            # [GC3-LOG] Log hasil akhir GET — aman terdaftar dan aktif
            print(f"[Startup] GET: terdaftar=True, path_valid=True, "
                  f"approved={_sa_status}", file=sys.stderr)
            print(f"[Startup]   Cmd: {val}", file=sys.stderr)
            return True

        elif sys.platform == "darwin":
            plist_file = (Path.home() / "Library" / "LaunchAgents" /
                          f"com.screenwatermark.{app_name}.plist")
            return plist_file.exists()
        else:
            desktop_file = (Path.home() / ".config" / "autostart" /
                            f"{app_name}.desktop")
            return desktop_file.exists()
    except Exception:
        return False


