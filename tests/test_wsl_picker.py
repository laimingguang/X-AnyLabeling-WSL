import ctypes
import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QWidget

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False


def _load_wsl_module():
    wsl_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "anylabeling",
        "views",
        "labeling",
        "utils",
        "wsl.py",
    )
    spec = importlib.util.spec_from_file_location(
        "anylabeling.views.labeling.utils.wsl", wsl_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_wsl_mod = _load_wsl_module()
pick_folder = _wsl_mod.pick_folder
get_existing_directory = _wsl_mod.get_existing_directory


class TestPickFolderNonWindows(unittest.TestCase):
    """pick_folder on non-Windows returns None without calling COM."""

    def test_returns_none_on_posix(self):
        with patch.object(_wsl_mod.os, "name", "posix"):
            result = pick_folder("title", 0)
        self.assertIsNone(result)

    def test_returns_none_on_macos(self):
        with patch.object(_wsl_mod.os, "name", "mac"):
            result = pick_folder("title", 0)
        self.assertIsNone(result)

    def test_skips_com_on_non_windows(self):
        with (
            patch.object(_wsl_mod.os, "name", "posix"),
            patch("ctypes.windll.ole32") as mock_ole32,
        ):
            pick_folder("title", 0)
            mock_ole32.CoCreateInstance.assert_not_called()

    def test_returns_none_on_other_platforms(self):
        for name in ("linux", "cygwin", "java"):
            with patch.object(_wsl_mod.os, "name", name):
                result = pick_folder("title", 0)
            self.assertIsNone(result)


class TestPickFolderComFailure(unittest.TestCase):
    """CoCreateInstance failure returns None without crashing."""

    def test_cocreate_failure_returns_none(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(
                ctypes.windll.ole32, "CoCreateInstance", return_value=0x80004005
            ),
        ):
            result = pick_folder("title", 0)
        self.assertIsNone(result)

    def test_isdir_not_called_on_cocreate_failure(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(
                ctypes.windll.ole32, "CoCreateInstance", return_value=0x80004005
            ),
            patch.object(_wsl_mod.os.path, "isdir") as mock_isdir,
        ):
            pick_folder("title", 0, "/some/dir")
            mock_isdir.assert_not_called()


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt6 required")
class TestGetExistingDirectory(unittest.TestCase):
    """get_existing_directory behavior independent of pick_folder internals."""

    def test_windows_returns_path_from_pick_folder(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/some/path"),
        ):
            result = get_existing_directory(caption="Test")
        self.assertEqual(result, "/some/path")

    def test_windows_returns_empty_on_cancel(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value=None),
        ):
            result = get_existing_directory(caption="Test")
        self.assertEqual(result, "")

    def test_windows_no_qt_fallback_on_cancel(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value=None),
            patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory") as mock_qf,
        ):
            get_existing_directory(caption="Test")
            mock_qf.assert_not_called()

    def test_qwidget_parent_extracts_winid(self):
        parent = MagicMock(spec=QWidget)
        parent.winId.return_value = 98765
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/path") as mock_pf,
        ):
            result = get_existing_directory(parent=parent, caption="Test")
        self.assertEqual(result, "/path")
        mock_pf.assert_called_once_with("Test", 98765, "")

    def test_qwidget_parent_int_winid_handled(self):
        parent = MagicMock(spec=QWidget)
        parent.winId.return_value = 0
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/path") as mock_pf,
        ):
            get_existing_directory(parent=parent, caption="Test")
            mock_pf.assert_called_once_with("Test", 0, "")

    def test_no_parent_uses_zero_hwnd(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(caption="Test")
            mock_pf.assert_called_once_with("Test", 0, "")

    def test_none_parent_uses_zero_hwnd(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(parent=None, caption="Test")
            mock_pf.assert_called_once_with("Test", 0, "")

    def test_non_qwidget_parent_uses_zero_hwnd(self):
        for parent in (42, "string", 3.14, [], {}):
            with (
                patch.object(_wsl_mod.os, "name", "nt"),
                patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
            ):
                get_existing_directory(parent=parent, caption="Test")
                mock_pf.assert_called_with("Test", 0, "")

    def test_start_dir_forwarded_to_pick_folder(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(caption="Test", directory="/start/path")
            mock_pf.assert_called_once_with("Test", 0, "/start/path")

    def test_empty_start_dir_forwarded_to_pick_folder(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(caption="Test", directory="")
            mock_pf.assert_called_once_with("Test", 0, "")

    def test_empty_caption_uses_default(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(caption="")
            caption_arg = mock_pf.call_args[0][0]
            self.assertEqual(caption_arg, "Select Folder")

    def test_caption_forwarded_to_pick_folder(self):
        with (
            patch.object(_wsl_mod.os, "name", "nt"),
            patch.object(_wsl_mod, "pick_folder", return_value="/p") as mock_pf,
        ):
            get_existing_directory(caption="My Custom Title")
            mock_pf.assert_called_once_with("My Custom Title", 0, "")

    def test_non_windows_delegates_to_qt(self):
        with (
            patch.object(_wsl_mod.os, "name", "posix"),
            patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory") as mock_qf,
        ):
            mock_qf.return_value = "/qt/fallback"
            result = get_existing_directory(
                caption="Test", directory="/start"
            )
        self.assertEqual(result, "/qt/fallback")
        mock_qf.assert_called_once()

    def test_non_windows_passes_options_to_qt(self):
        with (
            patch.object(_wsl_mod.os, "name", "posix"),
            patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory") as mock_qf,
        ):
            mock_qf.return_value = "/qt/path"
            get_existing_directory(
                caption="Test",
                directory="/dir",
                options=0x00000040,
            )
            args, kwargs = mock_qf.call_args
            self.assertEqual(args, (None, "Test", "/dir", 0x00000040))
            self.assertEqual(kwargs, {})


@unittest.skipUnless(os.name == "nt", "requires Windows COM")
class TestPickFolderIntegration(unittest.TestCase):
    """Real COM integration: dialog opens and user interacts."""

    def test_pick_folder_returns_string_on_success(self):
        result = pick_folder("Test: select any folder", 0)
        if result is not None:
            self.assertIsInstance(result, str)
            self.assertTrue(os.path.isdir(result))

    def test_pick_folder_returns_none_on_cancel(self):
        result = pick_folder("Test: press Cancel", 0)
        self.assertIsNone(result)


class TestNoStaleCalls(unittest.TestCase):
    """Verify all getExistingDirectory calls have been replaced."""

    def test_no_qfiledialog_getexistingdirectory(self):
        src_dir = os.path.join(os.path.dirname(__file__), "..", "anylabeling")
        stale = []
        for root, _dirs, files in os.walk(src_dir):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                if path.endswith("utils\\wsl.py") or path.endswith("utils/wsl.py"):
                    continue
                with open(path, encoding="utf-8") as fh:
                    for lineno, line in enumerate(fh, 1):
                        if "QFileDialog.getExistingDirectory(" in line:
                            stale.append(f"{path}:{lineno}")
        self.assertEqual(stale, [], f"Stale QFileDialog.getExistingDirectory calls:\n" + "\n".join(stale))


if __name__ == "__main__":
    unittest.main()
