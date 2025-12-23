# database/manager/db_schema_manager.py

import sqlite3
import os
from PyQt5.QtWidgets import QMessageBox

# استيراد دوال الاتصال الجديدة والمحددة
from ..db_connection import (
    get_financials_db_connection,
    get_inventory_db_connection,
    get_fixed_assets_db_connection,
    get_users_db_connection
)

# استيراد سكريبتات المخططات
# تأكد من وجود هذه الملفات في مجلد database/schems/
from ..schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
from ..schems.inventory_schema import INVENTORY_SCHEMA_SCRIPT
from ..schems.fixed_assets_schema import FIXED_ASSETS_SCHEMA_SCRIPT # تم التصحيح هنا: من assets_schema إلى fixed_assets_schema
from ..schems.users_schema import USERS_SCHEMA_SCRIPT
from ..schems.general_core_schema import GENERAL_CORE_SCHEMA_SCRIPT

# استيراد دوال تعبئة البيانات الافتراضية
# تأكد من أن هذه الملفات موجودة في database/schems/default_data/
from ..schems.default_data.financials_data_population import insert_default_data as populate_financials_data
from ..schems.default_data.inventory_data_population import insert_default_data as populate_inventory_data
#from ..schems.default_data.assets_data_population import insert_default_data as populate_assets_data
#from ..schems.default_data.fixed_assets_data_population import insert_default_data as populate_general_core_data


class DBSchemaManager:
    """
    مسؤول عن إنشاء وتحديث مخططات قواعد البيانات وملء البيانات الافتراضية.
    تم تعديله للتعامل مع قواعد بيانات منفصلة.
    """
    def __init__(self):
        pass

    def _execute_schema_script(self, get_connection_func, schema_script, db_name):
        """
        دالة مساعدة لتنفيذ سكريبت مخطط على قاعدة بيانات محددة.
        """
        conn = None
        try:
            conn = get_connection_func()
            if conn is None:
                print(f"Failed to get connection for {db_name}.")
                return False
            cursor = conn.cursor()
            cursor.executescript(schema_script)
            conn.commit()
            print(f"Schema for {db_name} initialized successfully.")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, f"خطأ في إنشاء المخطط لـ {db_name}", f"خطأ عند إنشاء مخطط قاعدة بيانات {db_name}: {e}")
            print(f"Error creating schema for {db_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def create_all_schemas(self):
        """
        ينشئ جميع مخططات قواعد البيانات (الجداول) اللازمة لنظام ERP.
        """
        print("Starting database schema initialization...")
        success = True

        # إنشاء مخطط قاعدة بيانات المالية
        if not self._execute_schema_script(get_financials_db_connection, FINANCIALS_SCHEMA_SCRIPT, "financials.db"):
            success = False
        
        # إنشاء مخطط قاعدة بيانات المخزون
        if not self._execute_schema_script(get_inventory_db_connection, INVENTORY_SCHEMA_SCRIPT, "inventory.db"):
            success = False

        # إنشاء مخطط قاعدة بيانات الأصول الثابتة
        if not self._execute_schema_script(get_fixed_assets_db_connection, FIXED_ASSETS_SCHEMA_SCRIPT, "fixed_assets.db"):
            success = False

        # إنشاء مخطط قاعدة بيانات المستخدمين
        if not self._execute_schema_script(get_users_db_connection, USERS_SCHEMA_SCRIPT, "users.db"):
            success = False

        # إذا كان GENERAL_CORE_SCHEMA_SCRIPT يحتوي على جداول أساسية مشتركة (مثل جداول الإعدادات أو الصلاحيات العامة)
        # ومن المفترض أن تطبق على قاعدة بيانات المالية كجزء من المخطط العام.
        if not self._execute_schema_script(get_financials_db_connection, GENERAL_CORE_SCHEMA_SCRIPT, "financials.db - General Core"):
            success = False

        if success:
            print("All core database schemas initialized successfully.")
            return True
        else:
            print("One or more database schemas failed to initialize.")
            return False

    def populate_all_default_data(self):
        """
        تعبئة البيانات الافتراضية لجميع قواعد البيانات.
        يفترض أن المخططات قد تم إنشاؤها بالفعل.
        """
        print("Populating all default data...")
        try:
            conn_financials = get_financials_db_connection()
            if conn_financials:
                populate_financials_data(conn_financials)
                conn_financials.close()

            conn_inventory = get_inventory_db_connection()
            if conn_inventory:
                populate_inventory_data(conn_inventory)
                conn_inventory.close()

            #conn_assets = get_fixed_assets_db_connection()
            #if conn_assets:
            #    populate_assets_data(conn_assets)
            #    conn_assets.close()

            #conn_users = get_users_db_connection()
            #if conn_users:
            #    populate_general_core_data(conn_users)
            #    conn_users.close()

            print("All default data populated successfully.")
        except Exception as e:
            QMessageBox.critical(None, "خطأ في التعبئة الشاملة", f"خطأ عند تعبئة جميع البيانات الافتراضية: {e}")
            print(f"Error populating all default data: {e}")

    def initialize_specific_database(self, db_type: str):
        """
        تهيئة (إنشاء المخطط وتعبئة البيانات الافتراضية) لقاعدة بيانات محددة.

        Args:
            db_type (str): نوع قاعدة البيانات المراد تهيئتها (مثل 'financials', 'inventory', 'fixed_assets', 'users').
        """
        success = False
        conn = None
        db_name = ""
        conn_func = None
        schema_script = ""
        data_populator = None

        if db_type == 'financials':
            db_name = "Financials DB"
            conn_func = get_financials_db_connection
            schema_script = FINANCIALS_SCHEMA_SCRIPT
            data_populator = populate_financials_data
        elif db_type == 'inventory':
            db_name = "Inventory DB"
            conn_func = get_inventory_db_connection
            schema_script = INVENTORY_SCHEMA_SCRIPT
            data_populator = populate_inventory_data
        #elif db_type == 'fixed_assets':
        #    db_name = "Fixed Assets DB"
        #    conn_func = get_fixed_assets_db_connection
        #    schema_script = FIXED_ASSETS_SCHEMA_SCRIPT # تم التصحيح هنا
        #    data_populator = populate_assets_data
        #elif db_type == 'users':
        #    db_name = "Users DB"
        #    conn_func = get_users_db_connection
        #    schema_script = GENERAL_CORE_SCHEMA_SCRIPT
        #    data_populator = populate_general_core_data
        else:
            print(f"Unknown database type: {db_type}")
            QMessageBox.warning(None, "خطأ", f"نوع قاعدة البيانات غير معروف: {db_type}")
            return

        print(f"Initializing {db_name}...")
        # 1. إنشاء المخطط
        success = self._execute_schema_script(conn_func, schema_script, db_name)

        if success:
            # 2. تعبئة البيانات الافتراضية
            try:
                conn = conn_func()
                if conn:
                    data_populator(conn)
                    conn.close()
                    print(f"Default data for {db_name} populated successfully.")
                else:
                    print(f"Failed to get connection for {db_name} to populate data.")
                    QMessageBox.critical(None, "خطأ في الاتصال", f"فشل الاتصال بقاعدة بيانات {db_name} لتعبئة البيانات.")
            except Exception as e:
                print(f"Error populating default data for {db_name}: {e}")
                QMessageBox.critical(None, "خطأ في التعبئة", f"خطأ عند تعبئة البيانات الافتراضية لـ {db_name}: {e}")
        else:
            print(f"Schema creation failed for {db_name}. Skipping data population.")
            QMessageBox.critical(None, "خطأ في المخطط", f"فشل إنشاء مخطط {db_name}. تم تخطي تعبئة البيانات.")