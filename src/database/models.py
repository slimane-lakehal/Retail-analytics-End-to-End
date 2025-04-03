from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db_connection import Base
from datetime import datetime

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(50))
    state = Column(String(50))
    zip_code = Column(String(20))
    loyalty_points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="customer")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    subcategory = Column(String(50))
    unit_cost = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    reorder_point = Column(Integer)
    reorder_quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inventory_items = relationship("Inventory", back_populates="product")
    transaction_items = relationship("TransactionItem", back_populates="product")
    promotions = relationship("ProductPromotion", back_populates="product")

class Store(Base):
    __tablename__ = "stores"

    store_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    city = Column(String(50))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(20))
    operating_hours = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    staff = relationship("Staff", back_populates="store")
    inventory = relationship("Inventory", back_populates="store")
    transactions = relationship("Transaction", back_populates="store")

class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    position = Column(String(50))
    hire_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="staff")
    transactions = relationship("Transaction", back_populates="staff")

class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False, default=0)
    last_restocked = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="inventory")
    product = relationship("Product", back_populates="inventory_items")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    staff_id = Column(Integer, ForeignKey("staff.staff_id"))
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    staff = relationship("Staff", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction")

class TransactionItem(Base):
    __tablename__ = "transaction_items"

    transaction_item_id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="items")
    product = relationship("Product", back_populates="transaction_items")

class Promotion(Base):
    __tablename__ = "promotions"

    promotion_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    discount_percentage = Column(Float, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    products = relationship("ProductPromotion", back_populates="promotion")

class ProductPromotion(Base):
    __tablename__ = "product_promotions"

    product_promotion_id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.promotion_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    promotion = relationship("Promotion", back_populates="products")
    product = relationship("Product", back_populates="promotions") 