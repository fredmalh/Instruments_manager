from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QDialog, QLineEdit, QComboBox, QTextEdit, QMessageBox,
                            QFormLayout, QGroupBox, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from database import Database
from datetime import datetime
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from .add_maintenance_dialog import AddMaintenanceDialog

class InstrumentDetailsDialog(QDialog):
    def __init__(self, instrument_id, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.instrument_id = instrument_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_instrument_data()
        self.set_edit_mode(False)  # Start in read-only mode

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
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
        self.setMinimumSize(1000, 600)  # Reduced height since we're making tables more compact
        
        # Set default font for the dialog and all its children
        default_font = QFont('Arial', 10)
        self.setFont(default_font)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Create horizontal layout for basic info and maintenance config
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        # General Information Group
        basic_group = QGroupBox("General Information")
        basic_group.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        
        # Create horizontal layout for two columns
        basic_columns = QHBoxLayout()
        basic_columns.setSpacing(20)
        
        # Create two form layouts for the columns
        left_column = QFormLayout()
        right_column = QFormLayout()
        left_column.setSpacing(8)
        right_column.setSpacing(8)
        
        # Create input fields
        self.name_input = QLineEdit()
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.location_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Operational', 'Maintenance', 'Out of Service'])
        self.responsible_user = QComboBox()
        self.date_start_input = QLineEdit()
        self.date_start_input.setPlaceholderText("YYYY-MM-DD")

        # Load users into responsible_user dropdown
        self.load_users()

        # Add fields to left column
        left_column.addRow('Name:', self.name_input)
        left_column.addRow('Model:', self.model_input)
        left_column.addRow('Serial Number:', self.serial_input)
        left_column.addRow('Location:', self.location_input)
        left_column.addRow('Brand:', self.brand_input)

        # Add fields to right column
        right_column.addRow('Status:', self.status_input)
        right_column.addRow('Responsible User:', self.responsible_user)
        right_column.addRow('Start Operating Date:', self.date_start_input)

        # Add columns to basic group
        basic_columns.addLayout(left_column)
        basic_columns.addLayout(right_column)
        basic_group.setLayout(basic_columns)
        top_layout.addWidget(basic_group)

        # Maintenance Configuration Group
        maintenance_group = QGroupBox("Maintenance Configuration")
        maintenance_group.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        maintenance_layout = QFormLayout()
        
        # Create maintenance type and period inputs
        self.maintenance_type1 = QComboBox()
        self.maintenance_type2 = QComboBox()
        self.maintenance_type3 = QComboBox()
        self.period1_input = QLineEdit()
        self.period2_input = QLineEdit()
        self.period3_input = QLineEdit()

        # Load maintenance types into dropdowns
        self.load_maintenance_types()

        # Add maintenance fields
        maintenance_layout.addRow('Maintenance Type 1:', self.maintenance_type1)
        maintenance_layout.addRow('Period 1 (weeks):', self.period1_input)
        maintenance_layout.addRow('Maintenance Type 2:', self.maintenance_type2)
        maintenance_layout.addRow('Period 2 (weeks):', self.period2_input)
        maintenance_layout.addRow('Maintenance Type 3:', self.maintenance_type3)
        maintenance_layout.addRow('Period 3 (weeks):', self.period3_input)

        maintenance_group.setLayout(maintenance_layout)
        top_layout.addWidget(maintenance_group)

        # Add top layout to main layout
        layout.addLayout(top_layout)

        # Maintenance Schedule Group
        schedule_group = QGroupBox("Maintenance Schedule")
        schedule_group.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        schedule_layout = QVBoxLayout()

        # Create schedule table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(4)
        self.schedule_table.setHorizontalHeaderLabels(['Type', 'Period (weeks)', 'Last Maintenance', 'Next Maintenance'])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set fixed height for schedule table (3 rows)
        header_height = self.schedule_table.horizontalHeader().height()
        row_height = 35  # Height for each row
        spacing = 2  # Spacing between rows
        padding = 10  # Additional padding
        self.schedule_table.setFixedHeight(header_height + (row_height * 3) + (spacing * 2) + padding)

        schedule_layout.addWidget(self.schedule_table)
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        # Maintenance History Group
        history_group = QGroupBox("Maintenance History")
        history_group.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        history_layout = QVBoxLayout()

        # Create history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(['Date', 'Type', 'Performed By', 'Notes'])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.history_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set fixed height for history table (6 rows)
        header_height = self.history_table.horizontalHeader().height()
        row_height = 35  # Height for each row
        spacing = 2  # Spacing between rows
        padding = 10  # Additional padding
        self.history_table.setFixedHeight(header_height + (row_height * 6) + (spacing * 5) + padding)
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Create edit/save/cancel buttons
        self.edit_button = QPushButton('Edit Data')
        self.save_button = QPushButton('Save Changes')
        self.cancel_button = QPushButton('Cancel')
        
        # Set fixed width for buttons
        button_width = 200
        self.edit_button.setFixedWidth(button_width)
        self.save_button.setFixedWidth(button_width)
        self.cancel_button.setFixedWidth(button_width)
        
        # Connect button signals
        self.edit_button.clicked.connect(lambda: self.set_edit_mode(True))
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button.clicked.connect(lambda: self.set_edit_mode(False))
        
        if self.is_admin:
            add_maintenance_button = QPushButton('Add Maintenance Record')
            add_maintenance_button.setFixedWidth(button_width)
            add_maintenance_button.clicked.connect(self.add_maintenance)
            button_layout.addWidget(add_maintenance_button)

        close_button = QPushButton('Close')
        close_button.setFixedWidth(button_width)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        # Add edit/save/cancel buttons
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

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

        # Set history table edit triggers based on edit mode
        if edit_mode:
            self.history_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        else:
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
                # Validate date is in YYYY-MM-DD format
                datetime.strptime(date_start, '%Y-%m-%d')
            except ValueError:
                QMessageBox.warning(self, 'Error', 'Please enter date in YYYY-MM-DD format')
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

            # Start transaction
            cursor = self.db.conn.cursor()
            
            # Update instrument
            cursor.execute("""
                UPDATE instruments SET
                    name = ?, model = ?, serial_number = ?, location = ?,
                    status = ?, brand = ?, responsible_user_id = ?,
                    date_start_operating = ?, maintenance_1 = ?, period_1 = ?,
                    maintenance_2 = ?, period_2 = ?, maintenance_3 = ?,
                    period_3 = ?
                WHERE id = ?
            """, (
                name, model, serial, location, status, brand,
                responsible_user_id, date_start, maint_type1, period1,
                maint_type2, period2, maint_type3, period3,
                self.instrument_id
            ))

            # Save changes to maintenance history
            for row in range(self.history_table.rowCount()):
                date = self.history_table.item(row, 0).text()
                maint_type = self.history_table.item(row, 1).text()
                performed_by = self.history_table.item(row, 2).text()
                notes = self.history_table.item(row, 3).text()

                # Get maintenance type ID
                cursor.execute("SELECT id FROM maintenance_types WHERE name = ?", (maint_type,))
                maint_type_result = cursor.fetchone()
                if not maint_type_result:
                    continue
                maint_type_id = maint_type_result['id']

                # Get user ID
                cursor.execute("SELECT id FROM users WHERE username = ?", (performed_by,))
                user_result = cursor.fetchone()
                if not user_result:
                    continue
                user_id = user_result['id']

                # Update maintenance record
                cursor.execute("""
                    UPDATE maintenance_records 
                    SET notes = ?, performed_by = ?
                    WHERE instrument_id = ? 
                    AND maintenance_date = ?
                    AND maintenance_type_id = ?
                """, (notes, user_id, self.instrument_id, date, maint_type_id))

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
            
            # Load General Information
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
                        # Validate date is in YYYY-MM-DD format
                        datetime.strptime(instrument['date_start_operating'], '%Y-%m-%d')
                        self.date_start_input.setText(instrument['date_start_operating'])
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

            # Store current column widths
            schedule_widths = [self.schedule_table.columnWidth(i) for i in range(self.schedule_table.columnCount())]
            history_widths = [self.history_table.columnWidth(i) for i in range(self.history_table.columnCount())]

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
                    # Calculate next maintenance date
                    next_maintenance = calculate_next_maintenance(last_maintenance, period)
                    
                    for col, value in enumerate([
                        type_name,
                        str(period),
                        str(last_maintenance or 'Never'),
                        str(next_maintenance or 'N/A')
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
                    format_date_for_display(record['maintenance_date']),
                    record['type_name'],
                    record['performed_by'],
                    record['notes']
                ]):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.history_table.setItem(i, col, item)

            # Restore column widths
            for i, width in enumerate(schedule_widths):
                self.schedule_table.setColumnWidth(i, width)
            for i, width in enumerate(history_widths):
                self.history_table.setColumnWidth(i, width)

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
        try:
            dialog = AddMaintenanceDialog(self.instrument_id, self.user_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_instrument_data()  # Refresh the data
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add maintenance record: {str(e)}')

    def delete_maintenance(self):
        """Delete the selected maintenance record"""
        try:
            # Get selected row
            selected_rows = self.history_table.selectedItems()
            if not selected_rows:
                QMessageBox.warning(self, 'Warning', 'Please select a maintenance record to delete')
                return
            
            # Get the row index of the first selected item
            row = selected_rows[0].row()
            
            # Get the maintenance date and type from the selected row
            date = self.history_table.item(row, 0).text()
            maint_type = self.history_table.item(row, 1).text()
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Are you sure you want to delete the maintenance record?\n\n'
                f'Date: {date}\nType: {maint_type}',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor = self.db.conn.cursor()
                
                # Delete the record
                cursor.execute("""
                    DELETE FROM maintenance_records 
                    WHERE instrument_id = ? 
                    AND maintenance_date = ?
                    AND maintenance_type_id = (
                        SELECT id FROM maintenance_types WHERE name = ?
                    )
                """, (self.instrument_id, date, maint_type))
                
                self.db.conn.commit()
                self.load_instrument_data()  # Refresh the data
                
                QMessageBox.information(self, 'Success', 'Maintenance record deleted successfully')
                
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to delete maintenance record: {str(e)}')

    def load_users(self):
        """Load users into the responsible_user dropdown"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            
            self.responsible_user.clear()
            for user in users:
                self.responsible_user.addItem(user['username'], user['id'])
        except Exception as e:
            self.show_error('Error', f'Failed to load users: {str(e)}')

    def load_maintenance_types(self):
        """Load maintenance types into the maintenance type dropdowns"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, name FROM maintenance_types ORDER BY name")
            types = cursor.fetchall()
            
            # Clear and populate all three dropdowns
            for combo in [self.maintenance_type1, self.maintenance_type2, self.maintenance_type3]:
                combo.clear()
                combo.addItem("", None)  # Add empty option
                for type_ in types:
                    combo.addItem(type_['name'], type_['id'])
        except Exception as e:
            self.show_error('Error', f'Failed to load maintenance types: {str(e)}') 