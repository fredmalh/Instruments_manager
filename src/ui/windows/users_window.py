from PyQt6.QtWidgets import QMessageBox, QDialog
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
                'position': 'center'
            },
            {
                'text': 'Edit User',
                'callback': self.edit_selected_user,
                'visible_if_admin': True,
                'position': 'center'
            },
            {
                'text': 'Delete User',
                'callback': self.delete_selected_user,
                'visible_if_admin': True,
                'position': 'center'
            },
            {
                'text': 'Refresh',
                'callback': self.load_data,
                'position': 'center'
            },
            {
                'text': 'Back to Main Menu',
                'callback': self.back_signal.emit,
                'position': 'center'
            }
        ]
        self.main_layout.addLayout(self.create_button_layout(buttons_config))

    def handle_cell_click(self, row, column):
        """Handle cell click events"""
        if column == 0:  # Only handle clicks on the Username column
            user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if user_id:
                self.edit_user(user_id)

    def load_data(self):
        """Load users data"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, username, email, is_admin FROM users ORDER BY username")
            
            self.table.clear_table()
            
            for user in cursor.fetchall():
                self.table.add_row([
                    user['username'],
                    user['email'],
                    'Administrator' if user['is_admin'] else 'User'
                ], user['id'])
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load users: {str(e)}')

    def add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_user(self, user_id):
        """Edit an existing user"""
        dialog = UserDetailsDialog(user_id, self.user_id, self.is_admin, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_selected_user(self):
        """Edit the selected user"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Warning', 'Please select a user to edit')
            return
        
        row = selected_items[0].row()
        user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if user_id:
            self.edit_user(user_id)

    def delete_selected_user(self):
        """Delete the selected user"""
        try:
            # Get selected row
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, 'Warning', 'Please select a user to delete')
                return
            
            # Get the row index of the first selected item
            row = selected_items[0].row()
            user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            username = self.table.item(row, 0).text()
            
            # Check if user is responsible for any instruments
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM instruments WHERE responsible_user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                # Get list of instruments where user is responsible
                cursor.execute("SELECT name FROM instruments WHERE responsible_user_id = ?", (user_id,))
                instruments = cursor.fetchall()
                instrument_list = "\n".join([f"- {inst['name']}" for inst in instruments])
                
                QMessageBox.warning(
                    self, 
                    'Cannot Delete User',
                    f'Cannot delete user {username} because they are responsible for the following instruments:\n\n'
                    f'{instrument_list}\n\n'
                    'Please reassign these instruments to another user before deleting.'
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Are you sure you want to delete user {username}?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                self.db.conn.commit()
                self.load_data()
                QMessageBox.information(self, 'Success', f'User {username} deleted successfully')
                
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to delete user: {str(e)}')
 