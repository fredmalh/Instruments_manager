from PyQt6.QtWidgets import (QPushButton, QLabel, QTableWidgetItem, 
                            QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
from database import Database
from datetime import datetime
from ..base.base_data_window import BaseDataWindow
from ..base.base_table import BaseTable
from ..dialogs.instrument_details_dialog import InstrumentDetailsDialog
from ..dialogs.add_instrument_dialog import AddInstrumentDialog

class InstrumentsWindow(BaseDataWindow):
    back_signal = pyqtSignal()

    def __init__(self, user_id, is_admin, db=None):
        super().__init__(user_id, is_admin, db)
        # Track dialog states to prevent multiple openings
        self.add_instrument_dialog_open = False
        self.instrument_details_dialog_open = False
        self.init_ui()

    def init_ui(self):
        super().init_ui()

        # Create title
        self.create_title('Instruments')

        # Create table
        self.table = BaseTable()
        self.table.set_headers([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Status', 'Responsible User'
        ])
        
        # Connect cell click event
        self.table.cellClicked.connect(self.handle_cell_click)
        self.main_layout.addWidget(self.table)

        # Create buttons using standardized layout
        buttons_config = [
            {
                'text': 'Add Instrument',
                'callback': self.add_instrument,
                'position': 'center'
            },
            {
                'text': 'Delete Instrument',
                'callback': self.delete_selected_instrument,
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
                # Prevent multiple dialogs
                if self.instrument_details_dialog_open:
                    return
                
                self.instrument_details_dialog_open = True
                try:
                    dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
                    dialog.show()
                finally:
                    self.instrument_details_dialog_open = False

    def load_data(self):
        """Load instruments data"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    i.id,
                    i.name,           -- Instrument
                    i.brand,          -- Brand
                    i.model,          -- Model
                    i.serial_number,  -- Serial Number
                    i.location,       -- Location
                    i.status,         -- Status
                    u.username as responsible_user  -- Responsible User
                FROM instruments i
                LEFT JOIN users u ON i.responsible_user_id = u.id
                ORDER BY i.name COLLATE NOCASE
            """)
            
            raw_results = cursor.fetchall()
            
            # Prepare data for the new helper method
            instruments_data = []
            for instrument in raw_results:
                instruments_data.append({
                    'id': instrument['id'],
                    'name': instrument['name'],
                    'brand': instrument['brand'],
                    'model': instrument['model'],
                    'serial_number': instrument['serial_number'],
                    'location': instrument['location'],
                    'status': instrument['status'],
                    'responsible_user': instrument['responsible_user'] or 'Not Assigned'
                })
            
            # Define column configuration for consistent formatting
            column_configs = [
                {'key': 'name', 'color': '#4a9eff', 'is_clickable': True},  # Instrument name - blue and clickable
                {'key': 'brand'},  # Brand
                {'key': 'model'},  # Model
                {'key': 'serial_number'},  # Serial Number
                {'key': 'location'},  # Location
                {'key': 'status'},  # Status
                {'key': 'responsible_user'}  # Responsible User
            ]
            
            # Use the new helper method to populate the table
            self.table.populate_table(instruments_data, column_configs)
            
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load instruments: {str(e)}')

    def add_instrument(self):
        # Check admin permission
        if not self.is_admin:
            QMessageBox.warning(self, 'Access Denied', 'Only admin users can add instruments.')
            return
            
        # Prevent multiple dialogs
        if self.add_instrument_dialog_open:
            return
        
        self.add_instrument_dialog_open = True
        try:
            dialog = AddInstrumentDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add instrument: {str(e)}')
        finally:
            self.add_instrument_dialog_open = False

    def delete_selected_instrument(self):
        """Delete the selected instrument"""
        # Check admin permission
        if not self.is_admin:
            QMessageBox.warning(self, 'Access Denied', 'Only admin users can delete instruments.')
            return
            
        # Validate selection using shared method
        if not self.validate_selection_for_delete(self.table, 'instrument'):
            return
            
        try:
            # Get selected row (we know selection exists from validation above)
            selected_items = self.table.selectedItems()
            
            # Get the row index of the first selected item
            row = selected_items[0].row()
            instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            instrument_name = self.table.item(row, 0).text()
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Are you sure you want to delete instrument "{instrument_name}"?\n\n'
                'This action cannot be undone.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor = self.db.conn.cursor()
                cursor.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
                self.db.conn.commit()
                self.load_data()
                QMessageBox.information(self, 'Success', f'Instrument "{instrument_name}" deleted successfully')
                
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to delete instrument: {str(e)}') 