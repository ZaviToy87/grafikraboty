# -*- coding: utf-8 -*-
"""
main_launcher.py - Единый запускатель: серверы + веб + десктопный клиент
"""

import sys
import os
import re
import json
import threading
import time
import socket
import subprocess
import webbrowser
import urllib.request
from urllib.parse import quote

# Импорт модуля уведомлений (если есть)
try:
    import notifications
except ImportError:
    notifications = None

# Текущая папка проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# VK интеграция (параллельно с Telegram)
try:
    import vk_startup
    VK_ENABLED = True
except Exception:
    VK_ENABLED = False

# Процесс десктопного клиента (для завершения при выходе)
_client_process = None
_tunnel_process = None

# Выход по кнопке «Выход» в трее
_tray_exit = False


def get_local_ip():
    """Локальный IP в сети (для доступа в той же Wi-Fi/локалке)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_public_ip():
    """Внешний (публичный) IP — для доступа из интернета (нужен проброс порта 8080 на роутере)."""
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "http://icanhazip.com"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ip = (r.read().decode() or "").strip()
                if ip and len(ip) < 20:
                    return ip
        except Exception:
            continue
    return None


def check_port(port):
    """Проверить, свободен ли порт (True = свободен, False = занят/слушает)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        return result != 0
    finally:
        sock.close()


def wait_for_port(port, timeout_sec=15):
    """Ждать, пока порт начнёт слушать (сервер поднимется). Возвращает True, если порт занят."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not check_port(port):  # порт занят — сервер слушает
            return True
        time.sleep(0.4)
    return False


def _try_free_port(port):
    """Попытаться освободить порт (завершить процесс). Работает на Windows. Возвращает True если порт освобождён."""
    if sys.platform != 'win32':
        return False
    try:
        cmd = [
            'powershell', '-NoProfile', '-NonInteractive', '-Command',
            '$c = Get-NetTCPConnection -LocalPort %d -State Listen -ErrorAction SilentlyContinue;'
            'if ($c) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue };'
            'Start-Sleep -Seconds 2' % port
        ]
        subprocess.run(cmd, capture_output=True, timeout=15, cwd=BASE_DIR)
        time.sleep(0.5)
        return check_port(port)
    except Exception:
        return False


def start_socket_server():
    """Запустить socket сервер"""
    try:
        print("🔧 Импорт модулей socket сервера...")
        import server
        print("✅ Модули импортированы")
        print("🔌 Запуск socket сервера на порту 5000...")
        server_instance = server.ScheduleServer()
        server_instance.start()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Ошибка запуска socket сервера: {e}")
        import traceback
        traceback.print_exc()


def start_web_server():
    """Запустить веб-сервер"""
    try:
        print("🔧 Импорт модулей веб-сервера...")
        import web_server as ws_mod
        app = ws_mod.app
        socketio = ws_mod.socketio
        print("✅ Модули импортированы (web_server: %s)" % getattr(ws_mod, "__file__", "?"))
        print("🌐 Запуск веб-сервера на порту 8080...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что установлены все зависимости:")
        print("   pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")
        import traceback
        traceback.print_exc()


def _load_telegram_config():
    """Загрузить токен и chat_ids для Telegram (сначала папка данных, затем папка приложения)."""
    try:
        from app_paths import DATA_DIR
        for folder in (DATA_DIR, BASE_DIR):
            path = os.path.join(folder, "telegram_config.json")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                token = (data.get("bot_token") or data.get("token") or "").strip()
                ids = data.get("chat_ids") or data.get("chat_id")
                if ids is None:
                    ids = []
                if isinstance(ids, (int, str)):
                    ids = [str(ids)]
                ids = [str(x).strip() for x in ids if str(x).strip()]
                tunnel_open_base = (data.get("tunnel_open_base") or "").strip().rstrip("/")
                return token, ids, path, tunnel_open_base
    except Exception:
        pass
    return None, [], None, ""


def _send_telegram(bot_token, chat_ids, text):
    """Отправить сообщение в Telegram с retry и обходом SSL проблем."""
    if not bot_token or not chat_ids:
        return False
    if isinstance(chat_ids, str):
        chat_ids = [chat_ids]
    
    url = "https://api.telegram.org/bot%s/sendMessage" % bot_token
    sent = 0
    
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    for cid in chat_ids:
        for attempt in range(3):
            try:
                data = json.dumps({
                    "chat_id": str(cid).strip(), 
                    "text": text, 
                    "disable_web_page_preview": True
                }).encode("utf-8")
                req = urllib.request.Request(url, data=data, method="POST", 
                                            headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as r:
                    if 200 <= r.status < 300:
                        sent += 1
                        break
            except urllib.error.URLError as e:
                reason = str(e.reason).lower()
                if "ssl" in reason or "timeout" in reason or "handshake" in reason:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                print(f"⚠️ Telegram ошибка (попытка {attempt+1}/3): {e}")
            except Exception as e:
                print(f"⚠️ Telegram ошибка (попытка {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue
        break  # переходим к следующему chat_id
    
    return sent > 0


def _build_start_message(link_local, public_ip, tunnel_url=None, tunnel_open_base=None):
    """Текст сообщения о запуске: локалка, ПК, при наличии — туннель для доступа с телефона/из интернета."""
    password = public_ip or "(узнайте на 2ip.ru)"
    msg = (
        "📡 Сервер графика работы запущен.\n\n"
        "🏠 Локалка (та же сеть Wi‑Fi / офис):\n%s\n\n"
        "💻 С этого ПК:\nhttp://127.0.0.1:8080\n\n"
    ) % link_local
    
    if tunnel_url and "2ip" not in str(password):
        one_tap_local = "%s/tunnel-open?tunnel=%s&pw=%s" % (
            link_local.rstrip("/"), quote(tunnel_url, safe=""), quote(str(password), safe="")
        )
        if tunnel_open_base:
            one_tap_public = "%s?tunnel=%s&pw=%s" % (
                tunnel_open_base, quote(tunnel_url, safe=""), quote(str(password), safe="")
            )
            msg += (
                "🌐 Доступ из интернета (с телефона / из дома):\n"
                "👉 Один тап (открыть и войти): %s\n\n"
                "• Или по туннелю: %s\n"
                "  Пароль при запросе: %s\n\n"
            ) % (one_tap_public, tunnel_url, password)
        else:
            msg += (
                "📱 С телефона в той же Wi-Fi (один тап):\n%s\n\n"
                "🌐 С телефона из интернета:\n%s\n"
                "Пароль при запросе: %s\n\n"
                "(Чтобы «один тап» работал из интернета — загрузите static/tunnel_open.html на хостинг и укажите tunnel_open_base в telegram_config.json.)\n\n"
            ) % (one_tap_local, tunnel_url, password)
    else:
        msg += "🔌 Туннель: запускается в фоне; если доступен Node.js — придёт отдельное сообщение со ссылкой.\n\n"
    
    msg += "🔑 Вход: admin / admin или учётные записи сотрудников."
    return msg


def _write_startup_links(link_local, link_public=None, tunnel_url=None):
    """Записать ссылки для входа в файл — скрипт «Открыть ссылку» может открыть их в браузере."""
    try:
        path = os.path.join(BASE_DIR, "startup_links.txt")
        lines = [link_local]
        if link_public:
            lines.append(link_public)
        if tunnel_url:
            lines.append(tunnel_url)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass


def _write_tunnel_info(tunnel_url, password):
    """Записать ссылку туннеля и пароль в DATA_DIR для API «Показать ссылку» в админке (в т.ч. с телефона)."""
    try:
        try:
            from app_paths import DATA_DIR
        except ImportError:
            DATA_DIR = BASE_DIR
        path = os.path.join(DATA_DIR, "tunnel_info.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"tunnel_url": tunnel_url, "password": str(password)}, f, ensure_ascii=False)
    except Exception:
        pass


def _get_config_node_dir():
    """Прочитать путь к Node.js из telegram_config.json (ключ node_dir), если указан."""
    try:
        from app_paths import DATA_DIR
        for folder in (DATA_DIR, BASE_DIR):
            path = os.path.join(folder, "telegram_config.json")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                node_dir = (data.get("node_dir") or "").strip()
                if node_dir and os.path.isdir(node_dir):
                    return node_dir
    except Exception:
        pass
    return None


def _get_node_candidate_dirs():
    """Список типичных папок с Node.js (для поиска и для расширения PATH при where/which)."""
    candidates = []
    if sys.platform == "win32":
        for base in (
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        ):
            candidates.append(os.path.join(base, "nodejs"))
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            candidates.append(os.path.join(localappdata, "Programs", "node"))
            candidates.append(os.path.join(localappdata, "Programs", "nodejs"))
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            candidates.append(os.path.join(userprofile, "scoop", "apps", "nodejs", "current"))
            candidates.append(os.path.join(userprofile, "AppData", "Local", "Programs", "node"))
        appdata = os.environ.get("APPDATA") or localappdata
        if appdata:
            nvm = os.path.join(appdata, "nvm")
            if os.path.isdir(nvm):
                try:
                    for name in os.listdir(nvm):
                        root = os.path.join(nvm, name)
                        if os.path.isfile(os.path.join(root, "node.exe")):
                            candidates.append(root)
                        bin_dir = os.path.join(root, "node_modules", "npm", "bin")
                        if os.path.isdir(bin_dir):
                            candidates.append(bin_dir)
                except OSError:
                    pass
    return [d for d in candidates if os.path.isdir(d)]


def _discover_node_via_shell():
    """Узнать путь к node через where (Windows) / which (Unix) с расширенным PATH. Возвращает (node_dir, npx_cmd) или (None, None)."""
    import shutil
    candidates = _get_node_candidate_dirs()
    base_path = os.environ.get("PATH", "")
    extended_path = os.pathsep.join(candidates) + os.pathsep + base_path
    env = os.environ.copy()
    env["PATH"] = extended_path
    try:
        if sys.platform == "win32":
            r = subprocess.run(
                'cmd /c where node',
                capture_output=True, timeout=8, shell=True, cwd=BASE_DIR, env=env, text=True,
            )
            out = (r.stdout or "").strip()
        else:
            r = subprocess.run(
                ["sh", "-c", "which node 2>/dev/null"],
                capture_output=True, timeout=5, cwd=BASE_DIR, env=env, text=True,
            )
            out = (r.stdout or "").strip()
        if r.returncode != 0 or not out:
            return None, None
        first_line = out.splitlines()[0].strip()
        if not first_line:
            return None, None
        node_exe_path = os.path.normpath(first_line)
        if not os.path.isfile(node_exe_path):
            return None, None
        node_dir = os.path.dirname(node_exe_path)
        npx_cmd = "npx.cmd" if (sys.platform == "win32" and os.path.isfile(os.path.join(node_dir, "npx.cmd"))) else "npx"
        if not os.path.isfile(os.path.join(node_dir, npx_cmd)) and not os.path.isfile(os.path.join(node_dir, "npx")):
            npx_cmd = "node"
        return node_dir, npx_cmd
    except Exception:
        return None, None


def _check_node_dir(node_dir):
    """Проверить папку: есть ли npx или node. Вернуть (dir, cmd) или (None, None)."""
    if not node_dir or not os.path.isdir(node_dir):
        return None, None
    npx_cmd = os.path.join(node_dir, "npx.cmd")
    npx_plain = os.path.join(node_dir, "npx")
    node_exe = os.path.join(node_dir, "node.exe")
    if os.path.isfile(npx_cmd) or (sys.platform != "win32" and os.path.isfile(npx_plain)):
        return node_dir, ("npx.cmd" if os.path.isfile(npx_cmd) else "npx")
    if os.path.isfile(node_exe):
        return node_dir, "node"
    return None, None


def _find_node_npx():
    """Найти путь к node/npx: конфиг → where/which с расширенным PATH → PATH процесса → типичные папки. Возвращает (node_dir, npx_cmd) или (None, None)."""
    import shutil
    
    # 0) Путь из настроек (telegram_config.json → node_dir)
    config_dir = _get_config_node_dir()
    if config_dir:
        d, cmd = _check_node_dir(config_dir)
        if d:
            return d, cmd
    
    # 1) Автоопределение: where node / which node с расширенным PATH
    node_dir, npx_name = _discover_node_via_shell()
    if node_dir:
        d, cmd = _check_node_dir(node_dir)
        if d:
            return d, cmd
    
    # 2) Стандартный поиск в PATH процесса
    npx_path = shutil.which("npx")
    if npx_path:
        return os.path.dirname(npx_path), "npx"
    node_path = shutil.which("node")
    if node_path:
        return os.path.dirname(node_path), "node"
    
    # 3) Перебор типичных папок
    for node_dir in _get_node_candidate_dirs():
        d, cmd = _check_node_dir(node_dir)
        if d:
            return d, cmd
    
    return None, None


def _node_available():
    """Проверить, установлен ли Node.js (нужен для localtunnel)."""
    node_dir, _ = _find_node_npx()
    if not node_dir:
        return False
    try:
        env = os.environ.copy()
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
        r = subprocess.run(
            "node -v",
            capture_output=True, timeout=10, shell=True, cwd=BASE_DIR, env=env,
        )
        return r.returncode == 0
    except Exception:
        return False


def _install_ai_dependencies():
    """Автоматическая установка AI зависимостей при первом запуске."""
    print("\n" + "=" * 60)
    print("🤖 Автоматическая установка AI зависимостей")
    print("=" * 60)
    print("✅ Puter.js работает через браузер (CDN)")
    print("   Python SDK не требуется!")
    print()
    print("📦 AI помощник доступен:")
    print("   • Веб-интерфейс: http://localhost:8080/puter-ai")
    print("   • 8 бесплатных моделей (GPT-5, Claude, Qwen)")
    print("   • Не требует API ключей")
    print()
    print("⚠️  DashScope AI (платный):")
    print("   • Проверьте ai_config.json")
    print("   • Если ошибка 403 — используйте Puter.js")
    print("=" * 60)
    return True


def _run_startup_checks():
    """Проверка окружения перед запуском: порты, Node.js, конфиг Telegram. Результаты выводятся в консоль."""
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("🔍 Проверка окружения перед запуском")
    print("Время: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    print("=" * 60)
    
    # Порты
    print("\n📌 Проверка портов:")
    p5000 = check_port(5000)
    p8080 = check_port(8080)
    
    if p5000:
        print("  ✅ Порт 5000 (socket) — свободен")
    else:
        print("  ⚠️  Порт 5000 (socket) — занят")
    
    if p8080:
        print("  ✅ Порт 8080 (веб) — свободен")
    else:
        print("  ⚠️  Порт 8080 (веб) — занят")
    
    if not p8080:
        print("\n  🔄 Порт 8080 занят. Пытаемся освободить (завершить старый процесс)...")
        if _try_free_port(8080):
            print("  ✅ Порт 8080 освобождён. Продолжаем.")
            p8080 = True
        else:
            print("\n  ❌ Не удалось освободить порт 8080!")
            print("     Закройте ВСЕ окна Графика (и консоль с сервером),")
            print("     затем запустите снова.")
            print("     Или используйте: Освободить_порт_8080.bat")
            sys.exit(1)
    
    if not p5000:
        print("\n  🔄 Порт 5000 занят. Пытаемся освободить...")
        if _try_free_port(5000):
            print("  ✅ Порт 5000 освобождён. Продолжаем.")
        else:
            print("\n  ❌ Порт 5000 занят!")
            print("     Закройте предыдущую копию Графика.")
            sys.exit(1)
    
    # Node.js
    print("\n📌 Проверка Node.js (для туннеля):")
    node_dir, npx_cmd = _find_node_npx()
    node_ok = False
    node_version = ""
    
    if node_dir:
        try:
            env = os.environ.copy()
            env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
            r = subprocess.run(
                "node -v",
                capture_output=True, timeout=8, shell=True, cwd=BASE_DIR, env=env, text=True,
            )
            if r.returncode == 0 and (r.stdout or "").strip():
                node_version = (r.stdout or "").strip()
                node_ok = True
        except Exception as e:
            print(f"  ⚠️ Ошибка проверки Node.js: {e}")
    
    if node_ok:
        print(f"  ✅ Node.js {node_version} найден (папка: {node_dir})")
    else:
        print("  ❌ Node.js не найден или не запускается!")
        print("     Туннель не будет работать.")
        print("     Установите Node.js с https://nodejs.org")
        print("     Или укажите путь в telegram_config.json: \"node_dir\": \"C:\\Program Files\\nodejs\"")
    
    # Telegram
    print("\n📌 Проверка Telegram:")
    token, chat_ids, config_path, tunnel_open_base = _load_telegram_config()
    has_config = os.path.isfile(config_path) if config_path else False
    
    if has_config:
        print(f"  ✅ Конфигурация найдена: {config_path}")
        if token and chat_ids:
            print(f"  ✅ Token: настроен ({len(token)} симв.)")
            print(f"  ✅ Chat IDs: настроено ({len(chat_ids)} получателей)")
        else:
            print("  ⚠️  Token: не задан в конфиге")
            print("  ⚠️  Chat IDs: не заданы в конфиге")
            print("     Telegram-уведомления не будут работать.")
    else:
        print("  ℹ️  Конфигурация Telegram не найдена (опционально)")
        print("     Скопируйте telegram_config.json.example в telegram_config.json")
        print("     и укажите токен бота и chat_ids для уведомлений.")
    
    # Локальный IP
    print("\n📡 Сетевая информация:")
    local_ip = get_local_ip()
    print(f"  🌐 Локальный IP: {local_ip}")
    print(f"  📱 Ссылка для локалки: http://{local_ip}:8080")
    
    public_ip = get_public_ip()
    if public_ip:
        print(f"  🌍 Внешний IP: {public_ip}")
        print(f"  🔗 Ссылка из интернета (после проброса порта): http://{public_ip}:8080")
    else:
        print("  ⚠️  Внешний IP не определён (проверьте интернет)")
    
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 60 + "\n")


def _run_tunnel_and_send_one_message(link_local, public_ip):
    """В фоне запустить localtunnel; когда есть ссылка — отправить второе сообщение. Процесс туннеля не завершаем — иначе ссылка перестаёт работать."""
    global _tunnel_process
    
    token, chat_ids, _, tunnel_open_base = _load_telegram_config()
    if not token or not chat_ids:
        return
    
    password = public_ip or "(узнайте на 2ip.ru)"
    tunnel_url = None
    
    # Лог в папке с правами на запись (при установке в Program Files — %LOCALAPPDATA%\GrafikRaboty)
    try:
        from app_paths import DATA_DIR
        tunnel_log = os.path.join(DATA_DIR, "tunnel_output.txt")
    except ImportError:
        tunnel_log = os.path.join(BASE_DIR, "tunnel_output.txt")
    
    # Форматы вывода localtunnel (loca.lt, localtunnel.me) и похожие туннели
    url_patterns = (
        r"https://[a-zA-Z0-9\-]+\.loca\.lt[/\s\)\"\']?",
        r"https://[a-zA-Z0-9\-]+\.localtunnel\.me[/\s\)\"\']?",
        r"https://[^\s\)\"\']+loca\.lt[/\s\)\"\']?",
        r"https://[^\s\)\"\']+localtunnel\.me[/\s\)\"\']?",
        r"https://[a-zA-Z0-9\-]+\.loca\.lt",
        r"https://[a-zA-Z0-9\-]+\.localtunnel\.me",
    )
    
    # Ищем Node.js (в т.ч. в Program Files — при запуске из ярлыка PATH часто без Node)
    node_dir, npx_name = _find_node_npx()
    
    if not node_dir:
        _tunnel_process = None
        fallback = (
            "📡 Напоминание: сервер графика работы запущен.\n\n"
            "🏠 Локалка (та же сеть): %s\n\n"
            "🔌 Туннель не удалось поднять: не найден Node.js. Установите с https://nodejs.org или укажите путь в telegram_config.json: \"node_dir\": \"C:\\\\Program Files\\\\nodejs\". "
            "Или используйте локалку в той же Wi-Fi.\n\n"
            "🔑 Вход: admin / admin или учётные записи сотрудников."
        ) % link_local
        if _send_telegram(token, chat_ids, fallback):
            print("📤 В Telegram отправлено напоминание (Node.js не установлен).")
        return
    
    env = os.environ.copy()
    env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    
    # Полный путь к npx — иначе из ярлыка/установщика shell может не найти npx в PATH
    npx_full = os.path.join(node_dir, npx_name)
    if not os.path.isfile(npx_full) and os.path.isfile(os.path.join(node_dir, "npx.cmd")):
        npx_full = os.path.join(node_dir, "npx.cmd")
    elif not os.path.isfile(npx_full) and os.path.isfile(os.path.join(node_dir, "npx")):
        npx_full = os.path.join(node_dir, "npx")
    
    try:
        try:
            if os.path.exists(tunnel_log):
                try:
                    os.remove(tunnel_log)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Запуск npx с захватом вывода в реальном времени (без буфера shell) — так ссылка находится надёжнее
        tunnel_url_from_thread = [None]  # mutable to set from reader thread
        
        def read_tunnel_output(pipe, logpath):
            try:
                with open(logpath, "w", encoding="utf-8", errors="replace") as logf:
                    while True:
                        line = pipe.readline()
                        if not line:
                            break
                        s = line.decode("utf-8", errors="replace")
                        logf.write(s)
                        logf.flush()
                        for pattern in url_patterns:
                            m = re.search(pattern, s)
                            if m:
                                u = m.group(0).rstrip("/).\"' \t\n")
                                if u.startswith("https://"):
                                    tunnel_url_from_thread[0] = u
                                break
            except Exception:
                pass
        
        proc = subprocess.Popen(
            [npx_full, "--yes", "localtunnel", "--port", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BASE_DIR,
            env=env,
        )
        _tunnel_process = proc
        
        reader = threading.Thread(target=read_tunnel_output, args=(proc.stdout, tunnel_log), daemon=True)
        reader.start()
        
        tunnel_url = None
        for _ in range(120):  # до 60 сек
            if proc.poll() is not None:
                break
            if tunnel_url_from_thread[0]:
                tunnel_url = tunnel_url_from_thread[0]
                _write_startup_links(link_local, link_public=None, tunnel_url=tunnel_url)
                break
            time.sleep(0.5)
        
        if tunnel_url is None and tunnel_url_from_thread[0]:
            tunnel_url = tunnel_url_from_thread[0]
        
        if tunnel_url and "2ip" not in str(password):
            _write_tunnel_info(tunnel_url, password)
            msg = _build_start_message(link_local, public_ip, tunnel_url=tunnel_url, tunnel_open_base=tunnel_open_base)
            if _send_telegram(token, chat_ids, msg):
                print("📤 В Telegram отправлено сообщение со ссылкой туннеля (доступ с телефона/из интернета).")
        else:
            # Туннель не выдал ссылку — вывести в консоль последние строки лога для отладки
            log_hint = ""
            if os.path.isfile(tunnel_log):
                try:
                    with open(tunnel_log, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.read().strip().splitlines()
                    if lines:
                        log_hint = lines[-1][:200] if lines else ""
                except Exception:
                    pass
            
            if log_hint:
                print("⚠️  Туннель (последняя строка лога): %s" % log_hint)
            else:
                print("⚠️  Туннель не выдал ссылку. Лог: %s" % tunnel_log)
            
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            _tunnel_process = None
            
            fallback = (
                "📡 Напоминание: сервер графика работы запущен.\n\n"
                "🏠 Локалка (та же сеть): %s\n\n"
                "🌐 Туннель не удалось поднять (сеть или сервис localtunnel). Для доступа с телефона используйте ссылку выше в той же Wi-Fi.\n\n"
                "🔑 Вход: admin / admin или учётные записи сотрудников."
            ) % link_local
            if _send_telegram(token, chat_ids, fallback):
                print("📤 В Telegram отправлено напоминание (локалка, туннель не поднят).")
    
    except Exception as e:
        print("⚠️  Туннель не запустился (для внешней ссылки нужен Node.js): %s" % e)
        _tunnel_process = None
        token, chat_ids = _load_telegram_config()[:2]
        if token and chat_ids:
            fallback = (
                "📡 Сервер графика работы запущен.\n\n🏠 Локалка: %s\n\n"
                "Туннель не запущен. Вход: admin / admin или учётные записи сотрудников."
            ) % link_local
            _send_telegram(token, chat_ids, fallback)


def _send_vk_startup_notification(local_ip, link_local, link_public):
    """Отправить VK уведомление о запуске сервера"""
    try:
        import vk_startup
        tunnel_url = "настраивается..."
        tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
        if os.path.exists(tunnel_info_path):
            import json
            with open(tunnel_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
                tunnel_url = info.get('tunnel_url', tunnel_url)
        
        vk_startup.send_vk_startup_notification(
            tunnel_url=tunnel_url,
            password=link_public or local_ip,
            link_local=link_local,
            local_ip=local_ip
        )
        print("✅ VK уведомление отправлено администратору")
    except Exception as e:
        print(f"⚠️ VK уведомление: {e}")


def _notify_telegram_and_hint(local_ip, link_local, link_public):
    """Отправить уведомления (Telegram, VK) о запуске сервера"""
    
    # VK уведомление — отключаем, т.к. launcher_with_vk.py отправляет своё
    # Это предотвращает дублирование уведомлений
    VK_NOTIFICATION_ENABLED = False  # Измените на True если нужно дублирование
    
    if VK_NOTIFICATION_ENABLED:
        _send_vk_startup_notification(local_ip, link_local, link_public)
    
    try:
        from app_paths import DATA_DIR
        config_in_data = os.path.join(DATA_DIR, "telegram_config.json")
        config_in_app = os.path.join(BASE_DIR, "telegram_config.json")
        if not os.path.isfile(config_in_data) and os.path.isfile(config_in_app):
            os.makedirs(DATA_DIR, exist_ok=True)
            import shutil
            shutil.copy2(config_in_app, config_in_data)
    except Exception:
        pass
    
    token, chat_ids, config_path, tunnel_open_base = _load_telegram_config()
    
    if token and chat_ids:
        # Запускаем туннель в фоне - сообщение отправится из tunnel_launcher.py
        t = threading.Thread(target=_run_tunnel_and_send_one_message, args=(link_local, get_public_ip()), daemon=True)
        t.start()
        print("🔄 Туннель запускается в фоне — сообщение придёт в Telegram.")
    else:
        try:
            from app_paths import DATA_DIR
            config_path = os.path.join(DATA_DIR, "telegram_config.json")
        except ImportError:
            config_path = os.path.join(BASE_DIR, "telegram_config.json")
        print("ℹ️ Чтобы при запуске присылать ссылку в Telegram: откройте файл")
        print("   %s" % config_path)
        print("   добавьте bot_token и chat_ids (инструкция: TELEGRAM_НАСТРОЙКА.txt)")


def start_desktop_client():
    """Запустить десктопное приложение на этом компьютере (без лишнего консольного окна)"""
    global _client_process
    
    client_script = os.path.join(BASE_DIR, 'client.py')
    if not os.path.isfile(client_script):
        print("⚠️  Файл client.py не найден, десктопный клиент не запущен.")
        return
    
    try:
        # На Windows используем pythonw, чтобы не открывалось второе консольное окно
        if sys.platform == 'win32':
            python_dir = os.path.dirname(sys.executable)
            pythonw = os.path.join(python_dir, 'pythonw.exe')
            executable = pythonw if os.path.isfile(pythonw) else sys.executable
        else:
            executable = sys.executable
        
        print("🖥️  Запуск десктопного клиента (окно = веб-интерфейс)...")
        _client_process = subprocess.Popen(
            [executable, client_script, "--webview"],
            cwd=BASE_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if _client_process.poll() is None:
            print("✅ Десктопный клиент запущен (окно программы)")
    except Exception as e:
        print(f"⚠️  Не удалось запустить десктопный клиент: {e}")


def main():
    """Главная функция запуска"""
    global _tunnel_process
    
    # Создаём PID файл для возможности остановки
    # PID файл теперь в DATA_DIR (без проблем с правами доступа)
    try:
        from app_paths import DATA_DIR
        pid_file = os.path.join(DATA_DIR, 'server.pid')
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        print(f"✅ PID файл создан: {pid_file}")
    except Exception as e:
        print(f"⚠️  Не удалось создать PID файл (некритично): {e}")
    
    print("=" * 60)
    print("🚀 Запуск системы управления графиком работы")
    print("=" * 60)
    
    _run_startup_checks()
    
    # Автоматическая установка AI зависимостей
    _install_ai_dependencies()
    
    # На любом компе автоматически: локальный и внешний IP
    local_ip = get_local_ip()
    
    print("\n⏳ Определение внешнего IP для удалённого доступа...")
    public_ip = get_public_ip()
    
    link_local = f"http://{local_ip}:8080"
    link_public = f"http://{public_ip}:8080" if public_ip else None
    
    print(f"\n📡 Локальный IP (та же сеть Wi‑Fi): {local_ip}")
    if public_ip:
        print(f"🌍 Внешний IP (интернет): {public_ip}")
    
    print(f"\n📱 Ссылки для доступа (откройте в браузере):")
    print(f"   • В той же сети:     {link_local}")
    if link_public:
        print(f"   • Удалённо (интернет): {link_public}")
    else:
        print(f"   • Удалённо: не определён (нужен проброс порта 8080 на роутере, см. инструкцию)")
    
    print(f"\n💻 На этом ПК: http://127.0.0.1:8080")
    print(f"🔌 Десктоп: {local_ip}:5000")
    
    print(f"\n🔑 Учётные данные:")
    print(f"   Админ: admin / admin")
    print(f"   Сотрудники: валерия / pass123, ольга / pass456")
    
    print("\n" + "=" * 60)
    print("🔄 Запуск серверов...")
    print("=" * 60 + "\n")
    
    # Запускаем socket сервер в отдельном потоке
    socket_thread = threading.Thread(target=start_socket_server, daemon=True)
    socket_thread.start()
    
    # Даём время на запуск socket сервера
    time.sleep(2)
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Ждём, пока веб-сервер начнёт слушать порт 8080 (до 30 сек — после установки первый запуск может быть дольше)
    print("🔄 Ожидание готовности веб-сервера (порт 8080)...")
    if wait_for_port(8080, timeout_sec=30):
        print("✅ Веб-сервер готов.")
    else:
        print("❌ Веб-сервер не ответил за 30 с. Проверьте ошибки выше.")
    
    if check_port(8080):
        print("\n⚠️ ВНИМАНИЕ: Веб-сервер не запустился!")
        print("   Проверьте ошибки выше или запустите: python check_and_install.py")
    else:
        print("\n✅ Серверы запущены успешно!")
    
    print(f"\n📱 Веб-интерфейс: http://{local_ip}:8080")
    print("🖥️  На этом компьютере также запущено десктопное приложение.")
    
    print("\n💡 Подключение:")
    print(f"   В той же сети → {link_local}")
    if link_public:
        print(f"   Из интернета → {link_public} (должен быть проброс порта 8080 на роутере)")
    print("   Логин/пароль: admin / admin или выданные учётные записи.")
    
    # Информация о мониторинге туннеля
    print("\n🔍 МОНИТОРИНГ ТУННЕЛЯ:")
    print(f"   Статус туннеля: {link_local}/tunnel-monitor")
    print(f"   API статуса: {link_local}/api/tunnel-status")
    print(f"   API логов: {link_local}/api/tunnel-logs")
    print(f"   API проверки порта: {link_local}/api/port-check")
    
    if not public_ip:
        print("\n⚠️  Внешний IP не определён. Возможные причины: нет интернета или заблокирован запрос.")
    
    print()
    
    _write_startup_links(link_local, link_public)
    
    # Туннель запускается из auto_tunnel_launcher.py (через launcher_with_vk.py)
    # _notify_telegram_and_hint(local_ip, link_local, link_public)  # отключено — туннель НЕ запускаем отсюда
    
    # Отправляем только Telegram-уведомление (без запуска туннеля)
    try:
        token, chat_ids, config_path, tunnel_open_base = _load_telegram_config()
        if token and chat_ids:
            msg = _build_start_message(link_local, get_public_ip(), tunnel_url=None, tunnel_open_base=tunnel_open_base)
            _send_telegram(token, chat_ids, msg)
            print("📤 В Telegram отправлено уведомление о запуске (туннель запустится отдельно).")
    except Exception as e:
        print(f"⚠️ Telegram уведомление: {e}")
    
    print("\n" + "=" * 60)
    print("Нажмите Ctrl+C для остановки серверов и программы")
    print("=" * 60 + "\n")
    
    # Сразу открываем браузер со страницей входа (после установки пользователь сразу видит интерфейс)
    # /login и ?v=2 чтобы не брать страницу из кэша браузера/окна
    if not check_port(8080):
        try:
            webbrowser.open('http://127.0.0.1:8080/login')
        except Exception:
            pass
    
    # Ждём, пока socket-сервер (5000) начнёт слушать — чтобы десктопный клиент мог подключиться
    print("🔄 Ожидание готовности socket-сервера (порт 5000)...")
    if wait_for_port(5000, timeout_sec=15):
        print("✅ Socket-сервер готов.")
    else:
        print("⚠️  Socket-сервер не ответил за 15 с. Десктопное окно откроет веб-интерфейс.")
    
    # Запускаем десктопный клиент (окно = веб-интерфейс, идентично браузеру)
    start_desktop_client()
    
    # Иконка в трее: «Открыть» (браузер), «Выход»
    def _on_tray_exit(icon_obj, item):
        global _tray_exit
        _tray_exit = True
        if icon_obj:
            icon_obj.stop()
    
    try:
        from PIL import Image  # type: ignore[import-untyped]
        import pystray  # type: ignore[import-untyped]
        img = Image.new('RGBA', (64, 64), (99, 102, 241, 255))
        for y in range(16, 48):
            for x in range(16, 48):
                img.putpixel((x, y), (255, 255, 255, 200))
        _tray_icon_obj = pystray.Icon(
            'grafik', img, 'ВестиГрад корпоративный график',
            menu=pystray.Menu(
                pystray.MenuItem('Открыть', lambda i, _: webbrowser.open('http://127.0.0.1:8080/login')),
                pystray.MenuItem('Выход', _on_tray_exit)
            )
        )
        _tray_thread = threading.Thread(target=lambda: _tray_icon_obj.run(), daemon=True)
        _tray_thread.start()
    except Exception:
        _tray_icon_obj = None
    
    # Держим программу запущенной (выход по Ctrl+C или по кнопке «Выход» в трее)
    try:
        while not _tray_exit:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    
    if _tray_exit:
        print("\n🛑 Выход из трея.")
    
    print("\n\n🛑 Остановка серверов и программы...")
    
    if _tunnel_process is not None and _tunnel_process.poll() is None:
        try:
            _tunnel_process.terminate()
            _tunnel_process.wait(timeout=3)
        except Exception:
            try:
                _tunnel_process.kill()
            except Exception:
                pass
        _tunnel_process = None
        print("✅ Туннель остановлен.")
    
    if _client_process is not None and _client_process.poll() is None:
        try:
            _client_process.terminate()
            _client_process.wait(timeout=3)
        except Exception:
            _client_process.kill()
        print("✅ Десктопный клиент закрыт.")
    
    print("✅ Серверы остановлены.")


if __name__ == "__main__":
    main()
