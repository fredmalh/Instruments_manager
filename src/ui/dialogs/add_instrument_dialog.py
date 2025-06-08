from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDateEdit, QSpinBox, QDialog)
from PyQt6.QtCore import QDate
from ..base.base_dialog import BaseDialog
from datetime import datetime

class AddInstrumentDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add New Instrument')
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        # Create form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Create input fields
        self.name_input = QLineEdit()
        self.model_input = QLineEdit()
        self.serial_number_input = QLineEdit()
        self.location_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(['Active', 'Inactive', 'Under Maintenance'])
        self.brand_input = QLineEdit()
        self.responsible_user_input = QComboBox()
        self.date_start_input = QDateEdit()
        self.date_start_input.setDate(QDate.currentDate())
        self.date_start_input.setCalendarPopup(True)

        # Add fields to form
        form_layout.addRow('Name:', self.name_input)
        form_layout.addRow('Model:', self.model_input)
        form_layout.addRow('Serial Number:', self.serial_number_input)
        form_layout.addRow('Location:', self.location_input)
        form_layout.addRow('Status:', self.status_input)
        form_layout.addRow('Brand:', self.brand_input)
        form_layout.addRow('Responsible User:', self.responsible_user_input)
        form_layout.addRow('Start Operating Date:', self.date_start_input)

        # Load users into combo box
        self.load_users()

        # Create main layout
        main_layout = self.layout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(self.create_button_layout())

    def load_users(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            
            self.responsible_user_input.clear()
            self.responsible_user_input.addItem('Not assigned', None)
            
            for user in users:
                self.responsible_user_input.addItem(user['username'], user['id'])
                
        except Exception as e:
            self.show_error('Error', f'Failed to load users: {str(e)}')

    def accept(self):
        # Validate required fields
        required_fields = [
            (self.name_input, 'Name'),
            (self.model_input, 'Model'),
            (self.serial_number_input, 'Serial Number'),
            (self.location_input, 'Location'),
            (self.brand_input, 'Brand')
        ]
        
        if not self.validate_required_fields([f.text() for f, _ in required_fields], 
                                          [n for _, n in required_fields]):
            return

        try:
            cursor = self.db.conn.cursor()
            
            # Insert new instrument
            cursor.execute("""
                INSERT INTO instruments (
                    name, model, serial_number, location, status,
                    brand, responsible_user_id, date_start_operating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.name_input.text(),
                self.model_input.text(),
                self.serial_number_input.text(),
                self.location_input.text(),
                self.status_input.currentText(),
                self.brand_input.text(),
                self.responsible_user_input.currentData(),
                self.date_start_input.date().toPyDate()
            ))
            
            self.db.conn.commit()
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to add instrument: {str(e)}') 