# database/manager/company_settings_manager.py

import sqlite3
import os
import sys

# --- تصحيح مسار المشروع الجذر ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class CompanySettingsManager(BaseManager):
    """
    مسؤول عن حفظ واسترجاع إعدادات الشركة من قاعدة البيانات.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: CompanySettingsManager initialized from {__file__}.")

    def get_setting(self, key, default_value=None):
        """
        يجلب قيمة إعداد معين من قاعدة البيانات.
        """
        query = "SELECT setting_value, setting_type FROM company_settings WHERE setting_key = ?"
        result = self.fetch_one(query, (key,))
        
        if not result:
            return default_value

        value_str = result['setting_value']
        value_type = result['setting_type']

        # تحويل القيمة إلى نوعها الصحيح
        try:
            if value_type == 'integer':
                return int(value_str)
            elif value_type == 'float':
                return float(value_str)
            elif value_type == 'boolean':
                return value_str.lower() in ('true', '1', 't')
            else: # string
                return value_str
        except (ValueError, TypeError):
            return default_value

    def get_all_settings(self):
        """
        يجلب كل الإعدادات المخزنة في قاعدة البيانات.
        """
        all_settings_raw = self.fetch_all("SELECT * FROM company_settings")
        settings_dict = {}
        if all_settings_raw:
            for setting in all_settings_raw:
                key = setting['setting_key']
                # نستخدم دالة get_setting لضمان تحويل النوع بشكل صحيح
                settings_dict[key] = self.get_setting(key)
        return settings_dict


    def save_settings(self, settings_data):
        """
        يحفظ مجموعة من الإعدادات في قاعدة البيانات.
        يستخدم INSERT OR REPLACE لتحديث القيم الموجودة أو إضافة الجديدة.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return False
            
            cursor = conn.cursor()

            # تحضير البيانات لتكون قائمة من Tuples
            data_to_save = []
            for key, data in settings_data.items():
                if data['value'] is not None:
                # استخدم الأسماء الصحيحة للأعمدة هنا
                    data_to_save.append((key, str(data['value']), data['type']))

            if not data_to_save:
                return True

            # استخدام جملة INSERT OR REPLACE للتعامل مع الإضافة والتحديث معاً
            query = """
            INSERT OR REPLACE INTO company_settings (setting_key, setting_value, setting_type)
            VALUES (?, ?, ?)
            """
            
            # استخدام cursor.executemany لتنفيذ العملية على كل البيانات
            cursor.executemany(query, data_to_save)
            
            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Database error in save_settings: {e}")
            if conn:
                conn.rollback() # تراجع عن التغييرات في حالة حدوث خطأ
            return False
        finally:
            if conn:
                conn.close()
