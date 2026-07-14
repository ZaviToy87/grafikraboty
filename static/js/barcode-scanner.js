/**
 * Barcode Scanner Component
 * Сканер штрих-кодов через камеру телефона
 * Использует QuaggaJS для распознавания
 */

class BarcodeScanner {
  constructor(options = {}) {
    this.options = {
      inputId: options.inputId || 'barcode-input',
      scanButtonId: options.scanButtonId || 'scan-barcode-btn',
      modalId: options.modalId || 'barcode-scanner-modal',
      videoElementId: options.videoElementId || 'barcode-video',
      canvasElementId: options.canvasElementId || 'barcode-canvas',
      onScan: options.onScan || this.onScan.bind(this),
      ...options
    };
    
    this.scanner = null;
    this.isActive = false;
    this.stream = null;
    this.lastScan = 0;
    this.scanDelay = 1000; // Задержка между сканированиями 1 секунда
    
    this.init();
  }
  
  async init() {
    console.log('[BarcodeScanner] Инициализация');
    
    // Находим элементы
    this.inputElement = document.getElementById(this.options.inputId);
    this.scanButton = document.getElementById(this.options.scanButtonId);
    this.modal = document.getElementById(this.options.modalId);
    
    // Добавляем обработчик кнопки сканирования
    if (this.scanButton) {
      this.scanButton.addEventListener('click', () => this.start());
    }
    
    // Проверка поддержки камеры
    this.cameraSupported = await this.checkCameraSupport();
    console.log('[BarcodeScanner] Камера поддерживается:', this.cameraSupported);
  }
  
  // Проверка поддержки камеры
  async checkCameraSupport() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cameras = devices.filter(device => device.kind === 'videoinput');
      return cameras.length > 0;
    } catch (error) {
      console.error('[BarcodeScanner] Ошибка проверки камеры:', error);
      return false;
    }
  }
  
  // Запуск сканера
  async start() {
    console.log('[BarcodeScanner] Запуск сканера');
    
    if (!this.cameraSupported) {
      this.showError('Камера не найдена или не подключена');
      return;
    }
    
    try {
      // Запрос доступа к камере
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Задняя камера
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });
      
      // Показываем модальное окно
      this.showModal();
      
      // Инициализация QuaggaJS
      await this.initQuagga();
      
      this.isActive = true;
      
    } catch (error) {
      console.error('[BarcodeScanner] Ошибка доступа к камере:', error);
      this.showError('Не удалось получить доступ к камере. Проверьте разрешения.');
    }
  }
  
  // Инициализация QuaggaJS
  async initQuagga() {
    return new Promise((resolve, reject) => {
      // Динамическая загрузка QuaggaJS
      if (typeof Quagga === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js';
        script.onload = () => this.startQuagga(resolve, reject);
        script.onerror = reject;
        document.head.appendChild(script);
      } else {
        this.startQuagga(resolve, reject);
      }
    });
  }
  
  // Запуск QuaggaJS
  startQuagga(resolve, reject) {
    const videoElement = document.getElementById(this.options.videoElementId);
    
    Quagga.init({
      inputStream: {
        name: 'Live',
        type: 'LiveStream',
        target: document.getElementById(this.options.modalId),
        constraints: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      },
      decoder: {
        readers: [
          'ean_reader',
          'ean_8_reader',
          'code_128_reader',
          'code_39_reader',
          'code_39_vin_reader',
          'codabar_reader',
          'upc_reader',
          'upc_e_reader',
          'i2of5_reader',
          '2of5_reader',
          'code_93_reader'
        ],
        multiple: false
      },
      locator: {
        patchSize: 'medium',
        halfSample: true
      },
      numOfWorkers: 2,
      frequency: 10
    }, (err) => {
      if (err) {
        console.error('[BarcodeScanner] Ошибка инициализации Quagga:', err);
        reject(err);
        return;
      }
      
      console.log('[BarcodeScanner] Quagga инициализирована');
      
      // Запуск сканирования
      Quagga.start();
      
      // Обработка результатов
      Quagga.onDetected(this.onDetected.bind(this));
      
      // Отрисовка overlay
      const canvas = Quagga.canvas.dom.overlay;
      canvas.style.position = 'absolute';
      canvas.style.top = '0';
      canvas.style.left = '0';
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      canvas.style.pointerEvents = 'none';
      
      resolve();
    });
  }
  
  // Обнаружение штрих-кода
  onDetected(result) {
    const now = Date.now();
    
    // Защита от повторных сканирований
    if (now - this.lastScan < this.scanDelay) {
      return;
    }
    
    const code = result.codeResult.code;
    console.log('[BarcodeScanner] Обнаружен штрих-код:', code);
    
    this.lastScan = now;
    
    // Визуальная обратная связь
    this.showScanSuccess(code);
    
    // Вызов callback
    this.options.onScan(code, result);
    
    // Автоматическое закрытие через 1.5 секунды
    setTimeout(() => this.stop(), 1500);
  }
  
  // Обработка успешного сканирования
  onScan(code, result) {
    console.log('[BarcodeScanner] Callback onScan:', code);
    
    // Заполнение поля ввода
    if (this.inputElement) {
      this.inputElement.value = code;
      
      // Событие изменения
      const event = new Event('change', { bubbles: true });
      this.inputElement.dispatchEvent(event);
      
      // Поиск товара
      this.searchProduct(code);
    }
  }
  
  // Поиск товара по штрих-коду
  async searchProduct(code) {
    try {
      const response = await fetch(`/api/barcodes?search=${encodeURIComponent(code)}`);
      const data = await response.json();
      
      if (data.barcodes && data.barcodes.length > 0) {
        const product = data.barcodes[0];
        this.showProductFound(product);
      } else {
        this.showProductNotFound(code);
      }
    } catch (error) {
      console.error('[BarcodeScanner] Ошибка поиска:', error);
    }
  }
  
  // Показ найденного товара
  showProductFound(product) {
    const modal = document.getElementById('product-info-modal');
    if (modal) {
      document.getElementById('product-name').textContent = product.product_name;
      document.getElementById('product-price').textContent = `${product.price} ₽`;
      document.getElementById('product-barcode').textContent = product.barcode;
      modal.style.display = 'block';
    }
  }
  
  // Товар не найден
  showProductNotFound(code) {
    alert(`Штрих-код ${code} не найден в базе`);
  }
  
  // Остановка сканера
  stop() {
    console.log('[BarcodeScanner] Остановка');
    
    if (Quagga) {
      Quagga.stop();
    }
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.hideModal();
    this.isActive = false;
  }
  
  // Показ модального окна
  showModal() {
    if (this.modal) {
      this.modal.style.display = 'flex';
      
      // Добавляем элементы сканера
      this.modal.innerHTML = `
        <div class="barcode-scanner-overlay">
          <div class="barcode-scanner-header">
            <h3>📷 Сканирование штрих-кода</h3>
            <button class="close-btn" onclick="window.barcodeScanner.stop()">×</button>
          </div>
          <div class="barcode-scanner-content">
            <video id="${this.options.videoElementId}" autoplay playsinline></video>
            <canvas id="${this.options.canvasElementId}"></canvas>
            <div class="scanner-guide">
              <div class="guide-frame"></div>
              <p>Наведите камеру на штрих-код</p>
            </div>
          </div>
          <div class="barcode-scanner-footer">
            <button class="btn btn-secondary" onclick="document.getElementById('barcode-input').focus()">
              ⌨️ Ввести вручную
            </button>
          </div>
        </div>
      `;
    }
  }
  
  // Скрытие модального окна
  hideModal() {
    if (this.modal) {
      this.modal.style.display = 'none';
    }
  }
  
  // Показ ошибки
  showError(message) {
    alert('❌ ' + message);
  }
  
  // Показ успеха сканирования
  showScanSuccess(code) {
    const overlay = document.querySelector('.barcode-scanner-overlay');
    if (overlay) {
      const flash = document.createElement('div');
      flash.className = 'scan-success';
      flash.innerHTML = `
        <div class="success-checkmark">
          <div class="check-icon">✓</div>
        </div>
        <div class="success-code">${code}</div>
      `;
      flash.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(76, 175, 80, 0.8);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        animation: fadeIn 0.3s ease;
      `;
      overlay.appendChild(flash);
      
      setTimeout(() => flash.remove(), 1500);
    }
  }
}

// CSS стили для сканера
const scannerStyles = document.createElement('style');
scannerStyles.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .barcode-scanner-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    flex-direction: column;
    z-index: 10000;
  }
  
  .barcode-scanner-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .barcode-scanner-header h3 {
    margin: 0;
    font-size: 18px;
  }
  
  .close-btn {
    background: transparent;
    border: none;
    color: white;
    font-size: 28px;
    cursor: pointer;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  .barcode-scanner-content {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  
  #barcode-video, #barcode-canvas {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .scanner-guide {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: white;
  }
  
  .guide-frame {
    width: 250px;
    height: 150px;
    border: 3px solid #4CAF50;
    border-radius: 10px;
    margin: 0 auto 15px;
    box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { border-color: #4CAF50; }
    50% { border-color: #8BC34A; }
  }
  
  .scanner-guide p {
    margin: 0;
    font-size: 14px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  }
  
  .barcode-scanner-footer {
    background: rgba(0, 0, 0, 0.8);
    padding: 15px;
    text-align: center;
  }
  
  .btn-secondary {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 14px;
    cursor: pointer;
  }
  
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  .success-checkmark {
    width: 80px;
    height: 80px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
    animation: scaleIn 0.3s ease;
  }
  
  @keyframes scaleIn {
    from { transform: scale(0); }
    to { transform: scale(1); }
  }
  
  .check-icon {
    font-size: 50px;
    color: #4CAF50;
    font-weight: bold;
  }
  
  .success-code {
    font-size: 24px;
    font-weight: bold;
  }
`;
document.head.appendChild(scannerStyles);

// Глобальный экземпляр
window.barcodeScanner = null;

// Инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
  window.barcodeScanner = new BarcodeScanner({
    inputId: 'barcode-input',
    scanButtonId: 'scan-barcode-btn',
    modalId: 'barcode-scanner-modal',
    onScan: (code, result) => {
      console.log('[BarcodeScanner] scanned:', code);
      // Автоматический поиск товара
      window.barcodeScanner.searchProduct(code);
    }
  });
});
