# 手动发布到 GitHub 的步骤

## 前置条件
- 已安装 Git（已安装：git version 2.55.0.windows.3）
- 本地仓库已初始化并提交（40 个文件，commit: f7d758e）

## 发布步骤

### 1. 在 GitHub 网页上创建空仓库

1. 访问 https://github.com/new
2. 仓库名填写：**TempMonitor**
3. 描述填写：Win11 桌面硬件温度监控悬浮窗
4. 选择 **Public**（公开）
5. **不要勾选** "Add a README" 和 ".gitignore"（我们已有）
6. 点击 **Create repository**

### 2. 复制并运行推送命令

创建完成后，GitHub 会显示如下命令，复制并依次在终端运行：

```powershell
# 先设置你的 GitHub 用户名
git config --global user.name "你的GitHub用户名"

# 添加远程仓库地址（替换 Jason-Zhong 为你的 GitHub 用户名）
git remote add origin https://github.com/Jason-Zhong/TempMonitor.git

# 推送到 GitHub
git push -u origin master
```

### 3. 创建 Release（可选）

```powershell
# 登录 GitHub CLI
gh auth login

# 创建 Release 并上传 exe
gh release create v1.0.0 dist/TempMonitor.exe --title "TempMonitor v1.0" --notes "首个发布版本 - CPU/内存/主板温度监控悬浮窗"
```

> 如果 gh CLI 登录反复失败，可以直接在 GitHub 网页上操作：
> 1. 进入仓库页面 → **Releases** → **Create a new release**
> 2. 标签填 `v1.0.0`，标题填 `TempMonitor v1.0`
> 3. 将 `dist/TempMonitor.exe` 拖拽上传作为附件
> 4. 点击 **Publish release**

## 项目目录结构

```
TempMonitor/
├── main.py                  # 主入口
├── config.py                # 配置管理器
├── hardware_service.py      # 硬件数据采集
├── requirements.txt         # Python 依赖
├── build.bat                # 打包脚本
├── README.md                # 项目说明
├── .gitignore
├── ui/
│   ├── overlay_window.py    # 悬浮窗 UI
│   ├── settings_window.py   # 设置对话框
│   └── tray_icon.py         # 系统托盘
├── libs/                    # 硬件监控依赖 DLL
└── dist/
    └── TempMonitor.exe      # 已编译的可执行文件
```
