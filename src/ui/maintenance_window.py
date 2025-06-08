from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                            QDialog, QLineEdit, QFormLayout, QComboBox, QTextEdit,
                            QSplitter, QHeaderView, QTableView, QScrollArea,
                            QMainWindow, QSizePolicy, QDateEdit, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from .dialogs.add_maintenance_dialog import AddMaintenanceDialog
from .base.base_table import BaseTable

class MaintenanceWindow(QWidget):
    def __init__(self, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('Maintenance Records')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'Instrument', 'Maintenance Type', 'Last Maintenance',
            'Next Maintenance', 'Status', 'Responsible User'
        ])
        self.table.row_double_clicked.connect(self.show_maintenance_details)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
        if self.is_admin:
            add_button = QPushButton('Add Maintenance Record')
            add_button.clicked.connect(self.add_maintenance)
            button_layout.addWidget(add_button)

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)

        # Load initial data
        self.load_data()

    def load_data(self):
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
                    u.username as responsible_user,
                    i.id as instrument_id,
                    mt.id as maintenance_type_id
                FROM instruments i
                JOIN maintenance_types mt ON (
                    mt.id = i.maintenance_1 OR
                    mt.id = i.maintenance_2 OR
                    mt.id = i.maintenance_3
                )
                LEFT JOIN users u ON i.responsible_user_id = u.id
                ORDER BY i.name, mt.name
            """)
            
            records = cursor.fetchall()
            self.table.clear_table()
            
            for record in records:
                # Calculate status
                next_maintenance = record['next_maintenance']
                status, color = get_maintenance_status(next_maintenance)
                
                # Create row data
                row_data = [
                    record['instrument_name'],
                    record['maintenance_type'],
                    format_date_for_display(record['last_maintenance']),
                    format_date_for_display(next_maintenance),
                    status,
                    record['responsible_user'] or 'Not assigned'
                ]
                
                # Add row to table
                self.table.add_row(row_data, (record['instrument_id'], record['maintenance_type_id']))
                
                # Highlight row if needed
                if color:
                    self.table.highlight_row(self.table.rowCount() - 1, color)
            
            # Resize columns to content
            self.table.resize_columns_to_content()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load maintenance records: {str(e)}')

    def show_maintenance_details(self, row):
        instrument_id, maintenance_type_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # Instead of showing a dialog, we'll just show a message for now
        QMessageBox.information(self, 'Maintenance Type Details', 
                              'This feature is not implemented yet.')

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data() 