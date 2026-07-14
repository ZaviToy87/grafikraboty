# -*- coding: utf-8 -*-
"""
VK Verification - отправка кодов верификации через VK
"""
import random
import time
import os
import json

# Пытаемся импортировать vk_bot
try:
    import vk_bot
    VK_AVAILABLE = True
except Exception:
    VK_AVAILABLE = False
    print("[VK Verification] vk_bot не доступен")

# Хранилище кодов (в памяти)
_verification_codes = {}

def _get_codes_file():
    """Получить путь к файлу хранения кодов."""
    try:
        from app_paths import DATA_DIR
        return os.path.join(DATA_DIR, "vk_codes.json")
    except ImportError:
        return "vk_codes.json"

def _load_codes():
    """Загрузить коды из файла."""
    global _verification_codes
    codes_file = _get_codes_file()
    if os.path.exists(codes_file):
        try:
            with open(codes_file, "r", encoding="utf-8") as f:
                _verification_codes = json.load(f)
        except Exception:
            _verification_codes = {}

def _save_codes():
    """Сохранить коды в файл."""
    codes_file = _get_codes_file()
    try:
        with open(codes_file, "w", encoding="utf-8") as f:
            json.dump(_verification_codes, f, ensure_ascii=False)
    except Exception as e:
        print(f"[VK Verification] Ошибка сохранения: {e}")

def _generate_code():
    """Сгенерировать 4-значный код."""
    return str(random.randint(1000, 9999))

def _cleanup_old_codes():
    """Удалить старые коды (старше 5 минут)."""
    now = time.time()
    to_delete = []
    for username, data in _verification_codes.items():
        if now - data.get("timestamp", 0) > 300:  # 5 минут
            to_delete.append(username)
    for username in to_delete:
        del _verification_codes[username]
    if to_delete:
        _save_codes()

def request_verification_code(username):
    """
    Request verification code via VK.

    Args:
        username: Username (admin, валерия, ольга)

    Returns:
        dict: {'success': True/False, 'message': '...'}
    """
    print(f"[VK VERIFY] >>> Request for username='{username}'")
    
    if not VK_AVAILABLE:
        print("[VK VERIFY] <<< VK bot not available")
        return {'success': False, 'message': 'VK bot not configured'}

    config = vk_bot.get_config()
    if not config or not config.get('service_token'):
        print("[VK VERIFY] <<< VK token not configured")
        return {'success': False, 'message': 'VK token not configured'}

    # Load codes
    _load_codes()
    _cleanup_old_codes()

    # Generate code
    code = _generate_code()
    print(f"[VK VERIFY] Generated code={code}")

    # Save code with timestamp
    _verification_codes[username] = {
        "code": code,
        "timestamp": time.time()
    }
    _save_codes()
    print(f"[VK VERIFY] Code saved for {username}")

    # Get VK ID
    vk_id = None
    user_map = config.get("vk_user_map", {})
    admin_vk_id = config.get("admin_vk_id")
    
    print(f"[VK VERIFY] Looking for VK ID: admin_vk_id={admin_vk_id}, user_map={user_map}")

    # For admin use admin_vk_id directly
    if username.lower() == "admin":
        if admin_vk_id:
            vk_id = admin_vk_id
            print(f"[VK VERIFY] Using admin_vk_id={vk_id}")
        else:
            # Try to find via map
            for vk_uid, uid in user_map.items():
                if uid == 1:
                    vk_id = int(vk_uid)
                    print(f"[VK VERIFY] Found vk_id={vk_id} from user_map")
                    break

    # For valeria and olga search in map
    elif username.lower() == "валерия":
        for vk_uid, uid in user_map.items():
            if uid == 2:
                vk_id = int(vk_uid)
                print(f"[VK VERIFY] Found valeria vk_id={vk_id}")
                break

    elif username.lower() == "ольга":
        for vk_uid, uid in user_map.items():
            if uid == 3:
                vk_id = int(vk_uid)
                print(f"[VK VERIFY] Found olga vk_id={vk_id}")
                break

    if not vk_id:
        msg = f'User "{username}" not found in VK. Check vk_config.json (admin_vk_id={admin_vk_id}, vk_user_map={user_map})'
        print(f"[VK VERIFY] <<< ERROR: {msg}")
        return {'success': False, 'message': msg}

    # Send code via VK
    message = (
        f"🔐 VERIFICATION CODE VetGid\n\n"
        f"User: {username}\n"
        f"Your code: {code}\n\n"
        f"Code valid for 5 minutes."
    )
    
    print(f"[VK VERIFY] Sending message to vk_id={vk_id}")

    try:
        result = vk_bot.send_message(
            user_id=int(vk_id),
            message=message
        )
        print(f"[VK VERIFY] send_message result={result}")
        if result:
            print(f"[VK VERIFY] <<< SUCCESS: Message sent to vk_id={vk_id}")
            return {'success': True, 'message': 'Code sent via VK'}
        else:
            print(f"[VK VERIFY] <<< FAILED: send_message returned {result}")
            return {'success': False, 'message': 'Failed to send message'}
    except Exception as e:
        print(f"[VK VERIFY] <<< EXCEPTION: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}

def verify_code(username, code):
    """
    Verify verification code.

    Args:
        username: Username
        code: 4-digit code

    Returns:
        dict: {'success': True/False, 'message': '...', 'user_id': int}
    """
    print(f"[VK VERIFY] verify_code: username={username}, code={code}")
    _load_codes()
    _cleanup_old_codes()

    if username not in _verification_codes:
        print(f"[VK VERIFY] <<< Code not requested for {username}")
        return {'success': False, 'message': 'Code not requested'}

    stored = _verification_codes[username]
    print(f"[VK VERIFY] Stored code={stored.get('code')}, timestamp={stored.get('timestamp')}")

    # Check code
    if stored["code"] != code:
        print(f"[VK VERIFY] <<< Wrong code: expected {stored['code']}, got {code}")
        return {'success': False, 'message': 'Wrong code'}

    # Check time (5 minutes)
    if time.time() - stored.get("timestamp", 0) > 300:  # 5 minutes
        del _verification_codes[username]
        _save_codes()
        print(f"[VK VERIFY] <<< Code expired")
        return {'success': False, 'message': 'Code expired'}

    # Delete used code
    del _verification_codes[username]
    _save_codes()
    print(f"[VK VERIFY] Code verified successfully")

    # Get user_id for login
    config = vk_bot.get_config()
    user_map = config.get("vk_user_map", {})
    user_id = None

    for vk_uid, uid in user_map.items():
        if uid == 1 and username == "admin":
            user_id = 1
            break
        elif uid == 2 and username == "валерия":
            user_id = 2
            break
        elif uid == 3 and username == "ольга":
            user_id = 3
            break

    if not user_id:
        user_id = 1  # Default to admin

    print(f"[VK VERIFY] <<< SUCCESS: user_id={user_id}")
    return {
        'success': True,
        'message': 'Verification successful',
        'user_id': user_id,
        'username': username
    }

if __name__ == "__main__":
    print("Тест VK Verification...")
    print("=" * 50)
    
    # Тест запроса кода
    result = request_verification_code("admin")
    print(f"Запрос кода: {result}")
    
    if result.get('success'):
        print("\nВведите код из VK:")
        test_code = input("> ")
        
        # Тест проверки кода
        result = verify_code("admin", test_code)
        print(f"Проверка кода: {result}")
