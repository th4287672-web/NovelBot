@echo off
rem MyNovelBot - 数据库重建工具启动脚本
rem 功能：从此项目中的 Poetry 虚拟环境启动数据库重建脚本。

chcp 65001 > nul
title MyNovelBot 数据库重建工具

echo =================================
echo  MyNovelBot 数据库重建工具
echo =================================
echo.
echo 警告：此脚本将引导您完成一个潜在的破坏性操作，
echo       即根据导出的文件覆盖现有的数据库。
echo.
pause
echo.
echo 正在查找 Python 虚拟环境...

rem 脚本所在的目录是 tools，所以 ..\novel_bot 指向后端目录
cd /d "%~dp0..\novel_bot"

rem 使用 poetry env info -p 获取虚拟环境的路径并存入变量
for /f "delims=" %%p in ('poetry env info --path') do (
    set "VENV_PATH=%%p"
)

if not defined VENV_PATH (
    echo [错误] 未能找到 Poetry 虚拟环境。
    echo        请先运行根目录的 install_dependencies.bat。
    pause
    exit /b 1
)

echo 找到虚拟环境路径。
echo.

rem 定义 python.exe 的路径
set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=%VENV_PATH%\bin\python"
)

if not exist "%PYTHON_EXE%" (
    echo [错误] 在虚拟环境中找不到 python.exe 或 python。
    pause
    exit /b 1
)

rem 返回到项目根目录
cd /d "%~dp0.."

echo 正在启动数据库重建脚本...
echo.

rem 直接调用虚拟环境中的 python 来执行新脚本
call "%PYTHON_EXE%" tools/rebuild_database_from_export.py

echo.
echo =================================
echo 脚本执行完毕。
echo =================================
echo.
pause