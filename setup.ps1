# Setup Restaurant API - Crea venv e instala dependencias
# Ejecutar desde la carpeta del proyecto: .\setup.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host "Restaurant API - Setup" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host ""

# Comprobar Python
try {
    $py = Get-Command python -ErrorAction Stop
} catch {
    try {
        $py = Get-Command py -ErrorAction Stop
    } catch {
        Write-Host "No se encontró Python. Instala Python 3.8+ y asegúrate de que 'python' o 'py' esté en el PATH." -ForegroundColor Red
        exit 1
    }
}

$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
$version = & $pythonCmd --version 2>&1
Write-Host "Python: $version" -ForegroundColor Green

# Crear venv si no existe
$venvPath = Join-Path $projectRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual en venv\ ..." -ForegroundColor Yellow
    & $pythonCmd -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Entorno virtual creado." -ForegroundColor Green
} else {
    Write-Host "Entorno virtual ya existe (venv\)." -ForegroundColor Green
}

# Instalar dependencias
$pip = Join-Path $venvPath "Scripts\pip.exe"
$requirements = Join-Path $projectRoot "requirements.txt"
if (-not (Test-Path $pip)) {
    Write-Host "No se encontró pip en venv. Recrea el venv: borra la carpeta venv y ejecuta de nuevo .\setup.ps1" -ForegroundColor Red
    exit 1
}
Write-Host "Instalando dependencias desde requirements.txt ..." -ForegroundColor Yellow
& $pip install -r $requirements --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Dependencias instaladas." -ForegroundColor Green

Write-Host ""
Write-Host "Setup completado." -ForegroundColor Cyan
Write-Host ""
Write-Host "Siguiente:" -ForegroundColor White
Write-Host "  1. Activa el entorno y ejecuta la app:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     python app.py" -ForegroundColor Gray
Write-Host "  2. Abre http://127.0.0.1:5000/ en el navegador." -ForegroundColor White
Write-Host ""
