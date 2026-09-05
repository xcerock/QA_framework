<#
.SYNOPSIS
    Arranca el banco de pruebas en Windows usando conda.

.DESCRIPTION
    Crea el entorno conda si no existe, comprueba el .env y levanta uvicorn.
    Equivalente de run.sh para Windows.

.EXAMPLE
    .\run.ps1
    .\run.ps1 -Port 9000
    .\run.ps1 -Recreate     # borra y vuelve a crear el entorno
#>
[CmdletBinding()]
param(
    [string]$EnvName = "qa-framework",
    [string]$AppHost,
    [int]$Port,
    [switch]$Recreate,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# --- conda disponible? ---------------------------------------------------
$conda = Get-Command conda -ErrorAction SilentlyContinue
if (-not $conda) {
    Write-Host "No encuentro 'conda' en el PATH." -ForegroundColor Red
    Write-Host "Abre una 'Anaconda Prompt' o ejecuta antes:" -ForegroundColor Yellow
    Write-Host '  & "$env:USERPROFILE\AppData\Local\miniconda3\shell\condabin\conda-hook.ps1"'
    exit 1
}

# --- localizar el prefijo del entorno ------------------------------------
function Get-EnvPrefix([string]$name) {
    $info = conda info --envs --json | ConvertFrom-Json
    foreach ($p in $info.envs) {
        if ((Split-Path $p -Leaf) -eq $name) { return $p }
    }
    return $null
}

$prefix = Get-EnvPrefix $EnvName

if ($prefix -and $Recreate) {
    Write-Host "Borrando el entorno '$EnvName'..." -ForegroundColor Yellow
    conda env remove -n $EnvName -y
    if (-not $?) { exit 1 }
    $prefix = $null
}

if (-not $prefix) {
    Write-Host "Creando el entorno conda '$EnvName'... (tarda un par de minutos)" -ForegroundColor Cyan
    conda env create -f environment.yml -n $EnvName
    if (-not $?) {
        Write-Host "Fallo al crear el entorno." -ForegroundColor Red
        exit 1
    }
    $prefix = Get-EnvPrefix $EnvName
}

$python = Join-Path $prefix "python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No encuentro python.exe en $prefix" -ForegroundColor Red
    exit 1
}

# --- dependencias al dia -------------------------------------------------
& $python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if (-not $?) {
    Write-Host "Fallo al instalar las dependencias." -ForegroundColor Red
    exit 1
}

# --- .env ----------------------------------------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "No hay .env. Copiando desde .env.example." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Edita .env y pon tu ANTHROPIC_API_KEY antes de continuar." -ForegroundColor Yellow
    exit 1
}

# --- arrancar ------------------------------------------------------------
# La consola de Windows usa cp1252 por defecto y rompe los acentos del banner.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# Los parametros ganan al .env; el .env gana al valor por defecto.
$envVars = @{}
foreach ($line in Get-Content ".env") {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $envVars[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
    }
}

if (-not $AppHost) { $AppHost = if ($envVars.HOST) { $envVars.HOST } else { "127.0.0.1" } }
if (-not $Port)    { $Port    = if ($envVars.PORT) { [int]$envVars.PORT } else { 8000 } }

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", $AppHost, "--port", "$Port")
if (-not $NoReload) {
    # En Windows el proceso hijo de --reload tarda ~40 s en arrancar la primera vez.
    # Usa -NoReload el dia de la demo: levanta en segundos.
    $uvicornArgs += "--reload"
    Write-Host "Con recarga automatica: la primera arrancada tarda ~40 s en Windows." -ForegroundColor DarkGray
    Write-Host "Usa -NoReload si tienes prisa." -ForegroundColor DarkGray
}

Write-Host "Arrancando en http://${AppHost}:${Port}" -ForegroundColor Green
& $python @uvicornArgs
