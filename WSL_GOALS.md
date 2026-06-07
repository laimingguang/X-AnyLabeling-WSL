# WSL 目录浏览功能改进目标

## 问题

Windows 上运行 X-AnyLabeling 时，`QFileDialog` 无法导航到 `\\wsl.localhost\` 下的 WSL 目录（Qt 和 Windows 原生对话框的已知限制）。但 Python 的 `os.listdir` 可以读写 UNC 路径。

## 已实现

- [x] 新增 `WslDirectoryPicker(QDialog)` 类：用 `os.listdir` + `QTreeWidget` 惰性加载 WSL 目录树
- [x] `open_folder_dialog` 中检测 WSL 发行版，弹出选择框让用户选 **Windows** 或 **WSL (Linux)**
- [x] 支持多发行版：`wsl -l -q` 获取所有发行版列表，在树中并列展示
- [x] `_loaded` 缓存避免重复 listdir，`OSError` 全覆盖异常处理
- [x] 修复原 bug：`getExistingDirectory` 取消时不再传空路径给 `import_image_folder`

## 待改进

- [ ] 从 uv 工具安装模式切换到源码运行模式，避免手动 Copy-Item
- [ ] 考虑是否为其他使用 `QFileDialog` 的地方（如 auto-labeling 模型选择）也添加 WSL 支持
- [ ] 考虑是否添加 WSL 路径历史记录 / 快速访问
- [ ] WSL 目录浏览性能优化（深度嵌套目录时可能卡 UI，考虑 QThread）

## 提 PR 前检查

- [ ] 代码风格是否匹配项目惯例（已有类风格，通过）
- [ ] 是否向后兼容（非 Windows / 无 WSL 时零影响，通过）
- [ ] `WslDirectoryPicker` 类的 docstring 是否清晰
- [ ] 是否需要在文档中说明 WSL 支持（可提 PR 后再补）
