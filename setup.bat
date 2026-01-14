@echo off
REM ============================================================================
REM SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP & INSTALLER (WINDOWS)
REM ============================================================================
REM Author  : Yahya Zulfikri
REM Project : Scraper Data Sekolah Seluruh Indonesia
REM License : MIT
REM ============================================================================

setlocal enabledelayedexpansion

REM Enable ANSI colors in Windows 10+
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

REM Color codes
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "MAGENTA=[95m"
set "WHITE=[97m"
set "NC=[0m"
set "BOLD=[1m"

REM Unicode symbols (fallback for older Windows)
set "CHECK=√"
set "CROSS=×"
set "ARROW=->"
set "INFO=i"
set "WARN=!"

cls

REM ============================================================================
REM HEADER
REM ============================================================================

echo %CYAN%
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║     SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP INSTALLER      ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo %NC%
echo %WHITE%Author  : Yahya Zulfikri%NC%
echo %WHITE%Project : Scraper Data Sekolah Seluruh Indonesia%NC%
echo %WHITE%License : MIT%NC%
echo.

REM ============================================================================
REM CHECK ADMIN PRIVILEGES
REM ============================================================================

echo %ARROW% %BOLD%Memeriksa hak akses...%NC%
net session >nul 2>&1
if %errorLevel% == 0 (
    echo %GREEN%√ Running as Administrator%NC%
) else (
    echo %YELLOW%! Running without Administrator privileges%NC%
    echo %YELLOW%  Beberapa fitur mungkin memerlukan admin%NC%
)
echo.

REM ============================================================================
REM CHECK INTERNET CONNECTION
REM ============================================================================

echo %ARROW% %BOLD%Memeriksa koneksi internet...%NC%
ping -n 1 google.com >nul 2>&1
if %errorLevel% == 0 (
    echo %GREEN%√ Koneksi internet tersedia%NC%
) else (
    ping -n 1 8.8.8.8 >nul 2>&1
    if !errorLevel! == 0 (
        echo %GREEN%√ Koneksi internet tersedia%NC%
    ) else (
        echo %RED%× Tidak ada koneksi internet!%NC%
        echo %RED%Setup dibatalkan. Silakan periksa koneksi Anda.%NC%
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM DETECT SYSTEM ARCHITECTURE
REM ============================================================================

echo %ARROW% %BOLD%Mendeteksi sistem...%NC%
echo %INFO% OS: %WHITE%Windows%NC%
echo %INFO% Architecture: %WHITE%%PROCESSOR_ARCHITECTURE%%NC%
echo %INFO% Processor: %WHITE%%PROCESSOR_IDENTIFIER%%NC%
echo.

REM ============================================================================
REM CHECK GIT
REM ============================================================================

echo %ARROW% %BOLD%Memeriksa Git...%NC%
where git >nul 2>&1
if %errorLevel% == 0 (
    echo %GREEN%√ Git sudah terinstall%NC%
    for /f "tokens=*" %%i in ('git --version') do set GIT_VERSION=%%i
    echo %INFO% Version: %WHITE%!GIT_VERSION!%NC%
) else (
    echo %YELLOW%! Git tidak ditemukan%NC%
    echo %INFO% Downloading Git installer...
    
    REM Download Git
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile 'git-installer.exe'}"
    
    if exist git-installer.exe (
        echo %INFO% Installing Git...
        start /wait git-installer.exe /VERYSILENT /NORESTART
        del git-installer.exe
        echo %GREEN%√ Git berhasil diinstall%NC%
    ) else (
        echo %RED%× Gagal download Git%NC%
        echo %INFO% Install manual dari: https://git-scm.com/download/win
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM CLONE REPOSITORY
REM ============================================================================

echo %ARROW% %BOLD%Cloning repository...%NC%
set REPO_URL=https://github.com/zulfikriyahya/scraping-dikdasmen.git
set TARGET_DIR=scraping-dikdasmen

if exist "%TARGET_DIR%" (
    echo %YELLOW%! Directory %TARGET_DIR% sudah ada%NC%
    set /p REPLY="Hapus dan clone ulang? (y/n): "
    if /i "!REPLY!"=="y" (
        rmdir /s /q "%TARGET_DIR%"
        git clone %REPO_URL% %TARGET_DIR%
    )
) else (
    git clone %REPO_URL% %TARGET_DIR%
)

if %errorLevel% == 0 (
    echo %GREEN%√ Repository berhasil di-clone%NC%
    cd %TARGET_DIR%
) else (
    echo %RED%× Gagal clone repository%NC%
    pause
    exit /b 1
)
echo.

REM ============================================================================
REM CHECK PYTHON
REM ============================================================================

echo %ARROW% %BOLD%Memeriksa Python...%NC%
where python >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('python --version') do set PY_VERSION=%%i
    echo %GREEN%√ Python sudah terinstall%NC%
    echo %INFO% Version: %WHITE%!PY_VERSION!%NC%
) else (
    where python3 >nul 2>&1
    if !errorLevel! == 0 (
        for /f "tokens=*" %%i in ('python3 --version') do set PY_VERSION=%%i
        echo %GREEN%√ Python3 sudah terinstall%NC%
        echo %INFO% Version: %WHITE%!PY_VERSION!%NC%
        set PYTHON_CMD=python3
    ) else (
        echo %YELLOW%! Python tidak ditemukan%NC%
        echo %INFO% Downloading Python installer...
        
        REM Download Python
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python-installer.exe'}"
        
        if exist python-installer.exe (
            echo %INFO% Installing Python...
            start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
            del python-installer.exe
            echo %GREEN%√ Python berhasil diinstall%NC%
            
            REM Refresh environment variables
            call refreshenv.cmd >nul 2>&1
            set PYTHON_CMD=python
        ) else (
            echo %RED%× Gagal download Python%NC%
            echo %INFO% Install manual dari: https://www.python.org/downloads/
            pause
            exit /b 1
        )
    )
)

if not defined PYTHON_CMD set PYTHON_CMD=python
echo.

REM ============================================================================
REM CHECK GOOGLE CHROME
REM ============================================================================

echo %ARROW% %BOLD%Memeriksa Google Chrome...%NC%

set CHROME_PATH=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=%LocalAppData%\Google\Chrome\Application\chrome.exe
)

if defined CHROME_PATH (
    echo %GREEN%√ Google Chrome terdeteksi%NC%
    echo %INFO% Path: %WHITE%!CHROME_PATH!%NC%
) else (
    echo %YELLOW%! Google Chrome tidak terdeteksi%NC%
    echo %INFO% Downloading Chrome installer...
    
    REM Download Chrome
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://dl.google.com/chrome/install/latest/chrome_installer.exe' -OutFile 'chrome-installer.exe'}"
    
    if exist chrome-installer.exe (
        echo %INFO% Installing Chrome...
        start /wait chrome-installer.exe /silent /install
        del chrome-installer.exe
        echo %GREEN%√ Chrome berhasil diinstall%NC%
    ) else (
        echo %RED%× Gagal download Chrome%NC%
        echo %INFO% Install manual dari: https://www.google.com/chrome/
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM CREATE VIRTUAL ENVIRONMENT
REM ============================================================================

echo %ARROW% %BOLD%Membuat virtual environment...%NC%

if exist "venv" (
    echo %GREEN%√ Virtual environment sudah ada%NC%
) else (
    echo %INFO% Creating venv...
    %PYTHON_CMD% -m venv venv
    if !errorLevel! == 0 (
        echo %GREEN%√ Virtual environment berhasil dibuat%NC%
    ) else (
        echo %RED%× Gagal membuat virtual environment%NC%
        pause
        exit /b 1
    )
)
echo.

REM ============================================================================
REM ACTIVATE VIRTUAL ENVIRONMENT
REM ============================================================================

echo %ARROW% %BOLD%Mengaktifkan virtual environment...%NC%
call venv\Scripts\activate.bat
if %errorLevel% == 0 (
    echo %GREEN%√ Virtual environment aktif%NC%
) else (
    echo %RED%× Gagal mengaktifkan venv%NC%
    pause
    exit /b 1
)
echo.

REM ============================================================================
REM UPGRADE PIP
REM ============================================================================

echo %ARROW% %BOLD%Upgrading pip...%NC%
python -m pip install --upgrade pip --quiet
echo %GREEN%√ Pip upgraded%NC%
echo.

REM ============================================================================
REM CREATE REQUIREMENTS.TXT
REM ============================================================================

echo %ARROW% %BOLD%Membuat requirements.txt...%NC%

(
echo # Python Dependencies for Scraper Data Sekolah
echo # Author: Yahya Zulfikri
echo # Project: Scraper Data Sekolah Seluruh Indonesia
echo.
echo selenium^>=4.15.0
echo beautifulsoup4^>=4.12.0
echo openpyxl^>=3.1.0
echo requests^>=2.31.0
echo pandas^>=2.0.0
echo psutil^>=5.9.0
echo lxml^>=4.9.0
) > requirements.txt

echo %GREEN%√ requirements.txt created%NC%
echo.

REM ============================================================================
REM INSTALL PYTHON DEPENDENCIES
REM ============================================================================

echo %ARROW% %BOLD%Menginstall Python dependencies...%NC%
echo.

echo %INFO% Installing selenium...
pip install "selenium>=4.15.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ selenium%NC%) else (echo %RED%  × selenium%NC%)

echo %INFO% Installing beautifulsoup4...
pip install "beautifulsoup4>=4.12.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ beautifulsoup4%NC%) else (echo %RED%  × beautifulsoup4%NC%)

echo %INFO% Installing openpyxl...
pip install "openpyxl>=3.1.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ openpyxl%NC%) else (echo %RED%  × openpyxl%NC%)

echo %INFO% Installing requests...
pip install "requests>=2.31.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ requests%NC%) else (echo %RED%  × requests%NC%)

echo %INFO% Installing pandas...
pip install "pandas>=2.0.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ pandas%NC%) else (echo %RED%  × pandas%NC%)

echo %INFO% Installing psutil...
pip install "psutil>=5.9.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ psutil%NC%) else (echo %RED%  × psutil%NC%)

echo %INFO% Installing lxml...
pip install "lxml>=4.9.0" --quiet
if %errorLevel% == 0 (echo %GREEN%  √ lxml%NC%) else (echo %RED%  × lxml%NC%)

echo.
echo %GREEN%√ Python dependencies terinstall%NC%
echo.

REM ============================================================================
REM WEBDRIVER INFO
REM ============================================================================

echo %ARROW% %BOLD%ChromeDriver...%NC%
echo %GREEN%√ Selenium Manager akan handle ChromeDriver otomatis%NC%
echo.

REM ============================================================================
REM SUCCESS MESSAGE
REM ============================================================================

echo %GREEN%
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                     SETUP SELESAI! √                               ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo %NC%
echo.

REM ============================================================================
REM ASK TO RUN SCRAPER
REM ============================================================================

set /p RUN_NOW="%CYAN%Jalankan scraper sekarang? %NC%[y/n]: "

if /i "%RUN_NOW%"=="y" (
    echo.
    echo %ARROW% %BOLD%Menjalankan scraper...%NC%
    echo.
    
    if exist "stable-lite.py" (
        python stable-lite.py
    ) else (
        echo %RED%× File stable-lite.py tidak ditemukan!%NC%
        echo %INFO% Pastikan file ada di directory ini
    )
) else (
    echo.
    echo %INFO% Untuk menjalankan scraper nanti, gunakan:
    echo %WHITE%  venv\Scripts\activate%NC%
    echo %WHITE%  python stable-lite.py%NC%
    echo.
)

pause