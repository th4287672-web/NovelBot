@echo off
rem 设置代码页为UTF-8，以正确显示中文字符
chcp 65001 > nul
title MyNovelBot Frontend Builder for Stable Release

echo ===========================================
echo  MyNovelBot 稳定版前端构建器 (build.bat)
echo ===========================================
echo.

echo [1/3] 正在清理旧的构建产物...
cd /d "%~dp0web-ui"
if exist .output rmdir /s /q .output
if exist dist-stable rmdir /s /q dist-stable
echo      旧的 '.output' 和 'dist-stable' 目录已清理。
echo.

echo [2/3] 正在生成新的前端静态文件 (Nuxt Generate)...
echo      这可能需要一分钟左右的时间，请稍候。
call pnpm generate
if errorlevel 1 (
    echo.
    echo [严重错误] 前端静态文件生成失败^!
    echo           请检查上面的错误日志。
    pause
    exit /b 1
)
echo      前端静态文件生成成功！
echo.

echo [3/3] 正在将构建产物部署到稳定版目录 (dist-stable)...
set SOURCE_DIR="%~dp0web-ui\.output\public"
set DEST_DIR="%~dp0web-ui\dist-stable"

echo      正在复制构建产物...
xcopy %SOURCE_DIR% %DEST_DIR%\ /E /I /Q /Y

if errorlevel 1 (
    echo [严重错误] 复制文件失败^!
    pause
    exit /b 1
)
echo      文件已成功部署。
echo.


echo =============================================================
echo ==  稳定版前端构建并部署成功！                           ==
echo ==  'web-ui\dist-stable' 目录已更新。                      ==
echo ==  您现在可以将项目提交或分发给用户。                     ==
echo ==  用户可以使用 'run_stable.bat' 来启动这个稳定版本。   ==
echo =============================================================
echo.
pause