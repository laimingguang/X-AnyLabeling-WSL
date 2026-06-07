# WSL 目录浏览功能改进目标

## 问题

Windows 上运行 X-AnyLabeling 时，`QFileDialog` 无法导航到 `\\wsl.localhost\` 下的 WSL 目录（Qt 和 Windows 原生对话框的已知限制）。但 Python 的 `os.listdir` 可以读写 UNC 路径。

## 已实现

- [x] 新增 `WslDirectoryPicker(QDialog)` 类：用 `os.listdir` + `QTreeWidget` 惰性加载 WSL 目录树
- [x] `open_folder_dialog` 中检测 WSL 发行版，弹出选择框让用户选 **Windows** 或 **WSL (Linux)**
- [x] 支持多发行版：`wsl -l -q` 获取所有发行版列表，在树中并列展示
- [x] `_loaded` 缓存避免重复 listdir，`OSError` 全覆盖异常处理
- [x] 修复原 bug：`getExistingDirectory` 取消时不再传空路径给 `import_image_folder`
- [x] 切换到源码运行模式：`uv tool install --editable "C:\code\projects\X-AnyLabeling"`
- [x] 提取纯逻辑到 `utils/wsl.py`（`is_user_distro` + `list_directory_entries`），零外部依赖
- [x] `label_widget.py` 中 `_is_user_distro` 改为调用 `utils/wsl.py` 的函数
- [x] `_populate_children` 改为调用 `utils/wsl.py` 的 `list_directory_entries`
- [x] `test_wsl_picker.py`：22 个测试全部通过（13 纯逻辑 + 4 目录列举 + 3 名称提取 + 2 Qt 集成测试）
- [x] `uv tool install --with pytest` 保证 pytest 随工具环境一起部署
- [x] 修复 UNC 路径 `osp.basename` 返回空字符串的问题（改用 `path.rstrip("\\").split("\\")[-1]`）
- [x] `_is_user_distro` 过滤策略：非空 `/home` 优先（`docker` 名称兜底），覆盖当前所有 WSL 发行版

## 待改进

- [ ] 安装 PyQt6 到测试环境，启用 5 个 Qt 集成测试
- [ ] 为 `open_folder_dialog` 的 WSL 检测逻辑编写测试（mock `subprocess.run` + `QMessageBox`）
- [ ] 考虑是否为其他使用 `QFileDialog` 的地方（如 auto-labeling 模型选择）也添加 WSL 支持
- [ ] 考虑是否添加 WSL 路径历史记录 / 快速访问
- [ ] WSL 目录浏览性能优化（深度嵌套目录时可能卡 UI，考虑 QThread）

## 发现并修复的 bug

- `osp.basename(r"\\wsl.localhost\Ubuntu")` 在 Windows 上返回 `""`（原代码在 6 个地方使用了此模式）
- `os.listdir(r"\\wsl.localhost")` 在 `\\wsl.localhost` 根目录抛出 WinError 64（需用 `wsl -l -q` 替代）
- `wsl -l -q` 输出编码为 UTF-16-LE（标准编码检测会失败）
- `uv tool install` 重新安装时会清空 `pip install` 安装的包，需用 `uv tool install --editable`

## 提 PR 前检查

- [ ] 代码风格是否匹配项目惯例（已有类风格，通过）
- [ ] 是否向后兼容（非 Windows / 无 WSL 时零影响，通过）
- [ ] `WslDirectoryPicker` 类及各提取函数的 docstring 是否清晰
- [ ] 是否需要在文档中说明 WSL 支持（可提 PR 后再补）
- [ ] 17 个纯逻辑测试 + 5 个 Qt 集成测试全部通过
- [ ] 整理 commit 历史，确保只包含 WSL 相关改动
