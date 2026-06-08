<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

A fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) that adds **native WSL2 dataset directory browsing** on Windows. If you do your deep learning on WSL2 but want crisp HiDPI rendering at the GUI layer, this fork closes the gap between the two environments.

---

## The Problem

**WSL2** is the de facto deep learning environment on Windows. It provides a real Linux kernel with native NVIDIA CUDA GPU-PV support (direct `/dev/nvidia*` access), full-speed ext4 filesystems, and seamless training framework integration. Practitioners run training, data preprocessing, and model inference inside WSL2/Ubuntu as a matter of course.

For **GUI tools like X-AnyLabeling**, however, **WSLG** (WSL GUI) has fundamental display limitations on high-DPI screens. Internally, WSLG uses an RDP-based rendering pipeline: a `Weston` Wayland compositor → `mutter` window manager → RDP server → Windows RDP client. On displays with non-integer scale factors (>150%), this produces visibly blurry or pixel-doubled rendering, lacks per-monitor DPI awareness, introduces input latency, and delivers font quality far below native Windows ClearType / DirectWrite. The natural solution is to run X-AnyLabeling on **native Windows**, where HiDPI, font rendering, and GPU-accelerated painting work flawlessly.

But this creates a second problem. X-AnyLabeling's folder dialog (`QFileDialog`) depends on the Windows Shell API (`IFileDialog` / `IFileOpenDialog`) for directory navigation. The Windows Shell does not recognize `\\wsl.localhost` as a navigable namespace entry. Although the WSL network provider (`wslfs.sys` + `wsl.exe`) surfaces it as a UNC path at the Win32 API layer, Qt's shell integration cannot enumerate or enter it. The typical workaround — mapping a network drive to `\\wsl.localhost\Ubuntu\home\...` via `net use` — is fragile, user-unfriendly, and does not survive reboots.

In short: you must choose between **good display quality** (Windows-native GUI) and **access to your WSL dataset** (running inside WSL). Until now.

## Our Solution

The root cause of the WSL folder picker problem is a Windows Shell API flag. Qt's `QFileDialog.getExistingDirectory` opens the native `IFileOpenDialog` with the `FOS_FORCEFILESYSTEM` flag set. This flag **hides the WSL Linux node** (`\\wsl.localhost`) from the dialog's navigation pane — a known Windows limitation ([microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079), [microsoft/WindowsAppSDK#6284](https://github.com/microsoft/WindowsAppSDK/issues/6284)).

This fork uses the same fix as **JetBrains JBR PR #497**: it opens `IFileOpenDialog` directly via ctypes with `FOS_PICKFOLDERS` but **without** `FOS_FORCEFILESYSTEM`. The result is a fully native Windows folder dialog that shows the WSL Linux node:

![WSL/Windows selector](assets/wsl-select-dialog.png)

- **COM-level fix**: a lightweight ctypes wrapper calls `CoCreateInstance(CLSID_FileOpenDialog)`, strips `FOS_FORCEFILESYSTEM`, and shows the dialog via the standard `IFileOpenDialog::Show`.
- **Drop-in replacement**: `get_existing_directory()` mirrors Qt's `QFileDialog.getExistingDirectory` signature. On Windows it calls the COM dialog; on non-Windows it delegates to Qt directly.
- **No double dialogs**: if the user cancels the COM dialog, the function returns an empty string — no fallback, no second popup.
- **8 call sites replaced**: all native (non-`DontUseNativeDialog`) folder pickers across the app use the new COM-aware helper — Open Folder, Change Output Directory, Compare View, CSV Export Directory, Chatbot Export, Classifier Export, Video Classification Export, and Training Dataset Directory.
- **13 `DontUseNativeDialog` call sites unchanged**: these already used Qt's custom dialog (no `IFileOpenDialog` involved), so they never had the WSL problem.
- **No external dependencies**: uses only Python stdlib (`ctypes`, `os`, `typing`) to call the Windows Shell API directly.
- **Backward compatible**: identical behavior on Linux, macOS, and Windows without WSL.

The result is seamless: **native Windows GUI quality + full WSL filesystem access**, zero configuration, no workarounds needed.

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

To run tests:

```bash
uv tool install --editable . --with pytest
& "$env:USERPROFILE\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
```

## Relationship to Upstream

Everything except the WSL directory picker is identical to upstream. To sync with the latest upstream changes:

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
git push --force-with-lease
```

## License

[GPL-3.0](./LICENSE)
