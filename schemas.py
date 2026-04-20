from typing import Optional # Bu satır en üstlerde yoksa ekle
from pydantic import BaseModel
from datetime import date

# --- ESKİ ŞEMALAR (Temel Yapı Taşlarımız) ---
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str

class CategoryCreate(BaseModel):
    user_id: int
    type: str
    name: str

class TransactionCreate(BaseModel):
    user_id: int
    category_id: int
    card_id: Optional[int] = None  # İŞTE EKSİK OLAN HAYAT KURTARICI SATIR!
    amount: float
    transaction_date: str
    description: Optional[str] = None

# --- YENİ ŞEMALAR (Kredi Kartı ve Taksit Modülü) ---
class CreditCardCreate(BaseModel):
    user_id: int
    card_name: str
    closing_day: int
    due_day: int
    limit_amount: float

class InstallmentPlanCreate(BaseModel):
    user_id: int
    category_id: int
    card_id: int      # <-- YENİ EKLENDİ
    description: str
    total_amount: float
    installment_count: int
    start_date: date

class InvoiceCreate(BaseModel):
    user_id: int
    type: str
    amount: float
    due_date: str
    is_paid: bool = False
    card_id: Optional[int] = None  # YENİ EKLENEN SATIR

class UserLogin(BaseModel):
    username: str
    password: str