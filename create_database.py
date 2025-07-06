import sqlite3
import bcrypt
import os
import sys
from datetime import datetime
from src.utils.path_utils import get_database_directory, get_database_path

def create_database():
    # Get database directory using the new path utility
    app_data_dir = get_database_directory()
    
    # Set database path
    db_path = get_database_path()
    print(f"Creating database at: {db_path}")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    print("Creating database tables...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )
    ''')

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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    ''')

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

    # Add default users
    default_users = [
        ('admin1', 'admin1@example.com', bcrypt.hashpw('admin111'.encode('utf-8'), bcrypt.gensalt()), True),
        ('admin2', 'admin2@example.com', bcrypt.hashpw('admin222'.encode('utf-8'), bcrypt.gensalt()), True),
        ('user1', 'user1@example.com', bcrypt.hashpw('user111'.encode('utf-8'), bcrypt.gensalt()), False),
        ('user2', 'user2@example.com', bcrypt.hashpw('user222'.encode('utf-8'), bcrypt.gensalt()), False),
        ('user3', 'user3@example.com', bcrypt.hashpw('user333'.encode('utf-8'), bcrypt.gensalt()), False),
        ('user4', 'user4@example.com', bcrypt.hashpw('user444'.encode('utf-8'), bcrypt.gensalt()), False),
        ('user5', 'user5@example.com', bcrypt.hashpw('user555'.encode('utf-8'), bcrypt.gensalt()), False)
    ]
    
    cursor.executemany(
        "INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
        default_users
    )

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

    # Add dummy instruments
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

    conn.commit()
    conn.close()
    print(f"Database created successfully at {db_path}")

if __name__ == "__main__":
    create_database() 