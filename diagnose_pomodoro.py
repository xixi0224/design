"""
诊断番茄钟记录问题
"""
import pymysql
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "zhinote",
    "charset": "utf8mb4"
}

def diagnose():
    print("=" * 60)
    print("番茄钟记录诊断工具")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. 检查今日记录
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n📅 查询日期: {today}")
        print("-" * 60)
        
        cursor.execute("""
            SELECT id, study_date, study_duration, review_count, task_count, created_at, updated_at
            FROM zhinote_study_stats
            WHERE study_date = %s
        """, (today,))
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"✅ 今日有 {len(rows)} 条记录:")
            for row in rows:
                print(f"  ID={row[0]}, 日期={row[1]}, 时长={row[2]}分钟, "
                      f"复习={row[3]}次, 任务={row[4]}个, "
                      f"创建时间={row[5]}, 更新时间={row[6]}")
        else:
            print("❌ 今日没有任何记录")
        
        # 2. 检查所有记录
        print("\n" + "-" * 60)
        print("📊 所有学习记录:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT id, study_date, study_duration, review_count, task_count, created_at
            FROM zhinote_study_stats
            ORDER BY study_date DESC
            LIMIT 10
        """)
        
        all_rows = cursor.fetchall()
        
        if all_rows:
            print(f"总共 {len(all_rows)} 条记录（显示最近10条）:")
            for row in all_rows:
                print(f"  [{row[1]}] {row[2]}分钟 (ID={row[0]})")
        else:
            print("❌ 数据库中没有任何学习记录")
        
        # 3. 计算今日总时长
        print("\n" + "-" * 60)
        print("⏱️  今日总学习时长:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT COALESCE(SUM(study_duration), 0)
            FROM zhinote_study_stats
            WHERE study_date = %s
        """, (today,))
        
        total = cursor.fetchone()[0]
        print(f"  今日总时长: {total} 分钟 = {total/60:.1f} 小时")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("诊断完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {str(e)}")

def clear_today_data():
    """清理今日数据"""
    print("\n⚠️  准备清理今日的所有学习记录...")
    confirm = input("确认清理？(yes/no): ")
    
    if confirm.lower() == 'yes':
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            cursor.execute("""
                DELETE FROM zhinote_study_stats
                WHERE study_date = %s
            """, (today,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            print(f"✅ 已删除 {deleted} 条记录")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ 清理失败: {str(e)}")
    else:
        print("❌ 已取消清理")

if __name__ == "__main__":
    diagnose()
    
    print("\n")
    action = input("是否要清理今日数据？(y/n): ")
    if action.lower() == 'y':
        clear_today_data()
        print("\n清理后，请重新测试番茄钟功能")
