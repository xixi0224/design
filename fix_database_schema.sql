-- ========================================
-- ZhiNote 数据库表字段修复脚本
-- 用于修改已存在的表结构，使其与代码匹配
-- ========================================

USE railway;

-- ========================================
-- 修复 zhinote_notes 表
-- ========================================
-- 问题：user_id 设置为 NOT NULL，但代码插入时没有提供
-- 解决：改为允许 NULL

ALTER TABLE zhinote_notes 
MODIFY COLUMN user_id INT DEFAULT NULL COMMENT '用户ID，可为空';

-- ========================================
-- 修复 zhinote_analysis 表
-- ========================================
-- 确保字段与代码匹配

-- 检查是否有错误的字段名，如果有则修改
-- 如果表结构正确，以下语句会跳过

-- 确保有 doc_id 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS doc_id INT NOT NULL COMMENT '关联文档/笔记ID' AFTER id;

-- 确保有 section 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS section VARCHAR(255) COMMENT '段落/章节名' AFTER doc_id;

-- 确保有 summary 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS summary TEXT COMMENT '内容摘要' AFTER section;

-- 确保有 keywords 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS keywords TEXT COMMENT '关键词（JSON数组）' AFTER summary;

-- 确保有 is_exam_point 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS is_exam_point TINYINT(1) DEFAULT 0 COMMENT '是否考点' AFTER keywords;

-- 确保有 importance 字段
ALTER TABLE zhinote_analysis 
ADD COLUMN IF NOT EXISTS importance VARCHAR(20) DEFAULT '⭐⭐' COMMENT '重要程度' AFTER is_exam_point;

-- 删除可能存在的错误字段
ALTER TABLE zhinote_analysis 
DROP COLUMN IF EXISTS note_id;

ALTER TABLE zhinote_analysis 
DROP COLUMN IF EXISTS key_points;

ALTER TABLE zhinote_analysis 
DROP COLUMN IF EXISTS study_suggestions;

-- ========================================
-- 修复 zhinote_audio_records 表
-- ========================================
-- 确保字段名正确

ALTER TABLE zhinote_audio_records 
ADD COLUMN IF NOT EXISTS course_id INT DEFAULT 1 COMMENT '课程ID' AFTER id;

ALTER TABLE zhinote_audio_records 
ADD COLUMN IF NOT EXISTS filename VARCHAR(500) NOT NULL COMMENT '音频文件名' AFTER course_id;

ALTER TABLE zhinote_audio_records 
ADD COLUMN IF NOT EXISTS transcript_text TEXT COMMENT '语音转文本结果' AFTER status;

-- 删除可能存在的错误字段
ALTER TABLE zhinote_audio_records 
DROP COLUMN IF EXISTS user_id;

ALTER TABLE zhinote_audio_records 
DROP COLUMN IF EXISTS audio_path;

ALTER TABLE zhinote_audio_records 
DROP COLUMN IF EXISTS transcript;

-- ========================================
-- 修复 zhinote_auto_notes 表
-- ========================================
-- 添加缺失的字段

ALTER TABLE zhinote_auto_notes 
ADD COLUMN IF NOT EXISTS source_id INT NOT NULL COMMENT '源内容ID' AFTER id;

ALTER TABLE zhinote_auto_notes 
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) NOT NULL COMMENT '源类型：document/audio/text' AFTER source_id;

ALTER TABLE zhinote_auto_notes 
ADD COLUMN IF NOT EXISTS structure TEXT COMMENT '笔记结构（JSON）' AFTER content;

-- ========================================
-- 修复 zhinote_reminders 表
-- ========================================
-- 添加 updated_at 字段

ALTER TABLE zhinote_reminders 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- ========================================
-- 修复 zhinote_knowledge_categories 表
-- ========================================
-- 如果表名错误（使用了zhinote_categories），需要重命名

-- 检查是否存在错误的表名
-- 如果存在 zhinote_categories 但不存在 zhinote_knowledge_categories
-- 则重命名表

RENAME TABLE IF EXISTS zhinote_categories TO zhinote_knowledge_categories;

-- ========================================
-- 添加缺失的索引
-- ========================================

-- zhinote_notes 索引
ALTER TABLE zhinote_notes 
ADD INDEX IF NOT EXISTS idx_user_id (user_id);

ALTER TABLE zhinote_notes 
ADD INDEX IF NOT EXISTS idx_created_at (created_at);

-- zhinote_analysis 索引
ALTER TABLE zhinote_analysis 
ADD INDEX IF NOT EXISTS idx_doc_id (doc_id);

-- zhinote_auto_notes 索引
ALTER TABLE zhinote_auto_notes 
ADD INDEX IF NOT EXISTS idx_source (source_id, source_type);

-- ========================================
-- 验证修复结果
-- ========================================
SELECT '========================================' AS '';
SELECT '✅ 数据库表结构修复完成！' AS message;
SELECT '========================================' AS '';

-- 显示所有表
SELECT table_name AS '表名' 
FROM information_schema.tables 
WHERE table_schema = 'railway' AND table_name LIKE 'zhinote_%'
ORDER BY table_name;

SELECT '========================================' AS '';
SELECT '提示：请检查上述表是否完整' AS note;
SELECT '========================================' AS '';
