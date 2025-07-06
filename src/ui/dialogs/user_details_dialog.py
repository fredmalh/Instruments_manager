from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QMessageBox, QApplication)
from ..base.base_dialog import BaseDialog
import bcrypt
from database import Database

class UserDetailsDialog(BaseDialog):
    def __init__(self, user_id, current_user_id, is_admin, parent=None):
        self.user_id = user_id
        self.current_user_id = current_user_id
        self.is_admin = is_admin
        self.db = Database()  # Initialize database connection
        super().__init__(parent)  # This will call init_ui() from BaseDialog
        self.setWindowTitle('User Details')
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
        
        # Load user data after UI is initialized
        self.load_user_data()

    def init_ui(self):
        """Initialize the UI. This is called by BaseDialog.__init__"""
        # Create main layout with better spacing
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

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

        # Add fields to form with better organization
        form_layout.addRow('Username:', self.username_input)
        form_layout.addRow('Email:', self.email_input)
        form_layout.addRow('Password:', self.password_input)
        form_layout.addRow('Confirm Password:', self.confirm_password_input)
        form_layout.addRow('Admin:', self.is_admin_checkbox)

        # Add form layout to main layout
        main_layout.addLayout(form_layout)

        # Create button layout
        button_layout = self.create_button_layout('Save', 'Close')
        
        # Only show save button for admin or if user is editing their own profile
        can_edit = self.is_admin or self.user_id == self.current_user_id
        if not can_edit:
            for button in button_layout.findChildren(QPushButton):
                if button.text() == 'Save':
                    button.setVisible(False)
        
        main_layout.addLayout(button_layout)

        # Set fields as read-only if user can't edit
        if not can_edit:
            for widget in self.findChildren((QLineEdit, QCheckBox)):
                widget.setEnabled(False)

    def load_user_data(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT username, email, is_admin FROM users WHERE id = ?", (self.user_id,))
            
            user = cursor.fetchone()
            if user:
                self.username_input.setText(user['username'])
                self.email_input.setText(user['email'])
                self.is_admin_checkbox.setChecked(bool(user['is_admin']))
                
                # Clear password fields and set placeholder
                self.password_input.clear()
                self.confirm_password_input.clear()
                self.password_input.setPlaceholderText('Leave blank to keep current password')
                
        except Exception as e:
            self.show_error('Error', f'Failed to load user data: {str(e)}')

    def validate_password(self):
        """Validate password requirements"""
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # If both password fields are empty, it means no change
        if not password and not confirm_password:
            return True

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
        """Hash the password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def accept(self):
        # Check if user can edit
        can_edit = self.is_admin or self.user_id == self.current_user_id
        if not can_edit:
            return

        # Validate required fields
        required_fields = [
            (self.username_input.text(), 'Username'),
            (self.email_input.text(), 'Email')
        ]
        
        if not self.validate_required_fields([f for f, _ in required_fields], 
                                          [n for _, n in required_fields]):
            return

        # Validate password if it's being changed
        if self.password_input.text() or self.confirm_password_input.text():
            if not self.validate_password():
                return

        try:
            cursor = self.db.conn.cursor()
            
            # Check if username already exists (excluding current user)
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", 
                         (self.username_input.text(), self.user_id))
            if cursor.fetchone():
                self.show_error('Error', 'Username already exists')
                return

            # Check if email already exists (excluding current user)
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", 
                         (self.email_input.text(), self.user_id))
            if cursor.fetchone():
                self.show_error('Error', 'Email already exists')
                return

            # Prepare update query
            if self.password_input.text():
                # Update with new password
                cursor.execute("""
                    UPDATE users SET username = ?, email = ?, password = ?, is_admin = ?
                    WHERE id = ?
                """, (
                    self.username_input.text(),
                    self.email_input.text(),
                    self.hash_password(self.password_input.text()),
                    self.is_admin_checkbox.isChecked(),
                    self.user_id
                ))
            else:
                # Update without changing password
                cursor.execute("""
                    UPDATE users SET username = ?, email = ?, is_admin = ?
                    WHERE id = ?
                """, (
                    self.username_input.text(),
                    self.email_input.text(),
                    self.is_admin_checkbox.isChecked(),
                    self.user_id
                ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to update user: {str(e)}') 