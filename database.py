import sqlite3
import bcrypt
from datetime import datetime, timedelta
import os
import json
import socket
import time
from pathlib import Path
import sys

class Database:
    def __init__(self):
        # Get the directory where the executable is located
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # If running as script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.db_path = os.path.join(self.base_dir, 'lab_instruments.db')
        self.lock_file = os.path.join(self.base_dir, 'db.lock')
        self.lock_timeout = 30  # seconds
        
        print(f"Database path: {self.db_path}")
        print(f"Lock file path: {self.lock_file}")
        
        # Ensure we can write to the directory
        try:
            test_file = os.path.join(self.base_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("Write permissions verified")
        except Exception as e:
            print(f"Warning: Cannot write to directory: {e}")
            
        self.acquire_lock()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.initialize_default_data()
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

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
        ''')

        # Instruments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            serial_number TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL,
            brand TEXT NOT NULL,
            responsible_user_id INTEGER,
            date_start_operating TEXT NOT NULL,
            maintenance_1 INTEGER,
            period_1 INTEGER,
            maintenance_2 INTEGER,
            period_2 INTEGER,
            maintenance_3 INTEGER,
            period_3 INTEGER,
            FOREIGN KEY (responsible_user_id) REFERENCES users (id),
            FOREIGN KEY (maintenance_1) REFERENCES maintenance_types (id),
            FOREIGN KEY (maintenance_2) REFERENCES maintenance_types (id),
            FOREIGN KEY (maintenance_3) REFERENCES maintenance_types (id)
        )
        ''')

        # Maintenance types table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
        ''')

        # Maintenance records table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            maintenance_type_id INTEGER NOT NULL,
            maintenance_date DATE NOT NULL,
            performed_by INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (instrument_id) REFERENCES instruments (id),
            FOREIGN KEY (maintenance_type_id) REFERENCES maintenance_types (id),
            FOREIGN KEY (performed_by) REFERENCES users (id)
        )
        ''')

        self.conn.commit()

    def initialize_default_data(self):
        cursor = self.conn.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Add default users
            default_users = [
                ('admin1', 'admin1@example.com', bcrypt.hashpw('admin111'.encode('utf-8'), bcrypt.gensalt()), True),
                ('admin2', 'admin2@example.com', bcrypt.hashpw('admin222'.encode('utf-8'), bcrypt.gensalt()), True),
                ('user1', 'user1@example.com', bcrypt.hashpw('user111'.encode('utf-8'), bcrypt.gensalt()), False),
                ('user2', 'user2@example.com', bcrypt.hashpw('user222'.encode('utf-8'), bcrypt.gensalt()), False),
                ('user3', 'user3@example.com', bcrypt.hashpw('user333'.encode('utf-8'), bcrypt.gensalt()), False),
                ('user4', 'user4@example.com', bcrypt.hashpw('user444'.encode('utf-8'), bcrypt.gensalt()), False)
            ]
            
            cursor.executemany(
                "INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                default_users
            )

        # Check if maintenance types exist
        cursor.execute("SELECT COUNT(*) FROM maintenance_types")
        if cursor.fetchone()[0] == 0:
            # Add default maintenance types
            maintenance_types = [
                ('Cleaning', 'Inspection and cleaning'),
                ('Calibration', 'Maintenance and calibration'),
                ('Battery test', 'Battery test'),
                ('Battery replacement', 'Battery replacement')
            ]
            
            cursor.executemany(
                "INSERT INTO maintenance_types (name, description) VALUES (?, ?)",
                maintenance_types
            )

        # Check if instruments exist
        cursor.execute("SELECT COUNT(*) FROM instruments")
        if cursor.fetchone()[0] == 0:
            # Add dummy instruments with responsible users
            dummy_instruments = [
                ('Microscope Olympus BX53', 'BX53', 'OLY-2023-001', 'Lab 101', 'Operational', 'Olympus', 3, '01-01-2025', 1, 13, None, None, None, None),
                ('Centrifuge Eppendorf 5810R', '5810R', 'EPP-2023-002', 'Lab 101', 'Operational', 'Eppendorf', 3, '10-01-2025', 1, 4, 2, 13, 3, 52),
                ('PCR Machine Bio-Rad T100', 'T100', 'BIO-2023-003', 'Lab 102', 'Operational', 'Bio-Rad', 3, '20-01-2025', 1, 13, None, None, None, None),
                ('Autoclave Tuttnauer 2540M', '2540M', 'TUT-2023-004', 'Lab 103', 'Operational', 'Tuttnauer', 3, '30-01-2025', 2, 13, None, None, None, None),
                ('pH Meter Mettler Toledo', 'SevenCompact', 'MET-2023-005', 'Lab 101', 'Operational', 'Mettler Toledo', 3, '01-02-2025', 2, 13, None, None, None, None),
                ('Incubator Memmert IN55', 'IN55', 'MEM-2023-006', 'Lab 102', 'Operational', 'Memmert', 3, '10-02-2025', 2, 13, None, None, None, None),
                ('Spectrophotometer Thermo Scientific', 'GENESYS 150', 'THE-2023-007', 'Lab 103', 'Operational', 'Thermo Scientific', 4, '20-02-2025', 1, 4, 2, 13, 3, 52),
                ('Water Purification System Milli-Q', 'Advantage A10', 'MIL-2023-008', 'Lab 101', 'Operational', 'Merck', 4, '01-03-2025', 2, 13, None, None, None, None),
                ('Freezer -80°C Thermo Scientific', 'ULT-1386-3-V', 'THE-2023-009', 'Lab 104', 'Operational', 'Thermo Scientific', 4, '10-03-2025', 2, 13, None, None, None, None),
                ('Laminar Flow Hood Esco', 'Airstream AC2-4S1', 'ESC-2023-010', 'Lab 102', 'Operational', 'Esco', 4, '20-03-2025', 2, 13, 3, 52, None, None),
                ('Vortex Mixer IKA', 'MS 3 digital', 'IKA-2023-011', 'Lab 101', 'Operational', 'IKA', 4, '30-03-2025', 2, 13, 3, 52, None, None),
                ('Magnetic Stirrer IKA', 'RCT basic', 'IKA-2023-012', 'Lab 101', 'Operational', 'IKA', 4, '01-04-2025', 2, 13, None, None, None, None),
                ('Hot Plate Corning', 'PC-420D', 'COR-2023-013', 'Lab 102', 'Operational', 'Corning', 5, '10-04-2025', 2, 13, None, None, None, None),
                ('Microplate Reader BioTek', 'Synergy H1', 'BIO-2023-014', 'Lab 103', 'Operational', 'BioTek', 5, '20-04-2025', 1, 4, 2, 13, 3, 52),
                ('Gel Documentation System Bio-Rad', 'ChemiDoc MP', 'BIO-2023-015', 'Lab 102', 'Operational', 'Bio-Rad', 5, '30-04-2025', 1, 4, 2, 13, 3, 52),
                ('CO2 Incubator Thermo Scientific', 'Heracell 150i', 'THE-2023-016', 'Lab 104', 'Operational', 'Thermo Scientific', 5, '01-05-2025', 2, 13, None, None, None, None),
                ('Shaker Incubator New Brunswick', 'Innova 42', 'NEW-2023-017', 'Lab 102', 'Operational', 'New Brunswick', 5, '10-05-2025', 2, 13, None, None, None, None),
                ('Ultrasonic Cleaner Branson', 'CPXH', 'BRA-2023-018', 'Lab 103', 'Operational', 'Branson', 5, '10-05-2025', 2, 52, None, None, None, None),
                ('Microbalance Mettler Toledo', 'XS205', 'MET-2023-019', 'Lab 101', 'Operational', 'Mettler Toledo', 5, '20-05-2025', 2, 52, None, None, None, None),
                ('Refrigerator Thermo Scientific', 'TSX400', 'THE-2023-020', 'Lab 104', 'Operational', 'Thermo Scientific', 5, '20-05-2025', 2, 13, None, None, None, None)
            ]
            
            cursor.executemany(
                """INSERT INTO instruments 
                   (name, model, serial_number, location, status, brand, responsible_user_id, 
                    date_start_operating, maintenance_1, period_1, maintenance_2, period_2, 
                    maintenance_3, period_3) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                dummy_instruments
            )

            # Add maintenance records for each instrument's maintenance types
            cursor.execute("SELECT id, maintenance_1, maintenance_2, maintenance_3, responsible_user_id FROM instruments")
            instruments = cursor.fetchall()
            
            for instrument in instruments:
                # Add record for maintenance_1 if it exists
                if instrument['maintenance_1'] is not None:
                    cursor.execute("""
                        INSERT INTO maintenance_records 
                        (instrument_id, maintenance_type_id, maintenance_date, performed_by, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (instrument['id'], instrument['maintenance_1'], '2025-05-15', 
                          instrument['responsible_user_id'], 'The device functions properly'))
                
                # Add record for maintenance_2 if it exists
                if instrument['maintenance_2'] is not None:
                    cursor.execute("""
                        INSERT INTO maintenance_records 
                        (instrument_id, maintenance_type_id, maintenance_date, performed_by, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (instrument['id'], instrument['maintenance_2'], '2025-05-15', 
                          instrument['responsible_user_id'], 'The device functions properly'))
                
                # Add record for maintenance_3 if it exists
                if instrument['maintenance_3'] is not None:
                    cursor.execute("""
                        INSERT INTO maintenance_records 
                        (instrument_id, maintenance_type_id, maintenance_date, performed_by, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (instrument['id'], instrument['maintenance_3'], '2025-05-15', 
                          instrument['responsible_user_id'], 'The device functions properly'))

        self.conn.commit()

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