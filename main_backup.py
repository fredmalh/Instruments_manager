import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import CentralWindow
from src.services.reminder_scheduler import ReminderScheduler
from src.database.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Initialize database
    db = Database()
    
    # Initialize reminder scheduler
    reminder_scheduler = ReminderScheduler(db.connection)
    
    # Create and show central window
    window = CentralWindow()
    window.show()
    
    # Start reminder scheduler
    try:
        reminder_scheduler.start()
        logging.info("Reminder scheduler started successfully")
    except Exception as e:
        logging.error(f"Failed to start reminder scheduler: {e}")
    
    # Set up cleanup on application exit
    def cleanup():
        reminder_scheduler.stop()
        db.close()
        logging.info("Application cleanup completed")
    
    app.aboutToQuit.connect(cleanup)
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 