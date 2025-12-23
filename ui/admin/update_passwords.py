# update_passwords.py
# هذا سكربت يستخدم لمرة واحدة فقط لإنشاء المستخدمين وتصحيح كلمات المرور.

import sqlite3
import os
import sys

# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.admin.user_manager import UserManager
from database.db_connection import get_financials_db_connection

def run_user_setup_and_update():
    """
    يقوم بإنشاء المستخدمين الافتراضيين إذا لم يكونوا موجودين،
    ثم يقوم بتحديث كلمات مرورهم لضمان تطابق الهاش.
    """
    print("Starting user setup and password update script...")
    
    user_manager = UserManager(get_financials_db_connection)
    
    users_to_setup = {
        'admin': ('admin', '123', 'المدير العام', 1),
        'accountant': ('accountant', '123', 'المحاسب الرئيسي', 2),
        'user1': ('user1', '123', 'موظف إدخال فواتير', 3)
    }

    conn = None
    try:
        conn = get_financials_db_connection()
        if conn is None:
            print("ERROR: Could not connect to the database.")
            return

        cursor = conn.cursor()

        # --- الخطوة 1: محاولة إضافة المستخدمين (INSERT OR IGNORE) ---
        print("\n--- Step 1: Ensuring default users exist ---")
        for username, data in users_to_setup.items():
            _, password, full_name, role_id = data
            # نستخدم هاش مؤقت هنا فقط للإضافة، سيتم تصحيحه في الخطوة التالية
            temp_hash = user_manager._hash_password(password)
            
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password_hash, full_name, role_id) 
                VALUES (?, ?, ?, ?)
            """, (username, temp_hash, full_name, role_id))
            
            if cursor.rowcount > 0:
                print(f"User '{username}' was not found and has been created.")
            else:
                print(f"User '{username}' already exists.")
        
        conn.commit()

        # --- الخطوة 2: تحديث كلمات المرور لضمان الهاش الصحيح ---
        print("\n--- Step 2: Updating passwords to the correct hash ---")
        for username, data in users_to_setup.items():
            _, password, _, _ = data
            correct_hash = user_manager._hash_password(password)
            
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (correct_hash, username))
            
            if cursor.rowcount > 0:
                print(f"Successfully updated password for user: '{username}'")
            else:
                # هذه الرسالة لا يجب أن تظهر الآن
                print(f"WARNING: User '{username}' not found for update (this should not happen).")

        conn.commit()
        print("\nUser setup and password update process completed successfully!")

    except sqlite3.Error as e:
        print(f"DATABASE ERROR: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- تشغيل السكربت ---
if __name__ == '__main__':
    run_user_setup_and_update()
