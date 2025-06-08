from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

class BaseTable(QTableWidget):
    # Signal emitted when a row is double-clicked
    row_double_clicked = pyqtSignal(int)  # Emits the row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_logging()
        self.init_table()
        self.apply_dark_theme()

    def setup_logging(self):
        """Setup logging for the table"""
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def init_table(self):
        """Initialize table settings"""
        # Enable sorting
        self.setSortingEnabled(True)
        
        # Enable alternating row colors
        self.setAlternatingRowColors(True)
        
        # Enable selection of entire rows
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Enable single selection
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Enable grid
        self.setShowGrid(True)
        
        # Enable word wrap
        self.setWordWrap(True)
        
        # Connect double-click signal
        self.cellDoubleClicked.connect(self._handle_double_click)

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
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3d3d3d;
            }
        """)

    def _handle_double_click(self, row, column):
        """Handle double-click on a row"""
        self.row_double_clicked.emit(row)

    def set_headers(self, headers):
        """Set table headers"""
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)

    def add_row(self, data, row_id=None):
        """Add a row to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
            self.setItem(row, col, item)
        
        if row_id is not None:
            self.item(row, 0).setData(Qt.ItemDataRole.UserRole, row_id)

    def clear_table(self):
        """Clear all rows from the table"""
        self.setRowCount(0)

    def get_selected_row_id(self):
        """Get the ID of the selected row"""
        selected_rows = self.selectedItems()
        if selected_rows:
            return self.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return None

    def highlight_row(self, row, color='red'):
        """Highlight a specific row with a color"""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(color))

    def resize_columns_to_content(self):
        """Resize all columns to fit their content"""
        self.resizeColumnsToContents()
        self.resizeRowsToContents() 