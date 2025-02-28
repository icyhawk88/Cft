#!/bin/bash
# This script combines all the artifacts into a single installer

set -e

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Create directory structure
mkdir -p "$TEMP_DIR/templates"
mkdir -p "$TEMP_DIR/scripts"

# Function to extract content from an artifact file
extract_content() {
    local file="$1"
    local output_file="$2"
    
    # Extract content between the content parameter tags
    sed -n '/<parameter name="content">/,/<\/antml:parameter>/p' "$file" | 
        sed '1d;$d' > "$output_file"
}

# Process the frontend dashboard HTML
echo "Processing frontend dashboard..."
extract_content "dashboard-frontend.json" "$TEMP_DIR/templates/index.html"

# Process the login page
echo "Processing login page..."
extract_content "login-page.json" "$TEMP_DIR/templates/login.html"

# Process the backend server
echo "Processing backend server..."
extract_content "dashboard-backend.json" "$TEMP_DIR/app.py"

# Process the auth module
echo "Processing auth module..."
extract_content "dashboard-backend-auth.json" "$TEMP_DIR/auth.py"

# Process the storage management module
echo "Processing storage management module..."
extract_content "storage-management.json" "$TEMP_DIR/storage.py"

# Create the wsgi file
echo "Creating wsgi file..."
cat > "$TEMP_DIR/wsgi.py" << 'EOL'
from app import app

if __name__ == "__main__":
    app.run()
EOL

# Create the monitoring script
echo "Creating monitoring script..."
cat > "$TEMP_DIR/scripts/monitor_firmware.py" << 'EOL'
#!/usr/bin/env python3
import os
import time
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('firmware_monitor')

WATCH_DIR = os.path.expanduser('~/firmware/incoming')
os.makedirs(WATCH_DIR, exist_ok=True)

class FirmwareHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"New firmware detected: {event.src_path}")
            self.process_firmware(event.src_path)
    
    def process_firmware(self, firmware_path):
        # Wait for file to be completely written
        time.sleep(5)
        
        # Here you would call your Flask API to create a new project
        # For now, we'll just log the detection
        logger.info(f"Would process: {firmware_path}")
        
        # Example of how to call the API (requires requests library)
        # import requests
        # files = {'file': open(firmware_path, 'rb')}
        # data = {'name': os.path.basename(firmware_path), 'extract_filesystem': 'true', 'scan_vulnerabilities': 'true'}
        # response = requests.post('http://localhost:5000/api/projects', files=files, data=data)
        # logger.info(f"API response: {response.status_code}")

def main():
    event_handler = FirmwareHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    
    logger.info(f"Starting monitoring of {WATCH_DIR}")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
EOL

# Extract the installer script content
echo "Processing installer script..."
extract_content "installer-script.json" "$TEMP_DIR/installer.sh"
chmod +x "$TEMP_DIR/installer.sh"

# Create the final package
echo "Creating the installer package..."
cd "$TEMP_DIR"
tar -czf files.tar.gz app.py auth.py storage.py wsgi.py templates scripts

# Create self-extracting installer
echo "Creating self-extracting installer..."
INSTALLER_SCRIPT="$TEMP_DIR/installer.sh"
FINAL_INSTALLER="../hardware-hacking-lab-installer.sh"

# Combine the installer script with the tar.gz archive
cat "$INSTALLER_SCRIPT" > "$FINAL_INSTALLER"
cat "files.tar.gz" >> "$FINAL_INSTALLER"
chmod +x "$FINAL_INSTALLER"

echo "Cleaning up temporary files..."
cd ..
rm -rf "$TEMP_DIR"

echo "Installation package created successfully: hardware-hacking-lab-installer.sh"
echo "Run it with: sudo ./hardware-hacking-lab-installer.sh"