from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database import Database
from ..base.base_table import BaseTable

class BaseDataWindow(QMainWindow):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme to the window"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def init_ui(self):
        """Initialize the UI - to be overridden by subclasses"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def create_title(self, title_text):
        """Create a title label"""
        title = QLabel(title_text)
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        self.main_layout.addWidget(title)

    def create_button_layout(self, buttons_config):
        """Create a standardized button layout"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Add stretch to center buttons
        button_layout.addStretch()
        
        for config in buttons_config:
            if 'visible_if_admin' in config and config['visible_if_admin'] and not self.is_admin:
                continue
                
            button = QPushButton(config['text'])
            button.clicked.connect(config['callback'])
            button.setFixedWidth(150)
            
            if config.get('position') == 'left':
                button_layout.insertWidget(0, button)
            elif config.get('position') == 'right':
                button_layout.addWidget(button)
            else:  # center
                button_layout.addWidget(button)
        
        # Add stretch to center buttons
        button_layout.addStretch()
        
        return button_layout

    def handle_cell_click(self, row, column):
        """Handle cell click events - to be overridden by subclasses"""
        pass

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        self.load_data()  # Always refresh data when window is shown

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        self.load_data()  # Force reload when user is updated

    def load_data(self):
        """Load data - to be overridden by subclasses"""
        pass 