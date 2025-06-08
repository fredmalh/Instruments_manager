from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt
from database import Database
import logging

class BaseWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setup_logging()
        self.init_ui()
        self.apply_dark_theme()

    def setup_logging(self):
        """Setup logging for the window"""
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
        """Apply dark theme to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3d3d3d;
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
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 3px;
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

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.db.release_lock()
            event.accept()
        except Exception as e:
            self.logger.error(f"Error during window close: {str(e)}")
            event.accept() 