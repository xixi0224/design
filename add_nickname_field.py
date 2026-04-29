"""
为已存在的用户表添加 nickname 字段
"""
import pymysql
from app.config import DB_CONFIG

def add_nickname_field():
    """添加nickname字段"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'zhinote_users' 
            AND COLUMN_NAME = 'nickname'
        """, (DB_CONFIG['database'],))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ nickname 字段已存在")
        else:
            print("正在添加 nickname 字段...")
            cursor.execute("""
                ALTER TABLE zhinote_users 
                ADD COLUMN nickname VARCHAR(50) DEFAULT '' AFTER username
            """)
            conn.commit()
            print("✓ nickname 字段添加成功")
        
        # 更新现有用户的nickname为username
        print("正在更新现有用户的nickname...")
        cursor.execute("""
            UPDATE zhinote_users 
            SET nickname = username 
            WHERE nickname = '' OR nickname IS NULL
        """)
        conn.commit()
        print(f"✓ 已更新 {cursor.rowcount} 个用户")
        
        print("\n✅ 完成！")
        
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
    add_nickname_field()
