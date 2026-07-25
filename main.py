"""
main.py —— TempMonitor 主入口

整合硬件服务、设置管理器、悬浮窗 UI、系统托盘。
支持通过设置窗口动态调整所有配置项。
"""

import sys
import os

_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config import Config
from hardware_service import HardwareService
from ui.overlay_window import OverlayWindow
from ui.settings_window import SettingsWindow
from ui.tray_icon import TrayIcon, _set_autostart, _is_autostart_enabled

# 默认刷新间隔（毫秒）
DEFAULT_REFRESH_MS = 2000


class TempMonitorApp:
    """应用主控制器。"""

    def __init__(self):
        self._config = Config()
        self._hw_service = HardwareService()
        self._overlay: OverlayWindow = None
        self._tray: TrayIcon = None
        self._settings: SettingsWindow = None
        self._running = True
        self._refresh_interval = self._config.get("refresh_interval", DEFAULT_REFRESH_MS)

    def initialize(self) -> bool:
        """初始化所有组件。返回 True 表示成功。"""
        # 1. 初始化硬件服务
        hw_ok = self._hw_service.initialize()
        if not hw_ok:
            print(f"[警告] 硬件监控初始化失败: {self._hw_service.error}")
            print("[信息] 将使用 psutil 提供有限的内存数据")

        # 2. 创建设置窗口（不立即显示）
        self._settings = SettingsWindow(
            parent=None,  # 延迟绑定 parent
            on_applied=self._on_settings_applied,
        )

        # 3. 创建悬浮窗
        self._overlay = OverlayWindow(
            on_settings=self._on_open_settings,
            on_close=self._on_window_close,
        )

        # 设置窗口的 parent 为悬浮窗
        self._settings._parent = self._overlay.window

        # 4. 创建托盘
        self._tray = TrayIcon(
            on_toggle=self._on_tray_toggle,
            on_settings=self._on_open_settings,
            on_quit=self._on_tray_quit,
        )

        # 5. 同步配置中的开机自启状态到注册表
        if self._config.get("autostart", False):
            _set_autostart(True)
        elif _is_autostart_enabled():
            _set_autostart(False)

        return True

    def run(self):
        """启动应用。"""
        # 启动托盘
        try:
            self._tray.start()
        except Exception as e:
            print(f"[警告] 托盘图标启动失败: {e}")

        # 启动定时刷新
        self._schedule_refresh()

        # 进入 tkinter 主循环
        try:
            self._overlay.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _schedule_refresh(self):
        """安排下一次数据刷新。"""
        if not self._running:
            return
        try:
            data = self._hw_service.get_sensors()
            if self._overlay:
                self._overlay.update_data(data)
        except Exception as e:
            print(f"[错误] 数据刷新失败: {e}")
        finally:
            if self._running and self._overlay:
                try:
                    interval = self._config.get("refresh_interval", DEFAULT_REFRESH_MS)
                    self._overlay.window.after(interval, self._schedule_refresh)
                except Exception:
                    self._running = False

    # ---- 设置窗口 ----

    def _on_open_settings(self):
        """打开设置窗口。"""
        if self._settings:
            self._settings.open()

    def _on_settings_applied(self):
        """设置被应用时的回调。"""
        # 刷新间隔会在下次 _schedule_refresh 时自动读取新值
        pass

    # ---- 事件处理 ----

    def _on_window_close(self):
        """悬浮窗关闭：最小化到托盘。"""
        if self._overlay:
            self._overlay.hide()

    def _on_tray_toggle(self):
        """托盘图标点击：显示/隐藏悬浮窗。"""
        if self._overlay:
            self._overlay.toggle_visibility()

    def _on_tray_quit(self):
        """托盘退出。"""
        self._cleanup()
        try:
            os._exit(0)
        except Exception:
            sys.exit(0)

    def _cleanup(self):
        """清理所有资源。"""
        self._running = False
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        if self._hw_service:
            try:
                self._hw_service.close()
            except Exception:
                pass
        if self._overlay:
            try:
                self._overlay.quit()
            except Exception:
                pass


def main():
    """应用入口函数。"""
    app = TempMonitorApp()
    if app.initialize():
        app.run()
    else:
        print("TempMonitor 初始化失败，请检查系统配置。")
        input("按 Enter 键退出...")


if __name__ == "__main__":
    main()
