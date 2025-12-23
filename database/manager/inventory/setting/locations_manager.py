import os
import sys
import sqlite3
from typing import List, Dict, Optional

# --- تصحيح مسار المشروع الجذر ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)


class LocationManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """Establish a database connection."""
        return sqlite3.connect(self.db_path)

    def list_active_locations(self) -> List[Dict[str, str]]:
        """Retrieve all active locations."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, location_name_ar
                FROM store_locations  
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(zip(["id", "code", "location_name_ar"], row)) for row in rows]
        finally:
            conn.close()

    def create_location(self, code: str, name_ar: str) -> bool:
        """Create a new location."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO store_locations   (code, location_name_ar)
                VALUES (?, ?)
            """, (code, name_ar))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def update_location(self, location_id: int, code: str, name_ar: str) -> bool:
        """Update an existing location."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE store_locations  
                SET code = ?, location_name_ar = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, location_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def delete_location(self, location_id: int) -> bool:
        """Soft delete a location."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE store_locations  
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (location_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def location_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """Check if location with given code already exists."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            query = "SELECT 1 FROM store_locations   WHERE code = ? AND is_active = 1"
            params = [code]
            
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
                
            cursor.execute(query, params)
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()