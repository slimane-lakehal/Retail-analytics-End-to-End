import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from ..database.models import *
from ..database.db_connection import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, db: Session):
        self.db = db
    
    def extract_transaction_data(self, start_date, end_date):
        """
        Extract transaction data from the database
        """
        try:
            query = text("""
                SELECT 
                    t.transaction_id,
                    t.transaction_date,
                    t.total_amount,
                    t.payment_method,
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    s.store_id,
                    s.name as store_name,
                    st.staff_id,
                    st.first_name as staff_first_name,
                    st.last_name as staff_last_name
                FROM transactions t
                LEFT JOIN customers c ON t.customer_id = c.customer_id
                LEFT JOIN stores s ON t.store_id = s.store_id
                LEFT JOIN staff st ON t.staff_id = st.staff_id
                WHERE t.transaction_date BETWEEN :start_date AND :end_date
            """)
            
            result = self.db.execute(
                query,
                {
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            logger.error(f"Error extracting transaction data: {e}")
            raise
    
    def extract_inventory_data(self, store_id=None):
        """
        Extract inventory data from the database
        """
        try:
            query = text("""
                SELECT 
                    i.inventory_id,
                    i.store_id,
                    i.product_id,
                    i.quantity,
                    i.last_restocked,
                    p.name as product_name,
                    p.category,
                    p.unit_cost,
                    p.unit_price,
                    p.reorder_point,
                    p.reorder_quantity
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                WHERE (:store_id IS NULL OR i.store_id = :store_id)
            """)
            
            result = self.db.execute(
                query,
                {'store_id': store_id}
            )
            
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            logger.error(f"Error extracting inventory data: {e}")
            raise
    
    def transform_transaction_data(self, df):
        """
        Transform transaction data
        """
        try:
            # Convert date columns
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            # Create derived features
            df['day_of_week'] = df['transaction_date'].dt.day_name()
            df['month'] = df['transaction_date'].dt.month_name()
            df['hour'] = df['transaction_date'].dt.hour
            
            # Calculate customer metrics
            customer_metrics = df.groupby('customer_id').agg({
                'transaction_id': 'count',
                'total_amount': ['sum', 'mean']
            }).reset_index()
            
            customer_metrics.columns = [
                'customer_id',
                'transaction_count',
                'total_spent',
                'average_transaction'
            ]
            
            return df, customer_metrics
        except Exception as e:
            logger.error(f"Error transforming transaction data: {e}")
            raise
    
    def transform_inventory_data(self, df):
        """
        Transform inventory data
        """
        try:
            # Calculate inventory metrics
            df['stock_value'] = df['quantity'] * df['unit_cost']
            df['potential_sales_value'] = df['quantity'] * df['unit_price']
            
            # Calculate days since last restock
            df['days_since_restock'] = (
                datetime.now() - pd.to_datetime(df['last_restocked'])
            ).dt.days
            
            # Calculate stock status
            df['stock_status'] = np.where(
                df['quantity'] <= df['reorder_point'],
                'Low Stock',
                'Adequate'
            )
            
            # Calculate turnover rate
            df['turnover_rate'] = df['quantity'] / df['reorder_quantity']
            
            return df
        except Exception as e:
            logger.error(f"Error transforming inventory data: {e}")
            raise
    
    def load_aggregated_data(self, data, table_name):
        """
        Load aggregated data into the database
        """
        try:
            # Convert DataFrame to dictionary
            records = data.to_dict('records')
            
            # Insert records
            for record in records:
                # Create column list and values list
                columns = list(record.keys())
                values = [record[col] for col in columns]
                
                # Create the SQL query with named parameters
                query = f"""
                    INSERT INTO {table_name} 
                    ({', '.join(columns)})
                    VALUES ({', '.join([f':{col}' for col in columns])})
                    ON CONFLICT DO NOTHING
                """
                
                # Execute with named parameters
                self.db.execute(text(query), record)
            
            self.db.commit()
            logger.info(f"Successfully loaded {len(records)} records into {table_name}")
        except Exception as e:
            logger.error(f"Error loading data into {table_name}: {e}")
            self.db.rollback()
            raise
    
    def run_pipeline(self):
        """Run the complete data pipeline"""
        try:
            logger.info("Starting data pipeline...")
            
            logger.info("Getting transaction data...")
            transaction_data = self._get_transaction_data()
            logger.info(f"Retrieved {len(transaction_data)} transaction records")
            
            logger.info("Getting inventory data...")
            inventory_data = self._get_inventory_data()
            logger.info(f"Retrieved {len(inventory_data)} inventory records")
            
            logger.info("Getting product data...")
            product_data = self._get_product_data()
            logger.info(f"Retrieved {len(product_data)} product records")
            
            logger.info("Getting customer data...")
            customer_data = self._get_customer_data()
            logger.info(f"Retrieved {len(customer_data)} customer records")
            
            logger.info("Data pipeline completed successfully")
            return {
                'transaction_data': transaction_data,
                'inventory_data': inventory_data,
                'product_data': product_data,
                'customer_data': customer_data
            }
        except Exception as e:
            logger.error(f"Error in data pipeline: {str(e)}")
            raise
    
    def _get_transaction_data(self):
        """Get transaction data"""
        query = text("""
            SELECT 
                t.transaction_id,
                t.transaction_date,
                t.customer_id,
                t.store_id,
                t.total_amount,
                ti.product_id,
                ti.quantity,
                ti.unit_price
            FROM transactions t
            JOIN transaction_items ti ON t.transaction_id = ti.transaction_id
            ORDER BY t.transaction_date DESC
        """)
        return pd.read_sql(query, self.db.bind)
    
    def _get_inventory_data(self):
        """Get inventory data"""
        try:
            logger.info("Fetching inventory data...")
            query = text("""
                SELECT 
                    i.inventory_id,
                    i.store_id,
                    i.product_id,
                    i.quantity,
                    i.last_restocked,
                    p.name as product_name,
                    p.category,
                    p.unit_cost,
                    p.unit_price,
                    p.reorder_point,
                    (i.quantity * p.unit_cost) as total_value
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                ORDER BY i.store_id, p.category, p.name
            """)
            
            df = pd.read_sql(query, self.db.bind)
            
            if df.empty:
                logger.warning("No inventory data found")
                return pd.DataFrame(columns=[
                    'inventory_id', 'store_id', 'product_id', 'quantity',
                    'last_restocked', 'product_name', 'category', 'unit_cost',
                    'unit_price', 'reorder_point', 'total_value'
                ])
            
            # Convert last_restocked to datetime
            df['last_restocked'] = pd.to_datetime(df['last_restocked'])
            
            # Calculate additional metrics
            df['days_since_restock'] = (datetime.now() - df['last_restocked']).dt.days
            df['stock_status'] = np.where(df['quantity'] <= df['reorder_point'], 'Low', 'Adequate')
            
            # Ensure numeric columns are float
            numeric_cols = ['quantity', 'unit_cost', 'unit_price', 'total_value']
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            logger.info(f"Retrieved {len(df)} inventory records")
            logger.debug(f"Columns in inventory data: {df.columns.tolist()}")
            
            return df
        except Exception as e:
            logger.error(f"Error getting inventory data: {str(e)}")
            raise
    
    def _get_product_data(self):
        """Get product data"""
        query = text("""
            SELECT 
                p.product_id,
                p.sku,
                p.name,
                p.description,
                p.category,
                p.subcategory,
                p.unit_cost,
                p.unit_price,
                p.reorder_point,
                p.reorder_quantity
            FROM products p
        """)
        return pd.read_sql(query, self.db.bind)
    
    def _get_customer_data(self):
        """Get customer data"""
        query = text("""
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                c.phone,
                COUNT(t.transaction_id) as total_transactions,
                SUM(t.total_amount) as total_spent
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.phone
        """)
        return pd.read_sql(query, self.db.bind)

def run_data_pipeline():
    """
    Run the data pipeline
    """
    db = next(get_db())
    try:
        pipeline = DataPipeline(db)
        return pipeline.run_pipeline()
    finally:
        db.close() 