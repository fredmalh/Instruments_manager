from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox,
                            QTextEdit, QSplitter, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database import Database
from datetime import datetime, timedelta

class MaintenanceDetailsDialog(QDialog):
    def __init__(self, maintenance_id, user_id, is_admin, parent=None):
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Maintenance Details')
        self.setGeometry(100, 100, 800, 600)

        # Get maintenance details
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT 
                i.name as instrument_name,
                mt.name as maintenance_type,
                ims.period_days,
                COALESCE(
                    (SELECT MAX(maintenance_date)
                     FROM maintenance_records mr
                     WHERE mr.instrument_id = i.id
                     AND mr.maintenance_type_id = mt.id),
                    'Never'
                ) as last_maintenance,
                CASE
                    WHEN COALESCE(
                        (SELECT MAX(maintenance_date)
                         FROM maintenance_records mr
                         WHERE mr.instrument_id = i.id
                         AND mr.maintenance_type_id = mt.id),
                        '2000-01-01'
                    ) = 'Never' THEN
                        DATE('now')
                    ELSE
                        DATE(
                            (SELECT MAX(maintenance_date)
                             FROM maintenance_records mr
                             WHERE mr.instrument_id = i.id
                             AND mr.maintenance_type_id = mt.id),
                            '+' || ims.period_days || ' days'
                        )
                END as next_maintenance,
                u.username as responsible_user
            FROM instruments i
            JOIN maintenance_types mt ON mt.id = ?
            JOIN instrument_maintenance_schedule ims ON i.id = ims.instrument_id AND mt.id = ims.maintenance_type_id
            LEFT JOIN users u ON i.responsible_user_id = u.id
            WHERE i.id = ?
        """, (self.maintenance_id, self.maintenance_id))
        details = cursor.fetchone()

        if not details:
            QMessageBox.critical(self, 'Error', 'Could not load maintenance details')
            self.reject()
            return

        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"Maintenance Details: {details[0]} - {details[1]}")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create splitter for details and history
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Details section
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        
        details_layout.addRow('Instrument:', QLabel(details[0]))
        details_layout.addRow('Maintenance Type:', QLabel(details[1]))
        details_layout.addRow('Period (days):', QLabel(str(details[2])))
        details_layout.addRow('Last Maintenance:', QLabel(str(details[3])))
        details_layout.addRow('Next Maintenance:', QLabel(str(details[4])))
        details_layout.addRow('Responsible User:', QLabel(details[5]))

        splitter.addWidget(details_widget)

        # Maintenance history section
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_title = QLabel('Maintenance History')
        history_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        history_layout.addWidget(history_title)

        cursor.execute("""
            SELECT 
                mr.maintenance_date,
                u.username as performed_by,
                mr.notes
            FROM maintenance_records mr
            JOIN users u ON mr.performed_by = u.id
            WHERE mr.instrument_id = ?
            AND mr.maintenance_type_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (self.maintenance_id, self.maintenance_id))
        history = cursor.fetchall()

        history_table = QTableWidget()
        history_table.setColumnCount(3)
        history_table.setHorizontalHeaderLabels(['Date', 'Performed By', 'Notes'])
        history_table.setRowCount(len(history))

        for row, record in enumerate(history):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                history_table.setItem(row, col, item)

        history_table.resizeColumnsToContents()
        history_layout.addWidget(history_table)
        splitter.addWidget(history_widget)

        # Buttons
        button_layout = QHBoxLayout()
        
        add_maintenance_button = QPushButton('Add Maintenance Record')
        add_maintenance_button.clicked.connect(self.add_maintenance)
        button_layout.addWidget(add_maintenance_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def add_maintenance(self):
        dialog = AddMaintenanceDialog(self.maintenance_id, self.user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()  # Close details dialog to refresh data

class AddMaintenanceDialog(QDialog):
    def __init__(self, instrument_id, user_id, parent=None):
        super().__init__(parent)
        self.instrument_id = instrument_id
        self.user_id = user_id
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Maintenance Record')
        self.setFixedSize(400, 300)

        layout = QFormLayout(self)

        self.notes_input = QTextEdit()

        layout.addRow('Notes:', self.notes_input)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')

        save_button.clicked.connect(self.save_maintenance)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

    def save_maintenance(self):
        notes = self.notes_input.toPlainText()

        if not notes:
            QMessageBox.warning(self, 'Error', 'Please enter maintenance notes')
            return

        try:
            self.db.add_maintenance_record(
                self.instrument_id,
                self.maintenance_id,
                self.user_id,
                notes
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

class MaintenanceWindow(QWidget):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_maintenance_schedule()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
            }
            QTableWidget::item {
                padding: 5px;
                margin: 0px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3d3d3d;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('Maintenance Operations')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)  # Increased to 12 columns
        self.table.setHorizontalHeaderLabels([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Maintenance Type', 'Performed By', 'Last Maintenance', 
            'Notes', 'Period (weeks)', 'Next Maintenance', 'Next Maintenance Operation'
        ])
        self.table.doubleClicked.connect(self.show_maintenance_details)
        
        # Configure table for better scrolling and auto-resize
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Create buttons with fixed width
        if self.is_admin:
            self.add_button = QPushButton('Add Maintenance Schedule')
            self.add_button.clicked.connect(self.add_maintenance_schedule)
            self.add_button.setFixedWidth(200)

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.load_maintenance_schedule)
        refresh_button.setFixedWidth(200)

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(200)

        # Add buttons to layout with proper spacing
        bottom_layout.addStretch()
        if self.is_admin:
            bottom_layout.addWidget(self.add_button)
        bottom_layout.addWidget(refresh_button)
        bottom_layout.addWidget(back_button)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update button widths when window is resized
        button_width = self.width() // 4
        for button in self.findChildren(QPushButton):
            button.setFixedWidth(button_width)

    def load_maintenance_schedule(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT 
                    i.id,
                    i.name,
                    i.brand,
                    i.model,
                    i.serial_number,
                    i.location,
                    mt.name as maintenance_type,
                    u.username as performed_by,
                    (SELECT MAX(maintenance_date) 
                     FROM maintenance_records 
                     WHERE instrument_id = i.id AND maintenance_type_id = mt.id) as last_maintenance,
                    (SELECT notes 
                     FROM maintenance_records 
                     WHERE instrument_id = i.id AND maintenance_type_id = mt.id 
                     ORDER BY maintenance_date DESC LIMIT 1) as notes,
                    CASE 
                        WHEN i.maintenance_1 = mt.id THEN i.period_1
                        WHEN i.maintenance_2 = mt.id THEN i.period_2
                        WHEN i.maintenance_3 = mt.id THEN i.period_3
                    END as period_weeks
                FROM instruments i
                JOIN maintenance_types mt ON mt.id IN (i.maintenance_1, i.maintenance_2, i.maintenance_3)
                LEFT JOIN users u ON i.responsible_user_id = u.id
                WHERE i.status = 'Operational'
                ORDER BY i.name, mt.name
            """)
            schedules = cursor.fetchall()

            self.table.setRowCount(len(schedules))
            self.table.setColumnCount(12)
            self.table.setHorizontalHeaderLabels([
                'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
                'Maintenance Type', 'Performed By', 'Last Maintenance', 
                'Notes', 'Period (weeks)', 'Next Maintenance', 'Next Maintenance Operation'
            ])

            for row, schedule in enumerate(schedules):
                # Get the values we need for calculations
                last_maintenance = schedule[8]  # last_maintenance column
                period_weeks = schedule[10]     # period_weeks column
                
                for col, value in enumerate(schedule[1:]):  # Skip the ID column
                    item = QTableWidgetItem(str(value or ''))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    
                    # For the next maintenance column, calculate the date
                    if col == 10:  # Next maintenance column
                        if last_maintenance and period_weeks:
                            try:
                                last_date = datetime.strptime(last_maintenance, '%Y-%m-%d')
                                next_date = last_date + timedelta(weeks=int(period_weeks))
                                next_maintenance = next_date.strftime('%Y-%m-%d')
                                
                                # Color code based on how soon maintenance is due
                                days_until_next = (next_date - datetime.now()).days
                                if days_until_next < 0:
                                    item.setForeground(Qt.GlobalColor.red)  # Overdue
                                elif days_until_next <= 7:
                                    item.setForeground(Qt.GlobalColor.yellow)  # Due within a week
                                else:
                                    item.setForeground(Qt.GlobalColor.green)  # On schedule
                                
                                item.setText(next_maintenance)
                            except (ValueError, TypeError):
                                item.setText('Invalid date')
                        else:
                            item.setText('Not scheduled')
                    
                    # For the next maintenance operation column, show the last maintenance date
                    elif col == 11:  # Next Maintenance Operation column
                        if last_maintenance:
                            item.setText(str(last_maintenance))
                        else:
                            item.setText('Never')
                    
                    self.table.setItem(row, col, item)

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load maintenance schedule: {str(e)}')

    def show_maintenance_details(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            maintenance_id = int(self.table.item(selected_row, 0).text())
            dialog = MaintenanceDetailsDialog(maintenance_id, self.user_id, self.is_admin, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_maintenance_schedule()

    def add_maintenance_schedule(self):
        # TODO: Implement add functionality
        QMessageBox.information(self, 'Coming Soon', 'Add functionality will be implemented soon.')

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        self.init_ui()  # Reinitialize UI to update buttons
        self.load_maintenance_schedule()  # Reload maintenance data 