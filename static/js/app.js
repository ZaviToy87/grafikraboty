// Основной JavaScript для веб-приложения
let currentUser = userData || {
    id: 0,
    role: 'employee',
    full_name: 'Пользователь'
};

let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let selectedDay = null;
let tasks = [];
let schedule = [];
let recurring = [];
let colleagueTasks = [];

/** Тосты вместо alert: msg — текст, type — 'success' | 'error' | 'warning' | '' */
function showToast(msg, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = 'toast' + (type ? ' toast-' + type : '');
    el.textContent = typeof msg === 'string' ? msg : (msg && msg.message) || String(msg);
    container.appendChild(el);
    setTimeout(function() {
        el.style.opacity = '0';
        setTimeout(function() { el.remove(); }, 300);
   }, 3500);
}

/** Подмена alert на тосты (все оставшиеся alert показываются как тост) */
(function() {
    const _alert = window.alert;
    if (_alert) {
        window.alert = function(msg) {
            const s = typeof msg === 'string' ? msg : String(msg);
            const type = (s.indexOf('Ошибка') !== -1 || s.indexOf('ошибка') !== -1 || s.indexOf('Не ') === 0) ? 'error' : '';
            showToast(s, type);
       };
   }
})();

/** Модальное подтверждение: message, onConfirm() вызывается при нажатии «Да» */
function confirmModal(message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const msgEl = document.getElementById('confirm-modal-message');
    const okBtn = document.getElementById('confirm-modal-ok');
    const cancelBtn = document.getElementById('confirm-modal-cancel');
    if (!modal || !msgEl) return;
    msgEl.textContent = message;
    modal.classList.add('active');
    function close() {
        modal.classList.remove('active');
        okBtn.onclick = null;
        cancelBtn.onclick = null;
   }
    okBtn.onclick = function() {
        close();
        if (typeof onConfirm === 'function') onConfirm();
   };
    cancelBtn.onclick = close;
}

/** Состояние загрузки кнопки: btn — элемент, loading — true/false, loadingText — текст при загрузке */
function setButtonLoading(btn, loading, loadingText) {
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.textContent = loadingText || 'Сохранение…';
   } else {
        btn.disabled = false;
        btn.textContent = btn.dataset.originalText || btn.textContent;
   }
}

/** Форматирование даты и времени для отображения (ru-RU) */
function formatDateTimeRu(isoOrDate) {
    if (!isoOrDate) return '—';
    const d = typeof isoOrDate === 'string' ? new Date(isoOrDate) : isoOrDate;
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDateShortRu(isoOrDate) {
    if (!isoOrDate) return '—';
    const d = typeof isoOrDate === 'string' ? new Date(isoOrDate) : isoOrDate;
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

/** Получить иконку для типа файла */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄',
        'xlsx': '📊', 'xls': '📊', 'csv': '📊',
        'doc': '📝', 'docx': '📝', 'txt': '📄', 'rtf': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'webp': '🖼️', 'bmp': '🖼️',
        'mp4': '🎬', 'webm': '🎬', 'avi': '🎬', 'mov': '🎬', 'mkv': '🎬',
        'mp3': '🎵', 'wav': '🎵', 'ogg': '🎵', 'm4a': '🎵', 'flac': '🎵',
        'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
        'ppt': '📊', 'pptx': '📊',
        'json': '⚙️', 'xml': '⚙️', 'html': '🌐', 'css': '🎨'
   };
    return icons[ext] || '📁';
}

/** Форматирование размера файла */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Б';
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
}

/** Обновление даты и времени в шапке: красивая дата + нарисованные часы + цифровое время */
function updateNavDateTime() {
    const now = new Date();
    const dateEl = document.getElementById('nav-date');
    const clockEl = document.getElementById('nav-clock');
    const timeEl = document.getElementById('nav-time');
    if (dateEl) {
        dateEl.textContent = now.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
   }
    if (timeEl) {
        timeEl.textContent = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
   }
    if (clockEl) {
        updateNavClock(clockEl, now);
   }
}

/** Рисует или обновляет SVG-часы в контейнере */
function updateNavClock(container, now) {
    const size = 44;
    const cx = size / 2;
    const cy = size / 2;
    const r = (size / 2) - 2;
    const hour = now.getHours() % 12;
    const minute = now.getMinutes();
    const second = now.getSeconds();
    const secAngle = (second / 60) * 360 - 90;
    const minAngle = (minute / 60) * 360 - 90;
    const hrAngle = (hour + minute / 60) / 12 * 360 - 90;
    const deg = function (angle) { return (angle * Math.PI) / 180; };
    const secLen = r * 0.88;
    const minLen = r * 0.72;
    const hrLen = r * 0.5;
    if (!container._clockSvg) {
        let html = '<svg class="nav-clock-svg" viewBox="0 0 ' + size + ' ' + size + '" width="' + size + '" height="' + size + '">';
        html += '<circle class="nav-clock-face" cx="' + cx + '" cy="' + cy + '" r="' + r + '"/>';
        for (let i = 0; i < 12; i++) {
            const a = (i * 30 - 90) * Math.PI / 180;
            const x1 = cx + (r - 3) * Math.cos(a);
            const y1 = cy + (r - 3) * Math.sin(a);
            const x2 = cx + r * Math.cos(a);
            const y2 = cy + r * Math.sin(a);
            html += '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" class="nav-clock-tick"/>';
       }
        html += '<line class="nav-clock-hand nav-clock-hour" x1="' + cx + '" y1="' + cy + '" x2="' + (cx + hrLen * Math.cos(deg(hrAngle))) + '" y2="' + (cy + hrLen * Math.sin(deg(hrAngle))) + '"/>';
        html += '<line class="nav-clock-hand nav-clock-minute" x1="' + cx + '" y1="' + cy + '" x2="' + (cx + minLen * Math.cos(deg(minAngle))) + '" y2="' + (cy + minLen * Math.sin(deg(minAngle))) + '"/>';
        html += '<line class="nav-clock-hand nav-clock-second" x1="' + cx + '" y1="' + cy + '" x2="' + (cx + secLen * Math.cos(deg(secAngle))) + '" y2="' + (cy + secLen * Math.sin(deg(secAngle))) + '"/>';
        html += '</svg>';
        container.innerHTML = html;
        container._clockSvg = container.querySelector('.nav-clock-svg');
        container._hourLine = container.querySelector('.nav-clock-hour');
        container._minLine = container.querySelector('.nav-clock-minute');
        container._secLine = container.querySelector('.nav-clock-second');
   }
    const x = function (angle, len) { return cx + len * Math.cos(deg(angle)); };
    const y = function (angle, len) { return cy + len * Math.sin(deg(angle)); };
    container._hourLine.setAttribute('x2', x(hrAngle, hrLen));
    container._hourLine.setAttribute('y2', y(hrAngle, hrLen));
    container._minLine.setAttribute('x2', x(minAngle, minLen));
    container._minLine.setAttribute('y2', y(minAngle, minLen));
    container._secLine.setAttribute('x2', x(secAngle, secLen));
    container._secLine.setAttribute('y2', y(secAngle, secLen));
}

// Тема (светлая / тёмная)
// ========================================
// ТЕМНАЯ ТЕМА v3.0 — 3 режима + акцентный цвет
// ========================================

function initTheme() {
    const saved = localStorage.getItem('grafik-theme');
    const accentColor = localStorage.getItem('grafik-accent-color');
    
    // Применяем акцентный цвет
    if (accentColor) {
        document.documentElement.style.setProperty('--primary', accentColor);
        document.documentElement.style.setProperty('--primary-hover', adjustColor(accentColor, -20));
        document.documentElement.style.setProperty('--primary-light', adjustColor(accentColor, 40));
    }
    
    // Применяем режим темы
    if (saved === 'dark') {
        document.documentElement.classList.add('theme-dark');
    } else if (saved === 'auto') {
        // Автоматический режим — следим за системной темой
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        if (prefersDark.matches) {
            document.documentElement.classList.add('theme-dark');
        }
        prefersDark.addEventListener('change', function(e) {
            if (localStorage.getItem('grafik-theme') === 'auto') {
                if (e.matches) {
                    document.documentElement.classList.add('theme-dark');
                } else {
                    document.documentElement.classList.remove('theme-dark');
                }
            }
        });
    }
    
    // Кнопка переключения темы
    const btn = document.getElementById('theme-toggle');
    if (btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            openThemeModal();
        });
    }
}

function openThemeModal() {
    // Удаляем старую модалку если есть
    const oldModal = document.getElementById('theme-modal');
    if (oldModal) oldModal.remove();
    
    const currentTheme = localStorage.getItem('grafik-theme') || 'light';
    const currentAccent = localStorage.getItem('grafik-accent-color') || '#6366f1';
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'theme-modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 450px;">
            <div class="modal-header">
                <h3>🎨 Настройки темы</h3>
                <button type="button" class="modal-close" onclick="this.closest('.modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <div class="theme-options" style="display: flex; gap: 12px; margin-bottom: 24px; justify-content: center;">
                    <div class="theme-option ${currentTheme === 'light' ? 'active' : ''}" 
                         onclick="setThemeMode('light')" 
                         style="cursor: pointer; text-align: center; padding: 12px; border-radius: 12px; border: 2px solid ${currentTheme === 'light' ? 'var(--primary)' : 'var(--border)'}; background: white; color: #333; min-width: 100px;">
                        <div style="font-size: 32px; margin-bottom: 4px;">☀️</div>
                        <div style="font-size: 13px; font-weight: 600;">Светлая</div>
                    </div>
                    <div class="theme-option ${currentTheme === 'dark' ? 'active' : ''}" 
                         onclick="setThemeMode('dark')" 
                         style="cursor: pointer; text-align: center; padding: 12px; border-radius: 12px; border: 2px solid ${currentTheme === 'dark' ? 'var(--primary)' : 'var(--border)'}; background: #1e1e2e; color: #eee; min-width: 100px;">
                        <div style="font-size: 32px; margin-bottom: 4px;">🌙</div>
                        <div style="font-size: 13px; font-weight: 600;">Тёмная</div>
                    </div>
                    <div class="theme-option ${currentTheme === 'auto' ? 'active' : ''}" 
                         onclick="setThemeMode('auto')" 
                         style="cursor: pointer; text-align: center; padding: 12px; border-radius: 12px; border: 2px solid ${currentTheme === 'auto' ? 'var(--primary)' : 'var(--border)'}; background: linear-gradient(135deg, white 50%, #1e1e2e 50%); color: #333; min-width: 100px;">
                        <div style="font-size: 32px; margin-bottom: 4px;">🔄</div>
                        <div style="font-size: 13px; font-weight: 600;">Авто</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <label style="font-weight: 600; display: block; margin-bottom: 8px;">🎯 Акцентный цвет</label>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        ${['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#3b82f6', '#f97316'].map(color => `
                            <div onclick="setAccentColor('${color}')" 
                                 style="width: 36px; height: 36px; border-radius: 50%; background: ${color}; cursor: pointer; border: 3px solid ${currentAccent === color ? 'var(--primary)' : 'transparent'}; transition: transform 0.2s;"
                                 onmouseover="this.style.transform='scale(1.15)'" onmouseout="this.style.transform='scale(1)'"></div>
                        `).join('')}
                        <div style="position: relative; width: 36px; height: 36px;">
                            <input type="color" id="custom-accent-picker" value="${currentAccent}" 
                                   onchange="setAccentColor(this.value)"
                                   style="width: 36px; height: 36px; border-radius: 50%; cursor: pointer; border: none; padding: 0; background: none;">
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Закрыть</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function setThemeMode(mode) {
    localStorage.setItem('grafik-theme', mode);
    
    if (mode === 'dark') {
        document.documentElement.classList.add('theme-dark');
    } else if (mode === 'light') {
        document.documentElement.classList.remove('theme-dark');
    } else if (mode === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        if (prefersDark.matches) {
            document.documentElement.classList.add('theme-dark');
        } else {
            document.documentElement.classList.remove('theme-dark');
        }
    }
    
    // Обновляем модалку
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.querySelectorAll('.theme-option').forEach(el => {
            el.style.borderColor = 'var(--border)';
        });
        const options = modal.querySelectorAll('.theme-option');
        const idx = mode === 'light' ? 0 : mode === 'dark' ? 1 : 2;
        if (options[idx]) options[idx].style.borderColor = 'var(--primary)';
    }
    
    showToast(`Режим: ${mode === 'light' ? 'Светлая' : mode === 'dark' ? 'Тёмная' : 'Авто'}`, 'success');
}

function setAccentColor(color) {
    localStorage.setItem('grafik-accent-color', color);
    document.documentElement.style.setProperty('--primary', color);
    document.documentElement.style.setProperty('--primary-hover', adjustColor(color, -20));
    document.documentElement.style.setProperty('--primary-light', adjustColor(color, 40));
    
    // Обновляем модалку
    const modal = document.getElementById('theme-modal');
    if (modal) {
        modal.querySelectorAll('[onclick*="setAccentColor"]').forEach(el => {
            if (el.tagName === 'DIV') {
                el.style.borderColor = 'transparent';
            }
        });
    }
    
    showToast('Акцентный цвет изменён', 'success');
}

function adjustColor(hex, percent) {
    // Упрощённая версия — осветление/затемнение hex цвета
    hex = hex.replace('#', '');
    const num = parseInt(hex, 16);
    const r = Math.min(255, Math.max(0, (num >> 16) + percent));
    const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + percent));
    const b = Math.min(255, Math.max(0, (num & 0x0000FF) + percent));
    return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
}


// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    updateNavDateTime();
    setInterval(updateNavDateTime, 1000);
    initTheme();
    initNavigation();
    initMobileNav();
    initYearSelect();
    initTaskForm();
    initCalendarFilterAndHotkeys();
    initCalendarClickDelegation();
    const now = new Date();
    const monthSelect = document.getElementById('month-select');
    if (monthSelect) monthSelect.value = String(now.getMonth() + 1);
    loadCalendar();
    loadTasks();
    loadChatTopics();
    loadChat();
    startChatAutoRefresh();  // Авто-обновление для VK темы
    initChatFileInput();
    loadFiles();
    loadReminders();
    initWebSocket();
    
    // Обработчики для фильтров файлов
    initFileFilters();

    setInterval(() => {
        if (document.getElementById('page-calendar').classList.contains('active')) {
            loadCalendar();
       }
        loadReminders();
        if (document.getElementById('page-chat').classList.contains('active')) {
            loadChat();
       }
        if (document.getElementById('page-files').classList.contains('active')) {
            loadFiles(fileCurrentPage);
       }
   }, 5000);
});

// Инициализация фильтров файлов
function initFileFilters() {
    const fileSearch = document.getElementById('file-search');
    const fileDateFilter = document.getElementById('file-date-filter');
    const fileCategory = document.getElementById('file-category');
    
    if (fileSearch) {
        let fileSearchTimeout;
        fileSearch.addEventListener('input', function() {
            clearTimeout(fileSearchTimeout);
            fileSearchTimeout = setTimeout(() => {
                loadFiles(0); // Сброс на первую страницу
           }, 500);
       });
   }
    
    if (fileDateFilter) {
        fileDateFilter.addEventListener('change', function() {
            loadFiles(0);
       });
   }
    
    if (fileCategory) {
        fileCategory.addEventListener('change', function() {
            loadFiles(0);
       });
   }
}

// Навигация
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            showPage(page);
       });
   });
}

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const pageEl = document.getElementById(`page-${pageName}`);
    if (pageEl) pageEl.classList.add('active');
    const navEl = document.querySelector(`[data-page="${pageName}"]`);
    if (navEl) navEl.classList.add('active');
    
    document.getElementById('sidebar').classList.remove('open');
    if (pageName === 'admin' && currentUser.role === 'admin') {
        loadAdminUsers();
        loadAuditLog();
        loadVkSeenUsers();
        initSalarySelectors();
        loadSalarySummary();
        loadAdjustments();
   }
    if (pageName === 'chat') {
        requestNotificationPermission();
        loadChatTopics().then(() => loadChat());
   }
    if (pageName === 'work-journal') {
        initWorkJournalPage();
        loadWorkJournal();
   }
    if (pageName === 'converter') {
        // Страница конвертера ценников загружается через iframe
        // Дополнительно ничего делать не нужно
   }
}

function initMobileNav() {
    const toggle = document.getElementById('nav-toggle');
    const sidebar = document.getElementById('sidebar');
    const closeBtn = document.getElementById('sidebar-close');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
       });
        if (closeBtn) closeBtn.addEventListener('click', function() {
            sidebar.classList.remove('open');
       });
        sidebar.addEventListener('click', function(e) {
            if (e.target.closest('.nav-item')) sidebar.classList.remove('open');
       });
   }
}

/** Загрузка списка пользователей в админ-панели (доступы и права) */
async function showTunnelLink() {
    const btn = document.getElementById('btn-show-tunnel');
    if (btn) { btn.disabled = true; btn.textContent = 'Загрузка…'; }
    try {
        const res = await fetch('/tunnel-info');
        const data = await res.json();
        if (data.status === 'ok') {
            document.getElementById('tunnel-link-url').value = data.tunnel_url || '';
            document.getElementById('tunnel-link-password').value = data.password || '';
            document.getElementById('tunnel-link-modal').classList.add('active');
            if (!data.tunnel_url) showToast('Туннель ещё не запущен или ссылка не сохранена. Запустите программу с туннелем и подождите минуту.', 'warning');
       } else {
            showToast(data.message || 'Ошибка', 'error');
       }
   } catch (e) {
        showToast('Ошибка загрузки', 'error');
   }
    if (btn) { btn.disabled = false; btn.textContent = 'Показать ссылку и пароль'; }
}
function closeTunnelLinkModal() {
    document.getElementById('tunnel-link-modal').classList.remove('active');
}
function copyTunnelLink() {
    const input = document.getElementById('tunnel-link-url');
    const url = input && input.value ? input.value.trim() : '';
    if (!url) { showToast('Нет ссылки для копирования', 'warning'); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function() { showToast('Ссылка скопирована', 'success'); }).catch(function() { fallbackCopy(url); });
   } else {
        fallbackCopy(url);
   }
}
function fallbackCopy(text) {
    try {
        const el = document.createElement('textarea');
        el.value = text;
        el.setAttribute('readonly', '');
        el.style.position = 'absolute'; el.style.left = '-9999px';
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
        showToast('Ссылка скопирована', 'success');
   } catch (e) {
        showToast('Скопируйте ссылку вручную', 'warning');
   }
}

async function loadAdminUsers() {
    const container = document.getElementById('users-list');
    if (!container) return;
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        if (data.status !== 'success' || !Array.isArray(data.users)) {
            container.innerHTML = '<p style="color:#6b7280;">Не удалось загрузить список</p>';
            return;
       }
        container.innerHTML = '';
        data.users.forEach(u => {
            const roleText = (u.role === 'admin') ? 'Администратор' : 'Сотрудник';
            const isSelf = Number(u.id) === Number(currentUser.id);
            const card = document.createElement('div');
            card.className = 'user-card';
            card.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:var(--bg-secondary, #fff); border-radius:8px; margin-bottom:8px; border:1px solid var(--border, #e5e7eb);';
            card.innerHTML = `
                <div>
                    <div style="font-weight:600;">${escapeHtml(u.full_name || u.username || '')}</div>
                    <div style="font-size:12px; color:#6b7280;">${escapeHtml(u.username)} · <strong>${escapeHtml(roleText)}</strong>${isSelf ? ' (вы)' : ''}</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span class="badge" style="background:${u.role === 'admin' ? '#6366f1' : '#4CAF50'}; color:white; padding:4px 10px; border-radius:6px;">${escapeHtml(roleText)}</span>
                    ${!isSelf ? '<button type="button" class="btn btn-secondary btn-sm btn-password-user" data-user-id="' + u.id + '" data-name="' + escapeHtml(u.full_name || u.username) + '">🔑 Пароль</button>' : ''}
                    ${!isSelf ? '<button type="button" class="btn btn-danger btn-sm btn-delete-user" data-user-id="' + u.id + '" data-name="' + escapeHtml(u.full_name || u.username) + '">Удалить</button>' : ''}
                </div>
            `;
            container.appendChild(card);
            const delBtn = card.querySelector('.btn-delete-user');
            if (delBtn) delBtn.addEventListener('click', function() { deleteUser(this.dataset.userId, this.dataset.name); });
            const pwdBtn = card.querySelector('.btn-password-user');
            if (pwdBtn) pwdBtn.addEventListener('click', function() { openPasswordModal(this.dataset.userId, this.dataset.name); });
       });
        if (data.users.length === 0) {
            container.innerHTML = '<p style="color:#6b7280;">Нет пользователей</p>';
       }
   } catch (e) {
        console.error(e);
        container.innerHTML = '<p style="color:#c00;">Ошибка загрузки</p>';
   }
}

/** Журнал действий (audit log) — только админ */
async function loadAuditLog() {
    const container = document.getElementById('audit-log-container');
    if (!container) return;
    try {
        const res = await fetch('/api/audit-log?limit=200');
        const data = await res.json();
        if (data.status !== 'success' || !Array.isArray(data.items)) {
            container.innerHTML = '<p class="text-muted">Нет данных или ошибка.</p>';
            return;
       }
        if (data.items.length === 0) {
            container.innerHTML = '<p class="text-muted">Записей пока нет.</p>';
            return;
       }
        container.innerHTML = '<table><thead><tr><th>Время</th><th>Действие</th><th>Пользователь</th><th>Детали</th><th>IP</th></tr></thead><tbody>' +
            data.items.map(a => {
                const time = (a.created_at || '').replace('T', ' ').slice(0, 19);
                const user = [a.full_name, a.username].filter(Boolean).join(' ') || '—';
                const details = (a.details || '').slice(0, 80);
                const ip = a.ip_address || '—';
                return '<tr><td>' + escapeHtml(time) + '</td><td>' + escapeHtml(a.action || '') + '</td><td>' + escapeHtml(user) + '</td><td>' + escapeHtml(details) + '</td><td>' + escapeHtml(ip) + '</td></tr>';
           }).join('') + '</tbody></table>';
   } catch (e) {
        console.error(e);
        container.innerHTML = '<p style="color:#c00;">Ошибка загрузки журнала</p>';
   }
}

let passwordModalUserId = null;
function openPasswordModal(userId, displayName) {
    passwordModalUserId = userId;
    document.getElementById('password-modal-user-caption').textContent = 'Пользователь: ' + (displayName || userId);
    document.getElementById('password-modal-password').value = '';
    document.getElementById('password-modal').classList.add('active');
}
function closePasswordModal() {
    document.getElementById('password-modal').classList.remove('active');
    passwordModalUserId = null;
}
async function submitPasswordChange() {
    const password = document.getElementById('password-modal-password').value.trim();
    if (!password || password.length < 4) {
        showToast('Пароль не менее 4 символов', 'warning');
        return;
   }
    const btn = document.querySelector('#password-modal .btn-primary');
    setButtonLoading(btn, true, 'Сохранение…');
    try {
        const res = await fetch('/api/users/' + passwordModalUserId + '/password', {
            
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closePasswordModal();
            showToast('Пароль изменён', 'success');
       } else {
            showToast(data.message || 'Ошибка', 'error');
       }
   } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
   } finally {
        setButtonLoading(btn, false);
   }
}

function openAddUserModal() {
    document.getElementById('add-user-username').value = '';
    document.getElementById('add-user-password').value = '';
    document.getElementById('add-user-fullname').value = '';
    document.getElementById('add-user-role').value = 'employee';
    document.getElementById('add-user-modal').classList.add('active');
}

function closeAddUserModal() {
    document.getElementById('add-user-modal').classList.remove('active');
}

function openInstructionModal() {
    document.getElementById('instruction-modal').classList.add('active');
    document.getElementById('sidebar').classList.remove('open');
}
function closeInstructionModal() {
    document.getElementById('instruction-modal').classList.remove('active');
}

/** Подсказки по экрану: тур с подсветкой элементов */
var _tourSteps = [
    { page: 'calendar', selector: '.controls-calendar', title: 'Месяц и год', text: 'Выберите месяц и год, нажмите «Загрузить» — здесь строится календарь на выбранный период.' },
    { page: 'calendar', selector: '#calendar-grid', title: 'Сетка календаря', text: 'Кликните по любому дню — справа откроется панель дня с задачами, файлами и кнопками действий.' },
    { page: 'calendar', selector: '#day-dashboard', title: 'Панель дня', text: 'После клика по дню здесь появятся кнопки «Задачи на день», «График дня: обзор и действия», список задач от коллег и файлов.' },
    { page: 'calendar', selector: '#nav-toggle', title: 'Меню', text: 'Все разделы: Календарь, Задачи (типы смен), Файлы, Чат, Рабочий журнал. Ниже — Инструкция и Выход.' },
    { page: 'tasks', selector: '#page-tasks .page-header', title: 'Раздел «Задачи»', text: 'Типы смен (Утро, Ревизия и т.д.). Администратор может добавлять и менять типы; сотрудники выбирают их в своём дне.' },
    { page: 'files', selector: '#page-files .page-header', title: 'Раздел «Файлы»', text: 'Загрузка фото и документов с привязкой к дате (до 50 МБ). Удобно загружать с телефона.' },
    { page: 'chat', selector: '#page-chat .page-header', title: 'Чат', text: 'Темы создаёт администратор. Сообщения в теме «Telegram» автоматически отправляются в группу Telegram.' },
    { page: 'work-journal', selector: '#page-work-journal .page-header', title: 'Рабочий журнал', text: 'Открытие смены (касса), записи за день, закрытие (безнал, чеки, Z-отчёт). Сотрудник видит только дни, когда он в графике.' },
    { page: 'calendar', selector: '.nav-user', title: 'Шапка', text: 'Инструкция — полный текст и подсказки по экрану. Печать — сохранить календарь в PDF. Тема — светлая/тёмная.' }
];
if (typeof currentUser !== 'undefined' && currentUser && currentUser.role === 'admin') {
    _tourSteps.push({ page: 'admin', selector: '#page-admin .admin-section', title: 'Админ-панель', text: 'Пользователи, статистика, привязка участников Telegram к сотрудникам (чтобы фото из группы попадали в смену).' });
}
_tourSteps.push({ page: 'calendar', selector: '#nav-open-instruction', title: 'Инструкция', text: 'В любой момент можно открыть полную текстовую инструкцию или снова запустить подсказки по экрану.' });

var _tourIndex = 0;
var _tourHighlightClass = 'tour-highlight';

function startGuidedTour() {
    _tourIndex = 0;
    var overlay = document.getElementById('tour-overlay');
    var tooltip = document.getElementById('tour-tooltip');
    if (overlay) {
        overlay.style.display = 'block';
        overlay.onclick = function() { _tourEnd(); };
   }
    if (tooltip) {
        tooltip.style.display = 'none';
        tooltip.onclick = function(e) { e.stopPropagation(); };
   }
    document.getElementById('tour-btn-next').onclick = function(e) { e.stopPropagation(); _tourNext(); };
    document.getElementById('tour-btn-skip').onclick = function(e) { e.stopPropagation(); _tourEnd(); };
    _tourGoToStep(0);
}

function _tourNext() {
    _tourIndex++;
    if (_tourIndex >= _tourSteps.length) {
        _tourEnd();
        return;
   }
    _tourGoToStep(_tourIndex);
}

function _tourEnd() {
    var overlay = document.getElementById('tour-overlay');
    var tooltip = document.getElementById('tour-tooltip');
    document.querySelectorAll('.' + _tourHighlightClass).forEach(function(el) { el.classList.remove(_tourHighlightClass); });
    if (overlay) overlay.style.display = 'none';
    if (tooltip) tooltip.style.display = 'none';
}

function _tourGoToStep(index) {
    var step = _tourSteps[index];
    if (!step) { _tourEnd(); return; }
    document.querySelectorAll('.' + _tourHighlightClass).forEach(function(el) { el.classList.remove(_tourHighlightClass); });
    if (step.page && typeof showPage === 'function') {
        showPage(step.page);
   }
    setTimeout(function() {
        var el = document.querySelector(step.selector);
        var tooltip = document.getElementById('tour-tooltip');
        var overlay = document.getElementById('tour-overlay');
        if (!tooltip) return;
        document.getElementById('tour-tooltip-title').textContent = step.title;
        document.getElementById('tour-tooltip-text').textContent = step.text;
        document.getElementById('tour-btn-next').textContent = index < _tourSteps.length - 1 ? 'Далее' : 'Готово';
        if (el) {
            el.classList.add(_tourHighlightClass);
            el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            tooltip.style.transform = '';
       } else {
            tooltip.style.transform = 'translate(-50%, -50%)';
            tooltip.style.left = '50%';
            tooltip.style.top = '50%';
       }
        tooltip.style.display = 'block';
        setTimeout(function() {
            var rect = el ? el.getBoundingClientRect() : null;
            if (rect) {
                var ttRect = tooltip.getBoundingClientRect();
                var x = rect.left + (rect.width / 2) - (ttRect.width / 2);
                var y = rect.bottom + 12;
                if (y + ttRect.height > window.innerHeight - 20) y = rect.top - ttRect.height - 12;
                if (x < 16) x = 16;
                if (x + ttRect.width > window.innerWidth - 16) x = window.innerWidth - ttRect.width - 16;
                tooltip.style.left = x + 'px';
                tooltip.style.top = y + 'px';
           }
       }, 50);
   }, step.page ? 300 : 0);
}

async function submitAddUser() {
    const username = (document.getElementById('add-user-username').value || '').trim();
    const password = (document.getElementById('add-user-password').value || '').trim();
    const full_name = (document.getElementById('add-user-fullname').value || '').trim();
    const role = document.getElementById('add-user-role').value || 'employee';
    if (!username) { showToast('Введите логин', 'warning'); return; }
    if (!password || password.length < 4) { showToast('Пароль не менее 4 символов', 'warning'); return; }
    try {
        const res = await fetch('/api/users', {
            
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username, password: password, full_name: full_name || username, role: role })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeAddUserModal();
            loadAdminUsers();
            showToast('Пользователь создан', 'success');
       } else {
            showToast(data.message || 'Ошибка создания', 'error');
       }
   } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
   }
}

function deleteUser(userId, displayName) {
    confirmModal('Удалить пользователя «' + displayName + '»? Его записи в графике и задачи будут удалены.', async function() {
        try {
            const res = await fetch('/api/users/' + userId, { method: 'DELETE' });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                loadAdminUsers();
                loadAuditLog();
                showToast('Пользователь удалён', 'success');
           } else {
                showToast(data.message || 'Ошибка удаления', 'error');
           }
       } catch (e) {
            showToast('Ошибка: ' + e.message, 'error');
       }
   });
}

/** Участники VK: список из чата и привязка к пользователям системы */
async function loadVkSeenUsers() {
    const container = document.getElementById('vk-seen-list');
    const btnFetch = document.getElementById('btn-vk-fetch-members');
    if (!container) return;
    try {
        const response = await fetch('/api/vk-chat/vk-seen-users');
        const data = await response.json();
        if (!response.ok || data.status !== 'success') {
            container.innerHTML = '<p style="color:#6b7280;">' + (data.message || 'VK не настроен или нет доступа') + '</p>';
            if (btnFetch) btnFetch.onclick = null;
            return;
       }
        const seen = data.seen || [];
        const users = data.users || [];
        const user_map = data.user_map || {};
        if (seen.length === 0) {
            container.innerHTML = '<p style="color:#6b7280;">Пока никого нет. Нажмите «Загрузить участников из чата VK» — будут подтянуты те, кто писал в чат (последние 100 сообщений).</p>';
       } else {
            let html = '<div class="vk-members-table-wrapper" style="overflow-x:auto;"><table class="vk-members-table" style="width:100%; border-collapse:collapse;"><thead><tr><th style="text-align:left;padding:10px;border-bottom:2px solid #e5e7eb;">VK ID</th><th style="text-align:left;padding:10px;border-bottom:2px solid #e5e7eb;">Имя / username</th><th style="text-align:left;padding:10px;border-bottom:2px solid #e5e7eb;">Был в чате</th><th style="text-align:left;padding:10px;border-bottom:2px solid #e5e7eb;">Привязать к пользователю</th><th style="text-align:left;padding:10px;border-bottom:2px solid #e5e7eb;"></th></tr></thead><tbody>';
            seen.forEach(s => {
                const name = [s.first_name, s.last_name].filter(Boolean).join(' ') || s.username || '—';
                const mapped_to = s.mapped_to != null ? String(s.mapped_to) : '';
                let selectOpts = '<option value="">— Не привязан</option>';
                users.forEach(u => {
                    const uid = String(u.id);
                    const uname = escapeHtml(u.full_name || u.username || uid);
                    selectOpts += '<option value="' + escapeHtml(uid) + '"' + (uid === mapped_to ? ' selected' : '') + '>' + uname + '</option>';
               });
                html += '<tr data-vk-id="' + escapeHtml(s.vk_id) + '" style="border-bottom:1px solid #f0f0f0;">' +
                    '<td style="padding:10px;"><code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;">' + escapeHtml(s.vk_id) + '</code></td>' +
                    '<td style="padding:10px;">' + escapeHtml(name) + (s.username ? ' <span style="color:#6b7280;">@' + escapeHtml(s.username) + '</span>' : '') + '</td>' +
                    '<td style="padding:10px;font-size:12px;color:#6b7280;">' + (s.last_seen ? s.last_seen.slice(0, 16).replace('T', ' ') : '—') + '</td>' +
                    '<td style="padding:10px;"><select class="form-control vk-map-select" style="min-width:180px;">' + selectOpts + '</select></td>' +
                    '<td style="padding:10px;"><button type="button" class="btn btn-primary btn-sm vk-save-btn" style="padding:6px 12px;">Сохранить</button></td></tr>';
           });
            html += '</tbody></table></div>';
            container.innerHTML = html;
            container.querySelectorAll('.vk-save-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const row = this.closest('tr');
                    const vkId = row.dataset.vkId;
                    const select = row.querySelector('.vk-map-select');
                    const userId = select.value ? parseInt(select.value, 10) : null;
                    try {
                        const res = await fetch('/api/vk-chat/vk-user-map', { 
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ vk_id: vkId, user_id: userId })
                       });
                        const d = await res.json().catch(() => ({}));
                        if (res.ok && d.status === 'success') {
                            loadVkSeenUsers();
                            showToast('Привязка сохранена', 'success');
                       } else {
                            showToast(d.message || 'Ошибка сохранения', 'warning');
                       }
                   } catch (e) {
                        showToast('Ошибка: ' + e.message, 'danger');
                   }
               });
           });
       }
        if (btnFetch) {
            btnFetch.onclick = async function() {
                btnFetch.disabled = true;
                btnFetch.textContent = 'Загрузка...';
                try {
                    // Вызываем новый endpoint для загрузки участников
                    const res = await fetch('/api/vk-chat/vk-load-members', { 
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }, 
                   });
                    const d = await res.json().catch(() => ({}));
                    if (res.ok && d.status === 'success') {
                        // После загрузки обновляем список
                        loadVkSeenUsers();
                        showToast(d.message || 'Участники загружены', 'success');
                   } else {
                        showToast(d.message || 'Ошибка', 'warning');
                   }
               } catch (e) {
                    showToast('Ошибка: ' + e.message, 'danger');
               } finally {
                    btnFetch.disabled = false;
                    btnFetch.textContent = '🔄 Загрузить участников из чата VK';
               }
           };
       }
   } catch (e) {
        console.error(e);
        container.innerHTML = '<p style="color:#c00;">Ошибка загрузки: ' + escapeHtml(e.message) + '</p>';
   }
}

// Фильтр по сотруднику (админ), горячие клавиши, переход к дате
function initCalendarFilterAndHotkeys() {
    const filterEl = document.getElementById('filter-user-select');
    if (filterEl && currentUser.role === 'admin') {
        fetch('/api/users', { credentials: 'include' }).then(r => r.json()).then(data => {
            if (data.status !== 'success' || !data.users) return;
            data.users.filter(u => u.role === 'employee').forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = u.full_name || u.username;
                filterEl.appendChild(opt);
            });
            filterEl.addEventListener('change', () => loadCalendar());
        });
    }
    document.addEventListener('keydown', function(e) {
        if (!document.getElementById('page-calendar')?.classList.contains('active')) return;
        const tag = (e.target?.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        if (e.key === 'n' || e.key === 'н') { e.preventDefault(); nextMonth(); }
        else if (e.key === 'p' || e.key === 'з') { e.preventDefault(); prevMonth(); }
        else if (e.key === 't' || e.key === 'е') { e.preventDefault(); goToToday(); }
        else if (e.key === 'Enter' && selectedDay != null) { e.preventDefault(); openDayMenuModal(selectedDay); }
   });
}

function nextMonth() {
    const monthEl = document.getElementById('month-select');
    const yearEl = document.getElementById('year-select');
    if (!monthEl || !yearEl) return;
    let m = parseInt(monthEl.value, 10) || 1;
    let y = parseInt(yearEl.value, 10) || new Date().getFullYear();
    if (m >= 12) { m = 1; y++; } else m++;
    monthEl.value = String(m);
    yearEl.value = String(y);
    loadCalendar();
}

function prevMonth() {
    const monthEl = document.getElementById('month-select');
    const yearEl = document.getElementById('year-select');
    if (!monthEl || !yearEl) return;
    let m = parseInt(monthEl.value, 10) || 1;
    let y = parseInt(yearEl.value, 10) || new Date().getFullYear();
    if (m <= 1) { m = 12; y--; } else m--;
    monthEl.value = String(m);
    yearEl.value = String(y);
    loadCalendar();
}

function goToToday() {
    const now = new Date();
    const monthEl = document.getElementById('month-select');
    const yearEl = document.getElementById('year-select');
    if (monthEl) monthEl.value = String(now.getMonth() + 1);
    if (yearEl) yearEl.value = String(now.getFullYear());
    loadCalendar().then(() => { selectDayAndShowDashboard(now.getDate()); });
}

async function sendWeeklyDigest() {
    try {
        const r = await fetch('/api/weekly-digest');
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.status === 'success') alert('Дайджест отправлен в Telegram');
        else alert(d.message || 'Ошибка');
   } catch (e) { alert('Ошибка: ' + e.message); }
}

function goToDate() {
    const dayEl = document.getElementById('go-to-day');
    const day = dayEl ? parseInt(dayEl.value, 10) : 0;
    if (!day || day < 1 || day > 31) { alert('Введите день от 1 до 31'); return; }
    const monthEl = document.getElementById('month-select');
    const yearEl = document.getElementById('year-select');
    currentYear = parseInt(yearEl?.value, 10) || new Date().getFullYear();
    currentMonth = parseInt(monthEl?.value, 10) || new Date().getMonth() + 1;
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    if (day > daysInMonth) { alert(`В этом месяце только ${daysInMonth} дней`); return; }
    loadCalendar().then(() => selectDayAndShowDashboard(day));
}

// Инициализация года и авто-загрузка при смене месяца/года (в т.ч. на мобильной)
function initYearSelect() {
    const yearSelect = document.getElementById('year-select');
    const monthSelect = document.getElementById('month-select');
    const currentYear = new Date().getFullYear();
    if (yearSelect) {
        for (let year = currentYear - 2; year <= currentYear + 2; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            if (year === currentYear) option.selected = true;
            yearSelect.appendChild(option);
       }
        yearSelect.addEventListener('change', function() { loadCalendar(); });
   }
    if (monthSelect) {
        monthSelect.addEventListener('change', function() { loadCalendar(); });
   }
}

/** Делегирование клика по сетке календаря: клик по ячейке дня открывает панель дня */
function initCalendarClickDelegation() {
    const grid = document.getElementById('calendar-grid');
    if (!grid) return;
    function handleDayClick(e) {
        const cell = e.target.closest('.calendar-day');
        if (!cell) return;
        const dayStr = cell.getAttribute('data-day');
        if (dayStr) {
            const day = parseInt(dayStr, 10);
            if (day >= 1 && day <= 31) selectDayAndShowDashboard(day);
       }
   }
    grid.addEventListener('click', handleDayClick, true);
}

// Загрузка календаря
async function loadCalendar() {
    const yearEl = document.getElementById('year-select');
    const monthEl = document.getElementById('month-select');
    const filterEl = document.getElementById('filter-user-select');
    if (!yearEl || !monthEl) return;
    currentYear = parseInt(yearEl.value, 10) || new Date().getFullYear();
    currentMonth = parseInt(monthEl.value, 10) || new Date().getMonth() + 1;
    let url = `/api/schedule?year=${currentYear}&month=${currentMonth}&user_id=${currentUser.id}`;
    if (filterEl && filterEl.value) url += `&filter_user_id=${encodeURIComponent(filterEl.value)}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            schedule = Array.isArray(data.schedule) ? data.schedule : [];
            recurring = Array.isArray(data.recurring) ? data.recurring : [];
            await loadColleagueTasks();
       } else {
            schedule = [];
            recurring = [];
       }
        // Всегда рисуем сетку дней, иначе клики по дням не работают
        renderCalendar();
        renderCalendarLegend();
        renderCalendarStats();
        renderWeekProgress();
   } catch (error) {
        console.error('Ошибка загрузки календаря:', error);
        schedule = [];
        recurring = [];
        renderCalendar();
        renderCalendarLegend();
        renderCalendarStats();
        renderWeekProgress();
   }
}

function renderCalendarLegend() {
    const wrap = document.getElementById('calendar-legend');
    if (!wrap) return;
    if (!tasks.length) { wrap.style.display = 'none'; return; }
    wrap.innerHTML = '';
    wrap.style.display = 'flex';
    wrap.style.flexWrap = 'wrap';
    wrap.style.gap = '8px';
    wrap.style.marginTop = '8px';
    tasks.slice(0, 12).forEach(t => {
        const span = document.createElement('span');
        span.className = 'legend-item';
        span.style.cssText = `display:inline-flex;align-items:center;gap:4px;font-size:12px;`;
        span.innerHTML = `<span style="width:10px;height:10px;border-radius:2px;background:${t.color || '#999'}"></span> ${escapeHtml((t.name || '').substring(0, 18))}`;
        wrap.appendChild(span);
   });
}

function renderCalendarStats() {
    const wrap = document.getElementById('calendar-stats');
    if (!wrap) return;
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const daysWithSchedule = new Set(schedule.map(s => Number(s.day))).size;
    wrap.innerHTML = `<span>Дней с записями: ${daysWithSchedule} из ${daysInMonth}</span><span id="calendar-stats-files">Файлов за месяц: —</span>`;
    wrap.style.display = 'flex';
    wrap.style.gap = '16px';
    wrap.style.marginTop = '6px';
    wrap.style.fontSize = '13px';
    wrap.style.color = 'var(--text-secondary)';
    fetch('/api/files', { credentials: 'include' }).then(r => r.json()).then(data => {
        const filesCount = (data.status === 'success' && Array.isArray(data.files))
            ? data.files.filter(f => Number(f.month) === currentMonth && Number(f.year) === currentYear).length
            : 0;
        const el = document.getElementById('calendar-stats-files');
        if (el) el.textContent = 'Файлов за месяц: ' + filesCount;
    }).catch(() => {});
}

function renderWeekProgress() {
    const wrap = document.getElementById('calendar-week-progress');
    if (!wrap) return;
    const today = new Date();
    const currentDay = today.getDate();
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const weekStart = currentDay - (today.getDay() || 7) + 1;
    const weekEnd = Math.min(weekStart + 6, daysInMonth);
    const weekDays = Math.max(0, weekEnd - weekStart + 1);
    let filled = 0;
    for (let d = weekStart; d <= weekEnd; d++) {
        if (d >= 1 && schedule.some(s => Number(s.day) === d)) filled++;
   }
    const pct = weekDays ? Math.round((filled / weekDays) * 100) : 0;
    wrap.innerHTML = `Неделя заполнена на ${pct}%`;
    wrap.style.display = 'block';
}

// Отрисовка календаря
function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    if (!grid) return;
    grid.innerHTML = '';
    
    // Заголовки дней недели
    const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    weekdays.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        header.style.fontWeight = 'bold';
        header.style.textAlign = 'center';
        header.style.padding = '10px';
        grid.appendChild(header);
   });
    
    // Получаем первый день месяца
    const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();
    const adjustedFirstDay = firstDay === 0 ? 6 : firstDay - 1; // Понедельник = 0
    
    // Пустые ячейки до первого дня
    for (let i = 0; i < adjustedFirstDay; i++) {
        const empty = document.createElement('div');
        grid.appendChild(empty);
   }
    
    // Дни месяца
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const today = new Date();
    
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.setAttribute('data-day', String(day));
        dayElement.style.cursor = 'pointer';
        
        const isToday = today.getDate() === day && 
                       today.getMonth() + 1 === currentMonth && 
                       today.getFullYear() === currentYear;
        
        if (isToday) dayElement.classList.add('today');
        
        const dayOfWeek = new Date(currentYear, currentMonth - 1, day).getDay();
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            dayElement.classList.add('weekend');
       }
        
        dayElement.innerHTML = `
            <div class="day-number">${day}</div>
            <div class="day-tasks" id="tasks-${day}"></div>
        `;
        
        // Левая кнопка — показываем панель дня справа (задачи, коллеги, файлы); меню «Действия» — по кнопке в панели
        dayElement.addEventListener('click', () => selectDayAndShowDashboard(day));
        
        // Правая кнопка - контекстное меню (только для админов)
        if (currentUser.role === 'admin') {
            dayElement.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                openQuickAssignMenu(day, e);
           });
       }
        
        const taskContainer = dayElement.querySelector('.day-tasks');
        // Обязательные повторяющиеся (Протирка полок сб/вс, Ревизия 1/16, Ценники и Сроки 2/17)
        const recForDay = recurring.filter(r => Number(r.day) === day);
        recForDay.forEach(rec => {
            (rec.tasks || []).forEach(t => {
                const row = document.createElement('div');
                row.className = 'day-schedule-row';
                row.style.marginBottom = '2px';
                const badge = document.createElement('span');
                badge.className = 'task-badge';
                badge.style.cssText = 'display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 2px; background-color: ' + (t.color || '#B39DDB') + ';';
                badge.title = (t.name || '') + ' (обяз.)';
                const nameSpan = document.createElement('span');
                nameSpan.style.cssText = 'font-size: 9px; color: #555;';
                nameSpan.textContent = (t.name || '').substring(0, 8) + ' (обяз.)';
                row.appendChild(badge);
                row.appendChild(nameSpan);
                taskContainer.appendChild(row);
           });
       });
        // За день может быть несколько записей (админ — все сотрудники, сотрудник — одна)
        const dayEntries = schedule.filter(s => Number(s.day) === day);
        dayEntries.forEach(daySchedule => {
            try {
                const raw = daySchedule.task_ids;
                const taskIds = Array.isArray(raw) ? raw : JSON.parse(typeof raw === 'string' ? raw : '[]');
                const row = document.createElement('div');
                row.className = 'day-schedule-row';
                row.style.marginBottom = '2px';
                const fullName = (daySchedule.full_name || '').trim() || '—';
                const nameSpan = document.createElement('span');
                nameSpan.className = 'day-schedule-name';
                nameSpan.title = fullName;
                nameSpan.setAttribute('data-full-name', fullName);
                nameSpan.textContent = shortNameForCell(fullName);
                nameSpan.style.cssText = 'font-size: 10px; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 1px;';
                row.appendChild(nameSpan);
                const badgesWrap = document.createElement('div');
                badgesWrap.className = 'day-schedule-badges';
                (taskIds || []).forEach(taskId => {
                    const numId = Number(taskId);
                    const task = tasks.find(t => Number(t.id) === numId);
                    if (task) {
                        const badge = document.createElement('span');
                        badge.className = 'task-badge';
                        badge.style.cssText = 'display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 2px; background-color: ' + (task.color || '#3498db') + ';';
                        badge.title = task.name || '';
                        badgesWrap.appendChild(badge);
                   }
               });
                row.appendChild(badgesWrap);
                taskContainer.appendChild(row);
           } catch (e) {
                console.error('Ошибка парсинга задач дня:', e);
           }
       });
        // Задачи коллегам (кому я поставил / мне поставили)
        const dayColleagueTasks = colleagueTasks.filter(ct =>
            Number(ct.day) === day && (Number(ct.assignee_id) === Number(currentUser.id) || Number(ct.created_by) === Number(currentUser.id))
        );
        dayColleagueTasks.forEach(ct => {
            const row = document.createElement('div');
            row.className = 'day-schedule-row colleague-task-row';
            row.style.marginBottom = '2px';
            const badge = document.createElement('span');
            badge.className = 'task-badge';
            badge.style.cssText = 'display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 4px; background-color: ' + (ct.color || '#3498db') + ';';
            badge.title = (ct.title || '') + (ct.completed ? ' ✓ Выполнено' : '');
            const nameSpan = document.createElement('span');
            nameSpan.style.cssText = 'font-size: 9px; color: #555;';
            nameSpan.textContent = (Number(ct.assignee_id) === Number(currentUser.id) ? 'Мне: ' : '') + (ct.title || '').substring(0, 12) + (ct.completed ? ' ✓' : '');
            nameSpan.title = ct.title + (ct.assignee_name ? ' → ' + ct.assignee_name : '') + (ct.completed ? ' (выполнено)' : '');
            row.appendChild(badge);
            row.appendChild(nameSpan);
            taskContainer.appendChild(row);
       });
        
        grid.appendChild(dayElement);
   }
}

// Напоминания: сегодня (задачи на день) + что предстоит в ближайшие дни — блок всегда сверху
async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const data = await response.json();
        const banner = document.getElementById('reminders-banner');
        if (!banner) return;
        const hasToday = data.status === 'success' && data.today_summary != null;
        const reminders = Array.isArray(data.reminders) ? data.reminders : [];
        if (!hasToday && reminders.length === 0) {
            banner.style.display = 'none';
            banner.innerHTML = '';
            return;
       }
        let html = '';
        if (hasToday) {
            const dateStr = data.today_date ? escapeHtml(data.today_date) : '';
            html += '<strong>📅 Сегодня' + (dateStr ? ' (' + dateStr + ')' : '') + ':</strong> ' + escapeHtml(data.today_summary);
            if (reminders.length) html += '<br><br><strong>🔔 На ближайшие дни:</strong><br>';
       }
        if (reminders.length) {
            if (!hasToday) html += '<strong>🔔 Напоминание: что предстоит</strong><br>';
            html += reminders.map(r => escapeHtml(r.message)).join('<br>');
       }
        banner.innerHTML = html;
        banner.style.display = 'block';
   } catch (e) {
        console.error('Ошибка загрузки напоминаний:', e);
        const banner = document.getElementById('reminders-banner');
        if (banner) banner.style.display = 'none';
   }
}

// Загрузка задач
async function loadTasks() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        if (data.status === 'success') {
            tasks = data.tasks;
            renderTasks();
       }
   } catch (error) {
        console.error('Ошибка загрузки задач:', error);
   }
}

let editingTaskId = null;

/** Короткое имя для ячейки календаря (мобильная версия): первое слово, до 10 символов, полное имя — в title */
function shortNameForCell(fullName) {
    if (!fullName || fullName === '—') return '—';
    const first = fullName.trim().split(/\s+/)[0] || fullName;
    if (first.length <= 10) return first;
    return first.slice(0, 8) + '…';
}

function renderTasks() {
    const container = document.getElementById('tasks-list');
    const btnAdd = document.getElementById('btn-add-task');
    if (btnAdd) btnAdd.style.display = currentUser.role === 'admin' ? '' : 'none';
    container.innerHTML = '';

    if (tasks.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'tasks-empty';
        empty.textContent = 'Пока нет задач. Добавьте задачу (кнопка выше) — она появится в календаре при назначении на день.';
        container.appendChild(empty);
        return;
   }

    tasks.forEach(task => {
        const item = document.createElement('div');
        item.className = 'task-item task-item-row';
        const color = (task.color || '#3498db').replace(/"/g, '');
        item.innerHTML = `
            <div class="task-item-color" style="background-color: ${color}" title="Цвет"></div>
            <div class="task-item-name">${escapeHtml(task.name || '—')}</div>
            ${currentUser.role === 'admin' ? `
                <button type="button" class="btn btn-sm btn-edit-task" onclick="openEditTaskModal(${task.id})" title="Изменить">✎</button>
                <button type="button" class="btn btn-sm btn-delete-task" onclick="deleteTask(${task.id})" title="Удалить">✕</button>
            ` : ''}
        `;
        container.appendChild(item);
   });
}

function initTaskForm() {
    const colorPick = document.getElementById('task-form-color');
    const hexInput = document.getElementById('task-form-color-hex');
    const nameInput = document.getElementById('task-form-name');
    if (colorPick && hexInput) {
        colorPick.addEventListener('input', function() { hexInput.value = this.value; });
        hexInput.addEventListener('input', function() {
            let v = this.value.replace(/^#?/, '#');
            if (/^#[0-9A-Fa-f]{6}$/.test(v)) colorPick.value = v;
       });
   }
    if (nameInput) {
        nameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); saveTaskFromModal(); }
       });
   }
}

function openTaskModal() {
    if (currentUser.role !== 'admin') return;
    editingTaskId = null;
    document.getElementById('task-form-title').textContent = 'Добавить задачу';
    document.getElementById('task-form-name').value = '';
    document.getElementById('task-form-color').value = '#3498db';
    document.getElementById('task-form-color-hex').value = '#3498db';
    document.getElementById('task-form-modal').classList.add('active');
    document.getElementById('task-form-name').focus();
}

function openEditTaskModal(taskId) {
    if (currentUser.role !== 'admin') return;
    const task = tasks.find(t => Number(t.id) === Number(taskId));
    if (!task) return;
    editingTaskId = taskId;
    document.getElementById('task-form-title').textContent = 'Редактировать задачу';
    document.getElementById('task-form-name').value = task.name || '';
    const color = task.color || '#3498db';
    document.getElementById('task-form-color').value = color;
    document.getElementById('task-form-color-hex').value = color;
    document.getElementById('task-form-modal').classList.add('active');
    document.getElementById('task-form-name').focus();
}

function closeTaskModal() {
    document.getElementById('task-form-modal').classList.remove('active');
    editingTaskId = null;
}

async function saveTaskFromModal() {
    const nameEl = document.getElementById('task-form-name');
    const colorEl = document.getElementById('task-form-color');
    const name = (nameEl && nameEl.value || '').trim();
    const color = (colorEl && colorEl.value) || '#3498db';
    if (!name) {
        alert('Введите название задачи');
        return;
   }

    const saveBtn = document.getElementById('task-form-save');
    if (saveBtn) saveBtn.disabled = true;

    try {
        if (editingTaskId != null) {
            const res = await fetch('/api/tasks/' + editingTaskId, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, color: color })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                closeTaskModal();
                await loadTasks();
            } else {
                alert('Ошибка: ' + (data.message || res.status));
            }
        } else {
            const res = await fetch('/api/tasks/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, color: color })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                closeTaskModal();
                await loadTasks();
            } else {
                alert('Ошибка: ' + (data.message || res.status));
            }
        }
    } finally {
        if (saveBtn) saveBtn.disabled = false;
    }
}

async function deleteTask(taskId) {
    if (currentUser.role !== 'admin') return;
    const task = tasks.find(t => Number(t.id) === Number(taskId));
    const taskName = task ? (task.name || '') : '';
    if (!confirm('Удалить задачу «' + taskName + '»? Она пропадёт из списка (в календаре старые записи могут отображаться без названия).')) return;
    try {
        const res = await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            await loadTasks();
       } else {
            alert('Ошибка: ' + (data.message || res.status));
       }
   } catch (e) {
        alert('Ошибка удаления');
   }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---------- Выбор дня: только панель справа (постоянная). Окно редактирования — по кнопке «Задачи на день» ----------
function selectDayAndShowDashboard(day) {
    selectedDay = day;
    updateDayDashboard(day);
}

async function updateDayDashboard(day) {
    const placeholder = document.getElementById('day-dashboard-placeholder');
    const content = document.getElementById('day-dashboard-content');
    const titleEl = document.getElementById('day-dashboard-title');
    const tasksEl = document.getElementById('day-dashboard-tasks');
    const colleagueEl = document.getElementById('day-dashboard-colleague');
    const filesEl = document.getElementById('day-dashboard-files');
    const actionsBtn = document.getElementById('day-dashboard-actions-btn');
    if (!content || !placeholder) {
        console.warn('Панель дня не найдена (day-dashboard-placeholder/content). Обновите страницу или проверьте, что запускаете из папки проекта.');
        return;
   }

    placeholder.style.display = 'none';
    content.style.display = 'block';
    var aside = document.getElementById('day-dashboard');
    if (aside) aside.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    if (titleEl) titleEl.textContent = `День ${day}.${currentMonth}.${currentYear}`;

    const editBtn = document.getElementById('day-dashboard-edit-btn');
    if (editBtn) {
        editBtn.onclick = () => openDayModal(day);
   }
    if (actionsBtn) {
        actionsBtn.onclick = () => openDayMenuModal(day);
   }
    const copyBtn = document.getElementById('day-dashboard-copy-btn');
    if (copyBtn) {
        copyBtn.onclick = () => openCopyDayModal(day);
   }

    // Задачи на день (график)
    const daySchedule = schedule.filter(s => Number(s.day) === day);
    const isAdmin = currentUser && currentUser.role === 'admin';
    if (tasksEl) {
        tasksEl.innerHTML = '';
        if (daySchedule.length === 0) {
            tasksEl.innerHTML = '<div class="day-dashboard-empty">Нет записей на этот день</div>';
       } else {
            daySchedule.forEach(s => {
                if (!isAdmin && Number(s.user_id) !== Number(currentUser.id)) return;
                const name = (s.full_name || s.username || '—').trim();
                let taskNames = [];
                try {
                    const raw = s.task_ids;
                    const ids = Array.isArray(raw) ? raw : JSON.parse(typeof raw === 'string' ? raw : '[]');
                    taskNames = (ids || []).map(tid => {
                        const t = tasks.find(x => Number(x.id) === Number(tid));
                        return t ? (t.name || '') : String(tid);
                   });
               } catch (e) { taskNames = []; }
                const row = document.createElement('div');
                row.className = 'day-dashboard-task-row';
                row.innerHTML = `<strong>${escapeHtml(name)}</strong>: ${escapeHtml(taskNames.length ? taskNames.join(', ') : '(нет задач)')}`;
                if (s.notes) row.innerHTML += `<br><span class="day-dashboard-empty">${escapeHtml(String(s.notes))}</span>`;
                tasksEl.appendChild(row);
           });
       }
   }

    // Задачи от коллег / мне
    const dayCT = colleagueTasks.filter(ct =>
        Number(ct.day) === day && Number(ct.month) === currentMonth && Number(ct.year) === currentYear
    );
    if (colleagueEl) {
        colleagueEl.innerHTML = '';
        if (dayCT.length === 0) {
            colleagueEl.innerHTML = '<div class="day-dashboard-empty">Нет задач от коллег на этот день</div>';
       } else {
            dayCT.forEach(ct => {
                const row = document.createElement('div');
                row.className = 'day-dashboard-colleague-row';
                const toMe = Number(ct.assignee_id) === Number(currentUser.id);
                const isCreator = Number(ct.created_by) === Number(currentUser.id);
                const title = (ct.title || '').trim() || '—';
                const fromName = (ct.created_by_name || ct.creator_name || '').trim() || '—';
                const toName = (ct.assignee_name || '').trim() || '—';
                let html = `${toMe ? 'Мне: ' : 'Кому: ' + escapeHtml(toName) + ' — '}${escapeHtml(title)}${ct.completed ? ' ✓' : ''} (от ${escapeHtml(fromName)})`;
                if (ct.due_date) html += ` <span class="day-dashboard-empty">до ${escapeHtml(ct.due_date)}</span>`;
                if (ct.thanks_count > 0) html += ` 🙏 ${ct.thanks_count}`;
                row.innerHTML = html;
                if (ct.completed && isCreator && Number(ct.assignee_id) !== Number(currentUser.id)) {
                    const thanksBtn = document.createElement('button');
                    thanksBtn.type = 'button';
                    thanksBtn.className = 'btn btn-sm btn-secondary';
                    thanksBtn.textContent = 'Спасибо';
                    thanksBtn.style.marginLeft = '8px';
                    thanksBtn.onclick = async () => {
                        const r = await fetch(`/api/colleague-tasks/${ct.id}/thanks`, { method: 'POST' });
                        if (r.ok) updateDayDashboard(day);
                   };
                    row.appendChild(thanksBtn);
               }
                const tgBtn = document.createElement('button');
                tgBtn.type = 'button';
                tgBtn.className = 'btn btn-sm btn-secondary';
                tgBtn.textContent = '📤 В Telegram';
                tgBtn.style.marginLeft = '8px';
                tgBtn.onclick = async () => {
                    tgBtn.disabled = true;
                    try {
                        const r = await fetch(`/api/colleague-tasks/${ct.id}/send-telegram`, { method: 'POST' });
                        const d = await r.json().catch(() => ({}));
                        if (r.ok && d.status === 'success') {
                            tgBtn.textContent = '✓ Отправлено';
                       } else {
                            alert(d.message || 'Не удалось отправить');
                            tgBtn.disabled = false;
                       }
                   } catch (e) {
                        alert('Ошибка отправки');
                        tgBtn.disabled = false;
                   }
               };
                row.appendChild(tgBtn);
                colleagueEl.appendChild(row);
           });
       }
   }

    // Файлы на этот день
    try {
        const allFiles = await loadFilesList();
        const dayFiles = allFiles.filter(f =>
            Number(f.day) === day && Number(f.month) === currentMonth && Number(f.year) === currentYear
        );
        if (filesEl) {
            filesEl.innerHTML = '';
            if (dayFiles.length === 0) {
                filesEl.innerHTML = '<div class="day-dashboard-empty">Нет файлов на этот день</div>';
           } else {
                dayFiles.forEach(f => {
                    const row = document.createElement('div');
                    row.className = 'day-dashboard-file-row';
                    const name = (f.filename || '').toString() || '—';
                    row.innerHTML = `<a href="/api/files/${f.id}" target="_blank" rel="noopener">${escapeHtml(name)}</a>`;
                    filesEl.appendChild(row);
               });
           }
       }
   } catch (e) {
        if (filesEl) filesEl.innerHTML = '<div class="day-dashboard-empty">Не удалось загрузить файлы</div>';
   }
}

// ---------- График дня: обзор (кто в смене, задачи коллегам, файлы) и действия ----------
async function openDayMenuModal(day) {
    if (day == null) return;
    selectedDay = day;
    const titleEl = document.getElementById('day-menu-title');
    if (titleEl) titleEl.textContent = `День ${day}.${currentMonth}.${currentYear}`;
    const summaryEl = document.getElementById('day-menu-summary');
    if (summaryEl) {
        try {
            const sched = Array.isArray(schedule) ? schedule : [];
            const daySchedule = sched.filter(s => Number(s.day) === day && Number(s.month) === currentMonth && Number(s.year) === currentYear);
            const ctList = Array.isArray(colleagueTasks) ? colleagueTasks : [];
            const dayCT = ctList.filter(ct =>
                Number(ct.day) === day && Number(ct.month) === currentMonth && Number(ct.year) === currentYear
            );
            let dayFiles = [];
            try {
                const allFiles = await loadFilesList();
                dayFiles = Array.isArray(allFiles) ? allFiles.filter(f =>
                    Number(f.day) === day && Number(f.month) === currentMonth && Number(f.year) === currentYear
                ) : [];
           } catch (e) {}
            const who = daySchedule.map(s => (s.full_name || '—').trim()).filter(Boolean);
            const whoStr = who.length ? who.join(', ') : 'никого нет';
            let ctLines = dayCT.map(ct => {
                const from = (ct.created_by_name || '—').trim();
                const to = (ct.assignee_name || '—').trim();
                const title = String(ct.title || '—').substring(0, 30);
                return `${from} → ${to}: ${title}`;
           });
            if (ctLines.length > 5) ctLines = ctLines.slice(0, 5).concat(['… ещё ' + (dayCT.length - 5)]);
            const fileNames = dayFiles.map(f => String(f.filename || '—')).slice(0, 5);
            if (dayFiles.length > 5) fileNames.push('… ещё ' + (dayFiles.length - 5));
            summaryEl.innerHTML = [
                '<p><strong>👥 В графике:</strong> ' + escapeHtml(whoStr) + '</p>',
                dayCT.length ? '<p><strong>🤝 Задачи коллегам:</strong><br>' + ctLines.map(l => escapeHtml(l)).join('<br>') + '</p>' : '<p><strong>🤝 Задачи коллегам:</strong> нет</p>',
                '<p><strong>📎 Файлы:</strong> ' + (fileNames.length ? fileNames.map(escapeHtml).join(', ') : 'нет') + '</p>'
            ].join('');
       } catch (e) {
            console.error('openDayMenuModal summary:', e);
            summaryEl.innerHTML = '<p>Обзор загружается...</p>';
       }
   }
    const modal = document.getElementById('day-menu-modal');
    if (modal) modal.classList.add('active');
}

function closeDayMenuModal() {
    const modal = document.getElementById('day-menu-modal');
    if (modal) modal.classList.remove('active');
    selectedDay = null;
}

function openCopyDayModal(targetDay) {
    const targetEl = document.getElementById('copy-day-target');
    if (targetEl) targetEl.textContent = `${targetDay}.${currentMonth}.${currentYear}`;
    const sourceEl = document.getElementById('copy-day-source');
    if (sourceEl) { sourceEl.value = ''; sourceEl.focus(); }
    document.getElementById('copy-day-modal').classList.add('active');
}

function closeCopyDayModal() {
    document.getElementById('copy-day-modal').classList.remove('active');
}

async function doCopyDay() {
    const targetDay = selectedDay;
    if (targetDay == null) { alert('Сначала выберите день в календаре'); return; }
    const sourceEl = document.getElementById('copy-day-source');
    const sourceDay = sourceEl ? parseInt(sourceEl.value, 10) : 0;
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    if (!sourceDay || sourceDay < 1 || sourceDay > daysInMonth) {
        alert('Введите день от 1 до ' + daysInMonth);
        return;
   }
    if (sourceDay === targetDay) { alert('Выберите другой день для копирования'); return; }
    const sourceRows = schedule.filter(s => Number(s.day) === sourceDay);
    if (!sourceRows.length) { alert('В выбранном дне нет записей для копирования'); closeCopyDayModal(); return; }
    for (const row of sourceRows) {
        let taskIds = [];
        try {
            const raw = row.task_ids;
            taskIds = Array.isArray(raw) ? raw : JSON.parse(typeof raw === 'string' ? raw : '[]');
       } catch (e) {}
        const res = await fetch('/api/schedule/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: row.user_id,
                year: currentYear,
                month: currentMonth,
                day: targetDay,
                task_ids: taskIds,
                notes: (row.notes || '').trim()
            })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.status !== 'success') {
            alert('Ошибка копирования: ' + (data.message || res.status));
            return;
       }
   }
    closeCopyDayModal();
    loadCalendar();
    updateDayDashboard(targetDay);
    alert('Скопировано записей: ' + sourceRows.length);
}

function dayMenuOpenMyTasks() {
    const day = selectedDay;
    closeDayMenuModal();
    if (day != null) openDayModal(day);
}

function dayMenuAdminTasks() {
    dayMenuOpenMyTasks();
}

function dayMenuUploadFile() {
    const day = selectedDay;
    closeDayMenuModal();
    if (day != null) showUploadModalForDay(day);
}

function dayMenuAssignEmployee() {
    const day = selectedDay;
    closeDayMenuModal();
    if (day != null) openQuickAssignMenuFromButton(day);
}

/** Загрузить задачи коллегам за текущий месяц */
async function loadColleagueTasks() {
    try {
        const res = await fetch(`/api/colleague-tasks?year=${currentYear}&month=${currentMonth}`, { credentials: 'include' });
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.colleague_tasks)) {
            colleagueTasks = data.colleague_tasks;
        } else {
            colleagueTasks = [];
        }
    } catch (e) {
        console.error('Ошибка загрузки задач коллегам:', e);
        colleagueTasks = [];
    }
}

/** Открыть модальное окно «Поставить задачу коллеге» (день уже выбран в меню дня) */
async function openColleagueTaskModal() {
    const day = selectedDay;
    closeDayMenuModal();
    if (day == null) return;
    selectedDay = day; // сохраняем день для submitColleagueTask
    document.getElementById('colleague-task-modal-title').textContent = `🤝 Поставить задачу коллеге на ${day}.${currentMonth}.${currentYear}`;
    document.getElementById('colleague-task-title').value = '';
    document.getElementById('colleague-task-description').value = '';
    document.getElementById('colleague-task-color').value = '#3498db';
    document.getElementById('colleague-task-color-hex').value = '#3498db';
    const dueEl = document.getElementById('colleague-task-due-date');
    if (dueEl) dueEl.value = '';
    document.getElementById('colleague-task-file-name').textContent = '';
    document.getElementById('colleague-task-file-input').value = '';
    document.getElementById('colleague-task-file-input').onchange = function() {
        const nameEl = document.getElementById('colleague-task-file-name');
        nameEl.textContent = this.files && this.files[0] ? this.files[0].name : '';
   };
    const assigneeSelect = document.getElementById('colleague-task-assignee');
    assigneeSelect.innerHTML = '<option value="">— Выберите коллегу —</option>';
    try {
        const res = await fetch('/api/colleagues');
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.colleagues)) {
            data.colleagues.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.full_name || c.username || 'Сотрудник';
                assigneeSelect.appendChild(opt);
           });
       }
   } catch (e) {
        console.error(e);
        alert('Не удалось загрузить список коллег');
   }
    const colorPick = document.getElementById('colleague-task-color');
    const hexInput = document.getElementById('colleague-task-color-hex');
    colorPick.oninput = () => { hexInput.value = colorPick.value; };
    hexInput.oninput = function() {
        let v = this.value.replace(/^#?/, '#');
        if (/^#[0-9A-Fa-f]{6}$/.test(v)) colorPick.value = v;
   };
    document.getElementById('colleague-task-modal').classList.add('active');
}

function closeColleagueTaskModal() {
    document.getElementById('colleague-task-modal').classList.remove('active');
}

/** Отправить форму «Задача коллеге» */
async function submitColleagueTask() {
    const assigneeId = document.getElementById('colleague-task-assignee').value;
    const title = (document.getElementById('colleague-task-title').value || '').trim();
    const description = (document.getElementById('colleague-task-description').value || '').trim();
    const color = (document.getElementById('colleague-task-color').value || '#3498db').trim();
    const fileInput = document.getElementById('colleague-task-file-input');
    if (!assigneeId) {
        alert('Выберите, кому адресована задача');
        return;
   }
    if (!title) {
        alert('Введите название задачи');
        return;
   }
    let fileId = null;
    if (fileInput.files && fileInput.files[0]) {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('year', currentYear);
        formData.append('month', currentMonth);
        formData.append('day', selectedDay || new Date().getDate());
        const uploadRes = await fetch('/api/files/upload', { method: 'POST', body: formData, });
        const uploadData = await uploadRes.json().catch(() => ({}));
        if (uploadRes.ok && uploadData.status === 'success' && uploadData.file_id) {
            fileId = uploadData.file_id;
       }
   }
    const submitBtn = document.getElementById('colleague-task-submit');
    if (submitBtn) submitBtn.disabled = true;
    try {
        const res = await fetch('/api/colleague-tasks', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                assignee_id: parseInt(assigneeId, 10),
                year: currentYear,
                month: currentMonth,
                day: selectedDay,
                title: title,
                description: description,
                color: color,
                file_id: fileId,
                due_date: (document.getElementById('colleague-task-due-date')?.value || '').trim() || null
           })
       });
        const d = await res.json().catch(() => ({}));
        if (res.ok && d.status === 'success') {
            closeColleagueTaskModal();
            await loadColleagueTasks();
            renderCalendar();
            alert('Задача поставлена коллеге');
       } else {
            alert('Ошибка: ' + (d.message || res.status));
       }
   } catch (e) {
        alert('Ошибка отправки');
   } finally {
        if (submitBtn) submitBtn.disabled = false;
   }
}

/** Быстрое добавление задачи к выбранному дню (как в десктопе) */
async function quickAddTaskForDay(taskName, taskColor) {
    if (selectedDay == null) return;
    await loadTasks();
    let task = tasks.find(t => (t.name || '').trim() === taskName);
    if (!task) {
        const res = await fetch('/api/tasks/add', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: taskName, color: taskColor || '#3498db' })
       });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.status !== 'success') {
            alert('Не удалось добавить задачу: ' + (data.message || 'ошибка'));
            return;
       }
        await loadTasks();
        task = tasks.find(t => t.id === data.task_id) || tasks.find(t => (t.name || '').trim() === taskName);
   }
    if (!task) {
        alert('Задача не найдена после создания');
        return;
   }
    const daySchedule = schedule.find(s => Number(s.day) === selectedDay && Number(s.user_id) === Number(currentUser.id));
    let taskIds = [];
    if (daySchedule && daySchedule.task_ids != null) {
        try {
            const raw = daySchedule.task_ids;
            taskIds = Array.isArray(raw) ? raw : JSON.parse(typeof raw === 'string' ? raw : '[]');
       } catch (e) {}
   }
    if (taskIds.indexOf(task.id) >= 0) {
        closeDayMenuModal();
        loadCalendar();
        return;
   }
    taskIds.push(task.id);
    const response = await fetch('/api/schedule/update', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: currentUser.id,
            year: currentYear,
            month: currentMonth,
            day: selectedDay,
            task_ids: taskIds,
            notes: daySchedule ? (daySchedule.notes || '') : ''
       })
   });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.status === 'success') {
        loadCalendar();
   } else {
        alert('Ошибка: ' + (data.message || 'не удалось добавить задачу'));
   }
}

/** Загрузка файла на выбранный день (из меню дня) */
function showUploadModalForDay(day) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*,.pdf';
    input.onchange = async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('year', currentYear);
        formData.append('month', currentMonth);
        formData.append('day', day);
        try {
            const res = await fetch('/api/files/upload', { method: 'POST', body: formData, });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                loadFiles();
                loadCalendar();
                alert('Файл загружен');
           } else {
                alert('Ошибка: ' + (data.message || res.status));
           }
       } catch (err) {
            console.error(err);
            alert('Ошибка загрузки');
       }
   };
    input.click();
}

/** Открыть выбор сотрудника для назначения (как по ПКМ, но из кнопки в меню дня) */
function openQuickAssignMenuFromButton(day) {
    const wrap = document.createElement('div');
    wrap.className = 'context-menu';
    wrap.style.cssText = 'position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); z-index: 10000; background: white; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15); padding: 16px; min-width: 260px;';
    wrap.innerHTML = `<div style="font-weight: bold; margin-bottom: 12px;">Поставить сотрудника на ${day}.${currentMonth}.${currentYear}</div>`;
    fetch('/api/users')
        .then(r => r.json())
        .then(data => {
            if (data.status !== 'success' || !data.users) return;
            const employees = data.users.filter(u => u.role === 'employee');
            employees.forEach(emp => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-primary btn-sm';
                btn.style.cssText = 'width: 100%; margin: 4px 0; text-align: left;';
                btn.textContent = emp.full_name || emp.username;
                btn.onclick = async () => {
                    document.body.removeChild(wrap);
                    document.body.removeChild(backdrop);
                    await loadTasks();
                    const shiftTask = tasks.find(t => (t.name || '').includes('Смена физическая'));
                    if (!shiftTask) {
                        alert('Не найдена задача «Смена физическая»');
                        return;
                   }
                    const res = await fetch('/api/schedule/update', { 
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: emp.id,
                            year: currentYear,
                            month: currentMonth,
                            day: day,
                            task_ids: [shiftTask.id],
                            notes: ''
                       })
                   });
                    const d = await res.json().catch(() => ({}));
                    if (res.ok && d.status === 'success') {
                        loadCalendar();
                        alert('Назначено: ' + (emp.full_name || emp.username));
                   } else {
                        alert('Ошибка: ' + (d.message || res.status));
                   }
               };
                wrap.appendChild(btn);
           });
            const closeBtn = document.createElement('button');
            closeBtn.className = 'btn btn-secondary btn-sm';
            closeBtn.style.marginTop = '8px';
            closeBtn.textContent = 'Закрыть';
            closeBtn.onclick = () => { document.body.removeChild(wrap); document.body.removeChild(backdrop); };
            wrap.appendChild(closeBtn);
       });
    const backdrop = document.createElement('div');
    backdrop.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 9999;';
    backdrop.onclick = () => { document.body.removeChild(wrap); document.body.removeChild(backdrop); };
    document.body.appendChild(backdrop);
    document.body.appendChild(wrap);
}

// Модальное окно редактирования дня (Мои задачи на день)
async function openDayModal(day) {
    selectedDay = day;
    const modal = document.getElementById('day-modal');
    const title = document.getElementById('modal-title');
    const tasksContainer = document.getElementById('modal-tasks');
    const notes = document.getElementById('modal-notes');
    
    title.textContent = `${day}.${currentMonth}.${currentYear}`;
    
    // Загружаем задачи
    await loadTasks();
    
    // Находим задачи текущего пользователя на этот день
    const daySchedule = schedule.find(s => Number(s.day) === day && Number(s.user_id) === Number(currentUser.id));
    let selectedTaskIds = [];
    if (daySchedule && daySchedule.task_ids != null) {
        try {
            const raw = daySchedule.task_ids;
            selectedTaskIds = Array.isArray(raw) ? raw : JSON.parse(typeof raw === 'string' ? raw : '[]');
       } catch (e) { selectedTaskIds = []; }
   }
    
    // Отображаем чекбоксы
    tasksContainer.innerHTML = '';
    tasks.forEach(task => {
        const label = document.createElement('label');
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.style.padding = '10px';
        label.style.marginBottom = '8px';
        label.style.cursor = 'pointer';
        label.style.borderRadius = '8px';
        label.style.transition = 'background 0.2s';
        
        label.addEventListener('mouseenter', () => {
            label.style.background = '#f5f7fa';
       });
        label.addEventListener('mouseleave', () => {
            label.style.background = 'transparent';
       });
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = task.id;
        checkbox.checked = selectedTaskIds.some(id => Number(id) === Number(task.id));
        checkbox.style.marginRight = '10px';
        
        const colorBox = document.createElement('div');
        colorBox.style.width = '20px';
        colorBox.style.height = '20px';
        colorBox.style.backgroundColor = task.color;
        colorBox.style.borderRadius = '4px';
        colorBox.style.marginRight = '10px';
        colorBox.style.border = '1px solid #e5e7eb';
        
        const taskName = document.createElement('span');
        taskName.textContent = task.name;
        
        label.appendChild(checkbox);
        label.appendChild(colorBox);
        label.appendChild(taskName);
        tasksContainer.appendChild(label);
   });
    
    notes.value = daySchedule ? (daySchedule.notes || '') : '';
    
    // Блок «Задачи мне от коллег»
    const colleagueBlock = document.getElementById('modal-colleague-tasks');
    if (colleagueBlock) {
        const dayCT = colleagueTasks.filter(ct =>
            Number(ct.day) === day && Number(ct.assignee_id) === Number(currentUser.id)
        );
        if (dayCT.length === 0) {
            colleagueBlock.innerHTML = '';
            colleagueBlock.style.display = 'none';
       } else {
            colleagueBlock.style.display = 'block';
            colleagueBlock.innerHTML = '<p class="modal-section-title">📌 Задачи мне от коллег</p>';
            dayCT.forEach(ct => {
                const div = document.createElement('div');
                div.className = 'colleague-task-item';
                div.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:8px 10px;margin-bottom:6px;border-radius:8px;background:#f5f7fa;border-left:4px solid ' + (ct.color || '#3498db') + ';';
                const left = document.createElement('div');
                left.innerHTML = '<strong>' + escapeHtml(ct.title || '') + '</strong>' +
                    (ct.description ? '<br><span style="font-size:12px;color:#6b7280;">' + escapeHtml(ct.description.substring(0, 100)) + (ct.description.length > 100 ? '…' : '') + '</span>' : '') +
                    (ct.created_by_name ? '<br><span style="font-size:11px;color:#9ca3af;">От: ' + escapeHtml(ct.created_by_name) + '</span>' : '') +
                    (ct.file_id ? '<br><a href="/api/files/' + ct.file_id + '" target="_blank" rel="noopener" class="colleague-task-file-link">📎 Скачать вложение</a>' : '');
                div.appendChild(left);
                const right = document.createElement('div');
                right.style.display = 'flex';
                right.style.alignItems = 'center';
                right.style.gap = '8px';
                if (ct.completed) {
                    const done = document.createElement('span');
                    done.style.cssText = 'color:var(--success,#10b981);font-weight:bold;';
                    done.textContent = '✓ Выполнено';
                    right.appendChild(done);
               } else {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'btn btn-sm btn-success';
                    btn.textContent = 'Отметить выполненной';
                    btn.onclick = async () => {
                        const r = await fetch('/api/colleague-tasks/' + ct.id + '/complete', { method: 'PATCH' });
                        const d = await r.json().catch(() => ({}));
                        if (r.ok && d.status === 'success') {
                            await loadColleagueTasks();
                            renderCalendar();
                            openDayModal(day);
                       } else {
                            alert('Ошибка: ' + (d.message || r.status));
                       }
                   };
                    right.appendChild(btn);
               }
                const tgBtn = document.createElement('button');
                tgBtn.type = 'button';
                tgBtn.className = 'btn btn-sm btn-secondary';
                tgBtn.textContent = '📤 В Telegram';
                tgBtn.onclick = async () => {
                    tgBtn.disabled = true;
                    try {
                        const r = await fetch('/api/colleague-tasks/' + ct.id + '/send-telegram', { method: 'POST' });
                        const d = await r.json().catch(() => ({}));
                        if (r.ok && d.status === 'success') {
                            tgBtn.textContent = '✓ Отправлено';
                       } else {
                            alert(d.message || 'Не удалось отправить');
                            tgBtn.disabled = false;
                       }
                   } catch (e) {
                        alert('Ошибка отправки');
                        tgBtn.disabled = false;
                   }
               };
                right.appendChild(tgBtn);
                div.appendChild(right);
                colleagueBlock.appendChild(div);
           });
       }
   }
    
    modal.classList.add('active');
}

function closeDayModal() {
    document.getElementById('day-modal').classList.remove('active');
    selectedDay = null;
}

async function saveDay() {
    if (!selectedDay) return;
    
    const checkboxes = document.querySelectorAll('#modal-tasks input[type="checkbox"]');
    const selectedTaskIds = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value));
    
    const notes = document.getElementById('modal-notes').value;
    
    try {
        const response = await fetch('/api/schedule/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                year: currentYear,
                month: currentMonth,
                day: selectedDay,
                task_ids: selectedTaskIds,
                notes: notes
            })
        });

        const data = await response.json().catch(() => ({}));
        if (response.ok && data.status === 'success') {
            closeDayModal();
            loadCalendar();
        } else {
            alert('Ошибка сохранения: ' + (data.message || response.status || 'неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        alert('Ошибка сохранения. Проверьте подключение.');
   }
}

// Чат (темы, дата/время, редактирование и удаление сообщений)
let chatTopics = [];
let currentChatTopicId = 1;
let aiTopicId = null;

async function loadChatTopics() {
    try {
        const res = await fetch('/api/chat/topics');
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.topics)) {
            chatTopics = data.topics;
            renderChatTopics();
       }
   } catch (e) {
        console.error('Ошибка загрузки тем чата:', e);
        chatTopics = [{ id: 1, title: 'Общий' }];
        renderChatTopics();
   }
}

function renderChatTopics() {
    const listEl = document.getElementById('chat-topics-list');
    const titleEl = document.getElementById('chat-topic-title');
    if (!listEl) return;
    listEl.innerHTML = '';
    const current = chatTopics.find(t => Number(t.id) === Number(currentChatTopicId));
    aiTopicId = null;
    if (titleEl) titleEl.textContent = current ? (current.title || 'Общий') : 'Общий';
    chatTopics.forEach(t => {
        const item = document.createElement('div');
        item.className = 'chat-topic-item' + (Number(t.id) === Number(currentChatTopicId) ? ' active' : '');
        item.dataset.topicId = t.id;
        const lowerTitle = (t.title || '').toLowerCase();
        const isTelegramTopic = Number(t.id) === 2 || lowerTitle === 'telegram';
        const isAiTopic = lowerTitle.indexOf('qwen') !== -1 || lowerTitle.indexOf('ai') !== -1 || lowerTitle.indexOf('помощник') !== -1;
        if (!aiTopicId && isAiTopic) {
            aiTopicId = t.id;
       }
        
        // Кнопки действий: редактировать и удалить (только для админа или создателя)
        let actionsHtml = '';
        if (!isTelegramTopic && (currentUser.role === 'admin' || Number(t.created_by) === Number(currentUser.id))) {
            actionsHtml = '<span class="chat-topic-item-actions">';
            actionsHtml += '<button type="button" class="btn-icon" onclick="event.stopPropagation(); openEditTopicModal(' + t.id + ')" title="Изменить">✎</button>';
            // Кнопка удаления только для админа и только для не-AI тем или если тема создана пользователем
            if (currentUser.role === 'admin' && (!isAiTopic || Number(t.created_by) === Number(currentUser.id))) {
                actionsHtml += '<button type="button" class="btn-icon" onclick="event.stopPropagation(); deleteTopic(' + t.id + ')" title="Удалить" style="color:#dc3545;">🗑️</button>';
           }
            actionsHtml += '</span>';
       }
        
        item.innerHTML = '<span class="chat-topic-item-title">' + escapeHtml(t.title || '') + '</span>' + actionsHtml;
        item.onclick = () => {
            console.log(`[CHAT] Switching to topic ${t.id}: ${t.title}`);
            currentChatTopicId = t.id;
            renderChatTopics();
            loadChat();
            startChatAutoRefresh();  // Запускаем авто-обновление для VK темы
        };
        listEl.appendChild(item);
   });
}

// Авто-обновление чата каждые 3 секунды для VK темы
let chatRefreshInterval = null;

function startChatAutoRefresh() {
    // Очищаем предыдущий интервал
    if (chatRefreshInterval) {
        clearInterval(chatRefreshInterval);
        chatRefreshInterval = null;
    }
    
    // Если выбрана VK тема (topic_id=3), обновляем каждые 3 сек
    if (Number(currentChatTopicId) === 3) {
        console.log('[CHAT] Auto-refresh enabled for VK topic (every 3s)');
        chatRefreshInterval = setInterval(() => {
            console.log('[CHAT] Auto-refreshing VK messages...');
            loadChat();
        }, 3000);
    }
}

async function loadChat() {
    try {
        console.log(`[CHAT] Loading messages for topic_id=${currentChatTopicId}`);
        const response = await fetch('/api/chat/messages?limit=100&topic_id=' + currentChatTopicId);
        const data = await response.json();
        console.log('[CHAT] API response:', data.status, 'messages:', data.messages ? data.messages.length : 0);
        
        if (data.messages && data.messages.length > 0) {
            console.log('[CHAT] First message:', data.messages[0]);
            console.log('[CHAT] Last message:', data.messages[data.messages.length - 1]);
        }
        
        const list = (data && data.status === 'success' && Array.isArray(data.messages)) ? data.messages : [];
        console.log('[CHAT] Rendering', list.length, 'messages');
        renderChat(list);
   } catch (error) {
        console.error('[CHAT] Error loading messages:', error);
        renderChat([]);
   }
}

function getInitials(name) {
    if (!name || !name.trim()) return '?';
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return (name[0] || '?').toUpperCase();
}

function formatChatText(text) {
    if (!text) return '';
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function renderChat(messages) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    // Запоминаем, находимся ли мы «внизу» чата, чтобы не сбрасывать прокрутку,
    // когда пользователь листает старые сообщения.
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    const shouldStickToBottom = distanceFromBottom < 80;
    container.innerHTML = '';
    const list = Array.isArray(messages) ? messages : [];

    list.forEach(msg => {
        const isOwn = Number(msg.user_id) === Number(currentUser.id);
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-bubble-wrap' + (isOwn ? ' own' : '');
        messageDiv.dataset.msgId = msg.id;

        const dateTimeStr = formatDateTimeRu(msg.created_at);
        const author = (msg.full_name || msg.username || 'Пользователь').toString();
        const text = (msg.message || '').toString();
        const initials = getInitials(author);
        const attachmentFileId = msg.attachment_file_id ? Number(msg.attachment_file_id) : null;

        const actions = isOwn || currentUser.role === 'admin' ?
            '<div class="chat-bubble-actions">' +
            (isOwn ? '<button type="button" class="btn-icon chat-msg-edit" data-msg-id="' + msg.id + '" title="Изменить">✎</button>' : '') +
            '<button type="button" class="btn-icon chat-msg-delete" onclick="deleteChatMessage(' + msg.id + ')" title="Удалить">✕</button>' +
            '</div>' : '';

        let bodyContent = '<div class="chat-bubble-text">' + formatChatText(text) + '</div>';
        if (attachmentFileId) {
            const viewUrl = '/api/files/' + attachmentFileId + '/view';
            const downloadUrl = '/api/files/' + attachmentFileId + '/download';
            const filename = msg.filename || 'Файл';
            const filetype = msg.file_type || '';
            
            // Определяем тип файла и показываем соответствующий контент
            const isImage = filetype.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(filename);
            const isVideo = filetype.startsWith('video/') || /\.(mp4|webm|ogg|avi|mov)$/i.test(filename);
            const isAudio = filetype.startsWith('audio/') || /\.(mp3|wav|ogg|m4a|flac)$/i.test(filename);
            const isDocument = filetype.includes('pdf') || filetype.includes('spreadsheet') || filetype.includes('word') || 
                              /\.(pdf|xlsx|xls|doc|docx|txt|rtf|csv)$/i.test(filename);
            
            if (isImage) {
                // Фото — показываем превью с кликом для просмотра
                bodyContent += '<div class="chat-attachment">' +
                    '<img src="' + viewUrl + '" alt="Фото" loading="lazy" style="cursor:pointer;" onclick="showFileViewModal(' + attachmentFileId + ', \'' + escapeJs(filename) + '\', \'' + (filetype || '') + '\', ' + (msg.file_size || 0) + ')">' +
                    '<a href="' + downloadUrl + '" target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Скачать</a>' +
                    '</div>';
           } else if (isVideo) {
                // Видео — показываем превью или плеер
                bodyContent += '<div class="chat-attachment chat-video">' +
                    '<video controls class="chat-video-player">' +
                    '<source src="' + viewUrl + '" type="' + filetype + '">' +
                    'Your browser does not support video. <a href="' + downloadUrl + '">Download</a>' +
                    '</video>' +
                    '<a href="' + downloadUrl + '" target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Download video</a>' +
                    '</div>';
           } else if (isAudio) {
                // Аудио — показываем плеер
                bodyContent += '<div class="chat-attachment chat-audio">' +
                    '<audio controls class="chat-audio-player">' +
                    '<source src="' + viewUrl + '" type="' + filetype + '">' +
                    'Your browser does not support audio. <a href="' + downloadUrl + '">Download</a>' +
                    '</audio>' +
                    '<a href="' + downloadUrl + '" target="_blank" rel="noopener" class="btn btn-sm btn-secondary">Download audio</a>' +
                    '</div>';
           } else {
                // Документы и остальные файлы — иконка + название + кнопка просмотра
                const fileIcon = getFileIcon(filename);
                bodyContent += '<div class="chat-attachment chat-document">' +
                    '<div class="chat-file-icon">' + fileIcon + '</div>' +
                    '<div class="chat-file-info">' +
                    '<div class="chat-file-name">' + escapeHtml(filename) + '</div>' +
                    '<div class="chat-file-size">' + formatFileSize(msg.file_size) + '</div>' +
                    '</div>' +
                    '<div class="chat-file-actions">' +
                    '<button type="button" class="btn btn-sm btn-secondary" onclick="showFileViewModal(' + attachmentFileId + ', \'' + escapeJs(filename) + '\', \'' + (filetype || '') + '\', ' + (msg.file_size || 0) + ')">Просмотреть</button>' +
                    '<a href="' + downloadUrl + '" target="_blank" rel="noopener" class="btn btn-sm btn-primary">Скачать</a>' +
                    '</div>' +
                    '</div>';
           }
       }

        messageDiv.innerHTML = `
            <div class="chat-avatar" title="${escapeHtml(author)}">${escapeHtml(initials)}</div>
            <div class="chat-bubble">
                <div class="chat-bubble-header">
                    <span class="chat-bubble-author">${escapeHtml(author)}</span>
                    <span class="chat-bubble-time" title="${escapeHtml(dateTimeStr)}">${escapeHtml(dateTimeStr)}</span>
                    ${actions}
                </div>
                ${bodyContent}
            </div>
        `;

        container.appendChild(messageDiv);
   });
    container.querySelectorAll('.chat-msg-edit').forEach(btn => {
        btn.onclick = function() {
            const wrap = this.closest('.chat-bubble-wrap');
            const textEl = wrap ? wrap.querySelector('.chat-bubble-text') : null;
            const raw = textEl ? textEl.innerText || '' : '';
            openEditMsgModal(parseInt(this.dataset.msgId, 10), raw);
       };
   });
    if (shouldStickToBottom) {
        container.scrollTop = container.scrollHeight;
   }
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const fileInput = document.getElementById('chat-file-input');
    const message = input.value.trim();
    const hasFile = fileInput && fileInput.files && fileInput.files[0];
    if (!message && !hasFile) return;

    async function doSend(attachmentFileId) {
        const isAi = aiTopicId != null && Number(currentChatTopicId) === Number(aiTopicId);
        if (isAi && attachmentFileId) {
            showToast('В AI-чат нельзя отправлять вложения, только текст.', 'warning');
            return;
       }
        const body = { message: message || '', topic_id: currentChatTopicId };
        if (!isAi && attachmentFileId) body.attachment_file_id = attachmentFileId;
        const url = isAi ? '/api/ai-chat/send' : '/api/chat/send';
        const res = await fetch(url, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            input.value = '';
            if (fileInput) { fileInput.value = ''; }
            const nameEl = document.getElementById('chat-attach-name');
            if (nameEl) { nameEl.style.display = 'none'; nameEl.textContent = ''; }
            loadChat();
       } else {
            alert('Ошибка: ' + (data.message || res.status));
       }
   }

    if (hasFile) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        const now = new Date();
        formData.append('year', now.getFullYear());
        formData.append('month', now.getMonth() + 1);
        formData.append('day', now.getDate());
        fetch('/api/files/upload', { method: 'POST', body: formData, })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success' && data.file_id) {
                    return doSend(data.file_id);
               }
                alert('Ошибка загрузки файла: ' + (data.message || ''));
           })
            .catch(err => { console.error(err); alert('Ошибка загрузки файла'); });
   } else {
        doSend(null);
   }
}

function initChatFileInput() {
    const fileInput = document.getElementById('chat-file-input');
    const nameEl = document.getElementById('chat-attach-name');
    if (!fileInput || !nameEl) return;
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            nameEl.textContent = '📎 ' + this.files[0].name;
            nameEl.style.display = 'block';
       } else {
            nameEl.style.display = 'none';
            nameEl.textContent = '';
       }
   });
}

function createAiChat() {
    // Проверяем, есть ли уже тема AI
    const existingAiTopic = chatTopics.find(t => {
        const lowerTitle = (t.title || '').toLowerCase();
        return lowerTitle.indexOf('qwen') !== -1 || lowerTitle.indexOf('ai') !== -1 || lowerTitle.indexOf('помощник') !== -1;
   });
    
    if (existingAiTopic) {
        // Если тема уже есть, переключаемся на неё
        currentChatTopicId = existingAiTopic.id;
        aiTopicId = existingAiTopic.id;
        renderChatTopics();
        loadChat();
        showToast('AI помощник уже создан', 'info');
        return;
   }
    
    // Создаём новую тему AI
    fetch('/api/chat/topics', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: '🤖 Qwen помощник' })
   })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.topic) {
            currentChatTopicId = data.topic.id;
            aiTopicId = data.topic.id;
            loadChatTopics();
            loadChat();
            showToast('AI помощник создан! Задайте свой вопрос.', 'success');
       } else {
            showToast('Ошибка создания AI чата: ' + (data.message || ''), 'error');
       }
   })
    .catch(err => {
        console.error('Ошибка создания AI чата:', err);
        showToast('Ошибка создания AI чата', 'error');
   });
}

function openCreateTopicModal() {
    document.getElementById('chat-topic-modal-title').textContent = 'Новая тема';
    document.getElementById('chat-topic-name').value = '';
    document.getElementById('chat-topic-save-btn').onclick = function() { saveChatTopic(true); };
    document.getElementById('chat-topic-modal').classList.add('active');
}

let editingTopicId = null;
function openEditTopicModal(id) {
    const t = chatTopics.find(x => Number(x.id) === Number(id));
    if (!t) return;
    editingTopicId = id;
    document.getElementById('chat-topic-modal-title').textContent = 'Редактировать тему';
    document.getElementById('chat-topic-name').value = t.title || '';
    document.getElementById('chat-topic-save-btn').onclick = function() { saveChatTopic(false); };
    document.getElementById('chat-topic-modal').classList.add('active');
}

function closeChatTopicModal() {
    document.getElementById('chat-topic-modal').classList.remove('active');
    editingTopicId = null;
}

async function deleteTopic(topicId) {
    if (!confirm('Вы уверены, что хотите удалить эту тему? Все сообщения в ней будут удалены.')) {
        return;
   }
    
    try {
        const res = await fetch('/api/chat/topics/' + topicId, { 
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }, 
       });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Тема удалена', 'success');
            // Переключаемся на общий чат
            const generalTopic = chatTopics.find(t => Number(t.id) !== Number(topicId));
            if (generalTopic) {
                currentChatTopicId = generalTopic.id;
           }
            loadChatTopics();
            loadChat();
       } else {
            showToast('Ошибка удаления: ' + (data.message || ''), 'error');
       }
   } catch (err) {
        console.error('Ошибка удаления темы:', err);
        showToast('Ошибка удаления темы', 'error');
   }
}

async function saveChatTopic(isCreate) {
    const name = (document.getElementById('chat-topic-name').value || '').trim();
    if (!name) { alert('Введите название темы'); return; }
    if (isCreate) {
        const res = await fetch('/api/chat/topics', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: name }) });
        const d = await res.json().catch(() => ({}));
        if (res.ok && d.status === 'success') {
            closeChatTopicModal();
            await loadChatTopics();
       } else { alert('Ошибка: ' + (d.message || res.status)); }
   } else {
        const res = await fetch('/api/chat/topics/' + editingTopicId, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: name }) });
        const d = await res.json().catch(() => ({}));
        if (res.ok && d.status === 'success') {
            closeChatTopicModal();
            await loadChatTopics();
       } else { alert('Ошибка: ' + (d.message || res.status)); }
   }
}

function openEditMsgModal(id, text) {
    document.getElementById('chat-edit-msg-id').value = id;
    document.getElementById('chat-edit-msg-text').value = text || '';
    document.getElementById('chat-edit-msg-modal').classList.add('active');
}

function closeChatEditMsgModal() {
    document.getElementById('chat-edit-msg-modal').classList.remove('active');
}

async function submitChatEditMessage() {
    const id = document.getElementById('chat-edit-msg-id').value;
    const message = (document.getElementById('chat-edit-msg-text').value || '').trim();
    if (!message) return;
    const res = await fetch('/api/chat/messages/' + id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: message }) });
    const d = await res.json().catch(() => ({}));
    if (res.ok && d.status === 'success') {
        closeChatEditMsgModal();
        loadChat();
   } else { alert('Ошибка: ' + (d.message || res.status)); }
}

async function deleteChatMessage(id) {
    if (!confirm('Удалить это сообщение?')) return;
    const res = await fetch('/api/chat/messages/' + id, { method: 'DELETE' });
    const d = await res.json().catch(() => ({}));
    if (res.ok && d.status === 'success') loadChat();
    else alert('Ошибка: ' + (d.message || res.status));
}

const chatInputEl = document.getElementById('chat-input');
if (chatInputEl) {
    chatInputEl.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
       }
   });
}

// Запрос разрешения на уведомления (для новых сообщений в чате)
function requestNotificationPermission() {
    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
        Notification.requestPermission().catch(function() {});
   }
}

// WebSocket для реального времени
function initWebSocket() {
    const socket = io();
    
    // Присоединяемся к комнате уведомлений пользователя
    if (currentUser && currentUser.id) {
        socket.emit('join', { user_id: currentUser.id });
    }
    
    // Real-time уведомления
    socket.on('new_notification', function(data) {
        console.log('[NOTIF] New notification:', data);
        // Обновляем бейдж
        checkUnreadNotifications();
        // Показываем тост
        if (data.title) {
            showToast(`🔔 ${data.title}${data.message ? ': ' + data.message : ''}`, data.type === 'error' ? 'error' : data.type === 'warning' ? 'warning' : 'success');
        }
        // Если панель открыта, обновляем список
        const panel = document.getElementById('notification-panel');
        if (panel && panel.style.display === 'block') {
            loadNotifications();
        }
    });
    
    socket.on('new_message', function(data) {

        console.log('[CHAT] Socket.IO new_message:', data.topic_id, 'current:', currentChatTopicId);
        if (Number(data.topic_id) === Number(currentChatTopicId)) {
            console.log('[CHAT] Reloading chat...');
            loadChat();
        }
        // Для VK темы всегда обновляем
        if (Number(data.topic_id) === 3) {
            startChatAutoRefresh();
        }
        if (Notification.permission === 'granted' && Number(data.user_id) !== Number(currentUser.id)) {
            const author = (data.full_name || data.username || 'Кто-то').toString();
            const body = (data.message || '').toString().slice(0, 100);
            try {
                const n = new Notification('Чат: График работы', { body: author + ': ' + body });
                n.onclick = function() {
                    window.focus();
                    showPage('chat');
                    if (data.topic_id != null) {
                        currentChatTopicId = Number(data.topic_id);
                        loadChatTopics();
                        loadChat();
                   }
               };
           } catch (e) {}
       }
   });
    socket.on('message_updated', function(data) {
        const wrap = document.querySelector('.chat-bubble-wrap[data-msg-id="' + data.id + '"]');
        if (wrap) {
            const textEl = wrap.querySelector('.chat-bubble-text');
            if (textEl) textEl.innerHTML = formatChatText(data.message || '');
       }
   });
    socket.on('message_deleted', function(data) {
        const wrap = document.querySelector('.chat-bubble-wrap[data-msg-id="' + data.id + '"]');
        if (wrap) wrap.remove();
   });
    
    socket.on('schedule_updated', function() {
        loadCalendar();
   });
}

// Утилиты
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAddTaskModal() {
    openTaskModal();
}

function showUploadModal() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*,.pdf';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('year', currentYear);
        formData.append('month', currentMonth);
        formData.append('day', selectedDay || new Date().getDate());
        
        fetch('/api/files/upload', {
            method: 'POST',
            body: formData,
            
       }).then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Файл загружен');
                loadFiles();
           } else {
                alert('Ошибка: ' + data.message);
           }
       }).catch(error => {
            console.error('Ошибка:', error);
            alert('Ошибка загрузки файла');
       });
   };
    input.click();
}

// Переменные для пагинации файлов
let fileCurrentPage = 0;
const FILES_PER_PAGE = 20;

// Загрузка файлов с поддержкой фильтров и пагинации
async function loadFiles(page = 0) {
    fileCurrentPage = page;
    
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        const allFiles = (data && data.status === 'success' && Array.isArray(data.files)) ? data.files : [];
        
        // Сохраняем в глобальную переменную
        window._filesCache = allFiles;
        
        // Применяем фильтры
        let filteredFiles = filterFiles(allFiles);
        
        // Вычисляем статистику
        updateFileStats(allFiles, filteredFiles);
        
        // Рендерим с пагинацией
        renderFilesWithPagination(filteredFiles, page);
        
   } catch (error) {
        console.error('Ошибка загрузки файлов:', error);
        window._filesCache = [];
        renderFilesWithPagination([], 0);
   }
}

// Фильтрация файлов
function filterFiles(files) {
    const search = (document.getElementById('file-search')?.value || '').toLowerCase().trim();
    const dateFilter = document.getElementById('file-date-filter')?.value;
    const category = document.getElementById('file-category')?.value || 'all';
    
    return files.filter(file => {
        // Поиск по названию
        if (search && !file.filename.toLowerCase().includes(search)) {
            return false;
       }
        
        // Фильтр по дате
        if (dateFilter) {
            const fileDate = `${file.year}-${String(file.month).padStart(2, '0')}-${String(file.day).padStart(2, '0')}`;
            if (fileDate !== dateFilter) {
                return false;
           }
       }
        
        // Фильтр по категории
        if (category !== 'all') {
            const ext = (file.file_type || file.filename.split('.').pop() || '').toLowerCase();
            const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].some(e => ext.includes(e));
            const isVideo = ['mp4', 'webm', 'ogg', 'avi', 'mov'].some(e => ext.includes(e));
            const isDocument = ['pdf', 'xlsx', 'xls', 'doc', 'docx', 'txt', 'csv', 'rtf'].some(e => ext.includes(e));
            
            if (category === 'photo' && !isImage) return false;
            if (category === 'video' && !isVideo) return false;
            if (category === 'document' && !isDocument) return false;
       }
        
        return true;
   });
}

// Обновление статистики
function updateFileStats(allFiles, filteredFiles) {
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'];
    const docExts = ['pdf', 'xlsx', 'xls', 'doc', 'docx', 'txt', 'csv', 'rtf'];
    
    let photosCount = 0;
    let docsCount = 0;
    let totalSize = 0;
    
    filteredFiles.forEach(file => {
        const ext = (file.file_type || file.filename.split('.').pop() || '').toLowerCase();
        const isImage = imageExts.some(e => ext.includes(e));
        const isDocument = docExts.some(e => ext.includes(e));
        
        if (isImage) photosCount++;
        if (isDocument) docsCount++;
        totalSize += (file.file_size || 0);
   });
    
    document.getElementById('file-total').textContent = `Всего: ${filteredFiles.length}`;
    document.getElementById('file-photos-count').textContent = `📷 Фото: ${photosCount}`;
    document.getElementById('file-docs-count').textContent = `📄 Документы: ${docsCount}`;
    document.getElementById('file-size-total').textContent = `Общий размер: ${(totalSize / (1024 * 1024)).toFixed(2)} MB`;
}

// Рендеринг с пагинацией
function renderFilesWithPagination(files, page) {
    const container = document.getElementById('files-list');
    if (!container) return;
    
    const totalPages = Math.ceil(files.length / FILES_PER_PAGE) || 1;
    const startIndex = page * FILES_PER_PAGE;
    const endIndex = startIndex + FILES_PER_PAGE;
    const pageFiles = files.slice(startIndex, endIndex);
    
    container.innerHTML = '';
    
    if (pageFiles.length === 0) {
        container.innerHTML = '<p class="files-empty">Нет файлов</p>';
   } else {
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
        pageFiles.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            
            const dateStr = formatDateTimeRu(file.uploaded_at);
            const sizeKb = ((file.file_size || 0) / 1024).toFixed(2);
            const name = (file.filename || '').toString();
            const fullName = (file.full_name || '').toString();
            const dayStr = [file.year, file.month, file.day].filter(Boolean).length === 3
                ? `${file.day}.${file.month}.${file.year}` : '';
            const ext = (file.file_type || name.split('.').pop() || '').toLowerCase();
            const isImage = imageExts.indexOf(ext) >= 0;
            const viewUrl = '/api/files/' + Number(file.id) + '/view';
            const previewHtml = isImage
                ? '<div class="file-item-preview"><img src="' + viewUrl + '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'no-preview\')"></div>'
                : '<div class="file-item-preview no-preview"><span class="file-item-preview-icon">📄</span></div>';
            
            item.innerHTML = `
                ${previewHtml}
                <div class="file-item-info">
                    <div class="file-item-name">${escapeHtml(name)}</div>
                    <div class="file-item-meta">
                        ${escapeHtml(dateStr)} • ${sizeKb} KB
                        ${dayStr ? ' • ' + escapeHtml(dayStr) : ''}
                        ${fullName ? ' • ' + escapeHtml(fullName) : ''}
                    </div>
                </div>
                <div class="file-item-actions">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="viewFile(${Number(file.id)})">Просмотреть</button>
                    <button type="button" class="btn btn-primary btn-sm" onclick="downloadFile(${Number(file.id)})">Скачать</button>
                    ${currentUser.role === 'admin' ? `<button type="button" class="btn btn-edit-file btn-sm" onclick="openEditFileModal(${Number(file.id)})" title="Изменить">✎</button>
                    <button type="button" class="btn btn-delete-file btn-sm" onclick="deleteFile(${Number(file.id)})" title="Удалить">✕</button>` : ''}
                </div>
            `;
            container.appendChild(item);
       });
   }
    
    // Обновляем информацию о странице
    document.getElementById('file-page-info').textContent = `Страница ${page + 1} из ${totalPages}`;
    document.getElementById('file-prev-btn').disabled = page === 0;
    document.getElementById('file-next-btn').disabled = (page + 1) * FILES_PER_PAGE >= files.length;
}

// Пагинация
function prevFilePage() {
    if (fileCurrentPage > 0) {
        loadFiles(fileCurrentPage - 1);
   }
}

function nextFilePage() {
    const filteredFiles = filterFiles(window._filesCache || []);
    if ((fileCurrentPage + 1) * FILES_PER_PAGE < filteredFiles.length) {
        loadFiles(fileCurrentPage + 1);
   }
}

let editingFileId = null;

function renderFiles(files) {
    const container = document.getElementById('files-list');
    if (!container) return;

    container.innerHTML = '';
    const list = Array.isArray(files) ? files : [];

    if (list.length === 0) {
        container.innerHTML = '<p class="files-empty">Нет файлов</p>';
        return;
   }

    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    list.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';

        const dateStr = formatDateTimeRu(file.uploaded_at);
        const sizeKb = ((file.file_size || 0) / 1024).toFixed(2);
        const name = (file.filename || '').toString();
        const fullName = (file.full_name || '').toString();
        const dayStr = [file.year, file.month, file.day].filter(Boolean).length === 3
            ? `${file.day}.${file.month}.${file.year}` : '';
        const ext = (file.file_type || name.split('.').pop() || '').toLowerCase();
        const isImage = imageExts.indexOf(ext) >= 0;
        const viewUrl = '/api/files/' + Number(file.id) + '/view';
        const previewHtml = isImage
            ? '<div class="file-item-preview"><img src="' + viewUrl + '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'no-preview\')"></div>'
            : '<div class="file-item-preview no-preview"><span class="file-item-preview-icon">📄</span></div>';

        item.innerHTML = `
            ${previewHtml}
            <div class="file-item-info">
                <div class="file-item-name">${escapeHtml(name)}</div>
                <div class="file-item-meta">
                    ${escapeHtml(dateStr)} • ${sizeKb} KB
                    ${dayStr ? ' • ' + escapeHtml(dayStr) : ''}
                    ${fullName ? ' • ' + escapeHtml(fullName) : ''}
                </div>
            </div>
            <div class="file-item-actions">
                <button type="button" class="btn btn-secondary btn-sm" onclick="viewFile(${Number(file.id)})">Просмотреть</button>
                <button type="button" class="btn btn-primary btn-sm" onclick="downloadFile(${Number(file.id)})">Скачать</button>
                ${currentUser.role === 'admin' ? `<button type="button" class="btn btn-edit-file btn-sm" onclick="openEditFileModal(${Number(file.id)})" title="Изменить">✎</button>
                <button type="button" class="btn btn-delete-file btn-sm" onclick="deleteFile(${Number(file.id)})" title="Удалить">✕</button>` : ''}
            </div>
        `;
        container.appendChild(item);
   });
}

function viewFile(fileId) {
    // Открываем модальное окно для просмотра файла
    const list = Array.isArray(window._filesCache) ? window._filesCache : [];
    const file = list.find(f => Number(f.id) === Number(fileId));
    if (file) {
        showFileViewModal(file.id, file.filename, file.file_type, file.file_size);
   } else {
        // Если файл не найден в кэше, просто открываем в новой вкладке
        window.open(`/api/files/${fileId}/view`, '_blank');
   }
}

function downloadFile(fileId) {
    window.open(`/api/files/${fileId}/download`, '_blank');
}

async function openEditFileModal(fileId) {
    const list = await loadFilesList();
    const file = list.find(f => Number(f.id) === Number(fileId));
    if (!file) return;
    editingFileId = fileId;
    document.getElementById('file-form-filename').value = file.filename || '';
    document.getElementById('file-form-day').value = file.day || '';
    document.getElementById('file-form-month').value = file.month || '';
    document.getElementById('file-form-year').value = file.year || '';
    document.getElementById('file-form-modal').classList.add('active');
}

async function loadFilesList() {
    try {
        const res = await fetch('/api/files');
        const data = await res.json();
        return (data && data.status === 'success' && Array.isArray(data.files)) ? data.files : [];
   } catch (e) {
        return [];
   }
}

function closeFileModal() {
    document.getElementById('file-form-modal').classList.remove('active');
    editingFileId = null;
}

// Модальное окно для просмотра файлов (фото и документы)
function showFileViewModal(fileId, filename, filetype, filesize) {
    const modal = document.getElementById('file-view-modal');
    const container = document.getElementById('file-view-container');
    const filenameEl = document.getElementById('file-view-filename');
    const metaEl = document.getElementById('file-view-meta');
    
    const viewUrl = `/api/files/${fileId}/view`;
    
    // Определяем тип файла
    const isImage = filetype && filetype.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(filename);
    const isVideo = filetype && filetype.startsWith('video/') || /\.(mp4|webm|ogg|avi|mov)$/i.test(filename);
    const isPDF = filetype && filetype.includes('pdf') || /\.pdf$/i.test(filename);
    const isExcel = filetype && (filetype.includes('spreadsheet') || filetype.includes('excel')) || /\.(xlsx|xls|csv)$/i.test(filename);
    const isWord = filetype && (filetype.includes('word') || filetype.includes('document')) || /\.(doc|docx)$/i.test(filename);
    
    let contentHtml = '';
    
    if (isImage) {
        // Изображение — показываем в img
        contentHtml = `<img src="${viewUrl}" alt="${escapeHtml(filename)}" onload="this.style.opacity=1">`;
   } else if (isVideo) {
        // Видео — показываем в video
        contentHtml = `<video controls style="max-width:100%; max-height:70vh;"><source src="${viewUrl}" type="${filetype || ''}"></video>`;
   } else if (isPDF) {
        // PDF — показываем в iframe
        contentHtml = `<iframe src="${viewUrl}#toolbar=0"></iframe>`;
   } else if (isExcel || isWord) {
        // Excel/Word — показываем iframe с предпросмотром (если браузер поддерживает)
        contentHtml = `<iframe src="${viewUrl}"></iframe>`;
   } else {
        // Остальные файлы — иконка и сообщение
        const fileIcon = getFileIcon(filename);
        contentHtml = `<div style="color:#fff; padding:40px;"><div style="font-size:64px; margin-bottom:20px;">${fileIcon}</div><div>Предпросмотр недоступен</div><div style="margin-top:20px;"><a href="${viewUrl}" target="_blank" class="btn btn-primary">Открыть в новой вкладке</a></div></div>`;
   }
    
    container.innerHTML = contentHtml;
    filenameEl.textContent = filename || 'Файл';
    metaEl.textContent = filesize ? formatFileSize(filesize) + (filetype ? ' • ' + filetype : '') : '';
    
    modal.style.display = 'flex';
}

function closeFileViewModal() {
    const modal = document.getElementById('file-view-modal');
    modal.style.display = 'none';
    document.getElementById('file-view-container').innerHTML = '';
}

async function saveFileFromModal() {
    if (editingFileId == null) return;
    const filename = (document.getElementById('file-form-filename').value || '').trim();
    const day = parseInt(document.getElementById('file-form-day').value, 10);
    const month = parseInt(document.getElementById('file-form-month').value, 10);
    const year = parseInt(document.getElementById('file-form-year').value, 10);
    if (!filename) {
        alert('Введите название файла');
        return;
   }
    if (!(year >= 2020 && year <= 2100 && month >= 1 && month <= 12 && day >= 1 && day <= 31)) {
        alert('Укажите корректную дату (день, месяц, год)');
        return;
   }
    try {
        const res = await fetch('/api/files/' + editingFileId, { 
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename, year: year, month: month, day: day })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeFileModal();
            await loadFiles();
       } else {
            alert('Ошибка: ' + (data.message || res.status));
       }
   } catch (e) {
        alert('Ошибка сохранения');
   }
}

function deleteFile(fileId) {
    confirmModal('Удалить этот файл? Файл будет удалён безвозвратно.', async function() {
        try {
            const res = await fetch('/api/files/' + fileId, { method: 'DELETE' });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                await loadFiles();
                showToast('Файл удалён', 'success');
           } else {
                showToast('Ошибка: ' + (data.message || res.status), 'error');
           }
       } catch (e) {
            showToast('Ошибка удаления', 'error');
       }
   });
}

// Контекстное меню для быстрого назначения (только для админов)
async function openQuickAssignMenu(day, event) {
    if (currentUser.role !== 'admin') return;
    
    try {
        // Загружаем список сотрудников
        const response = await fetch('/api/users');
        const data = await response.json();
        
        if (data.status !== 'success') {
            alert('Не удалось загрузить список сотрудников');
            return;
       }
        
        const employees = data.users.filter(u => u.role === 'employee');
        if (employees.length === 0) {
            alert('Нет сотрудников для назначения');
            return;
       }
        
        // Все сотрудники кнопками (сортировка по имени)
        const sorted = [...employees].sort((a, b) =>
            (a.full_name || a.username || '').localeCompare(b.full_name || b.username || '')
        );
        const quickUsers = sorted;
        
        // Создаем контекстное меню (с прокруткой при большом числе сотрудников)
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${event.clientX}px;
            top: ${event.clientY}px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 8px;
            z-index: 10000;
            min-width: 200px;
            max-height: 70vh;
            overflow-y: auto;
        `;
        
        const title = document.createElement('div');
        title.textContent = `${day}.${currentMonth}.${currentYear}`;
        title.style.cssText = 'font-weight: bold; padding: 8px; border-bottom: 1px solid #e5e7eb; margin-bottom: 4px;';
        menu.appendChild(title);
        
        // Кнопки для каждого сотрудника
        quickUsers.forEach(emp => {
            const btn = document.createElement('button');
            btn.textContent = emp.full_name || emp.username;
            btn.className = 'btn btn-primary btn-sm';
            btn.style.cssText = 'width: 100%; margin: 4px 0; text-align: left; padding: 8px;';
            btn.onclick = async () => {
                // Находим задачу "Смена физическая"
                await loadTasks();
                const shiftTask = tasks.find(t => 
                    t.name.includes('Смена физическая') || t.name === 'Смена физическая'
                );
                
                if (!shiftTask) {
                    alert('Не найдена задача "Смена физическая"');
                    document.body.removeChild(menu);
                    return;
               }
                
                // Сохраняем задачу
                const saveResponse = await fetch('/api/schedule/update', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: emp.id,
                        year: currentYear,
                        month: currentMonth,
                        day: day,
                        task_ids: [shiftTask.id],
                        notes: ''
                   })
               });
                
                const saveData = await saveResponse.json().catch(() => ({}));
                if (saveResponse.ok && saveData.status === 'success') {
                    document.body.removeChild(menu);
                    loadCalendar();
                    alert(`Задача назначена ${emp.full_name || emp.username}`);
               } else {
                    alert('Ошибка сохранения: ' + (saveData.message || saveResponse.status || 'неизвестная ошибка'));
               }
           };
            menu.appendChild(btn);
       });
        
        document.body.appendChild(menu);
        
        // Закрытие при клике вне меню
        const closeMenu = (e) => {
            if (!menu.contains(e.target)) {
                document.body.removeChild(menu);
                document.removeEventListener('click', closeMenu);
           }
       };
        
        setTimeout(() => {
            document.addEventListener('click', closeMenu);
       }, 100);
        
   } catch (error) {
        console.error('Ошибка открытия контекстного меню:', error);
   }
}

// ---------- Рабочий журнал ----------
let wjShifts = [];
let wjCurrentShiftId = null;

function initWorkJournalPage() {
    const now = new Date();
    const monthSelect = document.getElementById('wj-month');
    const yearSelect = document.getElementById('wj-year');
    if (monthSelect && !monthSelect.options.length) {
        for (let m = 1; m <= 12; m++) {
            const o = document.createElement('option');
            o.value = m;
            o.textContent = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'][m - 1];
            if (m === now.getMonth() + 1) o.selected = true;
            monthSelect.appendChild(o);
       }
   }
    if (yearSelect && !yearSelect.options.length) {
        for (let y = now.getFullYear(); y >= now.getFullYear() - 2; y--) {
            const o = document.createElement('option');
            o.value = y;
            o.textContent = y;
            if (y === now.getFullYear()) o.selected = true;
            yearSelect.appendChild(o);
        }
    }
    const userSelect = document.getElementById('wj-user');
    if (userSelect && currentUser.role === 'admin' && userSelect.options.length <= 1) {
        fetch('/api/users', { credentials: 'include' }).then(r => r.json()).then(data => {
            if (data.status !== 'success' || !data.users) return;
            data.users.filter(u => u.role === 'employee').forEach(u => {
                const o = document.createElement('option');
                o.value = u.id;
                o.textContent = u.full_name || u.username;
                userSelect.appendChild(o);
            });
        });
    }
}

async function loadWorkJournal() {
    const month = document.getElementById('wj-month')?.value || new Date().getMonth() + 1;
    const year = document.getElementById('wj-year')?.value || new Date().getFullYear();
    const userSelect = document.getElementById('wj-user');
    const userId = userSelect ? userSelect.value : '';
    let url = `/api/work-journal?year=${year}&month=${month}`;
    if (userId) url += `&user_id=${userId}`;
    try {
        const res = await fetch(url, { credentials: 'include' });
        const data = await res.json();
        if (data.status !== 'success' || !Array.isArray(data.sessions)) {
            document.getElementById('work-journal-list').innerHTML = '<p class="text-muted">Нет данных или ошибка загрузки.</p>';
            return;
       }
        wjShifts = data.sessions;  // sessions вместо shifts
        renderWorkJournalList(wjShifts);
   } catch (e) {
        console.error(e);
        document.getElementById('work-journal-list').innerHTML = '<p class="text-muted">Ошибка загрузки.</p>';
   }
}

function renderWorkJournalList(shifts) {
    const listEl = document.getElementById('work-journal-list');
    if (!listEl) return;
    if (!shifts || shifts.length === 0) {
        listEl.innerHTML = '<p class="text-muted">Нет смен за выбранный период. Откройте смену для дня из графика.</p>';
        return;
   }
    listEl.innerHTML = shifts.map(s => {
        // Используем status для определения статуса
        const isClosed = s.status === 'closed';
        const isOpen = s.status === 'opened';
        const canClose = !isClosed;  // Можно закрыть если не закрыта
        const closed = isClosed ? '✅ Закрыта' : (isOpen ? '🟢 Открыта' : '⚪ Не открыта');
        const name = (s.full_name || '').toString();
        return `
            <div class="work-journal-card" data-shift-id="${s.id}" style="margin-bottom:12px; padding:12px; background:var(--bg-secondary,#f9fafb); border-radius:8px; border:1px solid var(--border,#e5e7eb);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <div>
                        <strong>${escapeHtml([s.day, s.month, s.year].join('.'))}</strong>
                        ${name ? ' · ' + escapeHtml(name) : ''}
                        <span style="margin-left:8px;">${closed}</span>
                    </div>
                    <div>
                        <button type="button" class="btn btn-sm btn-secondary" onclick="showWjDetail(${s.id})">Подробнее</button>
                        ${canClose ? `
                            <button type="button" class="btn btn-sm btn-success" onclick="openWjEntryModal(${s.id})">➕ Запись</button>
                            <button type="button" class="btn btn-sm btn-success" onclick="openWjCloseModal(${s.id})">📒 Закрыть смену</button>
                        ` : ''}
                        ${isClosed ? `
                            <button type="button" class="btn btn-sm btn-danger" onclick="deleteWjShift(${s.id})">🗑️ Удалить</button>
                        ` : ''}
                    </div>
                </div>
                <div style="font-size:12px; color:#6b7280; margin-top:6px;">
                    Утро касса: ${formatMoney(s.morning_cash)}${s.evening_cash != null ? ' · Вечер наличные: ' + formatMoney(s.evening_cash) + ' · Безнал: ' + formatMoney(s.evening_cashless) : ''}
                </div>
                <div class="wj-shift-detail" style="display:none; margin-top:8px;"></div>
            </div>
        `;
   }).join('');
}

function formatMoney(val) {
    if (val == null || val === '') return '—';
    const n = Number(val);
    return isNaN(n) ? '—' : n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function getEntryKindName(kind) {
    const names = {
        'opening': '📦 Открытие смены',
        'closing': '🌙 Закрытие смены',
        'sale': '💰 Продажа',
        'expense': '💸 Расход',
        'opening': '📦 Открытие',
        'salary': '💵 Зарплата'
   };
    return names[kind] || kind;
}

function getEntryKindClass(kind) {
    const classes = {
        'opening': 'entry-opening',
        'closing': 'entry-closing',
        'sale': 'entry-sale',
        'expense': 'entry-expense'
   };
    return classes[kind] || '';
}

async function showWjDetail(shiftId) {
    wjCurrentShiftId = shiftId;
    const card = document.querySelector('.work-journal-card[data-shift-id="' + shiftId + '"]');
    if (!card) return;
    const detailEl = card.querySelector('.wj-shift-detail');
    if (!detailEl) return;

    // Сворачиваем, если уже раскрыта
    if (detailEl.style.display === 'block') {
        detailEl.style.display = 'none';
        detailEl.innerHTML = '';
        return;
   }

    // Сворачиваем остальные смены
    document.querySelectorAll('.wj-shift-detail').forEach(el => {
        if (el !== detailEl) {
            el.style.display = 'none';
            el.innerHTML = '';
       }
   });

    try {
        const res = await fetch(`/api/work-journal/shift/${shiftId}`, { credentials: 'include' });
        const data = await res.json();
        if (data.status !== 'success' || !data.shift) {
            detailEl.innerHTML = '<p class="text-muted error">Ошибка загрузки смены</p>';
            detailEl.style.display = 'block';
            return;
       }

        const s = data.shift;
        const isClosed = s.status === 'closed';
        const entries = s.entries || [];

        // Формируем HTML с подробной информацией
        let html = `
            <div style="margin-top:12px; padding:12px; background:#f0f4f8; border-radius:6px;">
                <h4 style="margin:0 0 12px 0; font-size:14px; color:#1976d2;">📊 Детали смены</h4>
                
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:8px; margin-bottom:12px;">
                    <div style="padding:8px; background:#e8f5e9; border-radius:4px;">
                        <div style="font-size:12px; color:#666;">📦 Утро</div>
                        <div style="font-size:16px; font-weight:bold; color:#2e7d32;">${formatMoney(s.morning_cash)} ₽</div>
                    </div>
                    <div style="padding:8px; background:#e3f2fd; border-radius:4px;">
                        <div style="font-size:12px; color:#666;">💰 Выручка</div>
                        <div style="font-size:16px; font-weight:bold; color:#1976d2;">${formatMoney(s.revenue_total)} ₽</div>
                    </div>
                    <div style="padding:8px; background:#fff3e0; border-radius:4px;">
                        <div style="font-size:12px; color:#666;">💸 Операции</div>
                        <div style="font-size:16px; font-weight:bold; color:#e65100;">${formatMoney(entries.filter(e => ['Внесла в кассу', 'Отдала деньги', 'Взяла зарплату'].includes(e.kind)).reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0))} ₽</div>
                    </div>
                    ${isClosed ? `
                    <div style="padding:8px; background:#f3e5f5; border-radius:4px;">
                        <div style="font-size:12px; color:#666;">💵 Вечер</div>
                        <div style="font-size:16px; font-weight:bold; color:#7b1fa2;">${formatMoney(s.evening_cash)} ₽</div>
                    </div>
                    ` : ''}
                </div>
        `;

        if (entries.length > 0) {
            html += `
                <div style="margin-top:12px;">
                    <strong style="font-size:13px;">📝 Операции:</strong>
                    <div style="margin-top:6px; max-height:200px; overflow-y:auto;">
                        ${entries.map(e => `
                            <div style="display:flex; justify-content:space-between; padding:4px 8px; background:#fff; border-radius:4px; margin-bottom:4px; font-size:13px;">
                                <span>${e.kind}</span>
                                <strong>${formatMoney(e.amount)} ₽</strong>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
       }

        if (isClosed) {
            const expected = (s.morning_cash || 0) + (s.revenue_total || 0) - entries.filter(e => ['Внесла в кассу', 'Отдала деньги', 'Взяла зарплату'].includes(e.kind)).reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0);
            const actual = s.evening_cash || 0;
            const discrepancy = actual - expected;
            
            html += `
                <div style="margin-top:12px; padding:8px; background:${discrepancy === 0 ? '#e8f5e9' : (discrepancy > 0 ? '#fff3e0' : '#ffebee')}; border-radius:4px; border:2px solid ${discrepancy === 0 ? '#4caf50' : (discrepancy > 0 ? '#ff9800' : '#f44336')};">
                    <div style="font-size:13px; font-weight:bold; color:#333;">
                        ${discrepancy === 0 ? '✅ ВСЁ СХОДИТСЯ' : (discrepancy > 0 ? '✅ ИЗЛИШЕК' : '❌ НЕДОСТАЧА')}
                    </div>
                    <div style="font-size:18px; font-weight:bold; color:${discrepancy === 0 ? '#4caf50' : (discrepancy > 0 ? '#ff9800' : '#f44336')};">
                        ${formatMoney(Math.abs(discrepancy))} ₽ ${discrepancy !== 0 ? (discrepancy > 0 ? '(больше)' : '(меньше)') : ''}
                    </div>
                </div>
            `;
       }

        html += `</div>`;
        detailEl.innerHTML = html;
        detailEl.style.display = 'block';

   } catch (e) {
        detailEl.innerHTML = '<p class="text-muted error">Ошибка: ' + e.message + '</p>';
        detailEl.style.display = 'block';
   }
}

// Показать полную бухгалтерскую форму смены
window.showShiftDetail = function(shiftId) {
    // Загружаем данные и открываем форму (аналогично openWjCloseModal, но только для просмотра)
    fetch(`/api/work-journal/shift/${shiftId}`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success' && data.shift) {
            const s = data.shift;
            const isClosed = s.status === 'closed';
            
            // Показываем уведомление с полной информацией
            let msg = `📒 СМЕНА ${s.day}.${s.month}.${s.year}\n\n`;
            msg += `👤 ${s.full_name || '—'}\n\n`;
            msg += `━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            msg += `📦 УТРО: ${formatMoney(s.morning_cash)} ₽\n\n`;
            msg += `💰 ПРИХОД:\n`;
            msg += `  • Выручка: ${formatMoney(s.revenue_total)} ₽\n`;
            msg += `  • Безнал: ${formatMoney(s.acquiring_amount)} ₽\n\n`;
            
            const entries = s.entries || [];
            const expenses = entries.filter(e => ['Внесла в кассу', 'Отдала деньги', 'Взяла зарплату'].includes(e.kind));
            if (expenses.length > 0) {
                msg += `💸 ОПЕРАЦИИ:\n`;
                expenses.forEach(e => msg += `  • ${e.kind}: ${formatMoney(e.amount)} ₽\n`);
                msg += `\n`;
           }
            
            if (isClosed) {
                const expected = (s.morning_cash || 0) + (s.revenue_total || 0) - expenses.reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0);
                const actual = s.evening_cash || 0;
                const discrepancy = actual - expected;
                
                msg += `━━━━━━━━━━━━━━━━━━━━━━━━\n`;
                msg += `📊 ДОЛЖНО: ${formatMoney(expected)} ₽\n`;
                msg += `💵 ФАКТ: ${formatMoney(actual)} ₽\n\n`;
                
                if (discrepancy === 0) {
                    msg += `✅ ВСЁ СХОДИТСЯ!\n`;
               } else if (discrepancy > 0) {
                    msg += `✅ ИЗЛИШЕК: +${formatMoney(discrepancy)} ₽\n`;
               } else {
                    msg += `❌ НЕДОСТАЧА: ${formatMoney(discrepancy)} ₽\n`;
               }
           } else {
                msg += `━━━━━━━━━━━━━━━━━━━━━━━━\n`;
                msg += `🟢 Смена открыта\n`;
           }
            
            alert(msg);
        }
    })
    .catch(err => alert('Ошибка: ' + err.message));
}

async function showWjDetail(shiftId) {
    const detailEl = document.getElementById('work-journal-detail');
    if (!detailEl) return;
    
    try {
        const res = await fetch(`/api/work-journal/shift/${shiftId}`, { credentials: 'include' });
        const data = await res.json();
        if (data.status !== 'success' || !data.shift) {
            detailEl.innerHTML = '<div class="alert alert-danger">❌ Ошибка загрузки данных</div>';
            detailEl.style.display = 'block';
            return;
        }

        const s = data.shift;
        const entries = s.entries || [];
        const isAdmin = currentUser && currentUser.role === 'admin';
        
        // Сохраняем записи в кэш для редактирования
        wjEditEntryCache = {};
        entries.forEach(e => { wjEditEntryCache[e.id] = e; });
        
        // Разделяем записи по типам
        const openingEntry = entries.find(e => e.kind === 'opening');
        const closingEntry = entries.find(e => e.kind === 'closing');
        const saleEntries = entries.filter(e => e.kind === 'sale');
        const expenseEntries = entries.filter(e => e.kind === 'expense');
        const otherEntries = entries.filter(e => !['opening', 'closing', 'sale', 'expense'].includes(e.kind));
        
        // Формируем HTML для каждой записи
        function renderEntry(e) {
            const kindName = getEntryKindName(e.kind);
            const kindClass = getEntryKindClass(e.kind);
            const amount = e.amount != null ? formatMoney(e.amount) : '';
            const note = e.note ? `<span class="entry-note">${escapeHtml(e.note)}</span>` : '';
            const time = formatDateTimeRu(e.created_at);
            
            return `
                <div class="entry-row ${kindClass}">
                    <div class="entry-main">
                        <span class="entry-kind">${kindName}</span>
                        ${amount ? `<span class="entry-amount">${amount}</span>` : ''}
                        ${note}
                    </div>
                    <div class="entry-footer">
                        <span class="entry-time">🕐 ${time}</span>
                        ${e.user_full_name ? `<span class="entry-author">👤 ${escapeHtml(e.user_full_name)}</span>` : ''}
                        ${isAdmin ? `
                            <button class="btn-icon btn-edit" onclick="openWjEditEntryModal(${e.id})" title="Редактировать">✏️</button>
                            <button class="btn-icon btn-delete" onclick="deleteWjEntry(${e.id})" title="Удалить">🗑️</button>
                        ` : ''}
                    </div>
                </div>
            `;
       }
        
        // Заголовок смены
        const shiftDate = `${s.day}.${s.month}.${s.year}`;
        const shiftUser = s.full_name || '';

        // Статус смены - используем status из новой БД
        const isClosed = s.status === 'closed';
        const isOpen = s.status === 'opened';

        // Статус смены для отображения
        const statusBadge = isClosed
            ? '<span class="badge" style="background:#10b981; color:white; padding:4px 10px; border-radius:6px; font-size:12px;">✅ Закрыта</span>'
            : (isOpen ? '<span class="badge" style="background:#f59e0b; color:white; padding:4px 10px; border-radius:6px; font-size:12px;">🟢 Открыта</span>' : '<span class="badge" style="background:#6b7280; color:white; padding:4px 10px; border-radius:6px; font-size:12px;">⚪ Не открыта</span>');
        
        // Секция с записями
        let entriesSection = '';
        
        if (openingEntry) {
            entriesSection += `
                <div class="entries-section">
                    <div class="section-header">📦 Утреннее открытие</div>
                    ${renderEntry(openingEntry)}
                </div>
            `;
       }
        
        if (saleEntries.length > 0 || expenseEntries.length > 0 || otherEntries.length > 0) {
            entriesSection += `<div class="entries-section"><div class="section-header">📝 Записи за день</div>`;
            
            saleEntries.forEach(e => { entriesSection += renderEntry(e); });
            expenseEntries.forEach(e => { entriesSection += renderEntry(e); });
            otherEntries.forEach(e => { entriesSection += renderEntry(e); });
            
            if (saleEntries.length === 0 && expenseEntries.length === 0 && otherEntries.length === 0) {
                entriesSection += '<div class="no-entries">Нет записей за день</div>';
           }
            
            entriesSection += '</div>';
       }
        
        if (closingEntry) {
            entriesSection += `
                <div class="entries-section">
                    <div class="section-header">🌙 Вечернее закрытие</div>
                    ${renderEntry(closingEntry)}
                </div>
            `;
       }
        
        if (!openingEntry && !closingEntry && saleEntries.length === 0 && expenseEntries.length === 0) {
            entriesSection = '<div class="no-entries">📭 Записей пока нет. Откройте смену или добавьте запись.</div>';
       }
        
        // Итоговая информация
        let totalsSection = '';
        if (isClosed) {
            const revenue = s.revenue_total != null ? formatMoney(s.revenue_total) : '—';
            const acquiring = s.acquiring_amount != null ? formatMoney(s.acquiring_amount) : '—';
            const cash = s.evening_cash != null ? formatMoney(s.evening_cash) : '—';
            const cashless = s.evening_cashless != null ? formatMoney(s.evening_cashless) : '—';
            
            // Считаем расхождение
            const morningCash = s.opening_sum || 0;
            const revenueTotal = s.revenue_total || 0;
            const acquiringAmount = s.acquiring_amount || 0;
            const terminalActual = s.terminal_actual || 0;
            
            // Наличные по ККТ = Выручка общая - Безнал по ККТ - Терминал
            const cashRevenue = revenueTotal - acquiringAmount - terminalActual;
            
            const expenses = entries.filter(e => ['Внесла в кассу', 'Отдала деньги', 'Взяла зарплату', 'Сняла в банк'].includes(e.kind))
                .reduce((sum, e) => {
                    // Внесла в кассу — ПЛЮС, остальное — МИНУС
                    if (e.kind === 'Внесла в кассу') {
                        return sum + (parseFloat(e.amount) || 0);
                    } else {
                        return sum - (parseFloat(e.amount) || 0);
                    }
                }, 0);
            
            const expected = morningCash + cashRevenue + expenses;
            const actual = s.evening_cash || 0;
            const discrepancy = actual - expected;
            
            let discrepancyHtml = '';
            if (Math.abs(discrepancy) > 0.01) {
                const discColor = discrepancy > 0 ? '#4caf50' : '#f44336';
                const discBg = discrepancy > 0 ? '#e8f5e9' : '#ffebee';
                const discText = discrepancy > 0 ? '✅ ИЗЛИШЕК' : '❌ НЕДОСТАЧА';
                discrepancyHtml = `
                    <div class="total-item" style="background:${discBg}; border:2px solid ${discColor};">
                        <span class="total-label" style="color:${discColor}; font-weight:bold;">${discText}:</span>
                        <span class="total-value" style="color:${discColor}; font-weight:bold;">${formatMoney(Math.abs(discrepancy))}</span>
                    </div>
                `;
            } else {
                discrepancyHtml = `
                    <div class="total-item" style="background:#e8f5e9; border:2px solid #4caf50;">
                        <span class="total-label" style="color:#4caf50; font-weight:bold;">✅ ВСЁ СХОДИТСЯ:</span>
                        <span class="total-value" style="color:#4caf50; font-weight:bold;">0</span>
                    </div>
                `;
            }

            totalsSection = `
                <div class="totals-block">
                    <div class="totals-header">📊 Итоги смены</div>
                    <div class="totals-grid">
                        <div class="total-item">
                            <span class="total-label">Утро (касса):</span>
                            <span class="total-value">${formatMoney(morningCash)}</span>
                        </div>
                        <div class="total-item">
                            <span class="total-label">Выручка (ККТ):</span>
                            <span class="total-value">${revenue}</span>
                        </div>
                        <div class="total-item">
                            <span class="total-label">Операции:</span>
                            <span class="total-value">${formatMoney(expenses)}</span>
                        </div>
                        <div class="total-item">
                            <span class="total-label">Эквайринг:</span>
                            <span class="total-value">${acquiring}</span>
                        </div>
                        <div class="total-item">
                            <span class="total-label">Наличные вечером:</span>
                            <span class="total-value">${cash}</span>
                        </div>
                        <div class="total-item">
                            <span class="total-label">Безнал:</span>
                            <span class="total-value">${cashless}</span>
                        </div>
                        ${discrepancyHtml}
                    </div>
                </div>
            `;
       }
        
        // Кнопки действий
        let actionButtons = '';
        if (!isClosed) {
            // Кнопка "Открыть смену" показывается ТОЛЬКО если смена ещё не открыта
            const showOpenButton = !openingEntry;
            actionButtons = `
                <div class="action-buttons" style="display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;">
                    ${showOpenButton ? `<button class="btn btn-primary" onclick="openWjOpenModalForDay()">📦 Открыть смену</button>` : ''}
                    ${openingEntry && !closingEntry ? `<button class="btn btn-success" onclick="openWjCloseModal(${s.id})">🌙 Закрыть смену</button>` : ''}
                    <button class="btn btn-info" onclick="openWjEntryModal(${s.id})">➕ Добавить запись</button>
                </div>
            `;
       }
        
        if (isAdmin) {
            actionButtons += `
                <div class="admin-buttons">
                    <button class="btn btn-secondary" onclick="openWjEditShiftModal(${s.id})">✏️ Редактировать смену</button>
                    <button class="btn btn-danger" onclick="deleteWjShift(${s.id})">🗑️ Удалить смену</button>
                </div>
            `;
       }
        
        // Формируем итоговый HTML
        detailEl.innerHTML = `
            <style>
                .wj-detail-card {
                    background: #fff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px;
                    margin-top: 12px;
               }
                .shift-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding-bottom: 12px;
                    border-bottom: 2px solid #f0f0f0;
                    margin-bottom: 16px;
               }
                .shift-title {
                    font-size: 16px;
                    font-weight: 600;
                    color: #2c3e50;
               }
                .entries-section {
                    margin: 16px 0;
                    border: 1px solid #e8e8e8;
                    border-radius: 6px;
                    overflow: hidden;
               }
                .section-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 10px 14px;
                    font-weight: 600;
                    font-size: 14px;
               }
                .entry-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    padding: 12px 14px;
                    border-bottom: 1px solid #f0f0f0;
                    transition: background 0.2s;
               }
                .entry-row:last-child {
                    border-bottom: none;
               }
                .entry-row:hover {
                    background: #f8f9fa;
               }
                .entry-opening { background: #f0fff4; }
                .entry-opening:hover { background: #e6ffea !important; }
                .entry-closing { background: #fffaf0; }
                .entry-closing:hover { background: #fff5e6 !important; }
                .entry-sale { background: #f0f7ff; }
                .entry-sale:hover { background: #e6f0ff !important; }
                .entry-expense { background: #fff5f5; }
                .entry-expense:hover { background: #ffebeb !important; }
                .entry-main {
                    flex: 1;
                    min-width: 0;
               }
                .entry-kind {
                    display: inline-block;
                    font-weight: 600;
                    color: #2d3748;
                    margin-right: 10px;
               }
                .entry-amount {
                    font-weight: 700;
                    color: #27ae60;
                    font-size: 15px;
               }
                .entry-note {
                    color: #718096;
                    margin-left: 8px;
               }
                .entry-footer {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 12px;
                    color: #a0aec0;
                    flex-shrink: 0;
                    margin-left: 12px;
               }
                .entry-time, .entry-author {
                    white-space: nowrap;
               }
                .btn-icon {
                    background: none;
                    border: none;
                    cursor: pointer;
                    padding: 4px 8px;
                    font-size: 14px;
                    opacity: 0.7;
                    transition: opacity 0.2s;
               }
                .btn-icon:hover {
                    opacity: 1;
               }
                .btn-edit { background: #edf2f7 !important; border-radius: 4px; }
                .btn-delete { background: #fed7d7 !important; border-radius: 4px; }
                .no-entries {
                    padding: 20px;
                    text-align: center;
                    color: #a0aec0;
                    font-style: italic;
               }
                .totals-block {
                    margin-top: 16px;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    border-radius: 8px;
                    padding: 16px;
               }
                .totals-header {
                    font-weight: 600;
                    font-size: 15px;
                    color: #2d3748;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #cbd5e0;
               }
                .totals-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 10px;
               }
                .total-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 12px;
                    background: white;
                    border-radius: 6px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
               }
                .total-label {
                    color: #718096;
                    font-size: 13px;
               }
                .total-value {
                    font-weight: 600;
                    color: #2d3748;
                    white-space: nowrap;
               }
                .action-buttons, .admin-buttons {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 16px;
                    padding-top: 16px;
                    border-top: 1px solid #e0e0e0;
               }
                .admin-buttons {
                    border-top: 1px dashed #cbd5e0;
               }
                .btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
               }
                .btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
               }
                .btn-primary { background: #667eea; color: white; }
                .btn-success { background: #48bb78; color: white; }
                .btn-info { background: #4299e1; color: white; }
                .btn-secondary { background: #a0aec0; color: white; }
                .btn-danger { background: #f56565; color: white; }
                .badge {
                    display: inline-block;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
               }
                .badge-success { background: #c6f6d5; color: #22543d; }
                .badge-warning { background: #fefcbf; color: #744210; }
                .badge-secondary { background: #e2e8f0; color: #4a5568; }
            </style>
            
            <div class="wj-detail-card">
                <div class="shift-header">
                    <div class="shift-title">
                        📅 Смена за ${shiftDate}${shiftUser ? ' · ' + escapeHtml(shiftUser) : ''}
                    </div>
                    ${statusBadge}
                </div>
                
                ${openingEntry ? `
                    <div class="info-block" style="background: #f0fff4; border-left: 4px solid #48bb78; padding: 12px; margin-bottom: 16px; border-radius: 4px;">
                        <strong>💰 Утро (касса):</strong> ${formatMoney(s.morning_cash || openingEntry.amount)}
                        ${openingEntry.created_at ? `<span style="color: #718096; margin-left: 12px;">🕐 ${formatDateTimeRu(openingEntry.created_at)}</span>` : ''}
                    </div>
                ` : ''}
                
                ${entriesSection}
                
                ${totalsSection}
                
                ${actionButtons}
            </div>
        `;
        
        detailEl.style.display = 'block';
        
   } catch (e) {
        console.error('Error loading shift details:', e);
        detailEl.innerHTML = '<div class="alert alert-danger">❌ Ошибка загрузки: ' + escapeHtml(e.message) + '</div>';
        detailEl.style.display = 'block';
   }
}

let wjEditEntryCache = {};

function openWjOpenModalForDay() {
    const month = document.getElementById('wj-month')?.value || currentMonth;
    const year = document.getElementById('wj-year')?.value || currentYear;
    const day = prompt('Введите число месяца (1–31) для открытия смены:', new Date().getDate());
    if (day == null) return;
    const d = parseInt(day, 10);
    if (d >= 1 && d <= 31) openWjOpenModal(d);
    else showToast('Введите число от 1 до 31', 'warning');
}

function exportWorkJournal() {
    const month = document.getElementById('wj-month')?.value || currentMonth;
    const year = document.getElementById('wj-year')?.value || currentYear;
    const userSelect = document.getElementById('wj-user');
    const userId = userSelect ? userSelect.value : '';
    let url = '/api/work-journal/export?year=' + year + '&month=' + month;
    if (userId) url += '&user_id=' + userId;
    window.open(url, '_blank');
    showToast('Скачивание CSV…', 'success');
}

function printWorkJournal() {
    const listEl = document.getElementById('work-journal-list');
    const detailEl = document.getElementById('work-journal-detail');
    if (!listEl) return;
    const prevDetailDisplay = detailEl ? detailEl.style.display : 'none';
    if (detailEl) detailEl.style.display = 'none';
    listEl.style.display = 'block';
    const month = document.getElementById('wj-month')?.value || currentMonth;
    const year = document.getElementById('wj-year')?.value || currentYear;
    const title = document.createElement('h2');
    title.textContent = 'Рабочий журнал — ' + month + '.' + year;
    title.style.marginBottom = '16px';
    listEl.insertBefore(title, listEl.firstChild);
    window.print();
    title.remove();
    if (detailEl) detailEl.style.display = prevDetailDisplay;
}

function printWorkJournalDetail() {
    const detailEl = document.getElementById('work-journal-detail');
    if (!detailEl || detailEl.style.display === 'none') return;
    window.print();
}

function updateChecklistState() {
    const checkboxes = document.querySelectorAll('.checklist-cb');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const btn = document.getElementById('btn-submit-wj-open');
    const warning = document.getElementById('checklist-warning');
    
    if (btn) btn.disabled = !allChecked;
    if (warning) warning.style.display = allChecked ? 'none' : 'block';
}

function openWjOpenModal(day) {
    const month = document.getElementById('wj-month')?.value || currentMonth;
    const year = document.getElementById('wj-year')?.value || currentYear;
    document.getElementById('wj-open-date-caption').textContent = `День ${day}.${month}.${year}`;
    document.getElementById('wj-morning-cash').value = '';
    document.getElementById('wj-open-modal').dataset.day = day;
    document.getElementById('wj-open-modal').dataset.month = month;
    document.getElementById('wj-open-modal').dataset.year = year;
    document.getElementById('wj-open-modal').dataset.attempt = '1';
    document.getElementById('wj-open-modal').classList.add('active');
    
    // Сбрасываем чек-лист при открытии модалки
    document.querySelectorAll('.checklist-cb').forEach(cb => cb.checked = false);
    updateChecklistState();
}

function closeWjOpenModal() {
    document.getElementById('wj-open-modal').classList.remove('active');
}

async function submitWjOpen() {
    const modal = document.getElementById('wj-open-modal');
    const day = modal.dataset.day;
    const month = modal.dataset.month;
    const year = modal.dataset.year;
    const attempt = parseInt(modal.dataset.attempt || '1', 10);
    const morningCash = document.getElementById('wj-morning-cash').value;
    const btn = document.querySelector('#wj-open-modal .btn-primary');
    setButtonLoading(btn, true, 'Открытие…');
    try {
        const res = await fetch('/api/work-journal/open', { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            
            body: JSON.stringify({
                year: parseInt(year),
                month: parseInt(month),
                day: parseInt(day),
                morning_cash: parseFloat(morningCash) || 0,
                attempt: attempt
           })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeWjOpenModal();
            await loadWorkJournal();
            showWjDetail(data.shift_id);
            showToast('Смена открыта', 'success');
       } else if (res.ok && data.status === 'discrepancy') {
            const left = data.attempts_left != null ? data.attempts_left : (3 - attempt);
            const msg = (data.message || 'Сумма пересчитана неверно либо у вас расхождения по кассе. Пересчитайте ещё раз либо обратитесь к администратору.') + (left > 0 ? '\n\nОсталось попыток: ' + left : '');
            alert(msg);
            modal.dataset.attempt = String(attempt + 1);
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   } finally {
        setButtonLoading(btn, false);
   }
}

function openWjEntryModal(shiftId) {
    wjCurrentShiftId = shiftId;
    document.getElementById('wj-entry-kind').value = 'Внесла в кассу';
    document.getElementById('wj-entry-amount').value = '';
    document.getElementById('wj-entry-note').value = '';
    document.getElementById('wj-entry-modal').classList.add('active');
}

function closeWjEntryModal() {
    document.getElementById('wj-entry-modal').classList.remove('active');
}

async function submitWjEntry() {
    const kind = document.getElementById('wj-entry-kind').value;
    const amount = document.getElementById('wj-entry-amount').value;
    const note = document.getElementById('wj-entry-note').value;
    const btn = document.querySelector('#wj-entry-modal .btn-primary');
    setButtonLoading(btn, true, 'Добавление…');
    try {
        const res = await fetch(`/api/work-journal/entry`, { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            
            body: JSON.stringify({ 
                shift_id: wjCurrentShiftId,
                entry_type: kind,
                amount: amount ? parseFloat(amount) : null, 
                description: note || null 
           })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeWjEntryModal();
            const detailEl = document.getElementById('work-journal-detail');
            if (detailEl && detailEl.style.display !== 'none') showWjDetail(wjCurrentShiftId);
            else loadWorkJournal();
            showToast('Запись добавлена', 'success');
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   } finally {
        setButtonLoading(btn, false);
   }
}

/** Зарплата по вилке от общей выручки (руб): до 15k→1500, 16–20k→1600, 20–25k→1750, 25–30k→1900, 30–35k→2500, 35–45k→3000, от 45k→4000 */
function salaryByRevenue(revenue) {
    if (revenue == null || revenue < 0) return 0;
    const r = parseFloat(revenue);
    if (r <= 15000) return 1500;
    if (r <= 20000) return 1600;
    if (r <= 25000) return 1750;
    if (r <= 30000) return 1900;
    if (r <= 35000) return 2500;
    if (r <= 45000) return 3000;
    return 4000;
}

/** Баланс записей смены: внесла (+) минус взяла/отдала/сняла (-) */
function wjEntriesBalance(entries) {
    if (!entries || !entries.length) return 0;
    const kindsIn = ['Внесла в кассу'];
    const kindsOut = ['Взяла зарплату', 'Отдала деньги', 'Сняла в банк'];
    let inSum = 0, outSum = 0, otherSum = 0;
    entries.forEach(e => {
        const amt = parseFloat(e.amount) || 0;
        if (kindsIn.includes(e.kind)) inSum += amt;
        else if (kindsOut.includes(e.kind)) outSum += amt;
        else if (e.kind === 'Другое') otherSum += amt;
   });
    // Округляем до 2 знаков, чтобы избежать проблем с плавающей точкой
    return Math.round((inSum - outSum + otherSum) * 100) / 100;
}

let wjCloseModalShift = null;

async function openWjCloseModal(shiftId) {
    console.log('📒 openWjCloseModal вызвана для shiftId:', shiftId);
    
    wjCurrentShiftId = shiftId;
    const s = wjShifts.find(x => Number(x.id) === Number(shiftId));
    console.log('Найдена смена:', s);

    // Заголовок
    const dateCaption = document.getElementById('wj-close-date-caption');
    if (dateCaption) dateCaption.textContent = s ? `День ${s.day}.${s.month}.${s.year}` : '';

    // Очищаем поля (проверяем существование)
    const clearField = (id) => { const el = document.getElementById(id); if (el) el.value = ''; };
    clearField('wj-revenue-total');
    clearField('wj-terminal-actual');
    clearField('wj-evening-cash');
    clearField('wj-close-note');
    clearField('wj-acquiring-file');
    clearField('wj-zreport-file');

    wjCloseModalShift = null;
    
    try {
        const res = await fetch(`/api/work-journal/shift/${shiftId}`, { credentials: 'include' });
        const data = await res.json();
        if (data.status === 'success' && data.shift) {
            wjCloseModalShift = data.shift;

            // Показываем утро - используем opening_sum из БД
            const morningCash = parseFloat(data.shift.opening_sum || data.shift.morning_cash) || 0;
            document.getElementById('wj-close-morning-cash').textContent = formatMoney(morningCash);
            
            // Показываем операции
            const entries = data.shift.entries || [];
            const expenses = entries.filter(e => ['Внесла в кассу', 'Отдала деньги', 'Взяла зарплату', 'Сняла в банк'].includes(e.kind));
            const expensesListEl = document.getElementById('wj-close-expenses-list');
            
            if (expenses.length === 0) {
                expensesListEl.textContent = 'Записей нет';
           } else {
                expensesListEl.innerHTML = expenses.map(e => 
                    `<div style="display:flex; justify-content:space-between; margin:4px 0;">` +
                    `<span>${e.kind}:</span>` +
                    `<strong>${formatMoney(parseFloat(e.amount) || 0)}</strong></div>`
                ).join('');
           }
            
            const totalExpenses = expenses.reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0);
            document.getElementById('wj-close-total-expenses').textContent = formatMoney(totalExpenses);
            
            // Обновляем итоги
            updateWjCloseTotalsNew();
       }
   } catch (e) { console.error(e); }
    
    document.getElementById('wj-close-modal').classList.add('active');

    // Вешаем обработчики на все поля
    ['wj-revenue-total', 'wj-terminal-actual', 'wj-evening-cash'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', updateWjCloseTotalsNew);
   });
}

function updateWjCloseTotalsNew() {
    // Просто вызываем calculateDiscrepancy для единой логики
    calculateDiscrepancy();
}

function calculateDiscrepancy() {
    if (!wjCloseModalShift) return;
    
    // 1. Утро (сумма открытия)
    const morningCash = parseFloat(wjCloseModalShift.opening_sum || wjCloseModalShift.morning_cash) || 0;
    
    // 2. Операции за смену (+/-)
    const entries = wjCloseModalShift.entries || [];
    const balance = wjEntriesBalance(entries);
    
    // 3. Чек ККТ (общий) — вводим вручную
    const revenueTotal = parseFloat(document.getElementById('wj-revenue-total').value) || 0;
    
    // 4. Чек терминала — вводим вручную
    const terminalActual = parseFloat(document.getElementById('wj-terminal-actual').value) || 0;
    
    // 5. Наличные по ККТ = Общая выручка - Безнал - Терминал
    // Безнал по ККТ = 0 (поле acquiring_amount не вводится, всегда 0)
    const cashRevenue = Math.round((revenueTotal - terminalActual) * 100) / 100;
    
    // 6. ДОЛЖНО БЫТЬ = Утро + Наличные по ККТ + Баланс операций (округляем до 2 знаков)
    const expectedCash = Math.round((morningCash + cashRevenue + balance) * 100) / 100;
    
    // 7. ФАКТ — наличные в кассе вечером
    const eveningCashRaw = document.getElementById('wj-evening-cash').value;
    const eveningCash = eveningCashRaw === '' ? null : parseFloat(eveningCashRaw);
    
    // 8. Расхождение = Факт - Должно (округляем до 2 знаков)
    const discrepancyCash = eveningCash != null ? Math.round((eveningCash - expectedCash) * 100) / 100 : null;
    
    // Обновляем UI
    document.getElementById('wj-close-expected-cash').textContent = formatMoney(expectedCash);
    document.getElementById('wj-close-actual-cash').textContent = eveningCash != null ? formatMoney(eveningCash) : '0';
    
    // Показываем расхождение
    const discBlock = document.getElementById('wj-close-discrepancy-block');
    const discValue = document.getElementById('wj-close-discrepancy-value');
    const discText = document.getElementById('wj-close-discrepancy-text');
    const discTitle = document.getElementById('wj-close-discrepancy-title');
    
    if (discrepancyCash != null && Math.abs(discrepancyCash) > 0.005) {
        discBlock.style.display = 'block';
        discValue.textContent = formatMoney(Math.abs(discrepancyCash));
        if (discrepancyCash > 0) {
            discBlock.style.background = '#e8f5e9';
            discBlock.style.borderColor = '#4caf50';
            discTitle.textContent = '✅ ИЗЛИШЕК';
            discText.textContent = 'В кассе больше, чем должно быть';
        } else {
            discBlock.style.background = '#ffebee';
            discBlock.style.borderColor = '#f44336';
            discTitle.textContent = '❌ НЕДОСТАЧА';
            discText.textContent = 'В кассе меньше, чем должно быть';
        }
    } else if (discrepancyCash != null && Math.abs(discrepancyCash) <= 0.005) {
        discBlock.style.display = 'block';
        discBlock.style.background = '#e8f5e9';
        discBlock.style.borderColor = '#4caf50';
        discTitle.textContent = '✅ ВСЁ СХОДИТСЯ!';
        discValue.textContent = '0';
        discText.textContent = '';
    } else {
        discBlock.style.display = 'none';
    }
}

function updateWjCloseTotals() {
    if (!wjCloseModalShift) return;
    
    // ПРАВИЛЬНАЯ ЛОГИКА:
    // 1. Утро (opening_sum) — сумма с утра
    const morningCash = parseFloat(wjCloseModalShift.opening_sum || wjCloseModalShift.morning_cash) || 0;
    
    // 2. Операции за смену (+/-)
    const entries = wjCloseModalShift.entries || [];
    const balance = wjEntriesBalance(entries);
    
    // 3. Чек ККТ (общий) = Наличные + Безнал по ККТ
    const revenueTotal = parseFloat(document.getElementById('wj-revenue-total').value) || 0;
    const acquiringAmount = parseFloat(document.getElementById('wj-acquiring-amount').value) || 0;
    
    // 4. Чек терминала (фактический безнал)
    const terminalActual = parseFloat(document.getElementById('wj-terminal-actual').value) || 0;
    
    // 5. ДОЛЖНО БЫТЬ = Утро + Наличные по ККТ + Операции
    // Наличные по ККТ = revenueTotal (это уже наличные, т.к. безнал введён отдельно)
    const expectedCash = morningCash + revenueTotal + balance;
    
    // 6. ФАКТ — сколько денег реально в кассе вечером
    const eveningCashRaw = document.getElementById('wj-evening-cash').value;
    const eveningCash = eveningCashRaw === '' ? null : parseFloat(eveningCashRaw);
    
    // 7. Расхождение = Факт - Должно
    const discrepancyCash = eveningCash != null ? (eveningCash - expectedCash) : null;
    
    // Обновляем UI
    document.getElementById('wj-close-expected-cash').textContent = formatMoney(expectedCash);
    document.getElementById('wj-close-actual-cash').textContent = eveningCash != null ? formatMoney(eveningCash) : '0';
    
    // Показываем расхождение
    const discBlock = document.getElementById('wj-close-discrepancy-block');
    const discValue = document.getElementById('wj-close-discrepancy-value');
    const discText = document.getElementById('wj-close-discrepancy-text');
    
    if (discrepancyCash != null && discrepancyCash !== 0) {
        discBlock.style.display = 'block';
        discValue.textContent = formatMoney(Math.abs(discrepancyCash));
        if (discrepancyCash > 0) {
            discBlock.style.background = '#e8f5e9';
            discBlock.style.borderColor = '#4caf50';
            discBlock.querySelector('h4').style.color = '#2e7d32';
            discText.textContent = '✅ ИЗЛИШЕК (в кассе больше, чем должно быть)';
        } else {
            discBlock.style.background = '#ffebee';
            discBlock.style.borderColor = '#f44336';
            discBlock.querySelector('h4').style.color = '#c62828';
            discText.textContent = '❌ НЕДОСТАЧА (в кассе меньше, чем должно быть)';
        }
    } else if (discrepancyCash === 0) {
        discBlock.style.display = 'block';
        discBlock.style.background = '#e8f5e9';
        discBlock.style.borderColor = '#4caf50';
        discBlock.querySelector('h4').style.color = '#2e7d32';
        discValue.textContent = '0';
        discText.textContent = '✅ ВСЁ СХОДИТСЯ!';
    } else {
        discBlock.style.display = 'none';
    }
}

function closeWjCloseModal() {
    document.getElementById('wj-close-modal').classList.remove('active');
}

async function submitWjClose() {
    const btn = document.querySelector('#wj-close-modal .btn-primary');
    setButtonLoading(btn, true, 'Сохранение…');

    // Простые поля
    const revenueTotal = document.getElementById('wj-revenue-total').value;
    const terminalActual = document.getElementById('wj-terminal-actual').value;
    const eveningCash = document.getElementById('wj-evening-cash').value;
    const closeNote = document.getElementById('wj-close-note').value;
    const acquiringFile = document.getElementById('wj-acquiring-file').files[0];
    const zreportFile = document.getElementById('wj-zreport-file').files[0];
    const month = document.getElementById('wj-month')?.value || currentMonth;
    const year = document.getElementById('wj-year')?.value || currentYear;

    let acquiringFileId = null, zReportFileId = null;

    try {
        // Загрузка файлов
        if (acquiringFile) {
            const fd = new FormData();
            fd.append('file', acquiringFile);
            fd.append('year', year); fd.append('month', month); fd.append('day', wjShifts.find(x => Number(x.id) === Number(wjCurrentShiftId))?.day || new Date().getDate());
            const r = await fetch('/api/files/upload', { method: 'POST', body: fd, });
            const d = await r.json().catch(() => ({}));
            if (r.ok && d.file_id) acquiringFileId = d.file_id;
       }
        if (zreportFile) {
            const fd = new FormData();
            fd.append('file', zreportFile);
            fd.append('year', year); fd.append('month', month); fd.append('day', wjShifts.find(x => Number(x.id) === Number(wjCurrentShiftId))?.day || new Date().getDate());
            const r = await fetch('/api/files/upload', { method: 'POST', body: fd, });
            const d = await r.json().catch(() => ({}));
            if (r.ok && d.file_id) zReportFileId = d.file_id;
       }

        // Отправка данных закрытия смены
        // closing_sum = наличные в кассе вечером (это сумма закрытия)
        const closingSum = eveningCash ? parseFloat(eveningCash) : 0;
        
        const res = await fetch(`/api/work-journal/close`, { method: 'POST',
            headers: { 'Content-Type': 'application/json' },

            body: JSON.stringify({
                shift_id: wjCurrentShiftId,
                closing_sum: closingSum,
                revenue_total: revenueTotal ? parseFloat(revenueTotal) : null,
                acquiring_amount: 0,
                terminal_actual: terminalActual ? parseFloat(terminalActual) : null,
                evening_cash: eveningCash ? parseFloat(eveningCash) : null,
                evening_cashless: 0,
                notes: closeNote || null,
                acquiring_file_id: acquiringFileId,
                z_report_file_id: zReportFileId
           })
       });

        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeWjCloseModal();
            const detailEl = document.getElementById('work-journal-detail');
            if (detailEl && detailEl.style.display !== 'none') showWjDetail(wjCurrentShiftId);
            else loadWorkJournal();
            showToast('Смена закрыта', 'success');
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   } catch (e) {
        console.error('Ошибка закрытия смены:', e);
        showToast('Ошибка сети при закрытии смены: ' + e.message, 'error');
   } finally {
        setButtonLoading(btn, false);
   }
}

let wjEditShiftId = null;

async function openWjEditShiftModal(shiftId) {
    wjEditShiftId = shiftId;
    const res = await fetch(`/api/work-journal/shift/${shiftId}`, { credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (data.status !== 'success' || !data.shift) {
        showToast('Ошибка загрузки смены', 'error');
        return;
   }
    const s = data.shift;
    document.getElementById('wj-edit-shift-caption').textContent = `Смена ${s.day}.${s.month}.${s.year}${s.full_name ? ' · ' + s.full_name : ''}`;
    const userSel = document.getElementById('wj-edit-user-id');
    userSel.innerHTML = '';
    const usersRes = await fetch('/api/users');
    const usersData = await usersRes.json().catch(() => ({}));
    (usersData.users || []).filter(u => u.role !== 'admin').forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.full_name || u.username;
        if (Number(u.id) === Number(s.user_id)) opt.selected = true;
        userSel.appendChild(opt);
   });
    document.getElementById('wj-edit-morning-cash').value = s.morning_cash != null ? s.morning_cash : '';
    document.getElementById('wj-edit-evening-cash').value = s.evening_cash != null ? s.evening_cash : '';
    document.getElementById('wj-edit-evening-cashless').value = s.evening_cashless != null ? s.evening_cashless : '';
    document.getElementById('wj-edit-revenue-total').value = s.revenue_total != null ? s.revenue_total : '';
    document.getElementById('wj-edit-acquiring-amount').value = s.acquiring_amount != null ? s.acquiring_amount : '';
    document.getElementById('wj-edit-close-note').value = s.close_note || '';
    document.getElementById('wj-edit-shift-modal').classList.add('active');
}

function closeWjEditShiftModal() {
    document.getElementById('wj-edit-shift-modal').classList.remove('active');
    wjEditShiftId = null;
}

async function deleteWjShift(shiftId) {
    confirmModal('Удалить смену полностью? Все записи за этот день будут удалены. Отменить нельзя.', async function() {
        const res = await fetch(`/api/work-journal/shift/${shiftId}`, { method: 'DELETE', });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            hideWorkJournalDetail();
            showToast('Смена удалена', 'success');
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   });
}

async function submitWjEditShift() {
    if (!wjEditShiftId) return;
    const btn = document.querySelector('#wj-edit-shift-modal .btn-primary');
    setButtonLoading(btn, true, 'Сохранение…');
    try {
        const v = (id) => { const el = document.getElementById(id); const val = el.value.trim(); return val === '' ? null : parseFloat(val); };
        const userIdEl = document.getElementById('wj-edit-user-id');
        const userId = userIdEl && userIdEl.value ? parseInt(userIdEl.value, 10) : undefined;
        const body = {
            morning_cash: v('wj-edit-morning-cash'),
            evening_cash: v('wj-edit-evening-cash'),
            evening_cashless: v('wj-edit-evening-cashless'),
            revenue_total: v('wj-edit-revenue-total'),
            acquiring_amount: v('wj-edit-acquiring-amount'),
            close_note: document.getElementById('wj-edit-close-note').value.trim() || null
       };
        if (userId !== undefined) body.user_id = userId;
        const res = await fetch(`/api/work-journal/shift/${wjEditShiftId}`, { method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            
            body: JSON.stringify(body)
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeWjEditShiftModal();
            showWjDetail(wjCurrentShiftId);
            showToast('Смена сохранена', 'success');
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   } finally {
        setButtonLoading(btn, false);
   }
}

let wjEditEntryId = null;

function openWjEditEntryModal(entryId) {
    const e = wjEditEntryCache[entryId];
    if (!e) return;
    wjEditEntryId = entryId;
    document.getElementById('wj-edit-entry-kind').value = e.kind || 'Внесла в кассу';
    document.getElementById('wj-edit-entry-amount').value = e.amount != null ? e.amount : '';
    document.getElementById('wj-edit-entry-note').value = e.note || '';
    document.getElementById('wj-edit-entry-modal').classList.add('active');
}

function closeWjEditEntryModal() {
    document.getElementById('wj-edit-entry-modal').classList.remove('active');
    wjEditEntryId = null;
}

async function submitWjEditEntry() {
    if (!wjEditEntryId) return;
    const btn = document.querySelector('#wj-edit-entry-modal .btn-primary');
    setButtonLoading(btn, true, 'Сохранение…');
    try {
        const amountVal = document.getElementById('wj-edit-entry-amount').value.trim();
        const res = await fetch(`/api/work-journal/entry/${wjEditEntryId}`, { method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            
            body: JSON.stringify({
                kind: document.getElementById('wj-edit-entry-kind').value,
                amount: amountVal === '' ? null : parseFloat(amountVal),
                note: document.getElementById('wj-edit-entry-note').value.trim() || null
           })
       });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'success') {
            closeWjEditEntryModal();
            if (wjCurrentShiftId != null) {
                showWjDetail(wjCurrentShiftId);
           } else {
                loadWorkJournal();
           }
            showToast('Запись сохранена', 'success');
       } else {
            showToast('Ошибка: ' + (data.message || res.status), 'error');
       }
   } finally {
        setButtonLoading(btn, false);
   }
}

async function deleteWjEntry(entryId) {
    const entry = wjEditEntryCache[entryId];
    const shiftId = entry && entry.shift_id ? entry.shift_id : wjCurrentShiftId;
    confirmModal('Удалить запись? Отменить нельзя.', async function() {
        try {
            const res = await fetch(`/api/work-journal/entry/${entryId}`, {
                method: 'DELETE',
                
           });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                showToast('Запись удалена', 'success');
                if (shiftId != null) {
                    showWjDetail(shiftId);
               } else {
                    loadWorkJournal();
               }
           } else {
                showToast('Ошибка: ' + (data.message || res.status), 'error');
           }
       } catch (e) {
            console.error(e);
            showToast('Ошибка удаления записи', 'error');
       }
   });
}

// ==================== Сводка зарплат, статистика, штрафы/бонусы ====================

const MONTHS_RU = ['','Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

function initSalarySelectors() {
    const mSel = document.getElementById('salary-month');
    const ySel = document.getElementById('salary-year');
    if (!mSel || !ySel || mSel.options.length > 0) return;
    const now = new Date();
    for (let m = 1; m <= 12; m++) {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = MONTHS_RU[m];
        if (m === now.getMonth() + 1) opt.selected = true;
        mSel.appendChild(opt);
   }
    for (let y = now.getFullYear() - 1; y <= now.getFullYear() + 1; y++) {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        if (y === now.getFullYear()) opt.selected = true;
        ySel.appendChild(opt);
   }
}

async function loadSalarySummary() {
    const mSel = document.getElementById('salary-month');
    const ySel = document.getElementById('salary-year');
    if (!mSel || !ySel) return;
    const year = ySel.value;
    const month = mSel.value;
    const container = document.getElementById('salary-summary-table');
    const statsContainer = document.getElementById('employee-stats-table');
    try {
        const [salRes, statsRes] = await Promise.all([
            fetch(`/api/salary-summary?year=${year}&month=${month}`, { credentials: 'include' }),
            fetch(`/api/employee-stats?year=${year}&month=${month}`, { credentials: 'include' })
        ]);
        const salData = await salRes.json();
        const statsData = await statsRes.json();
        if (salData.status === 'success' && salData.data.length) {
            let html = `<div class="salary-table-wrapper" style="overflow-x:auto;"><table class="salary-table">
                <thead><tr>
                    <th>Сотрудник</th><th>Смен</th><th>Выручка</th><th>Начислено</th><th>Штрафы/Бонусы</th><th>Взято</th><th>Остаток</th>
                </tr></thead><tbody>`;
            salData.data.forEach(r => {
                const balClass = r.balance < 0 ? ' style="color:var(--danger,#dc2626);font-weight:600;"' : (r.balance > 0 ? ' style="color:var(--success,#16a34a);font-weight:600;"' : '');
                const adjClass = r.adjustments < 0 ? ' style="color:var(--danger,#dc2626);"' : (r.adjustments > 0 ? ' style="color:var(--success,#16a34a);"' : '');
                html += `<tr>
                    <td><strong>${escapeHtml(r.full_name)}</strong></td>
                    <td>${r.days_worked}</td>
                    <td>${formatMoney(r.total_revenue)}</td>
                    <td>${formatMoney(r.salary_due)}</td>
                    <td${adjClass}>${r.adjustments >= 0 ? '+' : ''}${formatMoney(r.adjustments)}</td>
                    <td>${formatMoney(r.salary_taken)}</td>
                    <td${balClass}>${formatMoney(r.balance)}</td>
                </tr>`;
           });
            html += '</tbody></table></div>';
            container.innerHTML = html;
       } else {
            container.innerHTML = '<p class="text-muted">Нет данных за этот месяц.</p>';
       }
        if (statsData.status === 'success' && statsData.data.length) {
            let html = `<p class="text-muted" style="font-size:12px; margin-bottom:8px;">Норма: открытие до 9:00, закрытие в 19:00.</p>
                <div class="salary-table-wrapper" style="overflow-x:auto;"><table class="salary-table">
                <thead><tr>
                    <th>Сотрудник</th><th>Смен</th><th>Закрыто</th><th>Ср. выручка</th><th>Общ. выручка</th><th title="Открытие после 9:00">Опоздания</th><th title="Закрытие до 19:00">Раннее закр.</th><th title="Закрытие после 19:00">Позднее закр.</th><th>Расхождения</th>
                </tr></thead><tbody>`;
            statsData.data.forEach(r => {
                const lateClass = r.late_openings > 0 ? ' style="color:var(--danger,#dc2626);font-weight:600;"' : '';
                const earlyClass = (r.early_closings || 0) > 0 ? ' style="color:var(--danger,#dc2626);font-weight:600;"' : '';
                const lateCloseClass = (r.late_closings || 0) > 0 ? ' style="color:var(--warning,#d97706);font-weight:600;"' : '';
                const discClass = r.cash_discrepancies > 0 ? ' style="color:var(--danger,#dc2626);font-weight:600;"' : '';
                html += `<tr>
                    <td><strong>${escapeHtml(r.full_name)}</strong></td>
                    <td>${r.shifts_total}</td>
                    <td>${r.shifts_closed}</td>
                    <td>${formatMoney(r.avg_revenue)}</td>
                    <td>${formatMoney(r.total_revenue)}</td>
                    <td${lateClass}>${r.late_openings}</td>
                    <td${earlyClass}>${r.early_closings || 0}</td>
                    <td${lateCloseClass}>${r.late_closings || 0}</td>
                    <td${discClass}>${r.cash_discrepancies}</td>
                </tr>`;
           });
            html += '</tbody></table></div>';
            statsContainer.innerHTML = html;
       } else {
            statsContainer.innerHTML = '<p class="text-muted">Нет данных.</p>';
       }
   } catch (e) {
        container.innerHTML = '<p class="text-muted">Ошибка загрузки.</p>';
   }
}

// ---------- Штрафы и бонусы ----------

async function loadAdjustments() {
    const container = document.getElementById('adjustments-list');
    if (!container) return;
    const mSel = document.getElementById('salary-month');
    const ySel = document.getElementById('salary-year');
    const year = ySel ? ySel.value : new Date().getFullYear();
    const month = mSel ? mSel.value : (new Date().getMonth() + 1);
    try {
        const res = await fetch(`/api/salary-adjustments?year=${year}&month=${month}`, { credentials: 'include' });
        const data = await res.json();
        if (data.status === 'success' && data.data.length) {
            let html = '<div class="adjustments-items">';
            data.data.forEach(a => {
                const sign = a.amount >= 0 ? '+' : '';
                const cls = a.amount >= 0 ? 'adj-bonus' : 'adj-fine';
                html += `<div class="adjustment-item ${cls}">
                    <span class="adj-amount">${sign}${formatMoney(a.amount)}</span>
                    <span class="adj-name">${escapeHtml(a.full_name || a.username)}</span>
                    <span class="adj-reason">${escapeHtml(a.reason)}</span>
                    <button type="button" class="btn btn-sm" onclick="deleteAdjustment(${a.id})" title="Удалить">✕</button>
                </div>`;
           });
            html += '</div>';
            container.innerHTML = html;
       } else {
            container.innerHTML = '<p class="text-muted">Нет штрафов/бонусов за этот месяц.</p>';
       }
   } catch (e) {
        container.innerHTML = '<p class="text-muted">Ошибка загрузки.</p>';
   }
}

function openAdjustmentModal() {
    const sel = document.getElementById('adj-user');
    sel.innerHTML = '';
    fetch('/api/users', { credentials: 'include' }).then(r => r.json()).then(data => {
        (data.users || []).filter(u => u.role !== 'admin').forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = u.full_name || u.username;
            sel.appendChild(opt);
       });
   });
    document.getElementById('adj-amount').value = '';
    document.getElementById('adj-reason').value = '';
    document.getElementById('adjustment-modal').classList.add('active');
}

function closeAdjustmentModal() {
    document.getElementById('adjustment-modal').classList.remove('active');
}

async function submitAdjustment() {
    const userId = document.getElementById('adj-user').value;
    const amount = parseFloat(document.getElementById('adj-amount').value);
    const reason = document.getElementById('adj-reason').value.trim();
    if (!userId || isNaN(amount) || !reason) {
        showToast('Заполните все поля', 'error');
        return;
   }
    const mSel = document.getElementById('salary-month');
    const ySel = document.getElementById('salary-year');
    const year = ySel ? parseInt(ySel.value) : new Date().getFullYear();
    const month = mSel ? parseInt(mSel.value) : (new Date().getMonth() + 1);
    const res = await fetch('/api/salary-adjustments', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ user_id: parseInt(userId), year, month, amount, reason })
   });
    const data = await res.json();
    if (data.status === 'success') {
        closeAdjustmentModal();
        showToast(amount >= 0 ? 'Бонус добавлен' : 'Штраф добавлен', 'success');
        loadAdjustments();
        loadSalarySummary();
   } else {
        showToast(data.message || 'Ошибка', 'error');
   }
}

async function deleteAdjustment(id) {
    confirmModal('Удалить эту запись?', async function() {
        const res = await fetch('/api/salary-adjustments/' + id, { method: 'DELETE', });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Удалено', 'success');
            loadAdjustments();
            loadSalarySummary();
       }
   });
}

// ---------- Шаблоны графика ----------

function toggleTemplateMode() {
    const mode = document.getElementById('tpl-mode').value;
    document.getElementById('tpl-weekdays-block').style.display = mode === 'weekdays' ? '' : 'none';
    document.getElementById('tpl-rotation-block').style.display = mode === 'rotation' ? '' : 'none';
}

function openScheduleTemplateModal() {
    const userSel = document.getElementById('tpl-user');
    const taskSel = document.getElementById('tpl-task');
    userSel.innerHTML = '';
    taskSel.innerHTML = '';
    fetch('/api/users', { credentials: 'include' }).then(r => r.json()).then(data => {
        (data.users || []).filter(u => u.role !== 'admin').forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = u.full_name || u.username;
            userSel.appendChild(opt);
       });
   });
    fetch('/api/tasks', { credentials: 'include' }).then(r => r.json()).then(data => {
        (data.tasks || []).forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.name;
            taskSel.appendChild(opt);
       });
   });
    document.querySelectorAll('#tpl-weekdays-block input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.getElementById('tpl-work-days').value = 2;
    document.getElementById('tpl-off-days').value = 2;
    document.getElementById('tpl-start-day').value = 1;
    document.getElementById('tpl-mode').value = 'weekdays';
    toggleTemplateMode();
    document.getElementById('schedule-template-modal').classList.add('active');
}

function closeScheduleTemplateModal() {
    document.getElementById('schedule-template-modal').classList.remove('active');
}

async function submitScheduleTemplate() {
    const userId = document.getElementById('tpl-user').value;
    const taskId = document.getElementById('tpl-task').value;
    const mode = document.getElementById('tpl-mode').value;
    if (!userId) { showToast('Выберите сотрудника', 'error'); return; }
    const body = {
        user_id: parseInt(userId),
        year: currentYear,
        month: currentMonth,
        task_ids: taskId ? [parseInt(taskId)] : [],
        mode: mode
   };
    if (mode === 'weekdays') {
        const weekdays = [];
        document.querySelectorAll('#tpl-weekdays-block input[type="checkbox"]:checked').forEach(cb => weekdays.push(parseInt(cb.value)));
        if (!weekdays.length) { showToast('Выберите дни недели', 'error'); return; }
        body.weekdays = weekdays;
   } else {
        body.work_days = parseInt(document.getElementById('tpl-work-days').value) || 2;
        body.off_days = parseInt(document.getElementById('tpl-off-days').value) || 2;
        body.start_day = parseInt(document.getElementById('tpl-start-day').value) || 1;
   }
    const res = await fetch('/api/schedule/template', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify(body)
   });
    const data = await res.json();
    if (data.status === 'success') {
        closeScheduleTemplateModal();
        showToast(`График заполнен: ${data.filled} дней`, 'success');
        loadSchedule();
   } else {
        showToast(data.message || 'Ошибка', 'error');
   }
}

// ---------- Обновление системы ----------

function openUpdatePanel() {
    document.getElementById('update-modal').style.display = 'block';
}

function closeUpdatePanel() {
    document.getElementById('update-modal').style.display = 'none';
    document.getElementById('update-file-input').value = '';
    document.getElementById('update-progress').style.display = 'none';
}

async function uploadUpdateFile() {
    const fileInput = document.getElementById('update-file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Выберите файл обновления (.exe)', 'error');
        return;
   }
    
    if (!file.name.endsWith('.exe')) {
        showToast('Выберите файл с расширением .exe', 'error');
        return;
   }
    
    if (!confirm('Внимание! После загрузки обновления программа будет перезапущена.\n\nПродолжить?')) {
        return;
   }
    
    const progressDiv = document.getElementById('update-progress');
    const progressBar = document.getElementById('update-progress-bar');
    const statusText = document.getElementById('update-status');
    
    progressDiv.style.display = 'block';
    progressBar.style.width = '10%';
    statusText.textContent = 'Подготовка файла...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        progressBar.style.width = '30%';
        statusText.textContent = 'Загрузка на сервер...';
        
        const response = await fetch('/api/system/update', {
            method: 'POST',
            
            body: formData
       });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            progressBar.style.width = '100%';
            statusText.textContent = '✅ Обновление успешно загружено! Сервер устанавливает...';
            
            setTimeout(() => {
                closeUpdatePanel();
                showToast('Обновление загружено! Сервер перезапускается...', 'success');
           }, 2000);
       } else {
            progressBar.style.width = '100%';
            statusText.textContent = '❌ Ошибка: ' + (data.message || 'Неизвестная ошибка');
            showToast('Ошибка обновления: ' + (data.message || ''), 'error');
       }
   } catch (error) {
        progressBar.style.width = '100%';
        statusText.textContent = '❌ Ошибка соединения: ' + error.message;
        showToast('Ошибка соединения с сервером', 'error');
   }
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const updateModal = document.getElementById('update-modal');
    if (event.target == updateModal) {
        closeUpdatePanel();
    }
}

// Конец файла 

// ========================================
// АНАЛИТИКА И ДАШБОРДЫ (Chart.js)
// ========================================

function initAnalyticsCharts() {
    // Загрузка графиков при открытии страницы аналитики
    loadEmployeeLoadChart();
    loadDynamicsChart();
    loadHeatmapChart();
    loadSummaryStats();
}

async function loadEmployeeLoadChart() {
    const canvas = document.getElementById('chart-employee-load');
    if (!canvas) return;
    
    try {
        const res = await fetch(`/api/analytics/employee-load?year=${currentYear}&month=${currentMonth}`);
        const data = await res.json();
        if (data.status !== 'success') return;
        
        if (window._employeeLoadChart) window._employeeLoadChart.destroy();
        
        window._employeeLoadChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                plugins: {
                    title: { display: true, text: 'Загрузка сотрудников по дням недели' },
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Количество смен' } }
                }
            }
        });
    } catch (e) {
        console.error('Error loading employee load chart:', e);
    }
}

async function loadDynamicsChart() {
    const canvas = document.getElementById('chart-dynamics');
    if (!canvas) return;
    
    try {
        const res = await fetch(`/api/analytics/dynamics?year=${currentYear}&month=${currentMonth}`);
        const data = await res.json();
        if (data.status !== 'success') return;
        
        if (window._dynamicsChart) window._dynamicsChart.destroy();
        
        window._dynamicsChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                plugins: {
                    title: { display: true, text: 'Динамика операций по дням' },
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Количество' } }
                }
            }
        });
    } catch (e) {
        console.error('Error loading dynamics chart:', e);
    }
}

async function loadHeatmapChart() {
    const canvas = document.getElementById('chart-heatmap');
    if (!canvas) return;
    
    try {
        const res = await fetch(`/api/analytics/heatmap?year=${currentYear}&month=${currentMonth}`);
        const data = await res.json();
        if (data.status !== 'success') return;
        
        if (window._heatmapChart) window._heatmapChart.destroy();
        
        // Создаём тепловую карту как матрицу
        const matrixData = [];
        for (let i = 0; i < data.weekdays.length; i++) {
            for (let j = 0; j < data.hours.length; j++) {
                matrixData.push({
                    x: j,
                    y: i,
                    v: data.matrix[i][j]
                });
            }
        }
        
        window._heatmapChart = new Chart(canvas, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Активность',
                    data: matrixData,
                    backgroundColor(ctx) {
                        const value = ctx.dataset.data[ctx.dataIndex].v;
                        const max = data.max_value || 1;
                        const alpha = Math.min(value / max, 1);
                        return `rgba(99, 102, 241, ${alpha})`;
                    },
                    borderColor: '#fff',
                    borderWidth: 1,
                    width: ({chart}) => (chart.chartArea || {}).width / data.hours.length - 1,
                    height: ({chart}) => (chart.chartArea || {}).height / data.weekdays.length - 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: { display: true, text: 'Тепловая карта активности (день × час)' },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title(ctx) {
                                return `${data.weekdays[ctx[0].parsed.y]}, ${ctx[0].parsed.x}:00`;
                            },
                            label(ctx) {
                                return `Операций: ${ctx.parsed.v}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        offset: true,
                        ticks: { stepSize: 2 },
                        title: { display: true, text: 'Час дня' }
                    },
                    y: {
                        type: 'linear',
                        offset: true,
                        ticks: {
                            callback(value) { return data.weekdays[value]; }
                        },
                        title: { display: true, text: 'День недели' }
                    }
                }
            }
        });
    } catch (e) {
        console.error('Error loading heatmap chart:', e);
    }
}

async function loadSummaryStats() {
    const container = document.getElementById('analytics-summary');
    if (!container) return;
    
    try {
        const res = await fetch('/api/analytics/summary');
        const data = await res.json();
        if (data.status !== 'success') return;
        
        const s = data.summary;
        container.innerHTML = `
            <div class="stats-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px;">
                <div class="stat-card">
                    <div class="stat-value">${s.total_employees}</div>
                    <div class="stat-label">👥 Сотрудников</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${s.total_shifts}</div>
                    <div class="stat-label">📅 Смен</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${s.total_operations}</div>
                    <div class="stat-label">📦 Операций</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${s.total_sales}</div>
                    <div class="stat-label">💰 Продаж</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${formatCurrency(s.total_revenue)}</div>
                    <div class="stat-label">💵 Выручка</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${s.total_writeoffs}</div>
                    <div class="stat-label">🗑️ Списаний</div>
                </div>
            </div>
        `;
    } catch (e) {
        console.error('Error loading summary stats:', e);
    }
}

function formatCurrency(value) {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value);
}

// ========================================
// ЭКСПОРТ ОТЧЁТОВ
// ========================================

async function exportScheduleReport(format) {
    try {
        const res = await fetch('/api/export/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                format: format,
                year: currentYear,
                month: currentMonth
            })
        });
        
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `schedule_${currentYear}_${String(currentMonth).padStart(2, '0')}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast(`График экспортирован в ${format.toUpperCase()}`, 'success');
        } else {
            const data = await res.json();
            showToast(data.error || 'Ошибка экспорта', 'error');
        }
    } catch (e) {
        showToast('Ошибка экспорта: ' + e.message, 'error');
    }
}

async function exportRevisionReport(format, revisionId) {
    try {
        const res = await fetch('/api/export/revision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                format: format,
                revision_id: revisionId || null
            })
        });
        
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `revision_${revisionId || 'all'}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast(`Отчёт экспортирован в ${format.toUpperCase()}`, 'success');
        } else {
            const data = await res.json();
            showToast(data.error || 'Ошибка экспорта', 'error');
        }
    } catch (e) {
        showToast('Ошибка экспорта: ' + e.message, 'error');
    }
}

// ========================================
// NOTIFICATION CENTER
// ========================================

let notificationCheckInterval = null;

function toggleNotificationPanel() {

    const panel = document.getElementById('notification-panel');
    if (!panel) return;
    
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        loadNotifications();
    }
}

async function loadNotifications() {
    const body = document.getElementById('notification-panel-body');
    if (!body) return;
    
    body.innerHTML = '<div class="notification-loading">Загрузка...</div>';
    
    try {
        const response = await fetch('/api/notifications/list', { credentials: 'include' });
        const data = await response.json();
        
        if (data.status === 'success') {
            updateNotificationBadge(data.unread_count);
            
            if (data.notifications.length === 0) {
                body.innerHTML = '<div class="notification-empty">Нет уведомлений</div>';
                return;
            }
            
            body.innerHTML = data.notifications.map(n => {
                const typeIcon = {
                    'info': 'ℹ️',
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'reminder': '📢',
                    'task': '📋',
                    'chat': '💬',
                    'revision': '📦'
                };
                const icon = typeIcon[n.type] || 'ℹ️';
                const timeAgo = getTimeAgo(n.created_at);
                
                return `
                    <div class="notification-item ${n.is_read ? '' : 'notification-unread'}" onclick="${n.link ? `window.location.href='${n.link}'` : ''}">
                        <div class="notification-item-icon">${icon}</div>
                        <div class="notification-item-content">
                            <div class="notification-item-title">${escapeHtml(n.title)}</div>
                            ${n.message ? `<div class="notification-item-message">${escapeHtml(n.message)}</div>` : ''}
                            <div class="notification-item-time">${timeAgo}</div>
                        </div>
                        <div class="notification-item-actions">
                            ${!n.is_read ? `<button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); markNotificationRead(${n.id})" title="Отметить прочитанным">✅</button>` : ''}
                            <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteNotification(${n.id})" title="Удалить">🗑️</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (e) {
        body.innerHTML = '<div class="notification-error">Ошибка загрузки</div>';
    }
}

async function markNotificationRead(id) {
    try {
        await fetch('/api/notifications/read/' + id, { method: 'POST', credentials: 'include' });
        loadNotifications();
    } catch (e) {
        console.error('Error marking notification read:', e);
    }
}

async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/read-all', { method: 'POST', credentials: 'include' });
        loadNotifications();
        updateNotificationBadge(0);
        showToast('Все уведомления отмечены прочитанными', 'success');
    } catch (e) {
        console.error('Error marking all read:', e);
    }
}

async function deleteNotification(id) {
    try {
        await fetch('/api/notifications/delete/' + id, { method: 'DELETE', credentials: 'include' });
        loadNotifications();
    } catch (e) {
        console.error('Error deleting notification:', e);
    }
}

async function clearAllNotifications() {
    if (!confirm('Очистить все уведомления?')) return;
    try {
        await fetch('/api/notifications/clear', { method: 'POST', credentials: 'include' });
        loadNotifications();
        updateNotificationBadge(0);
        showToast('Все уведомления удалены', 'success');
    } catch (e) {
        console.error('Error clearing notifications:', e);
    }
}

async function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

async function checkUnreadNotifications() {
    try {
        const response = await fetch('/api/notifications/unread-count', { credentials: 'include' });
        const data = await response.json();
        if (data.status === 'success') {
            updateNotificationBadge(data.count);
        }
    } catch (e) {
        // Silent fail
    }
}

function getTimeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'только что';
    if (diff < 3600) return Math.floor(diff / 60) + ' мин назад';
    if (diff < 86400) return Math.floor(diff / 3600) + ' ч назад';
    if (diff < 172800) return 'вчера';
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
}

// Инициализация проверки уведомлений
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем непрочитанные каждые 30 секунд
    checkUnreadNotifications();
    notificationCheckInterval = setInterval(checkUnreadNotifications, 30000);
    
    // Закрытие панели при клике вне её
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('notification-panel');
        const bell = document.getElementById('notification-bell-wrap');
        if (panel && panel.style.display === 'block' && !panel.contains(e.target) && !bell.contains(e.target)) {
            panel.style.display = 'none';
        }
    });
});

// ========================================
// УМНЫЙ КОНТРОЛЬ (Smart Control)
// ========================================

/** Загрузка баннера умного контроля на странице ревизии */
async function loadSmartControlBanner() {
    const banner = document.getElementById('smart-control-banner');
    if (!banner) return;
    
    try {
        const res = await fetch('/api/smart-revision/control-banner');
        const data = await res.json();
        
        if (data.status !== 'success') {
            banner.style.display = 'none';
            return;
        }
        
        const critical = data.critical || [];
        const warnings = data.warnings || [];
        const noMovement = data.no_movement || [];
        
        if (critical.length === 0 && warnings.length === 0 && noMovement.length === 0) {
            banner.style.display = 'none';
            return;
        }
        
        let html = '<div class="smart-control-banner-inner">';
        
        if (critical.length > 0) {
            html += '<div class="smart-control-section critical">';
            html += '<div class="smart-control-icon">🔴</div>';
            html += '<div class="smart-control-content">';
            html += '<div class="smart-control-title">Критичные товары (≤ 7 дней до истечения срока):</div>';
            html += '<ul>' + critical.map(item => '<li>' + escapeHtml(item.name || item) + '</li>').join('') + '</ul>';
            html += '</div></div>';
        }
        
        if (warnings.length > 0) {
            html += '<div class="smart-control-section warning">';
            html += '<div class="smart-control-icon">🟡</div>';
            html += '<div class="smart-control-content">';
            html += '<div class="smart-control-title">Предупреждения (≤ 30 дней до истечения срока):</div>';
            html += '<ul>' + warnings.map(item => '<li>' + escapeHtml(item.name || item) + '</li>').join('') + '</ul>';
            html += '</div></div>';
        }
        
        if (noMovement.length > 0) {
            html += '<div class="smart-control-section info">';
            html += '<div class="smart-control-icon">ℹ️</div>';
            html += '<div class="smart-control-content">';
            html += '<div class="smart-control-title">Товары без движений (более 30 дней):</div>';
            html += '<ul>' + noMovement.map(item => '<li>' + escapeHtml(item.name || item) + '</li>').join('') + '</ul>';
            html += '</div></div>';
        }
        
        html += '</div>';
        banner.innerHTML = html;
        banner.style.display = 'block';
        
    } catch (e) {
        console.error('Ошибка загрузки баннера умного контроля:', e);
        banner.style.display = 'none';
    }
}

/** Показать предупреждения при открытии страницы ревизии */
function showShiftWarnings() {
    const warnings = document.getElementById('shift-warnings');
    if (!warnings) return;
    
    // Проверяем, есть ли активные предупреждения
    const criticalItems = document.querySelectorAll('.smart-control-section.critical li');
    const warningItems = document.querySelectorAll('.smart-control-section.warning li');
    
    if (criticalItems.length > 0 || warningItems.length > 0) {
        warnings.style.display = 'block';
        let msg = '';
        if (criticalItems.length > 0) {
            msg += '🔴 Критичных товаров: ' + criticalItems.length + '\n';
        }
        if (warningItems.length > 0) {
            msg += '🟡 Предупреждений: ' + warningItems.length;
        }
        warnings.querySelector('.warnings-text').textContent = msg;
    } else {
        warnings.style.display = 'none';
    }
}

/** Обновление панели акционных ценников */
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

/** Инициализация страницы ревизии */
function initRevisionPage() {
    // Загружаем баннер умного контроля
    loadSmartControlBanner();
    
    // Показываем предупреждения
    setTimeout(() => {
        showShiftWarnings();
    }, 500);
    
    // Наблюдаем за изменениями в панели акций
    const promotionPanel = document.getElementById('promotion-panel');
    if (promotionPanel) {
        const observer = new MutationObserver(() => {
            updatePromotionPanel();
        });
        observer.observe(promotionPanel, { childList: true, subtree: true });
    }
    
    // Наблюдаем за появлением страницы ревизии
    const revisionPage = document.getElementById('page-revision');
    if (revisionPage) {
        const pageObserver = new MutationObserver(() => {
            if (revisionPage.classList.contains('active')) {
                loadSmartControlBanner();
                setTimeout(() => showShiftWarnings(), 500);
            }
        });
        pageObserver.observe(revisionPage, { attributes: true, attributeFilter: ['class'] });
    }
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRevisionPage);
} else {
    initRevisionPage();
}
