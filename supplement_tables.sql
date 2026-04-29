-- 补充缺失的数据库表
-- 用于Railway MySQL

USE zhinote;

-- 自动笔记表
CREATE TABLE IF NOT EXISTS zhinote_auto_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 导出记录表
CREATE TABLE IF NOT EXISTS zhinote_export_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    export_type VARCHAR(50),
    export_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 复习提醒表
CREATE TABLE IF NOT EXISTS zhinote_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT,
    reminder_time DATETIME NOT NULL,
    is_completed TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 学校推荐表
CREATE TABLE IF NOT EXISTS zhinote_schools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    ranking VARCHAR(50),
    type VARCHAR(50),
    min_score INT,
    majors TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文档表
CREATE TABLE IF NOT EXISTS zhinote_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    file_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 音频记录表（如果zhinote_audio_files不存在）
CREATE TABLE IF NOT EXISTS zhinote_audio_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    audio_path VARCHAR(500) NOT NULL,
    duration INT,
    transcript TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文本输入表
CREATE TABLE IF NOT EXISTS zhinote_text_inputs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 知识点表
CREATE TABLE IF NOT EXISTS zhinote_knowledge_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    content TEXT NOT NULL,
    importance VARCHAR(50),
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 知识分类表
CREATE TABLE IF NOT EXISTS zhinote_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 学习记录表
CREATE TABLE IF NOT EXISTS zhinote_study_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    note_id INT,
    duration INT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_note_id ON zhinote_export_records(note_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON zhinote_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON zhinote_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON zhinote_audio_records(user_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON zhinote_text_inputs(user_id);
CREATE INDEX IF NOT EXISTS idx_note_id ON zhinote_knowledge_points(note_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON zhinote_study_records(user_id);
