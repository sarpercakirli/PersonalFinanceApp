from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env dosyasındaki gizli şifreleri sisteme yükler
load_dotenv()

# Şifreyi çevre değişkeninden alıyoruz (Kodda şifre yok!)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Bulut veritabanına bağlanma motoru
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,      # İstek atmadan önce bağlantı yaşıyor mu diye kontrol et
    pool_recycle=1800        # Bağlantıları her 30 dakikada bir (1800 saniye) yenile
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()