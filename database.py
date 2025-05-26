import sqlite3
import bcrypt
from datetime import datetime, timedelta
import os
import json
import socket
import time
from pathlib import Path
import sys
from PyQt6.QtWidgets import QMessageBox

class Database:
    def __init__(self):
        # Set fixed database directory
        app_data_dir = 'D:/CURSOR/PROJECTS/LabManager/Database'
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
            
        # Set database path
        self.db_path = os.path.join(app_data_dir, 'lab_instruments.db')
        self.lock_file = os.path.join(app_data_dir, 'db.lock')
        self.lock_timeout = 30  # seconds
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                "Database file not found. Please ensure 'lab_instruments.db' exists in:\n" + 
                app_data_dir
            )
        
        print(f"Database path: {self.db_path}")
        print(f"Lock file path: {self.lock_file}")
        
        # Ensure we can write to the directory
        try:
            test_file = os.path.join(app_data_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("Write permissions verified")
        except Exception as e:
            print(f"Warning: Cannot write to directory: {e}")
            
        self.acquire_lock()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.has_unsaved_changes = False

    def acquire_lock(self):
        """Try to acquire a lock on the database file"""
        print(f"Attempting to acquire lock...")
        start_time = time.time()
        
        # First, try to remove any existing lock file
        try:
            if os.path.exists(self.lock_file):
                print(f"Found existing lock file, attempting to remove...")
                os.remove(self.lock_file)
                print("Existing lock file removed")
        except Exception as e:
            print(f"Warning: Could not remove existing lock file: {e}")
        
        while time.time() - start_time < self.lock_timeout:
            try:
                if os.path.exists(self.lock_file):
                    print(f"Lock file exists at: {self.lock_file}")
                    try:
                        with open(self.lock_file, 'r') as f:
                            lock_data = json.load(f)
                            current_user = lock_data.get('username', 'Unknown')
                            hostname = lock_data.get('hostname', 'Unknown')
                            timestamp = lock_data.get('timestamp', '')
                            print(f"Lock file contents: {lock_data}")
                            
                            # Check if the lock is stale (older than 5 minutes)
                            if timestamp:
                                lock_time = datetime.fromisoformat(timestamp)
                                if (datetime.now() - lock_time).total_seconds() > 300:  # 5 minutes
                                    print(f"Removing stale lock from {current_user} on {hostname}")
                                    os.remove(self.lock_file)
                                    continue
                    except Exception as e:
                        print(f"Error reading lock file: {e}")
                        # If we can't read the lock file, try to remove it
                        try:
                            os.remove(self.lock_file)
                            print("Removed unreadable lock file")
                            continue
                        except:
                            pass
                        
                    raise Exception(
                        f"The database is currently in use by {current_user} on {hostname}.\n\n"
                        "Please wait until they finish or ask them to close the application.\n"
                        "If you believe this is an error, you can delete the 'db.lock' file."
                    )
                
                # Create lock file with current user info
                lock_data = {
                    'username': os.getenv('USERNAME', 'Unknown'),
                    'hostname': socket.gethostname(),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"Creating new lock file with data: {lock_data}")
                with open(self.lock_file, 'w') as f:
                    json.dump(lock_data, f)
                print("Lock acquired successfully")
                return True
            except Exception as e:
                if "The database is currently in use" in str(e):
                    raise e
                print(f"Error during lock acquisition: {e}")
                time.sleep(1)
        raise Exception("Could not acquire database lock after timeout")

    def release_lock(self):
        """Release the lock on the database file"""
        try:
            if os.path.exists(self.lock_file):
                print(f"Releasing lock file: {self.lock_file}")
                os.remove(self.lock_file)
                print("Lock released successfully")
        except Exception as e:
            print(f"Error releasing lock: {e}")

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

    def get_maintenance_history(self, instrument_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT mr.*, u.username, mt.name as maintenance_type
            FROM maintenance_records mr
            JOIN users u ON mr.performed_by = u.id
            JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            WHERE mr.instrument_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (instrument_id,))
        return cursor.fetchall()

    def save_changes(self):
        """Save any pending changes to the database"""
        if self.has_unsaved_changes:
            self.conn.commit()
            self.has_unsaved_changes = False

    def get_upcoming_maintenance(self, days=28):
        """Get maintenance operations due in the next specified number of days"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                i.id, i.name, i.model, i.serial_number, i.location,
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
            JOIN instrument_maintenance_schedule ims ON i.id = ims.instrument_id
            JOIN maintenance_types mt ON ims.maintenance_type_id = mt.id
            JOIN users u ON i.responsible_user_id = u.id
            WHERE DATE(ims.maintenance_date, '+' || ims.period_days || ' days') <= DATE('now', '+' || ? || ' days')
            ORDER BY next_maintenance ASC
        """, (days,))
        return cursor.fetchall()

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