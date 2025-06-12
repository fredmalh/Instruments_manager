from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, 
                            QWidget, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

class BaseTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_logging()
        self.init_table()
        self.apply_dark_theme()
        self.highlighted_rows = set()

    def setup_logging(self):
        """Setup logging for the table"""
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def apply_dark_theme(self):
        """Apply dark theme to the table"""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3d3d3d;
            }
            QLabel[clickable="true"] {
                color: #0d47a1;
                text-decoration: underline;
            }
            QLabel[clickable="true"]:hover {
                color: #1565c0;
                cursor: pointer;
            }
        """)

    def init_table(self):
        """Initialize table settings"""
        # Enable sorting
        self.setSortingEnabled(True)
        
        # Enable selection of entire rows
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Enable single selection
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Enable grid
        self.setShowGrid(True)
        
        # Enable word wrap
        self.setWordWrap(True)
        
        # Disable editing
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def highlight_row(self, row, color='red'):
        """Highlight a specific row with a color"""
        # Convert color name to hex if needed
        color_map = {
            'red': '#ff0000',
            'yellow': '#ffff00',
            'green': '#00ff00'
        }
        hex_color = color_map.get(color, color)
        
        # Add the row to highlighted set
        self.highlighted_rows.add(row)
        
        # Apply highlighting to each cell in the row
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                # Create a new item to ensure clean state
                new_item = QTableWidgetItem(item.text())
                new_item.setData(Qt.ItemDataRole.UserRole, item.data(Qt.ItemDataRole.UserRole))
                
                # Set the background color
                new_item.setBackground(QColor(hex_color))
                
                # Set text color to dark grey if background is yellow
                if hex_color == '#ffff00':
                    new_item.setForeground(QColor('#333333'))
                
                # Replace the old item
                self.setItem(row, col, new_item)
        
        # Force the row to be visible
        self.scrollToItem(self.item(row, 0))
        self.viewport().update()

    def clear_table(self):
        """Clear all rows from the table"""
        self.highlighted_rows.clear()
        self.setRowCount(0)

    def add_row(self, data, row_id=None):
        """Add a row to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, value in enumerate(data):
            if isinstance(value, QWidget):
                # For QWidgets, set the cell widget
                self.setCellWidget(row, col, value)
            else:
                # For regular values, create a QTableWidgetItem
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                
                # Set alternating row colors
                if row % 2 == 0:
                    item.setBackground(QColor("#2d2d2d"))
                else:
                    item.setBackground(QColor("#252525"))
                
                self.setItem(row, col, item)
        
        if row_id is not None:
            # Store the row_id in the first column's item
            if isinstance(data[0], QWidget):
                # If first column is a widget, create a hidden item for the ID
                item = QTableWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, row_id)
                self.setItem(row, 0, item)
            else:
                # If first column is a regular item, just set the data
                self.item(row, 0).setData(Qt.ItemDataRole.UserRole, row_id)
        
        # If this row was previously highlighted, reapply the highlight
        if row in self.highlighted_rows:
            self.highlight_row(row, 'yellow')

    def set_headers(self, headers):
        """Set table headers"""
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)

    def create_clickable_label(self, text, callback):
        """Create a clickable label with consistent styling"""
        label = QLabel(text)
        label.setProperty("clickable", "true")
        label.mousePressEvent = callback
        return label

    def get_selected_row_id(self):
        """Get the ID of the selected row"""
        selected_rows = self.selectedItems()
        if selected_rows:
            return self.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return None

    def resize_columns_to_content(self):
        """Resize all columns to fit their content"""
        self.resizeColumnsToContents()
        self.resizeRowsToContents() 