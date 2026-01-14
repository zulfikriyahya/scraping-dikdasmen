# ============================================================================
# SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP & INSTALLER (PowerShell)
# ============================================================================
# Author  : Yahya Zulfikri
# Project : Scraper Data Sekolah Seluruh Indonesia
# License : MIT
# ============================================================================

# Enable colors
$Host.UI.RawUI.ForegroundColor = "White"

# Function to print colored text
function Write-Color {
    param(
        [string]$Text,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    $colors = @{
        'Red' = [ConsoleColor]::Red
        'Green' = [ConsoleColor]::Green
        'Yellow' = [ConsoleColor]::Yellow
        'Blue' = [ConsoleColor]::Blue
        'Cyan' = [ConsoleColor]::Cyan
        'Magenta' = [ConsoleColor]::Magenta
        'White' = [ConsoleColor]::White
        'Gray' = [ConsoleColor]::Gray
    }
    
    if ($NoNewline) {
        Write-Host $Text -ForegroundColor $colors[$Color] -NoNewline
    } else {
        Write-Host $Text -ForegroundColor $colors[$Color]
    }
}

function Write-Step {
    param([string]$Message)
    Write-Color "➜ " -Color Cyan -NoNewline
    Write-Color $Message -Color White
}

function Write-Success {
    param([string]$Message)
    Write-Color "✓ " -Color Green -NoNewline
    Write-Color $Message -Color Green
}

function Write-Error-Msg {
    param([string]$Message)
    Write-Color "✗ " -Color Red -NoNewline
    Write-Color $Message -Color Red
}

function Write-Info {
    param([string]$Message)
    Write-Color "ℹ " -Color Blue -NoNewline
    Write-Color $Message -Color Blue
}

function Write-Warning-Msg {
    param([string]$Message)
    Write-Color "⚠ " -Color Yellow -NoNewline
    Write-Color $Message -Color Yellow
}

# ============================================================================
# HEADER
# ============================================================================

Clear-Host
Write-Color "╔════════════════════════════════════════════════════════════════════╗" -Color Cyan
Write-Color "║     SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP INSTALLER      ║" -Color Cyan
Write-Color "╚════════════════════════════════════════════════════════════════════╝" -Color Cyan
Write-Color ""
Write-Color "Author  : Yahya Zulfikri" -Color White
Write-Color "Project : Scraper Data Sekolah Seluruh Indonesia" -Color White
Write-Color "License : MIT" -Color White
Write-Color ""

# ============================================================================
# CHECK ADMIN
# ============================================================================

Write-Step "Memeriksa hak akses..."
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Success "Running as Administrator"
} else {
    Write-Warning-Msg "Running without Administrator privileges"
    Write-Info "Beberapa fitur mungkin memerlukan admin"
}
Write-Host ""

# ============================================================================
# CHECK INTERNET
# ============================================================================

Write-Step "Memeriksa koneksi internet..."
try {
    $ping = Test-Connection -ComputerName google.com -Count 1 -Quiet -ErrorAction Stop
    if ($ping) {
        Write-Success "Koneksi internet tersedia"
    } else {
        throw "No internet"
    }
} catch {
    Write-Error-Msg "Tidak ada koneksi internet!"
    Write-Error-Msg "Setup dibatalkan. Silakan periksa koneksi Anda."
    pause
    exit 1
}
Write-Host ""

# ============================================================================
# DETECT SYSTEM
# ============================================================================

Write-Step "Mendeteksi sistem..."
$os = Get-WmiObject -Class Win32_OperatingSystem
$processor = Get-WmiObject -Class Win32_Processor

Write-Info "OS: $($os.Caption)"
Write-Info "Architecture: $env:PROCESSOR_ARCHITECTURE"
Write-Info "Processor: $($processor.Name)"
Write-Host ""

# ============================================================================
# CHECK GIT
# ============================================================================

Write-Step "Memeriksa Git..."
$git = Get-Command git -ErrorAction SilentlyContinue

if ($git) {
    Write-Success "Git sudah terinstall"
    $gitVersion = git --version
    Write-Info "Version: $gitVersion"
} else {
    Write-Warning-Msg "Git tidak ditemukan"
    Write-Info "Downloading Git installer..."
    
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "git-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
        Write-Info "Installing Git..."
        Start-Process -FilePath $gitInstaller -Args "/VERYSILENT /NORESTART" -Wait
        Remove-Item $gitInstaller
        Write-Success "Git berhasil diinstall"
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {
        Write-Error-Msg "Gagal install Git"
        Write-Info "Install manual dari: https://git-scm.com/download/win"
        pause
        exit 1
    }
}
Write-Host ""

# ============================================================================
# CLONE REPOSITORY
# ============================================================================

Write-Step "Cloning repository..."
$repoUrl = "https://github.com/zulfikriyahya/scraping-dikdasmen.git"
$targetDir = "scraping-dikdasmen"

if (Test-Path $targetDir) {
    Write-Warning-Msg "Directory $targetDir sudah ada"
    $reply = Read-Host "Hapus dan clone ulang? (y/n)"
    
    if ($reply -eq 'y' -or $reply -eq 'Y') {
        Remove-Item -Path $targetDir -Recurse -Force
        git clone $repoUrl $targetDir
    }
} else {
    git clone $repoUrl $targetDir
}

if ($LASTEXITCODE -eq 0) {
    Write-Success "Repository berhasil di-clone"
    Set-Location $targetDir
} else {
    Write-Error-Msg "Gagal clone repository"
    pause
    exit 1
}
Write-Host ""

# ============================================================================
# CHECK PYTHON
# ============================================================================

Write-Step "Memeriksa Python..."
$python = Get-Command python -ErrorAction SilentlyContinue
$python3 = Get-Command python3 -ErrorAction SilentlyContinue

if ($python) {
    $pyVersion = python --version
    Write-Success "Python sudah terinstall"
    Write-Info "Version: $pyVersion"
    $pythonCmd = "python"
} elseif ($python3) {
    $pyVersion = python3 --version
    Write-Success "Python3 sudah terinstall"
    Write-Info "Version: $pyVersion"
    $pythonCmd = "python3"
} else {
    Write-Warning-Msg "Python tidak ditemukan"
    Write-Info "Downloading Python installer..."
    
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $pythonInstaller = "python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        Write-Info "Installing Python..."
        Start-Process -FilePath $pythonInstaller -Args "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Remove-Item $pythonInstaller
        Write-Success "Python berhasil diinstall"
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = "python"
    } catch {
        Write-Error-Msg "Gagal install Python"
        Write-Info "Install manual dari: https://www.python.org/downloads/"
        pause
        exit 1
    }
}
Write-Host ""

# ============================================================================
# CHECK GOOGLE CHROME
# ============================================================================

Write-Step "Memeriksa Google Chrome..."
$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Success "Google Chrome terdeteksi"
        Write-Info "Path: $path"
        $chromeFound = $true
        break
    }
}

if (-not $chromeFound) {
    Write-Warning-Msg "Google Chrome tidak terdeteksi"
    Write-Info "Downloading Chrome installer..."
    
    $chromeUrl = "https://dl.google.com/chrome/install/latest/chrome_installer.exe"
    $chromeInstaller = "chrome-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $chromeUrl -OutFile $chromeInstaller -UseBasicParsing
        Write-Info "Installing Chrome..."
        Start-Process -FilePath $chromeInstaller -Args "/silent /install" -Wait
        Remove-Item $chromeInstaller
        Write-Success "Chrome berhasil diinstall"
    } catch {
        Write-Error-Msg "Gagal install Chrome"
        Write-Info "Install manual dari: https://www.google.com/chrome/"
    }
}
Write-Host ""

# ============================================================================
# CREATE VIRTUAL ENVIRONMENT
# ============================================================================

Write-Step "Membuat virtual environment..."

if (Test-Path "venv") {
    Write-Success "Virtual environment sudah ada"
} else {
    Write-Info "Creating venv..."
    & $pythonCmd -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment berhasil dibuat"
    } else {
        Write-Error-Msg "Gagal membuat virtual environment"
        pause
        exit 1
    }
}
Write-Host ""

# ============================================================================
# ACTIVATE VENV & INSTALL DEPENDENCIES
# ============================================================================

Write-Step "Mengaktifkan virtual environment..."
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment aktif"
Write-Host ""

Write-Step "Upgrading pip..."
python -m pip install --upgrade pip --quiet
Write-Success "Pip upgraded"
Write-Host ""

# ============================================================================
# CREATE REQUIREMENTS.TXT
# ============================================================================

Write-Step "Membuat requirements.txt..."

$requirements = @"
# Python Dependencies for Scraper Data Sekolah
# Author: Yahya Zulfikri
# Project: Scraper Data Sekolah Seluruh Indonesia

selenium>=4.15.0
beautifulsoup4>=4.12.0
openpyxl>=3.1.0
requests>=2.31.0
pandas>=2.0.0
psutil>=5.9.0
lxml>=4.9.0
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
Write-Success "requirements.txt created"
Write-Host ""

# ============================================================================
# INSTALL PYTHON DEPENDENCIES
# ============================================================================

Write-Step "Menginstall Python dependencies..."
Write-Host ""

$packages = @(
    "selenium>=4.15.0",
    "beautifulsoup4>=4.12.0",
    "openpyxl>=3.1.0",
    "requests>=2.31.0",
    "pandas>=2.0.0",
    "psutil>=5.9.0",
    "lxml>=4.9.0"
)

foreach ($package in $packages) {
    $pkgName = $package -replace '>=.*', ''
    Write-Info "Installing $pkgName..."
    
    pip install $package --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Color "  ✓ $pkgName" -Color Green
    } else {
        Write-Color "  ✗ $pkgName (failed)" -Color Red
    }
}

Write-Host ""
Write-Success "Python dependencies terinstall"
Write-Host ""

# ============================================================================
# WEBDRIVER INFO
# ============================================================================

Write-Step "ChromeDriver..."
Write-Success "Selenium Manager akan handle ChromeDriver otomatis"
Write-Host ""

# ============================================================================
# SUCCESS MESSAGE
# ============================================================================

Write-Color "╔════════════════════════════════════════════════════════════════════╗" -Color Green
Write-Color "║                     SETUP SELESAI! ✓                               ║" -Color Green
Write-Color "╚════════════════════════════════════════════════════════════════════╝" -Color Green
Write-Host ""

# ============================================================================
# ASK TO RUN SCRAPER
# ============================================================================

Write-Color "Jalankan scraper sekarang? " -Color Cyan -NoNewline
$runNow = Read-Host "[y/n]"

if ($runNow -eq 'y' -or $runNow -eq 'Y') {
    Write-Host ""
    Write-Step "Menjalankan scraper..."
    Write-Host ""
    
    if (Test-Path "stable-lite.py") {
        python stable-lite.py
    } else {
        Write-Error-Msg "File stable-lite.py tidak ditemukan!"
        Write-Info "Pastikan file ada di directory ini"
    }
} else {
    Write-Host ""
    Write-Info "Untuk menjalankan scraper nanti, gunakan:"
    Write-Color "  .\venv\Scripts\Activate.ps1" -Color White
    Write-Color "  python stable-lite.py" -Color White
    Write-Host ""
}

pause