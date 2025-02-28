# Save this as storage.py in the app directory
import os
import shutil
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MAX_STORAGE_GB = float(os.getenv('MAX_STORAGE_GB', 50))  # Maximum storage in GB
AUTO_CLEANUP_DAYS = int(os.getenv('AUTO_CLEANUP_DAYS', 30))  # Auto-delete after X days

# Logger
logger = logging.getLogger("storage-manager")

def get_dir_size(path):
    """Calculate the total size of a directory in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):  # Handle broken symlinks
                total_size += os.path.getsize(fp)
    return total_size

def get_directory_usage(directory):
    """Get directory usage in GB"""
    size_bytes = get_dir_size(directory)
    return size_bytes / (1024 * 1024 * 1024)  # Convert to GB

def get_total_storage_usage(base_dirs):
    """Get total storage usage across multiple directories"""
    total_gb = 0
    for directory in base_dirs:
        if os.path.exists(directory):
            total_gb += get_directory_usage(directory)
    return total_gb

def cleanup_old_results(results_dir, days_threshold):
    """Remove results older than the specified threshold"""
    logger.info(f"Running cleanup for results older than {days_threshold} days")
    
    cleanup_count = 0
    cleanup_size = 0
    
    threshold_date = datetime.now() - timedelta(days=days_threshold)
    
    # Process each subdirectory in the results directory
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        
        if not os.path.isdir(item_path):
            continue
        
        # Get the modification time
        try:
            mtime = os.path.getmtime(item_path)
            modified_date = datetime.fromtimestamp(mtime)
            
            # If older than threshold, remove it
            if modified_date < threshold_date:
                dir_size = get_dir_size(item_path)
                logger.info(f"Removing old result: {item_path} (Last modified: {modified_date.isoformat()})")
                
                try:
                    shutil.rmtree(item_path)
                    cleanup_count += 1
                    cleanup_size += dir_size
                    logger.info(f"Successfully removed {item_path}")
                except Exception as e:
                    logger.error(f"Failed to remove {item_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {item_path}: {e}")
    
    # Convert cleanup_size to MB for logging
    cleanup_size_mb = cleanup_size / (1024 * 1024)
    logger.info(f"Cleanup completed: Removed {cleanup_count} directories, freed {cleanup_size_mb:.2f} MB")
    
    return cleanup_count, cleanup_size

def check_storage_and_cleanup_if_needed(upload_dir, results_dir):
    """Check storage usage and clean up if needed"""
    # Calculate current usage
    current_usage_gb = get_total_storage_usage([upload_dir, results_dir])
    logger.info(f"Current storage usage: {current_usage_gb:.2f} GB / {MAX_STORAGE_GB} GB")
    
    # If we're close to the limit (>90%), clean up
    if current_usage_gb > (MAX_STORAGE_GB * 0.9):
        logger.warning(f"Storage usage high ({current_usage_gb:.2f} GB). Starting cleanup...")
        
        # Try increasingly aggressive cleanup strategies
        # 1. First try normal age-based cleanup
        cleanup_count, _ = cleanup_old_results(results_dir, AUTO_CLEANUP_DAYS)
        
        if cleanup_count == 0:
            # 2. If that didn't help, be more aggressive
            logger.warning("No files cleaned up with normal threshold. Using more aggressive threshold.")
            cleanup_old_results(results_dir, AUTO_CLEANUP_DAYS // 2)
            
            # 3. Check again after cleanup
            new_usage_gb = get_total_storage_usage([upload_dir, results_dir])
            if new_usage_gb > (MAX_STORAGE_GB * 0.9):
                logger.error(f"Storage still high after cleanup: {new_usage_gb:.2f} GB")
                # You could implement emergency cleanup here
        
        return True  # Cleanup was performed
    
    return False  # No cleanup needed

def setup_scheduled_cleanup(upload_dir, results_dir):
    """Set up a background thread for periodic cleanup"""
    import threading
    
    def cleanup_worker():
        while True:
            try:
                # Check if cleanup is needed
                check_storage_and_cleanup_if_needed(upload_dir, results_dir)
                
                # Also run age-based cleanup periodically
                if AUTO_CLEANUP_DAYS > 0:
                    cleanup_old_results(results_dir, AUTO_CLEANUP_DAYS)
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
            
            # Sleep for a day (or other interval)
            time.sleep(86400)  # 24 hours
    
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Scheduled cleanup worker started")