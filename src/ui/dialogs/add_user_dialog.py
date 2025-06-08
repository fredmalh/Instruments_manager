from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDialog)
from ..base.base_dialog import BaseDialog
import hashlib

class AddUserDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add New User')
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        # Create form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Create input fields
        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_input = QComboBox()
        self.role_input.addItems(['User', 'Admin'])

        # Add fields to form
        form_layout.addRow('Username:', self.username_input)
        form_layout.addRow('Email:', self.email_input)
        form_layout.addRow('Password:', self.password_input)
        form_layout.addRow('Confirm Password:', self.confirm_password_input)
        form_layout.addRow('Role:', self.role_input)

        # Create main layout
        main_layout = self.layout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(self.create_button_layout())

    def validate_password(self):
        """Validate password requirements"""
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if password != confirm_password:
            self.show_error('Error', 'Passwords do not match')
            return False

        if len(password) < 8:
            self.show_error('Error', 'Password must be at least 8 characters long')
            return False

        if not any(c.isupper() for c in password):
            self.show_error('Error', 'Password must contain at least one uppercase letter')
            return False

        if not any(c.islower() for c in password):
            self.show_error('Error', 'Password must contain at least one lowercase letter')
            return False

        if not any(c.isdigit() for c in password):
            self.show_error('Error', 'Password must contain at least one number')
            return False

        return True

    def hash_password(self, password):
        """Hash the password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def accept(self):
        # Validate required fields
        required_fields = [
            (self.username_input.text(), 'Username'),
            (self.email_input.text(), 'Email'),
            (self.password_input.text(), 'Password'),
            (self.confirm_password_input.text(), 'Confirm Password')
        ]
        
        if not self.validate_required_fields([f for f, _ in required_fields], 
                                          [n for _, n in required_fields]):
            return

        # Validate password
        if not self.validate_password():
            return

        try:
            cursor = self.db.conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", 
                         (self.username_input.text(),))
            if cursor.fetchone():
                self.show_error('Error', 'Username already exists')
                return

            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", 
                         (self.email_input.text(),))
            if cursor.fetchone():
                self.show_error('Error', 'Email already exists')
                return

            # Insert new user
            cursor.execute("""
                INSERT INTO users (
                    username, email, password, role
                ) VALUES (?, ?, ?, ?)
            """, (
                self.username_input.text(),
                self.email_input.text(),
                self.hash_password(self.password_input.text()),
                self.role_input.currentText()
            ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to add user: {str(e)}') 