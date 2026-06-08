<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

本 fork 在 Windows 原生文件夹选择对话框中**使 WSL2 数据集目录可见**——无需变通方案，无需 WSLG 的模糊渲染，无需手动映射网络驱动器。

---

## 问题

Windows Shell 的 `IFileOpenDialog` 在被 `QFileDialog.getExistingDirectory` 调用时会设置 `FOS_FORCEFILESYSTEM` 标志。该标志会**隐藏导航栏中的 WSL Linux 节点**（`\\wsl.localhost`）——这是 Windows 的已知限制（[microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079)，已开放超过 3 年；[microsoft/WindowsAppSDK#6284](https://github.com/microsoft/WindowsAppSDK/issues/6284)）。

实际后果：如果你在 WSL2 上进行深度学习训练（CUDA GPU-PV、ext4 文件系统、训练框架原生支持），同时在 Windows 上使用 X-AnyLabeling 以获得清晰的 HiDPI 渲染，你将无法通过标准文件夹对话框浏览到 WSL 数据集。

## 解决方案

本 fork 采用了与 **JetBrains JBR PR #497** 相同的方案：直接通过 Python ctypes 打开 `IFileOpenDialog`，使用 `FOS_PICKFOLDERS` 但**不加** `FOS_FORCEFILESYSTEM`。WSL Linux 节点自然显示在侧边栏——无需自定义对话框，无需 Shell 命名空间破解，无需额外依赖。

### 实现原理

- **`pick_folder()`**——轻量级 ctypes 封装，调用 `CoCreateInstance(CLSID_FileOpenDialog)`。通过 `IFileDialog::GetOptions` 获取当前选项，添加 `FOS_PICKFOLDERS`，然后调用 `IFileDialog::Show`。`FOS_FORCEFILESYSTEM` 标志从未设置。返回选中路径或 `None`。

- **`get_existing_directory()`**——`QFileDialog.getExistingDirectory` 的即插即用替换方案，签名完全一致。Windows 上委托给 `pick_folder()`，非 Windows 上回退到标准 Qt 实现。返回选中路径或空字符串。

- **`utils/wsl.py`**——全部实现就在这里：约 130 行纯标准库代码（`ctypes`、`os`、`typing`）。零外部依赖。

- **替换了 8 处原生对话框调用点**——所有使用原生 `IFileOpenDialog`（未设置 `DontUseNativeDialog`）的文件夹选择器现在都通过 `get_existing_directory()`：

  | 位置 | 用途 |
  |------|------|
  | `label_widget.py` | 打开文件夹、更改输出目录、对比视图 |
  | `overview_dialog.py` | CSV 导出目录 |
  | `chatbot_dialog.py` | 聊天导出目录 |
  | `classifier/dialogs.py` | 分类器导出目录 |
  | `video_classifier/export_dialog.py` | 视频分类输出目录 |
  | `ultralytics_dialog.py` | 训练数据集（分类任务） |

- **13 处 `DontUseNativeDialog` 调用点保持不变**——这些调用点原本就使用 Qt 自定义对话框渲染（不涉及 `IFileOpenDialog`），因此从未出现 WSL 问题。

## 行为保证

| 场景 | 行为 |
|------|------|
| Windows + WSL | 原生对话框，WSL Linux 节点可见 |
| Windows（无 WSL） | 原生对话框，无明显变化 |
| Linux / macOS | 标准 `QFileDialog.getExistingDirectory`（与上游一致）|
| 用户取消对话框 | 返回空字符串，无二次弹窗回退 |
| COM 不可用 | 回退到 `QFileDialog.getExistingDirectory` |

## 安装

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

运行测试套件：

```bash
uv tool install --editable . --with pytest
& "$env:USERPROFILE\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
```

## 与上游的关系

除 WSL 文件夹选择器修复（`utils/wsl.py` + 8 处调用点 + 测试）外，其余部分与上游完全一致。同步最新上游变更：

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
```

## 许可证

[GPL-3.0](./LICENSE)
