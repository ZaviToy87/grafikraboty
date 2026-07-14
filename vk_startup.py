# -*- coding: utf-8 -*-
"""
Отправка VK уведомлений при запуске сервера v2.0
Вызывается из main_launcher.py
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def send_vk_startup_notification(tunnel_url, password, link_local, local_ip):
    """
    Отправить VK уведомление о запуске сервера v2.0 — КОНТРАСТНОЕ И ЯРКОЕ:
    - В ГРУППУ (чат сообщества)
    - В ЛИЧКУ админу

    Args:
        tunnel_url: URL туннеля
        password: Пароль (внешний IP)
        link_local: Локальная ссылка
        local_ip: Локальный IP
    """
    try:
        import vk_bot

        config = vk_bot.get_config()
        if not config or not config.get('service_token'):
            print("[VK] Токен не настроен — пропускаем")
            return False

        group_id = config.get('group_id')
        admin_vk_id = config.get('admin_vk_id')
        chat_peer_id = config.get('chat_peer_id', 2000000001)
        
        # Получаем актуальный публичный IP
        public_ip = vk_bot.get_public_ip() or local_ip

        if not group_id:
            print("[VK] Group ID не настроен — пропускаем")
            return False

        # 🔥 НОВОЕ ФОРМАТИРОВАНИЕ v2.0
        msg = (
            f"🚀 СЕРВЕР ЗАПУЩЕН — ВЕРСИЯ 2.0 🚀\n\n"
            
            f"⏰ Время запуска: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 ПОСТОЯННАЯ ССЫЛКА:\n"
            f"`{link_local}/get-tunnel-link`\n\n"
            
            f"🔐 ПАРОЛЬ: `{public_ip}`\n"
            f"_(это ваш внешний IP — не меняется)_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"🌐 ТУННЕЛЬ:\n"
            f"`{tunnel_url}`\n\n"
            
            f"📍 ЛОКАЛЬНАЯ СЕТЬ (Wi-Fi):\n"
            f"👉 `{link_local}`\n\n"
            
            f"🌍 ВНЕШНИЙ IP (проброс):\n"
            f"👉 `http://{public_ip}:8080`\n\n"
            
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 СОТРУДНИКАМ:\n"
            f"• Дома (Wi-Fi): {link_local}\n"
            f"• Извне (туннель): {tunnel_url}\n"
            f"• Извне (проброс): http://{public_ip}:8080\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"📊 Мониторинг:\n"
            f"• Статус туннеля: {link_local}/tunnel-status\n"
            f"• Автоперезапуск: включён\n\n"
            
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 БЫСТРЫЙ ДОСТУП:\n"
            f"• Открыть график: {link_local}\n"
            f"• Статус туннеля: {link_local}/tunnel-status\n\n"
            
            f"✅ v2.0 — Все IP актуальны!"
        )

        # ОТПРАВЛЯЕМ В ГРУППУ
        try:
            vk_bot.send_message(
                peer_id=int(chat_peer_id),
                message=msg
            )
            print(f"[VK v2.0] ✅ Уведомление отправлено в группу (peer_id={chat_peer_id})")
        except Exception as e:
            print(f"[VK v2.0] ❌ Ошибка отправки в группу: {e}")

        # ОТПРАВЛЯЕМ В ЛИЧКУ АДМИНУ
        if admin_vk_id:
            try:
                vk_bot.send_message(
                    user_id=int(admin_vk_id),
                    message=msg
                )
                print(f"[VK v2.0] ✅ Уведомление отправлено админу (vk_id={admin_vk_id})")
            except Exception as e:
                print(f"[VK v2.0] ❌ Ошибка отправки админу: {e}")

        return True
        
    except Exception as e:
        print(f"[VK v2.0] ❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("Тест VK уведомлений v2.0...")
    send_vk_startup_notification(
        tunnel_url="https://test.loca.lt",
        password="1.2.3.4",
        link_local="http://127.0.0.1:8080",
        local_ip="192.168.1.100"
    )
