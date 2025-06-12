from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from ..base.base_data_window import BaseDataWindow
from ..base.base_table import BaseTable
from database import Database
from ..dialogs.user_details_dialog import UserDetailsDialog
from ..dialogs.add_user_dialog import AddUserDialog

class UsersWindow(BaseDataWindow):
    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Users Management')

        # Create table
        self.table = BaseTable()
        self.table.set_headers(['Username', 'Email', 'Role'])
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
                'callback': self.load_data,
                'position': 'center'
            },
            {
                'text': 'Back to Main Menu',
                'callback': self.back_signal.emit,
                'position': 'right'
            }
        ]
        self.main_layout.addLayout(self.create_button_layout(buttons_config))

    def handle_cell_click(self, row, column):
        """Handle cell click events"""
        if column == 0:  # Only handle clicks on the Username column
            user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if user_id:
                dialog = UserDetailsDialog(user_id, self.user_id, self.is_admin, self)
                dialog.exec()

    def load_data(self):
        """Load users data"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    username,
                    email,
                    CASE 
                        WHEN is_admin = 1 THEN 'Administrator'
                        ELSE 'User'
                    END as role
                FROM users
                ORDER BY username
            """)
            
            self.table.clear_table()
            
            for user in cursor.fetchall():
                # Add row using BaseTable's add_row method with row_id
                self.table.add_row([
                    user['username'],  # Username
                    user['email'],     # Email
                    user['role']       # Role
                ], user['id'])  # Pass the user ID as row_id
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load users: {str(e)}')

    def add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data() 