# =============================================================================
# MyNovelBot �����Լ�ű� (v1.0)
# =============================================================================
# ����: ���ű�ֻ��鵱ǰ�����Ƿ�������ĿҪ��, ��������κΰ�װ���޸�.
#       ������ʧ��, ���ϸ��� README.md �ļ��е�ָ���ֶ���װ������.
# =============================================================================

function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Failure { param([string]$Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }

Clear-Host
Write-Host "============================================================================" -ForegroundColor Magenta
Write-Host "                        MyNovelBot �����Լ���" -ForegroundColor Magenta
Write-Host "============================================================================" -ForegroundColor Magenta
Write-Host

$allChecksPassed = $true

# 1. ��� nvm-windows
Write-Host "[1/5] ��� nvm-windows..."
$nvm_path = Get-Command nvm -ErrorAction SilentlyContinue
if ($nvm_path) {
    $nvm_version = nvm version
    if ($nvm_version -eq "1.2.2") {
        Write-Success " - [ͨ��] nvm-windows �汾��ȷ (v1.2.2)."
    } else {
        Write-Failure " - [ʧ��] nvm-windows �汾����ȷ (��Ҫ v1.2.2, ��ǰΪ v$nvm_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [ʧ��] δ�ҵ� nvm-windows ����."
    $allChecksPassed = $false
}

# 2. ��� Node.js
Write-Host "[2/5] ��� Node.js..."
$node_path = Get-Command node -ErrorAction SilentlyContinue
if ($node_path) {
    $node_version = node -v
    if ($node_version -eq "v24.7.0") {
        Write-Success " - [ͨ��] Node.js �汾��ȷ (v24.7.0)."
    } else {
        Write-Failure " - [ʧ��] Node.js �汾����ȷ (��Ҫ v24.7.0, ��ǰΪ $node_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [ʧ��] δ�ҵ� node ����."
    $allChecksPassed = $false
}

# 3. ��� pnpm
Write-Host "[3/5] ��� pnpm..."
$pnpm_path = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpm_path) {
    $pnpm_version = pnpm -v
    if ($pnpm_version -eq "10.15.1") {
        Write-Success " - [ͨ��] pnpm �汾��ȷ (v10.15.1)."
    } else {
        Write-Failure " - [ʧ��] pnpm �汾����ȷ (��Ҫ v10.15.1, ��ǰΪ v$pnpm_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [ʧ��] δ�ҵ� pnpm ����."
    $allChecksPassed = $false
}

# 4. ��� Python
Write-Host "[4/5] ��� Python..."
$python_path = Get-Command python -ErrorAction SilentlyContinue
if ($python_path) {
    $py_version = (python --version).Split(" ")[1]
    if ($py_version -like "3.13.0*") {
        Write-Success " - [ͨ��] Python �汾��ȷ (v$py_version)."
    } else {
        Write-Failure " - [ʧ��] Python �汾����ȷ (��Ҫ v3.13.0, ��ǰΪ v$py_version)."
        $allChecksPassed = $false
    }
} else {
    Write-Failure " - [ʧ��] δ�ҵ� python ����."
    $allChecksPassed = $false
}

# 5. ��� Poetry
Write-Host "[5/5] ��� Poetry..."
$poetry_path = Get-Command poetry -ErrorAction SilentlyContinue
if ($poetry_path) {
    Write-Success " - [ͨ��] Poetry �Ѱ�װ."
} else {
    Write-Failure " - [ʧ��] δ�ҵ� poetry ����."
    $allChecksPassed = $false
}

# �����ܽ�
Write-Host
Write-Host "----------------------------------------------------------------------------"
if ($allChecksPassed) {
    Write-Success "��ϲ! ���ĺ��Ŀ���������ȫ��������ȷ!"
    Write-Info "�������������� install_dependencies.bat ����װ��Ŀ������."
} else {
    Write-Failure "�������δͨ��!"
    Write-Info "�����Ŀ�е� README.md �ļ�, �ϸ������е�'������װָ��'���ֽ����ֶ�����."
}
Write-Host "----------------------------------------------------------------------------"
Write-Host
Write-Host "�� Enter ���˳�..." -ForegroundColor Yellow
Read-Host | Out-Null