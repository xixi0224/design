import os

DB_CONFIG = {
    "host": os.environ.get("MYSQLHOST", os.environ.get("MYSQL_HOST", "127.0.0.1")),
    "port": int(os.environ.get("MYSQLPORT", os.environ.get("MYSQL_PORT", "3306"))),
    "user": os.environ.get("MYSQLUSER", os.environ.get("MYSQL_USER", "root")),
    "password": os.environ.get("MYSQLPASSWORD", os.environ.get("MYSQL_PASSWORD", "041602")),
    "database": os.environ.get("MYSQLDATABASE", os.environ.get("MYSQL_DATABASE", "zhinote")),
    "charset": "utf8mb4",
}

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-1ba4b8933405452fa18df0e90b6ddfbc")
DASHSCOPE_MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen-plus")

# 七牛云配置
QINIU_AK = os.environ.get("QINIU_AK", "GTD6pKI_9WCDP_4C0wdmNDb3XBnBnRbu-5VLKAMdK7")
QINIU_SK = os.environ.get("QINIU_SK", "YTaSOh25ejkbpSMsnUgRg-3CoWGA3u8hPxJn9IjC")
QINIU_BUCKET = os.environ.get("QINIU_BUCKET", "zhinote-audio")
QINIU_DOMAIN = os.environ.get("QINIU_DOMAIN", "teg6y6kbh.hn-bkt.clouddn.com")