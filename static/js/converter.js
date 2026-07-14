/**
 * Конвертер ценников 2.0 - клиентская часть
 */

(function() {
    'use strict';

    // Элементы
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const colsCount = document.getElementById('cols-count');
    const orgName = document.getElementById('org-name');
    const orgSize = document.getElementById('org-size');
    const orgBold = document.getElementById('org-bold');
    const nameSize = document.getElementById('name-size');
    const nameBold = document.getElementById('name-bold');
    const priceBase = document.getElementById('price-base');
    const priceBold = document.getElementById('price-bold');
    const dateSize = document.getElementById('date-size');
    const dateBold = document.getElementById('date-bold');
    const btnGenerate = document.getElementById('btn-generate');
    const btnDownload = document.getElementById('btn-download');
    const btnRefreshFiles = document.getElementById('btn-refresh-files');
    const previewCanvas = document.getElementById('preview-canvas');
    const statusMessage = document.getElementById('status-message');
    const resultCard = document.getElementById('result-card');
    const resultMessage = document.getElementById('result-message');
    const filesList = document.getElementById('files-list');

    // Данные
    let uploadedFile = null;
    let itemsData = [];
    let generatedFileUrl = null;

    // Инициализация
    function init() {
        fileInput.addEventListener('change', onFileSelect);
        btnGenerate.addEventListener('click', onGenerate);
        btnDownload.addEventListener('click', onDownload);
        if (btnRefreshFiles) {
            btnRefreshFiles.addEventListener('click', loadFilesList);
        }
        
        // Кнопка загрузки с компьютера
        const btnLoadFromPc = document.getElementById('btn-load-from-pc');
        const fileFromPc = document.getElementById('file-from-pc');
        if (btnLoadFromPc && fileFromPc) {
            btnLoadFromPc.addEventListener('click', function() {
                fileFromPc.click();
            });
        }

        // Обновление превью при изменении настроек
        const inputs = [orgName, orgSize, orgBold, nameSize, nameBold, priceBase, priceBold, dateSize, dateBold];
        inputs.forEach(input => {
            input.addEventListener('input', updatePreview);
            input.addEventListener('change', updatePreview);
        });

        // Загрузка списка файлов
        loadFilesList();

        // Отрисовка демо-превью
        drawPreviewDemo();
    }
    
    // Загрузка файла с компьютера
    window.onFileFromPcSelected = function(input) {
        if (input.files && input.files[0]) {
            const file = input.files[0];
            uploadedFile = file;
            fileName.textContent = file.name;
            
            // Загружаем файл на сервер
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/api/converter/upload', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                                    statusMessage.textContent = `✅ Файл загружен: ${file.name}`;
                    statusMessage.className = 'status-message success';
                    
                    // Анализируем файл
                    analyzeFile(data.filename);
                    
                    // Обновляем список файлов
                    loadFilesList();
                } else {
                    statusMessage.textContent = `❌ Ошибка: ${data.message}`;
                    statusMessage.className = 'status-message error';
                }
            })
            .catch(err => {
                statusMessage.textContent = '❌ Ошибка загрузки файла';
                statusMessage.className = 'status-message error';
                console.error(err);
            });
        }
    };

    // Загрузка списка файлов
    function loadFilesList() {
        if (!filesList) return;

        filesList.innerHTML = '<p class="text-muted">Загрузка...</p>';

        fetch('/converter/files', { credentials: 'include' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.files && data.files.length > 0) {
                let html = '<div class="files-list-inner">';
                data.files.forEach(file => {
                    const isOutput = file.type === 'output';
                    const date = new Date(file.created_at).toLocaleString('ru-RU');
                    const size = (file.size / 1024).toFixed(1) + ' КБ';
                    
                    html += `
                        <div class="file-item ${isOutput ? 'file-item-output' : ''}" data-filename="${file.filename}">
                            <div class="file-item-info">
                                <div class="file-item-name">
                                    ${isOutput ? '✅ ' : '📄 '}${file.filename}
                                </div>
                                <div class="file-item-date">${date} · ${size}</div>
                                ${isOutput && file.products_count ? `<div class="file-item-meta">📦 ${file.products_count} товаров</div>` : ''}
                            </div>
                            <div class="file-item-actions">
                                ${isOutput ? `
                                    <button type="button" class="btn btn-sm btn-primary" onclick="viewFile('${file.filename}')" title="Открыть/Просмотр">👁️</button>
                                    <button type="button" class="btn btn-sm btn-success" onclick="downloadFile('${file.filename}')" title="Скачать">⬇️</button>
                                ` : `
                                    <span class="text-muted" style="font-size:11px;">Исходный файл</span>
                                `}
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                filesList.innerHTML = html;
            } else {
                filesList.innerHTML = '<p class="text-muted">Нет файлов</p>';
            }
        })
        .catch(err => {
            filesList.innerHTML = '<p class="text-muted error">Ошибка загрузки списка</p>';
            console.error('Ошибка загрузки списка файлов:', err);
        });
    }

    // Открыть файл (просмотр)
    window.viewFile = function(filename) {
        // Открываем в новой вкладке - браузер сам решит открыть или скачать
        window.open(`/converter/view/${encodeURIComponent(filename)}`, '_blank');
        showToast('Файл открывается...', 'info');
    }

    // Скачать файл
    window.downloadFile = function(filename) {
        const a = document.createElement('a');
        a.href = `/converter/download/${encodeURIComponent(filename)}`;
        a.download = filename;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast('Файл скачан: ' + filename, 'success');
    };

    // Печать файла
    window.printFile = function(filename) {
        if (!confirm('Отправить файл "' + filename + '" на печать?')) return;

        fetch('/api/converter/print', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filename: filename})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Файл отправлен на печать', 'success');
            } else {
                showToast('Ошибка: ' + data.error, 'error');
            }
        })
        .catch(err => {
            showToast('Ошибка печати: ' + err.message, 'error');
        });
    };

    // Выбор файла
    function onFileSelect(e) {
        const file = e.target.files[0];
        if (!file) {
            fileName.textContent = '';
            uploadedFile = null;
            itemsData = [];
            drawPreviewDemo();
            return;
        }
        
        uploadedFile = file;
        fileName.textContent = file.name;
        
        // Загрузка файла на сервер для анализа
        uploadFileForAnalysis(file);
    }

    // Загрузка файла для анализа
    function uploadFileForAnalysis(file) {
        const formData = new FormData();
        formData.append('file', file);

        showStatus('Загрузка и анализ файла...', 'info');

        // Сначала загружаем файл
        fetch('/converter/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(uploadData => {
            if (uploadData.status === 'success') {
                // Затем отправляем filename на анализ
                return fetch('/converter/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: uploadData.filename })
                });
            } else {
                throw new Error(uploadData.message || 'Ошибка загрузки');
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Сервер возвращает "products", а не "items"
                itemsData = data.products || [];
                showStatus(`Загружено позиций: ${data.count || itemsData.length}`, 'success');
                if (itemsData.length > 0) {
                    updatePreview();
                }
            } else {
                showStatus(`Ошибка: ${data.message || data.error}`, 'error');
                itemsData = [];
                drawPreviewDemo();
            }
        })
        .catch(err => {
            showStatus(`Ошибка загрузки: ${err.message}`, 'error');
            itemsData = [];
            drawPreviewDemo();
        });
    }

    // Генерация ценников
    function onGenerate() {
        if (!uploadedFile) {
            showStatus('Сначала выберите Excel файл', 'error');
            return;
        }

        if (itemsData.length === 0) {
            showStatus('Файл не содержит валидных данных', 'error');
            return;
        }

        const settings = collectSettings();
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('cols', settings.cols);
        formData.append('org_name', settings.org_name);
        formData.append('org_size', settings.org_size);
        formData.append('org_bold', settings.org_bold ? '1' : '0');
        formData.append('name_size', settings.name_size);
        formData.append('name_bold', settings.name_bold ? '1' : '0');
        formData.append('price_base', settings.price_base);
        formData.append('price_bold', settings.price_bold ? '1' : '0');
        formData.append('date_size', settings.date_size);
        formData.append('date_bold', settings.date_bold ? '1' : '0');

        showStatus('Формирование ценников...', 'info');
        btnGenerate.disabled = true;

        fetch('/converter/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                products: itemsData,
                settings: settings,
                markup: 0  // Наценка 0% по умолчанию
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message || 'Ошибка генерации'); });
            }
            return response.blob();
        })
        .then(blob => {
            // Создаём ссылку для скачивания
            if (generatedFileUrl) {
                URL.revokeObjectURL(generatedFileUrl);
            }
            generatedFileUrl = URL.createObjectURL(blob);

            const filename = `ценники_${formatTimestamp()}.xlsx`;
            resultMessage.textContent = `✅ Файл создан: ${filename}`;
            resultCard.style.display = 'block';
            btnDownload.dataset.filename = filename;

            // Обновляем список файлов
            loadFilesList();

            showStatus('Ценники успешно сформированы!', 'success');
        })
        .catch(err => {
            showStatus(`Ошибка: ${err.message}`, 'error');
        })
        .finally(() => {
            btnGenerate.disabled = false;
        });
    }

    // Скачивание файла
    function onDownload() {
        if (!generatedFileUrl) return;
        
        const a = document.createElement('a');
        a.href = generatedFileUrl;
        a.download = btnDownload.dataset.filename || 'ценники.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // Сбор настроек
    function collectSettings() {
        return {
            cols: parseInt(colsCount.value) || 3,
            font_name: document.getElementById('font-name')?.value || 'Calibri',
            org_name: orgName.value.trim() || 'ООО "КАКИЕ ЛЮДИ"',
            org_size: parseInt(orgSize.value) || 14,
            org_bold: orgBold.checked,
            name_size: parseInt(nameSize.value) || 14,
            name_bold: nameBold.checked,
            price_base: parseInt(priceBase.value) || 24,
            price_bold: priceBold.checked,
            date_size: parseInt(dateSize.value) || 10,
            date_bold: dateBold.checked
        };
    }

    // Обновление превью
    function updatePreview() {
        if (!itemsData || itemsData.length === 0) {
            drawPreviewDemo();
            return;
        }
        
        const settings = collectSettings();
        const item = itemsData[0]; // Первая позиция для превью
        
        drawPreview(item.name, item.price, settings);
    }

    // Демо-превью
    function drawPreviewDemo() {
        const settings = collectSettings();
        drawPreview(
            'Пример товара с длинным наименованием для проверки переноса строк',
            12345,
            settings
        );
    }

    // Отрисовка превью
    function drawPreview(name, price, settings) {
        const ctx = previewCanvas.getContext('2d');
        const width = previewCanvas.width;
        const height = previewCanvas.height;
        
        // Очистка
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);
        
        // Параметры
        const padding = 20;
        const blockWidth = width - padding * 2;
        
        // Шрифты
        const orgFont = `${settings.org_bold ? 'bold ' : ''}${settings.org_size}px Calibri`;
        const nameFont = `${settings.name_bold ? 'bold ' : ''}${settings.name_size}px Calibri`;
        const priceFontSize = getPriceFontSize(price, settings.price_base);
        const priceFont = `${settings.price_bold ? 'bold ' : ''}${priceFontSize}px Calibri`;
        const dateFont = `${settings.date_bold ? 'bold ' : ''}${settings.date_size}px Calibri`;
        
        // Высоты строк
        const orgHeight = Math.ceil(settings.org_size * 1.3) + 8;
        const dateHeight = Math.ceil(settings.date_size * 1.3) + 8;
        
        // Перенос наименования
        const nameLines = wrapText(ctx, name, blockWidth - 8, nameFont);
        const nameHeight = Math.ceil(settings.name_size * 1.3 * nameLines.length) + 8;
        const priceHeight = Math.ceil(priceFontSize * 1.3) + 10;
        
        const totalHeight = orgHeight + nameHeight + priceHeight + dateHeight;
        const startY = padding + Math.max(0, (height - totalHeight) / 2);
        
        // Рамки
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1;
        
        // Внешняя рамка
        ctx.strokeRect(padding, startY, blockWidth, totalHeight);
        
        // Горизонтальные линии
        ctx.beginPath();
        ctx.moveTo(padding, startY + orgHeight);
        ctx.lineTo(padding + blockWidth, startY + orgHeight);
        ctx.moveTo(padding, startY + orgHeight + nameHeight);
        ctx.lineTo(padding + blockWidth, startY + orgHeight + nameHeight);
        ctx.moveTo(padding, startY + orgHeight + nameHeight + priceHeight);
        ctx.lineTo(padding + blockWidth, startY + orgHeight + nameHeight + priceHeight);
        ctx.stroke();
        
        // Текст организации
        ctx.font = orgFont;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#000000';
        ctx.fillText(settings.org_name, padding + blockWidth / 2, startY + orgHeight / 2);
        
        // Наименование
        ctx.font = nameFont;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        let y = startY + orgHeight + 4;
        nameLines.forEach(line => {
            ctx.fillText(line, padding + 4, y);
            y += Math.ceil(settings.name_size * 1.3);
        });
        
        // Цена
        ctx.font = priceFont;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const priceInt = Math.round(price);
        ctx.fillText(`${priceInt}  р.`, padding + blockWidth / 2, startY + orgHeight + nameHeight + priceHeight / 2);
        
        // Дата
        ctx.font = dateFont;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        const today = new Date();
        const dateStr = `${String(today.getDate()).padStart(2, '0')}.${String(today.getMonth() + 1).padStart(2, '0')}.${today.getFullYear()}`;
        ctx.fillText(`Дата: ${dateStr}`, padding + 4, startY + orgHeight + nameHeight + priceHeight + dateHeight / 2);
    }

    // Размер шрифта цены
    function getPriceFontSize(price, baseSize) {
        const digits = String(Math.round(price)).length;
        let size = baseSize;
        if (digits > 4) {
            size = baseSize - (digits - 4);
        }
        return Math.max(12, size);
    }

    // Перенос текста
    function wrapText(ctx, text, maxWidth, font) {
        ctx.font = font;
        const words = text.split(' ');
        const lines = [];
        let line = '';
        
        for (let word of words) {
            const testLine = line ? `${line} ${word}` : word;
            const metrics = ctx.measureText(testLine);
            
            if (metrics.width <= maxWidth) {
                line = testLine;
            } else {
                if (line) lines.push(line);
                line = word;
            }
        }
        if (line) lines.push(line);
        
        return lines;
    }

    // Форматирование времени
    function formatTimestamp() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `${year}${month}${day}_${hours}${minutes}${seconds}`;
    }

    // Показ статуса
    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        
        if (type !== 'info') {
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 5000);
        }
    }

    // Запуск
    init();
})();
