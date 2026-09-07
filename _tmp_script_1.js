
    // Обработчик навигации по вкладкам
    document.addEventListener('DOMContentLoaded', function() {
        const navItems = document.querySelectorAll('.nav-item');
        const pages = document.querySelectorAll('.page');
        
        // Функция показа страницы
        function showPage(pageId) {
            // Скрываем все страницы
            pages.forEach(page => {
                page.style.display = 'none';
            });
            
            // Убираем активный класс у всех пунктов меню
            navItems.forEach(item => {
                item.classList.remove('active');
            });
            
            // Показываем нужную страницу
            const targetPage = document.getElementById('page-' + pageId);
            if (targetPage) {
                targetPage.style.display = 'block';
            }
            
            // Подсвечиваем активный пункт меню
            const activeNavItem = document.querySelector('.nav-item[href="#' + pageId + '"]');
            if (activeNavItem) {
                activeNavItem.classList.add('active');
            }
            
            // Загружаем данные для страницы
            if (pageId === 'barcodes') {
                loadBarcodes(0);
            } else if (pageId === 'calendar') {
                if (typeof loadCalendar === 'function') loadCalendar();
            } else if (pageId === 'tasks') {
                if (typeof loadTasks === 'function') loadTasks();
            } else if (pageId === 'work-journal') {
                if (typeof loadWorkJournal === 'function') loadWorkJournal();
            } else if (pageId === 'chat') {
                if (typeof loadChat === 'function') loadChat();
            } else if (pageId === 'files') {
                if (typeof loadFiles === 'function') loadFiles();
            } else if (pageId === 'converter') {
                if (typeof loadConverter === 'function') loadConverter();
            } else if (pageId === 'analytics') {
                if (typeof initAnalyticsCharts === 'function') initAnalyticsCharts();
            } else if (pageId === 'admin') {
                if (typeof loadAdmin === 'function') loadAdmin();
            }

        }
        
        // Навешиваем обработчики кликов на пункты меню
        navItems.forEach(item => {
            item.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                // Внешние ссылки (не начинающиеся с #) — не блокируем, даём браузеру перейти
                if (href && !href.startsWith('#')) {
                    return;
                }
                e.preventDefault();
                if (href && href.startsWith('#')) {
                    const pageId = href.substring(1);
                    showPage(pageId);
                }
            });
        });
        
        // Показываем первую страницу по умолчанию (календарь)
        showPage('calendar');
        
        // Обработка hash в URL
        window.addEventListener('hashchange', function() {
            const hash = window.location.hash.substring(1);
            if (hash) {
                showPage(hash);
            }
        });
        
        // Если есть hash при загрузке - показываем соответствующую страницу
        if (window.location.hash) {
            showPage(window.location.hash.substring(1));
        }
    });

    // ========================================
    // ФУНКЦИИ УПРАВЛЕНИЯ ШТРИХ-КОДАМИ
    // ========================================

// Управление штрих-кодами
    let barcodeCurrentPage = 0;
    const barcodeLimit = 50;
    let barcodeTotal = 0;

    async function loadBarcodes(page = 0) {
        barcodeCurrentPage = page;
        const search = document.getElementById('barcode-search').value;
        const offset = page * barcodeLimit;
        
        try {
            const url = `/api/barcodes?limit=${barcodeLimit}&offset=${offset}&search=${encodeURIComponent(search)}`;
            const response = await fetch(url, {
                credentials: 'include'
            });
            const data = await response.json();
            
            barcodeTotal = data.total;
            document.getElementById('barcode-total').textContent = `Всего: ${data.total}`;
            document.getElementById('barcode-page-info').textContent = `Страница ${page + 1}`;
            
            const tbody = document.getElementById('barcodes-body');
            if (data.barcodes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Штрих-коды не найдены</td></tr>';
            } else {
                tbody.innerHTML = data.barcodes.map(bc => `
                    <tr onclick="event.stopPropagation();">
                        <td>${escapeHtml(bc.product_name)}</td>
                        <td class="barcode-cell" onclick="copyToClipboard('${escapeJs(bc.factory_barcode || '')}')" title="Кликните для копирования">${bc.factory_barcode || '—'}</td>
                        <td class="barcode-cell" onclick="copyToClipboard('${escapeJs(bc.internal_barcode)}')" title="Кликните для копирования" style="font-weight: bold; color: var(--primary);">${bc.internal_barcode}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="editBarcode(${bc.id}, '${escapeJs(bc.product_name)}', '${escapeJs(bc.factory_barcode || '')}', '${escapeJs(bc.internal_barcode)}')">✏️</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteBarcode(${bc.id})">🗑️</button>
                        </td>
                    </tr>
                `).join('');
            }
            
            document.getElementById('barcode-prev-btn').disabled = page === 0;
            document.getElementById('barcode-next-btn').disabled = (page + 1) * barcodeLimit >= data.total;
        } catch (e) {
            console.error('Ошибка загрузки штрих-кодов:', e);
            alert('Ошибка загрузки штрих-кодов');
        }
    }

    async function copyToClipboard(text) {
        if (!text) { showNotification('Штрих-код пуст', 'error'); return; }
        try {
            await navigator.clipboard.writeText(text);
            showNotification('📋 Штрих-код скопирован: ' + text, 'success');
        } catch (e) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showNotification('📋 Штрих-код скопирован: ' + text, 'success');
        }
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = 'copy-notification';
        notification.style.cssText = 'position:fixed;bottom:20px;right:20px;background:' + (type==='success'?'#22c55e':type==='error'?'#ef4444':'#6366f1') + ';color:white;padding:12px 20px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:10000;animation:slideIn 0.3s ease;';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    function showAddBarcodeModal() {
        document.getElementById('barcode-modal-title').textContent = 'Добавить штрих-код';
        document.getElementById('barcode-id').value = '';
        document.getElementById('barcode-product-name').value = '';
        document.getElementById('barcode-factory').value = '';
        document.getElementById('barcode-internal').value = '';
        document.getElementById('barcode-modal').style.display = 'flex';
    }

    function editBarcode(id, name, factory, internal) {
        document.getElementById('barcode-modal-title').textContent = 'Редактировать штрих-код';
        document.getElementById('barcode-id').value = id;
        document.getElementById('barcode-product-name').value = name;
        document.getElementById('barcode-factory').value = factory;
        document.getElementById('barcode-internal').value = internal;
        document.getElementById('barcode-modal').style.display = 'flex';
    }

    function closeBarcodeModal() { document.getElementById('barcode-modal').style.display = 'none'; }
    function closeImportModal() { document.getElementById('barcode-import-modal').style.display = 'none'; }

    async function saveBarcode() {
        const id = document.getElementById('barcode-id').value;
        const productName = document.getElementById('barcode-product-name').value.trim();
        const factory = document.getElementById('barcode-factory').value.trim();
        const internal = document.getElementById('barcode-internal').value.trim();

        if (!productName || !internal) { alert('Наименование и внутренний штрих-код обязательны'); return; }

        try {
            const url = id ? `/api/barcodes/${id}` : '/api/barcodes/add';
            const method = id ? 'PUT' : 'POST';
            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({product_name: productName, factory_barcode: factory, internal_barcode: internal})
            });
            const result = await response.json();
            if (result.status === 'success') {
                showNotification('Штрих-код сохранён', 'success');
                closeBarcodeModal();
                loadBarcodes(barcodeCurrentPage);
            } else {
                alert(result.message || result.error || 'Ошибка сохранения');
            }
        } catch (e) {
            alert('Ошибка: ' + e.message);
        }
    }

    async function deleteBarcode(id) {
        if (!confirm('Удалить этот штрих-код?')) return;
        try {
            const response = await fetch(`/api/barcodes/delete/${id}`, {
                method: 'POST',
                credentials: 'include'
            });
            const result = await response.json();
            if (result.status === 'success') {
                showNotification('Штрих-код удалён', 'success');
                loadBarcodes(barcodeCurrentPage);
            } else {
                alert(result.message || result.error || 'Ошибка удаления');
            }
        } catch (e) {
            alert('Ошибка: ' + e.message);
        }
    }

    function prevBarcodePage() { if (barcodeCurrentPage > 0) loadBarcodes(barcodeCurrentPage - 1); }
    function nextBarcodePage() { loadBarcodes(barcodeCurrentPage + 1); }
    function exportBarcodes() { window.open('/api/barcodes/export', '_blank'); showNotification('Экспорт начат', 'info'); }
    
    function showImportModal() {
        document.getElementById('barcode-import-file').value = '';
        document.getElementById('barcode-import-modal').style.display = 'flex';
    }

    async function importBarcodes() {
        const fileInput = document.getElementById('barcode-import-file');
        const file = fileInput.files[0];
        if (!file) { alert('Выберите файл'); return; }
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/api/barcodes/import-excel', {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
            const result = await response.json();
            if (result.success) {
                showNotification(`Импортировано: ${result.added}, пропущено: ${result.skipped}`, 'success');
                closeImportModal();
                loadBarcodes(0);
            } else {
                alert(result.error || 'Ошибка импорта');
            }
        } catch (e) {
            alert('Ошибка: ' + e.message);
        }
    }

    function escapeHtml(text) { if (!text) return ''; return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
    function escapeJs(text) { if (!text) return ''; return String(text).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n'); }

    // Поиск штрих-кодов в реальном времени
    document.addEventListener('DOMContentLoaded', function() {
        const barcodeSearchInput = document.getElementById('barcode-search');
        let barcodeSearchTimeout;
        
        // Поиск при вводе (с задержкой 300мс)
        barcodeSearchInput.addEventListener('input', function(e) {
            clearTimeout(barcodeSearchTimeout);
            barcodeSearchTimeout = setTimeout(() => {
                loadBarcodes(0); // Сброс на первую страницу при поиске
            }, 300);
        });
        
        // Также работает по Enter
        barcodeSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(barcodeSearchTimeout);
                loadBarcodes(0);
            }
        });
    });

    // ========================================
    // АДМИН-ПАНЕЛЬ
    // ========================================
    
    // Импорт 1С
    function open1cImportModal() {
        document.getElementById('1c-import-modal').style.display = 'block';
        document.getElementById('1c-import-result').style.display = 'none';
    }
    
    function close1cImportModal() {
        document.getElementById('1c-import-modal').style.display = 'none';
    }
    
    async function import1cProducts() {
        const resultDiv = document.getElementById('1c-import-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<p>⏳ Импорт...</p>';
        
        try {
            const response = await fetch('/api/products-1c/import', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                let html = '<p style="color: #16a34a; font-weight: bold;">✅ Импорт завершён!</p>';
                html += `<p>📦 Импортировано: <strong>${data.imported}</strong></p>`;
                html += `<p>🔄 Обновлено: <strong>${data.updated}</strong></p>`;
                if (data.errors && data.errors.length > 0) {
                    html += `<p style="color: #dc2626;">⚠️ Ошибок: ${data.errors.length}</p>`;
                }
                resultDiv.innerHTML = html;
                resultDiv.style.background = '#f0fdf4';
                resultDiv.style.border = '1px solid #16a34a';
            } else {
                resultDiv.innerHTML = `<p style="color: #dc2626;">❌ Ошибка: ${data.message}</p>`;
                resultDiv.style.background = '#fef2f2';
                resultDiv.style.border = '1px solid #dc2626';
            }
        } catch (error) {
            console.error('Ошибка импорта 1C:', error);
            resultDiv.innerHTML = '<p style="color: #dc2626;">❌ Ошибка сети</p>';
            resultDiv.style.background = '#fef2f2';
            resultDiv.style.border = '1px solid #dc2626';
        }
    }

    // Напоминания
    function openCreateReminderModal() {
        document.getElementById('create-reminder-modal').style.display = 'block';
        document.getElementById('reminder-title').value = '';
        document.getElementById('reminder-message').value = '';
        document.getElementById('reminder-type').value = 'general';
        document.getElementById('reminder-require-confirm').checked = true;
        document.getElementById('reminder-expires').value = '';
    }
    
    function closeCreateReminderModal() {
        document.getElementById('create-reminder-modal').style.display = 'none';
    }
    
    async function createReminder() {
        const title = document.getElementById('reminder-title').value.trim();
        const message = document.getElementById('reminder-message').value.trim();
        const type = document.getElementById('reminder-type').value;
        const requireConfirm = document.getElementById('reminder-require-confirm').checked;
        const expiresHours = document.getElementById('reminder-expires').value;
        
        if (!title || !message) {
            alert('Заполните заголовок и текст');
            return;
        }
        
        const data = {
            title: title,
            message: message,
            type: type,
            require_confirmation: requireConfirm
        };
        
        if (expiresHours) {
            data.expires_hours = parseInt(expiresHours);
        }
        
        try {
            const response = await fetch('/api/reminders', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                alert('✅ Напоминание создано и отправлено в VK чат!');
                closeCreateReminderModal();
            } else {
                alert('Ошибка: ' + result.message);
            }
        } catch (error) {
            console.error('Ошибка создания напоминания:', error);
            alert('Ошибка сети');
        }
    }
    
    async function viewReminderStats(reminderId) {
        try {
            const response = await fetch(`/api/reminders/${reminderId}/stats`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const stats = data.stats;
                const confirmed = data.confirmed || [];
                const notConfirmed = data.not_confirmed || [];
                
                let msg = `📊 Статистика напоминания:\n\n`;
                msg += `📌 ${stats.title}\n\n`;
                msg += `✅ Подтвердили (${confirmed.length}):\n`;
                confirmed.forEach(p => {
                    msg += `  • ${p.full_name} — ${new Date(p.confirmed_at).toLocaleString('ru-RE')}\n`;
                });
                if (notConfirmed.length > 0) {
                    msg += `\n❌ Не подтвердили (${notConfirmed.length}):\n`;
                    notConfirmed.forEach(p => {
                        msg += `  • ${p.full_name}\n`;
                    });
                }
                
                alert(msg);
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            alert('Ошибка сети');
        }
    }

    // ========================================
    // РЕВИЗИЯ ТОВАРА
    // ========================================
    
    // ========================================
    // НАПОМИНАНИЯ
    // ========================================
    
    let currentReminderId = null;
    let remindersQueue = [];
    
    // Загрузка напоминаний при старте
    async function loadAndShowReminders() {
        try {
            const response = await fetch('/api/reminders');
            const data = await response.json();
            
            if (data.status === 'success' && data.reminders.length > 0) {
                // Фильтруем неподтверждённые
                remindersQueue = data.reminders.filter(r => !r.is_confirmed && r.require_confirmation);
                
                if (remindersQueue.length > 0) {
                    showNextReminder();
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки напоминаний:', error);
        }
    }
    
    function showNextReminder() {
        if (remindersQueue.length === 0) {
            return;
        }
        
        const reminder = remindersQueue[0];
        currentReminderId = reminder.id;
        
        const content = document.getElementById('reminder-content');
        if (content) {
            content.innerHTML = `
                <h2 style="color: #dc2626; margin-bottom: 16px; font-size: 24px;">${escapeHtml(reminder.title)}</h2>
                <div style="font-size: 16px; line-height: 1.6; color: var(--text-primary); margin-bottom: 20px;">
                    ${escapeHtml(reminder.message).replace(/\n/g, '<br>')}
                </div>
                <div style="background: #fef3c7; padding: 12px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <strong>📊 Статус:</strong> ${reminder.confirmed_users || 0} из ${reminder.total_users} сотрудников подтвердили
                </div>
                <div style="margin-top: 16px; font-size: 12px; color: var(--text-secondary);">
                    <strong>Дата:</strong> ${formatDateRu(reminder.created_at)} | 
                    <strong>Тип:</strong> ${getReminderTypeLabel(reminder.reminder_type)}
                    ${reminder.expires_at ? `<br><strong>Действует до:</strong> ${formatDateRu(reminder.expires_at)}` : ''}
                </div>
            `;
        }
        
        const modal = document.getElementById('reminder-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }
    
    function getReminderTypeLabel(type) {
        const labels = {
            'general': '📢 Общее',
            'revision': '⚠️ Ревизия',
            'schedule': '📅 График',
            'task': '📋 Задача'
        };
        return labels[type] || type;
    }
    
    function closeReminderModal() {
        // Нельзя закрыть просто так — только через подтверждение
        if (remindersQueue.length > 0) {
            alert('⚠️ Вы должны подтвердить прочтение нажатием кнопки "ПРОЧИТАНО И ПОНЯТНО"');
            return;
        }
        const modal = document.getElementById('reminder-modal');
        if (modal) modal.style.display = 'none';
    }
    
    async function confirmCurrentReminder() {
        if (!currentReminderId) return;
        
        try {
            const response = await fetch(`/api/reminders/${currentReminderId}/confirm`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Убираем из очереди
                remindersQueue.shift();
                
                // Закрываем модальное окно
                const modal = document.getElementById('reminder-modal');
                if (modal) modal.style.display = 'none';
                
                // Показываем следующее
                if (remindersQueue.length > 0) {
                    setTimeout(() => showNextReminder(), 500);
                } else {
                    alert('✅ Спасибо! Вы подтвердили прочтение.');
                }
                
                currentReminderId = null;
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка подтверждения:', error);
            alert('Ошибка сети');
        }
    }
    
    // Блокировка закрытия модального окна кликом вне его
    document.addEventListener('DOMContentLoaded', function() {
        // Загружаем напоминания через 2 секунды после загрузки страницы
        setTimeout(loadAndShowReminders, 2000);
    });
    
    // ========================================
    // НАПОМИНАНИЯ
    // ========================================
    
    // ========================================
    // COM-СКАНЕРЫ ШТРИХ-КОДОВ
    // ========================================

    let comScannerInterval = null;
    let lastScannedBarcode = null;
    let scannerPollingEnabled = false;

    // Переключение состояния сканера
    async function toggleScanner() {
        try {
            const response = await fetch('/api/com-scanner/toggle', {
                method: 'POST',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'success') {
                console.log(`📡 ${data.message}`);
                updateScannerStatusUI(data.enabled);

                // Показываем уведомление
                showNotification(
                    data.enabled ? '✅ Сканер включён' : '🛑 Сканер выключен',
                    data.message,
                    data.enabled ? 'success' : 'warning'
                );
            }
        } catch (error) {
            console.error('❌ Ошибка переключения сканера:', error);
            showNotification('⚠️ Ошибка', `Не удалось переключить сканер: ${error.message}`, 'error');
        }
    }

    // Обновление UI кнопки сканера
    function updateScannerStatusUI(enabled) {
        const btn = document.getElementById('scanner-toggle-btn');
        const icon = document.getElementById('scanner-status-icon');
        const text = document.getElementById('scanner-status-text');

        if (!btn || !icon || !text) return;

        if (enabled) {
            btn.className = 'btn btn-success';
            icon.textContent = '🟢';
            text.textContent = 'Сканер включён';
            startComScannerPolling();
        } else {
            btn.className = 'btn btn-secondary';
            icon.textContent = '⚫';
            text.textContent = 'Сканер выключен';
            stopComScannerPolling();
        }
    }

    // Проверка статуса сканера при загрузке
    async function checkScannerStatus() {
        try {
            const response = await fetch('/api/com-scanner/status', {
                credentials: 'include'
            });

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            if (data.status === 'success') {
                updateScannerStatusUI(data.enabled);
            }
        } catch (error) {
            console.warn('⚠️ Не удалось проверить статус сканера:', error.message);
        }
    }

    // 🆕 АВТО-ПОИСК ТОВАРА В 1С ПО ШТРИХ-КОДУ
    async function autoSearchProductByBarcode(barcode) {
        console.log('🔍 Авто-поиск товара по штрих-коду:', barcode);
        
        try {
            const response = await fetch(`/api/products-1c/barcode/${encodeURIComponent(barcode)}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                console.warn('⚠️ Товар не найден в 1C по штрих-коду:', barcode);
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.product) {
                console.log('✅ Товар найден в 1C:', data.product.name);
                
                // Авто-заполняем все поля
                const productNameField = document.getElementById('rev-product-name');
                const barcodeField = document.getElementById('rev-barcode');
                const priceField = document.getElementById('rev-retail-price');
                
                if (productNameField) {
                    productNameField.value = data.product.name || '';
                    productNameField.style.background = '#d1fae5';
                    setTimeout(() => { productNameField.style.background = ''; }, 1500);
                }
                
                if (barcodeField) {
                    barcodeField.value = data.product.barcode_main || barcode;
                }
                
                if (priceField && data.product.retail_price) {
                    priceField.value = data.product.retail_price;
                    priceField.style.background = '#d1fae5';
                    setTimeout(() => { priceField.style.background = ''; }, 1500);
                }
                
                // Показываем уведомление
                const searchResults = document.getElementById('rev-1c-results');
                if (searchResults) {
                    searchResults.innerHTML = `
                        <div style="padding: 10px; margin: 8px 0; background: #d1fae5; border: 2px solid #16a34a; border-radius: 8px;">
                            <div style="font-weight: bold; color: #166534;">✅ Товар автоматически найден!</div>
                            <div style="font-size: 13px; color: #15803d; margin-top: 4px;">
                                <strong>${escapeHtml(data.product.name)}</strong><br>
                                📦 ${data.product.barcode_main || 'Н/Д'} | 💰 ${data.product.retail_price || 'Н/Д'} ₽
                                ${data.product.group_name ? ` | 📁 ${escapeHtml(data.product.group_name)}` : ''}
                            </div>
                        </div>
                    `;
                }
                
                // Фокус на количество
                const quantityField = document.getElementById('rev-quantity');
                if (quantityField) {
                    setTimeout(() => quantityField.focus(), 300);
                }
                
            } else {
                console.log('ℹ️ Товар не найден в 1C по штрих-коду:', barcode);
                const searchResults = document.getElementById('rev-1c-results');
                if (searchResults) {
                    searchResults.innerHTML = `
                        <div style="padding: 10px; margin: 8px 0; background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px;">
                            <div style="font-weight: bold; color: #92400e;">⚠️ Товар не найден в базе 1C</div>
                            <div style="font-size: 13px; color: #78350f; margin-top: 4px;">
                                Заполните поля вручную
                            </div>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('❌ Ошибка авто-поиска товара:', error);
            const searchResults = document.getElementById('rev-1c-results');
            if (searchResults) {
                searchResults.innerHTML = `
                    <div style="padding: 10px; margin: 8px 0; background: #fee2e2; border: 2px solid #dc2626; border-radius: 8px;">
                        <div style="font-weight: bold; color: #991b1b;">❌ Ошибка поиска</div>
                        <div style="font-size: 13px; color: #7f1d1d; margin-top: 4px;">
                            ${escapeHtml(error.message)}
                        </div>
                    </div>
                `;
            }
        }
    }

    // Запуск опроса COM-сканеров
    function startComScannerPolling() {
        if (scannerPollingEnabled) {
            console.log('📡 Опрос сканеров уже запущен');
            return;
        }

        console.log('📡 Запуск опроса COM-сканеров (каждые 300мс)...');
        scannerPollingEnabled = true;

        // Проверяем каждые 300мс
        comScannerInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/com-scanner/last', {
                    credentials: 'include'
                });

                if (!response.ok) {
                    console.warn('⚠️ COM-сканер: ошибка ответа', response.status);
                    return;
                }

                const data = await response.json();

                if (data.status === 'success' && data.data.barcode) {
                    const newBarcode = data.data.barcode;

                    // Проверяем что штрих-код новый (не тот же самый)
                    if (lastScannedBarcode !== newBarcode) {
                        console.log('📠 Новый штрих-код:', newBarcode);
                        lastScannedBarcode = newBarcode;

                        // Ищем поле штрих-кода во всех возможных местах
                        let barcodeField = document.getElementById('rev-barcode');
                        
                        // Если не нашли в модальном окне — ищем на странице ревизии
                        if (!barcodeField) {
                            barcodeField = document.querySelector('#revision-add-modal input[type="text"][id*="barcode"]');
                        }
                        
                        if (barcodeField) {
                            console.log('✅ Поле штрих-кода найдено:', barcodeField.id);
                            const oldValue = barcodeField.value;
                            barcodeField.value = newBarcode;

                            // Визуальное подтверждение
                            barcodeField.style.background = '#d1fae5';
                            barcodeField.style.fontWeight = 'bold';
                            setTimeout(() => {
                                barcodeField.style.background = '';
                                barcodeField.style.fontWeight = '';
                            }, 1500);

                            // Триггерим событие input для реактивности
                            barcodeField.dispatchEvent(new Event('input', { bubbles: true }));
                            barcodeField.dispatchEvent(new Event('change', { bubbles: true }));

                            // Звуковой сигнал
                            playBeep();

                            console.log(`✅ Штрих-код заполнен: ${newBarcode} (было: ${oldValue})`);
                        } else {
                            console.warn('⚠️ Поле штрих-кода не найдено! Модальное окно открыто?');
                            console.log('🔍 Ищу все input[type="text"] на странице...');
                            const allInputs = document.querySelectorAll('input[type="text"]');
                            allInputs.forEach((input, i) => {
                                console.log(`  Input ${i}: id="${input.id}", placeholder="${input.placeholder}"`);
                            });
                        }

                        // 🆕 АВТО-ПОИСК ТОВАРА В 1С ПО ШТРИХ-КОДУ!
                        console.log('🔍 Авто-поиск товара в 1C по штрих-коду:', newBarcode);
                        autoSearchProductByBarcode(newBarcode);

                        // Также заполняем поле поиска 1C
                        const searchInput = document.getElementById('rev-1c-search');
                        if (searchInput) {
                            searchInput.value = newBarcode;
                        }

                        // Очищаем на сервере чтобы не дублировалось
                        try {
                            await fetch('/api/com-scanner/clear', {
                                method: 'POST',
                                credentials: 'include'
                            });
                            console.log('🗑️ Очередь сканера очищена');
                        } catch (clearError) {
                            console.warn('⚠️ Не удалось очистить очередь:', clearError);
                        }
                    }
                }
            } catch (error) {
                // Тихая ошибка — COM-сканеры могут быть не подключены
                // Но логируем для отладки
                if (error.message !== 'Failed to fetch') {
                    console.warn('⚠️ COM-сканер ошибка:', error.message);
                }
            }
        }, 300);
    }

    // Остановка опроса COM-сканеров
    function stopComScannerPolling() {
        if (!scannerPollingEnabled) {
            console.log('📡 Опрос сканеров уже остановлен');
            return;
        }

        console.log('🛑 Остановка опроса COM-сканеров...');
        scannerPollingEnabled = false;

        if (comScannerInterval) {
            clearInterval(comScannerInterval);
            comScannerInterval = null;
        }
    }
    
    // Простой звуковой сигнал
    function playBeep() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            // Звук не поддерживается
        }
    }
    
    // Запускаем опрос при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        checkScannerStatus();  // Проверяем статус сканера
    });
    
    // ========================================
    // РЕВИЗИЯ ТОВАРА (продолжение)
    // ========================================
    
    function formatDateRu(dateStr) {
        if (!dateStr) return '—';
        try {
            const date = new Date(dateStr);
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            return `${day}.${month}.${year}`;
        } catch (e) {
            return dateStr;
        }
    }
    
    async function loadRevisions(filter = 'all') {
        const filterSelect = document.getElementById('revision-filter');
        if (filterSelect && filter === 'all') {
            filter = filterSelect.value;
        }

        // Получаем параметры поиска и сортировки
        const search = document.getElementById('revision-search')?.value || '';
        const sortBy = document.getElementById('revision-sort')?.value || 'expiry_date';

        try {
            const url = `/api/revision/revisions?filter=${filter}&search=${encodeURIComponent(search)}&sort=${sortBy}`;
            const response = await fetch(url, {
                credentials: 'include'
            });
            const data = await response.json();

            console.log('📦 Ревизия API ответ:', data);

            if (data.status === 'success') {
                console.log('📦 Товаров найдено:', data.revisions ? data.revisions.length : 0);
                if (data.revisions && data.revisions.length > 0) {
                    console.log('📦 Первый товар:', data.revisions[0]);
                }
                renderRevisions(data.revisions || []);
                loadRevisionStats();
                loadSmartControlBanner();  // Загружаем баннер умного контроля
            } else {
                console.error('❌ Ошибка API:', data.message);
                document.getElementById('revisions-body').innerHTML = '<tr><td colspan="10" style="text-align: center; color: red;">Ошибка загрузки</td></tr>';
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки ревизии:', error);
            document.getElementById('revisions-body').innerHTML = '<tr><td colspan="10" style="text-align: center; color: red;">Ошибка сети</td></tr>';
        }
    }
    
    function renderRevisions(revisions) {
        const tbody = document.getElementById('revisions-body');
        if (!tbody) return;

        if (!revisions || revisions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: var(--text-secondary); padding: 40px;">Нет товаров</td></tr>';
            return;
        }

        tbody.innerHTML = revisions.map(rev => {
            const statusColors = {
                'active': 'background: #d1fae5; color: #065f46;',
                'admin_decision': 'background: #fee2e2; color: #991b1b;',
                'reserved_admin': 'background: #fef3c7; color: #92400e;',
                'sold': 'background: #e5e7eb; color: #374151;',
                'utilized': 'background: #e5e7eb; color: #374151;'
            };

            const statusLabels = {
                'active': 'В продаже',
                'admin_decision': 'Ждёт решения',
                'reserved_admin': 'Забронировано',
                'sold': 'Продано',
                'utilized': 'Утилизировано'
            };

            const colorStatus = rev.color_status || 'green';
            const rowColor = colorStatus === 'red' ? 'background: #fef2f2;' :
                            colorStatus === 'orange' ? 'background: #fff7ed;' :
                            colorStatus === 'yellow' ? 'background: #fefce8;' : '';
            
            const barcodeDisplay = rev.barcode ? 
                `<code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 13px;">${escapeHtml(rev.barcode)}</code>` : 
                '<span style="color: var(--text-secondary);">—</span>';
            
            const quantityDisplay = rev.quantity && rev.quantity > 1 ? 
                `<strong style="color: #dc2626;">${rev.quantity} шт</strong>` : 
                '<span style="color: var(--text-secondary);">1</span>';
            
            return `
                <tr style="${rowColor}" data-revision-id="${rev.id}">
                    <td style="text-align: center;">
                        <input type="checkbox" class="revision-checkbox" data-revision-id="${rev.id}" data-product-name="${escapeHtml(rev.product_name)}" data-quantity="${rev.quantity || 1}" data-barcode="${rev.barcode || ''}" data-price="${rev.final_price || 0}" data-retail-price="${rev.retail_price || 0}" data-discount="${rev.discount_percent || 0}" onchange="updatePromotionPanel()">
                    </td>
                    <td><strong>${escapeHtml(rev.product_name)}</strong><br><small style="color: var(--text-secondary);">${escapeHtml(rev.full_name)}</small></td>
                    <td>${quantityDisplay}</td>
                    <td>${barcodeDisplay}</td>
                    <td>${(rev.retail_price || 0).toFixed(2)} ₽</td>
                    <td>${formatDateRu(rev.expiry_date)}</td>
                    <td>${rev.days_remaining_formatted || '—'}</td>
                    <td><span style="background: ${rev.discount_percent >= 40 ? '#f97316' : rev.discount_percent >= 25 ? '#eab308' : '#22c55e'}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; white-space: nowrap;">${rev.discount_percent || 0}%</span></td>
                    <td><strong>${(rev.final_price || 0).toFixed(2)} ₽</strong></td>
                    <td><span style="${statusColors[rev.status] || ''}; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; white-space: nowrap;">${statusLabels[rev.status] || rev.status}</span></td>
                    <td>
                        ${rev.status === 'admin_decision' ? `
                            <button type="button" class="btn btn-sm btn-success" onclick="adminRevisionDecision(${rev.id}, 'sell')" style="padding: 4px 8px; margin: 2px 4px 2px 0;">✅ Продать</button>
                            <button type="button" class="btn btn-sm btn-warning" onclick="adminRevisionDecision(${rev.id}, 'reserve')" style="padding: 4px 8px; margin: 2px 0;">📦 Забрать</button>
                        ` : ''}
                        ${rev.status === 'active' && rev.days_remaining >= 0 && rev.quantity > 0 ? `
                            <button type="button" class="btn btn-sm btn-success" onclick="openOperationModal(${rev.id})" style="padding: 4px 8px; margin: 2px 4px 2px 0;">📦 Операция</button>
                        ` : ''}
                        ${currentUser.role === 'admin' ? `
                            <button type="button" class="btn btn-sm btn-info" onclick="openTransactionLog(${rev.id})" style="padding: 4px 8px; margin: 2px 4px 2px 0;">📋</button>
                            <button type="button" class="btn btn-sm btn-primary" onclick="openEditRevisionModal(${rev.id})" style="padding: 4px 8px; margin: 2px 4px 2px 0;">✏️</button>
                            <button type="button" class="btn btn-sm btn-danger" onclick="deleteRevision(${rev.id})" style="padding: 4px 8px; margin: 2px 0;">🗑️</button>
                        ` : ''}
                        ${rev.quantity === 0 ? '<span style="color: #6b7280; font-size: 11px;">✅ Продано</span>' : ''}
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    async function loadRevisionStats() {
        try {
            const response = await fetch('/api/revision/stats', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                const stats = data.stats;
                const container = document.getElementById('revision-stats');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: 16px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #0284c7;">
                            <div style="font-size: 24px; font-weight: bold;">${stats.total || 0}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Всего товаров</div>
                        </div>
                        <div style="padding: 16px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444;">
                            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${stats.expired || 0}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Просрочено</div>
                        </div>
                        <div style="padding: 16px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <div style="font-size: 24px; font-weight: bold; color: #d97706;">${stats.need_decision || 0}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Требуют решения</div>
                        </div>
                        <div style="padding: 16px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e;">
                            <div style="font-size: 24px; font-weight: bold;">${(stats.total_final_value || 0).toFixed(0)} ₽</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Общая стоимость</div>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
    
    function openAddRevisionModal() {
        const modal = document.getElementById('revision-add-modal');
        if (modal) {
            modal.style.display = 'block';
            document.getElementById('rev-product-name').value = '';
            document.getElementById('rev-barcode').value = '';
            document.getElementById('rev-retail-price').value = '';
            document.getElementById('rev-expiry-date').value = '';
        }
    }
    
    function closeAddRevisionModal() {
        const modal = document.getElementById('revision-add-modal');
        if (modal) modal.style.display = 'none';
    }
    
    async function addRevision() {
        const productName = document.getElementById('rev-product-name').value.trim();
        const quantity = parseInt(document.getElementById('rev-quantity').value) || 1;
        const barcode = document.getElementById('rev-barcode').value.trim();
        const retailPrice = parseFloat(document.getElementById('rev-retail-price').value);
        const expiryDate = document.getElementById('rev-expiry-date').value;
        
        if (!productName) {
            alert('Введите название товара');
            return;
        }
        if (!retailPrice || retailPrice <= 0) {
            alert('Введите корректную цену');
            return;
        }
        if (!expiryDate) {
            alert('Выберите срок годности');
            return;
        }
        
        try {
            const response = await fetch('/api/revision/revisions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    product_name: productName,
                    quantity: quantity,
                    barcode: barcode,
                    retail_price: retailPrice,
                    expiry_date: expiryDate
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                alert(`✅ Товар добавлен!\nКол-во: ${quantity} шт\nСкидка: ${data.discount_percent}%\nИтоговая цена: ${data.final_price.toFixed(2)} ₽`);
                closeAddRevisionModal();
                loadRevisions();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка добавления:', error);
            alert('Ошибка сети');
        }
    }
    
    // ========================================
    // ОПЕРАЦИИ С ТОВАРОМ (19 типов)
    // ========================================

    const ACTION_TYPES = {
        'sold': { label: '💰 Продажа', requiresPrice: true, requiresReason: false, reducesQuantity: true },
        'sold_discount': { label: '🏷️ Продажа со скидкой', requiresPrice: true, requiresReason: false, reducesQuantity: true },
        'sold_promo': { label: '🎁 Акционная продажа', requiresPrice: true, requiresReason: false, reducesQuantity: true },
        'written_off_expired': { label: '🗑️ Списание (просрочка)', requiresPrice: false, requiresReason: true, reducesQuantity: true },
        'written_off_damaged': { label: '🗑️ Списание (повреждение)', requiresPrice: false, requiresReason: true, reducesQuantity: true },
        'written_off_lost': { label: '🗑️ Списание (утеря)', requiresPrice: false, requiresReason: true, reducesQuantity: true },
        'taken_personal': { label: '👤 Забрала себе', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'taken_gift': { label: '🎁 Забрала в подарок', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'taken_test': { label: '🧪 Взяла на пробу', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'returned_supplier': { label: '🔄 Возврат поставщику', requiresPrice: false, requiresReason: true, reducesQuantity: true },
        'exchanged_supplier': { label: '🔄 Обмен у поставщика', requiresPrice: false, requiresReason: true, reducesQuantity: true },
        'exchanged_customer': { label: '🔄 Обмен клиенту', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'returned_customer': { label: '↩️ Возврат от клиента', requiresPrice: true, requiresReason: false, reducesQuantity: false },
        'transferred_store': { label: '📦 Перемещение на склад', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'transferred_branch': { label: '📦 Перемещение в филиал', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'utilized': { label: '♻️ Утилизация', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'donated': { label: '❤️ Пожертвование', requiresPrice: false, requiresReason: false, reducesQuantity: true },
        'price_increased': { label: '📈 Цена повышена', requiresPrice: true, requiresReason: false, reducesQuantity: false },
        'price_decreased': { label: '📉 Цена снижена', requiresPrice: true, requiresReason: false, reducesQuantity: false }
    };

    function openOperationModal(revisionId) {
        console.log('📦 openOperationModal вызвана с revisionId:', revisionId);
        
        // Пробуем несколько способов найти строку таблицы
        let row = null;
        
        // Способ 1: Ищем по data-атрибуту (более надежно)
        row = document.querySelector(`tr[data-revision-id="${revisionId}"]`);
        
        // Способ 2: Ищем по кнопке с onclick (старый способ)
        if (!row) {
            // Экранируем специальные символы для селектора
            const selector = `tr button[onclick*="openOperationModal(${revisionId})"]`;
            const button = document.querySelector(selector);
            if (button) {
                row = button.closest('tr');
            }
        }
        
        // Способ 3: Ищем по тексту в таблице (последний вариант)
        if (!row) {
            const allRows = document.querySelectorAll('#revisions-body tr[data-revision-id]');
            for (const r of allRows) {
                if (r.getAttribute('data-revision-id') == revisionId) {
                    row = r;
                    break;
                }
            }
        }
        
        if (!row) {
            console.error('❌ Не удалось найти строку товара с ID:', revisionId);
            alert('Ошибка: не удалось найти товар. Попробуйте обновить страницу.');
            return;
        }
        
        console.log('✅ Найдена строка товара:', row);

        // Получаем данные из data-атрибутов чекбокса (более надежно)
        const checkbox = row.querySelector('.revision-checkbox');
        let productName = '';
        let quantity = 1;
        let price = 0;
        
        if (checkbox) {
            productName = checkbox.getAttribute('data-product-name') || '';
            quantity = parseInt(checkbox.getAttribute('data-quantity') || '1');
            price = parseFloat(checkbox.getAttribute('data-price') || '0');
        } else {
            // Старый способ парсинга HTML (для обратной совместимости)
            const cells = row.querySelectorAll('td');
            if (cells.length > 0) {
                const nameHtml = cells[0].innerHTML;
                const nameMatch = nameHtml.match(/<strong>(.*?)<\/strong>/);
                productName = nameMatch ? nameMatch[1] : '';
                
                if (cells.length > 1) {
                    const quantityHtml = cells[1].innerHTML;
                    const quantityMatch = quantityHtml.match(/<strong.*?>(\d+) шт<\/strong>/);
                    quantity = quantityMatch ? parseInt(quantityMatch[1]) : 1;
                }
                
                if (cells.length > 7) {
                    const priceText = cells[7].innerText.replace('₽', '').trim();
                    price = parseFloat(priceText) || 0;
                }
            }
        }

        // Заполняем модальное окно
        document.getElementById('op-revision-id').value = revisionId;
        document.getElementById('op-product-name').textContent = productName || 'Неизвестный товар';
        document.getElementById('op-available-qty').textContent = quantity;
        document.getElementById('op-price').value = price;
        document.getElementById('op-quantity').value = 1;
        document.getElementById('op-quantity').max = quantity;
        document.getElementById('op-action').value = '';
        document.getElementById('op-reason').value = '';
        document.getElementById('op-notes').value = '';
        document.getElementById('op-action-description').textContent = '';

        // Скрываем дополнительные поля
        document.getElementById('op-price-group').style.display = 'none';
        document.getElementById('op-reason-group').style.display = 'none';

        // Показываем модальное окно
        const modal = document.getElementById('operation-modal');
        if (modal) {
            modal.style.display = 'block';
            console.log('✅ Модальное окно показано');
        } else {
            console.error('❌ Не найдено модальное окно operation-modal');
        }
    }

    function closeOperationModal() {
        document.getElementById('operation-modal').style.display = 'none';
    }

    function onActionChange() {
        const action = document.getElementById('op-action').value;
        const actionInfo = ACTION_TYPES[action];

        if (!actionInfo) {
            document.getElementById('op-action-description').textContent = '';
            document.getElementById('op-price-group').style.display = 'none';
            document.getElementById('op-reason-group').style.display = 'none';
            return;
        }

        // Показываем описание
        document.getElementById('op-action-description').textContent = actionInfo.label;

        // Показываем/скрываем поля
        document.getElementById('op-price-group').style.display = actionInfo.requiresPrice ? 'block' : 'none';
        document.getElementById('op-reason-group').style.display = actionInfo.requiresReason ? 'block' : 'none';
    }

    async function executeOperation() {
        const revisionId = document.getElementById('op-revision-id').value;
        const action = document.getElementById('op-action').value;
        const quantity = parseInt(document.getElementById('op-quantity').value);
        const price = parseFloat(document.getElementById('op-price').value);
        const reason = document.getElementById('op-reason').value.trim();
        const notes = document.getElementById('op-notes').value.trim();

        const actionInfo = ACTION_TYPES[action];

        if (!action) {
            alert('Выберите тип операции');
            return;
        }

        if (actionInfo.requiresQuantity && (!quantity || quantity <= 0)) {
            alert('Введите корректное количество');
            return;
        }

        if (actionInfo.requiresPrice && (!price || price <= 0)) {
            alert('Введите корректную цену');
            return;
        }

        if (actionInfo.requiresReason && !reason) {
            alert('Укажите причину операции');
            return;
        }

        try {
            const response = await fetch(`/api/revision/revisions/${revisionId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    status: action,
                    quantity: actionInfo.reducesQuantity ? quantity : 0,
                    sale_price: actionInfo.requiresPrice ? price : null,
                    reason: reason,
                    notes: notes
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                const message = actionInfo.reducesQuantity
                    ? `✅ ${actionInfo.label}: ${quantity} шт\nОсталось: ${data.quantity_after} шт`
                    : `✅ ${actionInfo.label} выполнена`;
                alert(message);
                closeOperationModal();
                loadRevisions();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка операции:', error);
            alert('Ошибка сети');
        }
    }

    // ========================================
    // ЖУРНАЛ ОПЕРАЦИЙ
    // ========================================

    async function openTransactionLog(revisionId) {
        document.getElementById('transaction-log-title').textContent = '📋 Журнал операций';
        document.getElementById('transaction-log-body').innerHTML = '<p style="text-align: center;">Загрузка...</p>';
        document.getElementById('transaction-log-modal').style.display = 'block';

        try {
            const response = await fetch(`/api/revision/revisions/${revisionId}/transactions`, {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.status === 'success' && data.transactions.length > 0) {
                // Метки действий
                const actionLabels = {
                    'sold': '💰 Продажа',
                    'sold_discount': '🏷️ Продажа со скидкой',
                    'sold_promo': '🎁 Акционная продажа',
                    'written_off_expired': '🗑️ Списание (просрочка)',
                    'written_off_damaged': '🗑️ Списание (повреждение)',
                    'written_off_lost': '🗑️ Списание (утеря)',
                    'taken_personal': '👤 Забрала себе',
                    'taken_gift': '🎁 Забрала в подарок',
                    'taken_test': '🧪 Взяла на пробу',
                    'returned_supplier': '🔄 Возврат поставщику',
                    'exchanged_supplier': '🔄 Обмен у поставщика',
                    'exchanged_customer': '🔄 Обмен клиенту',
                    'returned_customer': '↩️ Возврат от клиента',
                    'transferred_store': '📦 Перемещение на склад',
                    'transferred_branch': '📦 Перемещение в филиал',
                    'utilized': '♻️ Утилизация',
                    'donated': '❤️ Пожертвование',
                    'price_increased': '📈 Цена повышена',
                    'price_decreased': '📉 Цена снижена'
                };

                const actionColors = {
                    'sold': { bg: '#f0fdf4', border: '#22c55e' },
                    'sold_discount': { bg: '#dcfce7', border: '#16a34a' },
                    'sold_promo': { bg: '#d1fae5', border: '#059669' },
                    'written_off_expired': { bg: '#fef2f2', border: '#ef4444' },
                    'written_off_damaged': { bg: '#fee2e2', border: '#dc2626' },
                    'written_off_lost': { bg: '#fecaca', border: '#b91c1c' },
                    'taken_personal': { bg: '#fef3c7', border: '#f59e0b' },
                    'taken_gift': { bg: '#fde68a', border: '#d97706' },
                    'taken_test': { bg: '#fcd34d', border: '#b45309' },
                    'returned_supplier': { bg: '#dbeafe', border: '#3b82f6' },
                    'exchanged_supplier': { bg: '#bfdbfe', border: '#2563eb' },
                    'exchanged_customer': { bg: '#93c5fd', border: '#1d4ed8' },
                    'returned_customer': { bg: '#e0e7ff', border: '#6366f1' },
                    'transferred_store': { bg: '#ede9fe', border: '#8b5cf6' },
                    'transferred_branch': { bg: '#ddd6fe', border: '#7c3aed' },
                    'utilized': { bg: '#f3f4f6', border: '#6b7280' },
                    'donated': { bg: '#fce7f3', border: '#ec4899' },
                    'price_increased': { bg: '#d1fae5', border: '#10b981' },
                    'price_decreased': { bg: '#fef3c7', border: '#f59e0b' }
                };

                const html = data.transactions.map(t => {
                    const label = actionLabels[t.action] || t.action;
                    const colors = actionColors[t.action] || { bg: '#f0f9ff', border: '#0284c7' };
                    
                    return `
                    <div style="padding: 12px; margin: 8px 0; background: ${colors.bg}; border-left: 4px solid ${colors.border}; border-radius: 4px;">
                        <div style="font-weight: bold; margin-bottom: 4px;">${label}</div>
                        <div style="font-size: 13px; color: var(--text-secondary);">
                            <div>👤 <strong>${t.operator_name || t.full_name}</strong></div>
                            ${t.quantity > 0 ? `<div>📦 Количество: ${t.quantity} шт (было: ${t.quantity_before} → стало: ${t.quantity_after})</div>` : ''}
                            ${t.price ? `<div>💰 Цена: ${t.price.toFixed(2)} ₽${t.quantity > 0 ? ' (сумма: ' + (t.price * t.quantity).toFixed(2) + ' ₽)' : ''}</div>` : ''}
                            ${t.reason ? `<div>📝 Причина: ${t.reason}</div>` : ''}
                            ${t.notes ? `<div>💬 Примечание: ${t.notes}</div>` : ''}
                            <div style="margin-top: 4px; font-size: 11px; color: #9ca3af;">🕐 ${new Date(t.created_at).toLocaleString('ru-RU')}</div>
                        </div>
                    </div>
                `}).join('');

                document.getElementById('transaction-log-body').innerHTML = html;
            } else {
                document.getElementById('transaction-log-body').innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Нет операций</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки журнала:', error);
            document.getElementById('transaction-log-body').innerHTML = '<p style="text-align: center; color: red;">Ошибка загрузки</p>';
        }
    }

    function closeTransactionLog() {
        document.getElementById('transaction-log-modal').style.display = 'none';
    }

    // ========================================
    // ОБЩИЙ ЖУРНАЛ ВСЕХ ОПЕРАЦИЙ
    // ========================================

    async function openAllTransactionsLog() {
        document.getElementById('all-transactions-log-title').textContent = '📊 Общий журнал всех операций';
        document.getElementById('all-transactions-log-body').innerHTML = '<p style="text-align: center;">Загрузка...</p>';
        document.getElementById('all-transactions-log-modal').style.display = 'block';

        try {
            const response = await fetch('/api/revision/transactions/my', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.status === 'success' && data.transactions.length > 0) {
                // Метки действий
                const actionLabels = {
                    'sold': '💰 Продажа',
                    'sold_discount': '🏷️ Продажа со скидкой',
                    'sold_promo': '🎁 Акционная продажа',
                    'written_off_expired': '🗑️ Списание (просрочка)',
                    'written_off_damaged': '🗑️ Списание (повреждение)',
                    'written_off_lost': '🗑️ Списание (утеря)',
                    'taken_personal': '👤 Забрала себе',
                    'taken_gift': '🎁 Забрала в подарок',
                    'taken_test': '🧪 Взяла на пробу',
                    'returned_supplier': '🔄 Возврат поставщику',
                    'exchanged_supplier': '🔄 Обмен у поставщика',
                    'exchanged_customer': '🔄 Обмен клиенту',
                    'returned_customer': '↩️ Возврат от клиента',
                    'transferred_store': '📦 Перемещение на склад',
                    'transferred_branch': '📦 Перемещение в филиал',
                    'utilized': '♻️ Утилизация',
                    'donated': '❤️ Пожертвование',
                    'price_increased': '📈 Цена повышена',
                    'price_decreased': '📉 Цена снижена'
                };

                const actionColors = {
                    'sold': { bg: '#f0fdf4', border: '#22c55e' },
                    'sold_discount': { bg: '#dcfce7', border: '#16a34a' },
                    'sold_promo': { bg: '#d1fae5', border: '#059669' },
                    'written_off_expired': { bg: '#fef2f2', border: '#ef4444' },
                    'written_off_damaged': { bg: '#fee2e2', border: '#dc2626' },
                    'written_off_lost': { bg: '#fecaca', border: '#b91c1c' },
                    'taken_personal': { bg: '#fef3c7', border: '#f59e0b' },
                    'taken_gift': { bg: '#fde68a', border: '#d97706' },
                    'taken_test': { bg: '#fcd34d', border: '#b45309' },
                    'returned_supplier': { bg: '#dbeafe', border: '#3b82f6' },
                    'exchanged_supplier': { bg: '#bfdbfe', border: '#2563eb' },
                    'exchanged_customer': { bg: '#93c5fd', border: '#1d4ed8' },
                    'returned_customer': { bg: '#e0e7ff', border: '#6366f1' },
                    'transferred_store': { bg: '#ede9fe', border: '#8b5cf6' },
                    'transferred_branch': { bg: '#ddd6fe', border: '#7c3aed' },
                    'utilized': { bg: '#f3f4f6', border: '#6b7280' },
                    'donated': { bg: '#fce7f3', border: '#ec4899' },
                    'price_increased': { bg: '#d1fae5', border: '#10b981' },
                    'price_decreased': { bg: '#fef3c7', border: '#f59e0b' }
                };

                const html = `
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Сотрудник</th>
                                <th>Товар</th>
                                <th>Операция</th>
                                <th>Кол-во</th>
                                <th>Цена</th>
                                <th>Было → Стало</th>
                                <th>Причина</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.transactions.map(t => {
                                const label = actionLabels[t.action] || t.action;
                                const colors = actionColors[t.action] || { bg: '#f0f9ff', border: '#0284c7' };
                                return `
                                    <tr style="background: ${colors.bg}; border-left: 4px solid ${colors.border};">
                                        <td>${new Date(t.created_at).toLocaleString('ru-RU', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'})}</td>
                                        <td><strong>${t.operator_name || t.full_name || '—'}</strong></td>
                                        <td>${t.product_name || '—'}</td>
                                        <td><span style="font-size:12px;">${label}</span></td>
                                        <td>${t.quantity > 0 ? t.quantity + ' шт' : '—'}</td>
                                        <td>${t.price ? t.price.toFixed(2) + ' ₽' : '—'}</td>
                                        <td>${t.quantity_before || '—'} → ${t.quantity_after || '—'}</td>
                                        <td style="font-size:12px;">${t.reason || '—'}</td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                    <p style="margin-top: 12px; text-align: center; color: var(--text-secondary); font-size: 13px;">
                        Всего операций: <strong>${data.transactions.length}</strong>
                    </p>
                `;

                document.getElementById('all-transactions-log-body').innerHTML = html;
            } else {
                document.getElementById('all-transactions-log-body').innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">Нет операций</p>';
            }
        } catch (error) {
            console.error('Ошибка загрузки журнала:', error);
            document.getElementById('all-transactions-log-body').innerHTML = '<p style="text-align: center; color: red; padding: 40px;">❌ Ошибка загрузки</p>';
        }
    }

    function closeAllTransactionsLog() {
        document.getElementById('all-transactions-log-modal').style.display = 'none';
    }

    // ========================================
    // СТАТИСТИКА ПО СОТРУДНИКАМ (АДМИН)
    // ========================================

    async function loadEmployeeStats() {
        if (currentUser.role !== 'admin') return;

        try {
            const response = await fetch('/api/revision/stats/employees', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.status === 'success') {
                const container = document.getElementById('employee-stats-container');
                if (!container) return;

                if (data.employees.length === 0) {
                    container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Нет данных</p>';
                    return;
                }

                const html = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">
                        <div style="padding: 16px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #0284c7;">
                            <div style="font-size: 24px; font-weight: bold;">${data.total.total_operations || 0}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Всего операций</div>
                        </div>
                        <div style="padding: 16px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e;">
                            <div style="font-size: 24px; font-weight: bold;">${data.total.total_sold || 0} шт</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Продано</div>
                        </div>
                        <div style="padding: 16px; background: #fefce8; border-radius: 8px; border-left: 4px solid #eab308;">
                            <div style="font-size: 24px; font-weight: bold;">${(data.total.total_revenue || 0).toFixed(0)} ₽</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Выручка</div>
                        </div>
                    </div>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Сотрудник</th>
                                <th>Операций</th>
                                <th>Продано (шт)</th>
                                <th>Выручка</th>
                                <th>Списано (шт)</th>
                                <th>Последняя операция</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.employees.map(e => `
                                <tr>
                                    <td><strong>${e.full_name}</strong></td>
                                    <td>${e.total_operations}</td>
                                    <td>${e.total_sold}</td>
                                    <td>${(e.total_revenue || 0).toFixed(2)} ₽</td>
                                    <td>${e.total_written_off || 0}</td>
                                    <td>${e.last_operation ? new Date(e.last_operation).toLocaleString('ru-RU') : '—'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;

                container.innerHTML = html;
            }
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }
    
    async function adminRevisionDecision(revisionId, decision) {
        const confirmMsg = decision === 'reserve' ? 'Забрать товар себе?' : 'Разрешить продажу со скидкой 50%?';
        if (!confirm(confirmMsg)) return;
        
        try {
            const response = await fetch(`/api/revision/revisions/${revisionId}/decision`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({decision: decision})
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                alert(data.message);
                loadRevisions();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Ошибка сети');
        }
    }
    
    // ========================================
    // РЕДАКТИРОВАНИЕ И УДАЛЕНИЕ (АДМИН)
    // ========================================
    
    function openEditRevisionModal(revisionId) {
        // Находим товар в текущем списке
        const row = document.querySelector(`tr button[onclick*="openEditRevisionModal(${revisionId})"]`)?.closest('tr');
        if (!row) return;
        
        const cells = row.querySelectorAll('td');
        if (cells.length < 10) return;
        
        // Извлекаем данные из ячейки "Товар" (содержит название и имя)
        const nameHtml = cells[0].innerHTML;
        const nameMatch = nameHtml.match(/<strong>(.*?)<\/strong>/);
        const productName = nameMatch ? nameMatch[1] : '';
        
        // Извлекаем количество
        const quantityHtml = cells[1].innerHTML;
        const quantityMatch = quantityHtml.match(/<strong.*?>(\d+) шт<\/strong>/);
        const quantity = quantityMatch ? parseInt(quantityMatch[1]) : 1;
        
        // Извлекаем штрих-код
        const barcodeCell = cells[2].innerHTML;
        const barcodeMatch = barcodeCell.match(/<code.*?>(.*?)<\/code>/);
        const barcode = barcodeMatch ? barcodeMatch[1].trim() : '';
        
        // Извлекаем цену
        const priceText = cells[3].innerText.replace('₽', '').trim();
        const price = parseFloat(priceText);
        
        // Извлекаем дату
        const dateText = cells[4].innerText.trim();
        const dateParts = dateText.split('.');
        const expiryDate = dateParts.length === 3 ? `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` : '';
        
        // Заполняем форму
        document.getElementById('edit-rev-id').value = revisionId;
        document.getElementById('edit-rev-product-name').value = productName;
        document.getElementById('edit-rev-quantity').value = quantity;
        document.getElementById('edit-rev-barcode').value = barcode;
        document.getElementById('edit-rev-retail-price').value = price || '';
        document.getElementById('edit-rev-expiry-date').value = expiryDate;
        
        // Показываем модальное окно
        document.getElementById('edit-revision-modal').style.display = 'block';
    }
    
    function closeEditRevisionModal() {
        document.getElementById('edit-revision-modal').style.display = 'none';
    }
    
    async function saveEditRevision() {
        const revisionId = document.getElementById('edit-rev-id').value;
        const productName = document.getElementById('edit-rev-product-name').value.trim();
        const quantity = parseInt(document.getElementById('edit-rev-quantity').value) || 1;
        const barcode = document.getElementById('edit-rev-barcode').value.trim();
        const retailPrice = parseFloat(document.getElementById('edit-rev-retail-price').value);
        const expiryDate = document.getElementById('edit-rev-expiry-date').value;
        
        if (!productName) {
            alert('Введите название товара');
            return;
        }
        if (!retailPrice || retailPrice <= 0) {
            alert('Введите корректную цену');
            return;
        }
        if (!expiryDate) {
            alert('Выберите срок годности');
            return;
        }
        
        try {
            const response = await fetch(`/api/revision/revisions/${revisionId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    product_name: productName,
                    quantity: quantity,
                    barcode: barcode,
                    retail_price: retailPrice,
                    expiry_date: expiryDate
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                alert('✅ Товар обновлён');
                closeEditRevisionModal();
                loadRevisions();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка редактирования:', error);
            alert('Ошибка сети');
        }
    }
    
    async function deleteRevision(revisionId) {
        if (!confirm('⚠️ Вы уверены что хотите удалить этот товар?\n\nЭто действие нельзя отменить!')) return;
        
        try {
            const response = await fetch(`/api/revision/revisions/${revisionId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                alert('✅ Товар удалён');
                loadRevisions();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка удаления:', error);
            alert('Ошибка сети');
        }
    }

    // ============================================================================
    // УМНАЯ СИСТЕМА КОНТРОЛЯ ТОВАРОВ (v2.0)
    // ============================================================================

    /**
     * ЭТАП 4: Загрузка и отображение баннера умного контроля
     */
    async function loadSmartControlBanner() {
        try {
            const response = await fetch('/api/revision/warnings', { credentials: 'include' });
            const data = await response.json();

            if (data.status !== 'success') return;

            const banner = document.getElementById('smart-control-banner');
            if (!banner) return;

            const warnings = data.warnings;
            const hasWarnings = warnings.critical.length > 0 || warnings.warning.length > 0 || warnings.stagnant.length > 0;

            if (!hasWarnings) {
                banner.style.display = 'none';
                return;
            }

            banner.style.display = 'block';
            banner.innerHTML = `
                <h3>🧠 Умный контроль товаров</h3>

                <div class="smart-alert-summary">
                    <div class="smart-summary-card critical">
                        <div class="smart-summary-value">${warnings.critical.length}</div>
                        <div class="smart-summary-label">🔴 Критично (≤7 дн.)</div>
                    </div>
                    <div class="smart-summary-card warning">
                        <div class="smart-summary-value">${warnings.warning.length}</div>
                        <div class="smart-summary-label">🟠 Внимание (≤30 дн.)</div>
                    </div>
                    <div class="smart-summary-card stagnant">
                        <div class="smart-summary-value">${warnings.stagnant.length}</div>
                        <div class="smart-summary-label">🔵 Без движений</div>
                    </div>
                </div>

                ${warnings.critical.length > 0 ? `
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #dc2626;">🔴 Критично — истекают ≤7 дней:</strong>
                        ${warnings.critical.slice(0, 5).map(rev => `
                            <div class="smart-alert-item critical">
                                <div class="smart-alert-icon">🔴</div>
                                <div class="smart-alert-content">
                                    <div class="smart-alert-title">${escapeHtml(rev.product_name)}</div>
                                    <div class="smart-alert-desc">${rev.days_text} • Скидка ${rev.discount_percent}% • ${rev.full_name}</div>
                                </div>
                            </div>
                        `).join('')}
                        ${warnings.critical.length > 5 ? `<div style="color: #6b7280; font-size: 14px;">... и ещё ${warnings.critical.length - 5}</div>` : ''}
                    </div>
                ` : ''}

                ${warnings.warning.length > 0 ? `
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #ea580c;">🟠 Внимание — истекают ≤30 дней:</strong>
                        ${warnings.warning.slice(0, 3).map(rev => `
                            <div class="smart-alert-item high">
                                <div class="smart-alert-icon">🟠</div>
                                <div class="smart-alert-content">
                                    <div class="smart-alert-title">${escapeHtml(rev.product_name)}</div>
                                    <div class="smart-alert-desc">${rev.days_text} • Скидка ${rev.discount_percent}%</div>
                                </div>
                            </div>
                        `).join('')}
                        ${warnings.warning.length > 3 ? `<div style="color: #6b7280; font-size: 14px;">... и ещё ${warnings.warning.length - 3}</div>` : ''}
                    </div>
                ` : ''}

                ${warnings.stagnant.length > 0 ? `
                    <div>
                        <strong style="color: #2563eb;">🔵 Без движений >14 дней:</strong>
                        ${warnings.stagnant.slice(0, 3).map(rev => `
                            <div class="smart-alert-item low">
                                <div class="smart-alert-icon">🔵</div>
                                <div class="smart-alert-content">
                                    <div class="smart-alert-title">${escapeHtml(rev.product_name)}</div>
                                    <div class="smart-alert-desc">${rev.full_name} • Проверьте статус</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;
        } catch (error) {
            console.error('Ошибка загрузки умного контроля:', error);
        }
    }

    /**
     * ЭТАП 1: Показать предупреждения при запуске смены
     */
    async function showShiftWarnings() {
        try {
            const response = await fetch('/api/revision/warnings', { credentials: 'include' });
            const data = await response.json();

            if (data.status !== 'success') return;

            const warnings = data.warnings;
            const hasCritical = warnings.critical.length > 0;
            const hasWarning = warnings.warning.length > 0;

            if (!hasCritical && !hasWarning) return; // Нет предупреждений

            // Создаём модальное окно
            const modal = document.createElement('div');
            modal.className = 'modal shift-warnings-modal';
            modal.style.display = 'block';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">⚠️ ВНИМАНИЕ! Товары требуют проверки</h3>
                        <button type="button" class="close-modal" onclick="this.closest('.modal').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <p style="margin-bottom: 16px; color: #6b7280;">Перед началом смены проверьте следующие товары:</p>

                        <div class="shift-warning-list">
                            ${warnings.critical.map(rev => `
                                <div class="shift-warning-item critical">
                                    <div class="shift-warning-name">🔴 ${escapeHtml(rev.product_name)}</div>
                                    <div class="shift-warning-detail">
                                        ${rev.days_text} • Скидка ${rev.discount_percent}% • ${rev.full_name}<br>
                                        <strong>Рекомендация:</strong> Предложите покупателям со скидкой или сообщите админу
                                    </div>
                                </div>
                            `).join('')}

                            ${warnings.warning.map(rev => `
                                <div class="shift-warning-item">
                                    <div class="shift-warning-name">🟠 ${escapeHtml(rev.product_name)}</div>
                                    <div class="shift-warning-detail">
                                        ${rev.days_text} • Скидка ${rev.discount_percent}%<br>
                                        <strong>Рекомендация:</strong> Мониторьте продажу
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <div style="margin-top: 16px; padding: 12px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <strong>💡 Совет:</strong> Проверяйте сроки годности товаров перед каждой сменой. Это поможет избежать просрочки!
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="this.closest('.modal').remove()">✅ Понятно, начну смену</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
        } catch (error) {
            console.error('Ошибка показа предупреждений:', error);
        }
    }

    /**
     * ЭТАП 6: Управление выбором товаров для акционных ценников
     */
    function toggleSelectAllRevisions(checked) {
        document.querySelectorAll('.revision-checkbox').forEach(cb => {
            cb.checked = checked;
        });
        updatePromotionPanel();
    }

    function updatePromotionPanel() {
        const checkboxes = document.querySelectorAll('.revision-checkbox:checked');
        const panel = document.getElementById('promotion-panel');
        const countEl = document.getElementById('promotion-count');
        const selectAll = document.getElementById('select-all-revisions');

        if (countEl) countEl.textContent = checkboxes.length;

        if (panel) {
            panel.style.display = checkboxes.length > 0 ? 'block' : 'none';
        }

        // Обновляем состояние "выбрать все"
        const allCheckboxes = document.querySelectorAll('.revision-checkbox');
        if (selectAll && allCheckboxes.length > 0) {
            selectAll.checked = checkboxes.length === allCheckboxes.length && allCheckboxes.length > 0;
        }
    }

    function clearPromotionSelection() {
        document.querySelectorAll('.revision-checkbox').forEach(cb => {
            cb.checked = false;
        });
        const selectAll = document.getElementById('select-all-revisions');
        if (selectAll) selectAll.checked = false;
        updatePromotionPanel();
    }

    /**
     * ЭТАП 6: Генерация акционных ценников в формате конвертера
     * (толстые рамки, один столбик, старая/новая цена, "АКЦИЯ", огонёк)
     */
    async function generatePromotionPriceTags() {
        const checkboxes = document.querySelectorAll('.revision-checkbox:checked');

        if (checkboxes.length === 0) {
            alert('⚠️ Выберите товары для печати ценников');
            return;
        }

        // Собираем данные о выбранных товарах
        const products = [];
        checkboxes.forEach(cb => {
            products.push({
                name: cb.dataset.productName,
                barcode: cb.dataset.barcode,
                retail_price: parseFloat(cb.dataset.retailPrice),
                final_price: parseFloat(cb.dataset.price),
                discount: parseInt(cb.dataset.discount)
            });
        });

        // Создаём данные для акционных ценников в формате конвертера
        const converterData = {
            org_name: 'ООО "ВетГид"',
            products: products.map(p => ({
                name: p.name,
                price: p.final_price,
                old_price: p.retail_price,
                unit: 'шт',
                discount: p.discount
            })),
            settings: {
                cols: 1,  // Один столбик сверху вниз как просил пользователь
                font_name: 'Calibri',
                org_size: 14,
                org_bold: true,
                name_size: 14,
                name_bold: false,
                price_base: 24,
                price_bold: true,
                date_size: 10,
                date_bold: true
            }
        };

        try {
            // Отправляем данные в акционный генератор ценников
            const response = await fetch('/converter/generate-promotion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(converterData),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Ошибка генерации ценников');
            }

            // Скачиваем файл
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Акционные_ценники_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            alert(`✅ Создано ${products.length} акционных ценников!\n\nФайл скачан: Акционные_ценники_${new Date().toISOString().slice(0, 10)}.xlsx`);

            // Очищаем выбор
            clearPromotionSelection();
        } catch (error) {
            console.error('Ошибка генерации ценников:', error);
            alert('❌ Ошибка: ' + error.message);
        }
    }

    // ============================================================================
    // ПЕРЕХВАТ ШТРИХ-КОДОВ С КЛАВИАТУРЫ (HID режим сканера)
    // ============================================================================

    let barcodeBuffer = '';
    let barcodeTimer = null;
    const BARCODE_TIMEOUT = 100; // мс между символами
    const MIN_BARCODE_LENGTH = 8; // минимальная длина штрих-кода

    document.addEventListener('keydown', function(e) {
        // Игнорируем если фокус в текстовом поле (кроме специальных случаев)
        const activeElement = document.activeElement;
        const isInput = activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA');

        // Если модальное окно добавления товара открыто — перехватываем ВСЕ клавиши
        const modal = document.getElementById('revision-add-modal');
        const isModalOpen = modal && modal.style.display === 'block';

        if (isModalOpen) {
            // Модальное окно открыто — перехватываем ввод
            if (e.key === 'Enter') {
                // Enter — завершение штрих-кода
                if (barcodeBuffer.length >= MIN_BARCODE_LENGTH) {
                    console.log('📠 Штрих-код завершён (Enter):', barcodeBuffer);
                    handleBarcodeScanned(barcodeBuffer);
                    barcodeBuffer = '';
                    e.preventDefault();
                    e.stopPropagation();
                }
                return;
            }

            // Пропускаем специальные клавиши
            if (e.key.length > 1 && e.key !== 'Enter') {
                return; // Tab, Shift, Ctrl и т.д.
            }

            // Добавляем символ в буфер
            barcodeBuffer += e.key;
            
            // Сбрасываем таймер
            clearTimeout(barcodeTimer);
            barcodeTimer = setTimeout(() => {
                // Если прошло больше BARCODE_TIMEOUT — значит это не штрих-код а ручной ввод
                if (barcodeBuffer.length >= MIN_BARCODE_LENGTH) {
                    console.log('📠 Штрих-код завершён (timeout):', barcodeBuffer);
                    handleBarcodeScanned(barcodeBuffer);
                }
                barcodeBuffer = '';
            }, BARCODE_TIMEOUT);

            // Предотвращаем ввод в другие поля
            if (activeElement && activeElement.id !== 'rev-1c-search') {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });

    function handleBarcodeScanned(barcode) {
        console.log('🎯 Обработка штрих-кода:', barcode);

        // Очищаем буфер
        barcodeBuffer = '';
        clearTimeout(barcodeTimer);

        // Фокусируемся на поле поиска 1C
        const searchInput = document.getElementById('rev-1c-search');
        if (searchInput) {
            searchInput.value = barcode;
            searchInput.focus();
            
            // Авто-поиск товара
            console.log('🔍 Авто-поиск по штрих-коду:', barcode);
            search1cProducts();
        }

        // Звуковой сигнал
        playBeep();

        // Визуальное подтверждение
        showNotification('📠 Штрих-код отсканирован', barcode, 'success');
    }

    // ========================================
    // ПОИСК ТОВАРОВ В БАЗЕ 1С
    // ========================================
    
    async function search1cProducts() {
        const query = document.getElementById('rev-1c-search').value.trim();
        const resultsDiv = document.getElementById('rev-1c-results');

        if (!query) {
            resultsDiv.innerHTML = '<p style="color: var(--text-secondary);">Введите название или штрих-код</p>';
            return;
        }

        resultsDiv.innerHTML = '<p>🔍 Поиск...</p>';

        try {
            // Определяем тип поиска
            const isBarcode = /^\d+$/.test(query);
            let url;
            
            if (isBarcode) {
                // Поиск по штрих-коду — используем правильный маршрут
                url = `/api/products-1c/barcode/${encodeURIComponent(query)}`;
            } else {
                // Поиск по названию
                url = `/api/products-1c/search?query=${encodeURIComponent(query)}&limit=10`;
            }

            console.log('🔍 Поиск 1C:', url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📦 Результат поиска 1C:', data);

            if (data.status === 'success' && data.product) {
                // Для штрих-кода возвращаем один товар в data.product
                resultsDiv.innerHTML = `
                    <div style="padding: 8px; margin: 4px 0; background: white; border: 1px solid #e5e7eb; border-radius: 4px; cursor: pointer;"
                         onclick="select1cProduct(${JSON.stringify(data.product).replace(/"/g, '&quot;')})">
                        <div style="font-weight: bold;">${escapeHtml(data.product.name)}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${data.product.barcode_main ? `📦 ${data.product.barcode_main}` : ''}
                            ${data.product.retail_price ? `| ${data.product.retail_price} ₽` : ''}
                            ${data.product.group_name ? `| ${data.product.group_name}` : ''}
                        </div>
                    </div>
                `;
            } else if (data.status === 'success' && data.products && data.products.length > 0) {
                // Для поиска по названию возвращаем список в data.products
                resultsDiv.innerHTML = data.products.map(p => `
                    <div style="padding: 8px; margin: 4px 0; background: white; border: 1px solid #e5e7eb; border-radius: 4px; cursor: pointer;"
                         onclick="select1cProduct(${JSON.stringify(p).replace(/"/g, '&quot;')})">
                        <div style="font-weight: bold;">${escapeHtml(p.name)}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${p.barcode_main ? `📦 ${p.barcode_main}` : ''}
                            ${p.retail_price ? `| ${p.retail_price} ₽` : ''}
                            ${p.group_name ? `| ${p.group_name}` : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                resultsDiv.innerHTML = '<p style="color: var(--text-secondary);">Товары не найдены. Добавьте вручную.</p>';
            }
        } catch (error) {
            console.error('❌ Ошибка поиска 1C:', error);
            resultsDiv.innerHTML = `<p style="color: #dc2626;">❌ Ошибка: ${error.message}</p>`;
        }
    }
    
    function select1cProduct(product) {
        console.log('✅ Выбор товара из 1C:', product);
        
        // Заполняем поля данными из 1С
        document.getElementById('rev-product-name').value = product.name || '';
        document.getElementById('rev-barcode').value = product.barcode_main || '';
        document.getElementById('rev-retail-price').value = product.retail_price || '';

        // Очищаем результаты поиска
        document.getElementById('rev-1c-results').innerHTML = '<p style="color: #16a34a; font-weight: bold;">✅ Товар выбран! Заполните количество и срок годности.</p>';

        // Фокус на количество
        document.getElementById('rev-quantity').focus();
    }
    
    // Авто-поиск при вводе
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('rev-1c-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (this.value.length >= 3) {
                        search1cProducts();
                    }
                }, 500);
            });
        }
    });

    // Обработчик для страницы ревизии
    const revisionPage = document.getElementById('page-revision');
    if (revisionPage) {
        const observer = new MutationObserver(() => {
            if (revisionPage.style.display !== 'none') {
                loadRevisions();
                showShiftWarnings();  // ЭТАП 1: Показываем предупреждения при открытии
            }
        });
        observer.observe(revisionPage, {attributes: true, attributeFilter: ['style']});
    }

    // ========================================
    // УМНАЯ СТАТИСТИКА
    // ========================================
    
    async function openSmartStatsModal() {
        try {
            const response = await fetch('/api/smart/dashboard', {
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                const dashboard = data.dashboard;
                
                // Создаем модальное окно
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.style.display = 'block';
                modal.innerHTML = `
                    <div class="modal-content" style="max-width: 800px; max-height: 90vh;">
                        <div class="modal-header">
                            <h3>📊 Умная статистика ревизии</h3>
                            <button type="button" class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                        </div>
                        <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                            <div class="smart-dashboard">
                                <div class="smart-section quick-stats">
                                    <h3>📊 Быстрая статистика</h3>
                                    <div class="stats-grid">
                                        <div class="stat-card ${dashboard.quick_stats.expiring_soon > 0 ? 'warning' : ''}">
                                            <div class="stat-value">${dashboard.quick_stats.active_items}</div>
                                            <div class="stat-label">Активных товаров</div>
                                        </div>
                                        <div class="stat-card ${dashboard.quick_stats.expiring_soon > 0 ? 'urgent' : ''}">
                                            <div class="stat-value">${dashboard.quick_stats.expiring_soon}</div>
                                            <div class="stat-label">Скоро истекает</div>
                                        </div>
                                        <div class="stat-card ${dashboard.quick_stats.need_decision > 0 ? 'danger' : ''}">
                                            <div class="stat-value">${dashboard.quick_stats.need_decision}</div>
                                            <div class="stat-label">Требуют решения</div>
                                        </div>
                                        <div class="stat-card ${dashboard.quick_stats.high_discount > 0 ? 'info' : ''}">
                                            <div class="stat-value">${dashboard.quick_stats.high_discount}</div>
                                            <div class="stat-label">Большая скидка</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="smart-section performance">
                                    <h3>📈 Производительность</h3>
                                    <div class="performance-grid">
                                        <div class="perf-card">
                                            <div class="perf-title">7 дней</div>
                                            <div class="perf-value">${formatCurrency(dashboard.performance['7d_revenue'])}</div>
                                            <div class="perf-sub">${dashboard.performance['7d_sold']} продаж</div>
                                        </div>
                                        <div class="perf-card">
                                            <div class="perf-title">30 дней</div>
                                            <div class="perf-value">${formatCurrency(dashboard.performance['30d_revenue'])}</div>
                                            <div class="perf-sub">${dashboard.performance['30d_sold']} продаж</div>
                                        </div>
                                        <div class="perf-card">
                                            <div class="perf-title">Эффективность</div>
                                            <div class="perf-value ${dashboard.performance.efficiency < 70 ? 'low' : 'good'}">
                                                ${dashboard.performance.efficiency}%
                                            </div>
                                            <div class="perf-sub">продажи vs списания</div>
                                        </div>
                                    </div>
                                </div>
                                
                                ${dashboard.reminders && dashboard.reminders.length > 0 ? `
                                <div class="smart-section reminders">
                                    <h3>🔔 Активные напоминания</h3>
                                    <div class="reminders-list">
                                        ${dashboard.reminders.map(reminder => `
                                            <div class="reminder-item ${reminder.priority}">
                                                <div class="reminder-header">
                                                    <div class="reminder-title">${reminder.title}</div>
                                                    <div class="reminder-priority">${reminder.priority === 'urgent' ? '🔴' : reminder.priority === 'high' ? '🟠' : '🔵'}</div>
                                                </div>
                                                <div class="reminder-message">${reminder.message}</div>
                                                ${reminder.product_name ? `
                                                    <div class="reminder-product">
                                                        <strong>Товар:</strong> ${reminder.product_name}
                                                    </div>
                                                ` : ''}
                                                <div class="reminder-actions">
                                                    <button class="btn btn-sm btn-primary" onclick="completeReminder(${reminder.id})">✅ Выполнено</button>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                ` : ''}
                                
                                ${dashboard.top_employees && dashboard.top_employees.length > 0 ? `
                                <div class="smart-section">
                                    <h3>👥 Топ сотрудники</h3>
                                    <div class="employees-list">
                                        ${dashboard.top_employees.map((emp, index) => `
                                            <div class="employee-card">
                                                <div class="employee-rank">${index + 1}</div>
                                                <div class="employee-info">
                                                    <div class="employee-name">${emp.full_name}</div>
                                                    <div class="employee-stats">
                                                        <div class="stat">${emp.total_operations} операций</div>
                                                        <div class="stat">${emp.total_sold} продаж</div>
                                                        <div class="stat">${formatCurrency(emp.total_revenue)}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                ` : ''}
                                
                                ${dashboard.top_products && dashboard.top_products.length > 0 ? `
                                <div class="smart-section">
                                    <h3>📦 Топ товары</h3>
                                    <div class="products-list">
                                        ${dashboard.top_products.map((prod, index) => `
                                            <div class="product-card">
                                                <div class="employee-rank">${index + 1}</div>
                                                <div class="product-name">${prod.product_name}</div>
                                                <div class="product-stats">
                                                    <div class="stat">${prod.total_operations} операций</div>
                                                    <div class="stat">${prod.total_sold} продаж</div>
                                                    <div class="stat">${formatCurrency(prod.total_revenue)}</div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Закрыть</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
            } else {
                alert('Ошибка загрузки статистики: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка загрузки умной статистики:', error);
            alert('Ошибка сети при загрузке статистики');
        }
    }
    
    function formatCurrency(value) {
        return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value);
    }
    
    async function completeReminder(reminderId) {
        try {
            const response = await fetch(`/api/smart/reminders/${reminderId}/complete`, {
                method: 'POST',
                credentials: 'include'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                alert('✅ Напоминание отмечено как выполненное');
                // Закрываем модальное окно и обновляем
                document.querySelector('.modal').remove();
                openSmartStatsModal();
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (error) {
            console.error('Ошибка выполнения напоминания:', error);
            alert('Ошибка сети');
        }
    }

    