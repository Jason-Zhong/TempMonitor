"""
config.py —— 配置管理器

用 JSON 文件存储用户设置到 %APPDATA%/TempMonitor/settings.json。
提供加载/保存/监听回调功能。
"""

import os
import json
from typing import Any, Callable, Dict, Optional

# 默认配置
DEFAULTS = {
    "refresh_interval": 2000,           # 刷新间隔 (ms)
    "window_opacity": 0.88,             # 窗口透明度 (0.5-1.0)
    "font_size": "中",                  # 小/中/大
    "always_on_top": True,              # 置顶
    "autostart": False,                 # 开机自启
    "show_cpu_bar": True,               # 显示 CPU 进度条
    "show_memory_row": True,            # 显示内存行
    "show_motherboard_row": True,       # 显示主板温度行
    "color_theme": "深色",              # 深色/浅色
}

# 字体大小映射
FONT_SIZES = {
    "小": {"base": 9, "title": 10, "big": 12},
    "中": {"base": 11, "title": 12, "big": 14},
    "大": {"base": 13, "title": 14, "big": 16},
}

# 主题配色
THEMES = {
    "深色": {
        "bg": "#1a1a2e",
        "card_bg": "#16213e",
        "border": "#0f3460",
        "fg": "#e0e0e0",
        "sub_fg": "#667788",
        "title_fg": "#8899aa",
        "bar_bg": "#2a2a4a",
        "btn_bg": "#0f3460",
        "btn_fg": "#e0e0e0",
    },
    "浅色": {
        "bg": "#f5f5f5",
        "card_bg": "#ffffff",
        "border": "#d0d0d0",
        "fg": "#333333",
        "sub_fg": "#888888",
        "title_fg": "#555555",
        "bar_bg": "#e0e0e0",
        "btn_bg": "#e0e0e0",
        "btn_fg": "#333333",
    },
}


def _get_config_dir() -> str:
    """获取配置目录路径。"""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = os.path.join(appdata, "TempMonitor")
    os.makedirs(path, exist_ok=True)
    return path


def _get_config_path() -> str:
    """获取配置文件路径。"""
    return os.path.join(_get_config_dir(), "settings.json")


class Config:
    """配置管理器，单例模式。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data: Dict[str, Any] = {}
        self._callbacks: list[Callable] = []
        self.load()

    # ---- 读写接口 ----

    def load(self):
        """从 JSON 文件加载配置，缺失项用默认值填充。"""
        self._data = dict(DEFAULTS)
        path = _get_config_path()
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass  # 文件损坏时回退到默认值

    def save(self):
        """保存配置到 JSON 文件。"""
        path = _get_config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[Config] 保存配置失败: {e}")

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项并持久化，触发回调。"""
        if key in self._data and self._data[key] == value:
            return
        self._data[key] = value
        self.save()
        self._notify(key)

    def set_many(self, items: Dict[str, Any]):
        """批量设置配置项。"""
        changed = False
        for k, v in items.items():
            if k in self._data and self._data[k] == v:
                continue
            self._data[k] = v
            changed = True
        if changed:
            self.save()
            self._notify(None)

    # ---- 监听 ----

    def on_change(self, callback: Callable[[Optional[str]], Any]):
        """注册配置变更回调。参数是变更的 key，None 表示批量变更。"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify(self, key: Optional[str]):
        for cb in self._callbacks:
            try:
                cb(key)
            except Exception as e:
                print(f"[Config] 回调异常: {e}")

    # ---- 实用方法 ----

    def get_colors(self) -> dict:
        """获取当前主题的配色字典。"""
        theme = self._data.get("color_theme", "深色")
        return THEMES.get(theme, THEMES["深色"])

    def get_font_size(self) -> dict:
        """获取当前字体大小配置。"""
        size = self._data.get("font_size", "中")
        return FONT_SIZES.get(size, FONT_SIZES["中"])

    @property
    def data(self) -> Dict[str, Any]:
        return dict(self._data)

    def reset(self):
        """重置为默认值。"""
        self._data = dict(DEFAULTS)
        self.save()
        self._notify("__reset__")
