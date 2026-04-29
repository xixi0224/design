"""
运行此脚本以创建用户表和密码重置令牌表
请确保MySQL服务正在运行，并且config.py中的数据库配置正确
"""
import pymysql
from app.config import DB_CONFIG

def create_tables():
    """创建用户相关表"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("正在创建用户表...")
        
        # 创建用户表
        create_users_table = """
        CREATE TABLE IF NOT EXISTS zhinote_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            nickname VARCHAR(50) DEFAULT '',
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20) UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            avatar_url VARCHAR(255) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active TINYINT(1) DEFAULT 1,
            last_login TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(create_users_table)
        print("✓ 用户表创建成功")
        
        # 创建密码重置令牌表
        print("正在创建密码重置令牌表...")
        
        create_tokens_table = """
        CREATE TABLE IF NOT EXISTS zhinote_password_reset_tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(100) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES zhinote_users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(create_tokens_table)
        print("✓ 密码重置令牌表创建成功")
        
        # 提交更改
        conn.commit()
        
        print("\n✅ 所有表创建成功！")
        print("\n提示：")
        print("- 现在可以使用注册功能创建新账号")
        print("- 登录功能已连接到后端数据库")
        print("- 忘记密码功能需要邮箱已注册")
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_tables()
