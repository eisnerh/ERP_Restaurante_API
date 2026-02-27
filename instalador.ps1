# Instalador ERP Raul Castaño
# Descarga e instala lo necesario, luego instala la aplicación.
# Ejecutar como: powershell -ExecutionPolicy Bypass -File instalador.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ERP Raul Castano - Instalador" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Ubicacion de instalacion:" -ForegroundColor White
Write-Host "  $projectRoot" -ForegroundColor Yellow
Write-Host ""
Write-Host "  (La aplicacion se instalara en esta carpeta. Si quieres otro lugar," -ForegroundColor Gray
Write-Host "   copia el proyecto alli y ejecuta instalar.bat desde esa carpeta)" -ForegroundColor Gray
Write-Host ""

# --- 1. Verificar/Instalar Python ---
$pythonCmd = $null
foreach ($cmd in @("python", "py")) {
    try {
        $v = & $cmd --version 2>&1
        if ($v -match "Python 3\.(\d+)") {
            $pythonCmd = $cmd
            Write-Host "[OK] Python encontrado: $v" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "[!] Python no encontrado. Intentando instalar..." -ForegroundColor Yellow
    try {
        $winget = Get-Command winget -ErrorAction Stop
        Write-Host "    Ejecutando: winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements" -ForegroundColor Gray
        & winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    Python instalado. Cierra esta ventana, abre una nueva y ejecuta de nuevo: .\instalador.ps1" -ForegroundColor Yellow
            Write-Host "    (Es necesario para que el PATH se actualice)" -ForegroundColor Yellow
            pause
            exit 0
        }
    } catch {
        Write-Host "[X] No se pudo instalar Python automaticamente." -ForegroundColor Red
        Write-Host "    Descarga Python desde: https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "    Marca 'Add Python to PATH' durante la instalacion." -ForegroundColor White
        Start-Process "https://www.python.org/downloads/"
        pause
        exit 1
    }
}

# --- 2. Verificar PostgreSQL ---
$pgOk = $false
try {
    $pg = Get-Command psql -ErrorAction SilentlyContinue
    if ($pg) { $pgOk = $true }
} catch {}
if (-not $pgOk) {
    try {
        $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
        if ($pgService) { $pgOk = $true }
    } catch {}
}
if (-not $pgOk) {
    Write-Host "[!] PostgreSQL no detectado. La aplicacion lo requiere." -ForegroundColor Yellow
    $r = Read-Host "    Abrir pagina de descarga? (S/n)"
    if ($r -ne "n" -and $r -ne "N") {
        Start-Process "https://www.postgresql.org/download/windows/"
    }
    Write-Host "    Despues de instalar PostgreSQL, ejecuta de nuevo este instalador." -ForegroundColor Gray
    Write-Host ""
}

# --- 3. Crear entorno virtual e instalar dependencias ---
$venvPath = Join-Path $projectRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creando entorno virtual..." -ForegroundColor Yellow
    & $pythonCmd -m venv $venvPath
    Write-Host "    Entorno virtual creado." -ForegroundColor Green
} else {
    Write-Host "[OK] Entorno virtual ya existe." -ForegroundColor Green
}

$pip = Join-Path $venvPath "Scripts\pip.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $pip)) {
    Write-Host "[X] Error: pip no encontrado en venv. Borra la carpeta 'venv' y ejecuta de nuevo." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[*] Instalando dependencias..." -ForegroundColor Yellow
Start-Process -FilePath $pythonExe -ArgumentList "-m","pip","install","-r",(Join-Path $projectRoot "requirements.txt"),"-q" -Wait -NoNewWindow
Start-Process -FilePath $pythonExe -ArgumentList "-m","pip","install","pyinstaller","pillow","-q" -Wait -NoNewWindow
Write-Host "    Dependencias instaladas." -ForegroundColor Green

# --- 4. Crear .env y configurar PostgreSQL ---
$envExample = Join-Path $projectRoot ".env.example"
$envFile = Join-Path $projectRoot ".env"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "[*] Archivo .env creado." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Configuracion de PostgreSQL" -ForegroundColor Cyan
    Write-Host "  Ingresa la contrasena del usuario 'postgres' (la que definiste al instalar PostgreSQL)" -ForegroundColor White
    Write-Host "  (Enter para omitir y configurar despues en .env)" -ForegroundColor Gray
    $pgPassPlain = Read-Host "  Contrasena de PostgreSQL"
    if ($pgPassPlain) {
        $envContent = Get-Content $envFile -Raw
        $envContent = $envContent -replace "PGPASSWORD=.*", "PGPASSWORD=$pgPassPlain"
        Set-Content $envFile $envContent -NoNewline
        Write-Host "  Contrasena guardada en .env" -ForegroundColor Green
    }
} elseif (Test-Path $envFile) {
    Write-Host "[OK] Archivo .env ya existe." -ForegroundColor Green
}

# --- 5. Crear base de datos PostgreSQL y tablas ---
Write-Host ""
Write-Host "[*] Creando base de datos en PostgreSQL..." -ForegroundColor Yellow
$initOutput = & $pythonExe (Join-Path $projectRoot "scripts\init_db.py") 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Base de datos 'restaurant_erp' creada (o ya existia)." -ForegroundColor Green
    Write-Host "    Tablas creadas correctamente." -ForegroundColor Green
} else {
    Write-Host "    Error al conectar con PostgreSQL." -ForegroundColor Red
    Write-Host "    Verifica que:" -ForegroundColor Yellow
    Write-Host "      1. PostgreSQL este instalado y el servicio corriendo" -ForegroundColor Gray
    Write-Host "      2. La contrasena en .env sea correcta (PGPASSWORD)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "    Despues de corregir, ejecuta: python scripts\init_db.py" -ForegroundColor Gray
}

# --- 6. Migraciones ---
& $pythonExe (Join-Path $projectRoot "scripts\migrate_hrs_negativas.py") 2>$null
Write-Host "[OK] Migraciones aplicadas." -ForegroundColor Green

# --- 7. Crear icono ---
$iconPath = Join-Path $projectRoot "icon.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "[*] Generando icono de la aplicacion..." -ForegroundColor Yellow
    & $pythonExe (Join-Path $projectRoot "scripts\crear_icono.py") 2>$null
    Write-Host "    Icono creado: icon.ico" -ForegroundColor Green
} else {
    Write-Host "[OK] Icono ya existe." -ForegroundColor Green
}

# --- 8. Crear acceso directo en el escritorio ---
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "ERP Raul Castano.lnk"
$targetPath = Join-Path $projectRoot "iniciar_erp.bat"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "ERP Raul Castano - Sistema de gestion para restaurantes"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wsh) | Out-Null
Write-Host "[OK] Acceso directo creado en el escritorio." -ForegroundColor Green

# --- 9. Actualizar spec de PyInstaller con icono ---
$specPath = Join-Path $projectRoot "restaurant_api.spec"
if ((Test-Path $specPath) -and (Test-Path $iconPath)) {
    $spec = Get-Content $specPath -Raw
    if ($spec -match "icon=None") {
        $spec = $spec -replace "icon=None.*", "icon='icon.ico',"
        Set-Content $specPath $spec -NoNewline
        Write-Host "[OK] PyInstaller configurado para usar el icono." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalacion completada" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ubicacion:" -ForegroundColor White
Write-Host "  $projectRoot" -ForegroundColor Gray
Write-Host ""
Write-Host "Para iniciar la aplicacion:" -ForegroundColor White
Write-Host "  1. Doble clic en 'ERP Raul Castano' en el escritorio" -ForegroundColor Gray
Write-Host "  2. O ejecuta: .\iniciar_erp.bat" -ForegroundColor Gray
Write-Host "  3. Abre http://127.0.0.1:5000 en el navegador" -ForegroundColor Gray
Write-Host ""
Write-Host "Si es la primera vez, configura .env con la contrasena de PostgreSQL." -ForegroundColor Yellow
Write-Host ""
pause
