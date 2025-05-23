from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox,
                            QTextEdit, QSplitter, QHeaderView, QTableView, QScrollArea,
                            QMainWindow, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont
from database import Database
from datetime import datetime

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
            SELECT 
                i.name,
                i.model,
                i.serial_number,
                i.location,
                i.status,
                i.manufacturer,
                i.purchase_date,
                i.last_calibration,
                i.next_calibration,
                i.notes,
                u.username as responsible_user
            FROM instruments i
            LEFT JOIN users u ON i.responsible_user_id = u.id
            WHERE i.id = ?
        """, (self.instrument_id,))
        details = cursor.fetchone()

        if not details:
            QMessageBox.critical(self, 'Error', 'Could not load instrument details')
            self.close()
            return

        # Title
        title = QLabel(f"Instrument Details: {details[0]}")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create splitter for details and history
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Details section
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        
        # Add all details with proper labels
        details_layout.addRow('Name:', QLabel(details[0]))
        details_layout.addRow('Model:', QLabel(details[1]))
        details_layout.addRow('Serial Number:', QLabel(details[2]))
        details_layout.addRow('Location:', QLabel(details[3]))
        details_layout.addRow('Status:', QLabel(details[4]))
        details_layout.addRow('Manufacturer:', QLabel(details[5]))
        details_layout.addRow('Purchase Date:', QLabel(details[6]))
        details_layout.addRow('Last Calibration:', QLabel(details[7]))
        details_layout.addRow('Next Calibration:', QLabel(details[8]))
        details_layout.addRow('Notes:', QLabel(details[9]))
        details_layout.addRow('Responsible User:', QLabel(details[10]))

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
                u.username as performed_by,
                mr.notes
            FROM maintenance_records mr
            JOIN users u ON mr.performed_by = u.id
            WHERE mr.instrument_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (self.instrument_id,))
        history = cursor.fetchall()

        history_table = QTableWidget()
        history_table.setColumnCount(3)
        history_table.setHorizontalHeaderLabels(['Date', 'Performed By', 'Notes'])
        history_table.setRowCount(len(history))

        for row, record in enumerate(history):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                history_table.setItem(row, col, item)

        history_table.resizeColumnsToContents()
        history_layout.addWidget(history_table)
        splitter.addWidget(history_widget)

        # Set initial splitter sizes
        splitter.setSizes([300, 300])

        # Buttons
        button_layout = QHBoxLayout()
        
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

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
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
        self.table.horizontalHeader().setStretchLastSection(False)  # Disable stretch on last section
        
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
        cursor = self.db.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                i.*, 
                u.username as responsible_user,
                COALESCE(
                    (SELECT MAX(maintenance_date)
                     FROM maintenance_records mr
                     WHERE mr.instrument_id = i.id),
                    ?
                ) as last_maintenance,
                (
                    SELECT MIN(
                        CASE 
                            WHEN r.maintenance_date IS NULL THEN datetime(?, '+' || s.period_days || ' days')
                            ELSE datetime(r.maintenance_date, '+' || s.period_days || ' days')
                        END
                    )
                    FROM instrument_maintenance_schedule s
                    LEFT JOIN (
                        SELECT instrument_id, maintenance_type_id, MAX(maintenance_date) as maintenance_date
                        FROM maintenance_records
                        GROUP BY instrument_id, maintenance_type_id
                    ) r ON s.instrument_id = r.instrument_id AND s.maintenance_type_id = r.maintenance_type_id
                    WHERE s.instrument_id = i.id
                ) as next_maintenance
            FROM instruments i
            LEFT JOIN users u ON i.responsible_user_id = u.id
            ORDER BY i.name
        """, (today, today))
        instruments = cursor.fetchall()

        self.table.setRowCount(len(instruments))
        for row, instrument in enumerate(instruments):
            # Create items for each column
            for col in range(self.table.columnCount()):
                if col == 7:  # Responsible User column
                    value = instrument['responsible_user'] or 'Not assigned'
                elif col == 8:  # Next Maintenance column
                    value = str(instrument['next_maintenance'] or 'Not scheduled')
                else:
                    value = str(instrument[col])
                
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

        # Resize columns to content
        self.table.resizeColumnsToContents()

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
        self.init_ui()  # Reinitialize UI to update buttons
        self.load_instruments()  # Reload instruments 