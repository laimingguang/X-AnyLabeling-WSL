<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

A fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) that restores WSL2 directory visibility in native Windows folder picker dialogs.

## Background

Training on WSL2 is standard practice for Windows-based ML engineers — CUDA GPU-PV, ext4 filesystems, and training frameworks all work natively.

The GUI side, however, has a known tradeoff. WSLG (WSL GUI) delivers noticeably blurry rendering on high-DPI displays due to its RDP-based pipeline. The upstream maintainer has explicitly recommended running X-AnyLabeling natively on Windows rather than inside WSLG ([#811](https://github.com/CVHub520/X-AnyLabeling/issues/811)).

## The Problem

When running X-AnyLabeling on Windows natively, the standard folder picker dialog hides `\\wsl.localhost` and all its child directories. This is not a bug in X-AnyLabeling or Qt — it is a known Windows Shell API behavior: `QFileDialog.getExistingDirectory` sets the `FOS_FORCEFILESYSTEM` flag, which suppresses non-filesystem namespace entries. Microsoft has acknowledged this limitation ([microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079), open since 2021).

## The Fix

The `FOS_FORCEFILESYSTEM` flag is removed from the dialog options. The WSL Linux node then appears in the sidebar naturally — the same dialog, the same behavior, no extra dependencies.

The same approach is used by JetBrains across IntelliJ, PyCharm, and all other IDEs ([JBR PR #497](https://github.com/JetBrains/JetBrainsRuntime/pull/497)).

## Scope

This affects 8 folder picker dialogs:

| Dialog | Location |
|--------|----------|
| Open Folder / Change Output Dir / Compare View | Main labeling interface |
| CSV Export Directory | Overview dialog |
| Export Directory | AI Chat dialog |
| Export Directory | Classifier dialog |
| Output Directory | Video Classification dialog |
| Dataset Directory (Classify tasks) | Training dialog |

## Non-WSL Users

No behavioral change. Linux and macOS run the standard `QFileDialog.getExistingDirectory` — identical to upstream. Windows without WSL sees no visible difference in the dialog.

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
python anylabeling/app.py
```

## Relationship to Upstream

Everything except the folder picker fix is identical to the original repository. To sync:

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
```

## License

[GPL-3.0](./LICENSE)
