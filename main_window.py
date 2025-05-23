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
from maintenance_window import MaintenanceWindow
from users_window import UsersWindow

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

        # Basic Information
        self.name_input = QLineEdit()
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.location_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Operational', 'Maintenance', 'Out of Service'])
        self.date_start_input = QLineEdit()
        self.date_start_input.setPlaceholderText("DD-MM-YYYY")

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
                # Convert DD-MM-YYYY to YYYY-MM-DD for SQLite
                day, month, year = date_start.split('-')
                date_start = f"{year}-{month}-{day}"
            except ValueError:
                QMessageBox.warning(self, 'Error', 'Please enter date in DD-MM-YYYY format')
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

class InstrumentDetailsDialog(QMainWindow):
    def __init__(self, instrument_id, parent=None):
        super().__init__(parent)
        self.db = parent.db if parent else Database()
        self.user_id = parent.user_id if parent else None
        self.is_admin = parent.is_admin if parent else False
        self.instrument_id = instrument_id
        self.init_ui()
        self.apply_dark_theme()
        self.load_instrument_data()
        self.set_edit_mode(False)  # Start in read-only mode

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
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
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3d3d3d;
                margin-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

    def init_ui(self):
        self.setWindowTitle('Instrument Details')
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)

        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        # Create input fields instead of labels
        self.name_input = QLineEdit()
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.location_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Operational', 'Maintenance', 'Out of Service'])
        self.responsible_user = QComboBox()
        self.date_start_input = QLineEdit()
        self.date_start_input.setPlaceholderText("DD-MM-YYYY")

        # Load users for responsible user dropdown
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, username FROM users ORDER BY username")
        users = cursor.fetchall()
        for user_id, username in users:
            self.responsible_user.addItem(username, user_id)

        basic_layout.addRow('Name:', self.name_input)
        basic_layout.addRow('Model:', self.model_input)
        basic_layout.addRow('Serial Number:', self.serial_input)
        basic_layout.addRow('Location:', self.location_input)
        basic_layout.addRow('Brand:', self.brand_input)
        basic_layout.addRow('Status:', self.status_input)
        basic_layout.addRow('Responsible User:', self.responsible_user)
        basic_layout.addRow('Date Start Operating:', self.date_start_input)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Maintenance Configuration Group
        maintenance_config_group = QGroupBox("Maintenance Configuration")
        maintenance_config_layout = QFormLayout()

        # Create maintenance type and period inputs
        self.maintenance_type1 = QComboBox()
        self.maintenance_type2 = QComboBox()
        self.maintenance_type3 = QComboBox()
        self.period1_input = QLineEdit()
        self.period2_input = QLineEdit()
        self.period3_input = QLineEdit()
        
        # Set placeholders for period inputs
        self.period1_input.setPlaceholderText("Weeks between maintenance")
        self.period2_input.setPlaceholderText("Weeks between maintenance")
        self.period3_input.setPlaceholderText("Weeks between maintenance")

        # Load maintenance types
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

        maintenance_config_layout.addRow('Maintenance Type 1:', self.maintenance_type1)
        maintenance_config_layout.addRow('Period 1 (weeks):', self.period1_input)
        maintenance_config_layout.addRow('Maintenance Type 2:', self.maintenance_type2)
        maintenance_config_layout.addRow('Period 2 (weeks):', self.period2_input)
        maintenance_config_layout.addRow('Maintenance Type 3:', self.maintenance_type3)
        maintenance_config_layout.addRow('Period 3 (weeks):', self.period3_input)
        
        maintenance_config_group.setLayout(maintenance_config_layout)
        layout.addWidget(maintenance_config_group)

        # Maintenance Schedule Group
        schedule_group = QGroupBox("Maintenance Schedule")
        schedule_layout = QVBoxLayout()
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(3)
        self.schedule_table.setHorizontalHeaderLabels(['Maintenance Type', 'Period (weeks)', 'Last Maintenance'])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        self.schedule_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.schedule_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.schedule_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.schedule_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.schedule_table.setAlternatingRowColors(True)
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only by default
        schedule_layout.addWidget(self.schedule_table)
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        # Maintenance History Group
        history_group = QGroupBox("Maintenance History")
        history_layout = QVBoxLayout()
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(['Date', 'Type', 'Performed By', 'Notes'])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.history_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.history_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only by default
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.edit_button = QPushButton('Edit Data')
        self.save_button = QPushButton('Save Changes')
        self.cancel_button = QPushButton('Cancel')
        add_maintenance_button = QPushButton('Add Maintenance Record')
        close_button = QPushButton('Close')

        # Only show add maintenance button if user is admin or responsible for the instrument
        if self.is_admin or self.is_responsible_user():
            add_maintenance_button.clicked.connect(self.add_maintenance)
            buttons_layout.addWidget(add_maintenance_button)

        self.edit_button.clicked.connect(lambda: self.set_edit_mode(True))
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button.clicked.connect(lambda: self.set_edit_mode(False))
        close_button.clicked.connect(self.close)

        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)

    def set_edit_mode(self, edit_mode):
        # Enable/disable editing of fields
        self.name_input.setReadOnly(not edit_mode)
        self.model_input.setReadOnly(not edit_mode)
        self.serial_input.setReadOnly(not edit_mode)
        self.location_input.setReadOnly(not edit_mode)
        self.brand_input.setReadOnly(not edit_mode)
        self.status_input.setEnabled(edit_mode)
        self.responsible_user.setEnabled(edit_mode)
        self.date_start_input.setReadOnly(not edit_mode)
        
        # Enable/disable maintenance configuration
        self.maintenance_type1.setEnabled(edit_mode)
        self.maintenance_type2.setEnabled(edit_mode)
        self.maintenance_type3.setEnabled(edit_mode)
        self.period1_input.setReadOnly(not edit_mode)
        self.period2_input.setReadOnly(not edit_mode)
        self.period3_input.setReadOnly(not edit_mode)

        # Set table edit triggers based on edit mode
        if edit_mode:
            self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
            self.history_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        else:
            self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Show/hide appropriate buttons
        self.edit_button.setVisible(not edit_mode)
        self.save_button.setVisible(edit_mode)
        self.cancel_button.setVisible(edit_mode)

    def save_changes(self):
        try:
            # Get current values
            name = self.name_input.text().strip()
            model = self.model_input.text().strip()
            serial = self.serial_input.text().strip()
            location = self.location_input.text().strip()
            brand = self.brand_input.text().strip()
            status = self.status_input.currentText()
            responsible_user_id = self.responsible_user.currentData()
            date_start = self.date_start_input.text().strip()
            
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

            # Validate date format
            try:
                # Convert DD-MM-YYYY to YYYY-MM-DD for SQLite
                day, month, year = date_start.split('-')
                date_start = f"{year}-{month}-{day}"
            except ValueError:
                QMessageBox.warning(self, 'Error', 'Please enter date in DD-MM-YYYY format')
                return

            # Validate maintenance periods
            try:
                if period1:
                    period1 = int(period1)
                if period2:
                    period2 = int(period2)
                if period3:
                    period3 = int(period3)
            except ValueError:
                QMessageBox.warning(self, 'Error', 'Please enter valid numbers for maintenance periods')
                return

            # Update database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE instruments 
                SET name = ?, model = ?, serial_number = ?, location = ?, 
                    brand = ?, status = ?, responsible_user_id = ?, date_start_operating = ?,
                    maintenance_1 = ?, period_1 = ?, maintenance_2 = ?, period_2 = ?,
                    maintenance_3 = ?, period_3 = ?
                WHERE id = ?
            """, (name, model, serial, location, brand, status, 
                  responsible_user_id, date_start,
                  maint_type1, period1 if period1 else None,
                  maint_type2, period2 if period2 else None,
                  maint_type3, period3 if period3 else None,
                  self.instrument_id))
            
            self.db.conn.commit()
            self.set_edit_mode(False)  # Return to read-only mode
            self.load_instrument_data()  # Refresh the data
            
            # Notify parent to refresh the list
            if hasattr(self.parent(), 'load_instruments'):
                self.parent().load_instruments()

        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to save changes: {str(e)}')

    def load_instrument_data(self):
        try:
            cursor = self.db.conn.cursor()
            
            # Load basic information
            cursor.execute("""
                SELECT i.*, u.username as responsible_username
                FROM instruments i
                LEFT JOIN users u ON i.responsible_user_id = u.id
                WHERE i.id = ?
            """, (self.instrument_id,))
            instrument = cursor.fetchone()

            if instrument:
                self.name_input.setText(instrument['name'])
                self.model_input.setText(instrument['model'])
                self.serial_input.setText(instrument['serial_number'])
                self.location_input.setText(instrument['location'])
                self.brand_input.setText(instrument['brand'])
                self.status_input.setCurrentText(instrument['status'])
                
                # Format and set the date start operating
                if instrument['date_start_operating']:
                    try:
                        # Convert YYYY-MM-DD to DD-MM-YYYY for display
                        year, month, day = instrument['date_start_operating'].split('-')
                        formatted_date = f"{day}-{month}-{year}"
                        self.date_start_input.setText(formatted_date)
                    except:
                        self.date_start_input.setText(instrument['date_start_operating'])
                else:
                    self.date_start_input.setText('')
                
                # Set responsible user
                index = self.responsible_user.findData(instrument['responsible_user_id'])
                if index >= 0:
                    self.responsible_user.setCurrentIndex(index)

                # Set maintenance types and periods
                if instrument['maintenance_1']:
                    index = self.maintenance_type1.findData(instrument['maintenance_1'])
                    if index >= 0:
                        self.maintenance_type1.setCurrentIndex(index)
                if instrument['maintenance_2']:
                    index = self.maintenance_type2.findData(instrument['maintenance_2'])
                    if index >= 0:
                        self.maintenance_type2.setCurrentIndex(index)
                if instrument['maintenance_3']:
                    index = self.maintenance_type3.findData(instrument['maintenance_3'])
                    if index >= 0:
                        self.maintenance_type3.setCurrentIndex(index)

                self.period1_input.setText(str(instrument['period_1']) if instrument['period_1'] else '')
                self.period2_input.setText(str(instrument['period_2']) if instrument['period_2'] else '')
                self.period3_input.setText(str(instrument['period_3']) if instrument['period_3'] else '')

            # Load maintenance schedule
            cursor.execute("""
                SELECT 
                    mt1.name as type_name_1,
                    i.period_1,
                    (SELECT MAX(maintenance_date) FROM maintenance_records 
                     WHERE instrument_id = ? AND maintenance_type_id = i.maintenance_1) as last_maintenance_1,
                    mt2.name as type_name_2,
                    i.period_2,
                    (SELECT MAX(maintenance_date) FROM maintenance_records 
                     WHERE instrument_id = ? AND maintenance_type_id = i.maintenance_2) as last_maintenance_2,
                    mt3.name as type_name_3,
                    i.period_3,
                    (SELECT MAX(maintenance_date) FROM maintenance_records 
                     WHERE instrument_id = ? AND maintenance_type_id = i.maintenance_3) as last_maintenance_3
                FROM instruments i
                LEFT JOIN maintenance_types mt1 ON i.maintenance_1 = mt1.id
                LEFT JOIN maintenance_types mt2 ON i.maintenance_2 = mt2.id
                LEFT JOIN maintenance_types mt3 ON i.maintenance_3 = mt3.id
                WHERE i.id = ?
            """, (self.instrument_id, self.instrument_id, self.instrument_id, self.instrument_id))
            schedule = cursor.fetchone()

            if schedule:
                # Create rows for each maintenance type that exists
                rows = []
                if schedule['type_name_1']:
                    rows.append((schedule['type_name_1'], schedule['period_1'], schedule['last_maintenance_1']))
                if schedule['type_name_2']:
                    rows.append((schedule['type_name_2'], schedule['period_2'], schedule['last_maintenance_2']))
                if schedule['type_name_3']:
                    rows.append((schedule['type_name_3'], schedule['period_3'], schedule['last_maintenance_3']))

                self.schedule_table.setRowCount(len(rows))
                for i, (type_name, period, last_maintenance) in enumerate(rows):
                    for col, value in enumerate([
                        type_name,
                        str(period),
                        str(last_maintenance or 'Never')
                    ]):
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        self.schedule_table.setItem(i, col, item)

            # Load maintenance history
            cursor.execute("""
                SELECT mr.maintenance_date, mt.name as type_name, u.username as performed_by, mr.notes
                FROM maintenance_records mr
                JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
                JOIN users u ON mr.performed_by = u.id
                WHERE mr.instrument_id = ?
                ORDER BY mr.maintenance_date DESC
            """, (self.instrument_id,))
            history = cursor.fetchall()

            self.history_table.setRowCount(len(history))
            for i, record in enumerate(history):
                for col, value in enumerate([
                    str(record['maintenance_date']),
                    record['type_name'],
                    record['performed_by'],
                    record['notes']
                ]):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.history_table.setItem(i, col, item)

        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load instrument data: {str(e)}')

    def is_responsible_user(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT responsible_user_id 
                FROM instruments 
                WHERE id = ?
            """, (self.instrument_id,))
            result = cursor.fetchone()
            return result and result['responsible_user_id'] == self.user_id
        except Exception:
            return False

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.instrument_id, self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_instrument_data()  # Refresh the data

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
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('Instrument List')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(17)  # Updated number of columns
        self.table.setHorizontalHeaderLabels([
            'Name', 'Model', 'Serial Number', 'Location', 'Brand', 'Status', 'Responsible User',
            'Last Maintenance 1', 'Last Maintenance 2', 'Last Maintenance 3',
            'Next Maintenance',
            'Maintenance 1', 'Period 1', 'Maintenance 2', 'Period 2', 'Maintenance 3', 'Period 3'
        ])
        # Set horizontal header to stretch last section and show scrollbar when needed
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
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
        self.table.itemDoubleClicked.connect(self.show_instrument_details)
        layout.addWidget(self.table)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Create buttons with fixed width
        add_button = QPushButton('Add Instrument')
        refresh_button = QPushButton('Refresh')
        back_button = QPushButton('Back to Main Menu')

        # Set fixed width for buttons (1/4 of parent width)
        button_width = self.width() // 4
        add_button.setFixedWidth(button_width)
        refresh_button.setFixedWidth(button_width)
        back_button.setFixedWidth(button_width)

        add_button.clicked.connect(self.show_add_instrument)
        refresh_button.clicked.connect(self.load_instruments)
        back_button.clicked.connect(self.back_signal.emit)

        bottom_layout.addStretch()
        bottom_layout.addWidget(add_button)
        bottom_layout.addWidget(refresh_button)
        bottom_layout.addWidget(back_button)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update button widths when window is resized
        button_width = self.width() // 4
        for button in self.findChildren(QPushButton):
            button.setFixedWidth(button_width)

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
                SELECT i.*, u.username as responsible_username,
                       mt1.name as maintenance_type_1,
                       mt2.name as maintenance_type_2,
                       mt3.name as maintenance_type_3,
                       md1.last_date as last_maintenance_1,
                       md2.last_date as last_maintenance_2,
                       md3.last_date as last_maintenance_3,
                       CASE 
                           WHEN i.maintenance_1 IS NOT NULL AND i.period_1 IS NOT NULL THEN
                               CASE 
                                   WHEN md1.last_date IS NULL THEN
                                       date(i.date_start_operating)
                                   ELSE
                                       date(md1.last_date, '+' || (i.period_1 * 7) || ' days')
                               END
                           ELSE NULL
                       END as next_maintenance_1,
                       CASE 
                           WHEN i.maintenance_2 IS NOT NULL AND i.period_2 IS NOT NULL THEN
                               CASE 
                                   WHEN md2.last_date IS NULL THEN
                                       date(i.date_start_operating)
                                   ELSE
                                       date(md2.last_date, '+' || (i.period_2 * 7) || ' days')
                               END
                           ELSE NULL
                       END as next_maintenance_2,
                       CASE 
                           WHEN i.maintenance_3 IS NOT NULL AND i.period_3 IS NOT NULL THEN
                               CASE 
                                   WHEN md3.last_date IS NULL THEN
                                       date(i.date_start_operating)
                                   ELSE
                                       date(md3.last_date, '+' || (i.period_3 * 7) || ' days')
                               END
                           ELSE NULL
                       END as next_maintenance_3
                FROM instruments i
                LEFT JOIN users u ON i.responsible_user_id = u.id
                LEFT JOIN maintenance_types mt1 ON i.maintenance_1 = mt1.id
                LEFT JOIN maintenance_types mt2 ON i.maintenance_2 = mt2.id
                LEFT JOIN maintenance_types mt3 ON i.maintenance_3 = mt3.id
                LEFT JOIN maintenance_dates md1 ON i.id = md1.instrument_id AND i.maintenance_1 = md1.maintenance_type_id
                LEFT JOIN maintenance_dates md2 ON i.id = md2.instrument_id AND i.maintenance_2 = md2.maintenance_type_id
                LEFT JOIN maintenance_dates md3 ON i.id = md3.instrument_id AND i.maintenance_3 = md3.maintenance_type_id
                ORDER BY i.name
            """)
            instruments = cursor.fetchall()

            self.table.setRowCount(len(instruments))
            for i, instrument in enumerate(instruments):
                # Calculate the earliest next maintenance date
                next_maintenance_dates = [
                    instrument['next_maintenance_1'],
                    instrument['next_maintenance_2'],
                    instrument['next_maintenance_3']
                ]
                next_maintenance_dates = [d for d in next_maintenance_dates if d is not None]
                next_maintenance = min(next_maintenance_dates) if next_maintenance_dates else None

                for col, value in enumerate([
                    instrument['name'],
                    instrument['model'],
                    instrument['serial_number'],
                    instrument['location'],
                    instrument['brand'],
                    instrument['status'],
                    instrument['responsible_username'] or 'Not assigned',
                    str(instrument['last_maintenance_1'] or 'Never'),
                    str(instrument['last_maintenance_2'] or 'Never'),
                    str(instrument['last_maintenance_3'] or 'Never'),
                    str(next_maintenance or 'Not scheduled'),
                    instrument['maintenance_type_1'] or '',
                    str(instrument['period_1']) if instrument['period_1'] else '',
                    instrument['maintenance_type_2'] or '',
                    str(instrument['period_2']) if instrument['period_2'] else '',
                    instrument['maintenance_type_3'] or '',
                    str(instrument['period_3']) if instrument['period_3'] else ''
                ]):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, col, item)

        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load instruments: {str(e)}')

    def show_add_instrument(self):
        dialog = AddInstrumentDialog(self)
        dialog.finished.connect(self.load_instruments)  # Connect to finished signal to refresh list
        dialog.show()  # Changed from exec() to show()

    def show_instrument_details(self, item):
        row = item.row()
        instrument_id = self.get_instrument_id_from_row(row)
        if instrument_id:
            dialog = InstrumentDetailsDialog(instrument_id, self)
            dialog.show()  # Changed from exec() to show()

    def get_instrument_id_from_row(self, row):
        try:
            cursor = self.db.conn.cursor()
            name = self.table.item(row, 0).text()
            serial = self.table.item(row, 2).text()
            cursor.execute("SELECT id FROM instruments WHERE name = ? AND serial_number = ?", (name, serial))
            result = cursor.fetchone()
            return result['id'] if result else None
        except Exception:
            return None

class CentralWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user_id = None
        self.current_is_admin = False
        self.db = Database()  # Create a single database connection
        self.init_ui()
        self.apply_dark_theme()
        self.showMaximized()  # Start in full screen

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
            current_widget.setMinimumSize(self.size())
            current_widget.resize(self.size())

    def moveEvent(self, event):
        """Handle window move events"""
        super().moveEvent(event)
        # Update size of current widget when window is moved
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.setMinimumSize(self.size())
            current_widget.resize(self.size()) 