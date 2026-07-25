"""
overlay_window.py —— 桌面悬浮窗 UI（组件化版本）

半透明、置顶、可拖拽、无边框的硬件监控悬浮窗。
支持通过 Config 动态调整显示项、主题、字体等。
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

from config import Config


# 温度颜色方案
COLOR_OK = "#4CAF50"
COLOR_WARN = "#FF9800"
COLOR_CRIT = "#F44336"


def _temp_color(temp: Optional[float]) -> str:
    if temp is None:
        return "#e0e0e0"
    if temp >= 80:
        return COLOR_CRIT
    if temp >= 60:
        return COLOR_WARN
    return COLOR_OK


class OverlayWindow:
    """桌面悬浮窗 —— 组件化布局，支持配置驱动。"""

    def __init__(self, on_settings: Optional[Callable] = None, on_close: Optional[Callable] = None):
        self.on_settings = on_settings
        self.on_close = on_close
        self._config = Config()
        self._visible = True

        # 主窗口
        self.window = tk.Tk()
        self.window.title("TempMonitor")
        self.window.overrideredirect(True)
        self.window.configure(bg="#1a1a2e")

        self._apply_window_attrs()

        # 窗口尺寸
        self._win_width = 280
        self._win_height = 56  # 动态计算

        # 构建 UI
        self._build_ui()

        # 初始定位
        self._init_position()

        # 拖拽
        self._drag_data = {"x": 0, "y": 0}
        self._bind_drag(self.window)
        self._bind_drag(self._title_bar)

        # 右键菜单
        self._build_menu()

        # ESC 键
        self.window.bind("<Escape>", lambda e: self._on_close())

        # 监听配置变更
        self._config.on_change(self._on_config_changed)

        # 存储传感器数据
        self._sensors_data = {}

    def _apply_window_attrs(self):
        """根据当前配置设置窗口属性。"""
        cfg = self._config
        try:
            self.window.attributes("-alpha", cfg.get("window_opacity", 0.88))
            self.window.attributes("-topmost", cfg.get("always_on_top", True))
        except Exception:
            pass

    def _init_position(self):
        """定位到屏幕右上角。"""
        try:
            sw = self.window.winfo_screenwidth()
            sh = self.window.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080
        x = sw - self._win_width - 20
        y = 60
        self.window.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        """构建 UI 组件。"""
        self._colors = self._config.get_colors()
        self._font_sizes = self._config.get_font_size()

        # 主容器
        self._container = tk.Frame(self.window, bg=self._colors["bg"])
        self._container.pack(fill="both", expand=True)

        # ==== 标题栏 ====
        self._title_bar = tk.Frame(self._container, bg=self._colors["border"], height=28)
        self._title_bar.pack(fill="x")
        self._title_bar.pack_propagate(False)

        title_label = tk.Label(
            self._title_bar,
            text="TempMonitor",
            bg=self._colors["border"],
            fg=self._colors["title_fg"],
            font=("Segoe UI", self._font_sizes["base"], "bold"),
        )
        title_label.pack(side="left", padx=8)

        # 设置按钮
        self._btn_settings = tk.Button(
            self._title_bar, text="⚙",
            bg=self._colors["border"], fg=self._colors["title_fg"],
            bd=0, highlightthickness=0,
            activebackground=self._colors["btn_bg"],
            activeforeground=self._colors["btn_fg"],
            font=("Segoe UI", self._font_sizes["base"]),
            cursor="hand2",
            command=self._on_settings_click,
        )
        self._btn_settings.pack(side="right", padx=(0, 2), pady=1)

        # 关闭按钮
        self._btn_close = tk.Button(
            self._title_bar, text="✕",
            bg=self._colors["border"], fg=self._colors["title_fg"],
            bd=0, highlightthickness=0,
            activebackground="#F44336", activeforeground="#ffffff",
            font=("Segoe UI", self._font_sizes["base"]),
            cursor="hand2",
            command=self._on_close,
        )
        self._btn_close.pack(side="right", padx=(0, 4), pady=1)

        # ==== 内容区 ====
        self._content = tk.Frame(self._container, bg=self._colors["bg"])
        self._content.pack(fill="both", expand=True, padx=6, pady=4)

        # -- CPU 卡片 --
        self._cpu_frame = tk.Frame(self._content, bg=self._colors["card_bg"], bd=1, relief="solid", highlightbackground=self._colors["border"], highlightthickness=1)
        self._cpu_frame.pack(fill="x", pady=(0, 3))

        # CPU 第一行：温度 + 负载
        cpu_row1 = tk.Frame(self._cpu_frame, bg=self._colors["card_bg"])
        cpu_row1.pack(fill="x", padx=8, pady=(4, 0))
        self._cpu_temp_label = tk.Label(
            cpu_row1, text="CPU: --°C",
            bg=self._colors["card_bg"], fg=COLOR_OK,
            font=("Segoe UI", self._font_sizes["big"], "bold"),
            anchor="w",
        )
        self._cpu_temp_label.pack(side="left")
        self._cpu_load_label = tk.Label(
            cpu_row1, text="--%",
            bg=self._colors["card_bg"], fg=self._colors["fg"],
            font=("Segoe UI", self._font_sizes["big"]),
            anchor="e",
        )
        self._cpu_load_label.pack(side="right")

        # CPU 进度条（Canvas）
        self._cpu_bar_frame = tk.Frame(self._cpu_frame, bg=self._colors["card_bg"], height=12)
        self._cpu_bar_frame.pack(fill="x", padx=8, pady=(2, 0))
        self._cpu_bar_frame.pack_propagate(False)
        self._cpu_bar_canvas = tk.Canvas(
            self._cpu_bar_frame, height=10,
            bg=self._colors["bar_bg"], highlightthickness=0,
        )
        self._cpu_bar_canvas.pack(fill="x")
        self._cpu_bar_rect = self._cpu_bar_canvas.create_rectangle(
            0, 0, 0, 10,
            fill=COLOR_OK, outline="", tags="bar",
        )

        # CPU 底部信息：核心数 + 功耗
        self._cpu_sub_label = tk.Label(
            self._cpu_frame,
            text="",
            bg=self._colors["card_bg"], fg=self._colors["sub_fg"],
            font=("Segoe UI", self._font_sizes["base"] - 2),
            anchor="w",
        )
        self._cpu_sub_label.pack(fill="x", padx=8, pady=(0, 4))

        # -- 内存卡片（可选） --
        self._mem_frame = tk.Frame(self._content, bg=self._colors["card_bg"], bd=1, relief="solid", highlightbackground=self._colors["border"], highlightthickness=1)

        mem_row1 = tk.Frame(self._mem_frame, bg=self._colors["card_bg"])
        mem_row1.pack(fill="x", padx=8, pady=(4, 0))
        self._mem_label = tk.Label(
            mem_row1, text="MEM: --%",
            bg=self._colors["card_bg"], fg=self._colors["fg"],
            font=("Segoe UI", self._font_sizes["big"], "bold"),
            anchor="w",
        )
        self._mem_label.pack(side="left")
        self._mem_detail_label = tk.Label(
            mem_row1, text="--/--GB",
            bg=self._colors["card_bg"], fg=self._colors["sub_fg"],
            font=("Segoe UI", self._font_sizes["base"]),
            anchor="e",
        )
        self._mem_detail_label.pack(side="right")

        self._mem_bar_frame = tk.Frame(self._mem_frame, bg=self._colors["card_bg"], height=12)
        self._mem_bar_frame.pack(fill="x", padx=8, pady=(2, 4))
        self._mem_bar_frame.pack_propagate(False)
        self._mem_bar_canvas = tk.Canvas(
            self._mem_bar_frame, height=10,
            bg=self._colors["bar_bg"], highlightthickness=0,
        )
        self._mem_bar_canvas.pack(fill="x")
        self._mem_bar_rect = self._mem_bar_canvas.create_rectangle(
            0, 0, 0, 10,
            fill="#2196F3", outline="", tags="bar",
        )

        # -- 主板温度卡片（可选） --
        self._mb_frame = tk.Frame(self._content, bg=self._colors["card_bg"], bd=1, relief="solid", highlightbackground=self._colors["border"], highlightthickness=1)
        self._mb_label = tk.Label(
            self._mb_frame, text="主板: --°C",
            bg=self._colors["card_bg"], fg=self._colors["fg"],
            font=("Segoe UI", self._font_sizes["big"], "bold"),
            anchor="w",
        )
        self._mb_label.pack(fill="x", padx=8, pady=6)

        # 初始刷新可见性
        self._update_visibility()

        # 重新计算高度
        self._recalc_height()

    def _update_visibility(self):
        """根据配置显示/隐藏各卡片。"""
        cfg = self._config
        show_cpu_bar = cfg.get("show_cpu_bar", True)
        show_mem = cfg.get("show_memory_row", True)
        show_mb = cfg.get("show_motherboard_row", True)

        # CPU 进度条
        if show_cpu_bar:
            self._cpu_bar_frame.pack(fill="x", padx=8, pady=(2, 0))
        else:
            self._cpu_bar_frame.pack_forget()

        # 主板（必须先 pack，后面内存才能用 before 参数）
        if show_mb:
            self._mb_frame.pack(fill="x", pady=(0, 3))
        else:
            self._mb_frame.pack_forget()

        # 内存（插在主板前面，保持 CPU-内存-主板顺序）
        if show_mem:
            if show_mb:
                self._mem_frame.pack(fill="x", pady=(0, 3), before=self._mb_frame)
            else:
                self._mem_frame.pack(fill="x", pady=(0, 3))
        else:
            self._mem_frame.pack_forget()

    def _recalc_height(self):
        """根据可见卡片重新计算窗口高度。"""
        cfg = self._config
        show_cpu_bar = cfg.get("show_cpu_bar", True)
        show_mem = cfg.get("show_memory_row", True)
        show_mb = cfg.get("show_motherboard_row", True)

        h = 28  # 标题栏
        h += 4  # 内边距
        h += 48  # CPU 卡片基准高度
        if show_cpu_bar:
            h += 12  # 进度条
        h += 3  # 间距
        if show_mem:
            h += 44  # 内存卡片
            h += 3
        if show_mb:
            h += 28  # 主板卡片
            h += 3
        h += 4  # 底部内边距

        self._win_height = h
        try:
            self.window.geometry(f"{self._win_width}x{h}")
        except Exception:
            pass

    def _build_menu(self):
        """构建右键菜单。"""
        self._menu = tk.Menu(self.window, tearoff=0,
                             bg=self._colors.get("bg", "#1a1a2e"),
                             fg=self._colors.get("fg", "#e0e0e0"),
                             activebackground=self._colors.get("border", "#0f3460"),
                             activeforeground="#ffffff",
                             font=("Segoe UI", 9))

        self._menu.add_command(label="显示 / 隐藏", command=self._on_toggle_visible)
        self._menu.add_separator()
        self._menu.add_command(label="设置...", command=self._on_settings_click)
        self._menu.add_separator()
        self._menu.add_command(label="退出", command=self._on_close)

        self.window.bind("<Button-3>", self._show_menu)

    def _show_menu(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _on_toggle_visible(self):
        self.toggle_visibility()

    def _on_settings_click(self):
        if self.on_settings:
            self.on_settings()

    def _on_close(self):
        if self.on_close:
            self.on_close()
        else:
            self.hide()

    # ---- 拖拽 ----

    def _bind_drag(self, widget):
        widget.bind("<Button-1>", self._drag_start)
        widget.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        try:
            x = self.window.winfo_x() + dx
            y = self.window.winfo_y() + dy
            self.window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    # ---- 配置变更 ----

    def _on_config_changed(self, key: Optional[str]):
        """配置变更时刷新 UI。"""
        self._colors = self._config.get_colors()
        self._font_sizes = self._config.get_font_size()

        # 窗口属性
        self._apply_window_attrs()

        # 可见性
        self._update_visibility()
        self._recalc_height()

        # 如果有数据就刷新
        if self._sensors_data:
            self.update_data(self._sensors_data)

    # ---- 公共方法 ----

    def update_data(self, data: dict):
        """用传感器数据更新 UI。"""
        self._sensors_data = data
        self._colors = self._config.get_colors()
        self._font_sizes = self._config.get_font_size()

        cpu = data.get("cpu", {})
        memory = data.get("memory", {})
        mb = data.get("motherboard", {})

        # CPU 温度
        cpu_temp = cpu.get("temperature")
        cpu_load = cpu.get("load")
        temp_str = f"{cpu_temp:.1f}°C" if cpu_temp is not None else "--°C"
        load_str = f"{cpu_load:.0f}%" if cpu_load is not None else "--%"
        color = _temp_color(cpu_temp)

        self._cpu_temp_label.config(text=f"CPU: {temp_str}", fg=color)
        self._cpu_load_label.config(text=load_str)

        # CPU 进度条
        bar_width = self._cpu_bar_canvas.winfo_width() or (self._win_width - 20)
        fill_w = max(2, int(bar_width * min((cpu_load or 0), 100) / 100))
        self._cpu_bar_canvas.coords(self._cpu_bar_rect, 0, 0, fill_w, 10)
        self._cpu_bar_canvas.itemconfig(self._cpu_bar_rect, fill=color)

        # CPU 底部信息
        cpu_power = cpu.get("power")
        core_count = len(cpu.get("core_loads", []))
        parts = []
        if core_count:
            parts.append(f"⚡ {core_count} 核")
        if cpu_power is not None:
            parts.append(f"{cpu_power:.0f}W")
        self._cpu_sub_label.config(text="  ·  ".join(parts))

        # 内存
        mem_percent = memory.get("percent")
        mem_used_gb = (memory.get("used") or 0) / (1024 ** 3)
        mem_total_gb = (memory.get("total") or 1) / (1024 ** 3)
        mem_pct_str = f"{mem_percent:.0f}%" if mem_percent is not None else "--%"
        self._mem_label.config(text=f"MEM: {mem_pct_str}")
        self._mem_detail_label.config(text=f"{mem_used_gb:.1f}/{mem_total_gb:.1f}GB")

        # 内存进度条
        bar_width = self._mem_bar_canvas.winfo_width() or (self._win_width - 20)
        fill_w = max(2, int(bar_width * min((mem_percent or 0), 100) / 100))
        self._mem_bar_canvas.coords(self._mem_bar_rect, 0, 0, fill_w, 10)
        mem_color = COLOR_CRIT if (mem_percent or 0) >= 85 else "#2196F3"
        self._mem_bar_canvas.itemconfig(self._mem_bar_rect, fill=mem_color)

        # 主板温度
        mb_temp = mb.get("temperature")
        mb_str = f"{mb_temp:.1f}°C" if mb_temp is not None else "--°C"
        self._mb_label.config(text=f"主板: {mb_str}", fg=_temp_color(mb_temp))

        # 窗口标题显示温度
        if cpu_temp is not None:
            try:
                self.window.title(f"{cpu_temp:.0f}°C - TempMonitor")
            except Exception:
                pass

    def show(self):
        try:
            self.window.deiconify()
        except Exception:
            pass
        self._visible = True

    def hide(self):
        try:
            self.window.withdraw()
        except Exception:
            pass
        self._visible = False

    def toggle_visibility(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def visible(self) -> bool:
        return self._visible

    def run(self):
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            pass

    def quit(self):
        try:
            self.window.quit()
            self.window.destroy()
        except Exception:
            pass
