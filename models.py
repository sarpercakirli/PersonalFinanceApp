from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, Boolean
from database import Base
import datetime

class User(Base):
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=True)

class Category(Base):
    __tablename__ = "Categories"
    category_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    type = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)

class CreditCard(Base):
    __tablename__ = "CreditCards"
    card_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    card_name = Column(String(50), nullable=False)
    closing_day = Column(Integer, nullable=False)
    due_day = Column(Integer, nullable=False)
    limit_amount = Column(Float(53), nullable=False)

class InstallmentPlan(Base):
    __tablename__ = "InstallmentPlans"
    plan_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    category_id = Column(Integer, ForeignKey("Categories.category_id"))
    card_id = Column(Integer, ForeignKey("CreditCards.card_id"), nullable=True)
    description = Column(String(255))
    total_amount = Column(Float(53), nullable=False)
    installment_count = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)

class Debt(Base):
    __tablename__ = "Debts"
    debt_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    person_name = Column(String(100), nullable=False)
    amount = Column(Float(53), nullable=False)
    debt_type = Column(String(20), nullable=False)
    due_date = Column(Date)
    is_paid = Column(Boolean, default=False)

class Transaction(Base):
    __tablename__ = "Transactions"
    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    category_id = Column(Integer, ForeignKey("Categories.category_id"))
    card_id = Column(Integer, ForeignKey("CreditCards.card_id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("InstallmentPlans.plan_id"), nullable=True)
    debt_id = Column(Integer, ForeignKey("Debts.debt_id"), nullable=True)
    amount = Column(Float(53), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    description = Column(String(255), nullable=True)

class Invoice(Base):
    __tablename__ = "Invoices"
    invoice_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    type = Column(String(50), nullable=False)
    amount = Column(Float(53), nullable=False)
    due_date = Column(Date, nullable=False)
    is_paid = Column(Boolean, default=False)
    # İŞTE EKSİK OLAN HAYATİ SATIR:
    card_id = Column(Integer, ForeignKey("CreditCards.card_id"), nullable=True)
    period_year = Column(Integer)
    period_month = Column(Integer)
    payment_date = Column(Date, nullable=True)