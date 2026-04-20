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
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()