# X-AnyLabeling-WSL — 架构备忘

## 项目位置与路径绑定

```
C:\code\github\X-AnyLabeling-WSL     ← 项目源码 + git 仓库
       ↓ (uv tool install --editable 创建链接)
%USERPROFILE%\AppData\Roaming\uv\tools\x-anylabeling-cvhub\   ← uv 工具安装目录
       ↓ (editable 模式指向源码)
C:\code\github\X-AnyLabeling-WSL     ← 运行时实际加载的代码
```

**核心约束**：`uv tool install --editable .` 把**源码路径写死**在 uv 工具环境中。移动项目目录后必须重新安装，否则 uv tool 还在引用旧路径。

## 移动目录后需执行

```powershell
# 1. 移动项目
Move-Item -LiteralPath "C:\code\..." -Destination "C:\code\github\X-AnyLabeling-WSL"

# 2. 重新建立 uv 链接（旧路径已断）
uv tool install --editable "C:\code\github\X-AnyLabeling-WSL" --with pytest

# 3. 验证
cd "C:\code\github\X-AnyLabeling-WSL"
git status
& "C:\Users\zsw\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v
```

> 不需要修改 git remote（URL 不变）、测试路径（相对于 uv tool 环境）、pytest 命令（在同一 uv 工具中）。

## 各组件间的关系

| 组件 | 位置 | 与项目的绑定 |
|------|------|-------------|
| 源码 + git | `C:\code\github\X-AnyLabeling-WSL` | 手动移动 |
| uv tool | `%APPDATA%\uv\tools\x-anylabeling-cvhub\` | `--editable` 写死路径，移动后需重装 |
| pytest | uv tool 内部（`--with pytest` 安装） | 通过 `& "..."\Scripts\pytest.exe` 调用 |
| git remote | `origin = laimingguang/X-AnyLabeling-WSL` | URL 不变，不受路径影响 |

## 常用命令

```powershell
# 运行 WSL 测试
& "$env:USERPROFILE\AppData\Roaming\uv\tools\x-anylabeling-cvhub\Scripts\pytest.exe" tests\test_wsl_picker.py -v

# 从源码重新注册 uv tool（路径变化 / 重装 Python 后需要）
uv tool install --editable . --with pytest

# 同步上游
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git  # 首次
git fetch upstream
git rebase upstream/main
```

## 关键文件

- `anylabeling/views/labeling/label_widget.py` — `WslDirectoryPicker` 类、`_try_wsl_folder_open` 函数
- `anylabeling/views/labeling/utils/wsl.py` — 纯逻辑层（`get_wsl2_distro_paths`、`is_user_distro`、`list_directory_entries`）
- `anylabeling/views/training/ultralytics_dialog.py` — `browse_data_file` 中 WSL 支持（延迟 import）
- `tests/test_wsl_picker.py` — 43 个 WSL 相关测试
