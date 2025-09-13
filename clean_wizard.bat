@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: MyNovelBot ������ (Clean Wizard) v8.0 (����)
:: =============================================================================
:: ����: һվʽ��ǿ��������ű������ڽ�� MyNovelBot ��Ŀ�ĸ���������֢��
::
:: v8.0 ����:
:: - �û�Ҫ���ڱ���ԭ��һ����ȫģʽ��ͬʱ���������롰����ɾ��
::   pnpm ȫ��ִ�л��桱�ĺ˵���ѡ�Ϊ�û��ṩ����ϸ�ķ��տ��ơ�
:: - �޸������Ӻ����ĵ������⣬ȷ�������ӳ����ʹ�� `call` �ؼ��֡�
:: [�������� v8.1] ������ novel_bot ʱ��һ��ɾ�� poetry.lock �ļ���
:: =============================================================================

:main_menu
cls
echo.
echo ============================================================================
echo                 MyNovelBot ������ v8.1 (����)
echo ============================================================================
echo.
echo   ��ѡ����Ҫִ�е��������� (�ɶ�ѡ, ����: 1,3):
echo.
echo   --- �Ƽ����� ---
echo   [1] ���� pnpm ȫ�ֻ��� (��ȫģʽ, �Ƽ�)
echo.
echo   --- ��Ŀ������ ---
echo   [2] ���� MyNovelBot ��Ŀ¼ (��Ŀ�� node_modules)
echo   [3] ���� web-ui (ǰ�˻��������)
echo   [4] ���� novel_bot (��˻��桢�����������ļ�)
echo.
echo   --- �߼�/Σ��ѡ�� ---
echo   [5] ����ɾ�� pnpm ȫ��ִ�л��� (�˵���!)
echo.
echo   --- ��Ϸ��� ---
echo   [A] һ��ִ�а�ȫ���� (�Ƽ����: 1,2,3,4)
echo.
echo   [Q] �˳�
echo.
set /p choice="����ѡ��: "

if /i "%choice%"=="a" set selections=1,2,3,4& goto:execute_tasks
if /i "%choice%"=="" goto:main_menu
if /i "%choice%"=="q" exit /b
set selections=%choice%
goto:execute_tasks


:execute_tasks
cls
echo.
echo ============================================================================
echo                          ��ʼִ������
echo ============================================================================
echo.
echo ����ѡ����: %selections%
echo.
pause

:: Ԥ�Ȳ��裬ȷ��״̬�ȶ�
call:pre_run_warmup

:: ʹ���ȶ��� IF ���ṹִ������
echo "!selections!" | find "1" >nul && call:task_clean_global_safe
echo "!selections!" | find "2" >nul && call:task_clean_root
echo "!selections!" | find "3" >nul && call:task_clean_webui
echo "!selections!" | find "4" >nul && call:task_clean_novelbot
echo "!selections!" | find "5" >nul && call:task_clean_global_nuke


echo.
echo ============================================================================
echo                         ����ѡ������ִ����ϣ�
echo                       ���ڽ�������״̬���...
echo ============================================================================
echo.
call:final_check

echo.
echo ������ɣ���������˳���
pause
exit /b


:: =============================================================================
:: �����Ӻ���
:: =============================================================================

:pre_run_warmup
echo  - ���ڳ�ʼ������ű�...
goto:eof

:task_clean_global_safe
echo.
echo ----------------------------------------------------------------------------
echo [���� 1] ���� pnpm ȫ�ֻ��� (��ȫģʽ)
echo ----------------------------------------------------------------------------
echo.
echo  - ���ڴ� pnpm ȫ�ֿ�ִ�л������Ƴ������İ�...
call pnpm store prune
echo  - ���ڼ�� pnpm �Ƿ���Ȼ����...
where pnpm >nul 2>nul
if !errorlevel! equ 0 (
    echo    [�ɹ�] pnpm ������Ȼ���á�
) else (
    echo    [����] pnpm �����ƺ���������ϵͳ PATH �С�
)
goto:eof

:task_clean_global_nuke
echo.
echo ----------------------------------------------------------------------------
echo [���� 5] ����ɾ�� pnpm ȫ��ִ�л��� (�˵���)
echo ----------------------------------------------------------------------------
echo.
echo  [����] ��ѡ�񳹵�ɾ�� pnpm ȫ��ִ�л��棡
echo  [����] �⽫ɾ��������Ŀ���õ� pnpm �����ļ���
echo  [����] �´ΰ�װ����ʱ pnpm �����������������ݡ�
echo.
set /p confirm="ȷʵҪִ���� (Y/N): "
if /i not "%confirm%"=="y" (
    echo  - ������ȡ����
    goto:eof
)

echo  - ���ڲ�ѯ pnpm ȫ��ִ�л���·��...
for /f "delims=" %%i in ('pnpm store path') do set pnpm_store_path=%%i

if defined pnpm_store_path (
    if exist "!pnpm_store_path!" (
        echo  - �ҵ�·��: !pnpm_store_path!
        echo  - ����ɾ������Ŀ¼...
        rd /s /q "!pnpm_store_path!"
        echo    [�ɹ�] �ѳ���ɾ�� pnpm ȫ��ִ�л��档
    ) else (
        echo  - [��ʾ] ·�� "!pnpm_store_path!" �����ڣ�����ɾ����
    )
) else (
    echo  - [����] δ��ͨ�� 'pnpm store path' ��ȡȫ��ִ�л���·����
)
goto:eof

:task_clean_root
echo.
echo ----------------------------------------------------------------------------
echo [���� 2] ���� MyNovelBot ��Ŀ¼
echo ----------------------------------------------------------------------------
echo.
call:delete_if_exists "node_modules"
call:delete_if_exists "pnpm-lock.yaml"
goto:eof

:task_clean_webui
echo.
echo ----------------------------------------------------------------------------
echo [���� 3] ���� web-ui (ǰ�˻��������)
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
    echo  - δ�ҵ� web-ui Ŀ¼��
)
goto:eof

:task_clean_novelbot
echo.
echo ----------------------------------------------------------------------------
echo [���� 4] ���� novel_bot (��˻��桢�����������ļ�)
echo ----------------------------------------------------------------------------
echo.
if exist "novel_bot" (
    cd novel_bot
    rem [��������] ɾ�� poetry.lock �ļ�
    call:delete_if_exists "poetry.lock"
    echo  - �������� Python ����...
    call:delete_pycache
    echo  - ���ڼ�� Poetry ���⻷��...
    call poetry env info >nul 2>nul
    if !errorlevel! equ 0 (
        echo    [��ʾ] ��⵽ Poetry ���⻷����������ʹ�� 'poetry env remove python' �ֶ��Ƴ���
    ) else (
        echo    [��ʾ] δ��⵽��� Poetry ���⻷����
    )
    cd ..
) else (
    echo  - δ�ҵ� novel_bot Ŀ¼��
)
goto:eof

:final_check
echo [����״̬��֤]
echo.
call:verify_not_exists "MyNovelBot ��Ŀ¼" "node_modules" "pnpm-lock.yaml"
call:verify_not_exists "web-ui" "web-ui\node_modules" "web-ui\.nuxt" "web-ui\pnpm-lock.yaml"
call:verify_not_exists "novel_bot" "novel_bot\poetry.lock"
call:verify_command "pnpm"
call:verify_command "poetry"
goto:eof


:: =============================================================================
:: ��������
:: =============================================================================

:delete_if_exists
set "item=%~1"
if exist "%item%" (
    echo  - ����ɾ�� %item%...
    if exist "%item%\" (
        rd /s /q "%item%"
    ) else (
        del /f /q "%item%"
    )
    echo    [�ɹ�] ��ɾ����
) else (
    echo  - δ�ҵ� %item%����������
)
goto:eof

:delete_pycache
echo  - ���ڵݹ�ɾ�� __pycache__ Ŀ¼...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo    - ����ɾ�� "%%d"
        rd /s /q "%%d"
    )
)
echo  - __pycache__ ������ϡ�
goto:eof

:verify_not_exists
set "scope=%~1"
echo [��֤��Χ: %scope%]
shift
:verify_loop
if "%~1"=="" goto:eof
set "item=%~1"
if not exist "%item%" (
    echo  - [ͨ��] "%item%" �ѱ��ɹ�����
) else (
    echo  - [ʧ��] "%item%" ��Ȼ���ڡ��볢���ֶ�ɾ����
)
shift
goto:verify_loop

:verify_command
set "cmd=%~1"
echo.
echo [������֤: %cmd%]
where %cmd% >nul 2>nul
if !errorlevel! equ 0 (
    echo  - [ͨ��] "%cmd%" ��ϵͳ�п��á�
) else (
    echo  - [����] "%cmd%" ��ϵͳ�в����á���ȷ��������ȷ��װ����ӵ� PATH��
    if /i "%cmd%"=="poetry" (
        echo    [����] Poetry �Ǳ���Ŀ�ĺ�������������ذ���ָ�ϰ�װ��
    )
)
goto:eof