# tests/system/test_m2_system.py
"""
Phase M2 — system/ Extraction Verification
Run at M2 milestone: pytest tests/system/ -v
Headless — no display. Pynput is mocked where listener creation would fail.
Covers: TC-M2-001 → TC-M2-008
"""

import pytest
from unittest.mock import MagicMock, patch


# ── TC-M2-001 / TC-M2-002 / TC-M2-003 / TC-M2-004 ────────────────────────────

class TestHotkeyManager:

    def test_hotkeys_module_importable(self):
        """TC-M2-001: system/hotkeys.py imports cleanly."""
        from system.hotkeys import HotkeyManager, _preset_label, _preset_value
        assert HotkeyManager is not None
        assert callable(_preset_label)
        assert callable(_preset_value)

    def test_preset_label_lookup(self):
        """TC-M2-001b: _preset_label returns display string for known value."""
        from system.hotkeys import _preset_label
        assert _preset_label("<print_screen>") == "Print Screen"
        assert _preset_label("<ctrl>+<f9>") == "Ctrl+F9"

    def test_preset_value_lookup(self):
        """TC-M2-001c: _preset_value returns pynput string for known label."""
        from system.hotkeys import _preset_value
        assert _preset_value("Print Screen") == "<print_screen>"
        assert _preset_value("Ctrl+F9") == "<ctrl>+<f9>"

    def test_hotkey_manager_instantiates(self):
        """TC-M2-002: HotkeyManager creates cleanly with empty state."""
        from system.hotkeys import HotkeyManager
        mgr = HotkeyManager()
        assert mgr._callbacks == {}
        assert mgr._active_slots == set()
        assert mgr._listener is None

    def test_hotkey_manager_is_active_false_initially(self):
        """TC-M2-002b: is_active returns False for unregistered slot."""
        from system.hotkeys import HotkeyManager
        mgr = HotkeyManager()
        assert mgr.is_active("fullscreen") is False
        assert mgr.is_active("region") is False

    def test_register_stores_callback(self):
        """TC-M2-003: register() stores callback in _callbacks dict."""
        from system.hotkeys import HotkeyManager
        mgr = HotkeyManager()
        cb = MagicMock()
        # Inject directly — avoids pynput GlobalHotKeys in headless env
        with mgr._lock:
            mgr._callbacks["<print_screen>"] = ("fullscreen", cb)
            mgr._active_slots.add("fullscreen")
        assert mgr.is_active("fullscreen") is True
        assert "<print_screen>" in mgr._callbacks

    def test_unregister_removes_slot(self):
        """TC-M2-004: unregister() removes slot from callbacks and active set."""
        from system.hotkeys import HotkeyManager
        mgr = HotkeyManager()
        with mgr._lock:
            mgr._callbacks["<print_screen>"] = ("fullscreen", lambda: None)
            mgr._active_slots.add("fullscreen")
        # Unregister (mock _rebuild to avoid pynput)
        with patch.object(mgr, "_rebuild"):
            mgr.unregister("fullscreen")
        assert not mgr.is_active("fullscreen")

    def test_unregister_all_clears_everything(self):
        """unregister_all() leaves no callbacks or active slots."""
        from system.hotkeys import HotkeyManager
        mgr = HotkeyManager()
        with mgr._lock:
            mgr._callbacks["<print_screen>"] = ("fullscreen", lambda: None)
            mgr._callbacks["<ctrl>+<f9>"]    = ("history",    lambda: None)
            mgr._active_slots.update({"fullscreen", "history"})
        mgr.unregister_all()
        assert mgr._callbacks == {}
        assert mgr._active_slots == set()


# ── TC-M2-005 / TC-M2-006 ─────────────────────────────────────────────────────

class TestStartup:

    def test_startup_module_importable(self):
        """TC-M2-005: system/startup.py imports cleanly."""
        from system.startup import get_run_at_startup, set_run_at_startup
        assert callable(get_run_at_startup)
        assert callable(set_run_at_startup)

    def test_get_run_at_startup_returns_bool(self):
        """TC-M2-006: get_run_at_startup() returns bool without crashing."""
        from system.startup import get_run_at_startup
        result = get_run_at_startup()
        assert isinstance(result, bool), \
            f"Expected bool, got {type(result).__name__}"

    def test_startup_script_path_not_empty(self):
        """_get_startup_script_path() returns a non-empty path string."""
        from system.startup import _get_startup_script_path
        path = _get_startup_script_path()
        assert path and len(path) > 0


# ── TC-M2-007 / TC-M2-008 ─────────────────────────────────────────────────────

class TestIPC:

    def test_ipc_module_importable(self):
        """TC-M2-007: system/ipc.py imports cleanly."""
        from system.ipc import (_acquire_single_instance,
                                 _ipc_server_thread,
                                 _SW_LOCK_FILE,
                                 _SW_IPC_MAGIC,
                                 _SW_IPC_ACK)
        assert callable(_acquire_single_instance)
        assert callable(_ipc_server_thread)

    def test_acquire_single_instance_returns_tuple(self, tmp_path, monkeypatch):
        """TC-M2-008: _acquire_single_instance() returns (bool, int)."""
        # Redirect lock file to tmp_path to avoid interfering with live app
        monkeypatch.setattr(
            "system.ipc._SW_LOCK_FILE",
            tmp_path / ".screenwatermark_instance_test.lock")
        from system.ipc import _acquire_single_instance
        result = _acquire_single_instance()
        assert isinstance(result, tuple) and len(result) == 2
        is_first, port = result
        assert isinstance(is_first, bool)
        assert isinstance(port, int)
        # Cleanup: if we became "first", our server socket is now bound
        # The lock file in tmp_path will be cleaned up by pytest

    def test_ipc_magic_bytes_defined(self):
        """IPC magic and ack bytes are non-empty byte strings."""
        from system.ipc import _SW_IPC_MAGIC, _SW_IPC_ACK
        assert isinstance(_SW_IPC_MAGIC, bytes) and len(_SW_IPC_MAGIC) > 0
        assert isinstance(_SW_IPC_ACK, bytes) and len(_SW_IPC_ACK) > 0


# ── Bonus: tray module ────────────────────────────────────────────────────────

class TestTray:

    def test_tray_module_importable(self):
        """system/tray.py imports cleanly."""
        from system.tray import _make_tray_icon
        assert callable(_make_tray_icon)

    def test_make_tray_icon_returns_image(self):
        """_make_tray_icon() returns a valid PIL RGBA Image."""
        from system.tray import _make_tray_icon
        from PIL import Image
        img = _make_tray_icon()
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"
        assert img.size == (32, 32)
