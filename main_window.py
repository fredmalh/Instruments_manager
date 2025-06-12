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
from instruments_window import InstrumentsWindow
from src.ui.windows.maintenance_window import MaintenanceWindow
from users_window import UsersWindow
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from src.ui.dialogs.instrument_details_dialog import InstrumentDetailsDialog
import sys

class AddInstrumentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.db if parent else Database()
        self.user_id = parent.user_id if parent else None
        self.is_admin = parent.is_admin if parent else False
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
                padding: 5px;
                border-radius: 3px;
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
        self.setWindowTitle('Add New Instrument')
        self.setMinimumSize(500, 600)  # Set minimum size instead of fixed size
        
        # Create main layout
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # General Information
        self.name_input = QLineEdit()
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.location_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Operational', 'Maintenance', 'Out of Service'])
        self.date_start_input = QLineEdit()
        self.date_start_input.setPlaceholderText("YYYY-MM-DD")

        # Responsible User
        self.responsible_user = QComboBox()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, username FROM users ORDER BY username")
        users = cursor.fetchall()
        for user_id, username in users:
            self.responsible_user.addItem(username, user_id)
        
        # If not admin, set responsible user to current user
        if not self.is_admin and self.user_id:
            index = self.responsible_user.findData(self.user_id)
            if index >= 0:
                self.responsible_user.setCurrentIndex(index)
            self.responsible_user.setEnabled(False)  # Disable selection for non-admins

        # Maintenance Types
        self.maintenance_type1 = QComboBox()
        self.maintenance_type2 = QComboBox()
        self.maintenance_type3 = QComboBox()
        
        cursor.execute("SELECT id, name FROM maintenance_types ORDER BY name")
        maintenance_types = cursor.fetchall()
        for maint_id, maint_name in maintenance_types:
            self.maintenance_type1.addItem(maint_name, maint_id)
            self.maintenance_type2.addItem(maint_name, maint_id)
            self.maintenance_type3.addItem(maint_name, maint_id)
        
        # Add "None" option to maintenance types 2 and 3
        self.maintenance_type2.insertItem(0, "None", None)
        self.maintenance_type3.insertItem(0, "None", None)
        self.maintenance_type2.setCurrentIndex(0)
        self.maintenance_type3.setCurrentIndex(0)

        # Maintenance Periods
        self.period1_input = QLineEdit()
        self.period2_input = QLineEdit()
        self.period3_input = QLineEdit()
        self.period1_input.setPlaceholderText("Weeks between maintenance")
        self.period2_input.setPlaceholderText("Weeks between maintenance")
        self.period3_input.setPlaceholderText("Weeks between maintenance")

        # Add fields to layout
        layout.addRow('Name:', self.name_input)
        layout.addRow('Model:', self.model_input)
        layout.addRow('Serial Number:', self.serial_input)
        layout.addRow('Location:', self.location_input)
        layout.addRow('Brand:', self.brand_input)
        layout.addRow('Status:', self.status_input)
        layout.addRow('Date Start Operating:', self.date_start_input)
        layout.addRow('Responsible User:', self.responsible_user)
        
        # Add maintenance section
        maintenance_group = QGroupBox("Maintenance Schedule")
        maintenance_layout = QFormLayout()
        
        maintenance_layout.addRow('Maintenance Type 1:', self.maintenance_type1)
        maintenance_layout.addRow('Period 1 (weeks):', self.period1_input)
        maintenance_layout.addRow('Maintenance Type 2:', self.maintenance_type2)
        maintenance_layout.addRow('Period 2 (weeks):', self.period2_input)
        maintenance_layout.addRow('Maintenance Type 3:', self.maintenance_type3)
        maintenance_layout.addRow('Period 3 (weeks):', self.period3_input)
        
        maintenance_group.setLayout(maintenance_layout)
        layout.addRow(maintenance_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')

        # Set fixed width for buttons
        button_width = 150
        save_button.setFixedWidth(button_width)
        cancel_button.setFixedWidth(button_width)

        save_button.clicked.connect(self.save_instrument)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

    def save_instrument(self):
        # Get all input values
        name = self.name_input.text().strip()
        model = self.model_input.text().strip()
        serial = self.serial_input.text().strip()
        location = self.location_input.text().strip()
        brand = self.brand_input.text().strip()
        status = self.status_input.currentText()
        date_start = self.date_start_input.text().strip()
        responsible_user_id = self.responsible_user.currentData()
        
        # Get maintenance types and periods
        maint_type1 = self.maintenance_type1.currentData()
        maint_type2 = self.maintenance_type2.currentData()
        maint_type3 = self.maintenance_type3.currentData()
        period1 = self.period1_input.text().strip()
        period2 = self.period2_input.text().strip()
        period3 = self.period3_input.text().strip()

        # Validate required fields
        if not all([name, model, serial, location, brand, date_start]):
            QMessageBox.warning(self, 'Error', 'Please fill all required fields')
            return

        try:
            # Validate date format
            try:
                # Validate date is in YYYY-MM-DD format
                datetime.strptime(date_start, '%Y-%m-%d')
            except ValueError:
                QMessageBox.warning(self, 'Error', 'Please enter date in YYYY-MM-DD format')
                return

            # Start transaction
            cursor = self.db.conn.cursor()
            
            # Insert instrument
            cursor.execute("""
                INSERT INTO instruments (
                    name, model, serial_number, location, status, brand, 
                    responsible_user_id, date_start_operating,
                    maintenance_1, period_1, maintenance_2, period_2,
                    maintenance_3, period_3
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, model, serial, location, status, brand,
                responsible_user_id, date_start,
                maint_type1, period1 if period1 else None,
                maint_type2, period2 if period2 else None,
                maint_type3, period3 if period3 else None
            ))
            
            # Get the ID of the newly inserted instrument
            instrument_id = cursor.lastrowid
            
            # Add initial maintenance records for each maintenance type
            if maint_type1 and period1:
                cursor.execute("""
                    INSERT INTO maintenance_records (
                        instrument_id, maintenance_type_id, performed_by, 
                        maintenance_date, notes
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (instrument_id, maint_type1, responsible_user_id, date_start, 
                      "Initial maintenance record - instrument start date"))
            
            if maint_type2 and period2:
                cursor.execute("""
                    INSERT INTO maintenance_records (
                        instrument_id, maintenance_type_id, performed_by, 
                        maintenance_date, notes
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (instrument_id, maint_type2, responsible_user_id, date_start, 
                      "Initial maintenance record - instrument start date"))
            
            if maint_type3 and period3:
                cursor.execute("""
                    INSERT INTO maintenance_records (
                        instrument_id, maintenance_type_id, performed_by, 
                        maintenance_date, notes
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (instrument_id, maint_type3, responsible_user_id, date_start, 
                      "Initial maintenance record - instrument start date"))
            
            self.db.conn.commit()
            self.accept()
        except ValueError:
            QMessageBox.warning(self, 'Error', 'Please enter valid numbers for maintenance periods')
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to save instrument: {str(e)}')

class AddMaintenanceDialog(QDialog):
    def __init__(self, instrument_id, user_id, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.instrument_id = instrument_id
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Maintenance Record')
        self.setFixedSize(400, 300)

        layout = QFormLayout(self)

        self.maintenance_type = QComboBox()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, name FROM maintenance_types")
        for id, name in cursor.fetchall():
            self.maintenance_type.addItem(name, id)

        self.notes_input = QTextEdit()

        layout.addRow('Maintenance Type:', self.maintenance_type)
        layout.addRow('Notes:', self.notes_input)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')

        # Set fixed width for buttons
        button_width = 150
        save_button.setFixedWidth(button_width)
        cancel_button.setFixedWidth(button_width)

        save_button.clicked.connect(self.save_maintenance)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

    def save_maintenance(self):
        maintenance_type_id = self.maintenance_type.currentData()
        notes = self.notes_input.toPlainText()

        if not notes:
            QMessageBox.warning(self, 'Error', 'Please enter maintenance notes')
            return

        try:
            self.db.add_maintenance_record(
                self.instrument_id,
                maintenance_type_id,
                self.user_id,
                notes
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

class InstrumentsWindow(QWidget):
    back_signal = pyqtSignal()  # Add signal for back button

    def __init__(self, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = parent.db if parent else Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_instruments()

    def update_user(self, user_id, is_admin):
        self.user_id = user_id
        self.is_admin = is_admin
        self.load_instruments()  # Refresh the list with new user permissions

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
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
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel('List of Instruments')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # Increased column count
        self.table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Model', 'Serial Number', 'Location', 'Status', 'Brand', 'Responsible User', 'Next Maintenance'
        ])
        # Remove double-click connection
        # self.table.itemDoubleClicked.connect(self.show_instrument_details)
        
        # Configure table for better scrolling and auto-resize
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(False)  # Changed to False to allow proper resizing
        
        # Add table to layout with stretch factor to make it expand
        layout.addWidget(self.table, 1)

        # Create buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        if self.is_admin:
            self.add_button = QPushButton('Add Instrument')
            self.add_button.clicked.connect(self.show_add_instrument)
            self.add_button.setFixedWidth(200)
            button_layout.addWidget(self.add_button)

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(200)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Remove the dynamic width adjustment since we're using fixed width
        pass

    def load_instruments(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                WITH maintenance_dates AS (
                    SELECT 
                        instrument_id,
                        maintenance_type_id,
                        MAX(maintenance_date) as last_date
                    FROM maintenance_records
                    GROUP BY instrument_id, maintenance_type_id
                )
                SELECT 
                    i.id, i.name, i.model, i.serial_number, i.location, 
                    i.status, i.brand, u.username as responsible_user,
                    CASE 
                        WHEN i.maintenance_1 IS NOT NULL AND i.period_1 IS NOT NULL THEN
                            CASE 
                                WHEN md1.last_date IS NULL THEN
                                    date(i.date_start_operating)
                                ELSE
                                    date(md1.last_date, '+' || (i.period_1 * 7) || ' days')
                            END
                        ELSE NULL
                    END as next_maintenance
                FROM instruments i
                LEFT JOIN users u ON i.responsible_user_id = u.id
                LEFT JOIN maintenance_dates md1 ON i.id = md1.instrument_id AND i.maintenance_1 = md1.maintenance_type_id
                ORDER BY i.name
            """)
            
            instruments = cursor.fetchall()
            self.table.setRowCount(len(instruments))

            for row, instrument in enumerate(instruments):
                # Create clickable name label
                name_label = QLabel(instrument['name'])
                name_label.setStyleSheet("""
                    QLabel {
                        color: #0d47a1;
                        text-decoration: underline;
                    }
                    QLabel:hover {
                        color: #1565c0;
                        cursor: pointer;
                    }
                """)
                name_label.mousePressEvent = lambda e, iid=instrument['id']: self.show_instrument_details(iid)
                
                # Add name label to second column (after ID)
                self.table.setCellWidget(row, 1, name_label)
                
                # Add other columns
                for col, value in enumerate([
                    instrument['id'],
                    instrument['model'],
                    instrument['serial_number'],
                    instrument['location'],
                    instrument['status'],
                    instrument['brand'],
                    instrument['responsible_user'] or 'Not Assigned',
                    format_date_for_display(instrument['next_maintenance']) if instrument['next_maintenance'] else 'Not Scheduled'
                ], 0):
                    if col == 1:  # Skip name column as it's already set
                        continue
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row, col, item)

            # Resize columns to content
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load instruments: {str(e)}')

    def show_add_instrument(self):
        dialog = AddInstrumentDialog(self)
        dialog.finished.connect(self.load_instruments)  # Connect to finished signal to refresh list
        dialog.show()  # Changed from exec() to show()

    def show_instrument_details(self, instrument_id):
        dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_instruments()

    def delete_instrument(self):
        """Delete the selected instrument"""
        try:
            # Get selected row
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, 'Warning', 'Please select an instrument to delete')
                return
            
            # Get the row index of the first selected item
            row = selected_items[0].row()
            
            # Get instrument name and ID
            instrument_name = self.table.cellWidget(row, 1).text()  # Name is in second column
            instrument_id = self.table.item(row, 0).text()
            
            if not instrument_id:
                QMessageBox.warning(self, 'Error', 'Could not find instrument ID')
                return
            
            # Get count of maintenance records
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM maintenance_records 
                WHERE instrument_id = ?
            """, (instrument_id,))
            result = cursor.fetchone()
            maintenance_count = result['count']
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Are you sure you want to delete instrument {instrument_name}?\n\n'
                f'This will also delete {maintenance_count} maintenance record(s).',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Delete maintenance records first
                    cursor.execute("DELETE FROM maintenance_records WHERE instrument_id = ?", (instrument_id,))
                    
                    # Delete instrument
                    cursor.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
                    
                    self.db.conn.commit()
                    
                    # Refresh instruments table
                    self.load_instruments()
                    
                    QMessageBox.information(self, 'Success', f'Instrument {instrument_name} deleted successfully')
                    
                except Exception as e:
                    self.db.conn.rollback()
                    raise e
                
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to delete instrument: {str(e)}')

class CentralWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Laboratory Instruments Management System')
        
        # Set initial size
        window_width = 800
        window_height = 600
        self.setMinimumSize(800, 600)
        
        # Get the screen geometry
        screen = self.screen()
        screen_geometry = screen.geometry()
        
        # Calculate center position
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        
        # Set window position and size
        self.setGeometry(x, y, window_width, window_height)
        
        try:
            self.db = Database()
        except FileNotFoundError as e:
            QMessageBox.critical(self, 'Error', str(e))
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to connect to database: {str(e)}')
            sys.exit(1)
            
        self.init_ui()
        self.apply_dark_theme()
        self.show()
        self.showMaximized()  # Start maximized

    def init_ui(self):
        self.setWindowTitle('Laboratory Instrument Manager')

        # Create stacked widget to hold all views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create and add views
        self.login_view = LoginWindow(self.db)  # Pass database connection
        self.main_menu_view = None  # Will be created when needed
        self.instruments_view = None
        self.maintenance_view = None
        self.users_view = None

        # Add login view
        self.stacked_widget.addWidget(self.login_view)

        # Connect login success signal
        self.login_view.login_successful.connect(self.handle_login)

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
            if not self.main_menu_view:
                self.main_menu_view = MainMenu(user_id, is_admin, self.db)  # Pass database connection
                self.main_menu_view.show_instruments_signal.connect(self.show_instruments)
                self.main_menu_view.show_maintenance_signal.connect(self.show_maintenance)
                self.main_menu_view.show_users_signal.connect(self.show_users)
                self.main_menu_view.logout_signal.connect(self.show_login)
                self.stacked_widget.addWidget(self.main_menu_view)
            else:
                self.main_menu_view.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.main_menu_view)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show main menu: {str(e)}')

    def show_instruments(self, user_id, is_admin):
        """Show the instruments view"""
        try:
            if not self.instruments_view:
                self.instruments_view = InstrumentsWindow(user_id, is_admin, self)
                self.instruments_view.back_signal.connect(lambda: self.show_main_menu(user_id, is_admin))
                self.stacked_widget.addWidget(self.instruments_view)
            else:
                self.instruments_view.update_user(user_id, is_admin)
            
            self.stacked_widget.setCurrentWidget(self.instruments_view)
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
            if self.main_menu_view:
                self.main_menu_view.update_user(None, False)
                self.main_menu_view.deleteLater()
                self.main_menu_view = None
            if self.instruments_view:
                self.instruments_view.update_user(None, False)
                self.instruments_view.deleteLater()
                self.instruments_view = None
            if self.maintenance_view:
                self.maintenance_view.update_user(None, False)
                self.maintenance_view.deleteLater()
                self.maintenance_view = None
            if self.users_view:
                self.users_view.update_user(None, False)
                self.users_view.deleteLater()
                self.users_view = None
            
            # Clear and reset login view
            self.login_view.clear_inputs()
            
            # Create new database connection
            if hasattr(self, 'db') and self.db:
                self.db.conn.close()
            self.db = Database()
            self.login_view.db = self.db
            
            # Show login view
            self.stacked_widget.setCurrentWidget(self.login_view)
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
            # Close database connection
            if hasattr(self, 'db') and self.db:
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