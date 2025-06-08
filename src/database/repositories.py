from typing import List, Dict, Any, Optional
from datetime import datetime
from .database_manager import DatabaseManager, DatabaseQueryError
import bcrypt

class BaseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

class UserRepository(BaseRepository):
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.db.execute_query("SELECT * FROM users ORDER BY username")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.db.get_single_row("SELECT * FROM users WHERE id = ?", (user_id,))
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.db.get_single_row("SELECT * FROM users WHERE username = ?", (username,))
    
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user password and return user data if valid"""
        user = self.get_user_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return user
        return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def create_user(self, username: str, email: str, password: str, role: str) -> int:
        """Create a new user"""
        hashed_password = self.hash_password(password)
        query = """
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_update(query, (username, email, hashed_password, role))
    
    def update_user(self, user_id: int, username: str, email: str, 
                   password: Optional[str], role: str) -> int:
        """Update user details"""
        if password:
            hashed_password = self.hash_password(password)
            query = """
                UPDATE users 
                SET username = ?, email = ?, password = ?, role = ?
                WHERE id = ?
            """
            params = (username, email, hashed_password, role, user_id)
        else:
            query = """
                UPDATE users 
                SET username = ?, email = ?, role = ?
                WHERE id = ?
            """
            params = (username, email, role, user_id)
        return self.db.execute_update(query, params)
    
    def delete_user(self, user_id: int) -> int:
        """Delete a user"""
        return self.db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
    
    def check_username_exists(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if username exists"""
        if exclude_user_id:
            query = "SELECT 1 FROM users WHERE username = ? AND id != ?"
            params = (username, exclude_user_id)
        else:
            query = "SELECT 1 FROM users WHERE username = ?"
            params = (username,)
        return bool(self.db.get_scalar(query, params))
    
    def check_email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email exists"""
        if exclude_user_id:
            query = "SELECT 1 FROM users WHERE email = ? AND id != ?"
            params = (email, exclude_user_id)
        else:
            query = "SELECT 1 FROM users WHERE email = ?"
            params = (email,)
        return bool(self.db.get_scalar(query, params))

class InstrumentRepository(BaseRepository):
    def get_all_instruments(self) -> List[Dict[str, Any]]:
        """Get all instruments"""
        return self.db.execute_query("SELECT * FROM instruments ORDER BY name")
    
    def get_instrument_by_id(self, instrument_id: int) -> Optional[Dict[str, Any]]:
        """Get instrument by ID"""
        return self.db.get_single_row("SELECT * FROM instruments WHERE id = ?", (instrument_id,))
    
    def create_instrument(self, name: str, model: str, serial_number: str, 
                         location: str, status: str, brand: str, 
                         responsible_user_id: Optional[int], date_start_operating: datetime,
                         maintenance_1: Optional[int], period_1: Optional[int],
                         maintenance_2: Optional[int], period_2: Optional[int],
                         maintenance_3: Optional[int], period_3: Optional[int],
                         notes: Optional[str]) -> int:
        """Create a new instrument"""
        query = """
            INSERT INTO instruments (
                name, model, serial_number, location, status, brand,
                responsible_user_id, date_start_operating,
                maintenance_1, period_1, maintenance_2, period_2,
                maintenance_3, period_3, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (name, model, serial_number, location, status, brand,
                 responsible_user_id, date_start_operating,
                 maintenance_1, period_1, maintenance_2, period_2,
                 maintenance_3, period_3, notes)
        return self.db.execute_update(query, params)
    
    def update_instrument(self, instrument_id: int, name: str, model: str, 
                         serial_number: str, location: str, status: str, 
                         brand: str, responsible_user_id: Optional[int],
                         date_start_operating: datetime,
                         maintenance_1: Optional[int], period_1: Optional[int],
                         maintenance_2: Optional[int], period_2: Optional[int],
                         maintenance_3: Optional[int], period_3: Optional[int],
                         notes: Optional[str]) -> int:
        """Update instrument details"""
        query = """
            UPDATE instruments SET
                name = ?, model = ?, serial_number = ?, location = ?,
                status = ?, brand = ?, responsible_user_id = ?,
                date_start_operating = ?, maintenance_1 = ?, period_1 = ?,
                maintenance_2 = ?, period_2 = ?, maintenance_3 = ?,
                period_3 = ?, notes = ?
            WHERE id = ?
        """
        params = (name, model, serial_number, location, status, brand,
                 responsible_user_id, date_start_operating,
                 maintenance_1, period_1, maintenance_2, period_2,
                 maintenance_3, period_3, notes, instrument_id)
        return self.db.execute_update(query, params)
    
    def delete_instrument(self, instrument_id: int) -> int:
        """Delete an instrument"""
        return self.db.execute_update("DELETE FROM instruments WHERE id = ?", (instrument_id,))
    
    def get_instruments_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get instruments assigned to a user"""
        return self.db.execute_query(
            "SELECT * FROM instruments WHERE responsible_user_id = ? ORDER BY name",
            (user_id,)
        )

class MaintenanceRepository(BaseRepository):
    def get_all_maintenance_records(self) -> List[Dict[str, Any]]:
        """Get all maintenance records"""
        return self.db.execute_query("""
            SELECT mr.*, i.name as instrument_name, mt.name as maintenance_type_name,
                   u.username as performed_by_username
            FROM maintenance_records mr
            LEFT JOIN instruments i ON mr.instrument_id = i.id
            LEFT JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            LEFT JOIN users u ON mr.performed_by = u.id
            ORDER BY mr.maintenance_date DESC
        """)
    
    def get_maintenance_by_id(self, maintenance_id: int) -> Optional[Dict[str, Any]]:
        """Get maintenance record by ID"""
        return self.db.get_single_row("""
            SELECT mr.*, i.name as instrument_name, mt.name as maintenance_type_name,
                   u.username as performed_by_username
            FROM maintenance_records mr
            LEFT JOIN instruments i ON mr.instrument_id = i.id
            LEFT JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            LEFT JOIN users u ON mr.performed_by = u.id
            WHERE mr.id = ?
        """, (maintenance_id,))
    
    def create_maintenance_record(self, instrument_id: int, maintenance_type_id: int,
                                maintenance_date: datetime, performed_by: Optional[int],
                                notes: Optional[str]) -> int:
        """Create a new maintenance record"""
        query = """
            INSERT INTO maintenance_records (
                instrument_id, maintenance_type_id, maintenance_date,
                performed_by, notes
            ) VALUES (?, ?, ?, ?, ?)
        """
        params = (instrument_id, maintenance_type_id, maintenance_date,
                 performed_by, notes)
        return self.db.execute_update(query, params)
    
    def update_maintenance_record(self, maintenance_id: int, instrument_id: int,
                                maintenance_type_id: int, maintenance_date: datetime,
                                performed_by: Optional[int], notes: Optional[str]) -> int:
        """Update maintenance record"""
        query = """
            UPDATE maintenance_records SET
                instrument_id = ?, maintenance_type_id = ?, maintenance_date = ?,
                performed_by = ?, notes = ?
            WHERE id = ?
        """
        params = (instrument_id, maintenance_type_id, maintenance_date,
                 performed_by, notes, maintenance_id)
        return self.db.execute_update(query, params)
    
    def delete_maintenance_record(self, maintenance_id: int) -> int:
        """Delete a maintenance record"""
        return self.db.execute_update(
            "DELETE FROM maintenance_records WHERE id = ?",
            (maintenance_id,)
        )
    
    def get_maintenance_by_instrument(self, instrument_id: int) -> List[Dict[str, Any]]:
        """Get maintenance records for an instrument"""
        return self.db.execute_query("""
            SELECT mr.*, mt.name as maintenance_type_name,
                   u.username as performed_by_username
            FROM maintenance_records mr
            LEFT JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            LEFT JOIN users u ON mr.performed_by = u.id
            WHERE mr.instrument_id = ?
            ORDER BY mr.maintenance_date DESC
        """, (instrument_id,))
    
    def get_maintenance_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get maintenance records performed by a user"""
        return self.db.execute_query("""
            SELECT mr.*, i.name as instrument_name, mt.name as maintenance_type_name
            FROM maintenance_records mr
            LEFT JOIN instruments i ON mr.instrument_id = i.id
            LEFT JOIN maintenance_types mt ON mr.maintenance_type_id = mt.id
            WHERE mr.performed_by = ?
            ORDER BY mr.maintenance_date DESC
        """, (user_id,))

class MaintenanceTypeRepository(BaseRepository):
    def get_all_maintenance_types(self) -> List[Dict[str, Any]]:
        """Get all maintenance types"""
        return self.db.execute_query("SELECT * FROM maintenance_types ORDER BY name")
    
    def get_maintenance_type_by_id(self, type_id: int) -> Optional[Dict[str, Any]]:
        """Get maintenance type by ID"""
        return self.db.get_single_row(
            "SELECT * FROM maintenance_types WHERE id = ?",
            (type_id,)
        )
    
    def create_maintenance_type(self, name: str) -> int:
        """Create a new maintenance type"""
        return self.db.execute_update(
            "INSERT INTO maintenance_types (name) VALUES (?)",
            (name,)
        )
    
    def update_maintenance_type(self, type_id: int, name: str) -> int:
        """Update maintenance type"""
        return self.db.execute_update(
            "UPDATE maintenance_types SET name = ? WHERE id = ?",
            (name, type_id)
        )
    
    def delete_maintenance_type(self, type_id: int) -> int:
        """Delete a maintenance type"""
        return self.db.execute_update(
            "DELETE FROM maintenance_types WHERE id = ?",
            (type_id,)
        ) 