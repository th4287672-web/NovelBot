@echo off
chcp 65001 > nul
title MyNovelBot 依赖安装脚本

echo =================================
echo  MyNovelBot 依赖安装脚本
echo =================================
echo.

echo [1/2] 正在安装前端依赖 (web-ui)...
cd web-ui

echo      Detailed logs will be written to web-ui\pnpm-install.log
call pnpm install --reporter=verbose > pnpm-install.log 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [FATAL ERROR] Frontend dependency installation failed!
    echo.
    echo        Please check the 'pnpm-install.log' file in the 'web-ui' directory for details.
    echo        TIP: This can be caused by antivirus software. Try adding the project folder to the exclusion list.
    echo.
    pause
    exit /b 1
)

cd ..
echo [成功] 前端依赖安装完毕.
echo.

echo [2/2] 正在安装后端依赖 (novel_bot)...
cd novel_bot

echo      正在同步 pyproject.toml 与 poetry.lock 文件...
call poetry lock
if %errorlevel% neq 0 (
    echo.
    echo [错误] poetry lock 命令失败! 无法同步依赖锁定文件.
    echo        请检查 Poetry 安装和 pyproject.toml 文件内容.
    pause
    exit /b 1
)
echo      依赖锁定文件同步成功.
echo.

echo      正在检查 pyproject.toml 文件...
call poetry check
if %errorlevel% neq 0 (
    echo.
    echo [错误] pyproject.toml 文件内容无效! 请检查文件语法。
    pause
    exit /b 1
)
echo      pyproject.toml 文件有效。
echo.

echo      正在安装 Python 依赖 (包括开发工具)...
call poetry sync --with dev
if %errorlevel% neq 0 (
    echo.
    echo [错误] 后端依赖安装失败!
    echo        请检查 Python 和 Poetry 是否已根据 README 正确配置.
    pause
    exit /b 1
)
cd ..
echo [成功] 后端依赖安装完毕.
echo.

echo =================================
echo 所有依赖均已成功安装!
echo 本窗口将在 5 秒后自动关闭...
echo =================================
echo.

rem 使用 timeout 命令实现 5 秒后自动退出
timeout /t 5 /nobreak > nul
exit /b