# database/manager/admin/session.py
current_user = None

def set_current_user(user_data: dict):
    global current_user
    current_user = user_data
    print(f"DEBUG: Session - User set: {user_data}")

def clear_current_user():
    global current_user
    current_user = None

def get_current_user():
    print(f"DEBUG: Session - Getting user: {current_user}")
    return current_user

def get_current_user_id():
    global current_user
    print(f"DEBUG: Session - Getting user ID: {current_user}")
    if current_user and 'id' in current_user:
        return current_user['id']
    return None

def get_current_user_name():
    global current_user
    print(f"DEBUG: Session - Getting user name: {current_user}")
    if current_user:
        if 'full_name' in current_user:
            return current_user['full_name']
        elif 'username' in current_user:
            return current_user['username']
        elif 'name' in current_user:
            return current_user['name']
    return "مستخدم غير معروف"