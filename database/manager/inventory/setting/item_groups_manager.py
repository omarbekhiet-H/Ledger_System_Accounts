import sqlite3

class ItemGroupManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def list_active_groups(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.code, g.name_ar, g.name_en, g.description,
                   c.name_ar AS category_name
            FROM item_groups g
            LEFT JOIN item_categories c ON g.category_id = c.id
            WHERE g.is_active = 1
            ORDER BY g.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(["id", "code", "name_ar", "name_en", "description", "category_name"], row)) for row in rows]

    def create_group(self, code, name_ar, name_en, category_id, description):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO item_groups (code, name_ar, name_en, category_id, description)
                VALUES (?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, category_id, description))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def update_group(self, group_id, code, name_ar, name_en, category_id, description):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE item_groups
                SET code = ?, name_ar = ?, name_en = ?, category_id = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, category_id, description, group_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_group(self, group_id):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE item_groups
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (group_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
        
    def list_groups_by_category(self, category_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.code, g.name_ar, g.name_en, g.description,
               c.name_ar AS category_name
            FROM item_groups g
            LEFT JOIN item_categories c ON g.category_id = c.id
            WHERE g.is_active = 1 AND g.category_id = ?
            ORDER BY g.created_at DESC
        """, (category_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(["id", "code", "name_ar", "name_en", "description", "category_name"], row)) for row in rows]    