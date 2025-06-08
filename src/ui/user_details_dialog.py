from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                            QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from ..database import UserRepository

class UserDetailsDialog(QDialog):
    def __init__(self, user_repo: UserRepository, user_data=None, parent=None):
        super().__init__(parent)
        self.user_repo = user_repo
        self.user_data = user_data
        self.init_ui()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit, QComboBox {
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
        layout.setSpacing(15)

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel('Email:')
        self.email_input = QLineEdit()
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        layout.addLayout(email_layout)

        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Role
        role_layout = QHBoxLayout()
        role_label = QLabel('Role:')
        self.role_combo = QComboBox()
        self.role_combo.addItems(['User', 'Admin'])
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')
        save_button.clicked.connect(self.save_user)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Set window title
        self.setWindowTitle('Add User' if not self.user_data else 'Edit User')

        # If editing existing user, populate fields
        if self.user_data:
            self.username_input.setText(self.user_data['username'])
            self.email_input.setText(self.user_data['email'])
            self.role_combo.setCurrentText(self.user_data['role'])
            self.password_input.setPlaceholderText('Leave blank to keep current password')

    def save_user(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()

        if not username or not email:
            QMessageBox.warning(self, 'Error', 'Username and email are required')
            return

        try:
            if self.user_data:  # Editing existing user
                if self.user_repo.check_username_exists(username, self.user_data['id']):
                    QMessageBox.warning(self, 'Error', 'Username already exists')
                    return
                if self.user_repo.check_email_exists(email, self.user_data['id']):
                    QMessageBox.warning(self, 'Error', 'Email already exists')
                    return
                
                self.user_repo.update_user(
                    self.user_data['id'],
                    username,
                    email,
                    password if password else None,
                    role
                )
            else:  # Adding new user
                if not password:
                    QMessageBox.warning(self, 'Error', 'Password is required for new users')
                    return
                if self.user_repo.check_username_exists(username):
                    QMessageBox.warning(self, 'Error', 'Username already exists')
                    return
                if self.user_repo.check_email_exists(email):
                    QMessageBox.warning(self, 'Error', 'Email already exists')
                    return
                
                self.user_repo.create_user(username, email, password, role)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save user: {str(e)}') 