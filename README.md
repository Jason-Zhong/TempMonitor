<div align="center">

# 🌡️ TempMonitor

**Windows 桌面硬件温度监控悬浮窗**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2011%2B-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Release](https://img.shields.io/github/v/release/Jason-Zhong/TempMonitor?include_prereleases)

</div>

---

## 📖 简介

TempMonitor 是一款轻量级 Windows 桌面工具，在**半透明悬浮窗**上实时显示 CPU 温度、内存使用率和主板温度。支持设置面板自定义显示项、颜色主题、刷新频率等，适合游戏、超频、压测等场景下边玩边监控硬件状态。

> 💡 **和 TrafficMonitor 互补**：TrafficMonitor 强在任务栏网速监控，TempMonitor 强在 CPU/主板温度监控，两者可同时使用。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🌡️ **CPU 温度** | 实时核心温度 + 封装温度，颜色分级（绿/橙/红） |
| 📊 **CPU 负载** | 总负载 + 每核心负载 + 进度条 |
| 💾 **内存使用率** | 已用/总量 + 百分比 + 进度条（超85%变红） |
| 🔌 **主板温度** | 读取主板温度传感器（传感器存在时） |
| 🪟 **桌面悬浮窗** | 无边框、半透明、置顶、可拖拽 |
| ⚙️ **设置面板** | 刷新间隔、透明度、字体、主题、显示开关 |
| 🎨 **深色/浅色主题** | 一键切换 |
| 🖱️ **系统托盘** | 左键显隐、右键菜单（设置/开机自启/退出） |
| 🔄 **自适应刷新** | 1s~10s 可调 |

---

## 🖼️ 截图

> <!-- 建议放一张截图在此处 -->
> ```
> ┌─ TempMonitor ────⚙ ✕─┐
> │ CPU: 45°C        23%  │
> │ ████████░░░░░░░░░░░░  │
> │ ⚡ 4 核              │
> │                       │
> │ MEM: 50%  7.8/15.6 GB │
> │ ██████████░░░░░░░░░░  │
> │                       │
> │ 主板: 35°C            │
> └───────────────────────┘
> ```
>
> *（实际效果为半透明悬浮窗，颜色随温度变化）*

---

## 🏗️ 技术架构

```
TempMonitor/
├── main.py                  # 主入口：整合所有组件
├── config.py                # 配置管理器（JSON 持久化）
├── hardware_service.py      # 硬件数据采集层
├── ui/
│   ├── overlay_window.py    # 桌面悬浮窗 UI（tkinter）
│   ├── settings_window.py   # 设置对话框
│   └── tray_icon.py         # 系统托盘（pystray）
├── libs/
│   └── *.dll                # LibreHardwareMonitorLib 及依赖
└── dist/
    └── TempMonitor.exe      # 打包后的可执行文件
```

### 核心技术

| 组件 | 用途 |
|------|------|
| **Python 3.13 + tkinter** | GUI 框架，内置无需额外安装 |
| **LibreHardwareMonitorLib** | 通过 Ring0 驱动读取硬件传感器（CPU/主板/内存） |
| **psutil** | 内存使用率读取（跨平台可靠方案） |
| **pystray + Pillow** | 系统托盘图标 |
| **PyInstaller** | 打包为单文件 exe |

---

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 从 [Releases](https://github.com/Jason-Zhong/TempMonitor/releases) 下载 `TempMonitor.exe`
2. 双击运行即可

### 方式二：源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/Jason-Zhong/TempMonitor.git
cd TempMonitor

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
```

---

## 📦 打包为单文件 exe

```bash
# 安装 PyInstaller
pip install pyinstaller

# 执行打包
pyinstaller --onefile --windowed --name "TempMonitor" --add-data "libs\*.dll;libs" --hidden-import clr --collect-all pythonnet main.py
```

打包完成后在 `dist/TempMonitor.exe`。

> ⚠️ 打包后的 exe 需要目标机器安装 **.NET Runtime 8.0**（Win11 通常已内置或可通过 Windows Update 获取）。

---

## ⚙️ 设置说明

打开悬浮窗后，点击标题栏 **⚙** 按钮或右键菜单 **设置...**：

| 标签页 | 设置项 | 说明 |
|--------|--------|------|
| **显示** | 刷新间隔 | 1s / 2s / 3s / 5s / 10s |
| | 窗口透明度 | 50%~100% 滑块调节 |
| | 字体大小 | 小 / 中 / 大 |
| | 颜色主题 | 深色 / 浅色 |
| | 窗口置顶 | 是否始终在最前 |
| **高级** | CPU 进度条 | 显示/隐藏 |
| | 内存使用率行 | 显示/隐藏 |
| | 主板温度行 | 显示/隐藏 |
| | 开机自启 | 注册到 Windows 启动项 |

---

## 🔧 已知问题

| 问题 | 说明 |
|------|------|
| **传感器支持** | 部分设备（如虚拟机、某些笔记本）可能没有暴露温度传感器，此时对应数据会显示 `--°C` |
| **管理员权限** | LibreHardwareMonitorLib 在某些系统上需要管理员权限才能读取传感器 |
| **pythonnet 兼容性** | PyInstaller 打包时需注意 `--hidden-import clr` 参数 |
| **内存占用** | 由于加载 .NET CLR，内存约 30-50MB（高于原生 C++ 方案） |

---

## 📜 依赖声明

| 依赖 | 许可证 | 用途 |
|------|--------|------|
| [LibreHardwareMonitorLib](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) | MPL-2.0 | 硬件传感器读取 |
| [psutil](https://github.com/giampaolo/psutil) | BSD-3-Clause | 内存使用率 |
| [pystray](https://github.com/moses-palmer/pystray) | LGPL-3.0 | 系统托盘 |
| [Pillow](https://github.com/python-pillow/Pillow) | HPND | 托盘图标生成 |
| [pythonnet](https://github.com/pythonnet/pythonnet) | MIT | Python ↔ .NET 桥接 |

---

## 📄 License

本项目基于 **MIT License** 开源。

LibreHardwareMonitorLib 基于 **MPL-2.0** 许可证。

---

## 🙏 致谢

- [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) — 提供强大的硬件监控库
- [namazso](https://github.com/namazso) — PawnIO 等底层工具
- [TrafficMonitor](https://github.com/zhongyang219/TrafficMonitor) — 优秀的网速监控工具，启发本项目定位

---

<div align="center">
  <sub>Made with ❤️ for Windows hardware monitoring</sub>
</div>
