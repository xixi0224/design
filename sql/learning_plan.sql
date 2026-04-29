-- 学习计划表
CREATE TABLE IF NOT EXISTS `zhinote_learning_plans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `exam_date` date NOT NULL COMMENT '考试日期',
  `daily_hours` decimal(3,1) NOT NULL COMMENT '每日可用时间（小时）',
  `pending_tasks` text COMMENT '待完成任务',
  `exam_subject` varchar(100) NOT NULL COMMENT '考试科目',
  `plan_data` longtext COMMENT '计划数据（JSON格式）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习计划表';
