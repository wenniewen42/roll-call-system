import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "attendance.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))  # 儲存在環境變量中

    # 設定其他常用配置選項
    # SESSION_TYPE = 'redis'  # 使用 Redis 儲存會話資料
    # SESSION_PERMANENT = False
    # SESSION_USE_SIGNER = True
    # SESSION_REDIS = redis.StrictRedis(host='localhost', port=6379, db=0)  # 可以根據需求配置 Redis 連接
