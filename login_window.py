import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database import Database
from main_menu import MainMenu
import bcrypt

class LoginWindow(QWidget):
    login_successful = pyqtSignal(int, bool)  # Signal with user_id and is_admin

    def __init__(self, db=None):
        super().__init__()
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
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
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel('Laboratory Instrument Manager')
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel('Login')
        subtitle.setFont(QFont('Arial', 16))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter your username')
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter your password')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Login button
        login_button = QPushButton('Login')
        login_button.setFixedWidth(150)
        login_button.clicked.connect(self.try_login)
        layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Connect enter key to login
        self.username_input.returnPressed.connect(self.try_login)
        self.password_input.returnPressed.connect(self.try_login)

        # Set focus to username input
        self.username_input.setFocus()

    def clear_inputs(self):
        """Clear all input fields"""
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()

    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please enter both username and password')
            return

        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, password, is_admin FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Clear inputs before emitting signal
                self.clear_inputs()
                # Emit signal with user data
                self.login_successful.emit(int(user['id']), bool(user['is_admin']))
            else:
                QMessageBox.warning(self, 'Error', 'Invalid username or password')
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Login failed: {str(e)}')
            self.password_input.clear()
            self.password_input.setFocus()

    def showEvent(self, event):
        """Clear inputs when the login window is shown"""
        super().showEvent(event)
        self.clear_inputs()

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec()) 