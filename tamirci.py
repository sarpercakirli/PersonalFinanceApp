from database import engine
import models

print("Veritabanı kontrol ediliyor...")
# Bu komut, models.py içindeki tüm sınıfları kontrol eder ve SQL'de eksik olanları zorla yaratır.
models.Base.metadata.create_all(bind=engine)
print("İşlem başarılı! Eksik tablolar (Transactions ve InstallmentPlans) veritabanına işlendi.")