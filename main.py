from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
import models, schemas
from database import engine, get_db
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import uvicorn
import bcrypt

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# ==========================================
# 0. KULLANICI (LOGIN / REGISTER)
# ==========================================
@app.post("/kayit/")
def kayit_ol(user: schemas.UserCreate, db: Session = Depends(get_db)):
    mevcut = db.query(models.User).filter(models.User.username == user.username).first()
    if mevcut: return {"hata": "Bu kullanıcı adı zaten alınmış."}

    guvenli_sifre_bytes = user.password[:72].encode('utf-8')
    hashed_pw = bcrypt.hashpw(guvenli_sifre_bytes, bcrypt.gensalt()).decode('utf-8')

    otomatik_email = f"{user.username}@financeapp.local"
    yeni_kullanici = models.User(username=user.username, hashed_password=hashed_pw, full_name=user.full_name,
                                 email=otomatik_email)

    db.add(yeni_kullanici)
    db.commit()
    db.refresh(yeni_kullanici)

    # === [YENİ]: İLK GİRİŞ BAŞLANGIÇ PAKETİ (STARTER KIT) ===
    uid = yeni_kullanici.user_id

    # 1. Varsayılan Kategoriler
    varsayilan_kategoriler = [
        {"name": "Maaş / Harçlık", "type": "Gelir"},
        {"name": "Market & Mutfak", "type": "Gider"},
        {"name": "Kira / Barınma", "type": "Gider"},
        {"name": "Alışveriş", "type": "Gider"},
        {"name": "Giyim", "type": "Gider"},
        {"name": "Taksit", "type": "Gider"},
        {"name": "Dışarıda Yemek / Kahve", "type": "Gider"},
        {"name": "Ulaşım / Akaryakıt", "type": "Gider"},
        {"name": "Aidat", "type": "Fatura"},
        {"name": "Elektrik", "type": "Fatura"},
        {"name": "Su", "type": "Fatura"},
        {"name": "İnternet", "type": "Fatura"},
        {"name": "Doğalgaz", "type": "Fatura"},
        {"name": "Eğlence & Abonelik (Netflix vb.)", "type": "Gider"},
        {"name": "Yatırım (Fon / Hisse / Altın)", "type": "Yatırım"}
    ]

    for kat in varsayilan_kategoriler:
        yeni_kat = models.Category(user_id=uid, name=kat["name"], type=kat["type"])
        db.add(yeni_kat)

    db.commit()  # Kategorileri kalıcı olarak kaydet

    return {"mesaj": "Kayıt başarılı! Hesabınız temel kategorilerle hazırlandı.", "user_id": uid}


@app.post("/giris/")
def giris_yap(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()

    # [YENİ KORUMA]: Kullanıcı yoksa VEYA şifresi NULL ise (Eski hesaplar) çökmesini engeller
    if not db_user or not db_user.hashed_password:
        return {"hata": "Kullanıcı adı veya şifre hatalı. (Eski, şifresiz bir hesaba girmeye çalışıyor olabilirsiniz.)"}

    girilen_sifre_bytes = user.password[:72].encode('utf-8')
    db_hash_bytes = db_user.hashed_password.encode('utf-8')

    if not bcrypt.checkpw(girilen_sifre_bytes, db_hash_bytes):
        return {"hata": "Kullanıcı adı veya şifre hatalı."}

    return {"mesaj": "Giriş başarılı", "user_id": db_user.user_id, "username": db_user.username,
            "full_name": db_user.full_name}


# ==========================================
# 1. KATEGORİ (User ID Filtreli)
# ==========================================
@app.get("/kategoriler/{user_id}")
def kategorileri_getir(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Category).filter(models.Category.user_id == user_id).all()


@app.post("/kategoriler/")
def kategori_ekle(k: schemas.CategoryCreate, db: Session = Depends(get_db)):
    yeni = models.Category(**k.dict());
    db.add(yeni);
    db.commit();
    db.refresh(yeni);
    return yeni


@app.delete("/kategoriler/{id}")
def kategori_sil(id: int, db: Session = Depends(get_db)):
    kat = db.query(models.Category).filter(models.Category.category_id == id).first()
    if not kat: return {"hata": "Bulunamadı"}
    i_var = db.query(models.Transaction).filter(models.Transaction.category_id == id).first()
    p_var = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.category_id == id).first()
    if i_var or p_var: return {"hata": "Bağlı veri var."}
    db.delete(kat);
    db.commit();
    return {"mesaj": "Silindi"}


# ==========================================
# 2. İŞLEMLER (User ID Filtreli)
# ==========================================
@app.get("/islemler/{user_id}")
def islemleri_getir(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()


@app.post("/islemler/")
def islem_ekle(i: schemas.TransactionCreate, db: Session = Depends(get_db)):
    yeni = models.Transaction(**i.dict());
    db.add(yeni);
    db.commit();
    return yeni


@app.put("/islemler/{id}")
def islem_guncelle(id: int, i: schemas.TransactionCreate, db: Session = Depends(get_db)):
    eski = db.query(models.Transaction).filter(models.Transaction.transaction_id == id).first()
    if eski:
        eski.category_id = i.category_id;
        eski.card_id = i.card_id;
        eski.amount = i.amount;
        eski.transaction_date = i.transaction_date;
        eski.description = i.description
        db.commit();
        return {"mesaj": "Güncellendi"}


@app.delete("/islemler/{id}")
def islem_sil(id: int, db: Session = Depends(get_db)):
    i = db.query(models.Transaction).filter(models.Transaction.transaction_id == id).first()
    if i: db.delete(i); db.commit(); return {"m": "ok"}


# ==========================================
# 3. FATURALAR (User ID Filtreli)
# ==========================================
@app.get("/faturalar/{user_id}")
def faturalari_getir(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Invoice).filter(models.Invoice.user_id == user_id).all()


@app.post("/faturalar/")
def fatura_ekle(f: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    yeni = models.Invoice(**f.dict());
    db.add(yeni);
    db.commit();
    return yeni


@app.put("/faturalar/{invoice_id}")
def fatura_guncelle(invoice_id: int, fatura_data: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    mevcut = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not mevcut:
        return {"hata": "Fatura bulunamadı"}

    mevcut.type = fatura_data.type
    mevcut.amount = fatura_data.amount
    mevcut.due_date = fatura_data.due_date
    mevcut.card_id = fatura_data.card_id
    mevcut.period_year = fatura_data.period_year
    mevcut.period_month = fatura_data.period_month

    # --- İŞTE EKLENMESİ GEREKEN HAYATİ SATIR ---
    mevcut.payment_date = fatura_data.payment_date

    db.commit()
    return mevcut

@app.delete("/faturalar/{id}")
def fatura_sil(id: int, db: Session = Depends(get_db)):
    f = db.query(models.Invoice).filter(models.Invoice.invoice_id == id).first()
    if f: db.delete(f); db.commit(); return {"m": "ok"}


@app.put("/faturalar/ode/{invoice_id}")
def fatura_ode(invoice_id: int, db: Session = Depends(get_db)):
    fatura = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not fatura:
        return {"hata": "Fatura bulunamadı"}

    fatura.is_paid = True
    fatura.payment_date = datetime.now().date()  # YENİ EKLENEN AKIL
    db.commit()
    return {"mesaj": "Fatura ödendi"}

# ==========================================
# 4. TAKSİTLER & KARTLAR (User ID Filtreli)
# ==========================================
@app.get("/taksit-planlari/{user_id}")
def taksit_getir(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.InstallmentPlan).filter(models.InstallmentPlan.user_id == user_id).all()


@app.post("/taksit-planlari/")
def taksit_ekle(p: schemas.InstallmentPlanCreate, db: Session = Depends(get_db)):
    kart = db.query(models.CreditCard).filter(models.CreditCard.card_id == p.card_id).first()
    if kart and p.start_date.day > kart.closing_day: p.start_date = p.start_date + relativedelta(months=1)
    yeni = models.InstallmentPlan(**p.dict());
    db.add(yeni);
    db.commit();
    return yeni


@app.delete("/taksit-planlari/{id}")
def taksit_sil(id: int, db: Session = Depends(get_db)):
    p = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.plan_id == id).first()
    if p: db.delete(p); db.commit(); return {"m": "ok"}


@app.get("/kredi-kartlari/{user_id}")
def kart_getir(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.CreditCard).filter(models.CreditCard.user_id == user_id).all()


@app.post("/kredi-kartlari/")
def kart_ekle(k: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    yeni = models.CreditCard(**k.dict());
    db.add(yeni);
    db.commit();
    return yeni


@app.put("/kredi-kartlari/{card_id}")
def kart_guncelle(card_id: int, card_data: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    kart = db.query(models.CreditCard).filter(models.CreditCard.card_id == card_id).first()
    if not kart:
        return {"hata": "Kart bulunamadı"}

    kart.card_name = card_data.card_name
    kart.limit_amount = card_data.limit_amount
    kart.closing_day = card_data.closing_day
    # due_day varsayılan kalabilir

    db.commit()
    return {"mesaj": "Kart güncellendi"}


@app.delete("/kredi-kartlari/{card_id}")
def kart_sil(card_id: int, db: Session = Depends(get_db)):
    kart = db.query(models.CreditCard).filter(models.CreditCard.card_id == card_id).first()
    if not kart:
        return {"hata": "Kart bulunamadı"}

    db.delete(kart)
    db.commit()
    return {"mesaj": "Kart başarıyla silindi"}


# ==========================================
# 5. ANA ANALİZ MOTORU (Kusursuz Hesap Kesim Mantığı)
# ==========================================
@app.get("/aylik-rapor/{user_id}/{yil}/{ay}")
def aylik_rapor_getir(user_id: int, yil: int, ay: int, db: Session = Depends(get_db)):
    sonuc = []
    kartlar = db.query(models.CreditCard).filter(models.CreditCard.user_id == user_id).all()
    kart_kesim = {k.card_id: k.closing_day for k in kartlar}
    kart_isim = {k.card_id: k.card_name for k in kartlar}

    # 1. DÜZELTME: Veritabanı filtresini kaldırdık. Tüm kayıtları alıp Python'da süzüyoruz.
    normal = db.query(models.Transaction, models.Category).join(models.Category).filter(
        models.Transaction.user_id == user_id
    ).all()

    for i, k in normal:
        tx_date = i.transaction_date
        c_id = i.card_id
        tx_yil, tx_ay = tx_date.year, tx_date.month

        # Kesim tarihi kontrolü (Kart ile ödenmişse)
        if c_id and c_id in kart_kesim:
            if tx_date.day > kart_kesim[c_id]:
                tx_ay += 1
                if tx_ay > 12:
                    tx_ay = 1
                    tx_yil += 1

        # Artık dönemi kaydırılmış veriyi eşleştiriyoruz
        if tx_yil == yil and tx_ay == ay:
            k_adi = kart_isim.get(c_id, "Nakit / Banka Kartı")
            sonuc.append(
                {"tarih": tx_date, "aciklama": i.description or k.name, "kategori_adi": k.name, "tutar": i.amount,
                 "islem_turu": k.type, "kaynak": "Peşin", "kart_adi": k_adi})

    # 2. DÜZELTME: Taksitler için de kart kesim mantığını uyguladık
    taksitler = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.user_id == user_id).all()
    for p in taksitler:
        c_id = p.card_id
        k_adi = kart_isim.get(c_id, "Nakit / Banka Kartı")
        for i in range(p.installment_count):
            t_tar = p.start_date + relativedelta(months=i)
            tx_yil, tx_ay = t_tar.year, t_tar.month

            if c_id and c_id in kart_kesim:
                if t_tar.day > kart_kesim[c_id]:
                    tx_ay += 1
                    if tx_ay > 12:
                        tx_ay = 1
                        tx_yil += 1

            if tx_yil == yil and tx_ay == ay:
                sonuc.append({"tarih": t_tar, "aciklama": f"{p.description} ({i + 1}/{p.installment_count})",
                              "kategori_adi": "Taksit", "tutar": p.total_amount / p.installment_count,
                              "islem_turu": "Gider", "kaynak": "Taksit", "kart_adi": k_adi})

    faturalar = db.query(models.Invoice).filter(models.Invoice.user_id == user_id).all()
    for f in faturalar:
        # Grafikler için Ödeme Tarihini baz al (Yoksa Son Ödemeyi kullan)
        tx_date = getattr(f, 'payment_date', None) or f.due_date
        c_id = getattr(f, 'card_id', None)
        tx_yil, tx_ay = tx_date.year, tx_date.month

        if c_id and c_id in kart_kesim:
            if tx_date.day > kart_kesim[c_id]:
                tx_ay += 1
                if tx_ay > 12:
                    tx_ay = 1
                    tx_yil += 1

        if tx_yil == yil and tx_ay == ay:
            k_adi = kart_isim.get(c_id, "Nakit / Banka Kartı")
            sonuc.append(
                {"tarih": tx_date, "aciklama": f"{f.type} Faturası", "kategori_adi": "Fatura", "tutar": f.amount,
                 "islem_turu": "Gider", "kaynak": "Fatura", "kart_adi": k_adi})

    return sonuc


if __name__ == "__main__": uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)