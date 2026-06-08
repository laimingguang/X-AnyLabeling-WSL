<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[简体中文](README_zh-CN.md) | [English](README.md)

</div>

# WSL-Enhanced X-AnyLabeling

这是 [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) 的一个 fork，唯一增加的功能是：**在 Windows 上原生浏览 WSL2 数据集目录**。如果你用 WSL2 做深度学习、但希望在 Windows 原生环境下享受清晰的高分屏 GUI 体验，这个 fork 就是为此而生。

---

## 问题

**WSL2** 是 Windows 上深度学习的主流运行环境。它提供真实的 Linux 内核、原生 NVIDIA CUDA GPU-PV 支持（可直接访问 `/dev/nvidia*`）、全速 ext4 文件系统，与训练框架无缝集成。用户自然会在 WSL2/Ubuntu 中运行训练、数据预处理和模型推理。

但对于 **GUI 工具（如 X-AnyLabeling）**，**WSLG** 的高分屏体验存在根本性缺陷。WSLG 内部基于 RDP 远程渲染管线：`Weston`（Wayland 合成器）→ `mutter`（窗口管理器）→ RDP 服务器 → Windows RDP 客户端。在非整数缩放比（>150%）的屏幕上，渲染效果模糊或出现像素倍增，不支持按显示器独立 DPI 感知，存在输入延迟，字体渲染远不如 Windows 原生 ClearType / DirectWrite。自然的解决方案是在 **Windows 原生环境**下运行 X-AnyLabeling——HiDPI、字体渲染、GPU 加速绘制均完美工作。

但这又引出第二个问题。X-AnyLabeling 的文件对话框（`QFileDialog`）底层依赖 Windows Shell API（`IFileDialog` / `IFileOpenDialog`）进行目录导航。Windows Shell 不将 `\\wsl.localhost` 视为可导航的命名空间项。虽然 WSL 网络提供程序（`wslfs.sys` + `wsl.exe`）在 Win32 API 层以 UNC 路径形式将其暴露，但 Qt 的 Shell 集成无法枚举或进入该路径。常见的变通方案——通过 `net use` 将 `\\wsl.localhost\Ubuntu\home\...` 映射为网络驱动器——操作繁琐、重启后失效、用户体验差。

简而言之：你必须在 **好的显示效果**（Windows 原生 GUI）和 **访问 WSL 数据集**（在 WSL 内部运行）之间二选一。直到现在。

## 解决方案

WSL 文件夹选择器问题的根源是 Windows Shell API 的一个标志。Qt 的 `QFileDialog.getExistingDirectory` 在调用原生 `IFileOpenDialog` 时设置了 `FOS_FORCEFILESYSTEM` 标志。这个标志会**隐藏导航栏中的 WSL Linux 节点**（`\\wsl.localhost`）——这是 Windows 的已知限制（[microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079)、[microsoft/WindowsAppSDK#6284](https://github.com/microsoft/WindowsAppSDK/issues/6284)）。

本 fork 采用了与 **JetBrains JBR PR #497** 相同的修复方案：直接通过 ctypes 调用 `IFileOpenDialog`，使用 `FOS_PICKFOLDERS` 但**不加** `FOS_FORCEFILESYSTEM`。结果是一个完全原生的 Windows 文件夹对话框，能够正常显示 WSL Linux 节点：

![WSL/Windows 选择](assets/wsl-select-dialog.png)

- **COM 级别修复**：轻量级 ctypes 封装，调用 `CoCreateInstance(CLSID_FileOpenDialog)`，去掉 `FOS_FORCEFILESYSTEM`，通过标准 `IFileOpenDialog::Show` 显示对话框。
- **即插即用替换**：`get_existing_directory()` 的签名与 Qt 的 `QFileDialog.getExistingDirectory` 一致。Windows 上调用 COM 对话框，非 Windows 上直接委托给 Qt。
- **无重复弹窗**：用户取消 COM 对话框后返回空字符串，不弹第二个对话框。
- **替换了 8 处调用点**：应用中所有原生（非 `DontUseNativeDialog`）文件夹选择器均已使用新的 COM 辅助函数——打开文件夹、更改输出目录、对比视图、CSV 导出目录、聊天机器人导出、分类器导出、视频分类导出和训练数据集目录。
- **13 处 `DontUseNativeDialog` 调用点保持不变**：这些调用点原本就使用 Qt 自定义对话框（不涉及 `IFileOpenDialog`），因此从未出现 WSL 问题。
- **零额外依赖**：仅使用 Python 标准库（`ctypes`、`os`、`typing`）直接调用 Windows Shell API。
- **向后兼容**：在 Linux、macOS 和未安装 WSL 的 Windows 上行为一致。

最终效果是无缝的：**Windows 原生界面品质 + 完整 WSL 文件系统访问**，零配置，无需任何变通方案。

## 安装

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

运行测试：

```bash
uv tool install --editable . --with pytest
& "$env:USERPROFILE\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
```

## 与上游的关系

除 WSL 目录选择器外，所有功能与原版完全一致。与上游保持同步：

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
git push --force-with-lease
```

## 许可

[GPL-3.0](./LICENSE)
