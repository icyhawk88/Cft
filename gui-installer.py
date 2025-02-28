#!/usr/bin/env python3
# GUI installer for Hardware Hacking Lab
# Save this as gui_installer.py

import os
import sys
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import shutil
import random
import string

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Hacking Lab Installer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set app icon
        # self.root.iconbitmap("icon.ico")  # Uncomment if you have an icon
        
        # Initialize variables
        self.setup_variables()
        
        # Create styles
        self.setup_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        self.setup_welcome_tab()
        self.setup_installation_tab()
        self.setup_tools_tab()
        self.setup_security_tab()
        self.setup_review_tab()
        self.setup_progress_tab()
        
        # Setup bottom buttons
        self.setup_navigation_buttons()
        
        # Temp directory for extracted files
        self.temp_dir = None
        
    def setup_variables(self):
        # Configuration variables
        self.install_dir = tk.StringVar(value=os.path.expanduser("~/hardware-hacking-lab"))
        self.hostname = tk.StringVar(value="localhost")
        self.admin_user = tk.StringVar(value="admin")
        self.admin_pass = tk.StringVar(value=self.generate_password())
        self.max_storage = tk.StringVar(value="50")
        self.retention_days = tk.StringVar(value="30")
        self.install_extras = tk.BooleanVar(value=True)
        self.setup_ssl = tk.BooleanVar(value=False)
        self.domain_name = tk.StringVar(value="example.com")
        
        # Installation progress
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_text = tk.StringVar(value="Ready to install")
        
    def generate_password(self, length=12):
        """Generate a random secure password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))
        
    def setup_styles(self):
        # Configure styles for a modern look
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TNotebook", background="#f5f5f5")
        style.configure("TNotebook.Tab", padding=[10, 5], font=('Arial', 10))
        style.configure("TLabel", background="#f5f5f5", font=('Arial', 10))
        style.configure("Header.TLabel", font=('Arial', 16, 'bold'))
        style.configure("Subheader.TLabel", font=('Arial', 12, 'bold'))
        style.configure("TEntry", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10))
        style.configure("Next.TButton", font=('Arial', 10, 'bold'))
        
    def setup_welcome_tab(self):
        # Welcome tab
        welcome_tab = ttk.Frame(self.notebook)
        self.notebook.add(welcome_tab, text="Welcome")
        
        # Header
        ttk.Label(welcome_tab, text="Welcome to Hardware Hacking Lab", style="Header.TLabel").pack(pady=20)
        
        # Logo or image could go here
        ttk.Label(welcome_tab, text="🔧 🔍 🛠️", font=('Arial', 48)).pack(pady=20)
        
        # Description
        desc_text = """The Hardware Hacking Lab provides a complete environment for firmware analysis, 
reverse engineering, and hardware hacking. This installer will set up the lab on your system,
including a web dashboard and all necessary tools.

Features:
• Web interface for managing firmware analysis
• Automated extraction and analysis of firmware files
• Integration with reverse engineering tools
• Secure storage of results
• Monitoring of incoming firmware files

Click 'Next' to begin the installation process."""

        ttk.Label(welcome_tab, text=desc_text, wraplength=600, justify="center").pack(pady=20)
        
    def setup_installation_tab(self):
        # Installation options tab
        install_tab = ttk.Frame(self.notebook)
        self.notebook.add(install_tab, text="Installation")
        
        # Header
        ttk.Label(install_tab, text="Installation Options", style="Header.TLabel").pack(pady=10)
        
        # Create form frame
        form_frame = ttk.Frame(install_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Installation directory
        ttk.Label(form_frame, text="Installation Directory:", style="Subheader.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(form_frame)
        dir_frame.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)
        ttk.Entry(dir_frame, textvariable=self.install_dir, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(dir_frame, text="Browse", command=self.browse_install_dir).pack(side=tk.RIGHT, padx=5)
        
        # Hostname or IP
        ttk.Label(form_frame, text="Server Hostname/IP:", style="Subheader.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.hostname, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Admin credentials
        ttk.Label(form_frame, text="Admin Username:", style="Subheader.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.admin_user, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Admin Password:", style="Subheader.TLabel").grid(row=3, column=0, sticky=tk.W, pady=5)
        pw_frame = ttk.Frame(form_frame)
        pw_frame.grid(row=3, column=1, sticky=tk.W + tk.E, pady=5)
        ttk.Entry(pw_frame, textvariable=self.admin_pass, width=40, show="*").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(pw_frame, text="Generate", command=lambda: self.admin_pass.set(self.generate_password())).pack(side=tk.RIGHT, padx=5)
        
        # Configure grid column weighting
        form_frame.columnconfigure(1, weight=1)
        
    def setup_tools_tab(self):
        # Tools and storage options tab
        tools_tab = ttk.Frame(self.notebook)
        self.notebook.add(tools_tab, text="Tools & Storage")
        
        # Header
        ttk.Label(tools_tab, text="Tools and Storage Options", style="Header.TLabel").pack(pady=10)
        
        # Create form frame
        form_frame = ttk.Frame(tools_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Storage settings
        ttk.Label(form_frame, text="Storage Settings", style="Subheader.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Label(form_frame, text="Maximum Storage (GB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.max_storage, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Retention Period (days):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.retention_days, width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Tool options
        ttk.Label(form_frame, text="Tool Options", style="Subheader.TLabel").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Checkbutton(form_frame, text="Install additional tools (recommended, but takes longer)", 
                        variable=self.install_extras).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Tool descriptions
        tools_frame = ttk.Frame(form_frame)
        tools_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        tools_text = """Basic tools (always installed):
• Binwalk - Firmware extraction and analysis
• Radare2 - Reverse engineering framework
• Ghidra - Software reverse engineering suite
• Firmware Walker - Firmware scanner

Additional tools:
• Firmware-Mod-Kit - Enhanced firmware modification tools
• Qiling Framework - Advanced firmware emulation
• Angr - Binary analysis framework
"""
        
        tools_desc = tk.Text(tools_frame, wrap=tk.WORD, height=12, width=70, background="#f0f0f0", font=('Arial', 10))
        tools_desc.pack(fill=tk.BOTH, expand=True)
        tools_desc.insert(tk.END, tools_text)
        tools_desc.config(state=tk.DISABLED)
        
    def setup_security_tab(self):
        # Security options tab
        security_tab = ttk.Frame(self.notebook)
        self.notebook.add(security_tab, text="Security")
        
        # Header
        ttk.Label(security_tab, text="Security Options", style="Header.TLabel").pack(pady=10)
        
        # Create form frame
        form_frame = ttk.Frame(security_tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # HTTPS configuration
        ttk.Label(form_frame, text="HTTPS Configuration", style="Subheader.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ssl_check = ttk.Checkbutton(form_frame, text="Setup HTTPS with Let's Encrypt (requires a domain name)", 
                                    variable=self.setup_ssl, command=self.toggle_domain_entry)
        ssl_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.domain_label = ttk.Label(form_frame, text="Domain Name:")
        self.domain_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.domain_entry = ttk.Entry(form_frame, textvariable=self.domain_name, width=40)
        self.domain_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Initially disable domain entry if SSL not selected
        if not self.setup_ssl.get():
            self.domain_label.config(state=tk.DISABLED)
            self.domain_entry.config(state=tk.DISABLED)
        
        # Security recommendations
        ttk.Label(form_frame, text="Security Recommendations", style="Subheader.TLabel").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        security_frame = ttk.Frame(form_frame)
        security_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        security_text = """For production deployments, we recommend:

1. Using HTTPS with a valid SSL certificate
2. Implementing network-level security (firewall rules, VPN)
3. Regularly backing up your data
4. Periodically changing the admin password
5. Setting up intrusion detection
6. Auditing dashboard access

The installer will implement basic security headers and authentication.
"""
        
        security_desc = tk.Text(security_frame, wrap=tk.WORD, height=12, width=70, background="#f0f0f0", font=('Arial', 10))
        security_desc.pack(fill=tk.BOTH, expand=True)
        security_desc.insert(tk.END, security_text)
        security_desc.config(state=tk.DISABLED)
        
    def setup_review_tab(self):
        # Review tab
        self.review_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.review_tab, text="Review")
        
        # Header
        ttk.Label(self.review_tab, text="Review Installation Settings", style="Header.TLabel").pack(pady=10)
        
        # Create scrollable frame for settings
        review_frame = ttk.Frame(self.review_tab)
        review_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Will be populated when tab is shown
        self.review_text = tk.Text(review_frame, wrap=tk.WORD, height=20, width=70, font=('Arial', 10))
        self.review_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_progress_tab(self):
        # Progress tab
        self.progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_tab, text="Installation")
        
        # Header
        ttk.Label(self.progress_tab, text="Installation Progress", style="Header.TLabel").pack(pady=10)
        
        # Progress bar
        progress_frame = ttk.Frame(self.progress_tab)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # Status label
        ttk.Label(progress_frame, textvariable=self.status_text, font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Log output
        log_frame = ttk.LabelFrame(progress_frame, text="Installation Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrollable text widget for log
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=15, width=70, font=('Courier', 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
    def setup_navigation_buttons(self):
        # Bottom navigation buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Back button
        self.back_button = ttk.Button(button_frame, text="Back", command=self.go_back)
        self.back_button.pack(side=tk.LEFT, padx=5)
        
        # Next button
        self.next_button = ttk.Button(button_frame, text="Next", style="Next.TButton", command=self.go_next)
        self.next_button.pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        ttk.Button(button_frame, text="Cancel", command=self.confirm_cancel).pack(side=tk.RIGHT, padx=5)
        
    def toggle_domain_entry(self):
        """Enable/disable domain entry based on SSL checkbox"""
        if self.setup_ssl.get():
            self.domain_label.config(state=tk.NORMAL)
            self.domain_entry.config(state=tk.NORMAL)
        else:
            self.domain_label.config(state=tk.DISABLED)
            self.domain_entry.config(state=tk.DISABLED)
    
    def browse_install_dir(self):
        """Open directory browser to select installation directory"""
        directory = filedialog.askdirectory(initialdir=self.install_dir.get())
        if directory:
            self.install_dir.set(directory)
    
    def update_review_tab(self):
        """Update the review tab with current settings"""
        # Clear current text
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        
        # Add settings
        settings = [
            ("Installation Directory", self.install_dir.get()),
            ("Server Hostname/IP", self.hostname.get()),
            ("Admin Username", self.admin_user.get()),
            ("Admin Password", "*" * len(self.admin_pass.get())),
            ("Maximum Storage", f"{self.max_storage.get()} GB"),
            ("Retention Period", f"{self.retention_days.get()} days"),
            ("Install Additional Tools", "Yes" if self.install_extras.get() else "No"),
            ("Setup HTTPS", "Yes" if self.setup_ssl.get() else "No")
        ]
        
        if self.setup_ssl.get():
            settings.append(("Domain Name", self.domain_name.get()))
        
        # Format settings as text
        for setting, value in settings:
            self.review_text.insert(tk.END, f"{setting}: ", "bold")
            self.review_text.insert(tk.END, f"{value}\n\n")
        
        # Add confirmation message
        self.review_text.insert(tk.END, "\nClick 'Next' to begin installation or 'Back' to make changes.")
        
        # Configure tag for bold text
        self.review_text.tag_configure("bold", font=('Arial', 10, 'bold'))
        
        # Make text read-only
        self.review_text.config(state=tk.DISABLED)
    
    def go_back(self):
        """Navigate to previous tab"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab > 0:
            self.notebook.select(current_tab - 1)
    
    def go_next(self):
        """Navigate to next tab"""
        current_tab = self.notebook.index(self.notebook.select())
        
        # Validate current tab before proceeding
        if not self.validate_current_tab(current_tab):
            return
        
        # If we're on the review tab, start the installation
        if current_tab == 4:  # Review tab
            self.start_installation()
        else:
            # Update review tab if we're moving to it
            if current_tab == 3:  # Coming from Security tab to Review
                self.update_review_tab()
            
            # Move to next tab
            self.notebook.select(current_tab + 1)
    
    def validate_current_tab(self, tab_index):
        """Validate inputs on the current tab"""
        if tab_index == 1:  # Installation tab
            # Check installation directory
            if not self.install_dir.get():
                messagebox.showerror("Error", "Installation directory cannot be empty")
                return False
            
            # Check admin credentials
            if not self.admin_user.get():
                messagebox.showerror("Error", "Admin username cannot be empty")
                return False
            
            if not self.admin_pass.get():
                messagebox.showerror("Error", "Admin password cannot be empty")
                return False
                
        elif tab_index == 2:  # Tools & Storage tab
            # Validate storage settings
            try:
                storage = int(self.max_storage.get())
                if storage <= 0:
                    messagebox.showerror("Error", "Maximum storage must be greater than 0")
                    return False
            except ValueError:
                messagebox.showerror("Error", "Maximum storage must be a number")
                return False
                
            try:
                days = int(self.retention_days.get())
                if days < 0:
                    messagebox.showerror("Error", "Retention days cannot be negative")
                    return False
            except ValueError:
                messagebox.showerror("Error", "Retention days must be a number")
                return False
                
        elif tab_index == 3:  # Security tab
            # Validate domain if SSL is enabled
            if self.setup_ssl.get() and not self.domain_name.get():
                messagebox.showerror("Error", "Domain name is required for HTTPS setup")
                return False
                
        return True
    
    def confirm_cancel(self):
        """Confirm before closing the application"""
        if messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel the installation?"):
            self.cleanup()
            self.root.destroy()
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def log(self, message):
        """Add message to the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def update_progress(self, value, status):
        """Update the progress bar and status text"""
        self.progress_var.set(value)
        self.status_text.set(status)
        self.root.update_idletasks()
    
    def start_installation(self):
        """Start the installation process"""
        # Move to progress tab
        self.notebook.select(5)  # Progress tab
        
        # Disable navigation buttons during installation
        self.back_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        
        # Run installation in separate thread
        threading.Thread(target=self.run_installation, daemon=True).start()
    
    def extract_embedded_files(self):
        """Extract embedded files from the installer script"""
        self.log("Extracting installation files...")
        self.update_progress(5, "Extracting files...")
        
        # Create temp directory for extraction
        self.temp_dir = tempfile.mkdtemp()
        self.log(f"Using temporary directory: {self.temp_dir}")
        
        try:
            # Get the path to this script
            script_path = os.path.abspath(sys.argv[0])
            
            # Extract the tar.gz file from after the __FILES__ marker
            with open(script_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                
            # Find the __FILES__ marker
            marker_pos = content.find('__FILES__')
            if marker_pos == -1:
                self.log("Error: Could not find file marker in script")
                return False
            
            # Write the binary part to a temporary tar.gz file
            with open(script_path, 'rb') as f:
                f.seek(marker_pos + len('__FILES__') + 1)  # +1 for newline
                tar_content = f.read()
            
            tar_path = os.path.join(self.temp_dir, 'files.tar.gz')
            with open(tar_path, 'wb') as f:
                f.write(tar_content)
            
            # Extract the tar.gz file
            import tarfile
            with tarfile.open(tar_path) as tar:
                tar.extractall(path=self.temp_dir)
            
            self.log("Files extracted successfully")
            return True
            
        except Exception as e:
            self.log(f"Error extracting files: {str(e)}")
            return False
    
    def create_installer_script(self):
        """Create the installer script with user settings"""
        self.log("Creating installer script...")
        self.update_progress(10, "Creating installer script...")
        
        # Configuration
        config = {
            "INSTALL_DIR": self.install_dir.get(),
            "HOSTNAME": self.hostname.get(),
            "ADMIN_USER": self.admin_user.get(),
            "ADMIN_PASS": self.admin_pass.get(),
            "MAX_STORAGE": self.max_storage.get(),
            "RETENTION_DAYS": self.retention_days.get(),
            "INSTALL_EXTRAS": "true" if self.install_extras.get() else "false",
            "SETUP_SSL": "true" if self.setup_ssl.get() else "false",
            "DOMAIN_NAME": self.domain_name.get() if self.setup_ssl.get() else ""
        }
        
        # Create installer.sh with variables substituted
        installer_path = os.path.join(self.temp_dir, "installer.sh")