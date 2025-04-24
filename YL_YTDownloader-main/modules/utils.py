import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('youtube_downloader')

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = 'config.json'
    default_config = {
        'app': {
            'title': 'YouTube Downloader Pro',
            'version': '1.0.0',
            'theme': 'dark',
            'default_language': 'en'
        },
        'download': {
            'default_path': 'downloads',
            'default_format': 'mp4',
            'default_quality': '720p',
            'max_concurrent_downloads': 3
        },
        'database': {
            'uri': 'mongodb://localhost:27017',
            'name': 'youtube_downloader'
        },
        'security': {
            'jwt_secret': 'your-secret-key',
            'jwt_expiry_days': 1,
            'password_reset_expiry_hours': 1
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with default config to ensure all required keys exist
                return {**default_config, **config}
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return default_config

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config.json"""
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {str(e)}")
        return False

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def validate_url(url: str) -> bool:
    """Validate URL format"""
    import re
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(([A-Z0-9][A-Z0-9_-]*)(\.[A-Z0-9][A-Z0-9_-]*)+)'  # domain
        r'(/[A-Z0-9._~:/?#[\]@!$&\'()*+,;=]*)?$',  # path
        re.IGNORECASE
    )
    return bool(url_pattern.match(url))

def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get information about a file"""
    try:
        import magic
        import os
        
        if not os.path.exists(file_path):
            return None
            
        file_info = {
            'path': file_path,
            'size': os.path.getsize(file_path),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
            'mime_type': magic.from_file(file_path, mime=True)
        }
        
        return file_info
    except Exception as e:
        logging.error(f"Error getting file info: {str(e)}")
        return None

def create_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory: {str(e)}")
        return False

def cleanup_old_files(directory: str, days: int = 30) -> int:
    """Remove files older than specified days"""
    try:
        import time
        current_time = time.time()
        removed_count = 0
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if (current_time - file_time) > (days * 86400):  # 86400 seconds in a day
                    os.remove(file_path)
                    removed_count += 1
                    
        return removed_count
    except Exception as e:
        logging.error(f"Error cleaning up files: {str(e)}")
        return 0

def export_data(data: list, format: str = 'csv', filename: str = None) -> Optional[str]:
    """Export data to CSV or JSON format"""
    try:
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
        if format.lower() == 'csv':
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(data[0].keys())  # Write headers
                for row in data:
                    writer.writerow(row.values())
        elif format.lower() == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, default=str, indent=4)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return filename
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        return None 