from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox,
                            QTextEdit, QSplitter, QHeaderView, QSizePolicy, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
from database import Database
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
import sys

class MaintenanceDetailsDialog(QDialog):
    def __init__(self, maintenance_id, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Maintenance Details')
        self.setGeometry(100, 100, 800, 600)

        # Get maintenance details
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT 
                i.name as instrument_name,
                mt.name as maintenance_type,
                CASE 
                    WHEN i.maintenance_1 = mt.id THEN i.period_1
                    WHEN i.maintenance_2 = mt.id THEN i.period_2
                    WHEN i.maintenance_3 = mt.id THEN i.period_3
                END as period_days,
                COALESCE(
                    (SELECT MAX(maintenance_date)
                     FROM maintenance_records mr
                     WHERE mr.instrument_id = i.id
                     AND mr.maintenance_type_id = mt.id),
                    'Never'
                ) as last_maintenance,
                CASE
                    WHEN COALESCE(
                        (SELECT MAX(maintenance_date)
                         FROM maintenance_records mr
                         WHERE mr.instrument_id = i.id
                         AND mr.maintenance_type_id = mt.id),
                        '2000-01-01'
                    ) = 'Never' THEN
                        DATE('now')
                    ELSE
                        DATE(
                            (SELECT MAX(maintenance_date)
                             FROM maintenance_records mr
                             WHERE mr.instrument_id = i.id
                             AND mr.maintenance_type_id = mt.id),
                            '+' || (CASE 
                                WHEN i.maintenance_1 = mt.id THEN i.period_1
                                WHEN i.maintenance_2 = mt.id THEN i.period_2
                                WHEN i.maintenance_3 = mt.id THEN i.period_3
                            END * 7) || ' days'
                        )
                END as next_maintenance,
                u.username as responsible_user
            FROM instruments i
            JOIN maintenance_types mt ON mt.id = ?
            LEFT JOIN users u ON i.responsible_user_id = u.id
            WHERE i.id = ?
        """, (self.maintenance_id, self.maintenance_id))
        details = cursor.fetchone()

        if not details:
            QMessageBox.critical(self, 'Error', 'Could not load maintenance details')
            self.reject()
            return

        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"Maintenance Details: {details[0]} - {details[1]}")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create splitter for details and history
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Details section
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        
        details_layout.addRow('Instrument:', QLabel(details[0]))
        details_layout.addRow('Maintenance Type:', QLabel(details[1]))
        details_layout.addRow('Period (days):', QLabel(str(details[2])))
        details_layout.addRow('Last Maintenance:', QLabel(str(details[3])))
        details_layout.addRow('Next Maintenance:', QLabel(str(details[4])))
        details_layout.addRow('Responsible User:', QLabel(details[5]))

        splitter.addWidget(details_widget)

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
            AND mr.maintenance_type_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (self.maintenance_id, self.maintenance_id))
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

        # Buttons
        button_layout = QHBoxLayout()
        
        add_maintenance_button = QPushButton('Add Maintenance Record')
        add_maintenance_button.clicked.connect(self.add_maintenance)
        button_layout.addWidget(add_maintenance_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.maintenance_id, self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()  # Close details dialog to refresh data

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

        self.notes_input = QTextEdit()

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
        notes = self.notes_input.toPlainText()

        if not notes:
            QMessageBox.warning(self, 'Error', 'Please enter maintenance notes')
            return

        try:
            self.db.add_maintenance_record(
                self.instrument_id,
                self.maintenance_id,
                self.user_id,
                notes
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

class MaintenanceWindow(QMainWindow):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_maintenance_data()

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
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('Maintenance Operations')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)  # Adjusted to match our data
        self.table.setHorizontalHeaderLabels([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Maintenance Type', 'Performed By', 'Last Maintenance', 
            'Next Maintenance', 'Notes'
        ])
        self.table.doubleClicked.connect(self.show_maintenance_details)
        
        # Configure table for better scrolling and auto-resize
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Create buttons with fixed width
        if self.is_admin:
            self.add_button = QPushButton('Add Maintenance Record')
            self.add_button.clicked.connect(self.add_maintenance_record)
            self.add_button.setFixedWidth(200)

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.load_maintenance_data)
        refresh_button.setFixedWidth(200)

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(200)

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
        # Update button widths when window is resized
        button_width = self.width() // 4
        for button in self.findChildren(QPushButton):
            button.setFixedWidth(button_width)

    def load_maintenance_data(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id,
                    i.name,
                    i.brand,
                    i.model,
                    i.serial_number,
                    i.location,
                    mt.name as maintenance_type,
                    u.username as performed_by,
                    (SELECT MAX(maintenance_date) 
                     FROM maintenance_records 
                     WHERE instrument_id = i.id AND maintenance_type_id = mt.id) as last_maintenance,
                    (SELECT notes 
                     FROM maintenance_records 
                     WHERE instrument_id = i.id AND maintenance_type_id = mt.id 
                     ORDER BY maintenance_date DESC LIMIT 1) as notes,
                    CASE 
                        WHEN i.maintenance_1 = mt.id THEN i.period_1
                        WHEN i.maintenance_2 = mt.id THEN i.period_2
                        WHEN i.maintenance_3 = mt.id THEN i.period_3
                    END as period_weeks,
                    i.date_start_operating
                FROM instruments i
                JOIN maintenance_types mt ON mt.id IN (i.maintenance_1, i.maintenance_2, i.maintenance_3)
                LEFT JOIN users u ON i.responsible_user_id = u.id
                WHERE i.status = 'Operational'
                ORDER BY i.name, mt.name
            """)
            
            self.table.setRowCount(0)
            for row, data in enumerate(cursor.fetchall()):
                self.table.insertRow(row)
                
                # Calculate next maintenance date using our utility function
                next_maintenance = calculate_next_maintenance(
                    data['last_maintenance'],
                    data['period_weeks'],
                    data['date_start_operating']
                )
                
                # Get maintenance status using our utility function
                status, color = get_maintenance_status(next_maintenance)
                
                # Format dates for display
                last_maintenance_display = format_date_for_display(data['last_maintenance'])
                next_maintenance_display = format_date_for_display(next_maintenance)
                
                # Add data to table
                self.table.setItem(row, 0, QTableWidgetItem(str(data['name'])))
                self.table.setItem(row, 1, QTableWidgetItem(str(data['brand'])))
                self.table.setItem(row, 2, QTableWidgetItem(str(data['model'])))
                self.table.setItem(row, 3, QTableWidgetItem(str(data['serial_number'])))
                self.table.setItem(row, 4, QTableWidgetItem(str(data['location'])))
                self.table.setItem(row, 5, QTableWidgetItem(str(data['maintenance_type'])))
                self.table.setItem(row, 6, QTableWidgetItem(str(data['performed_by'] or 'Not assigned')))
                self.table.setItem(row, 7, QTableWidgetItem(last_maintenance_display))
                self.table.setItem(row, 8, QTableWidgetItem(next_maintenance_display))
                self.table.setItem(row, 9, QTableWidgetItem(str(data['notes'] or '')))
                
                # Store instrument_id in the first column for later use
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, data['id'])
                
                # Set row color based on maintenance status
                if color:
                    for col in range(self.table.columnCount()):
                        self.table.item(row, col).setBackground(QColor(color))
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load maintenance data: {str(e)}')

    def show_maintenance_details(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            try:
                # Get the instrument name and maintenance type
                instrument_name = self.table.item(selected_row, 0).text()
                maintenance_type = self.table.item(selected_row, 5).text()
                
                # Get the instrument_id and maintenance_type_id from the database
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    SELECT i.id as instrument_id, mt.id as maintenance_type_id
                    FROM instruments i
                    JOIN maintenance_types mt ON mt.name = ?
                    WHERE i.name = ?
                """, (maintenance_type, instrument_name))
                result = cursor.fetchone()
                
                if result:
                    dialog = MaintenanceDetailsDialog(result['maintenance_type_id'], self.user_id, self.is_admin, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        self.load_maintenance_data()
                else:
                    QMessageBox.warning(self, 'Error', 'Could not find maintenance details')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to show maintenance details: {str(e)}')

    def add_maintenance_record(self):
        try:
            selected_row = self.table.currentRow()
            if selected_row < 0:
                QMessageBox.warning(self, 'Warning', 'Please select an instrument first')
                return
                
            instrument_id = self.table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
            maintenance_type = self.table.item(selected_row, 5).text()
            
            dialog = MaintenanceRecordDialog(self.db, instrument_id, maintenance_type)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_maintenance_data()
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add maintenance record: {str(e)}')

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        
        # Update buttons visibility
        if hasattr(self, 'add_button'):
            self.add_button.setVisible(self.is_admin)
        
        # Reload data
        self.load_maintenance_data()

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        self.load_maintenance_data()  # Refresh data when window is shown

class MaintenanceRecordDialog(QDialog):
    def __init__(self, db, instrument_id, maintenance_type):
        super().__init__()
        self.db = db
        self.instrument_id = instrument_id
        self.maintenance_type = maintenance_type
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Add Maintenance Record')
        layout = QFormLayout()
        
        # ... existing code ...
        
    def accept(self):
        try:
            cursor = self.db.conn.cursor()
            
            # Get maintenance type ID
            cursor.execute("SELECT id FROM maintenance_types WHERE name = ?", (self.maintenance_type,))
            maintenance_type_id = cursor.fetchone()['id']
            
            # Format date for database storage
            maintenance_date = format_date_for_db(self.date_edit.date().toString('dd-MM-yyyy'))
            
            cursor.execute("""
                INSERT INTO maintenance_records (instrument_id, maintenance_type_id, performed_by, maintenance_date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (self.instrument_id, maintenance_type_id, self.performed_by.currentData(), 
                  maintenance_date, self.notes.toPlainText()))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add maintenance record: {str(e)}') 