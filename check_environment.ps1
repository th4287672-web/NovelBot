# =============================================================================
# MyNovelBot 环境自检脚本 (v1.0)
# =============================================================================
# 功能: 本脚本只检查当前环境是否满足项目要求, 不会进行任何安装或修改.
#       如果检查失败, 请严格按照 README.md 文件中的指引手动安装和配置.
# =============================================================================

function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Failure { param([string]$Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }

Clear-Host
Write-Host "============================================================================" -ForegroundColor Magenta
Write-Host "                        MyNovelBot 环境自检向导" -ForegroundColor Magenta
Write-Host "============================================================================" -ForegroundColor Magenta
Write-Host

$allChecksPassed = $true

# 1. 检查 nvm-windows
Write-Host "[1/5] 检查 nvm-windows..."
$nvm_path = Get-Command nvm -ErrorAction SilentlyContinue
if ($nvm_path) {
    $nvm_version = nvm version
    if ($nvm_version -eq "1.2.2") {
        Write-Success " - [通过] nvm-windows 版本正确 (v1.2.2)."
    } else {
        Write-Failure " - [失败] nvm-windows 版本不正确 (需要 v1.2.2, 当前为 v$nvm_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [失败] 未找到 nvm-windows 命令."
    $allChecksPassed = $false
}

# 2. 检查 Node.js
Write-Host "[2/5] 检查 Node.js..."
$node_path = Get-Command node -ErrorAction SilentlyContinue
if ($node_path) {
    $node_version = node -v
    if ($node_version -eq "v24.7.0") {
        Write-Success " - [通过] Node.js 版本正确 (v24.7.0)."
    } else {
        Write-Failure " - [失败] Node.js 版本不正确 (需要 v24.7.0, 当前为 $node_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [失败] 未找到 node 命令."
    $allChecksPassed = $false
}

# 3. 检查 pnpm
Write-Host "[3/5] 检查 pnpm..."
$pnpm_path = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpm_path) {
    $pnpm_version = pnpm -v
    if ($pnpm_version -eq "10.15.1") {
        Write-Success " - [通过] pnpm 版本正确 (v10.15.1)."
    } else {
        Write-Failure " - [失败] pnpm 版本不正确 (需要 v10.15.1, 当前为 v$pnpm_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [失败] 未找到 pnpm 命令."
    $allChecksPassed = $false
}

# 4. 检查 Python
Write-Host "[4/5] 检查 Python..."
$python_path = Get-Command python -ErrorAction SilentlyContinue
if ($python_path) {
    $py_version = (python --version).Split(" ")[1]
    if ($py_version -like "3.13.0*") {
        Write-Success " - [通过] Python 版本正确 (v$py_version)."
    } else {
        Write-Failure " - [失败] Python 版本不正确 (需要 v3.13.0, 当前为 v$py_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [失败] 未找到 python 命令."
    $allChecksPassed = $false
}

# 5. 检查 Poetry
Write-Host "[5/5] 检查 Poetry..."
$poetry_path = Get-Command poetry -ErrorAction SilentlyContinue
if ($poetry_path) {
    Write-Success " - [通过] Poetry 已安装."
} else {
    Write-Failure " - [失败] 未找到 poetry 命令."
    $allChecksPassed = $false
}

# 最终总结
Write-Host
Write-Host "----------------------------------------------------------------------------"
if ($allChecksPassed) {
    Write-Success "恭喜! 您的核心开发环境已全部配置正确!"
    Write-Info "现在您可以运行 install_dependencies.bat 来安装项目依赖了."
} else {
    Write-Failure "环境检查未通过!"
    Write-Info "请打开项目中的 README.md 文件, 严格按照其中的'环境安装指南'部分进行手动配置."
}
Write-Host "----------------------------------------------------------------------------"
Write-Host
Write-Host "按 Enter 键退出..." -ForegroundColor Yellow
Read-Host | Out-Null