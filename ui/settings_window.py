"""
settings_window.py —— 设置对话框

模态 Toplevel 窗口，分"显示"和"高级"两个标签页，
提供所有可配置项的控件。修改通过回调让主窗口即时响应。
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from config import Config


class SettingsWindow:
    """设置对话框。"""

    def __init__(self, parent: tk.Tk, on_applied: Optional[Callable] = None):
        self._parent = parent
        self._on_applied = on_applied
        self._config = Config()
        self._window: Optional[tk.Toplevel] = None

    def open(self):
        """打开模态设置对话框。"""
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            return

        cfg = self._config

        self._window = tk.Toplevel(self._parent)
        self._window.title("TempMonitor 设置")
        self._window.geometry("420x380")
        self._window.resizable(False, False)
        self._window.transient(self._parent)
        self._window.grab_set()

        # 配色
        colors = cfg.get_colors()
        self._window.configure(bg=colors.get("bg", "#1a1a2e"))

        # Notebook 分页
        notebook = ttk.Notebook(self._window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # ----- 显示标签页 -----
        display_frame = tk.Frame(notebook, bg=colors.get("bg", "#1a1a2e"))
        notebook.add(display_frame, text="  显示  ")

        self._vars = {}
        row = 0

        # 刷新间隔
        tk.Label(
            display_frame, text="刷新间隔:", anchor="w",
            bg=colors.get("bg"), fg=colors.get("fg"),
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky="w", padx=12, pady=(12, 4))
        interval_map = {"1s": 1000, "2s": 2000, "3s": 3000, "5s": 5000, "10s": 10000}
        inv_rev = {v: k for k, v in interval_map.items()}
        current_interval = inv_rev.get(cfg.get("refresh_interval", 2000), "2s")
        interval_var = tk.StringVar(value=current_interval)
        self._vars["refresh_interval"] = interval_var
        cb = ttk.Combobox(
            display_frame, textvariable=interval_var,
            values=list(interval_map.keys()), state="readonly", width=10,
        )
        cb.grid(row=row, column=1, sticky="w", padx=12, pady=(12, 4))
        row += 1

        # 窗口透明度
        tk.Label(
            display_frame, text="窗口透明度:", anchor="w",
            bg=colors.get("bg"), fg=colors.get("fg"),
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky="w", padx=12, pady=4)
        opacity_frame = tk.Frame(display_frame, bg=colors.get("bg"))
        opacity_frame.grid(row=row, column=1, sticky="ew", padx=12, pady=4)
        opacity_var = tk.DoubleVar(value=int(cfg.get("window_opacity", 0.88) * 100))
        self._vars["window_opacity"] = opacity_var
        scale = ttk.Scale(
            opacity_frame, from_=50, to=100, variable=opacity_var,
            orient="horizontal", length=120,
        )
        scale.pack(side="left")
        opacity_label = tk.Label(
            opacity_frame, text=f"{int(opacity_var.get())}%",
            bg=colors.get("bg"), fg=colors.get("fg"),
            font=("Segoe UI", 9),
        )
        opacity_label.pack(side="left", padx=(6, 0))

        def _update_opacity_label(*_):
            opacity_label.config(text=f"{int(opacity_var.get())}%")
        opacity_var.trace_add("write", _update_opacity_label)
        row += 1

        # 字体大小
        tk.Label(
            display_frame, text="字体大小:", anchor="w",
            bg=colors.get("bg"), fg=colors.get("fg"),
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky="w", padx=12, pady=4)
        font_var = tk.StringVar(value=cfg.get("font_size", "中"))
        self._vars["font_size"] = font_var
        ttk.Combobox(
            display_frame, textvariable=font_var,
            values=["小", "中", "大"], state="readonly", width=10,
        ).grid(row=row, column=1, sticky="w", padx=12, pady=4)
        row += 1

        # 颜色主题
        tk.Label(
            display_frame, text="颜色主题:", anchor="w",
            bg=colors.get("bg"), fg=colors.get("fg"),
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky="w", padx=12, pady=4)
        theme_var = tk.StringVar(value=cfg.get("color_theme", "深色"))
        self._vars["color_theme"] = theme_var
        ttk.Combobox(
            display_frame, textvariable=theme_var,
            values=["深色", "浅色"], state="readonly", width=10,
        ).grid(row=row, column=1, sticky="w", padx=12, pady=4)
        row += 1

        # 始终置顶
        top_var = tk.BooleanVar(value=cfg.get("always_on_top", True))
        self._vars["always_on_top"] = top_var
        tk.Checkbutton(
            display_frame, text="窗口始终置顶", variable=top_var,
            bg=colors.get("bg"), fg=colors.get("fg"),
            selectcolor=colors.get("card_bg"), activebackground=colors.get("bg"),
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 12))
        row += 1

        # 让第二列可拉伸
        display_frame.columnconfigure(1, weight=1)

        # ----- 高级标签页 -----
        adv_frame = tk.Frame(notebook, bg=colors.get("bg", "#1a1a2e"))
        notebook.add(adv_frame, text="  高级  ")

        row2 = 0
        # 显示 CPU 进度条
        cpu_bar_var = tk.BooleanVar(value=cfg.get("show_cpu_bar", True))
        self._vars["show_cpu_bar"] = cpu_bar_var
        tk.Checkbutton(
            adv_frame, text="显示 CPU 负载进度条", variable=cpu_bar_var,
            bg=colors.get("bg"), fg=colors.get("fg"),
            selectcolor=colors.get("card_bg"), activebackground=colors.get("bg"),
            font=("Segoe UI", 10),
        ).grid(row=row2, column=0, sticky="w", padx=12, pady=(12, 4))
        row2 += 1

        # 显示内存行
        mem_row_var = tk.BooleanVar(value=cfg.get("show_memory_row", True))
        self._vars["show_memory_row"] = mem_row_var
        tk.Checkbutton(
            adv_frame, text="显示内存使用率行", variable=mem_row_var,
            bg=colors.get("bg"), fg=colors.get("fg"),
            selectcolor=colors.get("card_bg"), activebackground=colors.get("bg"),
            font=("Segoe UI", 10),
        ).grid(row=row2, column=0, sticky="w", padx=12, pady=4)
        row2 += 1

        # 显示主板温度
        mb_row_var = tk.BooleanVar(value=cfg.get("show_motherboard_row", True))
        self._vars["show_motherboard_row"] = mb_row_var
        tk.Checkbutton(
            adv_frame, text="显示主板温度行", variable=mb_row_var,
            bg=colors.get("bg"), fg=colors.get("fg"),
            selectcolor=colors.get("card_bg"), activebackground=colors.get("bg"),
            font=("Segoe UI", 10),
        ).grid(row=row2, column=0, sticky="w", padx=12, pady=4)
        row2 += 1

        # 开机自启
        auto_var = tk.BooleanVar(value=cfg.get("autostart", False))
        self._vars["autostart"] = auto_var
        tk.Checkbutton(
            adv_frame, text="开机自动启动", variable=auto_var,
            bg=colors.get("bg"), fg=colors.get("fg"),
            selectcolor=colors.get("card_bg"), activebackground=colors.get("bg"),
            font=("Segoe UI", 10),
        ).grid(row=row2, column=0, sticky="w", padx=12, pady=(4, 12))

        # ----- 底部按钮 -----
        btn_frame = tk.Frame(self._window, bg=colors.get("bg"))
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))

        btn_style = {"font": ("Segoe UI", 10), "padx": 16, "pady": 4, "cursor": "hand2"}

        def do_ok():
            self._apply()
            self._close()

        def do_cancel():
            self._close()

        def do_apply():
            self._apply()

        tk.Button(btn_frame, text="确定", command=do_ok, **btn_style).pack(side="right", padx=(4, 0))
        tk.Button(btn_frame, text="应用", command=do_apply, **btn_style).pack(side="right", padx=4)
        tk.Button(btn_frame, text="取消", command=do_cancel, **btn_style).pack(side="right", padx=4)

        # 窗口关闭事件
        self._window.protocol("WM_DELETE_WINDOW", self._close)

        # 居中显示
        self._window.update_idletasks()
        pw, ph = self._parent.winfo_width(), self._parent.winfo_height()
        px, py = self._parent.winfo_x(), self._parent.winfo_y()
        ww, wh = 420, 380
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2
        self._window.geometry(f"{ww}x{wh}+{x}+{y}")

    def _apply(self):
        """将界面控件值写入 Config 并触发回调。"""
        interval_map = {"1s": 1000, "2s": 2000, "3s": 3000, "5s": 5000, "10s": 10000}
        changes = {}

        changes["refresh_interval"] = interval_map.get(
            self._vars["refresh_interval"].get(), 2000
        )
        changes["window_opacity"] = round(
            self._vars["window_opacity"].get() / 100, 2
        )
        changes["font_size"] = self._vars["font_size"].get()
        changes["color_theme"] = self._vars["color_theme"].get()
        changes["always_on_top"] = self._vars["always_on_top"].get()
        changes["show_cpu_bar"] = self._vars["show_cpu_bar"].get()
        changes["show_memory_row"] = self._vars["show_memory_row"].get()
        changes["show_motherboard_row"] = self._vars["show_motherboard_row"].get()
        changes["autostart"] = self._vars["autostart"].get()

        self._config.set_many(changes)

        # 处理开机自启（与 tray 功能联动）
        if self._vars["autostart"].get():
            from ui.tray_icon import _set_autostart
            _set_autostart(True)
        else:
            from ui.tray_icon import _set_autostart
            _set_autostart(False)

        if self._on_applied:
            self._on_applied()

    def _close(self):
        if self._window and self._window.winfo_exists():
            try:
                self._window.grab_release()
            except Exception:
                pass
            self._window.destroy()
        self._window = None
