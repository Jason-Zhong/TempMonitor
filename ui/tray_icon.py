"""
tray_icon.py —— 系统托盘管理

使用 pystray 创建系统托盘图标，提供菜单控制：显示/隐藏、开机自启设置、退出。
"""

import os
import sys
import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw, ImageFont


def _create_tray_image() -> Image.Image:
    """创建托盘图标 —— 一个简洁的芯片图标。"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 芯片主体（圆角矩形）
    margin = 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=8,
        fill=(26, 26, 46, 255),
        outline=(15, 52, 96, 255),
        width=3,
    )

    # 温度计符号（中间竖线 + 底部圆点）
    cx = size // 2
    # 竖线
    draw.rectangle(
        [cx - 3, 18, cx + 3, 38],
        fill=(76, 175, 80, 255),
    )
    # 圆点
    draw.ellipse(
        [cx - 6, 34, cx + 6, 46],
        fill=(76, 175, 80, 255),
    )

    # 两侧的小引脚
    for y_offset in [18, 28, 38]:
        draw.rectangle([4, y_offset, margin - 2, y_offset + 3], fill=(100, 150, 200, 200))
        draw.rectangle([size - margin + 2, y_offset, size - 4, y_offset + 3], fill=(100, 150, 200, 200))

    return img


def _get_startup_shortcut_path() -> str:
    """获取启动文件夹中的快捷方式路径。"""
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )
    return os.path.join(startup_dir, "TempMonitor.lnk")


def _is_autostart_enabled() -> bool:
    """检查是否已启用开机自启（通过注册表）。"""
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ,
        )
        value, _ = winreg.QueryValueEx(key, "TempMonitor")
        winreg.CloseKey(key)
        return bool(value)
    except (FileNotFoundError, OSError):
        return False


def _set_autostart(enabled: bool, exe_path: Optional[str] = None):
    """设置/取消开机自启（通过注册表 HKCU Run）。"""
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE | winreg.KEY_READ,
    )
    try:
        if enabled:
            target = exe_path or sys.executable
            # 如果是 Python 脚本，需要加上脚本路径
            if getattr(sys, 'frozen', False):
                full_cmd = f'"{target}"'
            else:
                script = os.path.abspath(sys.argv[0])
                full_cmd = f'"{target}" "{script}"'
            winreg.SetValueEx(key, "TempMonitor", 0, winreg.REG_SZ, full_cmd)
        else:
            try:
                winreg.DeleteValue(key, "TempMonitor")
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


class TrayIcon:
    """系统托盘图标控制器。"""

    def __init__(
        self,
        on_toggle: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        self.on_toggle = on_toggle
        self.on_settings = on_settings
        self.on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _build_menu(self):
        """构建右键菜单。"""
        autostart = _is_autostart_enabled()

        def toggle_show(icon, item):
            if self.on_toggle:
                self.on_toggle()

        def toggle_autostart(icon, item):
            new_state = not autostart
            _set_autostart(new_state)
            # 重建菜单以反映状态变化
            self._icon.menu = self._build_menu()

        def do_quit(icon, item):
            if self.on_quit:
                self.on_quit()

        def do_settings(icon, item):
            if self.on_settings:
                self.on_settings()

        return pystray.Menu(
            pystray.MenuItem("显示 / 隐藏", toggle_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("设置...", do_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "开机自启",
                toggle_autostart,
                checked=lambda item: autostart,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", do_quit),
        )

    def start(self):
        """在后台线程中启动托盘图标。"""
        if self._icon is not None:
            return

        image = _create_tray_image()
        self._icon = pystray.Icon(
            "TempMonitor",
            image,
            "TempMonitor - 硬件温度监控",
            menu=self._build_menu(),
        )

        def run_icon():
            try:
                self._icon.run()
            except Exception as e:
                print(f"[TrayIcon] 托盘运行失败: {e}")

        self._thread = threading.Thread(target=run_icon, daemon=True)
        self._thread.start()

    def stop(self):
        """停止托盘图标。"""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
            self._thread = None

    def notify(self, title: str, message: str):
        """显示通知气泡。"""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass
