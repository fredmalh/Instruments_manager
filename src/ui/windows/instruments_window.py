from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from ..base.base_main_window import BaseMainWindow
from ..base.base_table import BaseTable
from database import Database
from datetime import datetime
from date_utils import format_date_for_display, get_maintenance_status
from ..dialogs.instrument_details_dialog import InstrumentDetailsDialog

class InstrumentsWindow(BaseMainWindow):
    back_signal = pyqtSignal()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Instrument Management')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'ID', 'Name', 'Model', 'Serial Number', 'Location',
            'Status', 'Last Calibration', 'Next Calibration'
        ])
        self.table.row_double_clicked.connect(self.show_instrument_details)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
            {
                'text': 'Add Instrument',
                'callback': self.add_instrument,
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
                SELECT 
                    i.id,
                    i.name,
                    i.model,
                    i.serial_number,
                    i.location,
                    i.status,
                    i.last_calibration,
                    CASE 
                        WHEN i.calibration_period IS NOT NULL THEN
                            date(i.last_calibration, '+' || (i.calibration_period * 7) || ' days')
                        ELSE NULL
                    END as next_calibration
                FROM instruments i
                ORDER BY i.name
            """)
            
            instruments = cursor.fetchall()
            self.table.clear_table()
            
            for instrument in instruments:
                # Calculate status
                next_calibration = instrument['next_calibration']
                status, color = get_maintenance_status(next_calibration)
                
                # Create row data
                row_data = [
                    instrument['id'],
                    instrument['name'],
                    instrument['model'],
                    instrument['serial_number'],
                    instrument['location'],
                    status,
                    format_date_for_display(instrument['last_calibration']),
                    format_date_for_display(next_calibration)
                ]
                
                # Add row to table
                self.table.add_row(row_data, instrument['id'])
                
                # Highlight row if needed
                if color:
                    self.table.highlight_row(self.table.rowCount() - 1, color)
            
            # Resize columns to content
            self.table.resize_columns_to_content()
            
        except Exception as e:
            self.show_error('Error', f'Failed to load instruments: {str(e)}')

    def show_instrument_details(self, row):
        instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def add_instrument(self):
        dialog = AddInstrumentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data() 