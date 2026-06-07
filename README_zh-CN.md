<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[简体中文](README_zh-CN.md) | [English](README.md)

</div>

本仓库是 [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) 的一个 fork，**只增加了一项功能**：在 Windows 上原生浏览 WSL2 目录。

## 问题

Windows 上 Qt 的 `QFileDialog` 无法导航 `\\wsl.localhost\` UNC 路径，导致无法从界面打开 WSL2 中的数据集。Python 的 `os.listdir` 可以正常访问，但文件对话框不行。

## 解决方案

检测到 Windows 上存在 WSL 时，用一个自定义的 `WslDirectoryPicker` 对话框替代系统文件夹对话框。它通过 `wsl -l -q` 枚举 WSL 发行版、自动过滤非用户发行版（如 docker-desktop），让你直接浏览 WSL 文件系统 — 无需任何变通方案。

其余所有功能与原版完全一致。与上游保持同步：

```
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream && git rebase upstream/main && git push --force-with-lease
```

## 安装

```bash
git clone https://github.com/laimingguang/X-AnyLabeling.git
cd X-AnyLabeling
uv tool install --editable .
```

## 许可

[GPL-3.0](./LICENSE)
