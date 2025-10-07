from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from database import Database
from datetime import datetime
from date_utils import (
    format_date_for_display,
    get_maintenance_status
)
from ..base.base_data_window import BaseDataWindow
from ..base.base_table import BaseTable
from ..dialogs.instrument_details_dialog import InstrumentDetailsDialog

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
            
            # Prepare data with integrated highlighting
            maintenance_data = []
            
            for data in cursor.fetchall():
                # Get maintenance status and color in one call
                status, color = get_maintenance_status(data['next_maintenance'])
                
                # Format dates once
                last_maintenance_display = format_date_for_display(data['last_maintenance'])
                next_maintenance_display = format_date_for_display(data['next_maintenance'])
                
                # Create integrated data structure with highlighting
                maintenance_data.append({
                    'id': data['id'],
                    'name': data['name'],
                    'brand': data['brand'],
                    'model': data['model'],
                    'serial_number': data['serial_number'],
                    'location': data['location'],
                    'maintenance_type': data['maintenance_type'],
                    'performed_by': data['performed_by'] or 'Not assigned',
                    'last_maintenance': last_maintenance_display,
                    'next_maintenance': next_maintenance_display,
                    'notes': data['notes'] or '',
                    'highlight_color': color  # Integrated highlighting
                })
            
            # Define column configuration for consistent formatting
            column_configs = [
                {'key': 'name', 'color': '#4a9eff', 'is_clickable': True},  # Instrument name - blue and clickable
                {'key': 'brand'},  # Brand
                {'key': 'model'},  # Model
                {'key': 'serial_number'},  # Serial Number
                {'key': 'location'},  # Location
                {'key': 'maintenance_type'},  # Maintenance Type
                {'key': 'performed_by'},  # Performed By
                {'key': 'last_maintenance'},  # Last Maintenance
                {'key': 'next_maintenance'},  # Next Maintenance
                {'key': 'notes'}  # Notes
            ]
            
            # Use the new helper method to populate the table with integrated highlighting
            self.table.populate_table(maintenance_data, column_configs)
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load maintenance data: {str(e)}') 