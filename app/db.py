import pymysql
from app.config import DB_CONFIG

def get_conn():
    return pymysql.connect(**DB_CONFIG)