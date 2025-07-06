from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox, QMainWindow, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
from database import Database
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from src.ui.dialogs.instrument_details_dialog import InstrumentDetailsDialog
from src.ui.base.base_table import BaseTable
from ..base.base_data_window import BaseDataWindow
import sys

class MaintenanceWindow(BaseDataWindow):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__(user_id, is_admin, db)
        self.init_ui()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Maintenance Operations')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Maintenance Type', 'Performed By', 'Last Maintenance', 
            'Next Maintenance', 'Notes'
        ])
        
        # Connect cell click event
        self.table.cellClicked.connect(self.handle_cell_click)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
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

    def handle_cell_click(self, row, column):
        """Handle cell click events"""
        if column == 0:  # Only handle clicks on the Instrument column
            instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if instrument_id:
                dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
                dialog.show()

    def load_data(self):
        """Load maintenance data"""
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
                    i.id,
                    i.name,
                    i.brand,
                    i.model,
                    i.serial_number,
                    i.location,
                    mt.name as maintenance_type,
                    u.username as performed_by,
                    md.last_date as last_maintenance,
                    CASE 
                        WHEN md.last_date IS NULL THEN
                            date(i.date_start_operating)
                        ELSE
                            date(md.last_date, '+' || (
                                CASE 
                                    WHEN i.maintenance_1 = mt.id THEN i.period_1
                                    WHEN i.maintenance_2 = mt.id THEN i.period_2
                                    WHEN i.maintenance_3 = mt.id THEN i.period_3
                                END * 7
                            ) || ' days')
                    END as next_maintenance,
                    (SELECT notes 
                     FROM maintenance_records 
                     WHERE instrument_id = i.id AND maintenance_type_id = mt.id 
                     ORDER BY maintenance_date DESC LIMIT 1) as notes
                FROM instruments i
                JOIN maintenance_types mt ON mt.id IN (i.maintenance_1, i.maintenance_2, i.maintenance_3)
                LEFT JOIN users u ON i.responsible_user_id = u.id
                LEFT JOIN maintenance_dates md ON i.id = md.instrument_id AND mt.id = md.maintenance_type_id
                WHERE i.status = 'Operational'
                ORDER BY 
                    CASE 
                        WHEN next_maintenance IS NULL THEN 1 
                        ELSE 0 
                    END,
                    next_maintenance ASC,
                    i.name ASC,
                    mt.name ASC
            """)
            
            self.table.setRowCount(0)
            for row, data in enumerate(cursor.fetchall()):
                self.table.insertRow(row)
                
                # Get maintenance status using our utility function
                status, color = get_maintenance_status(data['next_maintenance'])
                
                # Format dates for display
                last_maintenance_display = format_date_for_display(data['last_maintenance'])
                next_maintenance_display = format_date_for_display(data['next_maintenance'])
                
                # Add data to table
                instrument_item = QTableWidgetItem(str(data['name']))
                instrument_item.setForeground(QBrush(QColor("#4a9eff")))  # Light blue color for hyperlink
                instrument_item.setData(Qt.ItemDataRole.UserRole, data['id'])
                self.table.setItem(row, 0, instrument_item)
                
                self.table.setItem(row, 1, QTableWidgetItem(str(data['brand'])))
                self.table.setItem(row, 2, QTableWidgetItem(str(data['model'])))
                self.table.setItem(row, 3, QTableWidgetItem(str(data['serial_number'])))
                self.table.setItem(row, 4, QTableWidgetItem(str(data['location'])))
                self.table.setItem(row, 5, QTableWidgetItem(str(data['maintenance_type'])))
                self.table.setItem(row, 6, QTableWidgetItem(str(data['performed_by'] or 'Not assigned')))
                self.table.setItem(row, 7, QTableWidgetItem(last_maintenance_display))
                self.table.setItem(row, 8, QTableWidgetItem(next_maintenance_display))
                self.table.setItem(row, 9, QTableWidgetItem(str(data['notes'] or '')))
                
                # Apply row highlighting if needed
                if color:
                    self.table.highlight_row(row, color)
                    # Re-apply blue color to instrument name after highlighting
                    self.table.item(row, 0).setForeground(QBrush(QColor("#4a9eff")))
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load maintenance data: {str(e)}') 