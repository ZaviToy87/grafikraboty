-- init_db.sql
-- Инициализация базы данных PostgreSQL при первом запуске
-- Автоматически выполняется при старте контейнера

-- Включаем расширение для UUID (если понадобится)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'employee',
    telegram_id VARCHAR(100),
    vk_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица задач
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- График работы (планируемые смены)
CREATE TABLE IF NOT EXISTS work_schedule (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    shift_date DATE NOT NULL,
    shift_type VARCHAR(50),
    start_time TIME,
    end_time TIME,
    is_planned BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, shift_date)
);

-- Фактические рабочие смены
CREATE TABLE IF NOT EXISTS work_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    opening_sum DECIMAL(10, 2) DEFAULT 0,
    closing_sum DECIMAL(10, 2),
    revenue_total DECIMAL(10, 2) DEFAULT 0,
    cash_revenue DECIMAL(10, 2) DEFAULT 0,
    cashless_revenue DECIMAL(10, 2) DEFAULT 0,
    acquiring_amount DECIMAL(10, 2) DEFAULT 0,
    terminal_actual DECIMAL(10, 2) DEFAULT 0,
    operations_in DECIMAL(10, 2) DEFAULT 0,
    operations_out DECIMAL(10, 2) DEFAULT 0,
    discrepancy DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Записи рабочего журнала
CREATE TABLE IF NOT EXISTS work_journal_entries (
    id SERIAL PRIMARY KEY,
    shift_id INTEGER REFERENCES work_sessions(id) ON DELETE CASCADE,
    entry_type VARCHAR(50),
    amount DECIMAL(10, 2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Сообщения чата
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    message_text TEXT,
    message_type VARCHAR(50) DEFAULT 'text',
    file_id INTEGER,
    vk_message_id VARCHAR(100),
    vk_synced BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT false
);

-- Темы чата
CREATE TABLE IF NOT EXISTS chat_topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Файлы
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    file_path VARCHAR(1000),
    file_size INTEGER,
    file_type VARCHAR(100),
    uploaded_by INTEGER REFERENCES users(id),
    description TEXT,
    category VARCHAR(100),
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Штрихкоды
CREATE TABLE IF NOT EXISTS barcodes (
    id SERIAL PRIMARY KEY,
    barcode VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    price DECIMAL(10, 2),
    unit VARCHAR(50),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Аудит лог
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Задачи коллег
CREATE TABLE IF NOT EXISTS colleague_tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    thanks_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Корректировки зарплаты
CREATE TABLE IF NOT EXISTS salary_adjustments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    reason VARCHAR(500),
    adjustment_type VARCHAR(50) DEFAULT 'bonus',
    period DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- VK вложения
CREATE TABLE IF NOT EXISTS vk_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES chat_messages(id) ON DELETE CASCADE,
    attachment_type VARCHAR(50),
    attachment_url VARCHAR(1000),
    attachment_id VARCHAR(255),
    owner_id VARCHAR(100),
    access_key VARCHAR(100),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_work_schedule_user_date ON work_schedule(user_id, shift_date);
CREATE INDEX IF NOT EXISTS idx_work_sessions_user ON work_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_status ON work_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_messages_topic ON chat_messages(topic_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_files_uploaded_by ON files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_barcodes_barcode ON barcodes(barcode);

-- Добавляем пользователей по умолчанию (пароль: admin)
-- Пароль хешируется в приложении, здесь только заглушки
INSERT INTO users (username, password_hash, full_name, role, telegram_id, vk_id) 
VALUES 
    ('admin', 'pbkdf2:sha256:260000$defaultsalt$placeholder', 'Администратор', 'admin', NULL, '146411666')
ON CONFLICT (username) DO NOTHING;

-- Создаем функцию для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_schedule_updated_at BEFORE UPDATE ON work_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_sessions_updated_at BEFORE UPDATE ON work_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_barcodes_updated_at BEFORE UPDATE ON barcodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
