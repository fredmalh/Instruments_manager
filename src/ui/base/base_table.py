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
        
        # Connect sorting signal for debugging
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

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

    def debug_table_state(self, message="Table state"):
        """Debug method to log current table state"""
        print(f"DEBUG: {message}")
        print(f"DEBUG: Rows: {self.rowCount()}, Columns: {self.columnCount()}")
        if self.rowCount() > 0:
            # Log first row
            first_row = []
            for col in range(self.columnCount()):
                item = self.item(0, col)
                first_row.append(item.text() if item else "None")
            print(f"DEBUG: First row: {first_row}")
            
            # Log last row
            last_row = []
            for col in range(self.columnCount()):
                item = self.item(self.rowCount()-1, col)
                last_row.append(item.text() if item else "None")
            print(f"DEBUG: Last row: {last_row}")
        print("---")

    def on_header_clicked(self, logical_index):
        """Handle header click for debugging"""
        print(f"DEBUG: Header clicked - Column {logical_index}")
        # Use a timer to check table state after sorting is complete
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.debug_table_state("After sorting"))

    def populate_table(self, data_list, column_configs=None, row_highlights=None):
        """
        Populate table with data using a consistent approach that preserves sorting
        
        Args:
            data_list: List of dictionaries containing row data
            column_configs: Optional list of column configuration dictionaries
                          Each config can have: 'key', 'formatter', 'color', 'is_clickable'
            row_highlights: Optional list of highlight colors for each row
        """
        # Disable sorting temporarily to prevent column count issues
        sorting_enabled = self.isSortingEnabled()
        self.setSortingEnabled(False)
        
        # Clear any existing sort state to prevent automatic re-sorting
        self.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        
        # Clear highlighted rows first
        self.highlighted_rows.clear()
        
        # Set column count BEFORE clearing rows to ensure proper table state
        if column_configs:
            self.setColumnCount(len(column_configs))
        elif data_list:
            # If no column_configs, use the number of keys in the first row
            self.setColumnCount(len(data_list[0]))
        
        # Now clear all rows
        self.setRowCount(0)
        
        for row_idx, row_data in enumerate(data_list):
            self.insertRow(row_idx)
            
            # Use column_configs to determine the order, or fall back to row_data.items()
            if column_configs:
                for col_idx, config in enumerate(column_configs):
                    key = config.get('key')
                    if key and key in row_data:
                        value = row_data[key]
                    else:
                        # Fallback: get value by index if key not found
                        values = list(row_data.values())
                        value = values[col_idx] if col_idx < len(values) else ''
                    
                    # Create item
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    # Apply column-specific formatting
                    if config.get('color'):
                        item.setForeground(QColor(config['color']))
                    
                    if config.get('is_clickable'):
                        # Store the row ID in UserRole for clickable items
                        row_id = row_data.get('id') or row_data.get('instrument_id')
                        if row_id:
                            item.setData(Qt.ItemDataRole.UserRole, row_id)
                    
                    # Set the item
                    self.setItem(row_idx, col_idx, item)
            else:
                # Fallback to original behavior if no column_configs provided
                for col_idx, (key, value) in enumerate(row_data.items()):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.setItem(row_idx, col_idx, item)
            
            # Apply row highlighting if specified
            if row_highlights and row_idx < len(row_highlights) and row_highlights[row_idx]:
                self._apply_row_highlighting(row_idx, row_highlights[row_idx])
            elif 'highlight_color' in row_data and row_data['highlight_color']:
                # Handle integrated highlighting from data
                self._apply_row_highlighting(row_idx, row_data['highlight_color'])
        
        # Re-enable sorting if it was enabled before
        self.setSortingEnabled(sorting_enabled)
        
        # Debug: Log the first few rows to verify data integrity
        if data_list and len(data_list) > 0:
            print(f"DEBUG: Table populated with {len(data_list)} rows")
            print(f"DEBUG: First row data: {data_list[0]}")
            if len(data_list) > 1:
                print(f"DEBUG: Second row data: {data_list[1]}")
            print(f"DEBUG: Last row data: {data_list[-1]}")
            print("---")

    def _apply_row_highlighting(self, row, color):
        """Apply highlighting to a specific row"""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                # Set background color
                item.setBackground(QColor(color))
                
                # Set text color based on background
                if color == 'yellow':  # Yellow background
                    if col == 0:  # Instrument name - keep blue
                        item.setForeground(QColor("#4a9eff"))
                    else:  # Other columns - dark grey
                        item.setForeground(QColor('#333333'))
                else:  # Other colors (red, green, etc.)
                    if col == 0:  # Instrument name - always keep blue
                        item.setForeground(QColor("#4a9eff"))
                    # For other columns with other colors, don't set text color
                    # This allows the default white text to be used 