<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

A fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) that enables **native WSL2 dataset directory browsing** on Windows. If you do your deep learning on WSL2 but want crisp HiDPI rendering at the GUI layer, this fork closes the gap between the two environments.

---

## The Problem

**WSL2** is the de facto deep learning environment on Windows. It provides a real Linux kernel with native NVIDIA CUDA GPU-PV support (direct `/dev/nvidia*` access), full-speed ext4 filesystems, and seamless training framework integration. Practitioners run training, data preprocessing, and model inference inside WSL2/Ubuntu as a matter of course.

For **GUI tools like X-AnyLabeling**, however, **WSLG** (WSL GUI) has fundamental display limitations on high-DPI screens. Internally, WSLG uses an RDP-based rendering pipeline: a `Weston` Wayland compositor → `mutter` window manager → RDP server → Windows RDP client. On displays with non-integer scale factors (>150%), this produces visibly blurry or pixel-doubled rendering, lacks per-monitor DPI awareness, introduces input latency, and delivers font quality far below native Windows ClearType / DirectWrite. The natural solution is to run X-AnyLabeling on **native Windows**, where HiDPI, font rendering, and GPU-accelerated painting work flawlessly.

But this creates a second problem. X-AnyLabeling's folder dialog (`QFileDialog`) depends on the Windows Shell API (`IFileDialog` / `IFileOpenDialog`) for directory navigation. The Windows Shell does not recognize `\\wsl.localhost` as a navigable namespace entry. Although the WSL network provider (`wslfs.sys` + `wsl.exe`) surfaces it as a UNC path at the Win32 API layer, Qt's shell integration cannot enumerate or enter it. The typical workaround — mapping a network drive to `\\wsl.localhost\Ubuntu\home\...` via `net use` — is fragile, user-unfriendly, and does not survive reboots.

In short: you must choose between **good display quality** (Windows-native GUI) and **access to your WSL dataset** (running inside WSL). Until now.

## Our Solution

When WSL is detected on Windows, this fork transparently replaces the native folder dialog with a custom `WslDirectoryPicker(QDialog)` that bypasses the Windows Shell entirely:

- **Distro enumeration** via `wsl -l -q`, decoded as UTF-16-LE with `errors="replace"` (the output encoding Windows actually uses, which standard detection misses).
- **User-distro filtering**: only distros with a non-empty `/home` directory are shown, with a secondary `"docker"` name check as a safeguard. This hides docker-desktop and other non-user environments.
- **Lazy-loaded tree navigation** using Python's `os.listdir` directly — `os.listdir` works fine on `\\wsl.localhost\Ubuntu\home\...` even though the Windows Shell cannot navigate there. Each directory is loaded on first expansion and cached in a `_loaded` set.
- **Robust error handling**: all `OSError` exceptions from `os.listdir` are caught (WinError 64 on the `\\wsl.localhost` root, permission errors on protected directories, etc.).
- **No external dependencies**: the pure-logic layer (`utils/wsl.py`) imports only `os` and `os.path`. The Qt dialog layer in `label_widget.py` uses only PyQt6 widgets already present in the project.

The result is seamless: **native Windows GUI quality + full WSL filesystem access**, zero configuration, no workarounds needed.

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling.git
cd X-AnyLabeling
uv tool install --editable .
```

To run tests:

```bash
uv tool install --editable . --with pytest
& "$env:USERPROFILE\.local\bin\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
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
