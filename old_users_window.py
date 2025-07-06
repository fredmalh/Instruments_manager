from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QDialog, QLineEdit, QFormLayout, QCheckBox, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database import Database
import bcrypt

class UserDialog(QDialog):
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = parent.db if parent else Database()  # Use parent's db connection if available
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add User' if not self.user_id else 'Edit User')
        self.setFixedSize(400, 300)

        layout = QFormLayout(self)

        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.is_admin_checkbox = QCheckBox()

        layout.addRow('Username:', self.username_input)
        layout.addRow('Email:', self.email_input)
        layout.addRow('Password:', self.password_input)
        layout.addRow('Admin:', self.is_admin_checkbox)

        if self.user_id:
            # Load existing user data
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT username, email, is_admin FROM users WHERE id = ?", (self.user_id,))
            user = cursor.fetchone()
            if user:
                self.username_input.setText(user[0])
                self.email_input.setText(user[1])
                self.is_admin_checkbox.setChecked(bool(user[2]))
                self.password_input.setPlaceholderText('Leave blank to keep current password')

        buttons_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')

        # Set fixed width for buttons
        button_width = 150
        save_button.setFixedWidth(button_width)
        cancel_button.setFixedWidth(button_width)

        save_button.clicked.connect(self.save_user)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

    def save_user(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        is_admin = self.is_admin_checkbox.isChecked()

        if not username or not email:
            QMessageBox.warning(self, 'Error', 'Please fill in all required fields')
            return

        try:
            if self.user_id:
                # Update existing user
                if password:
                    # Hash new password
                    salt = bcrypt.gensalt()
                    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                    cursor = self.db.conn.cursor()
                    cursor.execute("""
                        UPDATE users
                        SET username = ?, email = ?, password = ?, is_admin = ?
                        WHERE id = ?
                    """, (username, email, hashed, is_admin, self.user_id))
                else:
                    # Keep existing password
                    cursor = self.db.conn.cursor()
                    cursor.execute("""
                        UPDATE users
                        SET username = ?, email = ?, is_admin = ?
                        WHERE id = ?
                    """, (username, email, is_admin, self.user_id))
            else:
                # Create new user
                if not password:
                    QMessageBox.warning(self, 'Error', 'Please enter a password for the new user')
                    return
                
                # Hash password
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password, is_admin)
                    VALUES (?, ?, ?, ?)
                """, (username, email, hashed, is_admin))

            self.db.conn.commit()
            self.accept()
            
            # Force refresh of parent window's table
            if isinstance(self.parent(), OldUsersWindow):
                self.parent().load_users()
                
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))
            self.db.conn.rollback()  # Rollback on error

class OldUsersWindow(QWidget):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_users()

    def apply_dark_theme(self):
        self.setStyleSheet("""
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
                margin: 0px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
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
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Set minimum size before creating widgets
        self.setMinimumSize(800, 600)

        # Title
        title = QLabel('User Management')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Username', 'Full Name', 'Email', 'Role'])
        
        # Configure table for better scrolling and auto-resize
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self.table)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Create buttons with fixed width
        if self.is_admin:
            self.add_button = QPushButton('Add User')
            self.add_button.clicked.connect(self.add_user)
            self.add_button.setFixedWidth(150)  # Set fixed width

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.load_users)
        refresh_button.setFixedWidth(150)  # Set fixed width

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(150)  # Set fixed width

        # Add buttons to layout with proper spacing
        bottom_layout.addStretch()
        if self.is_admin:
            bottom_layout.addWidget(self.add_button)
        bottom_layout.addWidget(refresh_button)
        bottom_layout.addWidget(back_button)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Remove dynamic width adjustment since we're using fixed width
        pass

    def load_users(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, username, email, is_admin FROM users")
        users = cursor.fetchall()

        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            # Create clickable username label
            username_label = QLabel(user['username'])
            username_label.setStyleSheet("""
                QLabel {
                    color: #0d47a1;
                    text-decoration: underline;
                }
                QLabel:hover {
                    color: #1565c0;
                    cursor: pointer;
                }
            """)
            username_label.mousePressEvent = lambda e, uid=user['id']: self.edit_user(uid)
            
            # Add username label to first column
            self.table.setCellWidget(row, 0, username_label)
            
            # Add other columns
            for col, value in enumerate(user[1:], 1):
                if col == 3:  # Role column (is_admin)
                    item = QTableWidgetItem("Admin" if value else "Normal User")
                else:
                    item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

        # Resize columns to content
        self.table.resizeColumnsToContents()

    def add_user(self):
        dialog = UserDialog(parent=self)  # Pass self as parent to share database connection
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()  # Reload the table after adding a user

    def edit_user(self, user_id):
        dialog = UserDialog(user_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        self.init_ui()  # Reinitialize UI to update buttons
        self.load_users()  # Reload users 