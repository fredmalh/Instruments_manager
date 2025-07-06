import os
import sys
from pathlib import Path

def get_executable_directory() -> str:
    """
    Get the directory where the executable/script is located.
    
    Returns:
        str: The absolute path to the directory containing the executable/script
        
    This function works for both:
    - Development: When running as a Python script
    - Production: When running as a frozen executable (PyInstaller, cx_Freeze, etc.)
    """
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable (PyInstaller, cx_Freeze, etc.)
        return os.path.dirname(sys.executable)
    else:
        # Running as a script - get the directory of the main script
        # Find the main script by looking at sys.argv[0]
        main_script = sys.argv[0]
        if main_script.endswith('.py'):
            return os.path.dirname(os.path.abspath(main_script))
        else:
            # Fallback to current working directory
            return os.getcwd()

def get_database_path() -> str:
    """
    Get the path to the database file, which will be in the same directory as the executable.
    
    Returns:
        str: The absolute path to the database file
    """
    base_dir = get_executable_directory()
    
    # Return the database file path directly in the executable directory
    return str(Path(base_dir) / 'lab_instruments.db')

def get_database_directory() -> str:
    """
    Get the directory where the database should be stored.
    
    Returns:
        str: The absolute path to the database directory
    """
    base_dir = get_executable_directory()
    
    # Return the executable directory (database will be stored here)
    return str(Path(base_dir)) 