import sqlite3
import os
import threading

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()  # Thread-local storage for connections
        self.initialize_db()
        self.update_fields_table()
        self.update_storage_table()
        self.update_storage_conditions_table()
        self.update_soil_data_table()
    
    def _get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable WAL mode for better concurrent access
            self._local.connection.execute('PRAGMA journal_mode=WAL')
            # Optimize for better performance
            self._local.connection.execute('PRAGMA synchronous=NORMAL')
            self._local.connection.execute('PRAGMA cache_size=10000')
            self._local.connection.execute('PRAGMA temp_store=MEMORY')
        return self._local.connection
    
    def _execute_query(self, query, params=None, fetchone=False, fetchall=False):
        """Execute a query using connection pooling"""
        conn = self._get_connection()
        c = conn.cursor()
        try:
            if params:
                c.execute(query, params)
            else:
                c.execute(query)
            conn.commit()
            if fetchone:
                return c.fetchone()
            elif fetchall:
                return c.fetchall()
            return None
        except Exception as e:
            conn.rollback()
            raise e

    def initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Optimize database settings
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA synchronous=NORMAL')
        c.execute('PRAGMA cache_size=10000')
        c.execute('PRAGMA temp_store=MEMORY')
        
        # Try to delete from sqlite_sequence if it exists
        try:
            c.execute("DELETE FROM sqlite_sequence WHERE name='storage'")
            c.execute("DELETE FROM sqlite_sequence WHERE name='fields'")
        except sqlite3.OperationalError:
            # sqlite_sequence table doesn't exist, which is fine
            pass
        
        c.execute('''CREATE TABLE IF NOT EXISTS fields (
                id INTEGER PRIMARY KEY ,
                name TEXT,
                size REAL,
                crop TEXT,
                sowing_date TEXT,
                fertilizer_type TEXT,
                fertilizer_dates TEXT,
                humidity REAL,
                rainfall REAL,
                wind REAL,
                pressure REAL,
                image_url TEXT,
                latitude REAL,
                longitude REAL,
                polygon_geojson TEXT,
                area_sqm REAL,
                area_acres REAL
            )''')


        c.execute('''CREATE TABLE IF NOT EXISTS storage (
                id INTEGER PRIMARY KEY ,
                name TEXT,
                seed_type TEXT,
                seed_amount REAL,
                fertilizer_amount REAL,
                pesticide_amount REAL,
                latitude REAL,
                longitude REAL
            )''')

        c.execute('''CREATE TABLE IF NOT EXISTS soil_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            timestamp TEXT,
            moisture REAL,
            temperature REAL,
            air_humidity REAL,
            FOREIGN KEY (field_id) REFERENCES fields (id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS storage_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_id INTEGER,
            timestamp TEXT,
            humidity REAL,
            temperature REAL,
            FOREIGN KEY (storage_id) REFERENCES storage (id)
        )''')
        conn.commit()
        conn.close()

    def save_field(self, field_data):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO fields (name, size, crop, sowing_date, fertilizer_type, fertilizer_dates,
                   humidity, rainfall, wind, pressure, image_url, latitude, longitude, polygon_geojson, area_sqm, area_acres)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', field_data)
        conn.commit()

    def update_field(self, field_data, field_id):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''UPDATE fields SET
            name=?, size=?, crop=?, sowing_date=?, fertilizer_type=?, fertilizer_dates=?,
            humidity=?, rainfall=?, wind=?, pressure=?, image_url=?, latitude=?, longitude=?, polygon_geojson=?, area_sqm=?, area_acres=?
            WHERE id=?''', (*field_data, field_id))
        conn.commit()

    def get_field(self, field_id):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM fields WHERE id = ?", (field_id,))
        field = c.fetchone()
        return field

    def get_all_fields(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, latitude, longitude, polygon_geojson FROM fields")
        fields = c.fetchall()
        return fields
    
    def get_all_fields_with_details(self):
        """Get all fields with full details in a single query - optimized for field_view"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM fields")
        fields = c.fetchall()
        return fields

    def delete_field(self, field_id):
        """
        Delete a field and all its related data (cascade delete).
        This includes:
        - All soil_data records associated with the field
        - The field record itself
        
        Returns:
            Tuple (latitude, longitude) of the deleted field, or None if field not found
        """
        conn = self._get_connection()
        c = conn.cursor()
        try:
            # Get field coordinates before deletion
            c.execute("SELECT latitude, longitude FROM fields WHERE id = ?", (field_id,))
            result = c.fetchone()
            
            if result:
                # Delete all related soil_data records first (cascade delete)
                c.execute("DELETE FROM soil_data WHERE field_id = ?", (field_id,))
                
                # Delete the field itself
                c.execute("DELETE FROM fields WHERE id = ?", (field_id,))
                
                conn.commit()
                return result
            else:
                # Field not found
                conn.commit()
                return None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting field {field_id}: {e}")
            return None

    def save_storage(self, storage_data):
        conn = self._get_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO storage
                        (name, seed_type, seed_amount, fertilizer_amount, pesticide_amount, latitude, longitude)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', storage_data)
            storage_id = c.lastrowid
            conn.commit()
            return storage_id
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
            return None


    def get_all_storages(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, latitude, longitude FROM storage")
        storages = c.fetchall()
        return storages

    def get_storage(self, storage_id):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM storage WHERE id = ?", (storage_id,))
        storage = c.fetchone()
        return storage

    def update_storage(self, storage_data, storage_id):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''UPDATE storage SET
                    name=?, seed_type=?, seed_amount=?, fertilizer_amount=?,
                    pesticide_amount=?, latitude=?, longitude=?
                    WHERE id=?''', (*storage_data, storage_id))
        conn.commit()

    def update_storage_table(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("PRAGMA table_info(storage)")
        columns = [column[1] for column in c.fetchall()]
        if "latitude" not in columns:
            c.execute("ALTER TABLE storage ADD COLUMN latitude REAL")
        if "longitude" not in columns:
            c.execute("ALTER TABLE storage ADD COLUMN longitude REAL")
        conn.commit()

    def update_fields_table(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("PRAGMA table_info(fields)")
        columns = [column[1] for column in c.fetchall()]
        if "polygon_geojson" not in columns:
            try:
                c.execute("ALTER TABLE fields ADD COLUMN polygon_geojson TEXT")
            except Exception:
                pass
        if "area_sqm" not in columns:
            try:
                c.execute("ALTER TABLE fields ADD COLUMN area_sqm REAL")
            except Exception:
                pass
        if "area_acres" not in columns:
            try:
                c.execute("ALTER TABLE fields ADD COLUMN area_acres REAL")
            except Exception:
                pass
        conn.commit()

    def delete_storage(self, storage_id):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT latitude, longitude FROM storage WHERE id = ?", (storage_id,))
        result = c.fetchone()
        c.execute("DELETE FROM storage WHERE id = ?", (storage_id,))
        conn.commit()
        return result

    def get_distinct_crops(self):
        """Return a list of distinct crop names from fields table."""
        conn = self._get_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT DISTINCT crop FROM fields WHERE crop IS NOT NULL AND TRIM(crop) != '' ORDER BY crop")
            rows = c.fetchall()
            return [r[0] for r in rows]
        except Exception:
            return []

    def update_storage_conditions_table(self):
        """Update storage_conditions table structure if needed"""
        conn = self._get_connection()
        c = conn.cursor()
        try:
            # Table is created in initialize_db, just check if exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='storage_conditions'")
            if not c.fetchone():
                # Table doesn't exist, create it
                c.execute('''CREATE TABLE IF NOT EXISTS storage_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    storage_id INTEGER,
                    timestamp TEXT,
                    humidity REAL,
                    temperature REAL,
                    FOREIGN KEY (storage_id) REFERENCES storage (id)
                )''')
                conn.commit()
        except Exception as e:
            print(f"Error updating storage_conditions table: {e}")

    def update_soil_data_table(self):
        """Update soil_data table structure if needed"""
        conn = self._get_connection()
        c = conn.cursor()
        try:
            c.execute("PRAGMA table_info(soil_data)")
            columns = [column[1] for column in c.fetchall()]
            # Add air_humidity column if it doesn't exist
            if "air_humidity" not in columns:
                c.execute("ALTER TABLE soil_data ADD COLUMN air_humidity REAL")
                conn.commit()
        except Exception as e:
            print(f"Error updating soil_data table: {e}")

    def save_soil_data(self, field_id, moisture, temperature=None, air_humidity=None):
        """
        Save soil data to database.
        
        Args:
            field_id: Field ID
            moisture: Soil moisture value (soil humidity)
            temperature: Temperature value (optional)
            air_humidity: Air humidity value (optional)
        """
        conn = self._get_connection()
        c = conn.cursor()
        try:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            c.execute('''INSERT INTO soil_data 
                        (field_id, timestamp, moisture, temperature, air_humidity)
                        VALUES (?, ?, ?, ?, ?)''',
                     (field_id, timestamp, moisture, temperature, air_humidity))
            conn.commit()
        except Exception as e:
            print(f"Error saving soil data: {e}")
            conn.rollback()

    def get_soil_data(self, field_id, limit=100, start_time=None):
        """
        Get soil data for a specific field.
        
        Args:
            field_id: Field ID
            limit: Maximum number of records to return (default: 100)
            start_time: Start time for filtering (datetime object, optional)
        
        Returns:
            List of soil data records
        """
        conn = self._get_connection()
        c = conn.cursor()
        try:
            if start_time:
                from datetime import datetime
                if isinstance(start_time, datetime):
                    start_time_str = start_time.isoformat()
                else:
                    start_time_str = start_time
                c.execute('''SELECT * FROM soil_data 
                            WHERE field_id = ? AND timestamp >= ?
                            ORDER BY timestamp DESC LIMIT ?''',
                         (field_id, start_time_str, limit))
            else:
                c.execute('''SELECT * FROM soil_data 
                            WHERE field_id = ?
                            ORDER BY timestamp DESC LIMIT ?''',
                         (field_id, limit))
            data = c.fetchall()
            return data
        except Exception as e:
            print(f"Error getting soil data: {e}")
            return []

    def get_latest_soil_data(self, field_id):
        """
        Get the latest soil data for a specific field.
        
        Args:
            field_id: Field ID
        
        Returns:
            Latest soil data record or None
        """
        conn = self._get_connection()
        c = conn.cursor()
        try:
            c.execute('''SELECT * FROM soil_data 
                        WHERE field_id = ?
                        ORDER BY timestamp DESC LIMIT 1''',
                     (field_id,))
            data = c.fetchone()
            return data
        except Exception as e:
            print(f"Error getting latest soil data: {e}")
            return None

    def get_soil_data_range(self, field_id, start_time, end_time):
        """
        Get soil data for a specific field within a time range.
        
        Args:
            field_id: Field ID
            start_time: Start time (datetime object or ISO string)
            end_time: End time (datetime object or ISO string)
        
        Returns:
            List of soil data records
        """
        conn = self._get_connection()
        c = conn.cursor()
        try:
            from datetime import datetime
            if isinstance(start_time, datetime):
                start_time_str = start_time.isoformat()
            else:
                start_time_str = start_time
            if isinstance(end_time, datetime):
                end_time_str = end_time.isoformat()
            else:
                end_time_str = end_time
            c.execute('''SELECT * FROM soil_data 
                        WHERE field_id = ? AND timestamp >= ? AND timestamp <= ?
                        ORDER BY timestamp ASC''',
                     (field_id, start_time_str, end_time_str))
            data = c.fetchall()
            return data
        except Exception as e:
            print(f"Error getting soil data range: {e}")
            return []

