from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QMessageBox, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
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
                    i.name,           -- Instrument
                    i.brand,          -- Brand
                    i.model,          -- Model
                    i.serial_number,  -- Serial Number
                    i.location,       -- Location
                    mt.name as maintenance_type,  -- Maintenance Type
                    u.username as performed_by,   -- Performed By
                    mr.maintenance_date as last_maintenance,  -- Last Maintenance
                    CASE 
                        WHEN i.maintenance_1 IS NOT NULL AND i.period_1 IS NOT NULL THEN
                            CASE 
                                WHEN md1.last_date IS NULL THEN
                                    date(i.date_start_operating)
                                ELSE
                                    date(md1.last_date, '+' || (i.period_1 * 7) || ' days')
                            END
                        ELSE NULL
                    END as next_maintenance,  -- Next Maintenance
                    mr.notes  -- Notes
                FROM instruments i
                LEFT JOIN maintenance_records mr ON i.id = mr.instrument_id
                LEFT JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
                LEFT JOIN users u ON mr.performed_by = u.id
                LEFT JOIN maintenance_dates md1 ON i.id = md1.instrument_id AND i.maintenance_1 = md1.maintenance_type_id
                ORDER BY i.name
            """)
            
            self.table.clear_table()
            
            # Store rows that need highlighting
            rows_to_highlight = []
            
            for record in cursor.fetchall():
                # Get maintenance status using our utility function
                status, color = get_maintenance_status(record['next_maintenance'])
                
                # Add row using BaseTable's add_row method with row_id
                current_row = self.table.rowCount()
                self.table.add_row([
                    record['name'],  # Instrument
                    record['brand'],  # Brand
                    record['model'],  # Model
                    record['serial_number'],  # Serial Number
                    record['location'],  # Location
                    record['maintenance_type'] or 'Not Specified',  # Maintenance Type
                    record['performed_by'] or 'Not Assigned',  # Performed By
                    format_date_for_display(record['last_maintenance']) if record['last_maintenance'] else 'Not Performed',  # Last Maintenance
                    format_date_for_display(record['next_maintenance']) if record['next_maintenance'] else 'Not Scheduled',  # Next Maintenance
                    record['notes'] or ''  # Notes
                ], record['id'])  # Pass the instrument ID as row_id
                
                # Store row for highlighting if needed
                if color:
                    rows_to_highlight.append((current_row, color))
            
            # Apply highlighting after all rows are added
            for row, color in rows_to_highlight:
                self.table.highlight_row(row, color)
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load maintenance data: {str(e)}') 