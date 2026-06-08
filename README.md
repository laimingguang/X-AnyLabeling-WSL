<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

A fork of [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) that does one thing: **makes your WSL dataset folders visible in the Windows file picker dialog.** That's it. No extra dialogs, no workarounds, no configuration.

---

## If This Sounds Familiar

You train on **WSL2** — CUDA works, ext4 is fast, everything runs great. But when you run X-AnyLabeling on **Windows** (where the UI is crisp on high-DPI screens, fonts render correctly, and there's no input lag), you click "Open Folder" and… your WSL directories are simply not there. `\\wsl.localhost\Ubuntu\home\...` might as well be invisible.

The upstream maintainer has confirmed this workflow: run the app on Windows natively, not inside WSLG ([#811](https://github.com/CVHub520/X-AnyLabeling/issues/811)). But that leaves you with no way to browse to your WSL dataset.

## What This Fork Does

WSL folders now show up in the folder picker's sidebar — the same standard Windows dialog you already know, just without the restriction that was hiding your Linux files.

No custom dialog. No `net use` drive mapping. No switching back to WSLG.

| Where you'll see WSL folders | What it is |
|------------------------------|------------|
| Open Folder / Change Output Dir / Compare View | Main labeling interface |
| CSV Export | Overview dialog |
| Export Directory | AI Chat dialog |
| Export Directory | Classifier dialog |
| Output Directory | Video Classification dialog |
| Data File (Classify tasks) | Training dialog |

## Does This Affect Me If I Don't Use WSL?

**No.** The folder picker looks exactly the same as before. The change only affects what's listed in the sidebar — if you don't have WSL installed, nothing new appears.

On **Linux and macOS**, this fork behaves identically to the original X-AnyLabeling. Zero difference.

## Acknowledgments

The technical approach is based on **JetBrains JBR PR #497** — the same method JetBrains uses in their IDEs (IntelliJ, PyCharm, etc.) to show WSL files in native file dialogs. The fix addresses a known Windows API limitation ([microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079), open since 2021).

## Install

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

Then run it the same way as the original:

```bash
python anylabeling/app.py
```

## Relationship to Upstream

Everything except the folder picker fix is identical to the original [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling). To sync with upstream updates:

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
```

## License

[GPL-3.0](./LICENSE)
