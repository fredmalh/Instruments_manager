from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDateEdit, QTextEdit, QDialog, QPushButton,
                             QVBoxLayout)
from PyQt6.QtCore import QDate
from ..base.base_dialog import BaseDialog
from datetime import datetime

class AddMaintenanceDialog(BaseDialog):
    def __init__(self, instrument_id, user_id, parent=None):
        self.instrument_id = instrument_id
        self.user_id = user_id
        super().__init__(parent)  # This will call init_ui() and set up the layout
        self.setWindowTitle('Add Maintenance Record')
        self.setMinimumWidth(500)

    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Create input fields
        self.maintenance_type_input = QComboBox()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)

        # Add fields to form
        form_layout.addRow('Maintenance Type:', self.maintenance_type_input)
        form_layout.addRow('Date:', self.date_input)
        form_layout.addRow('Notes:', self.notes_input)

        # Load data into combo boxes
        self.load_maintenance_types()

        # Add form layout to main layout
        main_layout.addLayout(form_layout)

        # Create button layout
        button_layout = self.create_button_layout('Save', 'Cancel')
        main_layout.addLayout(button_layout)

    def load_maintenance_types(self):
        try:
            cursor = self.db.conn.cursor()
            # Get maintenance types configured for this instrument
            cursor.execute("""
                SELECT mt.id, mt.name 
                FROM maintenance_types mt
                WHERE mt.id IN (
                    SELECT maintenance_1 FROM instruments WHERE id = ?
                    UNION
                    SELECT maintenance_2 FROM instruments WHERE id = ?
                    UNION
                    SELECT maintenance_3 FROM instruments WHERE id = ?
                )
                ORDER BY mt.name
            """, (self.instrument_id, self.instrument_id, self.instrument_id))
            types = cursor.fetchall()
            
            self.maintenance_type_input.clear()
            for type_ in types:
                self.maintenance_type_input.addItem(type_['name'], type_['id'])
                
        except Exception as e:
            self.show_error('Error', f'Failed to load maintenance types: {str(e)}')

    def accept(self):
        # Validate required fields
        required_fields = [
            (self.maintenance_type_input.currentText(), 'Maintenance Type'),
            (self.notes_input.toPlainText(), 'Notes')
        ]
        
        if not self.validate_required_fields([f for f, _ in required_fields], 
                                          [n for _, n in required_fields]):
            return

        try:
            cursor = self.db.conn.cursor()
            
            # Add maintenance record
            cursor.execute("""
                INSERT INTO maintenance_records (
                    instrument_id, maintenance_type_id, maintenance_date,
                    performed_by, notes
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                self.instrument_id,
                self.maintenance_type_input.currentData(),
                self.date_input.date().toPyDate(),
                self.user_id,
                self.notes_input.toPlainText()
            ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to add maintenance record: {str(e)}') 