from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                            QMessageBox, QLineEdit, QComboBox,
                            QTextEdit, QSplitter, QHeaderView, QSizePolicy, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QBrush
from database import Database
from datetime import datetime, timedelta
from date_utils import (
    calculate_next_maintenance,
    format_date_for_display,
    format_date_for_db,
    get_maintenance_status
)
from src.ui.dialogs.instrument_details_dialog import InstrumentDetailsDialog
import sys

class MaintenanceWindow(QMainWindow):
    back_signal = pyqtSignal()  # Signal to go back to main menu

    def __init__(self, user_id, is_admin, db=None):
        super().__init__()
        self.user_id = user_id
        self.is_admin = is_admin
        self.db = db if db else Database()
        self.init_ui()
        self.apply_dark_theme()
        self.load_maintenance_data()

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
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel('Maintenance Operations')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)  # Adjusted to match our data
        self.table.setHorizontalHeaderLabels([
            'Instrument', 'Brand', 'Model', 'Serial Number', 'Location', 
            'Maintenance Type', 'Performed By', 'Last Maintenance', 
            'Next Maintenance', 'Notes'
        ])
        
        # Configure table for better scrolling and auto-resize
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        # Disable all edit triggers
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Connect cell click event
        self.table.cellClicked.connect(self.handle_cell_click)
        layout.addWidget(self.table)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Create buttons with fixed width
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.load_maintenance_data)
        refresh_button.setFixedWidth(200)

        back_button = QPushButton('Back to Main Menu')
        back_button.clicked.connect(self.back_signal.emit)
        back_button.setFixedWidth(200)

        # Add buttons to layout with proper spacing
        bottom_layout.addStretch()
        bottom_layout.addWidget(refresh_button)
        bottom_layout.addWidget(back_button)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)

    def handle_cell_click(self, row, column):
        """Handle cell click events"""
        if column == 0:  # Only handle clicks on the Instrument column
            instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if instrument_id:
                dialog = InstrumentDetailsDialog(instrument_id, self.user_id, self.is_admin, self)
                dialog.show()  # Use show() instead of exec() for QMainWindow

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update button widths when window is resized
        button_width = self.width() // 4
        for button in self.findChildren(QPushButton):
            button.setFixedWidth(button_width)

    def load_maintenance_data(self):
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
                    END as period_weeks,
                    i.date_start_operating
                FROM instruments i
                JOIN maintenance_types mt ON mt.id IN (i.maintenance_1, i.maintenance_2, i.maintenance_3)
                LEFT JOIN users u ON i.responsible_user_id = u.id
                WHERE i.status = 'Operational'
                ORDER BY i.name, mt.name
            """)
            
            self.table.setRowCount(0)
            for row, data in enumerate(cursor.fetchall()):
                self.table.insertRow(row)
                
                # Calculate next maintenance date using our utility function
                next_maintenance = calculate_next_maintenance(
                    data['last_maintenance'],
                    data['period_weeks'],
                    data['date_start_operating']
                )
                
                # Get maintenance status using our utility function
                status, color = get_maintenance_status(next_maintenance)
                
                # Format dates for display
                last_maintenance_display = format_date_for_display(data['last_maintenance'])
                next_maintenance_display = format_date_for_display(next_maintenance)
                
                # Add data to table
                instrument_item = QTableWidgetItem(str(data['name']))
                instrument_item.setForeground(QBrush(QColor("#4a9eff")))  # Light blue color for hyperlink
                instrument_item.setData(Qt.ItemDataRole.UserRole, data['id'])
                self.table.setItem(row, 0, instrument_item)
                
                self.table.setItem(row, 1, QTableWidgetItem(str(data['brand'])))
                self.table.setItem(row, 2, QTableWidgetItem(str(data['model'])))
                self.table.setItem(row, 3, QTableWidgetItem(str(data['serial_number'])))
                self.table.setItem(row, 4, QTableWidgetItem(str(data['location'])))
                self.table.setItem(row, 5, QTableWidgetItem(str(data['maintenance_type'])))
                self.table.setItem(row, 6, QTableWidgetItem(str(data['performed_by'] or 'Not assigned')))
                self.table.setItem(row, 7, QTableWidgetItem(last_maintenance_display))
                self.table.setItem(row, 8, QTableWidgetItem(next_maintenance_display))
                self.table.setItem(row, 9, QTableWidgetItem(str(data['notes'] or '')))
                
                # Set row color based on maintenance status
                if color:
                    for col in range(self.table.columnCount()):
                        self.table.item(row, col).setBackground(QColor(color))
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load maintenance data: {str(e)}')

    def update_user(self, user_id, is_admin):
        """Update the user information when returning to this view"""
        self.user_id = user_id
        self.is_admin = is_admin
        
        # Reload data
        self.load_maintenance_data()

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        self.load_maintenance_data()  # Refresh data when window is shown 