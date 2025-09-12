@echo off
rem 设置代码页为UTF-8，以正确显示中文字符
chcp 65001 > nul
title MyNovelBot 稳定版启动器

echo ===================================
echo  MyNovelBot 稳定版启动器
echo ===================================
echo.

echo [步骤 1/3] 正在验证前端文件...
if not exist "%~dp0web-ui\dist-stable\index.html" goto file_error
echo           前端文件验证通过。
echo.
goto start_services

:file_error
echo [严重错误] 找不到前端文件 (dist-stable\index.html)!
echo           请先运行 build.bat 构建前端。
pause
exit /b 1

:start_services
echo [步骤 2/3] 正在新窗口启动 MyNovelBot 后端 API 服务 (端口 8080)...
pushd "%~dp0novel_bot"
rem 设置为 API only 模式，让它不关心任何前端服务
set MYNOVELBOT_FRONTEND_MODE=api_only
start "MyNovelBot Backend API" python main.py
popd
echo.

echo [步骤 3/3] 正在新窗口启动前端静态文件服务器 (端口 8000)...
pushd "%~dp0web-ui\dist-stable"
rem 使用 Python 内置模块启动一个简单的 HTTP 服务器
start "MyNovelBot Frontend Server" python -m http.server 8000
popd
echo.

echo ========================================================
echo  启动成功！
echo.
echo  [重要] 后端 API 运行在: http://localhost:8080
echo  [重要] 前端页面请访问: http://localhost:8000
echo ========================================================
echo.
echo 所有进程均已启动，本窗口将在 15 秒后自动关闭...
timeout /t 15 /nobreak > nul
exit