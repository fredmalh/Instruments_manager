from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QDialog, QLineEdit, QComboBox, QTextEdit, QMessageBox,
                            QFormLayout, QGroupBox, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database import Database
from datetime import datetime
from date_utils import format_date_for_display, get_maintenance_status
from ..base.base_main_window import BaseMainWindow
from ..base.base_table import BaseTable

class MaintenanceWindow(BaseMainWindow):
    back_signal = pyqtSignal()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Maintenance Records')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'Instrument', 'Maintenance Type', 'Last Maintenance',
            'Next Maintenance', 'Status', 'Responsible User'
        ])
        self.table.row_double_clicked.connect(self.show_maintenance_details)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
            {
                'text': 'Add Maintenance Record',
                'callback': self.add_maintenance,
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
            self.show_error('Error', f'Failed to load maintenance records: {str(e)}')

    def show_maintenance_details(self, row):
        maintenance_type_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # Instead of showing a dialog, we'll just show a message for now
        QMessageBox.information(self, 'Maintenance Type Details', 
                              'This feature is not implemented yet.')

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data() 