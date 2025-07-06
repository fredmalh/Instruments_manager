from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QApplication)
from ..base.base_dialog import BaseDialog
import bcrypt

class AddUserDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)  # This will call init_ui() from BaseDialog
        self.setWindowTitle('Add User')
        self.setMinimumWidth(400)
        
        # Center the dialog on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Make sure dialog is visible and on top
        self.setVisible(True)
        self.raise_()
        self.activateWindow()

    def init_ui(self):
        """Initialize the UI. This is called by BaseDialog.__init__"""
        # Create main layout first
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Create form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Create input fields
        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_input")
        self.username_input.setText("")  # Explicitly set empty text
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumWidth(200)  # Set minimum width
        
        self.email_input = QLineEdit()
        self.email_input.setObjectName("email_input")
        self.email_input.setText("")
        self.email_input.setPlaceholderText("Enter email")
        self.email_input.setMinimumWidth(200)
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_input")
        self.password_input.setText("")
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumWidth(200)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("confirm_password_input")
        self.confirm_password_input.setText("")
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumWidth(200)
        
        self.is_admin_checkbox = QCheckBox()
        self.is_admin_checkbox.setObjectName("is_admin_checkbox")
        self.is_admin_checkbox.setStyleSheet("QCheckBox { color: white; }")

        # Add fields to form
        form_layout.addRow('Username:', self.username_input)
        form_layout.addRow('Email:', self.email_input)
        form_layout.addRow('Password:', self.password_input)
        form_layout.addRow('Confirm Password:', self.confirm_password_input)
        form_layout.addRow('Admin:', self.is_admin_checkbox)

        # Add layouts to main layout
        main_layout.addLayout(form_layout)
        main_layout.addLayout(self.create_button_layout())

    def validate_password(self):
        """Validate password requirements"""
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if password != confirm_password:
            self.show_error('Error', 'Passwords do not match')
            return False

        return True

    def hash_password(self, password):
        """Hash the password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

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
            cursor.execute("SELECT id FROM users WHERE username = ?", (self.username_input.text(),))
            if cursor.fetchone():
                self.show_error('Error', 'Username already exists')
                return

            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (self.email_input.text(),))
            if cursor.fetchone():
                self.show_error('Error', 'Email already exists')
                return

            # Create new user
            cursor.execute("""
                INSERT INTO users (username, email, password, is_admin)
                VALUES (?, ?, ?, ?)
            """, (
                self.username_input.text(),
                self.email_input.text(),
                self.hash_password(self.password_input.text()),
                self.is_admin_checkbox.isChecked()
            ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to create user: {str(e)}') 