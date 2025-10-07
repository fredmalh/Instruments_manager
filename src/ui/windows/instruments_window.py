from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
from ..base.base_data_window import BaseDataWindow
from ..base.base_table import BaseTable
from database import Database
from datetime import datetime
from date_utils import format_date_for_display, get_maintenance_status
from ..dialogs.instrument_details_dialog import InstrumentDetailsDialog
from ..dialogs.add_instrument_dialog import AddInstrumentDialog

class InstrumentsWindow(BaseDataWindow):
    back_signal = pyqtSignal()

    def __init__(self, user_id, is_admin, db=None):
        super().__init__(user_id, is_admin, db)
        self.init_ui()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Instruments')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Status', 'Responsible User', 'Next Maintenance'
        ])
        
        # Connect cell click event
        self.table.cellClicked.connect(self.handle_cell_click)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
            {
                'text': 'Add Instrument',
                'callback': self.add_instrument,
                'visible_if_admin': True,
                'position': 'center'
            },
            {
                'text': 'Delete Instrument',
                'callback': self.delete_selected_instrument,
                'visible_if_admin': True,
                'position': 'center'
            },
            {
                'text': 'Refresh',
                'callback': self.load_data,
                'position': 'center'
            },
            {
                'text': 'Back to Main Menu',
                'callback': self.back_signal.emit,
                'position': 'center'
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
        """Load instruments data"""
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
                    i.status,         -- Status
                    u.username as responsible_user,  -- Responsible User
                    CASE 
                        WHEN i.maintenance_1 IS NOT NULL AND i.period_1 IS NOT NULL THEN
                            CASE 
                                WHEN md1.last_date IS NULL THEN
                                    date(i.date_start_operating)
                                ELSE
                                    date(md1.last_date, '+' || (i.period_1 * 7) || ' days')
                            END
                        ELSE NULL
                    END as next_maintenance  -- Next Maintenance
                FROM instruments i
                LEFT JOIN users u ON i.responsible_user_id = u.id
                LEFT JOIN maintenance_dates md1 ON i.id = md1.instrument_id AND i.maintenance_1 = md1.maintenance_type_id
                ORDER BY i.name
            """)
            
            self.table.clear_table()
            
            for instrument in cursor.fetchall():
                # Create items for each column
                items = []
                for col, value in enumerate([
                    instrument['name'],  # Instrument
                    instrument['brand'],  # Brand
                    instrument['model'],  # Model
                    instrument['serial_number'],  # Serial Number
                    instrument['location'],  # Location
                    instrument['status'],  # Status
                    instrument['responsible_user'] or 'Not Assigned',  # Responsible User
                    format_date_for_display(instrument['next_maintenance']) if instrument['next_maintenance'] else 'Not Scheduled'  # Next Maintenance
                ]):
                    item = QTableWidgetItem(str(value))
                    if col == 0:  # First column (Instrument name)
                        item.setForeground(QBrush(QColor("#4a9eff")))  # Light blue color for hyperlink
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make item read-only
                    items.append(item)
                
                # Add row with items
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, item in enumerate(items):
                    self.table.setItem(row, col, item)
                
                # Store the instrument ID in the first column
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, instrument['id'])
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load instruments: {str(e)}')

    def add_instrument(self):
        try:
            dialog = AddInstrumentDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add instrument: {str(e)}')

    def delete_selected_instrument(self):
        """Delete the selected instrument"""
        try:
            # Get selected row
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, 'Warning', 'Please select an instrument to delete')
                return
            
            # Get the row index of the first selected item
            row = selected_items[0].row()
            instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            instrument_name = self.table.item(row, 0).text()
            
            # Check if instrument has maintenance records
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM maintenance_records WHERE instrument_id = ?", (instrument_id,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                QMessageBox.warning(
                    self, 
                    'Cannot Delete Instrument',
                    f'Cannot delete instrument "{instrument_name}" because it has maintenance records.\n\n'
                    'Please delete all maintenance records first, or contact an administrator.'
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Are you sure you want to delete instrument "{instrument_name}"?\n\n'
                'This action cannot be undone.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
                self.db.conn.commit()
                self.load_data()
                QMessageBox.information(self, 'Success', f'Instrument "{instrument_name}" deleted successfully')
                
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to delete instrument: {str(e)}') 