@echo off
chcp 65001 > nul
title MyNovelBot 数据迁移工具

echo =================================
echo  MyNovelBot 数据迁移工具
echo =================================
echo.
echo 正在查找 Python 虚拟环境...

rem 进入后端目录以使用正确的 poetry 项目上下文
cd /d "%~dp0..\novel_bot"

rem 使用 poetry env info -p 获取虚拟环境的路径并存入变量
for /f "delims=" %%p in ('poetry env info --path') do (
    set "VENV_PATH=%%p"
)

if not defined VENV_PATH (
    echo [错误] 未能找到 Poetry 虚拟环境。
    echo        请先在 novel_bot 目录下运行 'poetry install'。
    pause
    exit /b 1
)

echo 找到虚拟环境: %VENV_PATH%
echo.

rem 定义 python.exe 的路径
set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    rem 兼容 Linux/macOS 的路径结构
    set "PYTHON_EXE=%VENV_PATH%\bin\python"
)

if not exist "%PYTHON_EXE%" (
    echo [错误] 在虚拟环境中找不到 python.exe 或 python。
    echo 路径: %PYTHON_EXE%
    pause
    exit /b 1
)

rem 返回到项目根目录
cd /d "%~dp0.."

echo 正在从项目根目录运行迁移脚本...
echo.

rem 直接调用虚拟环境中的 python 来执行脚本
call "%PYTHON_EXE%" tools/migrate_legacy_data.py

echo.
echo =================================
echo 迁移脚本执行完毕。
echo 请检查上面的日志输出确认是否成功。
echo 本窗口将在 10 秒后自动关闭...
echo =================================
echo.
timeout /t 10 /nobreak > nul
exit /b