#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import uuid
import time
import logging
import threading
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("hardware-hacking-server")

# Initialize Flask app
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Configuration
UPLOAD_FOLDER = os.path.expanduser('~/firmware/uploads')
RESULTS_FOLDER = os.path.expanduser('~/firmware/results')
PROJECTS_FILE = os.path.expanduser('~/firmware/projects.json')
PROCESSES_FILE = os.path.expanduser('~/firmware/processes.json')

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Initialize data files if they don't exist
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(PROCESSES_FILE):
    with open(PROCESSES_FILE, 'w') as f:
        json.dump([], f)

# Helper functions
def get_projects():
    try:
        with open(PROJECTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading projects: {e}")
        return []

def save_projects(projects):
    try:
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving projects: {e}")

def get_processes():
    try:
        with open(PROCESSES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading processes: {e}")
        return []

def save_processes(processes):
    try:
        with open(PROCESSES_FILE, 'w') as f:
            json.dump(processes, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processes: {e}")

def update_process_status(process_id, status, progress=None, message=None):
    processes = get_processes()
    for process in processes:
        if process['id'] == process_id:
            process['status'] = status
            if progress is not None:
                process['progress'] = progress
            if message is not None:
                process['message'] = message
            process['updated_at'] = datetime.now().isoformat()
            break
    save_processes(processes)

def guess_device_type(filename):
    # Very basic detection based on filename - would be expanded
    filename = filename.lower()
    if 'esp' in filename:
        return 'ESP8266/ESP32'
    elif 'bk' in filename or 'beken' in filename:
        return 'Beken'
    elif 'rtl' in filename:
        return 'Realtek'
    elif 'mt' in filename:
        return 'MediaTek'
    else:
        return 'Unknown'

def run_analysis(process_id, filepath, options):
    """Run the firmware analysis in a separate thread"""
    try:
        # Update status to running
        update_process_status(process_id, "running", 10, "Starting analysis...")
        time.sleep(1)  # Simulate work
        
        # Extract filesystem if selected
        if options.get('extract_filesystem', True):
            update_process_status(process_id, "running", 20, "Extracting filesystem...")
            output_dir = os.path.join(RESULTS_FOLDER, process_id, 'extracted')
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                # Run binwalk for extraction
                cmd = f"binwalk -e -C {output_dir} {filepath}"
                subprocess.run(cmd, shell=True, check=True, timeout=300)
                update_process_status(process_id, "running", 40, "Filesystem extracted successfully")
            except Exception as e:
                logger.error(f"Error extracting filesystem: {e}")
                update_process_status(process_id, "running", 40, f"Extraction completed with errors: {str(e)}")
        
        # Scan for vulnerabilities if selected
        if options.get('scan_vulnerabilities', True):
            update_process_status(process_id, "running", 50, "Scanning for vulnerabilities...")
            time.sleep(2)  # Simulate work
            
            # In a real implementation, this would run security scanning tools
            
            update_process_status(process_id, "running", 70, "Vulnerability scan completed")
        
        # Identify components if selected
        if options.get('identify_components', True):
            update_process_status(process_id, "running", 80, "Identifying components...")
            time.sleep(1.5)  # Simulate work
            
            # In a real implementation, this would run component identification
            
            update_process_status(process_id, "running", 90, "Component identification completed")
        
        # Deep analysis if selected
        if options.get('deep_analysis', False):
            update_process_status(process_id, "running", 95, "Performing deep analysis...")
            time.sleep(3)  # Simulate more intensive work
            update_process_status(process_id, "running", 98, "Deep analysis completed")
        
        # Complete the process
        update_process_status(process_id, "completed", 100, "Analysis completed successfully")
        
        # Update the project with results
        projects = get_projects()
        for project in projects:
            if project['process_id'] == process_id:
                project['status'] = 'completed'
                project['completed_at'] = datetime.now().isoformat()
                break
        save_projects(projects)
        
    except Exception as e:
        logger.error(f"Error in analysis process: {e}")
        update_process_status(process_id, "failed", None, f"Analysis failed: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    return jsonify(get_projects())

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get form data
    name = request.form.get('name', file.filename)
    description = request.form.get('description', '')
    
    # Process options
    options = {
        'extract_filesystem': request.form.get('extract_filesystem', 'true').lower() == 'true',
        'scan_vulnerabilities': request.form.get('scan_vulnerabilities', 'true').lower() == 'true',
        'identify_components': request.form.get('identify_components', 'true').lower() == 'true',
        'deep_analysis': request.form.get('deep_analysis', 'false').lower() == 'true'
    }
    
    # Generate unique IDs
    project_id = str(uuid.uuid4())
    process_id = str(uuid.uuid4())
    
    # Save the file
    filename = secure_filename(file.filename)
    project_dir = os.path.join(UPLOAD_FOLDER, project_id)
    os.makedirs(project_dir, exist_ok=True)
    filepath = os.path.join(project_dir, filename)
    file.save(filepath)
    
    # Detect device type
    device_type = guess_device_type(filename)
    
    # Create results directory
    os.makedirs(os.path.join(RESULTS_FOLDER, process_id), exist_ok=True)
    
    # Create project entry
    now = datetime.now().isoformat()
    project = {
        'id': project_id,
        'name': name,
        'description': description,
        'filename': filename,
        'filepath': filepath,
        'device_type': device_type,
        'status': 'pending',
        'process_id': process_id,
        'created_at': now,
        'updated_at': now,
        'options': options
    }
    
    # Create process entry
    process = {
        'id': process_id,
        'project_id': project_id,
        'status': 'queued',
        'progress': 0,
        'message': 'Queued for analysis',
        'created_at': now,
        'updated_at': now
    }
    
    # Save entries
    projects = get_projects()
    projects.append(project)
    save_projects(projects)
    
    processes = get_processes()
    processes.append(process)
    save_processes(processes)
    
    # Start analysis in background
    threading.Thread(target=run_analysis, args=(process_id, filepath, options)).start()
    
    return jsonify(project), 201

@app.route('/api/projects/<project_id>', methods=['GET'])
def api_get_project(project_id):
    projects = get_projects()
    for project in projects:
        if project['id'] == project_id:
            return jsonify(project)
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    projects = get_projects()
    for i, project in enumerate(projects):
        if project['id'] == project_id:
            # Get process ID to remove process entry too
            process_id = project.get('process_id')
            
            # Remove project
            del projects[i]
            save_projects(projects)
            
            # Remove process if exists
            if process_id:
                processes = get_processes()
                processes = [p for p in processes if p['id'] != process_id]
                save_processes(processes)
            
            # Remove project files
            project_dir = os.path.join(UPLOAD_FOLDER, project_id)
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            # Remove results
            results_dir = os.path.join(RESULTS_FOLDER, process_id) if process_id else None
            if results_dir and os.path.exists(results_dir):
                shutil.rmtree(results_dir)
            
            return jsonify({'success': True})
    
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/processes', methods=['GET'])
def api_get_processes():
    return jsonify(get_processes())

@app.route('/api/processes/<process_id>', methods=['GET'])
def api_get_process(process_id):
    processes = get_processes()
    for process in processes:
        if process['id'] == process_id:
            return jsonify(process)
    return jsonify({'error': 'Process not found'}), 404

@app.route('/api/statistics', methods=['GET'])
def api_get_statistics():
    projects = get_projects()
    processes = get_processes()
    
    # Calculate statistics
    total_projects = len(projects)
    completed_projects = sum(1 for p in projects if p.get('status') == 'completed')
    active_processes = sum(1 for p in processes if p.get('status') in ['running', 'queued'])
    
    # Count device types
    device_types = {}
    for project in projects:
        device_type = project.get('device_type', 'Unknown')
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    # Count vulnerabilities (in a real app, this would be calculated from actual results)
    vulnerabilities_found = 7  # Placeholder
    
    return jsonify({
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'active_processes': active_processes,
        'device_types': device_types,
        'vulnerabilities_found': vulnerabilities_found
    })

@app.route('/api/results/<process_id>', methods=['GET'])
def api_get_results(process_id):
    results_dir = os.path.join(RESULTS_FOLDER, process_id)
    if not os.path.exists(results_dir):
        return jsonify({'error': 'Results not found'}), 404
    
    # In a real app, this would provide access to analysis results
    # For now just return a list of files
    results = []
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, results_dir)
            results.append({
                'path': rel_path,
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    return jsonify(results)

@app.route('/api/download/<process_id>/<path:file_path>', methods=['GET'])
def api_download_file(process_id, file_path):
    # Security: Ensure the requested file is within the results directory
    results_dir = os.path.join(RESULTS_FOLDER, process_id)
    requested_path = os.path.normpath(os.path.join(results_dir, file_path))
    
    if not requested_path.startswith(results_dir):
        return jsonify({'error': 'Access denied'}), 403
    
    if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get the directory containing the file
    dir_path = os.path.dirname(requested_path)
    file_name = os.path.basename(requested_path)
    
    return send_from_directory(dir_path, file_name, as_attachment=True)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)