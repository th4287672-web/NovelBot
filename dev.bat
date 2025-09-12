@echo off
setlocal
chcp 65001 > nul
title MyNovelBot 开发者启动器

echo ===========================================
echo  MyNovelBot 开发者启动器 (纯API模式)
echo ===========================================
echo.

echo [步骤 1/2] 正在新窗口启动 MyNovelBot Python 后端...
pushd "%~dp0novel_bot"
rem 设置环境变量，并直接运行 main.py
start "MyNovelBot Backend" cmd /c "set MYNOVELBOT_FRONTEND_MODE=api_only&& python main.py & pause"
popd
echo.

echo --- 正在等待后端 API (端口 8080) ---
:check_port
echo 正在检查端口 8080 是否已开始监听...
timeout /t 1 /nobreak > nul
netstat -ano | findstr ":8080" | findstr "LISTENING" > nul
if errorlevel 1 (
    echo 端口尚未就绪，正在重试...
    goto check_port
)
echo      后端 API 已就绪！
echo.

echo [步骤 2/2] 正在新窗口启动前端开发服务器...
pushd "%~dp0web-ui"
start "MyNovelBot Frontend (Dev Server)" cmd /k "pnpm dev"
popd
echo.

echo ===================================================================
echo  开发者模式启动成功！
echo.
echo  请在您的浏览器中访问: http://localhost:3000
echo ===================================================================
echo.
echo 所有进程均已启动，本窗口将在 15 秒后自动关闭...
timeout /t 15 /nobreak > nul
endlocal
exit /b