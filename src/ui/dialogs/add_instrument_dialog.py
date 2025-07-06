from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDateEdit, QSpinBox, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton)
from PyQt6.QtCore import QDate
from ..base.base_dialog import BaseDialog
from datetime import datetime
from PyQt6.QtWidgets import QApplication

class AddInstrumentDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)  # This will call init_ui() from BaseDialog
        self.setWindowTitle('Add New Instrument')
        self.setMinimumWidth(700)
        
        # Center the dialog on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Make sure dialog is visible and on top
        self.setVisible(True)
        self.raise_()
        self.activateWindow()

    def init_ui(self):
        """Initialize the UI. This is called by BaseDialog.__init__"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)  # Set the layout on the dialog

        # --- General Information Section ---
        general_group = QGroupBox('General Information')
        general_layout = QHBoxLayout()
        general_group.setLayout(general_layout)  # Set the layout on the group box
        
        left_form = QFormLayout()
        right_form = QFormLayout()
        left_form.setSpacing(8)
        right_form.setSpacing(8)

        # Create input fields with explicit initialization
        self.name_input = QLineEdit()
        self.name_input.setObjectName("name_input")
        self.name_input.setText("")  # Explicitly set empty text
        self.name_input.setPlaceholderText("Enter name")
        self.name_input.setMinimumWidth(200)  # Set minimum width
        
        self.model_input = QLineEdit()
        self.model_input.setObjectName("model_input")
        self.model_input.setText("")
        self.model_input.setPlaceholderText("Enter model")
        self.model_input.setMinimumWidth(200)
        
        self.serial_number_input = QLineEdit()
        self.serial_number_input.setObjectName("serial_number_input")
        self.serial_number_input.setText("")
        self.serial_number_input.setPlaceholderText("Enter serial number")
        self.serial_number_input.setMinimumWidth(200)
        
        self.location_input = QLineEdit()
        self.location_input.setObjectName("location_input")
        self.location_input.setText("")
        self.location_input.setPlaceholderText("Enter location")
        self.location_input.setMinimumWidth(200)
        
        self.brand_input = QLineEdit()
        self.brand_input.setObjectName("brand_input")
        self.brand_input.setText("")
        self.brand_input.setPlaceholderText("Enter brand")
        self.brand_input.setMinimumWidth(200)
        
        self.status_input = QComboBox()
        self.status_input.addItems(['Operational', 'Maintenance', 'Out of Service'])
        self.responsible_user_input = QComboBox()
        self.date_start_input = QDateEdit()
        self.date_start_input.setDate(QDate.currentDate())
        self.date_start_input.setCalendarPopup(True)

        # Populate responsible user
        self.load_users()

        # Add fields to form layouts
        left_form.addRow('Name:', self.name_input)
        left_form.addRow('Model:', self.model_input)
        left_form.addRow('Serial Number:', self.serial_number_input)
        left_form.addRow('Location:', self.location_input)
        left_form.addRow('Brand:', self.brand_input)
        right_form.addRow('Status:', self.status_input)
        right_form.addRow('Responsible User:', self.responsible_user_input)
        right_form.addRow('Start Operating Date:', self.date_start_input)

        # Add form layouts to general layout
        general_layout.addLayout(left_form)
        general_layout.addLayout(right_form)

        # --- Maintenance Configuration Section ---
        maintenance_group = QGroupBox('Maintenance Configuration')
        maintenance_form = QFormLayout()
        maintenance_group.setLayout(maintenance_form)  # Set the layout on the group box
        
        self.maintenance_type1 = QComboBox()
        self.maintenance_type2 = QComboBox()
        self.maintenance_type3 = QComboBox()
        self.period1_input = QLineEdit()
        self.period2_input = QLineEdit()
        self.period3_input = QLineEdit()
        self.load_maintenance_types()
        maintenance_form.addRow('Maintenance Type 1:', self.maintenance_type1)
        maintenance_form.addRow('Period 1 (weeks):', self.period1_input)
        maintenance_form.addRow('Maintenance Type 2:', self.maintenance_type2)
        maintenance_form.addRow('Period 2 (weeks):', self.period2_input)
        maintenance_form.addRow('Maintenance Type 3:', self.maintenance_type3)
        maintenance_form.addRow('Period 3 (weeks):', self.period3_input)

        # --- Place both sections side by side ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        top_layout.addWidget(general_group, 3)
        top_layout.addWidget(maintenance_group, 2)
        main_layout.addLayout(top_layout)

        # Create buttons with custom handler
        button_layout = self.create_button_layout()
        save_button = button_layout.itemAt(0).widget()
        save_button.clicked.disconnect()  # Disconnect default handler
        save_button.clicked.connect(self.handle_save)  # Connect to our handler
        
        main_layout.addLayout(button_layout)

        # Force layout update
        self.updateGeometry()
        self.adjustSize()

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Center the dialog on screen after it's shown
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def handle_save(self):
        """Handle save button click"""
        self.accept()

    def accept(self):
        # Get field values
        name_text = self.name_input.text()
        model_text = self.model_input.text()
        serial_text = self.serial_number_input.text()
        location_text = self.location_input.text()
        brand_text = self.brand_input.text()

        # Validate required fields
        required_fields = [
            (name_text.strip(), 'Name'),
            (model_text.strip(), 'Model'),
            (serial_text.strip(), 'Serial Number'),
            (location_text.strip(), 'Location'),
            (brand_text.strip(), 'Brand')
        ]
        
        field_values = [f for f, _ in required_fields]
        field_names = [n for _, n in required_fields]

        if not self.validate_required_fields(field_values, field_names):
            return

        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO instruments (
                    name, model, serial_number, location, status,
                    brand, responsible_user_id, date_start_operating,
                    maintenance_1, period_1, maintenance_2, period_2, maintenance_3, period_3
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name_text,
                model_text,
                serial_text,
                location_text,
                self.status_input.currentText(),
                brand_text,
                self.responsible_user_input.currentData(),
                self.date_start_input.date().toPyDate(),
                self.maintenance_type1.currentData(),
                self.period1_input.text() or None,
                self.maintenance_type2.currentData(),
                self.period2_input.text() or None,
                self.maintenance_type3.currentData(),
                self.period3_input.text() or None
            ))
            self.db.conn.commit()
            super().accept()
        except Exception as e:
            self.show_error('Error', str(e))

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

    def load_maintenance_types(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, name FROM maintenance_types ORDER BY name")
            types = cursor.fetchall()
            for combo in [self.maintenance_type1, self.maintenance_type2, self.maintenance_type3]:
                combo.clear()
                combo.addItem('None', None)
                for t in types:
                    combo.addItem(t['name'], t['id'])
        except Exception as e:
            self.show_error('Error', f'Failed to load maintenance types: {str(e)}') 