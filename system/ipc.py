"""
ScreenWatermark Pro - System IPC Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import socket as _socket
import threading
from pathlib import Path
import socket as _socket

_SW_IPC_SERVER = None   # server socket instance pertama (simpan agar tidak di-GC)
_SW_LOCK_FILE  = Path.home() / ".screenwatermark_instance.lock"
_SW_IPC_MAGIC  = b"SW_SHOW_WINDOW\n"  # instance kedua → pertama: "tampilkan window"
_SW_IPC_ACK    = b"SW_ACK\n"           # instance pertama → kedua: "saya app yang benar"


# Flag: koneksi SHOW datang saat app belum siap (app_ref masih kosong).
# Diset oleh server thread, dicek oleh main thread setelah _app_ref.append(app).
_ipc_pending_show = threading.Event()

def _ipc_server_thread(server_sock: "_socket.socket", app_ref: list):
    """
    Daemon thread: listen koneksi masuk dari instance kedua.
    app_ref adalah list satu elemen [app] — diisi setelah ScreenWatermarkApp dibuat.
    Pakai list karena Python closure tidak bisa re-assign variabel outer scope.

    Race condition ditangani via _ipc_pending_show:
    Jika koneksi SHOW datang sebelum app_ref diisi (selama __init__),
    set _ipc_pending_show. Main thread mengecek flag ini setelah app siap
    dan memanggil _show_window jika flag aktif.
    """
    server_sock.settimeout(1.0)   # timeout agar thread bisa cek _is_quitting
    while True:
        try:
            conn, _ = server_sock.accept()
        except _socket.timeout:
            # Cek apakah app sudah quit — jika ya, hentikan thread
            if app_ref and app_ref[0] and getattr(app_ref[0], "_is_quitting", False):
                break
            continue
        except Exception:
            break
        try:
            data = conn.recv(64)
            if data == _SW_IPC_MAGIC:
                # Balas ACK dulu — ini membuktikan ke instance kedua bahwa
                # port ini benar-benar dipegang oleh app yang sama, bukan
                # proses lain yang kebetulan menempati port tersebut.
                try: conn.sendall(_SW_IPC_ACK)
                except Exception: pass
                app = app_ref[0] if app_ref else None
                if app and not getattr(app, "_is_quitting", True):
                    # App sudah siap — langsung show di main thread
                    app.after(0, app._show_window)
                else:
                    # App belum siap (masih __init__) — set pending flag
                    # Main thread akan flush ini setelah app_ref diisi
                    _ipc_pending_show.set()
        except Exception:
            pass
        finally:
            try: conn.close()
            except: pass


def _acquire_single_instance() -> "tuple[bool, int]":
    """
    Coba jadi instance pertama via IPC socket.
    Return (True, port)  → kita adalah instance pertama, server sudah running.
    Return (False, port) → instance lain sudah berjalan di port ini,
                           pemanggil harus kirim SHOW lalu exit.
    """
    global _SW_IPC_SERVER

    # Baca port dari lock file (mungkin milik instance lama)
    saved_port = 0
    try:
        txt = _SW_LOCK_FILE.read_text(encoding="ascii").strip()
        saved_port = int(txt)
    except Exception:
        saved_port = 0

    # Coba connect ke instance yang mungkin sudah ada
    if saved_port > 0:
        try:
            probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            probe.settimeout(0.5)
            probe.connect(("127.0.0.1", saved_port))
            # Berhasil connect — kirim MAGIC dan tunggu ACK.
            # ACK membuktikan bahwa proses di ujung sana memang app yang sama,
            # bukan proses lain yang kebetulan menempati port tersebut.
            try:
                probe.sendall(_SW_IPC_MAGIC)
                probe.settimeout(1.0)
                ack = probe.recv(16)
                if ack == _SW_IPC_ACK:
                    # Konfirmasi: ini benar-benar instance app yang sedang jalan
                    return False, saved_port
                # Tidak ada ACK atau ACK salah → proses lain di port ini
                # → anggap tidak ada instance, lanjut sebagai instance pertama
            except Exception:
                pass
            finally:
                probe.close()
            # ACK tidak diterima → port bukan milik app → hapus lock file stale
            try: _SW_LOCK_FILE.unlink(missing_ok=True)
            except Exception: pass
            saved_port = 0
        except (_socket.timeout, ConnectionRefusedError, OSError):
            # Tidak bisa connect → port milik proses lama yang sudah mati
            saved_port = 0

    # Tidak ada instance lain — buat server socket kita sendiri
    try:
        srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))   # port 0 = OS pilih port bebas yang available
        srv.listen(4)
        port = srv.getsockname()[1]
        # Simpan port ke lock file agar instance berikutnya bisa connect
        try:
            _SW_LOCK_FILE.write_text(str(port), encoding="ascii")
        except Exception:
            pass
        _SW_IPC_SERVER = srv   # simpan agar tidak di-GC
        return True, port
    except Exception:
        return True, 0   # fail-open: jika tidak bisa bind, izinkan jalan


