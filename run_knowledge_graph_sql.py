import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "041602",
    "database": "zhinote",
    "charset": "utf8mb4",
}

SQL_FILE = r"d:\tingting\xixi\计算机设计大赛\ZhiNote2.0\ZhiNote2.0hou\sql\knowledge_graph.sql"

def main():
    print("正在连接数据库...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 按分号拆分并执行每条语句
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    for stmt in statements:
        print(f"执行: {stmt[:60]}...")
        cursor.execute(stmt)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("知识图谱表创建成功！")

if __name__ == "__main__":
    main()
