import PyInstaller.__main__
import os
import sys
import site
import time
from pathlib import Path

# Get the site-packages directory
site_packages = site.getsitepackages()[0]

# Find PyQt6 installation
pyqt_path = None
for path in site.getsitepackages():
    qt_path = os.path.join(path, 'PyQt6', 'Qt6')
    if os.path.exists(qt_path):
        pyqt_path = qt_path
        break

if not pyqt_path:
    print("Error: Could not find PyQt6 installation")
    sys.exit(1)

# Clean up any previous builds
def safe_remove(path):
    if os.path.exists(path):
        try:
            import shutil
            shutil.rmtree(path)
            print(f"Successfully removed {path}")
        except PermissionError:
            print(f"Warning: Could not remove {path} - it may be in use")
            print("Please close any running instances of the application and try again")
            sys.exit(1)
        except Exception as e:
            print(f"Warning: Error removing {path}: {e}")
            print("Trying to continue anyway...")

print("Cleaning up previous builds...")
safe_remove('dist')
safe_remove('build')

# Define PyInstaller arguments
args = [
    'main.py',  # Your main script
    '--name=LabInstrumentManager',  # Name of the executable
    '--onefile',  # Create a single executable
    '--windowed',  # Don't show console window
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace existing build
    '--hidden-import=pkgutil',  # Add hidden imports
    '--hidden-import=sqlite3',
    '--hidden-import=bcrypt',
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--collect-all=PyQt6',  # Collect all PyQt6 modules
    '--collect-submodules=PyQt6',  # Collect all PyQt6 submodules
    '--exclude-module=matplotlib',  # Exclude unnecessary modules
    '--exclude-module=numpy',
    '--exclude-module=PIL',
    '--exclude-module=scipy',
    '--exclude-module=pandas',
    '--exclude-module=tkinter',
    '--exclude-module=PyQt6.QtWebEngineCore',
    '--exclude-module=PyQt6.QtWebEngineWidgets',
    '--exclude-module=PyQt6.QtWebEngine',
    '--exclude-module=PyQt6.QtWebSockets',
    '--exclude-module=PyQt6.QtNetwork',
    '--exclude-module=PyQt6.QtBluetooth',
    '--exclude-module=PyQt6.QtDBus',
    '--exclude-module=PyQt6.QtDesigner',
    '--exclude-module=PyQt6.QtHelp',
    '--exclude-module=PyQt6.QtLocation',
    '--exclude-module=PyQt6.QtMultimedia',
    '--exclude-module=PyQt6.QtNfc',
    '--exclude-module=PyQt6.QtOpenGL',
    '--exclude-module=PyQt6.QtPositioning',
    '--exclude-module=PyQt6.QtPrintSupport',
    '--exclude-module=PyQt6.QtQml',
    '--exclude-module=PyQt6.QtQuick',
    '--exclude-module=PyQt6.QtQuickWidgets',
    '--exclude-module=PyQt6.QtRemoteObjects',
    '--exclude-module=PyQt6.QtSensors',
    '--exclude-module=PyQt6.QtSerialPort',
    '--exclude-module=PyQt6.QtSql',
    '--exclude-module=PyQt6.QtSvg',
    '--exclude-module=PyQt6.QtTest',
    '--exclude-module=PyQt6.QtWebChannel',
    '--exclude-module=PyQt6.QtWebEngineCore',
    '--exclude-module=PyQt6.QtWebEngineWidgets',
    '--exclude-module=PyQt6.QtWebEngine',
    '--exclude-module=PyQt6.QtWebSockets',
    '--exclude-module=PyQt6.QtXml',
    '--exclude-module=PyQt6.QtXmlPatterns',
]

print("Starting build process...")
# Run PyInstaller
PyInstaller.__main__.run(args)

print("\nBuild complete! The executable is in the 'dist' folder.")
print("You can find it at:", os.path.abspath(os.path.join('dist', 'LabInstrumentManager.exe')))