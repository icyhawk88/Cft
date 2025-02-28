# Save this as auth.py in the app directory
import os
import functools
import hashlib
import hmac
from flask import request, jsonify
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('API_KEY', 'default_insecure_key_please_change')

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = None

def init_admin_password():
    """Initialize the admin password hash from environment or create a default"""
    global ADMIN_PASSWORD_HASH
    password = os.getenv('ADMIN_PASSWORD', 'hacktheplanet')
    
    # Only hash if not already hashed (checking if it starts with $2b$)
    if not password.startswith('$2b$'):
        ADMIN_PASSWORD_HASH = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Optionally save the hash back to .env file for persistence
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Replace password with hash in .env
            if 'ADMIN_PASSWORD=' in env_content:
                new_content = env_content.replace(
                    f'ADMIN_PASSWORD={password}',
                    f'ADMIN_PASSWORD_HASH={ADMIN_PASSWORD_HASH}'
                )
                with open(env_path, 'w') as f:
                    f.write(new_content)
    else:
        ADMIN_PASSWORD_HASH = password

def require_api_key(func):
    """Decorator to require API key for API endpoints"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        provided_key = request.headers.get('X-Api-Key')
        
        # Simple API key validation
        if provided_key and hmac.compare_digest(provided_key, API_KEY):
            return func(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized - invalid or missing API key'}), 401
    return wrapper

def require_auth(func):
    """Decorator to require basic auth for web endpoints"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        session_token = request.cookies.get('session_token')
        
        # Allow access if valid session token in cookie
        if session_token and validate_session_token(session_token):
            return func(*args, **kwargs)
        
        # Check basic auth credentials
        if auth and auth.username == ADMIN_USERNAME and check_password(auth.password):
            # Create and set session token
            return func(*args, **kwargs)
        
        return jsonify({'error': 'Unauthorized - invalid credentials'}), 401
    return wrapper

def check_password(password):
    """Verify password against stored hash"""
    if ADMIN_PASSWORD_HASH is None:
        init_admin_password()
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8'))
    except Exception as e:
        print(f"Error checking password: {e}")
        return False

def validate_session_token(token):
    """Validate a session token (simplified implementation)"""
    # In a production app, you'd store sessions in a database
    # This is a simplified version for demonstration
    expected_token = hashlib.sha256(f"{ADMIN_USERNAME}:{API_KEY}".encode()).hexdigest()
    return hmac.compare_digest(token, expected_token)

def generate_session_token():
    """Generate a new session token"""
    return hashlib.sha256(f"{ADMIN_USERNAME}:{API_KEY}".encode()).hexdigest()

# Initialize admin password when module is loaded
init_admin_password()