from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database import Database

class MainMenu(QWidget):
    show_instruments_signal = pyqtSignal(int, bool)  # user_id, is_admin
    show_maintenance_signal = pyqtSignal(int, bool)  # user_id, is_admin
    show_users_signal = pyqtSignal(int, bool)  # user_id, is_admin
    logout_signal = pyqtSignal()  # Signal to go back to login

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel('Laboratory Instrument Manager')
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel('Main Menu')
        subtitle.setFont(QFont('Arial', 16))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        # List Instruments button
        list_instruments_btn = QPushButton('List Instruments')
        list_instruments_btn.clicked.connect(lambda: self.show_instruments_signal.emit(self.user_id, self.is_admin))
        buttons_layout.addWidget(list_instruments_btn)

        # Maintenance Operations button
        maintenance_btn = QPushButton('Maintenance Operations')
        maintenance_btn.clicked.connect(lambda: self.show_maintenance_signal.emit(self.user_id, self.is_admin))
        buttons_layout.addWidget(maintenance_btn)

        # Users button (only for admins)
        if self.is_admin:
            users_btn = QPushButton('Users')
            users_btn.clicked.connect(lambda: self.show_users_signal.emit(self.user_id, self.is_admin))
            buttons_layout.addWidget(users_btn)

        # Logout button
        logout_btn = QPushButton('Logout')
        logout_btn.clicked.connect(self.logout_signal.emit)
        buttons_layout.addWidget(logout_btn)

        layout.addLayout(buttons_layout)

        # User info
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        user = cursor.fetchone()
        if user:
            user_info = QLabel(f'Logged in as: {user["username"]} ({self.is_admin and "Admin" or "User"})')
            user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(user_info)

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        self.init_ui()  # Reinitialize UI to update buttons and user info

    def show_instruments(self):
        self.show_instruments_signal.emit(self.user_id, self.is_admin)

    def show_maintenance(self):
        self.show_maintenance_signal.emit(self.user_id, self.is_admin)

    def show_users(self):
        if self.is_admin:
            self.show_users_signal.emit(self.user_id, self.is_admin)
        else:
            QMessageBox.warning(self, 'Access Denied', 'Only administrators can access user management.')

    def logout(self):
        self.logout_signal.emit()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore() 