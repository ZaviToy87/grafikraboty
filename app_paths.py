# app_paths.py — пути к данным приложения (запись возможна при установке в Program Files)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _writable_data_dir():
    """Папка для БД, логов и загрузок: в профиле пользователя, если приложение в Program Files."""
    try:
        if "Program Files" in BASE_DIR or "Program Files (x86)" in BASE_DIR:
            appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or ""
            if appdata:
                data_dir = os.path.join(appdata, "GrafikRaboty")
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
    except Exception:
        pass
    return BASE_DIR

DATA_DIR = _writable_data_dir()
DB_PATH = os.path.join(DATA_DIR, "schedule.db")
SERVER_LOG_PATH = os.path.join(DATA_DIR, "server.log")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
TUNNEL_INFO_PATH = os.path.join(DATA_DIR, "tunnel_info.txt")
CLIENT_LOG_PATH = os.path.join(DATA_DIR, "client.log")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

def ensure_uploads_dir():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
