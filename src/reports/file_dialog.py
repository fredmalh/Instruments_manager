from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
import os
from datetime import datetime

class PDFSaveDialog:
    """Dialog for saving PDF reports with custom path selection"""
    
    @staticmethod
    def get_save_path(parent, default_filename, title="Save Maintenance Report"):
        """
        Show a file save dialog for PDF files
        
        Args:
            parent: Parent widget
            default_filename: Default filename to suggest
            title: Dialog title
        
        Returns:
            str: Selected file path, or None if cancelled
        """
        try:
            # Get the directory of the default filename
            default_dir = os.path.dirname(default_filename)
            default_name = os.path.basename(default_filename)
            
            # Show file save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                title,
                os.path.join(default_dir, default_name),
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if file_path:
                # Ensure the file has .pdf extension
                if not file_path.lower().endswith('.pdf'):
                    file_path += '.pdf'
                
                # Check if file already exists
                if os.path.exists(file_path):
                    reply = QMessageBox.question(
                        parent,
                        "File Exists",
                        f"The file '{os.path.basename(file_path)}' already exists.\nDo you want to replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return None
                
                return file_path
            
            return None
            
        except Exception as e:
            QMessageBox.critical(
                parent,
                "Error",
                f"Error showing save dialog: {str(e)}"
            )
            return None
    
    @staticmethod
    def show_success_message(parent, file_path):
        """Show success message after PDF generation"""
        try:
            message = f"Maintenance report generated successfully!\n\nFile saved to:\n{file_path}\n\nThe PDF will open automatically."
            
            QMessageBox.information(
                parent,
                "Report Generated",
                message
            )
        except Exception as e:
            print(f"Error showing success message: {e}")
    
    @staticmethod
    def show_error_message(parent, error_message):
        """Show error message if PDF generation fails"""
        try:
            QMessageBox.critical(
                parent,
                "PDF Generation Error",
                f"Failed to generate PDF report:\n\n{error_message}"
            )
        except Exception as e:
            print(f"Error showing error message: {e}") 