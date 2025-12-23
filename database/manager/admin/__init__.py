"""
حزمة مديري قاعدة البيانات للإدارة
توفر وحدات لإدارة المستخدمين، الأدوار، الصلاحيات، الإعدادات،
المراجعات (التدقيق)، والجداول المرجعية (lookup tables).
"""

# 🟢 إدارة المستخدمين
from database.manager.admin.NEWuser_manager import NEWUserManager

# 🟢 إدارة الصلاحيات
from database.manager.admin.NEWpermission_manager import NEWPermissionManager

# 🟢 إدارة الأدوار
try:
    from database.manager.admin.NEWrole_manager import NEWRoleManager
except ImportError:
    RoleManager = None

# 🟢 إدارة المراجعات (Audit logs)
try:
    from database.manager.admin.NEWaudit_manager import NEWAuditManager
except ImportError:
    AuditManager = None

# 🟢 إدارة الإعدادات العامة للنظام
try:
    from database.manager.admin.NEWsettings_manager import NEWSettingsManager
except ImportError:
    SettingManager = None

# 🟢 إدارة الجداول المرجعية (Lookup tables)
try:
    from database.manager.admin.NEWlookup_manager import NEWLookupManager
except ImportError:
    LookupManager = None


__all__ = [
    "NEWUserManager",
    "NEWPermissionManager",
    "NEWRoleManager",
    "NEWAuditManager",
    "NEWSettingManager",
    "NEWLookupManager",
]
