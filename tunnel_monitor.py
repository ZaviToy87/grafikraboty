#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tunnel Monitor with Auto-Restart and VK Notifications
Monitors localtunnel, auto-restarts on failure, sends VK notifications
"""

import os
import sys
import re
import json
import time
import subprocess
import threading
import logging
from datetime import datetime

# Setup logging
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'tunnel_monitor.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TunnelMonitor:
    def __init__(self, port=8080, max_restarts=-1, restart_delay=5):
        """
        Initialize tunnel monitor
        
        Args:
            port: Local port to tunnel (default 8080)
            max_restarts: Max restart attempts (-1 for unlimited)
            restart_delay: Delay between restarts in seconds
        """
        self.port = port
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.tunnel_process = None
        self.tunnel_url = None
        self.restart_count = 0
        self.running = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Paths
        try:
            from app_paths import DATA_DIR
            self.data_dir = DATA_DIR
        except ImportError:
            self.data_dir = self.base_dir
        
        self.tunnel_info_path = os.path.join(self.data_dir, 'tunnel_info.json')
        self.tunnel_log_path = os.path.join(LOGS_DIR, 'tunnel.log')
        
        # Find Node.js
        self.node_dir, self.npx_name = self._find_node_npx()
        
        logger.info(f"Tunnel Monitor initialized: port={port}, max_restarts={max_restarts}")
    
    def _find_node_npx(self):
        """Find Node.js and npx installation"""
        # Check common paths
        common_paths = [
            r"C:\Program Files\nodejs",
            r"C:\Program Files (x86)\nodejs",
            os.path.expanduser(r"~\AppData\Roaming\npm"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                npx_names = ['npx.cmd', 'npx.exe', 'npx']
                for name in npx_names:
                    if os.path.isfile(os.path.join(path, name)):
                        logger.info(f"Found Node.js at {path}")
                        return path, name
        
        # Check PATH
        import shutil
        npx_path = shutil.which('npx')
        if npx_path:
            node_dir = os.path.dirname(npx_path)
            logger.info(f"Found Node.js in PATH: {node_dir}")
            return node_dir, 'npx'
        
        logger.warning("Node.js not found!")
        return None, None
    
    def _load_vk_config(self):
        """Load VK configuration"""
        config_path = os.path.join(self.base_dir, 'vk_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _send_vk_message(self, message, peer_id=None):
        """Send VK message using direct API"""
        try:
            config = self._load_vk_config()
            token = config.get('token')
            group_id = config.get('group_id')
            
            if not token or not group_id:
                logger.warning("VK token or group_id not configured")
                return False
            
            # Use chat_peer_id if provided, otherwise use admin_vk_id
            if peer_id is None:
                chat_peer_id = config.get('chat_peer_id')
                if chat_peer_id:
                    peer_id = int(chat_peer_id)
                else:
                    admin_vk_id = config.get('admin_vk_id')
                    if admin_vk_id:
                        peer_id = int(admin_vk_id)
                    else:
                        logger.warning("No VK recipient configured")
                        return False
            
            # VK API endpoint
            import urllib.request
            import urllib.parse
            
            api_url = "https://api.vk.com/method/messages.send"
            
            # Determine if sending to user or chat
            if peer_id >= 2000000000:
                params = {
                    'peer_id': peer_id,
                    'message': message,
                    'random_id': int(time.time() * 1000),
                    'v': '5.131'
                }
            else:
                params = {
                    'user_id': peer_id,
                    'message': message,
                    'random_id': int(time.time() * 1000),
                    'v': '5.131'
                }
            
            data = urllib.parse.urlencode(params).encode('utf-8')
            req = urllib.request.Request(
                f"{api_url}?access_token={token}&v=5.131",
                data=data,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'response' in result:
                    logger.info(f"VK message sent to peer_id={peer_id}")
                    return True
                elif 'error' in result:
                    logger.error(f"VK API error: {result['error']}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send VK message: {e}")
            return False
    
    def _send_tunnel_notification(self, tunnel_url, password, is_restart=False):
        """Send tunnel notification to VK"""
        config = self._load_vk_config()
        admin_vk_id = config.get('admin_vk_id')
        chat_peer_id = config.get('chat_peer_id')
        
        if is_restart:
            msg = (
                f"⚠️ *Туннель перезапущен (попытка {self.restart_count})*\n\n"
                f"🌐 *Новая ссылка:*\n"
                f"`{tunnel_url}`\n\n"
                f"🔐 *Пароль:* `{password}`\n\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                f"Если туннель не работает — проверьте интернет."
            )
        else:
            msg = (
                f"✅ *Туннель запущен*\n\n"
                f"🌐 *Ссылка:*\n"
                f"`{tunnel_url}`\n\n"
                f"🔐 *Пароль:* `{password}`\n\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                f"Сервер работает стабильно."
            )
        
        # Send to admin
        if admin_vk_id:
            self._send_vk_message(msg, peer_id=int(admin_vk_id))
        
        # Send to chat if configured
        if chat_peer_id:
            self._send_vk_message(msg, peer_id=int(chat_peer_id))
    
    def _send_tunnel_error(self, error_message):
        """Send tunnel error notification to VK"""
        config = self._load_vk_config()
        admin_vk_id = config.get('admin_vk_id')
        
        if not admin_vk_id:
            return
        
        msg = (
            f"❌ *Туннель недоступен!*\n\n"
            f"Превышен лимит перезапусков ({self.restart_count}).\n\n"
            f"Ошибка: {error_message}\n\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"Требуется ручное вмешательство:\n"
            f"• Проверьте интернет\n"
            f"• Проверьте, запущен ли сервер на порту {self.port}\n"
            f"• Перезапустите сервер вручную"
        )
        
        self._send_vk_message(msg, peer_id=int(admin_vk_id))
    
    def _write_tunnel_info(self, tunnel_url, password):
        """Write tunnel info to JSON file"""
        try:
            info = {
                'tunnel_url': tunnel_url,
                'password': str(password),
                'started_at': datetime.now().isoformat(),
                'restart_count': self.restart_count
            }
            
            with open(self.tunnel_info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Tunnel info written to {self.tunnel_info_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write tunnel info: {e}")
            return False
    
    def _extract_tunnel_url(self, line):
        """Extract tunnel URL from log line"""
        patterns = [
            r"https://[a-zA-Z0-9\-]+\.loca\.lt",
            r"https://[a-zA-Z0-9\-]+\.localtunnel\.me",
            r"https://[^\s]+loca\.lt",
            r"https://[^\s]+localtunnel\.me",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                url = match.group(0).rstrip("/).\"' \t\n")
                if url.startswith("https://"):
                    return url
        return None
    
    def _start_tunnel(self):
        """Start localtunnel process"""
        if not self.node_dir:
            logger.error("Node.js not found! Cannot start tunnel.")
            return False
        
        npx_full = os.path.join(self.node_dir, self.npx_name)
        
        # Fallback to npx.cmd if needed
        if not os.path.isfile(npx_full):
            for alt_name in ['npx.cmd', 'npx.exe', 'npx']:
                alt_path = os.path.join(self.node_dir, alt_name)
                if os.path.isfile(alt_path):
                    npx_full = alt_path
                    self.npx_name = alt_name
                    break
        
        if not os.path.isfile(npx_full):
            logger.error(f"npx not found at {npx_full}")
            return False
        
        logger.info(f"Starting tunnel with {npx_full}")
        
        # Setup environment
        env = os.environ.copy()
        env["PATH"] = self.node_dir + os.pathsep + env.get("PATH", "")
        
        # Clear old log
        try:
            if os.path.exists(self.tunnel_log_path):
                os.remove(self.tunnel_log_path)
        except Exception:
            pass
        
        try:
            # Start tunnel process
            self.tunnel_process = subprocess.Popen(
                [npx_full, "--yes", "localtunnel", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.base_dir,
                env=env
            )
            
            logger.info(f"Tunnel process started (PID: {self.tunnel_process.pid})")
            
            # Read output in thread
            def read_output():
                try:
                    with open(self.tunnel_log_path, "w", encoding="utf-8", errors="replace") as logf:
                        while self.running and self.tunnel_process and self.tunnel_process.poll() is None:
                            line = self.tunnel_process.stdout.readline()
                            if not line:
                                break
                            
                            text = line.decode("utf-8", errors="replace")
                            logf.write(text)
                            logf.flush()
                            
                            # Extract URL
                            if not self.tunnel_url:
                                url = self._extract_tunnel_url(text)
                                if url:
                                    self.tunnel_url = url
                                    logger.info(f"Tunnel URL extracted: {url}")
                                    
                                    # Get password (use public IP or placeholder)
                                    password = self._get_public_ip() or "admin"
                                    
                                    # Write info
                                    self._write_tunnel_info(url, password)
                                    
                                    # Send notification
                                    is_restart = self.restart_count > 0
                                    self._send_tunnel_notification(url, password, is_restart=is_restart)
                                    
                except Exception as e:
                    logger.error(f"Error reading tunnel output: {e}")
            
            reader_thread = threading.Thread(target=read_output, daemon=True)
            reader_thread.start()
            
            # Wait for URL (up to 60 seconds)
            for _ in range(120):
                if self.tunnel_url:
                    return True
                if self.tunnel_process and self.tunnel_process.poll() is not None:
                    return False
                time.sleep(0.5)
            
            return self.tunnel_url is not None
            
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            self.tunnel_process = None
            return False
    
    def _get_public_ip(self):
        """Get public IP address"""
        try:
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                return response.read().decode('utf-8').strip()
        except Exception:
            return None
    
    def _check_tunnel_health(self):
        """Check if tunnel is healthy"""
        if not self.tunnel_process:
            return False
        
        # Check if process is running
        if self.tunnel_process.poll() is not None:
            logger.warning(f"Tunnel process exited with code {self.tunnel_process.poll()}")
            return False
        
        # Check if URL is still valid
        if not self.tunnel_url:
            return False
        
        # Try to access tunnel URL
        try:
            import urllib.request
            req = urllib.request.Request(self.tunnel_url, method='HEAD')
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Tunnel health check failed: {e}")
            # Don't fail immediately - might be temporary
            return True  # Assume healthy if process is running
    
    def _stop_tunnel(self):
        """Stop tunnel process"""
        if self.tunnel_process:
            try:
                logger.info("Stopping tunnel process...")
                self.tunnel_process.terminate()
                try:
                    self.tunnel_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Tunnel process didn't terminate gracefully, killing...")
                    self.tunnel_process.kill()
                    self.tunnel_process.wait(timeout=3)
            except Exception as e:
                logger.error(f"Error stopping tunnel: {e}")
            finally:
                self.tunnel_process = None
                self.tunnel_url = None
    
    def run(self):
        """Main monitor loop"""
        self.running = True
        logger.info("=" * 60)
        logger.info("Tunnel Monitor started")
        logger.info(f"Port: {self.port}, Max restarts: {self.max_restarts}")
        logger.info("=" * 60)
        
        while self.running:
            try:
                # Check if tunnel is running
                if not self._check_tunnel_health():
                    logger.warning("Tunnel is not healthy!")
                    
                    # Stop old process if any
                    if self.tunnel_process:
                        self._stop_tunnel()
                    
                    # Check restart limit
                    if self.max_restarts >= 0 and self.restart_count >= self.max_restarts:
                        logger.error(f"Max restarts ({self.max_restarts}) reached!")
                        self._send_tunnel_error("Max restarts reached")
                        break
                    
                    # Increment restart count
                    self.restart_count += 1
                    logger.info(f"Attempting restart #{self.restart_count}")
                    
                    # Delay before restart
                    if self.restart_count > 1:
                        logger.info(f"Waiting {self.restart_delay} seconds before restart...")
                        time.sleep(self.restart_delay)
                    
                    # Start new tunnel
                    if self._start_tunnel():
                        logger.info(f"Tunnel restarted successfully (attempt {self.restart_count})")
                    else:
                        logger.error(f"Failed to start tunnel (attempt {self.restart_count})")
                        
                        # Wait before next attempt
                        time.sleep(self.restart_delay * 2)
                else:
                    # Tunnel is healthy
                    if self.restart_count > 0:
                        logger.info(f"Tunnel running stably (restarts: {self.restart_count})")
                    
                    # Check periodically
                    time.sleep(30)
                    
            except KeyboardInterrupt:
                logger.info("Monitor interrupted by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
        
        # Cleanup
        self._stop_tunnel()
        logger.info("Tunnel Monitor stopped")
    
    def stop(self):
        """Stop the monitor"""
        self.running = False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Tunnel Monitor with Auto-Restart')
    parser.add_argument('--port', type=int, default=8080, help='Local port to tunnel')
    parser.add_argument('--max-restarts', type=int, default=-1, help='Max restart attempts (-1 for unlimited)')
    parser.add_argument('--restart-delay', type=int, default=5, help='Delay between restarts (seconds)')
    
    args = parser.parse_args()
    
    monitor = TunnelMonitor(
        port=args.port,
        max_restarts=args.max_restarts,
        restart_delay=args.restart_delay
    )
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        monitor.stop()


if __name__ == '__main__':
    main()
