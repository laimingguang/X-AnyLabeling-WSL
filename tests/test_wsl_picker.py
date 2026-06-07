import importlib.util
import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _load_wsl_module():
    """Load wsl.py directly without triggering anylabeling package init."""
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
is_user_distro = _wsl_mod.is_user_distro
list_directory_entries = _wsl_mod.list_directory_entries


class TestWslDistroFilter(unittest.TestCase):
    """Filtering logic: user distros vs docker internals."""

    def test_ubuntu_with_home(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=["zsw"]),
        ):
            self.assertTrue(
                is_user_distro(r"\\wsl.localhost\Ubuntu", "Ubuntu")
            )

    def test_docker_desktop_empty_home(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=[]),
        ):
            self.assertFalse(
                is_user_distro(
                    r"\\wsl.localhost\docker-desktop", "docker-desktop"
                )
            )

    def test_alpine_root_only_allowed(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=[]),
        ):
            self.assertTrue(
                is_user_distro(r"\\wsl.localhost\Alpine", "Alpine")
            )

    def test_docker_desktop_data_with_home(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=["data"]),
        ):
            # Non-empty /home overrides docker name check
            self.assertTrue(
                is_user_distro(
                    r"\\wsl.localhost\docker-desktop-data",
                    "docker-desktop-data",
                )
            )

    def test_debian_with_home(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=["user"]),
        ):
            self.assertTrue(
                is_user_distro(r"\\wsl.localhost\Debian", "Debian")
            )

    def test_kali_with_home(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=["kali"]),
        ):
            self.assertTrue(
                is_user_distro(r"\\wsl.localhost\kali-linux", "kali-linux")
            )

    def test_nonexistent_path(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=False),
        ):
            # Non-docker name → falls through as allowed; caller filters
            self.assertTrue(
                is_user_distro(
                    r"\\wsl.localhost\NonExistent", "NonExistent"
                )
            )

    def test_name_filter_applies_when_home_empty(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=True),
            patch.object(_wsl_mod.os, "listdir", return_value=[]),
        ):
            self.assertFalse(
                is_user_distro(
                    r"\\wsl.localhost\docker-desktop", "docker-desktop"
                )
            )

    def test_name_filter_allows_non_docker_when_home_empty(self):
        with (
            patch.object(_wsl_mod.osp, "isdir", return_value=False),
        ):
            self.assertTrue(
                is_user_distro(r"\\wsl.localhost\Alpine", "Alpine")
            )


class TestListDirectoryEntries(unittest.TestCase):
    """Directory listing with OSError handling."""

    def test_returns_sorted_subdirectories(self):
        with (
            patch.object(_wsl_mod.os, "listdir", return_value=["b", "a", "c"]),
            patch.object(_wsl_mod.osp, "isdir", side_effect=lambda p: True),
        ):
            result = list_directory_entries(r"\\wsl.localhost\Ubuntu\home")
        self.assertEqual(result, ["a", "b", "c"])

    def test_filters_out_files(self):
        with (
            patch.object(_wsl_mod.os, "listdir", return_value=["file.txt", "subdir", "notes.md"]),
            patch.object(_wsl_mod.osp, "isdir", side_effect=lambda p: p.endswith("subdir")),
        ):
            result = list_directory_entries(r"\\wsl.localhost\Ubuntu\home")
        self.assertEqual(result, ["subdir"])

    def test_empty_directory(self):
        with (
            patch.object(_wsl_mod.os, "listdir", return_value=[]),
        ):
            result = list_directory_entries(r"\\wsl.localhost\Ubuntu\home")
        self.assertEqual(result, [])

    def test_returns_none_on_oserror(self):
        with (
            patch.object(_wsl_mod.os, "listdir", side_effect=OSError(5, "Access denied")),
        ):
            result = list_directory_entries(r"\\wsl.localhost\docker-desktop")
        self.assertIsNone(result)


class TestWslNameExtraction(unittest.TestCase):
    """Basename extraction used instead of osp.basename on Windows UNC."""

    @staticmethod
    def _extract_name(path):
        return path.rstrip("\\").split("\\")[-1]

    def test_ubuntu(self):
        self.assertEqual(
            self._extract_name(r"\\wsl.localhost\Ubuntu"), "Ubuntu"
        )

    def test_docker_desktop(self):
        self.assertEqual(
            self._extract_name(r"\\wsl.localhost\docker-desktop"),
            "docker-desktop",
        )

    def test_nested_path(self):
        self.assertEqual(
            self._extract_name(r"\\wsl.localhost\Ubuntu\home\zsw"),
            "zsw",
        )

    def test_root_with_trailing_slash(self):
        self.assertEqual(
            self._extract_name(r"\\wsl.localhost\Ubuntu\\"), "Ubuntu"
        )


# --- Qt integration tests ---

try:
    from PyQt6 import QtWidgets

    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False


@unittest.skipUnless(
    PYQT_AVAILABLE, "PyQt6 required for WSL picker dialog tests"
)
class TestWslDirectoryPickerBuildTree(unittest.TestCase):

    def setUp(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def test_build_tree_filters_docker(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        distro_paths = [
            r"\\wsl.localhost\Ubuntu",
            r"\\wsl.localhost\docker-desktop",
        ]
        parent = QtWidgets.QWidget()
        with patch.object(
            WslDirectoryPicker,
            "_is_user_distro",
            side_effect=lambda p, n: "docker" not in n,
        ):
            picker = WslDirectoryPicker(distro_paths, parent)
        top_items = [
            picker._tree.topLevelItem(i)
            for i in range(picker._tree.topLevelItemCount())
        ]
        names = [item.text(0) for item in top_items]
        self.assertEqual(names, ["Ubuntu"])

    def test_build_tree_empty_home_still_shows_if_not_docker(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        distro_paths = [r"\\wsl.localhost\Alpine"]
        parent = QtWidgets.QWidget()
        with (
            patch.object(
                WslDirectoryPicker,
                "_is_user_distro",
                return_value=True,
            ),
            patch(
                "anylabeling.views.labeling.label_widget.osp.isdir",
                return_value=True,
            ),
        ):
            picker = WslDirectoryPicker(distro_paths, parent)
        self.assertEqual(picker._tree.topLevelItemCount(), 1)
        self.assertEqual(
            picker._tree.topLevelItem(0).text(0), "Alpine"
        )

    def test_build_tree_skips_missing_paths(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        distro_paths = [
            r"\\wsl.localhost\Ubuntu",
            r"\\wsl.localhost\NonExistent",
        ]
        parent = QtWidgets.QWidget()
        with (
            patch.object(
                WslDirectoryPicker,
                "_is_user_distro",
                return_value=True,
            ),
            patch(
                "anylabeling.views.labeling.label_widget.osp.isdir",
                side_effect=lambda p: "NonExistent" not in p,
            ),
        ):
            picker = WslDirectoryPicker(distro_paths, parent)
        self.assertEqual(picker._tree.topLevelItemCount(), 1)
        self.assertEqual(
            picker._tree.topLevelItem(0).text(0), "Ubuntu"
        )


@unittest.skipUnless(
    PYQT_AVAILABLE, "PyQt6 required for WSL picker dialog tests"
)
class TestWslDirectoryPickerGetDirectory(unittest.TestCase):

    def setUp(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def test_get_directory_returns_none_on_reject(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        distro_paths = [r"\\wsl.localhost\Ubuntu"]
        with (
            patch.object(
                WslDirectoryPicker,
                "_is_user_distro",
                return_value=True,
            ),
            patch(
                "anylabeling.views.labeling.label_widget.osp.isdir",
                return_value=True,
            ),
            patch.object(
                WslDirectoryPicker,
                "exec",
                return_value=QtWidgets.QDialog.DialogCode.Rejected,
            ),
        ):
            result = WslDirectoryPicker.get_directory(distro_paths)
        self.assertIsNone(result)

    def test_on_current_changed_sets_path_and_enables_button(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        distro_paths = [r"\\wsl.localhost\Ubuntu"]
        with (
            patch.object(
                WslDirectoryPicker, "_is_user_distro", return_value=True
            ),
            patch(
                "anylabeling.views.labeling.label_widget.osp.isdir",
                return_value=True,
            ),
        ):
            picker = WslDirectoryPicker(distro_paths)
        item = picker._tree.topLevelItem(0)
        picker._on_current_changed(item, None)
        self.assertEqual(
            picker._selected_path, r"\\wsl.localhost\Ubuntu"
        )
        self.assertTrue(picker._select_btn.isEnabled())
