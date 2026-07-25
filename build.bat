@echo off
REM TempMonitor 打包脚本 — 使用 PyInstaller 打包为单文件 exe
chcp 65001 >nul

echo ========================================
echo   TempMonitor 打包工具
echo ========================================

REM 确保在项目根目录
cd /d "%~dp0"

REM 检查 PyInstaller
python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [安装] 正在安装 PyInstaller...
    pip install pyinstaller
)

echo [打包] 正在打包 TempMonitor...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "TempMonitor" ^
    --add-data "libs\LibreHardwareMonitorLib.dll;libs" ^
    --hidden-import clr ^
    --collect-all pythonnet ^
    --noconfirm ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 打包完成！
    echo 输出文件: dist\TempMonitor.exe
    echo 大小: 
    for %%I in (dist\TempMonitor.exe) do echo %%~zI 字节
) else (
    echo [失败] 打包出错，请检查输出信息。
    pause
)
