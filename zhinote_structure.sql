-- ZhiNote 数据库表结构
-- 用于在Railway MySQL中创建表

-- 如果数据库不存在则创建
CREATE DATABASE IF NOT EXISTS zhinote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE zhinote;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

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
);

-- 音频记录表
CREATE TABLE IF NOT EXISTS zhinote_audio_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    audio_path VARCHAR(500) NOT NULL,
    duration INT,
    transcript TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文本输入表
CREATE TABLE IF NOT EXISTS zhinote_text_inputs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI分析结果表
CREATE TABLE IF NOT EXISTS zhinote_ai_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_id INT NOT NULL,
    summary TEXT,
    key_points TEXT,
    study_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 笔记表
CREATE TABLE IF NOT EXISTS zhinote_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    note_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 知识点表
CREATE TABLE IF NOT EXISTS zhinote_knowledge_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    content TEXT NOT NULL,
    importance VARCHAR(50),
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识分类表
CREATE TABLE IF NOT EXISTS zhinote_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习记录表
CREATE TABLE IF NOT EXISTS zhinote_study_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    note_id INT,
    duration INT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 复习提醒表
CREATE TABLE IF NOT EXISTS zhinote_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    note_id INT,
    reminder_time DATETIME NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 导出记录表
CREATE TABLE IF NOT EXISTS zhinote_export_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    export_format VARCHAR(20),
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习统计表
CREATE TABLE IF NOT EXISTS zhinote_study_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    stat_date DATE NOT NULL,
    study_duration INT DEFAULT 0,
    notes_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_date (user_id, stat_date)
);

-- 学习计划表
CREATE TABLE IF NOT EXISTS zhinote_learning_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    target_hours FLOAT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识图谱节点表
CREATE TABLE IF NOT EXISTS zhinote_graph_nodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    node_id VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    node_type VARCHAR(50),
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识图谱边表
CREATE TABLE IF NOT EXISTS zhinote_graph_edges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    source_node VARCHAR(100) NOT NULL,
    target_node VARCHAR(100) NOT NULL,
    edge_type VARCHAR(50),
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_user_id ON zhinote_documents(user_id);
CREATE INDEX idx_user_id ON zhinote_audio_records(user_id);
CREATE INDEX idx_user_id ON zhinote_text_inputs(user_id);
CREATE INDEX idx_user_id ON zhinote_notes(user_id);
CREATE INDEX idx_note_id ON zhinote_knowledge_points(note_id);
CREATE INDEX idx_user_id ON zhinote_study_records(user_id);
CREATE INDEX idx_user_id ON zhinote_reminders(user_id);
CREATE INDEX idx_note_id ON zhinote_export_records(note_id);
CREATE INDEX idx_user_id ON zhinote_study_stats(user_id);
CREATE INDEX idx_user_id ON zhinote_learning_plans(user_id);
CREATE INDEX idx_note_id ON zhinote_graph_nodes(note_id);
CREATE INDEX idx_note_id ON zhinote_graph_edges(note_id);
