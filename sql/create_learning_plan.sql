CREATE TABLE IF NOT EXISTS zhinote_learning_plans (
  id int(11) NOT NULL AUTO_INCREMENT,
  exam_date date NOT NULL,
  daily_hours decimal(3,1) NOT NULL,
  pending_tasks text,
  exam_subject varchar(100) NOT NULL,
  plan_data longtext,
  created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;