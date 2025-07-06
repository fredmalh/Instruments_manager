from PyQt6.QtWidgets import (QFormLayout, QLineEdit, QComboBox, 
                             QDateEdit, QTextEdit, QDialog, QPushButton,
                             QVBoxLayout)
from PyQt6.QtCore import QDate
from ..base.base_dialog import BaseDialog
from datetime import datetime
from src.reports import MaintenanceReportGenerator, PDFSaveDialog

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

    def _get_maintenance_data_for_pdf(self, maintenance_id):
        """Get all necessary data for PDF generation"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get maintenance record with related data
            cursor.execute("""
                SELECT 
                    mr.id,
                    mr.maintenance_date,
                    mr.notes,
                    mt.name as maintenance_type,
                    i.name as instrument_name,
                    i.model as instrument_model,
                    i.serial_number,
                    i.location,
                    i.brand,
                    u1.username as performed_by,
                    u2.username as responsible_user
                FROM maintenance_records mr
                JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
                JOIN instruments i ON mr.instrument_id = i.id
                JOIN users u1 ON mr.performed_by = u1.id
                LEFT JOIN users u2 ON i.responsible_user_id = u2.id
                WHERE mr.id = ?
            """, (maintenance_id,))
            
            record = cursor.fetchone()
            
            if record:
                # Calculate next maintenance date (simplified - you might want to enhance this)
                next_maintenance_date = None
                next_maintenance_type = None
                
                # Get next maintenance info from instrument schedule
                cursor.execute("""
                    SELECT 
                        mt.name as maintenance_type,
                        CASE
                            WHEN i.maintenance_1 = mt.id THEN i.period_1
                            WHEN i.maintenance_2 = mt.id THEN i.period_2
                            WHEN i.maintenance_3 = mt.id THEN i.period_3
                            ELSE NULL
                        END as period_days
                    FROM instruments i
                    JOIN maintenance_types mt ON (
                        mt.id = i.maintenance_1 OR 
                        mt.id = i.maintenance_2 OR 
                        mt.id = i.maintenance_3
                    )
                    WHERE i.id = ?
                    ORDER BY period_days ASC
                    LIMIT 1
                """, (self.instrument_id,))
                
                next_maintenance = cursor.fetchone()
                if next_maintenance and next_maintenance['period_days']:
                    from datetime import timedelta
                    maintenance_date = datetime.strptime(record['maintenance_date'], '%Y-%m-%d')
                    next_date = maintenance_date + timedelta(days=next_maintenance['period_days'])
                    next_maintenance_date = next_date.strftime('%Y-%m-%d')
                    next_maintenance_type = next_maintenance['maintenance_type']
                
                return {
                    'maintenance_date': record['maintenance_date'],
                    'report_number': f"MR-{record['id']:06d}",
                    'performed_by': record['performed_by'],
                    'instrument_name': record['instrument_name'],
                    'instrument_model': record['instrument_model'],
                    'serial_number': record['serial_number'],
                    'location': record['location'],
                    'brand': record['brand'],
                    'responsible_user': record['responsible_user'] or 'Not assigned',
                    'maintenance_type': record['maintenance_type'],
                    'notes': record['notes'],
                    'next_maintenance_date': next_maintenance_date,
                    'next_maintenance_type': next_maintenance_type
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting maintenance data for PDF: {e}")
            return None

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
            
            # Get the ID of the newly created maintenance record
            maintenance_id = cursor.lastrowid
            
            self.db.conn.commit()
            
            # Generate PDF report
            self._generate_pdf_report(maintenance_id)
            
            super().accept()
            
        except Exception as e:
            self.show_error('Error', f'Failed to add maintenance record: {str(e)}')

    def _generate_pdf_report(self, maintenance_id):
        """Generate PDF report for the maintenance record"""
        try:
            # Get maintenance data for PDF
            maintenance_data = self._get_maintenance_data_for_pdf(maintenance_id)
            
            if not maintenance_data:
                self.show_error('Error', 'Failed to get maintenance data for PDF generation')
                return
            
            # Create PDF generator
            generator = MaintenanceReportGenerator()
            
            # Generate default filename
            default_filename = generator._generate_default_filename(maintenance_data)
            
            # Show save dialog
            save_path = PDFSaveDialog.get_save_path(self, default_filename)
            
            if save_path:
                # Generate PDF
                pdf_path = generator.generate_maintenance_report(maintenance_data, save_path)
                
                if pdf_path:
                    # Show success message
                    PDFSaveDialog.show_success_message(self, pdf_path)
                    
                    # Open the PDF
                    generator.open_pdf(pdf_path)
                else:
                    PDFSaveDialog.show_error_message(self, "Failed to generate PDF file")
            else:
                # User cancelled save dialog
                print("PDF generation cancelled by user")
                
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            PDFSaveDialog.show_error_message(self, str(e)) 