import sqlite3
import bcrypt
import os
import getpass

# --- تأكد من أن هذا المسار صحيح ---
# يفترض هذا السكربت أنه يعمل من المجلد الجذر للمشروع
DB_PATH = os.path.join('data', 'users.db')

def hash_password(password):
    """تشفير كلمة المرور باستخدام bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def reset_user_password(db_path, username, new_password):
    """الاتصال بقاعدة البيانات وتحديث كلمة المرور للمستخدم المحدد."""
    if not os.path.exists(db_path):
        print(f"خطأ: ملف قاعدة البيانات غير موجود في المسار '{db_path}'")
        print("الرجاء تشغيل السكربت من المجلد الجذر لمشروعك.")
        return

    new_hashed_password = hash_password(new_password)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # تحديث كلمة المرور للمستخدم المحدد
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hashed_password, username))

        if cursor.rowcount == 0:
            print(f"خطأ: المستخدم '{username}' غير موجود في قاعدة البيانات. لم يتم تغيير شيء.")
        else:
            conn.commit()
            print(f"✅ نجاح! تم إعادة تعيين كلمة المرور للمستخدم '{username}'.")
            print("يمكنك الآن تشغيل البرنامج الرئيسي وتسجيل الدخول بكلمة المرور الجديدة.")

    except sqlite3.Error as e:
        print(f"خطأ في قاعدة البيانات: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("--- أداة إعادة تعيين كلمة المرور ---")
    user_to_reset = input("أدخل اسم المستخدم الذي تريد إعادة تعيين كلمة مروره (e.g., admin): ").strip()
    
    if user_to_reset:
        # استخدام getpass لإخفاء كلمة المرور أثناء الكتابة
        password = getpass.getpass(f"أدخل كلمة المرور الجديدة للمستخدم '{user_to_reset}': ")
        if password:
            reset_user_password(DB_PATH, user_to_reset, password)
        else:
            print("كلمة المرور لا يمكن أن تكون فارغة. تم إلغاء العملية.")
    else:
        print("اسم المستخدم لا يمكن أن يكون فارغًا. تم إلغاء العملية.")