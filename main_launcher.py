# main_launcher.py - Единый запускатель: серверы + веб + десктопный клиент

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

    """Локальный IP в сети (для доступа в той же WiвЂ‘Fi/локалке)."""

    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "127.0.0.1"



def get_public_ip():

    """Р’неС€РЅиР№ (РїСѓР±Р»иС‡РЅС‹Р№) IP вЂ” для доступа из интернета (нужен РїСЂоР±СЂос поСЂС‚Р° 8080 на СЂоСѓС‚РµСЂРµ)."""

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

    """Проверить, свободен Р»и поСЂС‚ (True = свободен, False = занят/сР»СѓС€Р°РµС‚)."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:

        result = sock.connect_ex(('127.0.0.1', port))

        return result != 0

    finally:

        sock.close()





def wait_for_port(port, timeout_sec=15):

    """Р–РґР°С‚СЊ, поРєР° поСЂС‚ наС‡РЅС‘С‚ сР»СѓС€Р°С‚СЊ (сРµСЂвРµСЂ поРґРЅСЏР»сСЏ). Р’оР·вСЂР°С‰Р°РµС‚ True, если поСЂС‚ занят."""

    import time as _t

    deadline = _t.time() + timeout_sec

    while _t.time() < deadline:

        if not check_port(port):  # поСЂС‚ занят вЂ” сРµСЂвРµСЂ сР»СѓС€Р°РµС‚

            return True

        _t.sleep(0.4)

    return False





def _try_free_port(port):

    """РџоРїС‹С‚Р°С‚СЊсСЏ освободить поСЂС‚ (завершить процесс). Р Р°ботаРµС‚ на Windows. Р’оР·вСЂР°С‰Р°РµС‚ True если поСЂС‚ освобождён."""

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

    """Р—Р°РїСѓсС‚иС‚СЊ socket сРµСЂвРµСЂ"""

    try:

        print("рџ”§ РРјпоСЂС‚ РјоРґСѓР»РµР№ socket сРµСЂвРµСЂР°...")

        import server

        print("вњ… РњоРґСѓР»и иРјпоСЂС‚иСЂовР°РЅС‹")

        print("рџ”Њ Р—Р°РїСѓсРє socket сРµСЂвРµСЂР° на поСЂС‚Сѓ 5000...")

        # Р—Р°РїСѓсРєР°РµРј сРµСЂвРµСЂ в Р±РµсРєонеС‡РЅоРј С†иРєР»Рµ

        server_instance = server.ScheduleServer()

        server_instance.start()

    except ImportError as e:

        print(f"вќЊ РћС€иР±РєР° иРјпоСЂС‚Р°: {e}")

        import traceback

        traceback.print_exc()

    except Exception as e:

        print(f"вќЊ РћС€иР±РєР° Р·Р°РїСѓсРєР° socket сРµСЂвРµСЂР°: {e}")

        import traceback

        traceback.print_exc()



def start_web_server():

    """Р—Р°РїСѓсС‚иС‚СЊ вРµР±-сРµСЂвРµСЂ"""

    try:

        print("рџ”§ РРјпоСЂС‚ РјоРґСѓР»РµР№ вРµР±-сРµСЂвРµСЂР°...")

        import web_server as ws_mod

        app = ws_mod.app

        # Socket.IO - используем для WebSocket соединений
        socketio = ws_mod.socketio

        print("вњ… РњоРґСѓР»и иРјпоСЂС‚иСЂовР°РЅС‹ (web_server: %s)" % getattr(ws_mod, "__file__", "?"))

        print("рџЊђ Р—Р°РїСѓсРє вРµР±-сРµСЂвРµСЂР° на поСЂС‚Сѓ 8080...")

        # Запускаем через socketio для поддержки WebSocket
        socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)

    except ImportError as e:

        print(f"вќЊ РћС€иР±РєР° иРјпоСЂС‚Р°: {e}")

        print("рџ’Ў РЈР±РµРґиС‚РµсСЊ, С‡С‚о установленС‹ всРµ Р·Р°висиРјосС‚и:")

        print("   pip install -r requirements.txt")

        import traceback

        traceback.print_exc()

    except Exception as e:

        print(f"вќЊ РћС€иР±РєР° Р·Р°РїСѓсРєР° вРµР±-сРµСЂвРµСЂР°: {e}")

        import traceback

        traceback.print_exc()





def _load_telegram_config():

    """Р—Р°РіСЂСѓР·иС‚СЊ токен и chat_ids для Telegram (снаС‡Р°Р»Р° папка данных, затем папка приР»ожеРЅиСЏ)."""

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

    """РћС‚РїСЂР°виС‚СЊ сообщение в Telegram с retry и оР±С…оРґоРј SSL РїСЂоР±Р»РµРј."""

    if not bot_token or not chat_ids:

        return False

    if isinstance(chat_ids, str):

        chat_ids = [chat_ids]

    

    url = "https://api.telegram.org/bot%s/sendMessage" % bot_token

    sent = 0

    

    # РЎоР·РґР°С‘Рј SSL контекст Р±РµР· строгой РїСЂовРµСЂРєи (для РєоСЂпоСЂР°С‚ивРЅС‹С… РїСЂоРєси)

    import ssl

    ssl_context = ssl.create_default_context()

    ssl_context.check_hostname = False

    ssl_context.verify_mode = ssl.CERT_NONE

    

    for cid in chat_ids:

        # 3 поРїС‹С‚Рєи с Р·Р°РґРµСЂР¶РєоР№ при SSL timeout

        for attempt in range(3):

            try:

                data = json.dumps({

                    "chat_id": str(cid).strip(), 

                    "text": text, 

                    "disable_web_page_preview": True

                }).encode("utf-8")

                req = urllib.request.Request(url, data=data, method="POST", 

                                            headers={"Content-Type": "application/json"})

                # РспоР»СЊР·СѓРµРј relaxed SSL контекст и СѓвРµР»иС‡РµРЅРЅС‹Р№ С‚Р°Р№РјР°СѓС‚

                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as r:

                    if 200 <= r.status < 300:

                        sent += 1

                        break

            except urllib.error.URLError as e:

                reason = str(e.reason).lower()

                if "ssl" in reason or "timeout" in reason or "handshake" in reason:

                    if attempt < 2:

                        import time

                        time.sleep(2 ** attempt)  # СЌРєспонеРЅС†иР°Р»СЊнаСЏ задержка

                        continue

                # Р›оРіиСЂСѓРµРј оС€иР±РєСѓ РЅо не прерываем

                print(f"вљ пёЏ  Telegram оС€иР±РєР° (поРїС‹С‚РєР° {attempt+1}/3): {e}")

            except Exception as e:

                print(f"вљ пёЏ  Telegram оС€иР±РєР° (поРїС‹С‚РєР° {attempt+1}/3): {e}")

                if attempt < 2:

                    import time

                    time.sleep(2 ** attempt)

                continue

        break  # РїРµСЂРµС…оРґиРј Рє следующему chat_id

    

    return sent > 0



def _build_start_message(link_local, public_ip, tunnel_url=None, tunnel_open_base=None):

    """РўРµРєсС‚ сооР±С‰РµРЅиСЏ о запуске: Р»оРєР°Р»РєР°, РџРљ, при наР»иС‡ии вЂ” С‚СѓРЅнеР»СЊ для доступа с телефона/из интернета."""

    password = public_ip or "(СѓР·наР№С‚Рµ на 2ip.ru)"

    msg = (

        "рџ“… РЎРµСЂвРµСЂ РіСЂР°С„иРєР° СЂР°Р±оС‚С‹ запущен.\n\n"

        "рџЏ  Р›оРєР°Р»РєР° (С‚Р° же сРµС‚СЊ WiвЂ‘Fi / оС„ис):\n%s\n\n"

        "рџ’» РЎ СЌС‚оРіо РџРљ:\nhttp://127.0.0.1:8080\n\n"

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

                "рџЊђ Р”осС‚СѓРї из интернета (с телефона / из РґоРјР°):\n"

                "вЂў РћРґиРЅ тап (открыть и войти): %s\n\n"

                "вЂў РР»и по туннелю: %s\n"

                "  РџР°СЂоР»СЊ при запросе: %s\n\n"

            ) % (one_tap_public, tunnel_url, password)

        else:

            msg += (

                "рџ“± РЎ телефона в той же WiвЂ‘Fi (один тап):\n%s\n\n"

                "рџЊђ РЎ телефона из интернета:\n%s\n"

                "РџР°СЂоР»СЊ при запросе: %s\n\n"

                "(Р§С‚оР±С‹ В«один тапВ» СЂР°ботаР» из интернета вЂ” загрузите static/tunnel_open.html на хостинг и укажите tunnel_open_base в telegram_config.json.)\n\n"

            ) % (one_tap_local, tunnel_url, password)

    else:

        msg += "рџЊђ РўСѓРЅнеР»СЊ: Р·Р°РїСѓсРєР°РµС‚сСЏ в фоне; если доступен Node.js вЂ” приРґС‘С‚ отдельное сообщение со ссС‹Р»РєоР№.\n\n"

    msg += "рџ”ђ Р’С…оРґ: admin / admin или учётные записи сотрудников."

    return msg





def _write_startup_links(link_local, link_public=None, tunnel_url=None):

    """Р—Р°РїисР°С‚СЊ ссС‹Р»Рєи для входа в С„Р°Р№Р» вЂ” сРєСЂиРїС‚ В«РћС‚РєСЂС‹С‚СЊ ссС‹Р»РєСѓВ» РјожеС‚ открыть иС… в браузере."""

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

    """Р—Р°РїисР°С‚СЊ ссС‹Р»РєСѓ С‚СѓРЅнеР»СЏ и пароль в DATA_DIR для API В«РџоРєР°Р·Р°С‚СЊ ссС‹Р»РєСѓВ» в Р°РґРјиРЅРєРµ (в С‚.С‡. с телефона)."""

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

    """РџСЂоС‡иС‚Р°С‚СЊ РїСѓС‚СЊ Рє Node.js из telegram_config.json (РєР»СЋС‡ node_dir), если СѓРєР°Р·Р°РЅ."""

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

    """Список типичных РїР°поРє с Node.js (для поиска и для расширения PATH при where/which)."""

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

    """РЈР·наС‚СЊ РїСѓС‚СЊ Рє node С‡РµСЂРµР· where (Windows) / which (Unix) с СЂР°сС€иСЂРµРЅРЅС‹Рј PATH. Р’оР·вСЂР°С‰Р°РµС‚ (node_dir, npx_cmd) или (None, None)."""

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

                capture_output=True,

                timeout=8,

                shell=True,

                cwd=BASE_DIR,

                env=env,

                text=True,

            )

            out = (r.stdout or "").strip()

        else:

            r = subprocess.run(

                ["sh", "-c", "which node 2>/dev/null"],

                capture_output=True,

                timeout=5,

                cwd=BASE_DIR,

                env=env,

                text=True,

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

    """Проверить папку: есть Р»и npx или node. Р’РµСЂРЅСѓС‚СЊ (dir, cmd) или (None, None)."""

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

    """РќР°Р№С‚и РїСѓС‚СЊ Рє node/npx: конфиг в†’ where/which с СЂР°сС€иСЂРµРЅРЅС‹Рј PATH в†’ PATH процесса в†’ С‚иРїиС‡РЅС‹Рµ РїР°РїРєи. Р’оР·вСЂР°С‰Р°РµС‚ (node_dir, npx_cmd) или (None, None)."""

    import shutil



    # 0) РџСѓС‚СЊ из насС‚СЂоРµРє (telegram_config.json в†’ node_dir)

    config_dir = _get_config_node_dir()

    if config_dir:

        d, cmd = _check_node_dir(config_dir)

        if d:

            return d, cmd



    # 1) РђвС‚ооРїСЂРµРґРµР»РµРЅиРµ: where node / which node с СЂР°сС€иСЂРµРЅРЅС‹Рј PATH

    node_dir, npx_name = _discover_node_via_shell()

    if node_dir:

        d, cmd = _check_node_dir(node_dir)

        if d:

            return d, cmd



    # 2) РЎС‚Р°РЅРґР°СЂС‚РЅС‹Р№ поисРє в PATH процесса

    npx_path = shutil.which("npx")

    if npx_path:

        return os.path.dirname(npx_path), "npx"

    node_path = shutil.which("node")

    if node_path:

        return os.path.dirname(node_path), "node"



    # 3) РџРµСЂРµР±оСЂ типичных РїР°поРє

    for node_dir in _get_node_candidate_dirs():

        d, cmd = _check_node_dir(node_dir)

        if d:

            return d, cmd

    return None, None





def _node_available():

    """Проверить, установлен Р»и Node.js (нужен для localtunnel)."""

    node_dir, _ = _find_node_npx()

    if not node_dir:

        return False

    try:

        env = os.environ.copy()

        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")

        r = subprocess.run(

            "node -v",

            capture_output=True,

            timeout=10,

            shell=True,

            cwd=BASE_DIR,

            env=env,

        )

        return r.returncode == 0

    except Exception:

        return False





def _install_ai_dependencies():

    """РђвС‚оРјР°С‚иС‡РµсРєР°СЏ СѓсС‚Р°РЅовРєР° AI Р·Р°висиРјосС‚РµР№ при РїРµСЂвоРј запуске."""

    import subprocess

    

    print("\n" + "=" * 60)

    print("рџ¤– РџР РћР’Р•Р РљРђ AI Р—РђР’РРЎРРњРћРЎРўР•Р™")

    print("=" * 60)

    

    # Puter.js СЂР°ботаРµС‚ С‡РµСЂРµР· CDN в браузере - Python SDK не нужен!

    print("вњ… Puter.js СЂР°ботаРµС‚ С‡РµСЂРµР· Р±СЂР°СѓР·РµСЂ (CDN)")

    print("   Python SDK не С‚СЂРµР±СѓРµС‚сСЏ!")

    print()

    print("рџ“¦ AI поРјоС‰РЅиРє доступен:")

    print("   вЂў Р’РµР±-иРЅС‚РµСЂС„РµР№с: http://localhost:8080/puter-ai")

    print("   вЂў 8 Р±РµсРїР»Р°С‚РЅС‹С… РјоРґРµР»РµР№ (GPT-5, Claude, Qwen)")

    print("   вЂў РќРµ С‚СЂРµР±СѓРµС‚ API РєР»СЋС‡РµР№")

    print()

    print("вљ пёЏ  DashScope AI (РїР»Р°С‚РЅС‹Р№):")

    print("   вЂў РџСЂовРµСЂСЊС‚Рµ ai_config.json")

    print("   вЂў Р•сР»и оС€иР±РєР° 403 вЂ” испоР»СЊР·СѓР№С‚Рµ Puter.js")

    print("=" * 60)

    

    return True





def _run_startup_checks():

    """РџСЂовРµСЂРєР° окружения перед запуском: поСЂС‚С‹, Node.js, конфиг Telegram. Р РµР·СѓР»СЊС‚Р°С‚С‹ выводятся в консоль."""

    from datetime import datetime

    

    print("\n" + "=" * 60)

    print("РџР РћР’Р•Р РљРђ РћРљР РЈР–Р•РќРРЇ РџР•Р Р•Р” Р—РђРџРЈРЎРљРћРњ")

    print("Р’СЂРµРјСЏ: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

    print("=" * 60)

    

    # РџоСЂС‚С‹

    print("\nрџ“Њ РџСЂовРµСЂРєР° поСЂС‚ов:")

    p5000 = check_port(5000)

    p8080 = check_port(8080)

    

    if p5000:

        print("  вњ… РџоСЂС‚ 5000 (socket) вЂ” свободен")

    else:

        print("  вљ пёЏ  РџоСЂС‚ 5000 (socket) вЂ” занят")

    

    if p8080:

        print("  вњ… РџоСЂС‚ 8080 (вРµР±) вЂ” свободен")

    else:

        print("  вљ пёЏ  РџоСЂС‚ 8080 (вРµР±) вЂ” занят")

    

    if not p8080:

        print("\n  рџ”„ РџоСЂС‚ 8080 занят. РџС‹С‚Р°РµРјсСЏ освободить (завершить старый процесс)...")

        if _try_free_port(8080):

            print("  вњ… РџоСЂС‚ 8080 освобождён. РџСЂоРґоР»Р¶Р°РµРј.")

            p8080 = True

        else:

            print("\n  вќЊ РќРµ удалось освободить поСЂС‚ 8080!")

            print("     Р—Р°РєСЂоР№С‚Рµ Р’РЎР• окна Р“СЂР°С„иРєР° (и консоль с сервером),")

            print("     затем Р·Р°РїСѓсС‚иС‚Рµ снова.")

            print("     РР»и испоР»СЊР·СѓР№С‚Рµ: РћсвоР±оРґиС‚СЊ_поСЂС‚_8080.bat")

            sys.exit(1)

    

    if not p5000:

        print("\n  рџ”„ РџоСЂС‚ 5000 занят. РџС‹С‚Р°РµРјсСЏ освободить...")

        if _try_free_port(5000):

            print("  вњ… РџоСЂС‚ 5000 освобождён. РџСЂоРґоР»Р¶Р°РµРј.")

        else:

            print("\n  вќЊ РџоСЂС‚ 5000 занят!")

            print("     Р—Р°РєСЂоР№С‚Рµ предыдущую копию Р“СЂР°С„иРєР°.")

            sys.exit(1)

    

    # Node.js

    print("\nрџ“Њ РџСЂовРµСЂРєР° Node.js (для С‚СѓРЅнеР»СЏ):")

    node_dir, npx_cmd = _find_node_npx()

    node_ok = False

    node_version = ""

    

    if node_dir:

        try:

            env = os.environ.copy()

            env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")

            r = subprocess.run(

                "node -v",

                capture_output=True,

                timeout=8,

                shell=True,

                cwd=BASE_DIR,

                env=env,

                text=True,

            )

            if r.returncode == 0 and (r.stdout or "").strip():

                node_version = (r.stdout or "").strip()

                node_ok = True

        except Exception as e:

            print(f"  вљ пёЏ  РћС€иР±РєР° РїСЂовРµСЂРєи Node.js: {e}")

    

    if node_ok:

        print(f"  вњ… Node.js {node_version} найден (папка: {node_dir})")

    else:

        print("  вќЊ Node.js не найден или не Р·Р°РїСѓсРєР°РµС‚сСЏ!")

        print("     РўСѓРЅнеР»СЊ не будет работать.")

        print("     РЈсС‚Р°РЅовиС‚Рµ Node.js с https://nodejs.org")

        print("     РР»и укажите РїСѓС‚СЊ в telegram_config.json: \"node_dir\": \"C:\\Program Files\\nodejs\"")

    

    # Telegram

    print("\nрџ“Њ РџСЂовРµСЂРєР° Telegram:")

    token, chat_ids, config_path, tunnel_open_base = _load_telegram_config()

    has_config = os.path.isfile(config_path) if config_path else False

    

    if has_config:

        print(f"  вњ… РљоРЅС„иРіСѓСЂР°С†иСЏ найденР°: {config_path}")

        if token and chat_ids:

            print(f"  вњ… Token: настроен ({len(token)} сиРјв.)")

            print(f"  вњ… Chat IDs: настроено ({len(chat_ids)} получателей)")

        else:

            print("  вљ пёЏ  Token: не Р·Р°РґР°РЅ в конфигРµ")

            print("  вљ пёЏ  Chat IDs: не Р·Р°РґР°РЅС‹ в конфигРµ")

            print("     Telegram-уведомления не Р±СѓРґСѓС‚ работать.")

    else:

        print("  в„№пёЏ  РљоРЅС„иРіСѓСЂР°С†иСЏ Telegram не найденР° (опционально)")

        print("     РЎРєоРїиСЂСѓР№С‚Рµ telegram_config.json.example в telegram_config.json")

        print("     и укажите токен бота и chat_ids для СѓвРµРґоРјР»РµРЅиР№.")

    

    # Локальный IP

    print("\nрџ“Њ РЎРµС‚РµвР°СЏ иРЅС„оСЂРјР°С†иСЏ:")

    local_ip = get_local_ip()

    print(f"  рџЊђ Локальный IP: {local_ip}")

    print(f"  рџ“± РЎсС‹Р»РєР° для Р»оРєР°Р»Рєи: http://{local_ip}:8080")

    

    public_ip = get_public_ip()

    if public_ip:

        print(f"  рџЊЌ Р’неС€РЅиР№ IP: {public_ip}")

        print(f"  рџ”— РЎсС‹Р»РєР° из интернета (посР»Рµ РїСЂоР±СЂосР° поСЂС‚Р°): http://{public_ip}:8080")

    else:

        print("  вљ пёЏ  Р’неС€РЅиР№ IP не определён (проверьте иРЅС‚РµСЂнеС‚)")

    

    print("\n" + "=" * 60)

    print("РџР РћР’Р•Р РљРђ Р—РђР’Р•Р РЁР•РќРђ")

    print("=" * 60 + "\n")





def _run_tunnel_and_send_one_message(link_local, public_ip):

    """Р’ фоне запустить localtunnel; когда есть ссылка вЂ” отправить второе сообщение. Процесс С‚СѓРЅнеР»СЏ не завершаем вЂ” инаС‡Рµ ссылка перестаёт работать."""

    global _tunnel_process

    token, chat_ids, _, tunnel_open_base = _load_telegram_config()

    if not token or not chat_ids:

        return

    password = public_ip or "(СѓР·наР№С‚Рµ на 2ip.ru)"

    tunnel_url = None

    # Р›оРі в РїР°РїРєРµ с РїСЂР°вР°Рји на Р·Р°РїисСЊ (при СѓсС‚Р°РЅовРєРµ в Program Files вЂ” %LOCALAPPDATA%\GrafikRaboty)

    try:

        from app_paths import DATA_DIR

        tunnel_log = os.path.join(DATA_DIR, "tunnel_output.txt")

    except ImportError:

        tunnel_log = os.path.join(BASE_DIR, "tunnel_output.txt")

    # Р¤оСЂРјР°С‚С‹ вС‹воРґР° localtunnel (loca.lt, localtunnel.me) и поС…оР¶иРµ С‚СѓРЅнеР»и

    url_patterns = (

        r"https://[a-zA-Z0-9\-]+\.loca\.lt[/\s\)\"\']?",

        r"https://[a-zA-Z0-9\-]+\.localtunnel\.me[/\s\)\"\']?",

        r"https://[^\s\)\"\']+loca\.lt[/\s\)\"\']?",

        r"https://[^\s\)\"\']+localtunnel\.me[/\s\)\"\']?",

        r"https://[a-zA-Z0-9\-]+\.loca\.lt",

        r"https://[a-zA-Z0-9\-]+\.localtunnel\.me",

    )

    # РќР°Р№С‚и Node.js (в С‚.С‡. в Program Files вЂ” при запуске из СЏСЂР»С‹РєР° PATH С‡Р°сС‚о Р±РµР· Node)

    node_dir, npx_name = _find_node_npx()

    if not node_dir:

        _tunnel_process = None

        fallback = (

            "рџ“… РќР°поРјинаРЅиРµ: сРµСЂвРµСЂ РіСЂР°С„иРєР° СЂР°Р±оС‚С‹ запущен.\n\n"

            "рџЏ  Р›оРєР°Р»РєР° (С‚Р° же сРµС‚СЊ): %s\n\n"

            "рџЊђ РўСѓРЅнеР»СЊ не удалось поРґРЅСЏС‚СЊ: не найден Node.js. РЈсС‚Р°РЅовиС‚Рµ с https://nodejs.org или укажите РїСѓС‚СЊ в telegram_config.json: \"node_dir\": \"C:\\\\Program Files\\\\nodejs\". "

            "РР»и испоР»СЊР·СѓР№С‚Рµ Р»оРєР°Р»РєСѓ в той же WiвЂ‘Fi.\n\n"

            "рџ”ђ Р’С…оРґ: admin / admin или учётные записи сотрудников."

        ) % link_local

        if _send_telegram(token, chat_ids, fallback):

            print("рџ“¤ Р’ Telegram оС‚РїСЂР°вР»РµРЅо напоРјинаРЅиРµ (Node.js не установлен).")

        return

    env = os.environ.copy()

    env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")

    # РџоР»РЅС‹Р№ РїСѓС‚СЊ Рє npx вЂ” инаС‡Рµ из СЏСЂР»С‹РєР°/СѓсС‚Р°РЅовС‰иРєР° shell РјожеС‚ не наР№С‚и npx в PATH

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

        # Р—Р°РїСѓсРє npx с Р·Р°С…вР°С‚оРј вС‹воРґР° в СЂРµР°Р»СЊРЅоРј вСЂРµРјРµРЅи (Р±РµР· Р±СѓС„РµСЂР° shell) вЂ” С‚Р°Рє ссылка наС…оРґиС‚сСЏ наРґС‘Р¶неРµ

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

        for _ in range(120):  # Рґо 60 сРµРє

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

                print("рџ“¤ Р’ Telegram оС‚РїСЂР°вР»РµРЅо сообщение со ссС‹Р»РєоР№ С‚СѓРЅнеР»СЏ (доступ с телефона/из интернета).")

        else:

            # РўСѓРЅнеР»СЊ не вС‹РґР°Р» ссС‹Р»РєСѓ вЂ” вС‹вРµсС‚и в консоль посР»РµРґРЅиРµ сС‚СЂоРєи Р»оРіР° для оС‚Р»Р°РґРєи

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

                print("вљ пёЏ  РўСѓРЅнеР»СЊ (посР»РµРґРЅСЏСЏ сС‚СЂоРєР° Р»оРіР°): %s" % log_hint)

            else:

                print("вљ пёЏ  РўСѓРЅнеР»СЊ не вС‹РґР°Р» ссС‹Р»РєСѓ. Р›оРі: %s" % tunnel_log)

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

                "рџ“… РќР°поРјинаРЅиРµ: сРµСЂвРµСЂ РіСЂР°С„иРєР° СЂР°Р±оС‚С‹ запущен.\n\n"

                "рџЏ  Р›оРєР°Р»РєР° (С‚Р° же сРµС‚СЊ): %s\n\n"

                "рџЊђ РўСѓРЅнеР»СЊ не удалось поРґРЅСЏС‚СЊ (сРµС‚СЊ или сРµСЂвис localtunnel). Р”Р»СЏ доступР° с телефона испоР»СЊР·СѓР№С‚Рµ ссС‹Р»РєСѓ вС‹С€Рµ в той же WiвЂ‘Fi.\n\n"

                "рџ”ђ Р’С…оРґ: admin / admin или учётные записи сотрудников."

            ) % link_local

            if _send_telegram(token, chat_ids, fallback):

                print("рџ“¤ Р’ Telegram оС‚РїСЂР°вР»РµРЅо напоРјинаРЅиРµ (Р»оРєР°Р»РєР°, С‚СѓРЅнеР»СЊ не поРґРЅСЏС‚).")

    except Exception as e:

        print("вљ пёЏ  РўСѓРЅнеР»СЊ не Р·Р°РїСѓсС‚иР»сСЏ (для внеС€неР№ ссС‹Р»Рєи нужен Node.js): %s" % e)

        _tunnel_process = None

        token, chat_ids = _load_telegram_config()[:2]

        if token and chat_ids:

            fallback = (

                "рџ“… РЎРµСЂвРµСЂ РіСЂР°С„иРєР° СЂР°Р±оС‚С‹ запущен.\n\nрџЏ  Р›оРєР°Р»РєР°: %s\n\n"

                "РўСѓРЅнеР»СЊ не запущен. Р’С…оРґ: admin / admin или учётные записи сотрудников."

            ) % link_local

            _send_telegram(token, chat_ids, fallback)




def _send_vk_startup_notification(local_ip, link_local, link_public):
    """Отправить VK уведомление о запуске сервера"""
    try:
        import vk_startup
        # Получим URL туннеля из файла
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

        # Р—Р°РїСѓсРєР°РµРј С‚СѓРЅнеР»СЊ в фоне - сообщение оС‚РїСЂР°виС‚сСЏ из tunnel_launcher.py

        t = threading.Thread(target=_run_tunnel_and_send_one_message, args=(link_local, get_public_ip()), daemon=True)

        t.start()

        print("вЏі РўСѓРЅнеР»СЊ Р·Р°РїСѓсРєР°РµС‚сСЏ в фоне вЂ” сообщение приРґС‘С‚ в Telegram.")

    else:

        try:

            from app_paths import DATA_DIR

            config_path = os.path.join(DATA_DIR, "telegram_config.json")

        except ImportError:

            config_path = os.path.join(BASE_DIR, "telegram_config.json")

        print("рџ’Ў Р§С‚оР±С‹ при запуске присС‹Р»Р°С‚СЊ ссС‹Р»РєСѓ в Telegram: оС‚РєСЂоР№С‚Рµ С„Р°Р№Р»")

        print("   %s" % config_path)

        print("   РґоР±Р°вСЊС‚Рµ bot_token и chat_ids (иРЅсС‚СЂСѓРєС†иСЏ: TELEGRAM_РќРђРЎРўР РћР™РљРђ.txt)")



def start_desktop_client():

    """Р—Р°РїСѓсС‚иС‚СЊ РґРµсРєС‚оРїРЅоРµ приР»ожеРЅиРµ на СЌС‚оРј РєоРјРїСЊСЋС‚РµСЂРµ (Р±РµР· Р»иС€неРіо консольРЅоРіо окна)"""

    global _client_process

    client_script = os.path.join(BASE_DIR, 'client.py')

    if not os.path.isfile(client_script):

        print("вљ пёЏ  Р¤Р°Р№Р» client.py не найден, десктопный клиент не запущен.")

        return

    try:

        # РќР° Windows испоР»СЊР·СѓРµРј pythonw, чтобы не оС‚РєСЂС‹вР°Р»осСЊ второе консольРЅоРµ оРєРЅо

        if sys.platform == 'win32':

            python_dir = os.path.dirname(sys.executable)

            pythonw = os.path.join(python_dir, 'pythonw.exe')

            executable = pythonw if os.path.isfile(pythonw) else sys.executable

        else:

            executable = sys.executable

        print("рџ–ҐпёЏ  Р—Р°РїСѓсРє РґРµсРєС‚оРїРЅоРіо клиентР° (оРєРЅо = вРµР±-иРЅС‚РµСЂС„РµР№с)...")

        _client_process = subprocess.Popen(

            [executable, client_script, "--webview"],

            cwd=BASE_DIR,

            stdin=subprocess.DEVNULL,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL,

        )

        if _client_process.poll() is None:

            print("вњ… Р”РµсРєС‚оРїРЅС‹Р№ клиент запущен (оРєРЅо РїСЂоРіСЂР°РјРјС‹)")

    except Exception as e:

        print(f"вљ пёЏ  РќРµ удалось запустить десктопный клиент: {e}")





def main():

    """Р“Р»Р°внаСЏ С„СѓРЅРєС†иСЏ Р·Р°РїСѓсРєР°"""

    global _tunnel_process

    

    # РЎоР·РґР°С‘Рј PID С„Р°Р№Р» для воР·РјоР¶РЅосС‚и осС‚Р°РЅовРєи

    # PID С„Р°Р№Р» С‚РµРїРµСЂСЊ в DATA_DIR (Р±РµР· РїСЂоР±Р»РµРј с РїСЂР°вР°Рји доступР°)

    try:

        from app_paths import DATA_DIR

        pid_file = os.path.join(DATA_DIR, 'server.pid')

        with open(pid_file, 'w', encoding='utf-8') as f:

            f.write(str(os.getpid()))

        print(f"вњ… PID С„Р°Р№Р» соР·РґР°РЅ: {pid_file}")

    except Exception as e:

        print(f"вљ пёЏ  РќРµ удалось соР·РґР°С‚СЊ PID С„Р°Р№Р» (неРєСЂиС‚иС‡РЅо): {e}")

    

    print("=" * 60)

    print("рџљЂ Р—Р°РїСѓсРє сисС‚РµРјС‹ СѓРїСЂР°вР»РµРЅиСЏ РіСЂР°С„иРєоРј СЂР°Р±оС‚С‹")

    print("=" * 60)



    _run_startup_checks()

    

    # РђвС‚оРјР°С‚иС‡РµсРєР°СЏ СѓсС‚Р°РЅовРєР° AI Р·Р°висиРјосС‚РµР№

    _install_ai_dependencies()



    # РќР° Р»СЋР±оРј РєоРјРїРµ Р°вС‚оРјР°С‚иС‡РµсРєи: Р»оРєР°Р»СЊРЅС‹Р№ и внешний IP

    local_ip = get_local_ip()

    print("\nвЏі РћРїСЂРµРґРµР»РµРЅиРµ внеС€неРіо IP для СѓРґР°Р»С‘РЅРЅоРіо доступР°...")

    public_ip = get_public_ip()

    link_local = f"http://{local_ip}:8080"

    link_public = f"http://{public_ip}:8080" if public_ip else None



    print(f"\nрџ“Ў Локальный IP (С‚Р° же сРµС‚СЊ WiвЂ‘Fi): {local_ip}")

    if public_ip:

        print(f"рџ“Ў Р’неС€РЅиР№ IP (иРЅС‚РµСЂнеС‚): {public_ip}")

    print(f"\nрџ“± РЎРЎР«Р›РљР Р”Р›РЇ РЎРћРўР РЈР”РќРР¦ (сРєиРЅСЊС‚Рµ РЅСѓР¶РЅСѓСЋ):")

    print(f"   вЂў Р’ той же сРµС‚и:     {link_local}")

    if link_public:

        print(f"   вЂў РЈРґР°Р»С‘РЅРЅо (иРЅС‚РµСЂнеС‚): {link_public}")

    else:

        print(f"   вЂў РЈРґР°Р»С‘РЅРЅо: насС‚СЂоР№С‚Рµ РїСЂоР±СЂос поСЂС‚Р° 8080 или С‚СѓРЅнеР»СЊ (сРј. Р’РќР•РЁРќРР™_Р”РћРЎРўРЈРџ.txt)")

    print(f"\nрџЊђ РќР° СЌС‚оРј РџРљ: http://127.0.0.1:8080")

    print(f"рџ’» Р”РµсРєС‚оРї: {local_ip}:5000")

    print(f"\nрџ”ђ РЈС‡РµС‚РЅС‹Рµ данные:")

    print(f"   РђРґРјиРЅ: admin / admin")

    print(f"   РЎоС‚СЂСѓРґРЅиРєи: вР°Р»РµСЂиСЏ / pass123, оР»СЊРіР° / pass456")

    print("\n" + "=" * 60)

    print("вЏі Р—Р°РїСѓсРє сРµСЂвРµСЂов...")

    print("=" * 60 + "\n")

    

    # Р—Р°РїСѓсРєР°РµРј socket сРµСЂвРµСЂ в оС‚РґРµР»СЊРЅоРј поС‚оРєРµ

    socket_thread = threading.Thread(target=start_socket_server, daemon=True)

    socket_thread.start()

    

    # Р”Р°РµРј время на Р·Р°РїСѓсРє socket сРµСЂвРµСЂР°

    time.sleep(2)

    

    # Р—Р°РїСѓсРєР°РµРј вРµР±-сРµСЂвРµСЂ в оС‚РґРµР»СЊРЅоРј поС‚оРєРµ

    web_thread = threading.Thread(target=start_web_server, daemon=True)

    web_thread.start()

    

    # Р–РґС‘Рј, поРєР° вРµР±-сРµСЂвРµСЂ наС‡РЅС‘С‚ сР»СѓС€Р°С‚СЊ поСЂС‚ 8080 (Рґо 30 сРµРє вЂ” посР»Рµ СѓсС‚Р°РЅовРєи РїРµСЂвС‹Р№ Р·Р°РїСѓсРє РјожеС‚ Р±С‹С‚СЊ РґоР»СЊС€Рµ)

    print("вЏі РћР¶иРґР°РЅиРµ РіоС‚овРЅосС‚и вРµР±-сРµСЂвРµСЂР° (поСЂС‚ 8080)...")

    if wait_for_port(8080, timeout_sec=30):

        print("вњ… Р’РµР±-сРµСЂвРµСЂ РіоС‚ов.")

    else:

        print("вљ пёЏ  Р’РµР±-сРµСЂвРµСЂ не оС‚вРµС‚иР» Р·Р° 30 с. РџСЂовРµСЂСЊС‚Рµ оС€иР±Рєи вС‹С€Рµ.")

    

    if check_port(8080):

        print("\nвљ пёЏ  Р’РќРРњРђРќРР•: Р’РµР±-сРµСЂвРµСЂ не Р·Р°РїСѓсС‚иР»сСЏ!")

        print("   РџСЂовРµСЂСЊС‚Рµ оС€иР±Рєи вС‹С€Рµ или Р·Р°РїСѓсС‚иС‚Рµ: python check_and_install.py")

    else:

        print("\nвњ… РЎРµСЂвРµСЂС‹ запущенС‹ СѓсРїРµС€РЅо!")

    print(f"\nрџ“± Р’РµР±-иРЅС‚РµСЂС„РµР№с: http://{local_ip}:8080")

    print("рџ–ҐпёЏ  РќР° СЌС‚оРј РєоРјРїСЊСЋС‚РµСЂРµ С‚Р°Рєже запущено РґРµсРєС‚оРїРЅоРµ приР»ожеРЅиРµ.")

    print("\nрџ’Ў РџоРґРєР»СЋС‡РµРЅиРµ:")

    print(f"   Р’ той же сРµС‚и в†’ {link_local}")

    if link_public:

        print(f"   РР· интернета в†’ {link_public} (РґоР»жеРЅ Р±С‹С‚СЊ РїСЂоР±СЂос поСЂС‚Р° 8080 на СЂоСѓС‚РµСЂРµ)")

    print("   Р›оРіиРЅ/пароль: admin / admin или вС‹данные учётные записи.")

    

    # РРЅС„оСЂРјР°С†иСЏ о РјоРЅиС‚оСЂиРЅРіРµ С‚СѓРЅнеР»СЏ

    print("\nрџ”Ќ РњРћРќРРўРћР РРќР“ ТУННЕЛЯ:")

    print(f"   РЎС‚Р°С‚Сѓс С‚СѓРЅнеР»СЏ: {link_local}/tunnel-monitor")

    print(f"   API сС‚Р°С‚СѓсР°: {link_local}/api/tunnel-status")

    print(f"   API Р»оРіов: {link_local}/api/tunnel-logs")

    print(f"   API РїСЂовРµСЂРєи поСЂС‚Р°: {link_local}/api/port-check")

    

    if not public_ip:

        print("\nвљ пёЏ  Р’неС€РЅиР№ IP не определён. РЈРґР°Р»С‘РЅРЅС‹Р№ доступ: РїСЂоР±СЂос поСЂС‚Р° 8080 или С‚СѓРЅнеР»СЊ вЂ” сРј. Р’РќР•РЁРќРР™_Р”РћРЎРўРЈРџ.txt")

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

    print("РќР°Р¶РјиС‚Рµ Ctrl+C для осС‚Р°РЅовРєи сРµСЂвРµСЂов и РїСЂоРіСЂР°РјРјС‹")

    print("=" * 60 + "\n")

    

    # РЎСЂР°Р·Сѓ оС‚РєСЂС‹вР°РµРј Р±СЂР°СѓР·РµСЂ со сС‚СЂР°РЅиС†РµР№ входа (посР»Рµ СѓсС‚Р°РЅовРєи поР»СЊР·овР°С‚РµР»СЊ сСЂР°Р·Сѓ виРґиС‚ иРЅС‚РµСЂС„РµР№с)

    # /login и ?v=2 чтобы не Р±СЂР°С‚СЊ сС‚СЂР°РЅиС†Сѓ из РєСЌС€Р° Р±СЂР°СѓР·РµСЂР°/окна

    if not check_port(8080):

        try:

            webbrowser.open('http://127.0.0.1:8080/login')

        except Exception:

            pass

    

    # Р–РґС‘Рј, поРєР° socket-сРµСЂвРµСЂ (5000) наС‡РЅС‘С‚ сР»СѓС€Р°С‚СЊ вЂ” чтобы десктопный клиент РјоРі поРґРєР»СЋС‡иС‚СЊсСЏ

    print("вЏі РћР¶иРґР°РЅиРµ РіоС‚овРЅосС‚и socket-сРµСЂвРµСЂР° (поСЂС‚ 5000)...")

    if wait_for_port(5000, timeout_sec=15):

        print("вњ… Socket-сРµСЂвРµСЂ РіоС‚ов.")

    else:

        print("вљ пёЏ  Socket-сРµСЂвРµСЂ не оС‚вРµС‚иР» Р·Р° 15 с. Р”РµсРєС‚оРїРЅоРµ оРєРЅо оС‚РєСЂоРµС‚ вРµР±-иРЅС‚РµСЂС„РµР№с.")

    

    # Р—Р°РїСѓсРєР°РµРј десктопный клиент (оРєРЅо = вРµР±-иРЅС‚РµСЂС„РµР№с, иРґРµРЅС‚иС‡РЅо Р±СЂР°СѓР·РµСЂСѓ)

    start_desktop_client()

    

    # РРєоРЅРєР° в трее: В«РћС‚РєСЂС‹С‚СЊВ» (Р±СЂР°СѓР·РµСЂ), В«Р’С‹С…оРґВ»

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

            'grafik', img, 'Р’РµС‚Р“иРґ РєоСЂпоСЂР°С‚ивРЅС‹Р№ РіСЂР°С„иРє',

            menu=pystray.Menu(

                pystray.MenuItem('РћС‚РєСЂС‹С‚СЊ', lambda i, _: webbrowser.open('http://127.0.0.1:8080/login')),

                pystray.MenuItem('Р’С‹С…оРґ', _on_tray_exit)

            )

        )

        _tray_thread = threading.Thread(target=lambda: _tray_icon_obj.run(), daemon=True)

        _tray_thread.start()

    except Exception:

        _tray_icon_obj = None

    

    # Р”РµСЂР¶иРј РїСЂоРіСЂР°РјРјСѓ запущенРЅоР№ (выход по Ctrl+C или по кнопке В«Р’С‹С…оРґВ» в трее)

    try:

        while not _tray_exit:

            time.sleep(0.5)

    except KeyboardInterrupt:

        pass

    if _tray_exit:

        print("\nрџ›‘ Р’С‹С…оРґ из С‚СЂРµСЏ.")

    print("\n\nрџ›‘ РћсС‚Р°РЅовРєР° сРµСЂвРµСЂов и РїСЂоРіСЂР°РјРјС‹...")

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

        print("вњ… РўСѓРЅнеР»СЊ осС‚Р°РЅовР»РµРЅ.")

    if _client_process is not None and _client_process.poll() is None:

        try:

            _client_process.terminate()

            _client_process.wait(timeout=3)

        except Exception:

            _client_process.kill()

        print("вњ… Р”РµсРєС‚оРїРЅС‹Р№ клиент Р·Р°РєСЂС‹С‚.")

    print("вњ… РЎРµСЂвРµСЂС‹ осС‚Р°РЅовР»РµРЅС‹.")



if __name__ == "__main__":

    main()





