#!/bin/bash

# ============================================================================
# SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP & INSTALLER
# ============================================================================
# Author  : Yahya Zulfikri
# Project : Scraper Data Sekolah Seluruh Indonesia
# License : MIT
# ============================================================================

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Unicode symbols
CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
ARROW="${CYAN}➜${NC}"
INFO="${BLUE}ℹ${NC}"
WARN="${YELLOW}⚠${NC}"

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║     SCRAPER DATA SEKOLAH SELURUH INDONESIA - SETUP INSTALLER      ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${WHITE}Author  : Yahya Zulfikri${NC}"
    echo -e "${WHITE}Project : Scraper Data Sekolah Seluruh Indonesia${NC}"
    echo -e "${WHITE}License : MIT${NC}"
    echo ""
}

print_step() {
    echo -e "${ARROW} ${BOLD}$1${NC}"
}

print_success() {
    echo -e "${CHECK} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "${CROSS} ${RED}$1${NC}"
}

print_info() {
    echo -e "${INFO} ${BLUE}$1${NC}"
}

print_warning() {
    echo -e "${WARN} ${YELLOW}$1${NC}"
}

# ============================================================================
# CHECK INTERNET CONNECTION
# ============================================================================

check_internet() {
    print_step "Memeriksa koneksi internet..."
    
    if ping -c 1 google.com &> /dev/null || ping -c 1 8.8.8.8 &> /dev/null; then
        print_success "Koneksi internet tersedia"
        return 0
    else
        print_error "Tidak ada koneksi internet!"
        print_error "Setup dibatalkan. Silakan periksa koneksi Anda."
        exit 1
    fi
}

# ============================================================================
# DETECT OS & ARCHITECTURE
# ============================================================================

detect_system() {
    print_step "Mendeteksi sistem operasi dan arsitektur..."
    
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    case "$OS" in
        Linux*)
            OS_TYPE="Linux"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO=$ID
                DISTRO_NAME=$NAME
            fi
            ;;
        Darwin*)
            OS_TYPE="macOS"
            DISTRO="macos"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="Windows"
            DISTRO="windows"
            ;;
        *)
            OS_TYPE="Unknown"
            ;;
    esac
    
    print_info "OS: ${WHITE}$OS_TYPE ($DISTRO_NAME)${NC}"
    print_info "Architecture: ${WHITE}$ARCH${NC}"
}

# ============================================================================
# CLONE REPOSITORY
# ============================================================================

clone_repo() {
    print_step "Cloning repository..."
    
    REPO_URL="https://github.com/zulfikriyahya/scraping-dikdasmen.git"
    TARGET_DIR="scraping-dikdasmen"
    
    if [ -d "$TARGET_DIR" ]; then
        print_warning "Directory $TARGET_DIR sudah ada"
        read -p "Hapus dan clone ulang? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$TARGET_DIR"
            git clone "$REPO_URL" "$TARGET_DIR"
        fi
    else
        git clone "$REPO_URL" "$TARGET_DIR"
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Repository berhasil di-clone"
        cd "$TARGET_DIR" || exit 1
    else
        print_error "Gagal clone repository"
        exit 1
    fi
}

# ============================================================================
# INSTALL DEPENDENCIES - LINUX
# ============================================================================

install_deps_linux() {
    print_step "Menginstall dependencies untuk Linux ($DISTRO)..."
    
    case "$DISTRO" in
        ubuntu|debian|linuxmint|pop)
            # Update package list
            print_info "Updating package list..."
            sudo apt-get update -qq
            
            # Install Python3
            if ! command -v python3 &> /dev/null; then
                print_info "Installing Python3..."
                sudo apt-get install -y python3 python3-pip python3-venv
            else
                print_success "Python3 sudah terinstall"
            fi
            
            # Install Chrome dependencies
            print_info "Installing Chrome/Chromium dependencies..."
            sudo apt-get install -y \
                libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
                libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
                libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
                libpangocairo-1.0-0 libxshmfence1 chromium-browser
            ;;
            
        fedora|rhel|centos)
            print_info "Updating package list..."
            sudo dnf update -y -q
            
            if ! command -v python3 &> /dev/null; then
                print_info "Installing Python3..."
                sudo dnf install -y python3 python3-pip
            else
                print_success "Python3 sudah terinstall"
            fi
            
            print_info "Installing Chrome dependencies..."
            sudo dnf install -y \
                nss atk at-spi2-atk cups-libs libdrm libxkbcommon \
                libXcomposite libXdamage libXrandr mesa-libgbm alsa-lib \
                pango cairo chromium
            ;;
            
        arch|manjaro)
            print_info "Updating package list..."
            sudo pacman -Sy --noconfirm
            
            if ! command -v python3 &> /dev/null; then
                print_info "Installing Python3..."
                sudo pacman -S --noconfirm python python-pip
            else
                print_success "Python3 sudah terinstall"
            fi
            
            print_info "Installing Chrome dependencies..."
            sudo pacman -S --noconfirm \
                nss atk at-spi2-atk cups libdrm libxkbcommon \
                libxcomposite libxdamage libxrandr mesa alsa-lib \
                pango cairo chromium
            ;;
            
        *)
            print_warning "Distro tidak dikenali, mencoba instalasi generic..."
            if ! command -v python3 &> /dev/null; then
                print_error "Python3 tidak ditemukan. Install manual: python3, python3-pip"
                exit 1
            fi
            ;;
    esac
    
    print_success "Dependencies Linux terinstall"
}

# ============================================================================
# INSTALL DEPENDENCIES - MACOS
# ============================================================================

install_deps_macos() {
    print_step "Menginstall dependencies untuk macOS..."
    
    # Check Homebrew
    if ! command -v brew &> /dev/null; then
        print_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        print_success "Homebrew sudah terinstall"
    fi
    
    # Install Python3
    if ! command -v python3 &> /dev/null; then
        print_info "Installing Python3..."
        brew install python3
    else
        print_success "Python3 sudah terinstall"
    fi
    
    # Install Chrome
    if [ ! -d "/Applications/Google Chrome.app" ]; then
        print_info "Installing Google Chrome..."
        brew install --cask google-chrome
    else
        print_success "Google Chrome sudah terinstall"
    fi
    
    print_success "Dependencies macOS terinstall"
}

# ============================================================================
# INSTALL DEPENDENCIES - WINDOWS (WSL/MSYS)
# ============================================================================

install_deps_windows() {
    print_step "Menginstall dependencies untuk Windows..."
    
    print_warning "Untuk Windows, gunakan WSL atau install manual:"
    print_info "1. Python 3.x dari python.org"
    print_info "2. Google Chrome dari google.com/chrome"
    print_info "3. Jalankan: pip install -r requirements.txt"
    
    read -p "Lanjutkan dengan Python di Windows/WSL? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# ============================================================================
# INSTALL PYTHON DEPENDENCIES
# ============================================================================

install_python_deps() {
    print_step "Menginstall Python dependencies..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Membuat virtual environment..."
        python3 -m venv venv
    else
        print_success "Virtual environment sudah ada"
    fi
    
    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip -q
    
    # Install packages
    print_info "Installing Python packages..."
    
    PACKAGES=(
        "selenium>=4.15.0"
        "beautifulsoup4>=4.12.0"
        "openpyxl>=3.1.0"
        "requests>=2.31.0"
        "pandas>=2.0.0"
        "psutil>=5.9.0"
    )
    
    for package in "${PACKAGES[@]}"; do
        pkg_name=$(echo $package | cut -d'>' -f1)
        print_info "Installing $pkg_name..."
        pip install "$package" -q
        
        if [ $? -eq 0 ]; then
            echo -e "  ${CHECK} $pkg_name"
        else
            echo -e "  ${CROSS} $pkg_name (failed)"
        fi
    done
    
    print_success "Python dependencies terinstall"
}

# ============================================================================
# INSTALL WEBDRIVER
# ============================================================================

install_webdriver() {
    print_step "Memeriksa ChromeDriver..."
    
    # ChromeDriver akan di-download otomatis oleh Selenium Manager
    # Cek apakah Chrome/Chromium terinstall
    
    if command -v google-chrome &> /dev/null || \
       command -v chromium &> /dev/null || \
       command -v chromium-browser &> /dev/null || \
       [ -d "/Applications/Google Chrome.app" ]; then
        print_success "Chrome/Chromium terdeteksi"
        print_info "Selenium Manager akan handle ChromeDriver secara otomatis"
    else
        print_warning "Chrome/Chromium tidak terdeteksi"
        print_info "Install Google Chrome atau Chromium secara manual"
    fi
}

# ============================================================================
# CREATE REQUIREMENTS.TXT
# ============================================================================

create_requirements() {
    print_step "Membuat requirements.txt..."
    
    cat > requirements.txt << EOF
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
EOF
    
    print_success "requirements.txt created"
}

# ============================================================================
# RUN SCRAPER
# ============================================================================

run_scraper() {
    print_step "Menjalankan scraper..."
    echo ""
    
    if [ -f "stable-lite.py" ]; then
        python3 stable-lite.py
    else
        print_error "File stable-lite.py tidak ditemukan!"
        print_info "Pastikan file ada di directory ini"
        exit 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header
    
    # Check internet
    check_internet
    echo ""
    
    # Detect system
    detect_system
    echo ""
    
    # Clone repository
    clone_repo
    echo ""
    
    # Install dependencies based on OS
    case "$OS_TYPE" in
        Linux)
            install_deps_linux
            ;;
        macOS)
            install_deps_macos
            ;;
        Windows)
            install_deps_windows
            ;;
        *)
            print_error "OS tidak didukung: $OS_TYPE"
            exit 1
            ;;
    esac
    echo ""
    
    # Create requirements.txt
    create_requirements
    echo ""
    
    # Install Python dependencies
    install_python_deps
    echo ""
    
    # Install webdriver
    install_webdriver
    echo ""
    
    # Success message
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║                     SETUP SELESAI! ✓                               ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Ask to run scraper
    echo ""
    read -p "$(echo -e ${CYAN}Jalankan scraper sekarang? ${NC}[y/n]: )" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        run_scraper
    else
        print_info "Untuk menjalankan scraper nanti, gunakan:"
        echo -e "${WHITE}  source venv/bin/activate${NC}"
        echo -e "${WHITE}  python3 stable-lite.py${NC}"
    fi
}

# Run main
main