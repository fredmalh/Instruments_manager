from PyQt6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from database import Database
import logging

class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db if parent else Database()
        self.setup_logging()
        self.init_ui()
        self.apply_dark_theme()

    def setup_logging(self):
        """Setup logging for the dialog"""
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def init_ui(self):
        """Initialize the UI. Override this in child classes."""
        pass

    def apply_dark_theme(self):
        """Apply dark theme to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 3px;
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
            QGroupBox {
                border: 1px solid #3d3d3d;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                color: #ffffff;
            }
        """)

    def create_button_layout(self, save_text="Save", cancel_text="Cancel"):
        """Create a standard button layout with save and cancel buttons"""
        button_layout = QHBoxLayout()
        
        save_button = QPushButton(save_text)
        cancel_button = QPushButton(cancel_text)
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        return button_layout

    def show_error(self, title, message):
        """Show error message box"""
        self.logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def show_warning(self, title, message):
        """Show warning message box"""
        self.logger.warning(f"{title}: {message}")
        QMessageBox.warning(self, title, message)

    def show_info(self, title, message):
        """Show info message box"""
        self.logger.info(f"{title}: {message}")
        QMessageBox.information(self, title, message)

    def validate_required_fields(self, fields, field_names):
        """Validate that all required fields are filled"""
        for field, name in zip(fields, field_names):
            if not field.strip():
                self.show_error('Error', f'Please fill in the {name} field')
                return False
        return True 