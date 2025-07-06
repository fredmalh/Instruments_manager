from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QDialog, QLineEdit, QComboBox, QTextEdit, QMessageBox,
                             QTabWidget, QFormLayout, QStackedWidget, QGroupBox,
                             QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QFont
from database import Database
from datetime import datetime
from login_window import LoginWindow
from main_menu import MainMenu
from src.ui.windows.instruments_window import InstrumentsWindow
from src.ui.windows.maintenance_window import MaintenanceWindow
from src.ui.windows.users_window import UsersWindow
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from src.ui.dialogs.instrument_details_dialog import InstrumentDetailsDialog
from src.ui.dialogs.add_instrument_dialog import AddInstrumentDialog
from src.ui.dialogs.add_maintenance_dialog import AddMaintenanceDialog
import sys

class CentralWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        
        # Initialize window attributes
        self.instruments_window = None
        self.maintenance_view = None
        self.users_view = None
        self.main_menu = None
        self.login_window = None
        
        self.init_ui()
        self.apply_dark_theme()
        self.show_login()
        
        # Show window maximized
        self.showMaximized()

    def init_ui(self):
        self.setWindowTitle('Laboratory Instrument Manager')
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Create login window
        self.login_window = LoginWindow(self.db)
        self.login_window.login_successful.connect(self.handle_login)
        self.stacked_widget.addWidget(self.login_window)

        # Create main menu
        self.main_menu = MainMenu(None, False, self.db)
        self.main_menu.show_instruments_signal.connect(self.show_instruments)
        self.main_menu.show_maintenance_signal.connect(self.show_maintenance)
        self.main_menu.show_users_signal.connect(self.show_users)
        self.main_menu.logout_signal.connect(self.show_login)
        self.stacked_widget.addWidget(self.main_menu)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

    def handle_login(self, user_id, is_admin):
        """Handle successful login"""
        try:
            # Update current user info
            self.current_user_id = user_id
            self.current_is_admin = is_admin
            self.show_main_menu(user_id, is_admin)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show main menu: {str(e)}')

    def show_main_menu(self, user_id, is_admin):
        """Show the main menu view"""
        try:
            if not self.main_menu:
                self.main_menu = MainMenu(user_id, is_admin, self.db)  # Pass database connection
                self.main_menu.show_instruments_signal.connect(self.show_instruments)
                self.main_menu.show_maintenance_signal.connect(self.show_maintenance)
                self.main_menu.show_users_signal.connect(self.show_users)
                self.main_menu.logout_signal.connect(self.show_login)
                self.stacked_widget.addWidget(self.main_menu)
            else:
                self.main_menu.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.main_menu)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show main menu: {str(e)}')

    def show_instruments(self, user_id, is_admin):
        """Show the instruments view"""
        try:
            if not self.instruments_window:
                self.instruments_window = InstrumentsWindow(user_id, is_admin, self.db)
                self.instruments_window.back_signal.connect(lambda: self.show_main_menu(user_id, is_admin))
                self.stacked_widget.addWidget(self.instruments_window)
            else:
                self.instruments_window.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.instruments_window)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show instruments: {str(e)}')

    def show_maintenance(self, user_id, is_admin):
        """Show the maintenance view"""
        try:
            if not self.maintenance_view:
                self.maintenance_view = MaintenanceWindow(user_id, is_admin, self.db)
                self.maintenance_view.back_signal.connect(lambda: self.show_main_menu(user_id, is_admin))
                self.stacked_widget.addWidget(self.maintenance_view)
            else:
                self.maintenance_view.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.maintenance_view)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show maintenance: {str(e)}')

    def show_users(self, user_id, is_admin):
        """Show the users view"""
        try:
            if not self.users_view:
                self.users_view = UsersWindow(user_id, is_admin, self.db)
                self.users_view.back_signal.connect(lambda: self.show_main_menu(user_id, is_admin))
                self.stacked_widget.addWidget(self.users_view)
            else:
                self.users_view.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.users_view)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show users: {str(e)}')

    def show_login(self):
        """Show the login view"""
        try:
            # Clear current user info
            self.current_user_id = None
            self.current_is_admin = False
            
            # Reset all views
            if self.main_menu:
                self.main_menu.update_user(None, False)
                self.main_menu.deleteLater()
                self.main_menu = None
            if self.instruments_window:
                self.instruments_window.update_user(None, False)
                self.instruments_window.deleteLater()
                self.instruments_window = None
            if self.maintenance_view:
                self.maintenance_view.update_user(None, False)
                self.maintenance_view.deleteLater()
                self.maintenance_view = None
            if self.users_view:
                self.users_view.update_user(None, False)
                self.users_view.deleteLater()
                self.users_view = None
            
            # Clear and reset login view
            self.login_window.clear_inputs()
            
            # Reuse existing database connection (don't create a new one)
            # The existing self.db connection is still valid and can be reused
            
            # Show login view
            self.stacked_widget.setCurrentWidget(self.login_window)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show login: {str(e)}')

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close database connection and release lock
            if hasattr(self, 'db') and self.db:
                self.db.release_lock()  # Release the database lock
                self.db.conn.close()
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Update size of current widget
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.resize(self.size())

    def moveEvent(self, event):
        """Handle window move events"""
        super().moveEvent(event)
        # Update size of current widget when window is moved
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.resize(self.size())

    def delete_user(self):
        """Delete the selected user"""
        try:
            # Get selected row
            selected_items = self.users_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, 'Warning', 'Please select a user to delete')
                return
            
            # Get the row index of the first selected item
            row = selected_items[0].row()
            user_id = self.users_table.item(row, 0).text()
            username = self.users_table.item(row, 1).text()
            
            # Check if user is responsible for any instruments
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM instruments 
                WHERE responsible_user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                # Get list of instruments where user is responsible
                cursor.execute("""
                    SELECT name 
                    FROM instruments 
                    WHERE responsible_user_id = ?
                """, (user_id,))
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
                # Delete user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                self.db.conn.commit()
                
                # Refresh users table
                self.load_users()
                
                QMessageBox.information(self, 'Success', f'User {username} deleted successfully')
                
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to delete user: {str(e)}') 