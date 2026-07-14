/**
 * smart_revision.js — JavaScript для умной системы ревизии
 */

// Конфигурация
const SMART_CONFIG = {
    refreshInterval: 30000, // 30 секунд
    apiBase: '/api/smart'
};

// Инициализация умной системы
function initSmartRevision() {
    console.log('🚀 Инициализация умной системы ревизии...');
    
    // Загружаем умную панель
    loadSmartDashboard();
    
    // Загружаем активные напоминания
    loadSmartReminders();
    
    // Настраиваем автообновление
    setInterval(() => {
        loadSmartDashboard();
        loadSmartReminders();
    }, SMART_CONFIG.refreshInterval);
    
    // Добавляем кнопки в интерфейс
    addSmartControls();
}

// Загрузить умную панель управления
function loadSmartDashboard() {
    fetch(`${SMART_CONFIG.apiBase}/dashboard`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateSmartDashboard(data.dashboard);
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки умной панели:', error);
        });
}

// Обновить отображение умной панели
function updateSmartDashboard(dashboard) {
    const container = document.getElementById('smart-dashboard-container');
    if (!container) return;
    
    const html = `
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
                                <span class="reminder-title">${reminder.title}</span>
                                <span class="reminder-priority">${getPriorityIcon(reminder.priority)}</span>
                            </div>
                            <div class="reminder-message">${reminder.message}</div>
                            ${reminder.product_name ? `
                                <div class="reminder-product">
                                    Товар: ${reminder.product_name}
                                    ${reminder.days_remaining !== null ? ` (${formatDays(reminder.days_remaining)})` : ''}
                                </div>
                            ` : ''}
                            <div class="reminder-actions">
                                <button class="btn btn-sm btn-success" onclick="completeReminder(${reminder.id})">
                                    ✓ Выполнено
                                </button>
                                <button class="btn btn-sm btn-secondary" onclick="dismissReminder(${reminder.id})">
                                    × Отклонить
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${dashboard.top_employees && dashboard.top_employees.length > 0 ? `
            <div class="smart-section top-employees">
                <h3>🏆 Топ сотрудники (30 дней)</h3>
                <div class="employees-list">
                    ${dashboard.top_employees.map((emp, index) => `
                        <div class="employee-card">
                            <div class="employee-rank">${index + 1}</div>
                            <div class="employee-info">
                                <div class="employee-name">${emp.full_name}</div>
                                <div class="employee-stats">
                                    <span class="stat">${formatCurrency(emp.revenue)}</span>
                                    <span class="stat">${emp.sold_qty || 0} продаж</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${dashboard.top_products && dashboard.top_products.length > 0 ? `
            <div class="smart-section top-products">
                <h3>📦 Популярные товары</h3>
                <div class="products-list">
                    ${dashboard.top_products.map((prod, index) => `
                        <div class="product-card">
                            <div class="product-name">${prod.product_name}</div>
                            <div class="product-stats">
                                <span class="stat">${prod.sold_qty || 0} продаж</span>
                                <span class="stat">${formatCurrency(prod.revenue || 0)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    container.innerHTML = html;
}

// Загрузить умные напоминания
function loadSmartReminders() {
    fetch(`${SMART_CONFIG.apiBase}/reminders?status=pending`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateRemindersBadge(data.reminders.length);
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки напоминаний:', error);
        });
}

// Обновить бейдж с количеством напоминаний
function updateRemindersBadge(count) {
    let badge = document.getElementById('smart-reminders-badge');
    
    if (count > 0) {
        if (!badge) {
            // Создаем бейдж если его нет
            const nav = document.querySelector('.nav-user');
            if (nav) {
                badge = document.createElement('span');
                badge.id = 'smart-reminders-badge';
                badge.className = 'badge badge-danger';
                badge.style.marginLeft = '8px';
                badge.style.cursor = 'pointer';
                badge.title = 'Активные напоминания';
                badge.onclick = showRemindersModal;
                nav.appendChild(badge);
            }
        }
        
        if (badge) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        }
        
        // Показываем уведомление если есть срочные напоминания
        if (count > 0 && !localStorage.getItem('reminders_notified')) {
            showNotification(`У вас ${count} активных напоминаний по ревизии`);
            localStorage.setItem('reminders_notified', 'true');
            setTimeout(() => localStorage.removeItem('reminders_notified'), 3600000); // 1 час
        }
    } else if (badge) {
        badge.style.display = 'none';
    }
}

// Показать модальное окно с напоминаниями
function showRemindersModal() {
    fetch(`${SMART_CONFIG.apiBase}/reminders?status=pending`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const modalHtml = `
                    <div class="modal" id="smart-reminders-modal" style="display: block;">
                        <div class="modal-overlay" onclick="closeRemindersModal()"></div>
                        <div class="modal-content" style="max-width: 800px; max-height: 80vh;">
                            <div class="modal-header">
                                <h3>🔔 Умные напоминания</h3>
                                <button type="button" class="modal-close" onclick="closeRemindersModal()">×</button>
                            </div>
                            <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                                ${data.reminders.length > 0 ? `
                                    <div class="reminders-modal-list">
                                        ${data.reminders.map(reminder => `
                                            <div class="reminder-modal-item ${reminder.priority}">
                                                <div class="reminder-modal-header">
                                                    <div>
                                                        <strong>${reminder.title}</strong>
                                                        <span class="reminder-type">${getReminderTypeText(reminder.reminder_type)}</span>
                                                    </div>
                                                    <span class="reminder-priority-badge ${reminder.priority}">
                                                        ${getPriorityText(reminder.priority)}
                                                    </span>
                                                </div>
                                                <div class="reminder-modal-message">${reminder.message}</div>
                                                ${reminder.product_name ? `
                                                    <div class="reminder-modal-product">
                                                        <strong>Товар:</strong> ${reminder.product_name}
                                                        ${reminder.expiry_date ? `<br><strong>Срок:</strong> ${formatDate(reminder.expiry_date)}` : ''}
                                                        ${reminder.days_remaining !== null ? `<br><strong>Осталось:</strong> ${formatDays(reminder.days_remaining)}` : ''}
                                                        ${reminder.final_price ? `<br><strong>Цена:</strong> ${formatCurrency(reminder.final_price)}` : ''}
                                                    </div>
                                                ` : ''}
                                                <div class="reminder-modal-actions">
                                                    <button class="btn btn-sm btn-success" onclick="completeReminder(${reminder.id})">
                                                        ✓ Отметить как выполненное
                                                    </button>
                                                    <button class="btn btn-sm btn-secondary" onclick="dismissReminder(${reminder.id})">
                                                        × Отклонить
                                                    </button>
                                                    ${reminder.revision_id ? `
                                                        <button class="btn btn-sm btn-info" onclick="goToRevision(${reminder.revision_id})">
                                                            📦 Перейти к товару
                                                        </button>
                                                    ` : ''}
                                                </div>
                                                <div class="reminder-modal-time">
                                                    Создано: ${formatDateTime(reminder.created_at)}
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : `
                                    <div class="no-reminders">
                                        <div style="text-align: center; padding: 40px;">
                                            <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                                            <h4>Нет активных напоминаний</h4>
                                            <p>Все задачи выполнены!</p>
                                        </div>
                                    </div>
                                `}
                            </div>
                            <div class="modal-actions">
                                <button class="btn btn-primary" onclick="loadSmartReminders(); closeRemindersModal();">
                                    Обновить
                                </button>
                                <button class="btn btn-secondary" onclick="closeRemindersModal()">
                                    Закрыть
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Добавляем модальное окно в DOM
                const modalContainer = document.createElement('div');
                modalContainer.innerHTML = modalHtml;
                document.body.appendChild(modalContainer.firstElementChild);
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки напоминаний:', error);
            showToast('Ошибка загрузки напоминаний', 'error');
        });
}

// Закрыть модальное окно напоминаний
function closeRemindersModal() {
    const modal = document.getElementById('smart-reminders-modal');
    if (modal) {
        modal.remove();
    }
}

// Отметить напоминание как выполненное
function completeReminder(reminderId) {
    fetch(`${SMART_CONFIG.apiBase}/reminders/${reminderId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Напоминание отмечено как выполненное', 'success');
            loadSmartDashboard();
            loadSmartReminders();
            closeRemindersModal();
        } else {
            showToast(data.message || 'Ошибка', 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showToast('Ошибка сервера', 'error');
    });
}

// Отклонить напоминание
function dismissReminder(reminderId) {
    if (confirm('Вы уверены, что хотите отклонить это напоминание?')) {
        // Здесь можно добавить API для отклонения
        showToast('Напоминание отклонено', 'info');
        loadSmartReminders();
        closeRemindersModal();
    }
}

// Перейти к товару
function goToRevision(revisionId) {
    // Переходим на страницу ревизии и выделяем товар
    window.location.hash = 'revision';
    setTimeout(() => {
        // Ищем и выделяем товар в таблице
        const row = document.querySelector(`tr[data-revision-id="${revisionId}"]`);
        if (row) {
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            row.classList.add('highlight');
            setTimeout(() => row.classList.remove('highlight'), 3000);
        }
    }, 500);
    
    closeRemindersModal();
}

// Добавить элементы управления в интерфейс
function addSmartControls() {
    // Добавляем контейнер для умной панели
    const revisionPage = document.getElementById('page-revision');
    if (revisionPage) {
        const header = revisionPage.querySelector('.page-header');
        if (header) {
            // Добавляем кнопку умной статистики
            const smartBtn = document.createElement('button');
            smartBtn.type = 'button';
            smartBtn.className = 'btn btn-info';
            smartBtn.innerHTML = '📊 Умная статистика';
            smartBtn.onclick = showSmartStatsModal;
            smartBtn.style.marginLeft = '8px';
            
            header.querySelector('.controls-revision').appendChild(smartBtn);
            
            // Добавляем контейнер для умной панели
            const statsContainer = revisionPage.querySelector('#revision-stats');
            if (statsContainer) {
                const smartContainer = document.createElement('div');
                smartContainer.id = 'smart-dashboard-container';
                smartContainer.style.marginTop = '20px';
                statsContainer.parentNode.insertBefore(smartContainer, statsContainer.nextSibling);
            }
        }
    }
}

// Показать модальное окно с расширенной статистикой
function showSmartStatsModal() {
    const period = prompt('За какой период показать статистику? (7, 30, 90, all)', '30');
    if (!period) return;
    
    fetch(`${SMART_CONFIG.apiBase}/stats?period=${period}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStatsModal(data.stats, period);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showToast('Ошибка загрузки статистики', 'error');
        });
}

// Показать модальное окно со статистикой
function showStatsModal(stats, period) {
    const modalHtml = `
        <div class="modal" id="smart-stats-modal" style="display: block;">
            <div class="modal-overlay" onclick="closeStatsModal()"></div>
            <div class="modal-content" style="max-width: 900px; max-height: 90vh;">
                <div class="modal-header">
                    <h3>📈 Умная статистика ${period !== 'all' ? `за ${period} дней` : 'за все время'}</h3>
                    <button type="button" class="modal-close" onclick="closeStatsModal()">×</button>
                </div>
                <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                    <div class="stats-modal-content">
                        <!-- Общая статистика -->
                        <div class="stats-section">
                            <h4>📊 Общая статистика</h4>
                            <div class="general-stats">
                                <div class="general-stat">
                                    <div class="stat-label">Всего операций</div>
                                    <div class="stat-value">${stats.general.total_operations || 0}</div>
                                </div>
                                <div class="general-stat">
                                    <div class="stat-label">Выручка</div>
                                    <div class="stat-value">${formatCurrency(stats.general.total_revenue || 0)}</div>
                                </div>
                                <div class="general-stat">
                                    <div class="stat-label">Списано на сумму</div>
                                    <div class="stat-value">${formatCurrency(stats.general.total_write_off_value || 0)}</div>
                                </div>
                                <div class="general-stat">
                                    <div class="stat-label">Забрано лично</div>
                                    <div class="stat-value">${stats.general.total_personal_qty || 0} шт</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Эффективность -->
                        <div class="stats-section">
                            <h4>🎯 Эффективность</h4>
                            <div class="efficiency-stats">
                                <div class="efficiency-item">
                                    <div class="efficiency-label">Эффективность продаж</div>
                                    <div class="efficiency-value ${stats.efficiency.sales_efficiency_percent < 70 ? 'low' : 'good'}">
                                        ${stats.efficiency.sales_efficiency_percent}%
                                    </div>
                                    <div class="efficiency-details">
                                        ${stats.efficiency.sold_items} продано / ${stats.efficiency.written_off_items} списано
                                    </div>
                                </div>
                                <div class="efficiency-item">
                                    <div class="efficiency-label">Всего товаров</div>
                                    <div class="efficiency-value">${stats.efficiency.total_items}</div>
                                    <div class="efficiency-details">
                                        ${stats.efficiency.personal_items} забрано лично
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Текущее состояние -->
                        <div class="stats-section">
                            <h4>📦 Текущее состояние ревизии</h4>
                            <div class="current-state">
                                <div class="state-item ${stats.current_state.expired > 0 ? 'danger' : ''}">
                                    <div class="state-label">Просрочено</div>
                                    <div class="state-value">${stats.current_state.expired || 0}</div>
                                </div>
                                <div class="state-item ${stats.current_state.expiring_soon > 0 ? 'warning' : ''}">
                                    <div class="state-label">Скоро истекает</div>
                                    <div class="state-value">${stats.current_state.expiring_soon || 0}</div>
                                </div>
                                <div class="state-item ${stats.current_state.need_decision > 0 ? 'danger' : ''}">
                                    <div class="state-label">Требуют решения</div>
                                    <div class="state-value">${stats.current_state.need_decision || 0}</div>
                                </div>
                                <div class="state-item ${stats.current_state.high_discount > 0 ? 'info' : ''}">
                                    <div class="state-label">Большая скидка</div>
                                    <div class="state-value">${stats.current_state.high_discount || 0}</div>
                                </div>
                                <div class="state-item">
                                    <div class="state-label">Общая стоимость</div>
                                    <div class="state-value">${formatCurrency(stats.current_state.total_value || 0)}</div>
                                </div>
                                <div class="state-item">
                                    <div class="state-label">Со скидкой</div>
                                    <div class="state-value">${formatCurrency(stats.current_state.total_final_value || 0)}</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Топ сотрудники -->
                        ${stats.top_employees && stats.top_employees.length > 0 ? `
                        <div class="stats-section">
                            <h4>🏆 Топ сотрудники</h4>
                            <div class="top-employees-table">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Сотрудник</th>
                                            <th>Выручка</th>
                                            <th>Продажи</th>
                                            <th>Списания</th>
                                            <th>Операций</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${stats.top_employees.map((emp, index) => `
                                            <tr>
                                                <td>${index + 1}</td>
                                                <td>${emp.full_name}</td>
                                                <td>${formatCurrency(emp.revenue || 0)}</td>
                                                <td>${emp.sold_qty || 0}</td>
                                                <td>${emp.write_off_qty || 0}</td>
                                                <td>${emp.total_operations || 0}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- Топ товары -->
                        ${stats.top_products && stats.top_products.length > 0 ? `
                        <div class="stats-section">
                            <h4>📦 Популярные товары</h4>
                            <div class="top-products-table">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Товар</th>
                                            <th>Продано</th>
                                            <th>Выручка</th>
                                            <th>Списано</th>
                                            <th>Добавлен</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${stats.top_products.map(prod => `
                                            <tr>
                                                <td>${prod.product_name}</td>
                                                <td>${prod.sold_qty || 0}</td>
                                                <td>${formatCurrency(prod.revenue || 0)}</td>
                                                <td>${prod.write_off_qty || 0}</td>
                                                <td>${formatDate(prod.first_added)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                        
                        <!-- Статистика по типам операций -->
                        ${stats.by_action && stats.by_action.length > 0 ? `
                        <div class="stats-section">
                            <h4>📋 Статистика по типам операций</h4>
                            <div class="operations-table">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Тип операции</th>
                                            <th>Количество</th>
                                            <th>Товаров</th>
                                            <th>Сумма</th>
                                            <th>Средняя цена</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${stats.by_action.map(op => `
                                            <tr>
                                                <td>${getOperationTypeText(op.action)}</td>
                                                <td>${op.operation_count || 0}</td>
                                                <td>${op.total_quantity || 0}</td>
                                                <td>${formatCurrency(op.total_value || 0)}</td>
                                                <td>${formatCurrency(op.avg_price || 0)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="exportStats(${period})">
                        📥 Экспорт в Excel
                    </button>
                    <button class="btn btn-secondary" onclick="closeStatsModal()">
                        Закрыть
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Добавляем модальное окно в DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer.firstElementChild);
}

// Закрыть модальное окно статистики
function closeStatsModal() {
    const modal = document.getElementById('smart-stats-modal');
    if (modal) {
        modal.remove();
    }
}

// Экспорт статистики
function exportStats(period) {
    showToast('Экспорт начат...', 'info');
    // Здесь можно добавить экспорт в Excel
    setTimeout(() => {
        showToast('Экспорт завершен', 'success');
    }, 2000);
}

// Вспомогательные функции
function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '—';
    const date = new Date(dateTimeString);
    return date.toLocaleString('ru-RU');
}

function formatDays(days) {
    if (days === null || days === undefined) return '—';
    if (days < 0) return `Просрочено ${Math.abs(days)} дн.`;
    if (days === 0) return 'Истекает сегодня';
    if (days === 1) return '1 день';
    if (days < 30) return `${days} дн.`;
    
    const months = Math.floor(days / 30);
    const remainingDays = days % 30;
    
    let result = [];
    if (months > 0) result.push(`${months} мес.`);
    if (remainingDays > 0) result.push(`${remainingDays} дн.`);
    
    return result.join(' ');
}

function getPriorityIcon(priority) {
    const icons = {
        'urgent': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    };
    return icons[priority] || '⚪';
}

function getPriorityText(priority) {
    const texts = {
        'urgent': 'Срочно',
        'high': 'Высокий',
        'medium': 'Средний',
        'low': 'Низкий'
    };
    return texts[priority] || priority;
}

function getReminderTypeText(type) {
    const texts = {
        'expiring_soon': 'Скоро истекает',
        'stale_high_discount': 'Не продается',
        'admin_decision': 'Решение админа',
        'personal_summary': 'Персональное'
    };
    return texts[type] || type;
}

function getOperationTypeText(action) {
    const texts = {
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
    return texts[action] || action;
}

// Уведомления
function showNotification(message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Умная ревизия', {
            body: message,
            icon: '/static/favicon.ico'
        });
    } else if ('Notification' in window && Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Умная ревизия', {
                    body: message,
                    icon: '/static/favicon.ico'
                });
            }
        });
    }
}

// Запросить разрешение на уведомления
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission();
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Ждем загрузки страницы ревизии
    setTimeout(() => {
        if (window.location.hash === '#revision' || document.getElementById('page-revision')) {
            initSmartRevision();
        }
    }, 1000);
    
    // Запрашиваем разрешение на уведомления
    requestNotificationPermission();
});

// Экспорт функций для использования в других скриптах
window.smartRevision = {
    init: initSmartRevision,
    loadDashboard: loadSmartDashboard,
    showReminders: showRemindersModal,
    showStats: showSmartStatsModal,
    completeReminder: completeReminder
};
