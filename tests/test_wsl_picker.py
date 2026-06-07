import importlib.util
import os
import sys
import unittest
from subprocess import TimeoutExpired
from unittest.mock import MagicMock, patch

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
get_wsl2_distro_paths = _wsl_mod.get_wsl2_distro_paths


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


class TestGetWsl2DistroPaths(unittest.TestCase):
    """WSL2 distro detection via wsl -l -v."""

    def _mock_output(self, text):
        mock = MagicMock()
        mock.stdout = text.encode("utf-16-le")
        return mock

    def test_returns_wsl2_paths(self):
        text = (
            "  NAME                   STATE           VERSION\n"
            "* Ubuntu                 Running         2\n"
            "  docker-desktop         Running         2\n"
        )
        with patch.object(
            _wsl_mod.subprocess, "run", return_value=self._mock_output(text)
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(
            paths,
            [
                r"\\wsl.localhost\Ubuntu",
                r"\\wsl.localhost\docker-desktop",
            ],
        )

    def test_filters_wsl1(self):
        text = (
            "  NAME                   STATE           VERSION\n"
            "  Ubuntu-18.04           Stopped         1\n"
            "  Ubuntu                 Running         2\n"
        )
        with patch.object(
            _wsl_mod.subprocess, "run", return_value=self._mock_output(text)
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [r"\\wsl.localhost\Ubuntu"])

    def test_filters_all_wsl1_returns_empty(self):
        text = (
            "  NAME                   STATE           VERSION\n"
            "  Ubuntu-18.04           Stopped         1\n"
        )
        with patch.object(
            _wsl_mod.subprocess, "run", return_value=self._mock_output(text)
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])

    def test_empty_output_returns_empty(self):
        with patch.object(
            _wsl_mod.subprocess, "run", return_value=self._mock_output("")
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])

    def test_whitespace_output_returns_empty(self):
        with patch.object(
            _wsl_mod.subprocess,
            "run",
            return_value=self._mock_output(" \t\n "),
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])

    def test_subprocess_error_returns_empty(self):
        with patch.object(
            _wsl_mod.subprocess,
            "run",
            side_effect=OSError(2, "No such file"),
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])

    def test_file_not_found_returns_empty(self):
        with patch.object(
            _wsl_mod.subprocess,
            "run",
            side_effect=FileNotFoundError(),
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])

    def test_timeout_returns_empty(self):
        with patch.object(
            _wsl_mod.subprocess,
            "run",
            side_effect=TimeoutExpired("wsl", 5),
        ):
            paths = get_wsl2_distro_paths()
        self.assertEqual(paths, [])


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


# --- WSL folder open orchestration (non-Qt scenarios) ---


class TestTryWslFolderOpen(unittest.TestCase):
    """_try_wsl_folder_open scenarios that don't need QMessageBox."""

    def test_not_windows(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        with patch(
            "anylabeling.views.labeling.label_widget.os.name", "posix"
        ):
            result = _try_wsl_folder_open(None, None)
        self.assertFalse(result)

    def test_no_distros_returns_false(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        with (
            patch(
                "anylabeling.views.labeling.label_widget.os.name", "nt"
            ),
            patch(
                "anylabeling.views.labeling.label_widget.get_wsl2_distro_paths",
                return_value=[],
            ),
        ):
            result = _try_wsl_folder_open(None, None)
        self.assertFalse(result)


@unittest.skipUnless(
    PYQT_AVAILABLE, "PyQt6 required for WSL dialog flow tests"
)
class TestTryWslFolderOpenQt(unittest.TestCase):
    """_try_wsl_folder_open scenarios that exercise the QMessageBox branch."""

    def setUp(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def _make_msgbox(self, clicked_role):
        mock_msg = MagicMock()
        btn_win = MagicMock()
        btn_wsl = MagicMock()
        mock_msg.addButton.side_effect = [btn_win, btn_wsl]
        if clicked_role == "win":
            mock_msg.clickedButton.return_value = btn_win
        elif clicked_role == "wsl":
            mock_msg.clickedButton.return_value = btn_wsl
        else:
            mock_msg.clickedButton.return_value = None
        return mock_msg

    def test_x_button_returns_true_no_callback(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        callback = MagicMock()
        mock_msg = self._make_msgbox(None)
        with (
            patch(
                "anylabeling.views.labeling.label_widget.os.name", "nt"
            ),
            patch(
                "anylabeling.views.labeling.label_widget.get_wsl2_distro_paths",
                return_value=[r"\\wsl.localhost\Ubuntu"],
            ),
            patch(
                "anylabeling.views.labeling.label_widget.QMessageBox",
                return_value=mock_msg,
            ),
        ):
            result = _try_wsl_folder_open(None, callback)
        self.assertTrue(result)
        callback.assert_not_called()

    def test_wsl_button_selects_directory(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        callback = MagicMock()
        mock_msg = self._make_msgbox("wsl")
        with (
            patch(
                "anylabeling.views.labeling.label_widget.os.name", "nt"
            ),
            patch(
                "anylabeling.views.labeling.label_widget.get_wsl2_distro_paths",
                return_value=[r"\\wsl.localhost\Ubuntu"],
            ),
            patch(
                "anylabeling.views.labeling.label_widget.QMessageBox",
                return_value=mock_msg,
            ),
            patch(
                "anylabeling.views.labeling.label_widget.WslDirectoryPicker.get_directory",
                return_value=r"\\wsl.localhost\Ubuntu\home\zsw",
            ),
        ):
            result = _try_wsl_folder_open(None, callback)
        self.assertTrue(result)
        callback.assert_called_once_with(
            r"\\wsl.localhost\Ubuntu\home\zsw"
        )

    def test_wsl_button_cancels_picker_returns_true(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        callback = MagicMock()
        mock_msg = self._make_msgbox("wsl")
        with (
            patch(
                "anylabeling.views.labeling.label_widget.os.name", "nt"
            ),
            patch(
                "anylabeling.views.labeling.label_widget.get_wsl2_distro_paths",
                return_value=[r"\\wsl.localhost\Ubuntu"],
            ),
            patch(
                "anylabeling.views.labeling.label_widget.QMessageBox",
                return_value=mock_msg,
            ),
            patch(
                "anylabeling.views.labeling.label_widget.WslDirectoryPicker.get_directory",
                return_value=None,
            ),
        ):
            result = _try_wsl_folder_open(None, callback)
        self.assertTrue(result)
        callback.assert_not_called()

    def test_windows_button_falls_through(self):
        from anylabeling.views.labeling.label_widget import (
            _try_wsl_folder_open,
        )

        callback = MagicMock()
        mock_msg = self._make_msgbox("win")
        with (
            patch(
                "anylabeling.views.labeling.label_widget.os.name", "nt"
            ),
            patch(
                "anylabeling.views.labeling.label_widget.get_wsl2_distro_paths",
                return_value=[r"\\wsl.localhost\Ubuntu"],
            ),
            patch(
                "anylabeling.views.labeling.label_widget.QMessageBox",
                return_value=mock_msg,
            ),
        ):
            result = _try_wsl_folder_open(None, callback)
        self.assertFalse(result)
        callback.assert_not_called()


@unittest.skipUnless(
    PYQT_AVAILABLE, "PyQt6 required for WSL picker dialog tests"
)
class TestWslPathInput(unittest.TestCase):
    """Path input box and QSettings persist."""

    def setUp(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def test_on_path_entered_valid_dir(self):
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
            picker._path_edit.setText(
                r"\\wsl.localhost\Ubuntu\home\zsw\datasets"
            )
            picker._on_path_entered()

        self.assertEqual(
            picker._selected_path,
            r"\\wsl.localhost\Ubuntu\home\zsw\datasets",
        )
        self.assertTrue(picker._select_btn.isEnabled())

    def test_on_path_entered_invalid_dir_ignored(self):
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
                side_effect=lambda p: "NonExistent" not in p,
            ),
        ):
            picker = WslDirectoryPicker(distro_paths)
            picker._selected_path = None
            picker._select_btn.setEnabled(False)
            picker._path_edit.setText(
                r"\\wsl.localhost\Ubuntu\NonExistent"
            )
            picker._on_path_entered()

        self.assertIsNone(picker._selected_path)
        self.assertFalse(picker._select_btn.isEnabled())

    def test_save_last_path_stores_to_qsettings(self):
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
            patch(
                "anylabeling.views.labeling.label_widget.QtCore.QSettings"
            ) as mock_settings_cls,
        ):
            mock_settings_cls.return_value.value.return_value = ""
            picker = WslDirectoryPicker(distro_paths)
            mock_settings = mock_settings_cls.return_value
            picker._selected_path = (
                r"\\wsl.localhost\Ubuntu\home\zsw\datasets"
            )
            picker._save_last_path()
            mock_settings.setValue.assert_called_once_with(
                "last_directory",
                r"\\wsl.localhost\Ubuntu\home\zsw\datasets",
            )

    def test_restore_last_path_on_init(self):
        from anylabeling.views.labeling.label_widget import (
            WslDirectoryPicker,
        )

        # Use a mock QSettings that returns a saved path
        mock_settings = MagicMock()
        mock_settings.value.return_value = (
            r"\\wsl.localhost\Ubuntu\home\zsw"
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
            patch(
                "anylabeling.views.labeling.label_widget.QtCore.QSettings",
                return_value=mock_settings,
            ),
        ):
            picker = WslDirectoryPicker(distro_paths)

        self.assertEqual(
            picker._selected_path, r"\\wsl.localhost\Ubuntu\home\zsw"
        )
        self.assertEqual(
            picker._path_edit.text(), r"\\wsl.localhost\Ubuntu\home\zsw"
        )
        self.assertTrue(picker._select_btn.isEnabled())


@unittest.skipUnless(
    PYQT_AVAILABLE, "PyQt6 required for UltralyticsDialog tests"
)
class TestUltralyticsDialogWsl(unittest.TestCase):
    """browse_data_file WSL integration for Classification dataset."""

    def setUp(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication([])

    def _make_mock_dialog(self, task_type="Classify"):
        mock = MagicMock(spec=[])
        mock.selected_task_type = task_type
        mock.config_widgets = {"data": MagicMock()}
        mock._handle_wsl_data_dir = MagicMock()
        mock.tr = MagicMock(return_value="")
        return mock

    def _bind_browse(self, mock_dialog):
        from anylabeling.views.training.ultralytics_dialog import (
            UltralyticsDialog,
        )

        return UltralyticsDialog.browse_data_file.__get__(
            mock_dialog, UltralyticsDialog
        )

    def test_classify_try_wsl_first(self):
        """Classify: WSL returning True should skip QFileDialog."""
        mock = self._make_mock_dialog("Classify")
        browse = self._bind_browse(mock)
        with patch(
            "anylabeling.views.labeling.label_widget._try_wsl_folder_open",
            return_value=True,
        ) as mock_try:
            browse()

        mock_try.assert_called_once_with(
            mock, mock._handle_wsl_data_dir
        )
        mock.config_widgets["data"].setText.assert_not_called()

    def test_classify_falls_through_when_no_wsl(self):
        """Classify: WSL returning False should fall to QFileDialog."""
        mock = self._make_mock_dialog("Classify")
        browse = self._bind_browse(mock)
        wsl_path = r"\\wsl.localhost\Ubuntu\data"
        with (
            patch(
                "anylabeling.views.labeling.label_widget._try_wsl_folder_open",
                return_value=False,
            ),
            patch(
                "anylabeling.views.training.ultralytics_dialog.QFileDialog.getExistingDirectory",
                return_value=wsl_path,
            ),
        ):
            browse()

        mock.config_widgets["data"].setText.assert_called_once_with(
            wsl_path
        )

    def test_non_classify_skips_wsl(self):
        """Detection/Segmentation: WSL path should not be triggered."""
        mock = self._make_mock_dialog("Detect")
        browse = self._bind_browse(mock)
        with (
            patch(
                "anylabeling.views.labeling.label_widget._try_wsl_folder_open",
            ) as mock_try,
            patch(
                "anylabeling.views.training.ultralytics_dialog.QFileDialog.getOpenFileName",
                return_value=("", ""),
            ),
        ):
            browse()

        mock_try.assert_not_called()
