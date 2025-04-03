import random
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from .models import Customer, Store, Staff, Product, Inventory, Transaction, TransactionItem, Promotion, ProductPromotion
import uuid

def generate_sample_data(db: Session):
    """Generate sample data for all tables"""
    try:
        print("Starting sample data generation...")
        
        # Generate basic data
        print("Generating stores...")
        stores = generate_stores(db)
        print(f"Generated {len(stores)} stores")
        
        print("Generating staff...")
        staff = generate_staff(db)
        print(f"Generated {len(staff)} staff members")
        
        print("Generating products...")
        products = generate_products(db)
        print(f"Generated {len(products)} products")
        
        print("Generating customers...")
        customers = generate_customers(db)
        print(f"Generated {len(customers)} customers")
        
        print("Generating promotions...")
        promotions = generate_promotions(db)
        print(f"Generated {len(promotions)} promotions")
        
        # Generate relational data
        print("Generating inventory...")
        inventory = generate_inventory(db, stores, products)
        print(f"Generated {len(inventory)} inventory items")
        
        print("Generating transactions...")
        transactions = generate_transactions(db, customers, stores, staff, products)
        print(f"Generated {len(transactions)} transactions")
        
        print("Generating product promotions...")
        product_promotions = generate_product_promotions(db, products, promotions)
        print(f"Generated {len(product_promotions)} product promotions")
        
        # Commit all data
        print("Committing all data to database...")
        db.commit()
        print("Data committed successfully")
        
        # Verify inventory data
        print("Verifying inventory data...")
        inventory_count = db.query(Inventory).count()
        print(f"Verified inventory count: {inventory_count}")
        
        return {
            'stores': len(stores),
            'staff': len(staff),
            'products': len(products),
            'customers': len(customers),
            'transactions': len(transactions),
            'inventory': inventory_count
        }
    except Exception as e:
        print(f"Error generating sample data: {str(e)}")
        db.rollback()
        raise e

def generate_stores(db: Session, num_stores=5):
    """Generate sample store data"""
    store_data = [
        {
            'store_id': 1,
            'name': 'Downtown Store',
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'phone': '212-555-0001',
            'operating_hours': '9:00 AM - 9:00 PM'
        },
        {
            'store_id': 2,
            'name': 'Suburban Mall',
            'address': '456 Mall Road',
            'city': 'Los Angeles',
            'state': 'CA',
            'zip_code': '90001',
            'phone': '213-555-0002',
            'operating_hours': '10:00 AM - 10:00 PM'
        },
        {
            'store_id': 3,
            'name': 'East Side Shop',
            'address': '789 East Ave',
            'city': 'Chicago',
            'state': 'IL',
            'zip_code': '60601',
            'phone': '312-555-0003',
            'operating_hours': '8:00 AM - 8:00 PM'
        },
        {
            'store_id': 4,
            'name': 'North Outlet',
            'address': '321 North Blvd',
            'city': 'Houston',
            'state': 'TX',
            'zip_code': '77001',
            'phone': '713-555-0004',
            'operating_hours': '9:00 AM - 9:00 PM'
        },
        {
            'store_id': 5,
            'name': 'South Market',
            'address': '654 South St',
            'city': 'Miami',
            'state': 'FL',
            'zip_code': '33101',
            'phone': '305-555-0005',
            'operating_hours': '10:00 AM - 8:00 PM'
        }
    ]
    
    stores = []
    for data in store_data:
        store = Store(**data)
        db.add(store)
        stores.append(store)
    
    # Flush to ensure store IDs are set
    db.flush()
    return stores

def generate_staff(db: Session, num_staff=10):
    """Generate sample staff data"""
    first_names = ['John', 'Jane', 'Emma', 'Chris', 'Anna', 'Lisa', 'Sarah', 'Michael', 'David', 'Rachel']
    last_names = ['Smith', 'Jones', 'Williams', 'Davis', 'Miller', 'Wilson', 'Garcia', 'Brown', 'Taylor', 'Anderson']
    positions = ['Manager', 'Sales Associate', 'Cashier', 'Stock Clerk']
    
    staff = []
    for i in range(num_staff):
        hire_date = datetime.now() - timedelta(days=random.randint(30, 365*3))  # Random hire date within last 3 years
        
        # Generate a unique email using UUID
        unique_id = str(uuid.uuid4())[:8]
        email = f"staff_{unique_id}@retail.com"
        
        staff_member = Staff(
            store_id=random.randint(1, 5),  # Assuming 5 stores
            first_name=random.choice(first_names),
            last_name=random.choice(last_names),
            email=email,
            phone=f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
            position=random.choice(positions),
            hire_date=hire_date
        )
        db.add(staff_member)
        staff.append(staff_member)
    
    return staff

def generate_products(db: Session, num_products=50):
    """Generate sample product data"""
    categories = ['Electronics', 'Clothing', 'Food', 'Home & Garden', 'Sports']
    products = []
    
    # Keep track of used SKUs
    used_skus = set()
    
    for i in range(num_products):
        category = random.choice(categories)
        unit_cost = round(random.uniform(200, 1000), 2)
        unit_price = round(unit_cost * 1.5, 2)  # 50% markup
        
        # Generate a unique SKU
        while True:
            sku = f"SKU-{category[:3].upper()}-{str(uuid.uuid4())[:6]}"
            if sku not in used_skus:
                used_skus.add(sku)
                break
        
        product = Product(
            product_id=i+1,  # Explicitly set product_id
            name=f"{category} Item {i+1}",
            sku=sku,
            category=category,
            description=f"Description for {category} item {i+1}",
            unit_cost=unit_cost,
            unit_price=unit_price,
            reorder_point=random.randint(15, 50),
            reorder_quantity=random.randint(50, 200)
        )
        db.add(product)
        products.append(product)
    
    # Flush to ensure product IDs are set
    db.flush()
    return products

def generate_customers(db: Session, num_customers=100):
    """Generate sample customer data"""
    first_names = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Taylor']
    
    customers = []
    for i in range(num_customers):
        # Generate a unique email using UUID
        unique_id = str(uuid.uuid4())[:8]
        email = f"customer_{unique_id}@example.com"
        
        customer = Customer(
            first_name=random.choice(first_names),
            last_name=random.choice(last_names),
            email=email,
            phone=f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
            address=f"{random.randint(100,999)} Customer St"
        )
        db.add(customer)
        customers.append(customer)
    
    return customers

def generate_inventory(db: Session, stores, products):
    """Generate sample inventory data"""
    try:
        inventory_items = []
        print(f"Generating inventory for {len(stores)} stores and {len(products)} products")
        
        # Verify stores and products exist
        if not stores or not products:
            raise ValueError("Stores or products list is empty")
            
        for store in stores:
            if not store.store_id:
                print(f"Warning: Store {store} has no store_id")
                continue
                
            print(f"Processing store {store.store_id}")
            for product in products:
                if not product.product_id:
                    print(f"Warning: Product {product} has no product_id")
                    continue
                    
                print(f"Creating inventory for product {product.product_id} in store {store.store_id}")
                inventory = Inventory(
                    store_id=store.store_id,
                    product_id=product.product_id,
                    quantity=random.randint(0, 200),
                    last_restocked=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.add(inventory)
                inventory_items.append(inventory)
                print(f"Added inventory item: store_id={store.store_id}, product_id={product.product_id}")
        
        # Verify inventory items were created
        if not inventory_items:
            raise ValueError("No inventory items were created")
            
        print(f"Created {len(inventory_items)} inventory items")
        return inventory_items
    except Exception as e:
        print(f"Error generating inventory: {str(e)}")
        db.rollback()
        raise e

def generate_transactions(db: Session, customers, stores, staff, products, num_transactions=1000):
    """Generate sample transaction data with realistic patterns"""
    transactions = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Define seasonal products and their peak seasons
    seasonal_products = {
        'Electronics': {'peak_months': [11, 12], 'multiplier': 3},  # Holiday season
        'Clothing': {'peak_months': [3, 4, 9], 'multiplier': 2},    # Spring and Back to school
        'Food': {'peak_months': [11, 12], 'multiplier': 2},         # Holiday season
        'Home & Garden': {'peak_months': [4, 5, 6], 'multiplier': 2.5},  # Spring/Summer
        'Sports': {'peak_months': [1, 6, 7], 'multiplier': 2}       # New Year and Summer
    }
    
    # Define product bundles (items commonly bought together)
    product_bundles = [
        {'category': 'Electronics', 'bundle_chance': 0.7},
        {'category': 'Sports', 'bundle_chance': 0.6},
        {'category': 'Home & Garden', 'bundle_chance': 0.5}
    ]
    
    # Group products by category for easier access
    products_by_category = {}
    for product in products:
        if product.category not in products_by_category:
            products_by_category[product.category] = []
        products_by_category[product.category].append(product)
    
    for _ in range(num_transactions):
        # Create transaction with seasonal timing bias
        transaction_date = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        
        customer = random.choice(customers)
        store = random.choice(stores)
        staff_member = random.choice(staff)
        
        transaction = Transaction(
            customer_id=customer.customer_id,
            store_id=store.store_id,
            staff_id=staff_member.staff_id,
            transaction_date=transaction_date,
            payment_method=random.choice(['Cash', 'Credit Card', 'Debit Card']),
            total_amount=0  # Will be updated after adding items
        )
        db.add(transaction)
        db.flush()  # Get transaction_id
        
        # Determine number of items based on seasonal factors
        current_month = transaction_date.month
        base_num_items = random.randint(1, 5)
        
        # Increase number of items during holiday season
        if current_month in [11, 12]:
            base_num_items = random.randint(2, 7)
        
        total_amount = 0
        added_categories = set()
        
        # First, add main items
        for _ in range(base_num_items):
            # Select category with seasonal bias
            category_weights = []
            for category in seasonal_products:
                weight = 1.0
                if current_month in seasonal_products[category]['peak_months']:
                    weight = seasonal_products[category]['multiplier']
                category_weights.append(weight)
            
            selected_category = random.choices(list(seasonal_products.keys()), weights=category_weights)[0]
            if selected_category in products_by_category:
                product = random.choice(products_by_category[selected_category])
                
                # Determine quantity based on category and price
                if product.category == 'Electronics':
                    quantity = random.randint(1, 2)  # People rarely buy multiple expensive electronics
                elif product.category == 'Food':
                    quantity = random.randint(1, 8)  # Food items often bought in larger quantities
                else:
                    quantity = random.randint(1, 4)
                
                # Apply seasonal discounts
                unit_price = product.unit_price
                if current_month in seasonal_products[selected_category]['peak_months']:
                    discount = random.uniform(0.1, 0.3)  # 10-30% discount during peak season
                    unit_price = round(unit_price * (1 - discount), 2)
                
                total_price = quantity * unit_price
                
                item = TransactionItem(
                    transaction_id=transaction.transaction_id,
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                db.add(item)
                total_amount += total_price
                added_categories.add(selected_category)
        
        # Then, add bundled items
        for bundle in product_bundles:
            if (bundle['category'] in added_categories and 
                random.random() < bundle['bundle_chance'] and 
                bundle['category'] in products_by_category):
                
                # Add 1-2 related items from same category
                num_bundle_items = random.randint(1, 2)
                for _ in range(num_bundle_items):
                    product = random.choice(products_by_category[bundle['category']])
                    quantity = random.randint(1, 2)
                    
                    # Bundle items often have small discounts
                    unit_price = round(product.unit_price * 0.95, 2)  # 5% bundle discount
                    total_price = quantity * unit_price
                    
                    item = TransactionItem(
                        transaction_id=transaction.transaction_id,
                        product_id=product.product_id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    db.add(item)
                    total_amount += total_price
        
        transaction.total_amount = total_amount
        transactions.append(transaction)
        
        # Commit every 100 transactions to avoid memory issues
        if len(transactions) % 100 == 0:
            db.commit()
    
    return transactions

def generate_promotions(db: Session, num_promotions=10):
    """Generate sample promotion data"""
    promotions = []
    end_date = datetime.now() + timedelta(days=30)
    
    for i in range(num_promotions):
        start_date = datetime.now() + timedelta(days=random.randint(0, 15))
        
        promotion = Promotion(
            name=f"Promotion {i+1}",
            description=f"Description for promotion {i+1}",
            discount_percentage=random.randint(5, 50),
            start_date=start_date,
            end_date=start_date + timedelta(days=random.randint(5, 15))
        )
        db.add(promotion)
        promotions.append(promotion)
    
    return promotions

def generate_product_promotions(db: Session, products, promotions):
    """Generate sample product promotion relationships"""
    product_promotions = []
    
    for promotion in promotions:
        # Each promotion applies to 3-10 random products
        num_products = random.randint(3, 10)
        selected_products = random.sample(products, num_products)
        
        for product in selected_products:
            product_promotion = ProductPromotion(
                product_id=product.product_id,
                promotion_id=promotion.promotion_id
            )
            db.add(product_promotion)
            product_promotions.append(product_promotion)
    
    return product_promotions 