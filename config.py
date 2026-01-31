import os
import pymysql

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 云数据库配置（注意：localhost 改为 127.0.0.1 或内网 IP）
    DB_CONFIG = {
        'host': '127.0.0.1',
        'user': 'root',           # 刚创建的数据库用户
        'password': '123456',       # 刚设置的密码
        'database': 'pf',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }