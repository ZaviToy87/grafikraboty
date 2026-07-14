/**
 * PWA Installer & Setup
 * Скрипт для установки PWA приложения и регистрации Service Worker
 */

class PWAInstaller {
  constructor() {
    this.deferredPrompt = null;
    this.swRegistration = null;
    this.installButton = null;
    
    this.init();
  }
  
  async init() {
    // Проверка поддержки Service Worker
    if ('serviceWorker' in navigator) {
      console.log('[PWA] Service Worker поддерживается');
      await this.registerServiceWorker();
      await this.setupInstallPrompt();
      this.setupConnectionListener();
    } else {
      console.warn('[PWA] Service Worker не поддерживается');
    }
  }
  
  // Регистрация Service Worker
  async registerServiceWorker() {
    try {
      this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js', {
        scope: '/'
      });
      
      console.log('[PWA] Service Worker зарегистрирован:', this.swRegistration);
      
      // Проверка обновлений Service Worker
      this.swRegistration.addEventListener('updatefound', () => {
        const newWorker = this.swRegistration.installing;
        console.log('[PWA] Найдено обновление Service Worker');
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            this.showUpdateNotification();
          }
        });
      });
      
      // Отправка сообщения о версии
      if (this.swRegistration.active) {
        this.swRegistration.active.postMessage({ type: 'GET_VERSION' });
      }
      
    } catch (error) {
      console.error('[PWA] Ошибка регистрации Service Worker:', error);
    }
  }
  
  // Настройка кнопки установки
  async setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('[PWA] BeforeInstallPrompt событие');
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });
    
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] Приложение установлено');
      this.hideInstallButton();
      this.deferredPrompt = null;
      
      // Аналитика установки
      if (window.gtag) {
        gtag('event', 'pwa_installed', {
          event_category: 'PWA',
          event_label: 'Installed'
        });
      }
    });
  }
  
  // Показ кнопки установки
  showInstallButton() {
    // Проверяем не установлено ли уже приложение
    if (window.matchMedia('(display-mode: standalone)').matches) {
      console.log('[PWA] Уже запущено как приложение');
      return;
    }
    
    // Создаём или показываем кнопку установки
    let button = document.getElementById('pwa-install-btn');
    
    if (!button) {
      button = document.createElement('div');
      button.id = 'pwa-install-btn';
      button.innerHTML = `
        <div class="pwa-install-banner">
          <div class="pwa-install-content">
            <div class="pwa-install-icon">📱</div>
            <div class="pwa-install-text">
              <strong>Установить приложение</strong>
              <p>Быстрый доступ к графику и задачам</p>
            </div>
            <button class="pwa-install-action">Установить</button>
            <button class="pwa-install-close">×</button>
          </div>
        </div>
      `;
      button.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        animation: slideUp 0.3s ease;
      `;
      
      document.body.appendChild(button);
      
      // Обработчики событий
      button.querySelector('.pwa-install-action').addEventListener('click', () => {
        this.install();
      });
      
      button.querySelector('.pwa-install-close').addEventListener('click', () => {
        this.hideInstallButton();
      });
      
      // Автоскрытие через 10 секунд
      setTimeout(() => this.hideInstallButton(), 10000);
    } else {
      button.style.display = 'block';
    }
  }
  
  // Скрытие кнопки установки
  hideInstallButton() {
    const button = document.getElementById('pwa-install-btn');
    if (button) {
      button.style.display = 'none';
    }
  }
  
  // Установка приложения
  async install() {
    if (!this.deferredPrompt) {
      console.warn('[PWA] Нет события установки');
      return;
    }
    
    try {
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;
      
      console.log('[PWA] Результат установки:', outcome);
      this.deferredPrompt = null;
      
      if (outcome === 'accepted') {
        console.log('[PWA] Пользователь принял установку');
      } else {
        console.log('[PWA] Пользователь отменил установку');
      }
      
      this.hideInstallButton();
    } catch (error) {
      console.error('[PWA] Ошибка установки:', error);
    }
  }
  
  // Показ уведомления об обновлении
  showUpdateNotification() {
    const notification = document.createElement('div');
    notification.id = 'pwa-update-notification';
    notification.innerHTML = `
      <div class="pwa-update-banner">
        <div class="pwa-update-content">
          <span>🔄 Доступна новая версия приложения</span>
          <button class="pwa-update-action">Обновить</button>
        </div>
      </div>
    `;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9999;
      background: #4CAF50;
      color: white;
      padding: 15px 25px;
      border-radius: 10px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      animation: slideDown 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    notification.querySelector('.pwa-update-action').addEventListener('click', () => {
      if (this.swRegistration && this.swRegistration.waiting) {
        this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
      window.location.reload();
    });
    
    // Автоскрытие через 30 секунд
    setTimeout(() => notification.remove(), 30000);
  }
  
  // Слушатель соединения
  setupConnectionListener() {
    window.addEventListener('online', () => {
      console.log('[PWA] Соединение восстановлено');
      this.syncData();
    });
    
    window.addEventListener('offline', () => {
      console.log('[PWA] Соединение потеряно');
      this.showOfflineIndicator();
    });
  }
  
  // Показ индикатора офлайн
  showOfflineIndicator() {
    let indicator = document.getElementById('offline-indicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'offline-indicator';
      indicator.innerHTML = '📡 Нет соединения';
      indicator.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #f44336;
        color: white;
        text-align: center;
        padding: 10px;
        z-index: 10000;
        font-weight: bold;
      `;
      document.body.appendChild(indicator);
    } else {
      indicator.style.display = 'block';
    }
  }
  
  // Скрытие индикатора офлайн
  hideOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
      indicator.style.display = 'none';
    }
  }
  
  // Синхронизация данных при восстановлении соединения
  async syncData() {
    console.log('[PWA] Синхронизация данных...');
    
    if ('serviceWorker' in navigator && 'sync' in window.SyncManager) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-data');
        console.log('[PWA] Синхронизация запланирована');
      } catch (error) {
        console.log('[PWA] Фоновая синхронизация не поддерживается:', error);
      }
    }
    
    this.hideOfflineIndicator();
  }
  
  // Проверка режима отображения
  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }
  
  // Получить информацию о кэше
  async getCacheInfo() {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      let totalItems = 0;
      
      for (const name of cacheNames) {
        const cache = await caches.open(name);
        const requests = await cache.keys();
        totalItems += requests.length;
      }
      
      return {
        caches: cacheNames.length,
        items: totalItems
      };
    }
    return null;
  }
}

// Инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
  window.pwaInstaller = new PWAInstaller();
});

// CSS стили для PWA компонентов
const pwaStyles = document.createElement('style');
pwaStyles.textContent = `
  @keyframes slideUp {
    from { transform: translateX(-50%) translateY(100px); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }
  
  @keyframes slideDown {
    from { transform: translateX(-50%) translateY(-100px); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }
  
  .pwa-install-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    max-width: 400px;
  }
  
  .pwa-install-content {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .pwa-install-icon {
    font-size: 40px;
  }
  
  .pwa-install-text {
    flex: 1;
    color: white;
  }
  
  .pwa-install-text strong {
    display: block;
    font-size: 16px;
    margin-bottom: 5px;
  }
  
  .pwa-install-text p {
    font-size: 13px;
    opacity: 0.9;
    margin: 0;
  }
  
  .pwa-install-action {
    background: white;
    color: #667eea;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: bold;
    cursor: pointer;
    transition: transform 0.2s;
  }
  
  .pwa-install-action:hover {
    transform: scale(1.05);
  }
  
  .pwa-install-close {
    background: transparent;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 5px 10px;
    opacity: 0.7;
  }
  
  .pwa-install-close:hover {
    opacity: 1;
  }
  
  .pwa-update-banner {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .pwa-update-action {
    background: white;
    color: #4CAF50;
    border: none;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    cursor: pointer;
    margin-left: auto;
  }
`;
document.head.appendChild(pwaStyles);
