# Hardware Hacking Lab

A complete environment for firmware analysis, reverse engineering, and hardware hacking.

![Hardware Hacking Lab Dashboard](dashboard_screenshot.png)

## Overview

The Hardware Hacking Lab provides a comprehensive web-based dashboard and toolset for hardware hacking, firmware analysis, and reverse engineering. It allows you to:

- Upload and analyze firmware files
- Track analysis progress in real-time
- View and extract components from firmware
- Identify potential vulnerabilities
- Manage your hardware hacking projects
- Automate the analysis of new firmware files

## Installation Options

### Option 1: Command-Line Installer

```bash
# Download the installer
wget https://example.com/hardware-hacking-lab-installer.sh

# Make it executable
chmod +x hardware-hacking-lab-installer.sh

# Run the installer
sudo ./hardware-hacking-lab-installer.sh
```

The installer will guide you through the installation process, prompting for necessary information.

### Option 2: GUI Installer

```bash
# Download the GUI installer
wget https://example.com/hardware-hacking-lab-gui-installer.py

# Make it executable
chmod +x hardware-hacking-lab-gui-installer.py

# Run the installer
./hardware-hacking-lab-gui-installer.py
```

The GUI installer provides a user-friendly interface to configure and install the Hardware Hacking Lab.

## System Requirements

- Ubuntu 20.04 LTS or later (other distributions may work but are not officially supported)
- 2GB RAM minimum (4GB or more recommended)
- 20GB free disk space minimum (50GB or more recommended)
- Python 3.8 or later
- Internet connection for downloading dependencies

## Files in This Package

- `hardware-hacking-lab-installer.sh`: Command-line installer script
- `hardware-hacking-lab-gui-installer.py`: GUI installer script
- `combine.sh`: Script to combine the artifacts into the installer
- `README.md`: This file

## Building from Source

If you've made modifications to the source code or want to rebuild the installer:

```bash
# Combine the artifacts into the installer
./combine.sh

# The installer will be created as hardware-hacking-lab-installer.sh
```

## Accessing the Dashboard

After installation, you can access the dashboard at:

```
http://your-server-ip
```

The default login credentials are:
- Username: admin
- Password: (set during installation)

## Using the Hardware Hacking Lab

### Uploading Firmware

1. Log in to the dashboard
2. Click the "Upload Firmware" button
3. Drag & drop or select a firmware file
4. Configure analysis options
5. Click "Start Analysis"

### Automatic Processing

You can place firmware files in the `~/firmware/incoming` directory for automatic processing:

```bash
# Copy firmware to the incoming directory
cp router_firmware.bin ~/firmware/incoming/
```

The system will automatically detect and analyze new files.

### Using Reverse Engineering Tools

The Hardware Hacking Lab includes several popular reverse engineering tools:

- **Binwalk**: `binwalk -e firmware.bin`
- **Radare2**: `r2 firmware.bin`
- **Ghidra**: `~/tools/ghidra/ghidraRun`

## Extending the Lab

### Adding Custom Tools

You can add custom tools to the lab by:

1. Installing the tool on your system
2. Updating the dashboard code to integrate with the tool
3. Restarting the dashboard service

### Modifying the Dashboard

The dashboard is built with Flask and can be customized:

- Frontend files: `~/hardware-hacking-lab/templates/`
- Backend code: `~/hardware-hacking-lab/app.py`

After making changes, restart the service:

```bash
sudo systemctl restart hardware-hacking-dashboard
```

## Troubleshooting

### Common Issues

- **Dashboard not accessible**: Check if the service is running with `sudo systemctl status hardware-hacking-dashboard`
- **Upload fails**: Check the maximum file size setting in Nginx config
- **Analysis fails**: Check the logs for specific errors

### Logs

- Dashboard logs: `~/hardware-hacking-lab/server.log`
- Nginx logs: `/var/log/nginx/error.log`
- System service logs: `journalctl -u hardware-hacking-dashboard.service`

## Security Considerations

For production use, consider these security enhancements:

1. Keep the system and tools updated
2. Change the admin password regularly
3. Set up network-level security (firewall, VPN)
4. Implement regular backups
5. Monitor system access and logs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

The Hardware Hacking Lab utilizes several open-source tools and libraries, including:

- Binwalk: https://github.com/ReFirmLabs/binwalk
- Radare2: https://github.com/radareorg/radare2
- Ghidra: https://github.com/NationalSecurityAgency/ghidra
- Flask: https://flask.palletsprojects.com/
- Tailwind CSS: https://tailwindcss.com/

## Contributing

We welcome contributions to the Hardware Hacking Lab! Please feel free to submit issues and pull requests.