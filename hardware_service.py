"""
hardware_service.py —— 硬件数据采集层

封装 LibreHardwareMonitorLib + psutil，提供 CPU 温度、内存使用率、主板温度等数据。
"""

import os
import sys
import psutil
from typing import Optional, Dict, Any


class HardwareService:
    """硬件监控服务，通过 LibreHardwareMonitorLib 采集传感器数据。"""

    def __init__(self):
        self._computer = None
        self._initialized = False
        self._error = None

    def initialize(self) -> bool:
        """初始化 LibreHardwareMonitorLib。返回 True 表示成功。"""
        try:
            # 计算 DLL 路径 —— 支持开发环境和打包后的路径
            dll_path = self._find_dll()
            if not dll_path:
                self._error = "找不到 LibreHardwareMonitorLib.dll"
                return False

            self._libs_dir = os.path.dirname(dll_path)

            import clr
            import System

            # 注册 AssemblyResolve 事件 —— 自动从 libs 目录加载依赖
            def _resolve(sender, args):
                name = args.Name.split(",")[0]
                dll_path_candidate = os.path.join(self._libs_dir, name + ".dll")
                if os.path.isfile(dll_path_candidate):
                    return System.Reflection.Assembly.LoadFrom(dll_path_candidate)
                return None

            System.AppDomain.CurrentDomain.AssemblyResolve += _resolve

            # 加载主 DLL
            clr.AddReference(dll_path)

            from LibreHardwareMonitor.Hardware import Computer

            self._computer = Computer()
            self._computer.IsCpuEnabled = True
            self._computer.IsMemoryEnabled = True
            self._computer.IsMotherboardEnabled = True
            self._computer.Open()

            self._initialized = True
            return True

        except Exception as e:
            self._error = f"硬件监控初始化失败: {e}"
            self._initialized = False
            return False

    def _find_dll(self) -> Optional[str]:
        """查找 DLL 文件的完整路径。
        
        优先使用 net472 版本（Win11 内置 .NET Framework 4.8，兼容性好），
        其次尝试 netstandard2.0 版本。
        """
        # 搜索顺序：net472 > netstandard2.0
        dll_names = ["LibreHardwareMonitorLib.net472.dll", "LibreHardwareMonitorLib.dll"]
        search_dirs = [
            os.path.join(os.path.dirname(__file__), "libs"),
            os.path.join(os.path.dirname(__file__), "..", "libs"),
            os.path.join(sys._MEIPASS, "libs") if getattr(sys, 'frozen', False) else None,
        ]
        for dll_name in dll_names:
            for d in search_dirs:
                if d:
                    p = os.path.join(d, dll_name)
                    if os.path.isfile(p):
                        return p
        return None

    @staticmethod
    def _try_add_reference(libs_dir: str, dll_name: str):
        """尝试加载依赖 DLL，如果文件存在的话。"""
        dll_path = os.path.join(libs_dir, dll_name)
        if os.path.isfile(dll_path):
            try:
                import clr
                clr.AddReference(dll_path)
            except Exception:
                pass  # 有些依赖可能已加载，忽略

    def get_sensors(self) -> Dict[str, Any]:
        """
        采集所有传感器数据，返回结构化字典。

        返回格式：
        {
            "cpu": {
                "temperature": 45.0,           # CPU 封装温度 (°C)
                "core_temperatures": [45.0, ...],  # 各核心温度
                "load": 23.5,                   # CPU 总负载 (%)
                "core_loads": [23.5, ...],       # 各核心负载
                "power": 65.0,                  # CPU 功耗 (W)
            },
            "memory": {
                "used": 8_123_456_789,          # 已用内存 (bytes)
                "total": 16_123_456_789,        # 总内存 (bytes)
                "percent": 50.3,                 # 使用率 (%)
            },
            "motherboard": {
                "temperature": 35.0,            # 主板温度 (°C)
            },
            "error": None,                      # 错误信息
        }
        """
        result = {
            "cpu": {"temperature": None, "core_temperatures": [], "load": None, "core_loads": [], "power": None},
            "memory": {"used": None, "total": None, "percent": None},
            "motherboard": {"temperature": None},
            "error": None,
        }

        # ----- psutil 内存数据（可靠的后备） -----
        try:
            mem = psutil.virtual_memory()
            result["memory"]["total"] = mem.total
            result["memory"]["used"] = mem.used
            result["memory"]["percent"] = round(mem.percent, 1)
        except Exception as e:
            result["error"] = f"psutil 内存读取失败: {e}"

        # ----- LibreHardwareMonitorLib 传感器数据 -----
        if not self._initialized or not self._computer:
            return result

        try:
            for hardware in self._computer.Hardware:
                hardware.Update()
                hw_type = str(hardware.HardwareType)

                hw_type_lower = hw_type.lower()

                if "cpu" in hw_type_lower:
                    self._parse_cpu_sensors(hardware, result)

                elif "memory" in hw_type_lower or "ram" in hw_type_lower:
                    self._parse_memory_sensors(hardware, result)

                elif "motherboard" in hw_type_lower or "board" in hw_type_lower or "superio" in hw_type_lower:
                    self._parse_motherboard_sensors(hardware, result)

                # 也检查子硬件（如 CPU 核心）
                for sub in getattr(hardware, 'SubHardware', []):
                    sub.Update()
                    sub_type = str(sub.HardwareType)
                    if "cpu" in sub_type.lower():
                        self._parse_cpu_sensors(sub, result, is_subhardware=True)

        except Exception as e:
            result["error"] = f"传感器读取失败: {e}"

        return result

    def _parse_cpu_sensors(self, hardware, result: dict, is_subhardware: bool = False):
        """解析 CPU 硬件传感器的数据。"""
        from LibreHardwareMonitor.Hardware import SensorType

        for sensor in hardware.Sensors:
            if sensor.Value is None:
                continue
            sensor_type = str(sensor.SensorType)
            sensor_name = str(sensor.Name)

            if "Temperature" in sensor_type:
                val = round(float(sensor.Value), 1)
                # 封装温度或核心温度
                if "Package" in sensor_name or "Core (T" in sensor_name:
                    if result["cpu"]["temperature"] is None:
                        result["cpu"]["temperature"] = val
                elif is_subhardware or "Core" in sensor_name or "CPU Core" in sensor_name:
                    result["cpu"]["core_temperatures"].append(val)
                    if result["cpu"]["temperature"] is None:
                        result["cpu"]["temperature"] = val

            elif "Load" in sensor_type:
                val = round(float(sensor.Value), 1)
                if "Total" in sensor_name:
                    result["cpu"]["load"] = val
                elif "#" in sensor_name and "Core" in sensor_name:
                    result["cpu"]["core_loads"].append(val)
                    if result["cpu"]["load"] is None:
                        result["cpu"]["load"] = val

            elif "Power" in sensor_type:
                if "Package" in sensor_name or "CPU Package" in sensor_name:
                    result["cpu"]["power"] = round(float(sensor.Value), 1)

    def _parse_memory_sensors(self, hardware, result: dict):
        """解析内存硬件传感器的数据（补充 psutil 数据）。"""
        from LibreHardwareMonitor.Hardware import SensorType

        for sensor in hardware.Sensors:
            if sensor.Value is None:
                continue
            sensor_type = str(sensor.SensorType)
            sensor_name = str(sensor.Name)

            if "Load" in sensor_type and result["memory"]["percent"] is None:
                result["memory"]["percent"] = round(float(sensor.Value), 1)

    def _parse_motherboard_sensors(self, hardware, result: dict):
        """解析主板硬件传感器的数据。"""
        from LibreHardwareMonitor.Hardware import SensorType

        for sensor in hardware.Sensors:
            if sensor.Value is None:
                continue
            sensor_type = str(sensor.SensorType)

            if "Temperature" in sensor_type:
                val = round(float(sensor.Value), 1)
                if result["motherboard"]["temperature"] is None:
                    result["motherboard"]["temperature"] = val

    def close(self):
        """关闭硬件监控。"""
        if self._computer:
            try:
                self._computer.Close()
            except Exception:
                pass
            self._computer = None
            self._initialized = False

    @property
    def error(self) -> Optional[str]:
        return self._error

    def __del__(self):
        self.close()
