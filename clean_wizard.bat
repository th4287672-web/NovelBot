@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: MyNovelBot 清理向导 (Clean Wizard) v8.0 (汉化)
:: =============================================================================
:: 描述: 一站式、强力的清理脚本，用于解决 MyNovelBot 项目的各种疑难杂症。
::
:: v8.0 更新:
:: - 用户要求在保留原有一键安全模式的同时，单独剥离“彻底删除
::   pnpm 全局执行缓存”的核弹级选项，为用户提供更精细的风险控制。
:: - 修复部分子函数的调用问题，确保所有子程序均使用 `call` 关键字。
:: [核心新增 v8.1] 在清理 novel_bot 时，一并删除 poetry.lock 文件。
:: =============================================================================

:main_menu
cls
echo.
echo ============================================================================
echo                 MyNovelBot 清理向导 v8.1 (汉化)
echo ============================================================================
echo.
echo   请选择需要执行的清理任务 (可多选, 例如: 1,3):
echo.
echo   --- 推荐流程 ---
echo   [1] 清理 pnpm 全局缓存 (安全模式, 推荐)
echo.
echo   --- 项目内清理 ---
echo   [2] 清理 MyNovelBot 根目录 (项目级 node_modules)
echo   [3] 清理 web-ui (前端缓存和依赖)
echo   [4] 清理 novel_bot (后端缓存、依赖和锁定文件)
echo.
echo   --- 高级/危险选项 ---
echo   [5] 彻底删除 pnpm 全局执行缓存 (核弹级!)
echo.
echo   --- 组合方案 ---
echo   [A] 一键执行安全清理 (推荐组合: 1,2,3,4)
echo.
echo   [Q] 退出
echo.
set /p choice="您的选择: "

if /i "%choice%"=="a" set selections=1,2,3,4& goto:execute_tasks
if /i "%choice%"=="" goto:main_menu
if /i "%choice%"=="q" exit /b
set selections=%choice%
goto:execute_tasks


:execute_tasks
cls
echo.
echo ============================================================================
echo                          开始执行清理
echo ============================================================================
echo.
echo 您的选择是: %selections%
echo.
pause

:: 预热步骤，确保状态稳定
call:pre_run_warmup

:: 使用稳定的 IF 语句结构执行任务
echo "!selections!" | find "1" >nul && call:task_clean_global_safe
echo "!selections!" | find "2" >nul && call:task_clean_root
echo "!selections!" | find "3" >nul && call:task_clean_webui
echo "!selections!" | find "4" >nul && call:task_clean_novelbot
echo "!selections!" | find "5" >nul && call:task_clean_global_nuke


echo.
echo ============================================================================
echo                         所有选定任务执行完毕！
echo                       正在进行最终状态检查...
echo ============================================================================
echo.
call:final_check

echo.
echo 清理完成，按任意键退出。
pause
exit /b


:: =============================================================================
:: 任务子函数
:: =============================================================================

:pre_run_warmup
echo  - 正在初始化清理脚本...
goto:eof

:task_clean_global_safe
echo.
echo ----------------------------------------------------------------------------
echo [任务 1] 清理 pnpm 全局缓存 (安全模式)
echo ----------------------------------------------------------------------------
echo.
echo  - 正在从 pnpm 全局可执行缓存中移除孤立的包...
call pnpm store prune
echo  - 正在检查 pnpm 是否依然可用...
where pnpm >nul 2>nul
if !errorlevel! equ 0 (
    echo    [成功] pnpm 命令依然可用。
) else (
    echo    [警告] pnpm 命令似乎不在您的系统 PATH 中。
)
goto:eof

:task_clean_global_nuke
echo.
echo ----------------------------------------------------------------------------
echo [任务 5] 彻底删除 pnpm 全局执行缓存 (核弹级)
echo ----------------------------------------------------------------------------
echo.
echo  [警告] 您选择彻底删除 pnpm 全局执行缓存！
echo  [警告] 这将删除所有项目共用的 pnpm 依赖文件。
echo  [警告] 下次安装依赖时 pnpm 会重新下载所有内容。
echo.
set /p confirm="确实要执行吗 (Y/N): "
if /i not "%confirm%"=="y" (
    echo  - 操作已取消。
    goto:eof
)

echo  - 正在查询 pnpm 全局执行缓存路径...
for /f "delims=" %%i in ('pnpm store path') do set pnpm_store_path=%%i

if defined pnpm_store_path (
    if exist "!pnpm_store_path!" (
        echo  - 找到路径: !pnpm_store_path!
        echo  - 正在删除缓存目录...
        rd /s /q "!pnpm_store_path!"
        echo    [成功] 已彻底删除 pnpm 全局执行缓存。
    ) else (
        echo  - [提示] 路径 "!pnpm_store_path!" 不存在，无需删除。
    )
) else (
    echo  - [错误] 未能通过 'pnpm store path' 获取全局执行缓存路径。
)
goto:eof

:task_clean_root
echo.
echo ----------------------------------------------------------------------------
echo [任务 2] 清理 MyNovelBot 根目录
echo ----------------------------------------------------------------------------
echo.
call:delete_if_exists "node_modules"
call:delete_if_exists "pnpm-lock.yaml"
goto:eof

:task_clean_webui
echo.
echo ----------------------------------------------------------------------------
echo [任务 3] 清理 web-ui (前端缓存和依赖)
echo ----------------------------------------------------------------------------
echo.
if exist "web-ui" (
    cd web-ui
    call:delete_if_exists "node_modules"
    call:delete_if_exists ".nuxt"
    call:delete_if_exists "pnpm-lock.yaml"
    call:delete_pycache
    cd ..
) else (
    echo  - 未找到 web-ui 目录。
)
goto:eof

:task_clean_novelbot
echo.
echo ----------------------------------------------------------------------------
echo [任务 4] 清理 novel_bot (后端缓存、依赖和锁定文件)
echo ----------------------------------------------------------------------------
echo.
if exist "novel_bot" (
    cd novel_bot
    rem [核心新增] 删除 poetry.lock 文件
    call:delete_if_exists "poetry.lock"
    echo  - 正在清理 Python 缓存...
    call:delete_pycache
    echo  - 正在检查 Poetry 虚拟环境...
    call poetry env info >nul 2>nul
    if !errorlevel! equ 0 (
        echo    [提示] 检测到 Poetry 虚拟环境。您可以使用 'poetry env remove python' 手动移除。
    ) else (
        echo    [提示] 未检测到活动的 Poetry 虚拟环境。
    )
    cd ..
) else (
    echo  - 未找到 novel_bot 目录。
)
goto:eof

:final_check
echo [最终状态验证]
echo.
call:verify_not_exists "MyNovelBot 根目录" "node_modules" "pnpm-lock.yaml"
call:verify_not_exists "web-ui" "web-ui\node_modules" "web-ui\.nuxt" "web-ui\pnpm-lock.yaml"
call:verify_not_exists "novel_bot" "novel_bot\poetry.lock"
call:verify_command "pnpm"
call:verify_command "poetry"
goto:eof


:: =============================================================================
:: 辅助函数
:: =============================================================================

:delete_if_exists
set "item=%~1"
if exist "%item%" (
    echo  - 正在删除 %item%...
    if exist "%item%\" (
        rd /s /q "%item%"
    ) else (
        del /f /q "%item%"
    )
    echo    [成功] 已删除。
) else (
    echo  - 未找到 %item%，无需清理。
)
goto:eof

:delete_pycache
echo  - 正在递归删除 __pycache__ 目录...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo    - 正在删除 "%%d"
        rd /s /q "%%d"
    )
)
echo  - __pycache__ 清理完毕。
goto:eof

:verify_not_exists
set "scope=%~1"
echo [验证范围: %scope%]
shift
:verify_loop
if "%~1"=="" goto:eof
set "item=%~1"
if not exist "%item%" (
    echo  - [通过] "%item%" 已被成功清理。
) else (
    echo  - [失败] "%item%" 仍然存在。请尝试手动删除。
)
shift
goto:verify_loop

:verify_command
set "cmd=%~1"
echo.
echo [命令验证: %cmd%]
where %cmd% >nul 2>nul
if !errorlevel! equ 0 (
    echo  - [通过] "%cmd%" 在系统中可用。
) else (
    echo  - [警告] "%cmd%" 在系统中不可用。请确认其已正确安装并添加到 PATH。
    if /i "%cmd%"=="poetry" (
        echo    [警告] Poetry 是本项目的核心依赖，请务必按照指南安装。
    )
)
goto:eof