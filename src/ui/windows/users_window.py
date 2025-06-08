from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from ..base.base_main_window import BaseMainWindow
from ..base.base_table import BaseTable
from database import Database
from datetime import datetime

class UsersWindow(BaseMainWindow):
    back_signal = pyqtSignal()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('User Management')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'ID', 'Username', 'Email', 'Role', 'Last Login'
        ])
        self.table.row_double_clicked.connect(self.show_user_details)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
            {
                'text': 'Add User',
                'callback': self.add_user,
                'visible_if_admin': True,
                'position': 'left'
            },
            {
                'text': 'Refresh',
                'callback': self.load_users,
                'position': 'center'
            },
            {
                'text': 'Back to Main Menu',
                'callback': self.back_signal.emit,
                'position': 'right'
            }
        ]
        self.main_layout.addLayout(self.create_button_layout(buttons_config))

        # Load initial data
        self.load_users()

    def load_users(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, last_login
                FROM users
                ORDER BY username
            """)
            
            users = cursor.fetchall()
            self.table.clear_table()

            for user in users:
                # Format data for display
                row_data = [
                    user['id'],
                    user['username'],
                    user['email'],
                    user['role'],
                    user['last_login'] or 'Never'
                ]
                
                # Add row to table
                self.table.add_row(row_data, user['id'])

            # Resize columns to content
            self.table.resize_columns_to_content()
            
        except Exception as e:
            self.show_error('Error', f'Failed to load users: {str(e)}')

    def show_user_details(self, row):
        user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = UserDetailsDialog(user_id, self.user_id, self.is_admin, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        
        # Update buttons visibility
        if hasattr(self, 'add_button'):
            self.add_button.setVisible(self.is_admin)
        
        # Reload data
        self.load_users() 