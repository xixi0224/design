"""
数据库初始化脚本
在Railway部署时自动创建所有必需的表
"""

import pymysql
import os
import sys

def init_database():
    """初始化数据库，创建所有必需的表"""
    
    # 从环境变量获取数据库连接信息
    db_config = {
        'host': os.environ.get('MYSQLHOST', os.environ.get('MYSQL_HOST', '127.0.0.1')),
        'port': int(os.environ.get('MYSQLPORT', os.environ.get('MYSQL_PORT', '3306'))),
        'user': os.environ.get('MYSQLUSER', os.environ.get('MYSQL_USER', 'root')),
        'password': os.environ.get('MYSQLPASSWORD', os.environ.get('MYSQL_PASSWORD', '')),
        'database': os.environ.get('MYSQLDATABASE', os.environ.get('MYSQL_DATABASE', 'railway')),
        'charset': 'utf8mb4'
    }
    
    print(f"正在连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("数据库连接成功！")
        
        # 读取SQL文件
        sql_file = os.path.join(os.path.dirname(__file__), 'complete_database_schema.sql')
        
        if not os.path.exists(sql_file):
            print(f"错误: 找不到SQL文件 {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割）
        sql_statements = sql_content.split(';')
        
        # 执行每个SQL语句
        success_count = 0
        error_count = 0
        
        for statement in sql_statements:
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                cursor.execute(statement)
                success_count += 1
            except Exception as e:
                # 忽略已存在的表错误
                if 'already exists' in str(e).lower() or 'exists' in str(e).lower():
                    print(f"  ⚠️  表已存在，跳过")
                else:
                    print(f"  ❌ 执行失败: {str(e)}")
                    print(f"     SQL: {statement[:100]}...")
                    error_count += 1

        # 兜底：补齐业务代码依赖但 schema 可能遗漏的表
        # 说明：线上日志出现过 railway.zhinote_audio_files 不存在，导致上传/转写链路失败
        fallback_statements = [
            """
            CREATE TABLE IF NOT EXISTS zhinote_audio_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(512) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ]

        for statement in fallback_statements:
            stmt = statement.strip()
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
                success_count += 1
                print("  ✅ 兜底建表/补表成功: zhinote_audio_files")
            except Exception as e:
                # 兜底失败不阻断服务启动，但需要打印出来方便排查
                print(f"  ⚠️  兜底建表失败: {str(e)}")
        
        conn.commit()
        
        print(f"\n✅ 数据库初始化完成！")
        print(f"   成功: {success_count} 条语句")
        print(f"   失败: {error_count} 条语句")
        
        # 验证表是否创建成功
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n📋 当前数据库共有 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
