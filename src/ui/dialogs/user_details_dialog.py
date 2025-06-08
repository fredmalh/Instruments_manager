from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDialog, QPushButton)
from ..base.base_dialog import BaseDialog
import hashlib

class UserDetailsDialog(BaseDialog):
    def __init__(self, user_id, current_user_id, is_admin, parent=None):
        self.user_id = user_id
        self.current_user_id = current_user_id
        self.is_admin = is_admin
        super().__init__(parent)
        self.setWindowTitle('User Details')
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_user_data()

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
            for widget in self.findChildren((QLineEdit, QComboBox)):
                widget.setEnabled(False)

    def load_user_data(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT username, email, role FROM users WHERE id = ?
            """, (self.user_id,))
            
            user = cursor.fetchone()
            if user:
                self.username_input.setText(user['username'])
                self.email_input.setText(user['email'])
                self.role_input.setCurrentText(user['role'])
                
                # Clear password fields
                self.password_input.clear()
                self.confirm_password_input.clear()
                
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
        """Hash the password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

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
            cursor.execute("""
                SELECT id FROM users 
                WHERE username = ? AND id != ?
            """, (self.username_input.text(), self.user_id))
            if cursor.fetchone():
                self.show_error('Error', 'Username already exists')
                return

            # Check if email already exists (excluding current user)
            cursor.execute("""
                SELECT id FROM users 
                WHERE email = ? AND id != ?
            """, (self.email_input.text(), self.user_id))
            if cursor.fetchone():
                self.show_error('Error', 'Email already exists')
                return

            # Prepare update query
            if self.password_input.text():
                # Update with new password
                cursor.execute("""
                    UPDATE users SET
                        username = ?, email = ?, password = ?, role = ?
                    WHERE id = ?
                """, (
                    self.username_input.text(),
                    self.email_input.text(),
                    self.hash_password(self.password_input.text()),
                    self.role_input.currentText(),
                    self.user_id
                ))
            else:
                # Update without changing password
                cursor.execute("""
                    UPDATE users SET
                        username = ?, email = ?, role = ?
                    WHERE id = ?
                """, (
                    self.username_input.text(),
                    self.email_input.text(),
                    self.role_input.currentText(),
                    self.user_id
                ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to update user: {str(e)}') 