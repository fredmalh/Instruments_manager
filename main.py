import sys
from PyQt6.QtWidgets import QApplication
from main_window import CentralWindow

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show central window
    window = CentralWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 