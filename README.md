<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

This is a fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) with **one additional feature**: native WSL2 directory browsing on Windows.

## The Problem

On Windows, Qt's `QFileDialog` cannot navigate `\\wsl.localhost\` UNC paths, making it impossible to open WSL2 datasets from the GUI. Python's `os.listdir` works fine, but the file dialog does not.

## The Fix

When WSL is detected on Windows, a custom `WslDirectoryPicker` dialog replaces the native folder dialog. It enumerates WSL distros via `wsl -l -q`, filters non-user distros (e.g. docker-desktop), and lets you browse directly into your WSL filesystem — no workarounds needed.

Everything else is identical to upstream. Keep up with upstream changes via:

```
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream && git rebase upstream/main && git push --force-with-lease
```

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling.git
cd X-AnyLabeling
uv tool install --editable .
```

## License

[GPL-3.0](./LICENSE)
