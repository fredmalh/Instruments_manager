from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox,
                            QTextEdit, QSplitter, QHeaderView, QTableView, QScrollArea,
                            QMainWindow, QSizePolicy, QDateEdit, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex, QDate
from PyQt6.QtGui import QFont, QColor
from database import Database
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)

class InstrumentDetailsDialog(QMainWindow):
    def __init__(self, instrument_id, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.instrument_id = instrument_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Instrument Details')
        self.setMinimumSize(800, 600)
        
        # Enable window resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWindowState(Qt.WindowState.WindowActive)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Get instrument details
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
                i.*,
                u.username as responsible_user,
                mt1.name as maintenance_type_1,
                mt2.name as maintenance_type_2,
                mt3.name as maintenance_type_3,
                CASE 
                    WHEN md1.last_date IS NULL THEN 'Never'
                    ELSE md1.last_date
                END as last_maintenance_1,
                CASE 
                    WHEN md2.last_date IS NULL THEN 'Never'
                    ELSE md2.last_date
                END as last_maintenance_2,
                CASE 
                    WHEN md3.last_date IS NULL THEN 'Never'
                    ELSE md3.last_date
                END as last_maintenance_3
            FROM instruments i
            LEFT JOIN users u ON i.responsible_user_id = u.id
            LEFT JOIN maintenance_types mt1 ON i.maintenance_1 = mt1.id
            LEFT JOIN maintenance_types mt2 ON i.maintenance_2 = mt2.id
            LEFT JOIN maintenance_types mt3 ON i.maintenance_3 = mt3.id
            LEFT JOIN maintenance_dates md1 ON i.id = md1.instrument_id AND i.maintenance_1 = md1.maintenance_type_id
            LEFT JOIN maintenance_dates md2 ON i.id = md2.instrument_id AND i.maintenance_2 = md2.maintenance_type_id
            LEFT JOIN maintenance_dates md3 ON i.id = md3.instrument_id AND i.maintenance_3 = md3.maintenance_type_id
            WHERE i.id = ?
        """, (self.instrument_id,))
        details = cursor.fetchone()

        if not details:
            QMessageBox.critical(self, 'Error', 'Could not load instrument details')
            self.close()
            return

        # Calculate next maintenance dates using our utility function
        next_maintenance_1 = calculate_next_maintenance(
            details['last_maintenance_1'],
            details['period_1'],
            details['date_start_operating']
        )
        next_maintenance_2 = calculate_next_maintenance(
            details['last_maintenance_2'],
            details['period_2'],
            details['date_start_operating']
        )
        next_maintenance_3 = calculate_next_maintenance(
            details['last_maintenance_3'],
            details['period_3'],
            details['date_start_operating']
        )

        # Get maintenance status for each maintenance type
        status_1, color_1 = get_maintenance_status(next_maintenance_1)
        status_2, color_2 = get_maintenance_status(next_maintenance_2)
        status_3, color_3 = get_maintenance_status(next_maintenance_3)

        # Format dates for display
        last_maintenance_1_display = format_date_for_display(details['last_maintenance_1']) if details['last_maintenance_1'] != 'Never' else 'Never'
        last_maintenance_2_display = format_date_for_display(details['last_maintenance_2']) if details['last_maintenance_2'] != 'Never' else 'Never'
        last_maintenance_3_display = format_date_for_display(details['last_maintenance_3']) if details['last_maintenance_3'] != 'Never' else 'Never'
        next_maintenance_1_display = format_date_for_display(next_maintenance_1) if next_maintenance_1 else 'Not scheduled'
        next_maintenance_2_display = format_date_for_display(next_maintenance_2) if next_maintenance_2 else 'Not scheduled'
        next_maintenance_3_display = format_date_for_display(next_maintenance_3) if next_maintenance_3 else 'Not scheduled'

        # Title
        title = QLabel(f"Instrument Details: {details['name']}")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create splitter for details and history
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Details section
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        
        # Add basic details
        details_layout.addRow('Name:', QLabel(details['name']))
        details_layout.addRow('Model:', QLabel(details['model']))
        details_layout.addRow('Serial Number:', QLabel(details['serial_number']))
        details_layout.addRow('Location:', QLabel(details['location']))
        details_layout.addRow('Status:', QLabel(details['status']))
        details_layout.addRow('Manufacturer:', QLabel(details['manufacturer']))
        details_layout.addRow('Purchase Date:', QLabel(format_date_for_display(details['purchase_date'])))
        details_layout.addRow('Last Calibration:', QLabel(format_date_for_display(details['last_calibration'])))
        details_layout.addRow('Next Calibration:', QLabel(format_date_for_display(details['next_calibration'])))
        details_layout.addRow('Notes:', QLabel(details['notes']))
        details_layout.addRow('Responsible User:', QLabel(details['responsible_user'] or 'Not assigned'))

        # Add maintenance details
        maintenance_group = QGroupBox("Maintenance Schedule")
        maintenance_layout = QFormLayout(maintenance_group)

        # Maintenance Type 1
        if details['maintenance_type_1']:
            maint1_label = QLabel(f"{details['maintenance_type_1']} (Every {details['period_1']} weeks)")
            maint1_label.setStyleSheet(f"color: {color_1};" if color_1 else "")
            maintenance_layout.addRow('Type 1:', maint1_label)
            maintenance_layout.addRow('Last Maintenance:', QLabel(last_maintenance_1_display))
            maintenance_layout.addRow('Next Maintenance:', QLabel(next_maintenance_1_display))

        # Maintenance Type 2
        if details['maintenance_type_2']:
            maint2_label = QLabel(f"{details['maintenance_type_2']} (Every {details['period_2']} weeks)")
            maint2_label.setStyleSheet(f"color: {color_2};" if color_2 else "")
            maintenance_layout.addRow('Type 2:', maint2_label)
            maintenance_layout.addRow('Last Maintenance:', QLabel(last_maintenance_2_display))
            maintenance_layout.addRow('Next Maintenance:', QLabel(next_maintenance_2_display))

        # Maintenance Type 3
        if details['maintenance_type_3']:
            maint3_label = QLabel(f"{details['maintenance_type_3']} (Every {details['period_3']} weeks)")
            maint3_label.setStyleSheet(f"color: {color_3};" if color_3 else "")
            maintenance_layout.addRow('Type 3:', maint3_label)
            maintenance_layout.addRow('Last Maintenance:', QLabel(last_maintenance_3_display))
            maintenance_layout.addRow('Next Maintenance:', QLabel(next_maintenance_3_display))

        details_layout.addRow(maintenance_group)

        # Make the details section scrollable
        details_scroll = QScrollArea()
        details_scroll.setWidget(details_widget)
        details_scroll.setWidgetResizable(True)
        splitter.addWidget(details_scroll)

        # Maintenance history section
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_title = QLabel('Maintenance History')
        history_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        history_layout.addWidget(history_title)

        cursor.execute("""
            SELECT 
                mr.maintenance_date,
                mt.name as maintenance_type,
                u.username as performed_by,
                mr.notes
            FROM maintenance_records mr
            JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            JOIN users u ON mr.performed_by = u.id
            WHERE mr.instrument_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (self.instrument_id,))
        history = cursor.fetchall()

        history_table = QTableWidget()
        history_table.setColumnCount(4)
        history_table.setHorizontalHeaderLabels(['Date', 'Type', 'Performed By', 'Notes'])
        history_table.setRowCount(len(history))

        for row, record in enumerate(history):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:  # Date column
                    item.setText(format_date_for_display(value))
                history_table.setItem(row, col, item)

        history_table.resizeColumnsToContents()
        history_layout.addWidget(history_table)
        splitter.addWidget(history_widget)

        # Set initial splitter sizes
        splitter.setSizes([300, 300])

        # Buttons
        button_layout = QHBoxLayout()
        
        if self.is_admin:
            add_maintenance_button = QPushButton('Add Maintenance Record')
            add_maintenance_button.clicked.connect(self.add_maintenance)
            button_layout.addWidget(add_maintenance_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.instrument_id, self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.close()  # Close details window to refresh data

class AddMaintenanceDialog(QDialog):
    def __init__(self, instrument_id, user_id, parent=None):
        super().__init__(parent)
        self.instrument_id = instrument_id
        self.user_id = user_id
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Maintenance Record')
        self.setFixedSize(400, 300)

        layout = QFormLayout(self)

        # Get available maintenance types for this instrument
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT mt.id, mt.name
            FROM maintenance_types mt
            JOIN instrument_maintenance_schedule ims ON mt.id = ims.maintenance_type_id
            WHERE ims.instrument_id = ?
        """, (self.instrument_id,))
        maintenance_types = cursor.fetchall()

        self.maintenance_type = QComboBox()
        for maint_id, maint_name in maintenance_types:
            self.maintenance_type.addItem(maint_name, maint_id)

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

class InstrumentsTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ['ID', 'Name', 'Model', 'Serial Number', 'Location', 'Status', 'Brand', 'Responsible User']

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            if col == 7:  # Skip the responsible_user_id column
                return str(self._data[row][col + 1])  # Use the username instead
            return str(self._data[row][col])

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def updateData(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def getColumnWidth(self, column, view):
        if not self._data:
            return 100  # Default width if no data

        # Get the header width
        header_width = view.fontMetrics().horizontalAdvance(self._headers[column]) + 20

        # Get the maximum content width
        content_width = 0
        for row in range(len(self._data)):
            value = str(self.data(self.index(row, column), Qt.ItemDataRole.DisplayRole))
            width = view.fontMetrics().horizontalAdvance(value) + 20
            content_width = max(content_width, width)

        return max(header_width, content_width)

class InstrumentsWindow(QWidget):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_instruments()

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
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
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
        self.table.doubleClicked.connect(self.show_instrument_details)
        
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
            self.add_button.clicked.connect(self.add_instrument)
            self.add_button.setFixedWidth(200)
            button_layout.addWidget(self.add_button)

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(200)
        button_layout.addWidget(back_button)

        # Add buttons to layout with proper spacing
        button_layout.addStretch()
        if self.is_admin:
            button_layout.addWidget(self.add_button)
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

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
                       CASE 
                           WHEN md1.last_date IS NULL THEN 'Never'
                           ELSE date(md1.last_date)
                       END as last_maintenance_1,
                       CASE 
                           WHEN md2.last_date IS NULL THEN 'Never'
                           ELSE date(md2.last_date)
                       END as last_maintenance_2,
                       CASE 
                           WHEN md3.last_date IS NULL THEN 'Never'
                           ELSE date(md3.last_date)
                       END as last_maintenance_3,
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

                # Format dates for display
                last_maintenance_1_display = format_date_for_display(instrument['last_maintenance_1']) if instrument['last_maintenance_1'] != 'Never' else 'Never'
                last_maintenance_2_display = format_date_for_display(instrument['last_maintenance_2']) if instrument['last_maintenance_2'] != 'Never' else 'Never'
                last_maintenance_3_display = format_date_for_display(instrument['last_maintenance_3']) if instrument['last_maintenance_3'] != 'Never' else 'Never'
                next_maintenance_display = format_date_for_display(next_maintenance) if next_maintenance else 'Not scheduled'

                # Add data to table - setting each item individually to ensure proper formatting
                self.table.setItem(i, 0, QTableWidgetItem(str(instrument['name'])))
                self.table.setItem(i, 1, QTableWidgetItem(str(instrument['model'])))
                self.table.setItem(i, 2, QTableWidgetItem(str(instrument['serial_number'])))
                self.table.setItem(i, 3, QTableWidgetItem(str(instrument['location'])))
                self.table.setItem(i, 4, QTableWidgetItem(str(instrument['brand'])))
                self.table.setItem(i, 5, QTableWidgetItem(str(instrument['status'])))
                self.table.setItem(i, 6, QTableWidgetItem(str(instrument['responsible_username'] or 'Not assigned')))
                self.table.setItem(i, 7, QTableWidgetItem(last_maintenance_1_display))
                self.table.setItem(i, 8, QTableWidgetItem(last_maintenance_2_display))
                self.table.setItem(i, 9, QTableWidgetItem(last_maintenance_3_display))
                self.table.setItem(i, 10, QTableWidgetItem(next_maintenance_display))
                self.table.setItem(i, 11, QTableWidgetItem(str(instrument['maintenance_type_1'] or '')))
                self.table.setItem(i, 12, QTableWidgetItem(str(instrument['period_1']) if instrument['period_1'] else ''))
                self.table.setItem(i, 13, QTableWidgetItem(str(instrument['maintenance_type_2'] or '')))
                self.table.setItem(i, 14, QTableWidgetItem(str(instrument['period_2']) if instrument['period_2'] else ''))
                self.table.setItem(i, 15, QTableWidgetItem(str(instrument['maintenance_type_3'] or '')))
                self.table.setItem(i, 16, QTableWidgetItem(str(instrument['period_3']) if instrument['period_3'] else ''))

                # Set alignment for all items
                for col in range(self.table.columnCount()):
                    self.table.item(i, col).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                # Set row color based on maintenance status
                if next_maintenance and next_maintenance < datetime.now():
                    for col in range(self.table.columnCount()):
                        self.table.item(i, col).setBackground(QColor('red'))

                # Store instrument_id in the first column for later use
                self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, instrument['id'])

            # Resize columns to content
            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load instruments: {str(e)}')

    def show_instrument_details(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            instrument_id = int(self.table.item(selected_row, 0).text())
            dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
            dialog.show()  # Changed from exec() to show()
            # Note: We don't need to check the result since it's a non-modal window

    def add_instrument(self):
        # TODO: Implement add functionality
        QMessageBox.information(self, 'Coming Soon', 'Add functionality will be implemented soon.')

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        
        # Update buttons visibility
        if hasattr(self, 'add_button'):
            self.add_button.setVisible(self.is_admin)
        
        # Reload data
        self.load_instruments()

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        self.load_instruments()  # Refresh data when window is shown 