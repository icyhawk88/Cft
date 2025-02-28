#!/bin/bash
# Hardware Hacking Lab Installer
# This script will install all components of the Hardware Hacking Lab

set -e

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║  ${GREEN}Hardware Hacking Lab - Installation Guide${BLUE}             ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# Get the actual username (not root or sudo user)
if [ -n "$SUDO_USER" ]; then
  ACTUAL_USER="$SUDO_USER"
  USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
  ACTUAL_USER="$USER"
  USER_HOME="$HOME"
fi

# Create temp directory for files
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to prompt for input with a default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local input
    
    read -p "$prompt [$default]: " input
    echo "${input:-$default}"
}

# Function to prompt for yes/no with default
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [[ "$default" == "y" ]]; then
        read -p "$prompt [Y/n]: " input
        [[ "${input:-y}" =~ ^[Yy] ]]
    else
        read -p "$prompt [y/N]: " input
        [[ "${input:-n}" =~ ^[Yy] ]]
    fi
}

# Banner for section
section_banner() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

# Display a spinner for long-running commands
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Function to extract files from this script
extract_files() {
    section_banner "Extracting Files"
    echo "Extracting necessary files..."
    
    # Skip to the __FILES__ marker in this script
    local line_count=0
    local start_line=0
    
    while read -r line; do
        ((line_count++))
        if [[ "$line" == "__FILES__" ]]; then
            start_line=$line_count
            break
        fi
    done < "$0"
    
    if [[ $start_line -eq 0 ]]; then
        echo -e "${RED}Error: Could not find file marker in script${NC}"
        exit 1
    fi
    
    # Extract files from this script
    tail -n +$((start_line + 1)) "$0" | tar xz -C "$TEMP_DIR"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Files extracted successfully${NC}"
    else
        echo -e "${RED}Failed to extract files${NC}"
        exit 1
    fi
}

# Gather user inputs
gather_inputs() {
    section_banner "Configuration"
    
    echo -e "${YELLOW}Please provide the following information:${NC}"
    echo ""
    
    # Instance information
    INSTANCE_HOSTNAME=$(prompt_with_default "Enter your OCI instance hostname or IP" "localhost")
    
    # Installation directory
    INSTALL_DIR=$(prompt_with_default "Installation directory" "$USER_HOME/hardware-hacking-lab")
    
    # Admin credentials
    ADMIN_USER=$(prompt_with_default "Admin username" "admin")
    ADMIN_PASS=$(prompt_with_default "Admin password" "$(openssl rand -hex 8)")
    
    # Storage settings
    MAX_STORAGE=$(prompt_with_default "Maximum storage for firmware files (GB)" "50")
    RETENTION_DAYS=$(prompt_with_default "Number of days to keep old analysis results" "30")
    
    # Ask about additional tools
    INSTALL_EXTRAS=$(prompt_yes_no "Install additional tools (may take longer)?" "y")
    
    # Ask about securing with SSL
    SETUP_SSL=$(prompt_yes_no "Setup HTTPS with Let's Encrypt? (requires a domain name)" "n")
    if $SETUP_SSL; then
        DOMAIN_NAME=$(prompt_with_default "Enter your domain name" "example.com")
    fi
    
    # Confirm settings
    echo ""
    echo -e "${YELLOW}Please review your settings:${NC}"
    echo "Instance hostname: $INSTANCE_HOSTNAME"
    echo "Installation directory: $INSTALL_DIR"
    echo "Admin username: $ADMIN_USER"
    echo "Admin password: $ADMIN_PASS"
    echo "Maximum storage: ${MAX_STORAGE}GB"
    echo "Result retention: ${RETENTION_DAYS} days"
    echo "Install extra tools: $(if $INSTALL_EXTRAS; then echo 'Yes'; else echo 'No'; fi)"
    echo "Setup SSL: $(if $SETUP_SSL; then echo "Yes, for domain $DOMAIN_NAME"; else echo 'No'; fi)"
    echo ""
    
    if ! $(prompt_yes_no "Are these settings correct?" "y"); then
        echo "Restarting configuration..."
        gather_inputs
    fi
}

# Install dependencies
install_dependencies() {
    section_banner "Installing Dependencies"
    
    echo "Updating system packages..."
    apt update &
    PID=$!
    spinner $PID
    wait $PID
    
    echo "Installing required packages..."
    apt install -y build-essential git python3-pip python3-dev python3-venv \
        cmake libffi-dev libssl-dev unzip wget curl tmux vim htop ncdu \
        autoconf automake libtool pkg-config nginx certbot python3-certbot-nginx \
        binwalk firmware-mod-kit &
    PID=$!
    spinner $PID
    wait $PID
    
    # Install Docker if not already installed
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        apt install -y docker.io docker-compose
        systemctl enable --now docker
        usermod -aG docker "$ACTUAL_USER" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Dependencies installed successfully${NC}"
}

# Set up application directories and files
setup_application() {
    section_banner "Setting Up Application"
    
    echo "Creating directory structure..."
    mkdir -p "$INSTALL_DIR/static" "$INSTALL_DIR/templates" "$INSTALL_DIR/scripts"
    mkdir -p "$USER_HOME/tools" "$USER_HOME/firmware"
    mkdir -p "$USER_HOME/firmware/uploads" "$USER_HOME/firmware/results" "$USER_HOME/firmware/incoming"
    
    # Copy files from temp directory to install directory
    echo "Copying application files..."
    cp "$TEMP_DIR/app.py" "$INSTALL_DIR/"
    cp "$TEMP_DIR/auth.py" "$INSTALL_DIR/"
    cp "$TEMP_DIR/storage.py" "$INSTALL_DIR/"
    cp "$TEMP_DIR/wsgi.py" "$INSTALL_DIR/"
    cp "$TEMP_DIR/templates/index.html" "$INSTALL_DIR/templates/"
    cp "$TEMP_DIR/templates/login.html" "$INSTALL_DIR/templates/"
    cp "$TEMP_DIR/scripts/monitor_firmware.py" "$INSTALL_DIR/scripts/"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/app.py"
    chmod +x "$INSTALL_DIR/scripts/monitor_firmware.py"
    
    # Create .env file
    echo "Creating configuration file..."
    cat > "$INSTALL_DIR/.env" << EOL
# API Key for accessing protected endpoints
API_KEY=$(openssl rand -hex 16)

# Admin credentials for the dashboard
ADMIN_USERNAME=$ADMIN_USER
ADMIN_PASSWORD=$ADMIN_PASS

# Configuration for automatic cleanup
MAX_STORAGE_GB=$MAX_STORAGE
AUTO_CLEANUP_DAYS=$RETENTION_DAYS
EOL

    # Ensure proper ownership
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR" "$USER_HOME/tools" "$USER_HOME/firmware"
    chmod 600 "$INSTALL_DIR/.env"
    
    echo -e "${GREEN}Application files set up successfully${NC}"
}

# Set up Python virtual environment
setup_virtualenv() {
    section_banner "Setting Up Python Environment"
    
    echo "Creating virtual environment..."
    su - "$ACTUAL_USER" -c "python3 -m venv $INSTALL_DIR/venv"
    
    echo "Installing Python packages..."
    su - "$ACTUAL_USER" -c "source $INSTALL_DIR/venv/bin/activate && pip install --upgrade pip"
    su - "$ACTUAL_USER" -c "source $INSTALL_DIR/venv/bin/activate && pip install flask gunicorn werkzeug watchdog requests pymongo bcrypt python-dotenv"
    
    echo -e "${GREEN}Python environment set up successfully${NC}"
}

# Install reverse engineering tools
install_tools() {
    section_banner "Installing Reverse Engineering Tools"
    
    # Install basic tools
    echo "Installing Ghidra..."
    if [ ! -d "$USER_HOME/tools/ghidra" ]; then
        mkdir -p "$USER_HOME/tools/ghidra"
        cd "$USER_HOME/tools/ghidra"
        wget -q https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_10.3.2_build/ghidra_10.3.2_PUBLIC_20230711.zip
        unzip -q ghidra_10.3.2_PUBLIC_20230711.zip
        rm ghidra_10.3.2_PUBLIC_20230711.zip
        chown -R "$ACTUAL_USER:$ACTUAL_USER" "$USER_HOME/tools/ghidra"
    fi
    
    echo "Installing radare2..."
    if ! command -v r2 &> /dev/null; then
        cd "$USER_HOME/tools"
        git clone https://github.com/radareorg/radare2.git
        cd radare2
        ./sys/install.sh
    fi
    
    echo "Installing firmware analysis tools..."
    if [ ! -d "$USER_HOME/tools/firmwalker" ]; then
        git clone https://github.com/craigz28/firmwalker.git "$USER_HOME/tools/firmwalker"
        chmod +x "$USER_HOME/tools/firmwalker/firmwalker.sh"
    fi
    
    if [ ! -d "$USER_HOME/tools/firmware-analysis-toolkit" ]; then
        git clone https://github.com/attify/firmware-analysis-toolkit.git "$USER_HOME/tools/firmware-analysis-toolkit"
    fi
    
    # For Beken chips specifically
    if [ ! -d "$USER_HOME/tools/beken" ]; then
        mkdir -p "$USER_HOME/tools/beken"
        cd "$USER_HOME/tools/beken"
        git clone https://github.com/pvvx/ATC_MiThermometer.git
    fi
    
    # Install additional tools if requested
    if $INSTALL_EXTRAS; then
        echo "Installing additional tools..."
        
        # Install Firmware-Mod-Kit
        if [ ! -d "$USER_HOME/tools/firmware-mod-kit" ]; then
            git clone https://github.com/rampageX/firmware-mod-kit.git "$USER_HOME/tools/firmware-mod-kit"
            cd "$USER_HOME/tools/firmware-mod-kit"
            ./configure && make
        fi
        
        # Install Qiling Framework
        su - "$ACTUAL_USER" -c "source $INSTALL_DIR/venv/bin/activate && pip install qiling"
        
        # Install Angr
        su - "$ACTUAL_USER" -c "source $INSTALL_DIR/venv/bin/activate && pip install angr"
    fi
    
    echo -e "${GREEN}Reverse engineering tools installed successfully${NC}"
}

# Configure system services
setup_services() {
    section_banner "Configuring System Services"
    
    echo "Creating systemd service for the web dashboard..."
    cat > /etc/systemd/system/hardware-hacking-dashboard.service << EOL
[Unit]
Description=Hardware Hacking Dashboard
After=network.target

[Service]
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 --chdir $INSTALL_DIR wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    echo "Creating systemd service for firmware monitoring..."
    cat > /etc/systemd/system/firmware-monitor.service << EOL
[Unit]
Description=Firmware Monitor Service
After=network.target

[Service]
User=$ACTUAL_USER
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/scripts/monitor_firmware.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOL

    echo "Configuring Nginx..."
    cat > /etc/nginx/sites-available/hardware-hacking-dashboard << EOL
server {
    listen 80;
    server_name $INSTANCE_HOSTNAME;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; font-src 'self' https://cdnjs.cloudflare.com;";

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $INSTALL_DIR/static;
    }
    
    # Increase request size limit for firmware uploads
    client_max_body_size 100M;
}
EOL

    # Enable the site
    ln -sf /etc/nginx/sites-available/hardware-hacking-dashboard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Set up SSL if requested
    if $SETUP_SSL; then
        echo "Setting up HTTPS with Let's Encrypt..."
        certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --redirect --email "$ACTUAL_USER@$DOMAIN_NAME"
    fi
    
    echo "Reloading systemd and starting services..."
    systemctl daemon-reload
    systemctl enable nginx
    systemctl restart nginx
    systemctl enable hardware-hacking-dashboard.service
    systemctl start hardware-hacking-dashboard.service
    systemctl enable firmware-monitor.service
    systemctl start firmware-monitor.service
    
    echo -e "${GREEN}Services configured and started successfully${NC}"
}

# Create a test script
create_test_script() {
    section_banner "Creating Test Script"
    
    echo "Creating setup verification script..."
    cat > "$INSTALL_DIR/test_setup.py" << 'EOL'
#!/usr/bin/env python3
import os
import sys
import subprocess
import json

def check_command(command):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        return False

def main():
    print("Hardware Hacking Lab Setup Verification")
    print("======================================")
    
    # Check Python and virtual environment
    print("\nChecking Python environment:")
    python_version = sys.version.split()[0]
    print(f"✓ Python version: {python_version}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Running in virtual environment")
    else:
        print("✗ Not running in virtual environment")
    
    # Check installed tools
    print("\nChecking installed tools:")
    tools = {
        "binwalk": "binwalk --help",
        "radare2": "r2 -v",
        "Ghidra": f"test -d {os.path.expanduser('~/tools/ghidra')}",
        "Docker": "docker --version"
    }
    
    for tool, command in tools.items():
        if check_command(command):
            print(f"✓ {tool} is installed")
        else:
            print(f"✗ {tool} is NOT installed")
    
    # Check directory structure
    print("\nChecking directory structure:")
    directories = [
        "~/firmware",
        "~/firmware/uploads",
        "~/firmware/results",
        "~/tools"
    ]
    
    for directory in directories:
        path = os.path.expanduser(directory)
        if os.path.isdir(path):
            print(f"✓ {directory} exists")
        else:
            print(f"✗ {directory} does NOT exist")
    
    # Check web server
    print("\nChecking web server:")
    if check_command("curl -s http://localhost:5000 > /dev/null"):
        print("✓ Web server is running on port 5000")
    else:
        print("✗ Web server is NOT running on port 5000")
    
    print("\nSetup verification complete!")

if __name__ == "__main__":
    main()
EOL

    chmod +x "$INSTALL_DIR/test_setup.py"
    chown "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR/test_setup.py"
    
    echo -e "${GREEN}Test script created successfully${NC}"
}

# Display completion message
display_completion() {
    section_banner "Installation Complete"
    
    echo -e "${GREEN}Your Hardware Hacking Lab has been installed!${NC}"
    echo ""
    echo -e "Access the dashboard at: ${BLUE}http://$INSTANCE_HOSTNAME${NC}"
    if $SETUP_SSL; then
        echo -e "Secure access: ${BLUE}https://$DOMAIN_NAME${NC}"
    fi
    echo ""
    echo -e "Login credentials:"
    echo -e "Username: ${YELLOW}$ADMIN_USER${NC}"
    echo -e "Password: ${YELLOW}$ADMIN_PASS${NC}"
    echo ""
    echo -e "To upload firmware files for automatic processing:"
    echo -e "Copy files to: ${BLUE}$USER_HOME/firmware/incoming${NC}"
    echo ""
    echo -e "To verify the installation:"
    echo -e "Run: ${BLUE}$INSTALL_DIR/test_setup.py${NC}"
    echo ""
    echo -e "Logs can be found at:"
    echo -e "- Dashboard: ${BLUE}$INSTALL_DIR/server.log${NC}"
    echo -e "- Nginx: ${BLUE}/var/log/nginx/error.log${NC}"
    echo -e "- System services: ${BLUE}journalctl -u hardware-hacking-dashboard.service${NC}"
    echo ""
    echo -e "${PURPLE}Happy hardware hacking!${NC}"
}

# Main installation flow
main() {
    extract_files
    gather_inputs
    install_dependencies
    setup_application
    setup_virtualenv
    install_tools
    setup_services
    create_test_script
    display_completion
    
    # Clean up temporary files
    rm -rf "$TEMP_DIR"
}

# Start installation
main

# Exit before the file content
exit 0

# Mark the start of embedded files
__FILES__