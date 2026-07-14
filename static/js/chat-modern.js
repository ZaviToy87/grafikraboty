/* =====================================================
   СОВРЕМЕННЫЙ ЧАТ - v2.0
   Группировка, сетка фото, автопрокрутка
   ===================================================== */

class ModernChat {
  constructor() {
    this.messages = [];
    this.currentTopic = 3; // VK чат по умолчанию
    this.currentUser = null;
    this.photoModal = null;
    this.currentPhotos = [];
    this.currentPhotoIndex = 0;
    
    this.init();
  }
  
  init() {
    this.currentUser = window.currentUser || { id: 1, username: 'admin' };
    this.bindEvents();
    this.loadMessages();
  }
  
  bindEvents() {
    // Отправка по Enter (Ctrl+Enter для новой строки)
    const input = document.getElementById('chat-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.ctrlKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      
      // Автоувеличение высоты
      input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      });
    }
    
    // Кнопка отправки
    const sendBtn = document.getElementById('send-message-btn');
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.sendMessage());
    }
    
    // Кнопка скролла вниз
    const scrollBtn = document.getElementById('scroll-to-bottom');
    if (scrollBtn) {
      scrollBtn.addEventListener('click', () => this.scrollToBottom());
    }
    
    // Скролл для показа кнопки
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.addEventListener('scroll', () => {
        this.updateScrollButton();
      });
    }
    
    // Закрытие модального окна
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closePhotoModal();
      }
    });
  }
  
  async loadMessages() {
    try {
      const response = await fetch(`/api/chat/messages?limit=100&topic_id=${this.currentTopic}`);
      const data = await response.json();
      this.messages = data.messages || [];
      this.renderMessages();
    } catch (error) {
      console.error('Ошибка загрузки сообщений:', error);
    }
  }
  
  renderMessages() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Группировка сообщений
    const groups = this.groupMessages(this.messages);
    
    groups.forEach(group => {
      const groupEl = this.createMessageGroup(group);
      container.appendChild(groupEl);
    });
    
    // Прокрутка вниз
    this.scrollToBottom();
    this.updateScrollButton();
  }
  
  groupMessages(messages) {
    const groups = [];
    let currentGroup = null;
    let lastDate = null;
    
    messages.forEach((msg, index) => {
      const msgDate = this.getMessageDate(msg.created_at);
      const isOutgoing = msg.user_id === this.currentUser.id;
      
      // Добавляем разделитель даты
      if (msgDate !== lastDate) {
        groups.push({ type: 'date', date: msgDate, label: this.formatDateLabel(msgDate) });
        lastDate = msgDate;
        currentGroup = null;
      }
      
      // Для VK используем vk_conversation_id для группировки
      // Все сообщения с одинаковым vk_conversation_id идут в одну группу
      const convId = msg.vk_conversation_id || msg.conversation_message_id || msg.id;
      const prevMsg = messages[index - 1];
      const prevConvId = prevMsg?.vk_conversation_id || prevMsg?.conversation_message_id || prevMsg?.id;
      
      // Новая группа если:
      // 1. Сменился пользователь
      // 2. Разный conversation_id (для VK - разные сообщения)
      // 3. Прошло больше 5 минут между сообщениями
      const shouldNewGroup = !currentGroup || 
        currentGroup.user_id !== msg.user_id ||
        (convId && convId !== prevConvId) ||
        (index > 0 && this.getTimeDiff(messages[index-1].created_at, msg.created_at) > 300);
      
      if (shouldNewGroup) {
        currentGroup = {
          type: 'message',
          user_id: msg.user_id,
          username: msg.full_name || msg.username,
          is_outgoing: isOutgoing,
          messages: [],
          conversation_id: convId
        };
        groups.push(currentGroup);
      }
      
      currentGroup.messages.push(msg);
    });
    
    return groups;
  }
  
  createMessageGroup(group) {
    if (group.type === 'date') {
      return this.createDateDivider(group.label);
    }
    
    const div = document.createElement('div');
    div.className = `message-group ${group.is_outgoing ? 'outgoing' : 'incoming'}`;
    
    // Аватарка (только для входящих)
    if (!group.is_outgoing) {
      const avatar = document.createElement('div');
      avatar.className = `message-avatar avatar-color-${group.user_id % 8}`;
      avatar.textContent = (group.username || '?')[0].toUpperCase();
      div.appendChild(avatar);
    }
    
    // Пузырь сообщения
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Объединяем все сообщения в группе
    const allText = [];
    const allPhotos = [];
    const allAttachments = [];
    
    group.messages.forEach(msg => {
      if (msg.message) allText.push(msg.message);
      if (msg.attachment_file_id && msg.file) {
        if (msg.file.file_type?.startsWith('image/')) {
          allPhotos.push(msg.file);
        } else {
          allAttachments.push(msg.file);
        }
      }
    });
    
    // Заголовок (имя + время)
    const header = document.createElement('div');
    header.className = 'message-header';
    
    if (!group.is_outgoing) {
      const sender = document.createElement('span');
      sender.className = 'message-sender';
      sender.textContent = group.username;
      header.appendChild(sender);
    }
    
    const time = document.createElement('span');
    time.className = 'message-time';
    const lastMsg = group.messages[group.messages.length - 1];
    time.textContent = this.formatTime(lastMsg.created_at);
    header.appendChild(time);
    
    bubble.appendChild(header);
    
    // Текст
    if (allText.length > 0) {
      const text = document.createElement('div');
      text.className = 'message-text';
      text.textContent = allText.join('\n');
      bubble.appendChild(text);
    }
    
    // Фото сеткой
    if (allPhotos.length > 0) {
      const photosGrid = document.createElement('div');
      photosGrid.className = 'message-photos';
      photosGrid.setAttribute('data-count', Math.min(allPhotos.length, 10).toString());
      
      allPhotos.forEach((photo, index) => {
        const photoItem = document.createElement('div');
        photoItem.className = 'photo-item';
        
        const img = document.createElement('img');
        img.src = `/api/files/${photo.id}/view`;
        img.loading = 'lazy';
        img.alt = 'Фото';
        
        photoItem.appendChild(img);
        
        // Счётчик для 10+ фото
        if (index === 9 && allPhotos.length > 10) {
          const overlay = document.createElement('div');
          overlay.className = 'photo-count-overlay';
          overlay.textContent = `+${allPhotos.length - 10}`;
          photoItem.appendChild(overlay);
        }
        
        photoItem.addEventListener('click', () => {
          this.openPhotoModal(allPhotos, index);
        });
        
        photosGrid.appendChild(photoItem);
      });
      
      bubble.appendChild(photosGrid);
    }
    
    // Вложения
    if (allAttachments.length > 0) {
      const attachments = document.createElement('div');
      attachments.className = 'message-attachments';
      
      allAttachments.forEach(file => {
        const att = document.createElement('div');
        att.className = 'message-attachment';
        att.innerHTML = `
          <div class="attachment-icon">📎</div>
          <div class="attachment-info">
            <div class="attachment-name">${file.filename}</div>
            <div class="attachment-size">${this.formatFileSize(file.file_size)}</div>
          </div>
        `;
        att.addEventListener('click', () => {
          window.open(`/api/files/${file.id}/view`, '_blank');
        });
        attachments.appendChild(att);
      });
      
      bubble.appendChild(attachments);
    }
    
    div.appendChild(bubble);
    return div;
  }
  
  createDateDivider(label) {
    const div = document.createElement('div');
    div.className = 'date-divider';
    div.innerHTML = `<span>${label}</span>`;
    return div;
  }
  
  sendMessage() {
    const input = document.getElementById('chat-input');
    if (!input || !input.value.trim()) return;
    
    const message = {
      message: input.value.trim(),
      topic_id: this.currentTopic
    };
    
    fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        input.value = '';
        input.style.height = 'auto';
        this.loadMessages();
      }
    })
    .catch(error => console.error('Ошибка отправки:', error));
  }
  
  openPhotoModal(photos, index) {
    this.currentPhotos = photos;
    this.currentPhotoIndex = index;
    
    let modal = document.getElementById('photo-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'photo-modal';
      modal.className = 'photo-modal';
      modal.innerHTML = `
        <div class="photo-modal-header">
          <h3>Просмотр фото</h3>
          <button class="photo-modal-close" onclick="chat.closePhotoModal()">×</button>
        </div>
        <div class="photo-modal-content">
          <button class="photo-modal-nav prev" onclick="chat.prevPhoto()">❮</button>
          <img src="" alt="Фото" id="modal-photo-img">
          <button class="photo-modal-nav next" onclick="chat.nextPhoto()">❯</button>
        </div>
        <div class="photo-modal-counter" id="photo-counter"></div>
      `;
      document.body.appendChild(modal);
    }
    
    this.showPhoto();
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  
  showPhoto() {
    const photo = this.currentPhotos[this.currentPhotoIndex];
    const img = document.getElementById('modal-photo-img');
    const counter = document.getElementById('photo-counter');
    const prevBtn = document.querySelector('.photo-modal-nav.prev');
    const nextBtn = document.querySelector('.photo-modal-nav.next');
    
    if (img) {
      img.src = `/api/files/${photo.id}/view`;
    }
    
    if (counter) {
      counter.textContent = `${this.currentPhotoIndex + 1} / ${this.currentPhotos.length}`;
    }
    
    if (prevBtn) {
      prevBtn.disabled = this.currentPhotoIndex === 0;
    }
    
    if (nextBtn) {
      nextBtn.disabled = this.currentPhotoIndex === this.currentPhotos.length - 1;
    }
  }
  
  prevPhoto() {
    if (this.currentPhotoIndex > 0) {
      this.currentPhotoIndex--;
      this.showPhoto();
    }
  }
  
  nextPhoto() {
    if (this.currentPhotoIndex < this.currentPhotos.length - 1) {
      this.currentPhotoIndex++;
      this.showPhoto();
    }
  }
  
  closePhotoModal() {
    const modal = document.getElementById('photo-modal');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
  
  scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    }
  }
  
  updateScrollButton() {
    const container = document.getElementById('chat-messages');
    const button = document.getElementById('scroll-to-bottom');
    
    if (!container || !button) return;
    
    const threshold = container.scrollHeight - container.scrollTop - container.clientHeight;
    
    if (threshold > 200) {
      button.classList.add('visible');
    } else {
      button.classList.remove('visible');
    }
  }
  
  // Утилиты
  getMessageDate(timestamp) {
    const date = new Date(timestamp);
    return date.toISOString().split('T')[0];
  }
  
  formatDateLabel(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Сегодня';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Вчера';
    } else {
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
    }
  }
  
  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }
  
  getTimeDiff(time1, time2) {
    const d1 = new Date(time1);
    const d2 = new Date(time2);
    return (d2 - d1) / 1000; // секунды
  }
  
  formatFileSize(bytes) {
    if (!bytes) return '';
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 10) / 10 + ' ' + sizes[i];
  }
}

// Инициализация
let chat;
document.addEventListener('DOMContentLoaded', () => {
  chat = new ModernChat();
  
  // Подключение Socket.IO для реального времени
  if (typeof io !== 'undefined') {
    const socket = io();
    
    socket.on('new_message', (data) => {
      if (chat.currentTopic === data.topic_id) {
        chat.loadMessages();
      }
    });
  }
});
