-- ========================================
-- ZhiNote 数据库表结构安全检查与修复
-- 先检查字段是否存在，再决定是否添加/修改
-- ========================================

USE railway;

-- ========================================
-- 1. 修改 zhinote_notes 表（最关键！）
-- ========================================

-- 将 user_id 改为允许 NULL
ALTER TABLE zhinote_notes 
MODIFY COLUMN user_id INT DEFAULT NULL COMMENT '用户ID，可为空';

-- ========================================
-- 2. 检查并修复 zhinote_analysis 表
-- ========================================

-- 先查看表结构
SELECT '=== zhinote_analysis 表结构 ===' AS '';
DESCRIBE zhinote_analysis;

-- 如果 doc_id 已存在，跳过添加
-- 如果不存在，才添加
SET @dbname = 'railway';
SET @tablename = 'zhinote_analysis';
SET @columnname = 'doc_id';

SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_analysis ADD COLUMN doc_id INT NOT NULL COMMENT ''关联文档/笔记ID'' AFTER id',
    'SELECT ''doc_id 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 section 字段
SET @columnname = 'section';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_analysis ADD COLUMN section VARCHAR(255) COMMENT ''段落/章节名'' AFTER doc_id',
    'SELECT ''section 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 keywords 字段
SET @columnname = 'keywords';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_analysis ADD COLUMN keywords TEXT COMMENT ''关键词（JSON数组）'' AFTER summary',
    'SELECT ''keywords 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 is_exam_point 字段
SET @columnname = 'is_exam_point';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_analysis ADD COLUMN is_exam_point TINYINT(1) DEFAULT 0 COMMENT ''是否考点'' AFTER keywords',
    'SELECT ''is_exam_point 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 importance 字段
SET @columnname = 'importance';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_analysis ADD COLUMN importance VARCHAR(20) DEFAULT ''⭐⭐'' COMMENT ''重要程度'' AFTER is_exam_point',
    'SELECT ''importance 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 3. 检查并修复 zhinote_audio_records 表
-- ========================================

SELECT '=== zhinote_audio_records 表结构 ===' AS '';
DESCRIBE zhinote_audio_records;

SET @tablename = 'zhinote_audio_records';

-- 检查并添加 course_id
SET @columnname = 'course_id';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_audio_records ADD COLUMN course_id INT DEFAULT 1 COMMENT ''课程ID'' AFTER id',
    'SELECT ''course_id 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 filename
SET @columnname = 'filename';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_audio_records ADD COLUMN filename VARCHAR(500) NOT NULL COMMENT ''音频文件名'' AFTER course_id',
    'SELECT ''filename 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 transcript_text
SET @columnname = 'transcript_text';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_audio_records ADD COLUMN transcript_text TEXT COMMENT ''语音转文本结果'' AFTER status',
    'SELECT ''transcript_text 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 4. 检查并修复 zhinote_auto_notes 表
-- ========================================

SELECT '=== zhinote_auto_notes 表结构 ===' AS '';
DESCRIBE zhinote_auto_notes;

SET @tablename = 'zhinote_auto_notes';

-- 检查并添加 source_id
SET @columnname = 'source_id';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_auto_notes ADD COLUMN source_id INT NOT NULL COMMENT ''源内容ID'' AFTER id',
    'SELECT ''source_id 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 source_type
SET @columnname = 'source_type';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_auto_notes ADD COLUMN source_type VARCHAR(50) NOT NULL COMMENT ''源类型'' AFTER source_id',
    'SELECT ''source_type 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 structure
SET @columnname = 'structure';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_auto_notes ADD COLUMN structure TEXT COMMENT ''笔记结构（JSON）'' AFTER content',
    'SELECT ''structure 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 5. 修改 zhinote_reminders 表
-- ========================================

SELECT '=== zhinote_reminders 表结构 ===' AS '';
DESCRIBE zhinote_reminders;

SET @tablename = 'zhinote_reminders';
SET @columnname = 'updated_at';
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = @tablename 
    AND COLUMN_NAME = @columnname
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE zhinote_reminders ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at',
    'SELECT ''updated_at 字段已存在，跳过'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 6. 重命名表（如果存在）
-- ========================================

-- 检查是否存在 zhinote_categories
SET @table_exists = (
    SELECT COUNT(*) 
    FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA = @dbname 
    AND TABLE_NAME = 'zhinote_categories'
);

SET @sql = IF(@table_exists > 0,
    'RENAME TABLE zhinote_categories TO zhinote_knowledge_categories',
    'SELECT ''zhinote_categories 表不存在，跳过重命名'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ========================================
-- 完成 - 显示最终表结构
-- ========================================
SELECT '========================================' AS '';
SELECT '✅ 数据库表结构检查与修复完成！' AS message;
SELECT '========================================' AS '';

SELECT '=== 最终表清单 ===' AS '';
SELECT table_name AS '表名' 
FROM information_schema.tables 
WHERE table_schema = 'railway' AND table_name LIKE 'zhinote_%'
ORDER BY table_name;

SELECT '========================================' AS '';
