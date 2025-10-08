import sqlite3
import bcrypt
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import signal
from PyQt6.QtWidgets import QMessageBox
from src.utils.path_utils import get_database_directory, get_database_path

class Database:
    def __init__(self):
        # Get database directory using the new path utility
        app_data_dir = get_database_directory()
        
        # Set database path
        self.db_path = get_database_path()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                "Database file not found. Please ensure 'lab_instruments.db' exists in:\n" + 
                app_data_dir
            )
        
        print(f"Database path: {self.db_path}")
        
        # Ensure we can write to the directory
        try:
            test_file = os.path.join(app_data_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("Write permissions verified")
        except Exception as e:
            print(f"Warning: Cannot write to directory: {e}")
            
        # Connect to database with WAL mode for concurrent access
        self.conn = sqlite3.connect(self.db_path, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        
        self.has_unsaved_changes = False

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        print(f"Received signal {signum}, cleaning up...")
        if hasattr(self, 'conn'):
            self.conn.close()
        sys.exit(0)

    def verify_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, password, is_admin FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return {'id': user['id'], 'is_admin': bool(user['is_admin'])}
        return None

    def get_all_instruments(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM instruments")
        return cursor.fetchall()

    def add_instrument(self, name, model, serial_number, location):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO instruments (name, model, serial_number, location) VALUES (?, ?, ?, ?)",
            (name, model, serial_number, location)
        )
        self.conn.commit()
        self.has_unsaved_changes = True
        return cursor.lastrowid

    def add_maintenance_record(self, instrument_id, maintenance_type_id, user_id, notes):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_records (
                instrument_id, maintenance_type_id, maintenance_date,
                performed_by, notes
            )
            VALUES (?, ?, DATE('now'), ?, ?)
        """, (instrument_id, maintenance_type_id, user_id, notes))
        self.conn.commit()
        self.has_unsaved_changes = True
        return True

    def save_changes(self):
        """Save any pending changes to the database"""
        if self.has_unsaved_changes:
            self.conn.commit()
            self.has_unsaved_changes = False

    def get_instrument_details(self, instrument_id):
        """Get detailed information about an instrument including maintenance schedule"""
        cursor = self.conn.cursor()
        
        # Get basic instrument info
        cursor.execute("""
            SELECT i.*, u.username as responsible_user
            FROM instruments i
            LEFT JOIN users u ON i.responsible_user_id = u.id
            WHERE i.id = ?
        """, (instrument_id,))
        instrument = cursor.fetchone()
        
        if not instrument:
            return None
            
        # Get maintenance schedule
        cursor.execute("""
            SELECT mt.name, ims.period_days,
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
                   END as next_maintenance
            FROM instruments i
            JOIN instrument_maintenance_schedule ims ON i.id = ims.instrument_id
            JOIN maintenance_types mt ON ims.maintenance_type_id = mt.id
            WHERE i.id = ?
        """, (instrument_id,))
        maintenance_schedule = cursor.fetchall()
        
        # Get maintenance history
        cursor.execute("""
            SELECT 
                mr.maintenance_date,
                mt.name as maintenance_type,
                u.username as performed_by,
                mr.notes
            FROM maintenance_records mr
            JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            JOIN users u ON mr.performed_by = u.id
            WHERE mr.instrument_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (instrument_id,))
        maintenance_history = cursor.fetchall()
        
        return {
            'instrument': instrument,
            'maintenance_schedule': maintenance_schedule,
            'maintenance_history': maintenance_history
        }

    def get_user_responsibilities(self, user_id):
        """Get all instruments a user is responsible for"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.*, 
                   GROUP_CONCAT(mt.name) as maintenance_types,
                   GROUP_CONCAT(ims.period_days) as maintenance_periods
            FROM instruments i
            LEFT JOIN instrument_maintenance_schedule ims ON i.id = ims.instrument_id
            LEFT JOIN maintenance_types mt ON ims.maintenance_type_id = mt.id
            WHERE i.responsible_user_id = ?
            GROUP BY i.id
        """, (user_id,))
        return cursor.fetchall()

    def __del__(self):
        """Cleanup when the database connection is closed"""
        try:
            self.save_changes()
            if hasattr(self, 'conn'):
                self.conn.close()
            self.release_lock()
        except Exception as e:
            print(f"Error during cleanup: {e}") 