"""
حزمة واجهات المستخدم لنظام ERP
"""

from ui.admin.NEWaudit_window import AuditWindow
from ui.admin.NEWlogin_window import LoginWindow
from ui.admin.NEWlookup_window import LookupWindow
from ui.admin.NEWpermissions_window import PermissionsWindow
from ui.admin.NEWreset_password_window import ResetPasswordWindow
from ui.admin.NEWroles_window import RolesWindow
from ui.admin.NEWsetting_window import SettingWindow
from ui.admin.NEWuser_management import UserManagementWindow

__all__ = [
    'AuditWindow',
    'LoginWindow',
    'LookupWindow',  # أضفت فاصلة هنا
    'PermissionsWindow',
    'ResetPasswordWindow',
    'RolesWindow',
    'SettingWindow',
    'UserManagementWindow'
]