# backup_manager.py

import sqlite3
from database.connection_utils import get_project_root
import os
import shutil
import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QStyle,QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_file_dir = os.path.dirname(os.path.abspath(__file__))
# بما أن backup_manager.py في ui/tools، نحتاج للعودة مستويين للوصول إلى جذر المشروع
project_root = get_project_root()
if project_root not in sys.path:
    sys.path.append(project_root)
print(f"DEBUG: Project Root set to: {project_root}") # رسالة تصحيح جديدة

# استيراد مسارات قواعد البيانات من db_connection
# ملاحظة: سنقوم بتعديل هذه المسارات بعد الاستيراد لتشير إلى مجلد 'schems'
try:
    from database.db_connection import (
        DB_DIR as DB_CONN_BASE_DIR, # المسار الأساسي كما هو معرف في db_connection.py (مجلد database)
        FINANCIALS_DB_FILE as DB_CONN_FINANCIALS_DB_FILE_OLD,
        INVENTORY_DB_FILE as DB_CONN_INVENTORY_DB_FILE_OLD,
        FIXED_ASSETS_DB_FILE as DB_CONN_FIXED_ASSETS_DB_FILE_OLD,
        USERS_DB_FILE as DB_CONN_USERS_DB_FILE_OLD
    )
    print("DEBUG: Successfully imported DB paths from db_connection.py (as per db_connection's definition).")

    # الآن، سنقوم بتعريف المسار الصحيح حيث توجد ملفات .db فعليًا
    # بما أن db_connection.py في 'database/'، ومجلد 'schems' داخل 'database/'،
    # فإن المسار الصحيح هو 'project_root/database/schems/'
    DB_SCHEMAS_DIR = os.path.join(project_root, 'database', 'schems')
    print(f"DEBUG: Actual DB Schemas Directory set to: {DB_SCHEMAS_DIR}")

    # إعادة تعريف المسارات الكاملة لملفات قواعد البيانات باستخدام المسار الصحيح
    FINANCIALS_DB_FILE = os.path.join(DB_SCHEMAS_DIR, 'financials.db')
    INVENTORY_DB_FILE = os.path.join(DB_SCHEMAS_DIR, 'inventory.db')
    FIXED_ASSETS_DB_FILE = os.path.join(DB_SCHEMAS_DIR, 'fixed_assets.db')
    USERS_DB_FILE = os.path.join(DB_SCHEMAS_DIR, 'users.db')

    # قائمة بجميع مسارات قواعد البيانات التي سيتم نسخها احتياطيًا
    ALL_DB_FILES = [
        FINANCIALS_DB_FILE,
        INVENTORY_DB_FILE,
        FIXED_ASSETS_DB_FILE,
        USERS_DB_FILE
    ]
    # قاموس لربط أسماء قواعد البيانات الأصلية بمساراتها الكاملة
    DB_NAME_TO_PATH = {
        os.path.basename(FINANCIALS_DB_FILE): FINANCIALS_DB_FILE,
        os.path.basename(INVENTORY_DB_FILE): INVENTORY_DB_FILE,
        os.path.basename(FIXED_ASSETS_DB_FILE): FIXED_ASSETS_DB_FILE,
        os.path.basename(USERS_DB_FILE): USERS_DB_FILE,
    }
    print("DEBUG: DB file paths redefined for backup_manager's use to point to 'schems' folder.")

except ImportError as e:
    error_msg = (
        f"ملف db_connection.py أو مسارات قواعد البيانات غير موجودة. "
        f"تأكد من أن db_connection.py في مجلد database وأن المتغيرات معرفة. "
        f"خطأ الاستيراد: {e}"
    )
    QMessageBox.critical(None, "خطأ في الاستيراد", error_msg)
    print(f"ERROR: ImportError in backup_manager.py: {error_msg}")
    sys.exit(1)


class BackupManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("أداة النسخ الاحتياطي والاستيراد لقواعد البيانات")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(500, 350) # Increased height for new button
        self.backup_folder = ""

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("إدارة النسخ الاحتياطي والاستيراد")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # اختيار مجلد الحفظ (للنسخ الاحتياطي)
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("مجلد النسخ الاحتياطي:")
        self.folder_path_display = QLineEdit("الرجاء اختيار مجلد...")
        self.folder_path_display.setReadOnly(True)
        self.browse_button = QPushButton("استعراض...")
        self.browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.browse_button.clicked.connect(self.browse_for_folder)

        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path_display)
        folder_layout.addWidget(self.browse_button)
        main_layout.addLayout(folder_layout)

        # أزرار الإجراءات
        action_buttons_layout = QHBoxLayout()
        self.start_backup_btn = QPushButton("بدء النسخ الاحتياطي")
        self.start_backup_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.start_backup_btn.clicked.connect(self.start_backup_process)
        self.start_backup_btn.setEnabled(False) # معطلة حتى يتم اختيار مجلد

        self.restore_backup_btn = QPushButton("استيراد نسخة احتياطية")
        self.restore_backup_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.restore_backup_btn.clicked.connect(self.restore_backup_process)
        # زر الاستيراد لا يعتمد على مجلد النسخ الاحتياطي، لذا يمكن تفعيله دائمًا
        self.restore_backup_btn.setEnabled(True) 

        action_buttons_layout.addWidget(self.start_backup_btn)
        action_buttons_layout.addWidget(self.restore_backup_btn)
        main_layout.addLayout(action_buttons_layout)

        # شريط التقدم
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # رسالة الحالة
        self.status_label = QLabel("الانتظار لاختيار مجلد وبدء النسخ الاحتياطي أو الاستيراد...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #555; margin-top: 10px;")
        main_layout.addWidget(self.status_label)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #ECF0F1;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
                color: #34495E;
            }
            QLabel {
                font-weight: bold;
                color: #2C3E50;
            }
            QLineEdit {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
                color: #2C3E50;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: 1px solid #007bff;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #AAB7B8;
                border-color: #AAB7B8;
                color: #6C7A89;
            }
            QProgressBar {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                text-align: center;
                background-color: white;
                color: #2C3E50;
            }
            QProgressBar::chunk {
                background-color: #28a745; /* Green for progress */
                border-radius: 5px;
            }
            #restore_backup_btn { /* Specific style for restore button */
                background-color: #ffc107; /* Yellow/Orange */
                color: #343a40; /* Dark text for contrast */
                border-color: #ffc107;
            }
            #restore_backup_btn:hover {
                background-color: #e0a800;
                border-color: #e0a800;
            }
            #restore_backup_btn:pressed {
                background-color: #cc9900;
            }
        """)
        self.restore_backup_btn.setObjectName("restore_backup_btn") # Set object name for specific styling

    def browse_for_folder(self):
        """يفتح مربع حوار لاختيار مجلد النسخ الاحتياطي."""
        folder = QFileDialog.getExistingDirectory(self, "اختر مجلد النسخ الاحتياطي")
        if folder:
            self.backup_folder = folder
            self.folder_path_display.setText(folder)
            self.start_backup_btn.setEnabled(True)
            self.status_label.setText(f"مجلد النسخ الاحتياطي المحدد: {folder}")
        else:
            self.backup_folder = ""
            self.folder_path_display.setText("الرجاء اختيار مجلد...")
            self.start_backup_btn.setEnabled(False)
            self.status_label.setText("الانتظار لاختيار مجلد وبدء النسخ الاحتياطي أو الاستيراد...")

    def start_backup_process(self):
        """يبدأ عملية النسخ الاحتياطي لجميع قواعد البيانات."""
        if not self.backup_folder:
            QMessageBox.warning(self, "مجلد غير محدد", "الرجاء اختيار مجلد للنسخ الاحتياطي أولاً.")
            return

        # تعطيل الأزرار أثناء العملية
        self.start_backup_btn.setEnabled(False)
        self.restore_backup_btn.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.status_label.setText("بدء عملية النسخ الاحتياطي...")
        QApplication.processEvents() # تحديث الواجهة

        total_dbs = len(ALL_DB_FILES)
        if total_dbs == 0:
            self.status_label.setText("لا توجد قواعد بيانات للنسخ الاحتياطي.")
            self.progress_bar.setValue(100)
            self.start_backup_btn.setEnabled(True)
            self.restore_backup_btn.setEnabled(True)
            self.browse_button.setEnabled(True)
            return

        success_count = 0
        error_messages = []

        for i, db_path in enumerate(ALL_DB_FILES):
            db_name = os.path.basename(db_path)
            self.status_label.setText(f"جاري نسخ: {db_name} احتياطيًا...")
            QApplication.processEvents() # تحديث الواجهة

            try:
                # إنشاء اسم ملف النسخة الاحتياطية مع الطابع الزمني
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{os.path.splitext(db_name)[0]}_{timestamp}.db"
                backup_full_path = os.path.join(self.backup_folder, backup_filename)

                # التأكد من وجود مجلد قاعدة البيانات المصدر
                if not os.path.exists(db_path):
                    error_messages.append(f"خطأ: ملف قاعدة البيانات '{db_name}' غير موجود في المسار المتوقع: {db_path}") # Added db_path to error
                    continue

                # نسخ الملف
                shutil.copy2(db_path, backup_full_path)
                success_count += 1
                print(f"DEBUG: تم نسخ {db_name} احتياطيًا إلى {backup_full_path}")

            except Exception as e:
                error_messages.append(f"فشل نسخ {db_name} احتياطيًا: {e}")
                print(f"ERROR: Failed to backup {db_name}: {e}")
            
            # تحديث شريط التقدم
            progress = int(((i + 1) / total_dbs) * 100)
            self.progress_bar.setValue(progress)
            QApplication.processEvents() # تحديث الواجهة

        # انتهاء العملية
        self.start_backup_btn.setEnabled(True)
        self.restore_backup_btn.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.progress_bar.setValue(100)

        if success_count == total_dbs:
            QMessageBox.information(self, "نجاح النسخ الاحتياطي", "تم إنشاء نسخة احتياطية لجميع قواعد البيانات بنجاح!")
            self.status_label.setText("اكتمل النسخ الاحتياطي بنجاح.")
        else:
            QMessageBox.warning(self, "النسخ الاحتياطي غير مكتمل", 
                                f"تم نسخ {success_count} من {total_dbs} قواعد بيانات احتياطيًا.\n"
                                "حدثت الأخطاء التالية:\n" + "\n".join(error_messages))
            self.status_label.setText("اكتمل النسخ الاحتياطي مع أخطاء.")

    def restore_backup_process(self):
        """
        يسمح للمستخدم باختيار ملف نسخة احتياطية ويقوم باستعادته.
        """
        self.status_label.setText("الانتظار لاختيار ملف النسخة الاحتياطية...")
        QApplication.processEvents()

        # فتح مربع حوار لاختيار ملف النسخة الاحتياطية
        backup_file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية", "", "SQLite Database Files (*.db);;All Files (*)"
        )

        if not backup_file_path:
            self.status_label.setText("تم إلغاء عملية الاستيراد.")
            return

        backup_filename = os.path.basename(backup_file_path)
        
        # محاولة استنتاج اسم قاعدة البيانات الأصلية من اسم ملف النسخة الاحتياطية
        # نفترض أن اسم النسخة الاحتياطية هو "original_name_YYYYMMDD_HHMMSS.db"
        parts = backup_filename.split('_')
        
        # تحقق من أن هناك أجزاء كافية لاستنتاج اسم قاعدة البيانات الأصلي
        if len(parts) < 2: 
            QMessageBox.critical(self, "خطأ في الاستيراد", 
                                 f"لا يمكن تحديد قاعدة البيانات الأصلية من اسم الملف: {backup_filename}\n"
                                 "يرجى التأكد من أن اسم الملف يتبع التنسيق المتوقع (مثال: financials_YYYYMMDD_HHMMSS.db).")
            self.status_label.setText("فشل الاستيراد: اسم ملف غير صالح.")
            return

        original_db_name_base = parts[0] # e.g., 'financials'
        original_db_name = f"{original_db_name_base}.db" # e.g., 'financials.db'

        target_db_path = DB_NAME_TO_PATH.get(original_db_name)

        if not target_db_path:
            QMessageBox.critical(self, "خطأ في الاستيراد", 
                                 f"لا يمكن تحديد قاعدة البيانات الأصلية من اسم الملف: {backup_filename}\n"
                                 "يرجى التأكد من أن اسم الملف يتبع التنسيق المتوقع (مثال: financials_YYYYMMDD_HHMMSS.db).")
            self.status_label.setText("فشل الاستيراد: اسم ملف غير صالح.")
            return

        # تأكيد من المستخدم قبل الاستعادة
        reply = QMessageBox.question(self, "تأكيد الاستيراد",
                                     f"أنت على وشك استعادة قاعدة البيانات '{original_db_name}'\n"
                                     f"من الملف:\n'{backup_file_path}'\n\n"
                                     "هذه العملية ستقوم بالكتابة فوق قاعدة البيانات الحالية.\n"
                                     "هل أنت متأكد أنك تريد المتابعة؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            self.status_label.setText("تم إلغاء عملية الاستيراد بواسطة المستخدم.")
            return

        # تعطيل الأزرار أثناء العملية
        self.start_backup_btn.setEnabled(False)
        self.restore_backup_btn.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"جاري استعادة: {original_db_name} من {backup_filename}...")
        QApplication.processEvents()

        try:
            # التأكد من إغلاق أي اتصالات مفتوحة بقاعدة البيانات المستهدفة
            # هذا جزء حاسم، وإلا ستفشل عملية النسخ
            # في تطبيقات PyQt5، قد تحتاج إلى التأكد من أن أي Managers
            # أو اتصالات قاعدة بيانات أخرى لا تستخدم الملف المستهدف حاليًا.
            # (لا يمكن للكود هنا إغلاق الاتصالات المفتوحة في أجزاء أخرى من تطبيقك)
            
            shutil.copy2(backup_file_path, target_db_path)
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "نجاح الاستيراد", 
                                    f"تم استعادة قاعدة البيانات '{original_db_name}' بنجاح!")
            self.status_label.setText("اكتمل الاستيراد بنجاح.")
            print(f"DEBUG: تم استعادة {original_db_name} من {backup_file_path}")

        except Exception as e:
            self.progress_bar.setValue(0) # Reset progress on error
            QMessageBox.critical(self, "فشل الاستيراد", 
                                 f"فشل استعادة قاعدة البيانات '{original_db_name}'.\n"
                                 f"السبب: {e}\n\n"
                                 "تأكد من عدم استخدام قاعدة البيانات حاليًا بواسطة أي برامج أخرى.")
            self.status_label.setText("فشل الاستيراد.")
            print(f"ERROR: Failed to restore {original_db_name}: {e}")
        finally:
            self.start_backup_btn.setEnabled(True)
            self.restore_backup_btn.setEnabled(True)
            self.browse_button.setEnabled(True)
            QApplication.processEvents()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BackupManagerWindow()
    window.show()
    sys.exit(app.exec_())