<div align="center">
  <p>
    <a href="https://github.com/laimingguang/X-AnyLabeling-WSL/" target="_blank">
      <img alt="X-AnyLabeling" height="200px" src="https://github.com/user-attachments/assets/0714a182-92bd-4b47-b48d-1c5d7c225176"></a>
  </p>

[English](README.md) | [简体中文](README_zh-CN.md)

</div>

# WSL-Enhanced X-AnyLabeling

这是一个 [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) 的 fork，只做了一件事：**让 Windows 文件夹选择弹窗能看到你的 WSL 数据集目录。** 没有多余的对话框，没有变通方案，不需要配置。

---

## 你是不是也遇到过这个情况

你的深度学习跑在 **WSL2** 上——CUDA 直通、ext4 文件系统、训练框架都好好的。但跑 X-AnyLabeling 的时候，你希望在 **Windows 原生环境** 下运行（4K 屏清晰、字体渲染正常、没有输入延迟）。一打开文件夹选择器，WSL 的目录全都不见了。`\\wsl.localhost\Ubuntu\home\...` 就像不存在一样。

上游作者已经在 issue 里确认了这个方案：在 Windows 原生跑，不要在 WSLG 里跑（[#811](https://github.com/CVHub520/X-AnyLabeling/issues/811)）。但这把你晾在半路了——你的数据全在 WSL 里，Windows 弹窗却看不到。

## 我们做了什么

WSL 文件夹现在会正常显示在文件夹选择器的左侧导航栏里——就是那个你熟悉的 Windows 原生弹窗，只是去掉了隐藏 Linux 文件的限制。

不需要自定义对话框，不需要 `net use` 映射网络驱动器，不需要切回 WSLG。

| 你能看到 WSL 文件夹的地方 | 对应功能 |
|---------------------------|----------|
| 打开目录 / 更改输出目录 / 对比视图 | 标注主界面 |
| CSV 导出目录 | 概览对话框 |
| 导出目录 | AI 聊天对话框 |
| 导出目录 | 分类器对话框 |
| 输出目录 | 视频分类对话框 |
| 数据文件（分类任务） | 训练对话框 |

## 不用 WSL 的人会受影响吗？

**不会。** 文件夹弹窗看起来和之前完全一样。改动只影响侧边栏的内容——你没有 WSL 的话，什么也不会多出来。

**Linux 和 macOS** 上这个 fork 的行为和原版 X-AnyLabeling 完全一致。没有任何区别。

## 致谢

技术方案参考了 [**JetBrains JBR PR #497**](https://github.com/JetBrains/JetBrainsRuntime/pull/497)——和 JetBrains 家 IDE（IntelliJ、PyCharm 等）在原生文件对话框中显示 WSL 文件用的是同一个方法。这个修复针对的 Windows API 限制（[microsoft/WSL#9079](https://github.com/microsoft/WSL/issues/9079)）已经挂了 3 年多无人修复。

## 安装

```bash
git clone https://github.com/laimingguang/X-AnyLabeling-WSL.git
cd X-AnyLabeling
uv tool install --editable .
```

运行方式和原版一样：

```bash
python anylabeling/app.py
```

## 与原版的关系

除文件夹选择器修复外，其余部分和原始 [CVHub520/X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) 完全一致。同步上游更新：

```bash
git remote add upstream https://github.com/CVHub520/X-AnyLabeling.git
git fetch upstream
git rebase upstream/main
```

## 许可证

[GPL-3.0](./LICENSE)
