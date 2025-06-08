from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import Database

class BaseMainWindow(QMainWindow):
    def __init__(self, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        """Initialize the base UI components. Override in subclasses."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    def create_title(self, text):
        """Create a standardized title label."""
        title = QLabel(text)
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        self.main_layout.addWidget(title)
        return title

    def create_button_layout(self, buttons_config):
        """Create a standardized button layout.
        
        Args:
            buttons_config: list of dicts with keys:
                - text: button text
                - callback: function to call on click
                - width: button width (default: 200)
                - visible_if_admin: whether button is only visible to admins (default: False)
                - position: 'left', 'right', or 'center' (default: 'right')
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # Group buttons by position
        left_buttons = []
        center_buttons = []
        right_buttons = []
        
        for config in buttons_config:
            button = QPushButton(config['text'])
            button.clicked.connect(config['callback'])
            button.setFixedWidth(config.get('width', 200))
            
            if config.get('visible_if_admin', False):
                button.setVisible(self.is_admin)
            
            position = config.get('position', 'right')
            if position == 'left':
                left_buttons.append(button)
            elif position == 'center':
                center_buttons.append(button)
            else:
                right_buttons.append(button)
        
        # Add buttons to layout in correct order
        for button in left_buttons:
            layout.addWidget(button)
        
        layout.addStretch()
        
        for button in center_buttons:
            layout.addWidget(button)
        
        layout.addStretch()
        
        for button in right_buttons:
            layout.addWidget(button)
        
        return layout

    def show_error(self, title, message):
        """Show a standardized error message."""
        QMessageBox.critical(self, title, message)

    def show_warning(self, title, message):
        """Show a standardized warning message."""
        QMessageBox.warning(self, title, message)

    def show_info(self, title, message):
        """Show a standardized info message."""
        QMessageBox.information(self, title, message)

    def apply_dark_theme(self):
        """Apply the standardized dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
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
            QMessageBox {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1565c0;
            }
        """)

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view."""
        self.user_id = user_id
        self.is_admin = is_admin
        
        # Update buttons visibility
        for button in self.findChildren(QPushButton):
            if hasattr(button, 'visible_if_admin'):
                button.setVisible(self.is_admin) 