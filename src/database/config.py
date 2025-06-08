import os
from pathlib import Path
from typing import Dict, Any

class DatabaseConfig:
    """Database configuration settings"""
    
    # Default database settings
    DEFAULT_SETTINGS: Dict[str, Any] = {
        'pool_size': 5,
        'timeout': 5,
        'check_same_thread': False
    }
    
    @staticmethod
    def get_database_path() -> str:
        """Get the database file path"""
        # Get the application root directory
        root_dir = Path(__file__).parent.parent.parent
        
        # Create data directory if it doesn't exist
        data_dir = root_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # Return the database file path
        return str(data_dir / 'instruments.db')
    
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Get database settings"""
        settings = DatabaseConfig.DEFAULT_SETTINGS.copy()
        
        # Override settings with environment variables if they exist
        if 'DB_POOL_SIZE' in os.environ:
            settings['pool_size'] = int(os.environ['DB_POOL_SIZE'])
        if 'DB_TIMEOUT' in os.environ:
            settings['timeout'] = int(os.environ['DB_TIMEOUT'])
            
        return settings 