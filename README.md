<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

A fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) that makes WSL2 dataset directories visible in native Windows folder selection dialogs — no workarounds, no WSLG blur, no manual network drive mapping.

---

## The Problem

Windows Shell's `IFileOpenDialog` sets the `FOS_FORCEFILESYSTEM` flag when invoked via `QFileDialog.getExistingDirectory`. This flag **hides the WSL Linux node** (`\\wsl.localhost`) from the folder picker's navigation pane — a known Windows limitation ([microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079), still open for 3+ years; [microsoft/WindowsAppSDK#6284](https://github.com/microsoft/WindowsAppSDK/issues/6284)).

The practical consequence: if you run your deep learning on WSL2 (where CUDA GPU-PV, ext4 filesystems, and training frameworks work natively) but use X-AnyLabeling on Windows for crisp HiDPI rendering, you cannot browse to your WSL datasets through the standard folder dialog.

## The Solution

This fork follows the same approach as **JetBrains JBR PR #497**: it opens `IFileOpenDialog` directly via Python ctypes with `FOS_PICKFOLDERS` but **without** `FOS_FORCEFILESYSTEM`. The WSL Linux node appears naturally in the sidebar — no custom dialog, no shell namespace hacking, no extra dependencies.

### How it works

- **`pick_folder()`** — a lightweight ctypes wrapper around `CoCreateInstance(CLSID_FileOpenDialog)`. It gets the dialog's current options via `IFileDialog::GetOptions`, adds `FOS_PICKFOLDERS`, and calls `IFileDialog::Show`. The `FOS_FORCEFILESYSTEM` flag is never set. Returns the selected path or `None`.

- **`get_existing_directory()`** — a drop-in replacement for `QFileDialog.getExistingDirectory` with an identical signature. On Windows it delegates to `pick_folder()`; on non-Windows it falls through to the standard Qt implementation. Returns the selected path or empty string.

- **`utils/wsl.py`** — the entire implementation lives here: ~130 lines of pure stdlib (`ctypes`, `os`, `typing`). No external dependencies.

- **8 native dialog call sites replaced** — all folder pickers that used the native `IFileOpenDialog` (without `DontUseNativeDialog`) now route through `get_existing_directory()`:

  | Location | Usage |
  |----------|-------|
  | `label_widget.py` | Open Folder, Change Output Directory, Compare View |
  | `overview_dialog.py` | CSV Export Directory |
  | `chatbot_dialog.py` | Chat Export Directory |
  | `classifier/dialogs.py` | Classifier Export Directory |
  | `video_classifier/export_dialog.py` | Video Classification Output |
  | `ultralytics_dialog.py` | Training Dataset (Classify) |

- **13 `DontUseNativeDialog` call sites unchanged** — these already used Qt's custom dialog renderer, which does not involve `IFileOpenDialog` and therefore never had the WSL problem.

## Behavioral Guarantees

| Scenario | Behavior |
|----------|----------|
| Windows + WSL | Native dialog with WSL Linux node visible |
| Windows (no WSL) | Native dialog, no visible change |
| Linux / macOS | Standard `QFileDialog.getExistingDirectory` (identical to upstream) |
| User cancels dialog | Returns empty string, no double-dialog fallback |
| COM unavailable | Falls through to `QFileDialog.getExistingDirectory` |

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

To run the test suite:

```bash
uv tool install --editable . --with pytest
& "$env:USERPROFILE\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
```

## Relationship to Upstream

Everything except the WSL folder picker fix (`utils/wsl.py` + 8 call sites + tests) is identical to upstream. To sync with the latest upstream changes:

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
```

## License

[GPL-3.0](./LICENSE)
