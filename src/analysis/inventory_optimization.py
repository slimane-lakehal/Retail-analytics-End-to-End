import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.models import Inventory, TransactionItem, Product
from ..database.db_connection import get_db
from sqlalchemy import text

def calculate_inventory_metrics(db: Session, store_id=None):
    """
    Calculate key inventory metrics
    """
    # Base query for inventory
    query = db.query(
        Inventory.product_id,
        Inventory.quantity,
        Product.reorder_point,
        Product.reorder_quantity,
        Product.unit_cost,
        Product.unit_price
    ).join(
        Product,
        Inventory.product_id == Product.product_id
    )
    
    # Filter by store if specified
    if store_id:
        query = query.filter(Inventory.store_id == store_id)
    
    # Execute query and convert to DataFrame
    inventory_data = query.all()
    df = pd.DataFrame(inventory_data, columns=[
        'product_id', 'quantity', 'reorder_point',
        'reorder_quantity', 'unit_cost', 'unit_price'
    ])
    
    # Calculate metrics
    df['stock_value'] = df['quantity'] * df['unit_cost']
    df['potential_sales_value'] = df['quantity'] * df['unit_price']
    df['stock_status'] = np.where(
        df['quantity'] <= df['reorder_point'],
        'Low Stock',
        'Adequate'
    )
    
    return df

def calculate_abc_analysis(inventory_metrics):
    """
    Perform ABC analysis on inventory
    """
    # Sort by stock value
    sorted_inventory = inventory_metrics.sort_values('stock_value', ascending=False)
    
    # Calculate cumulative percentage
    sorted_inventory['cumulative_value'] = sorted_inventory['stock_value'].cumsum()
    total_value = sorted_inventory['stock_value'].sum()
    sorted_inventory['cumulative_percentage'] = (
        sorted_inventory['cumulative_value'] / total_value
    ) * 100
    
    # Assign ABC categories
    sorted_inventory['abc_category'] = np.where(
        sorted_inventory['cumulative_percentage'] <= 80,
        'A',
        np.where(
            sorted_inventory['cumulative_percentage'] <= 95,
            'B',
            'C'
        )
    )
    
    return sorted_inventory

def calculate_eoq(annual_demand, ordering_cost, holding_cost):
    """
    Calculate Economic Order Quantity (EOQ)
    """
    try:
        # Convert inputs to numpy arrays and ensure they're float
        annual_demand = np.asarray(annual_demand, dtype=float)
        holding_cost = np.asarray(holding_cost, dtype=float)
        ordering_cost = float(ordering_cost)
        
        # Validate inputs
        if len(annual_demand) != len(holding_cost):
            raise ValueError(f"Shape mismatch: annual_demand ({len(annual_demand)}) and holding_cost ({len(holding_cost)})")
        
        # Handle zero or negative values
        valid_mask = (annual_demand > 0) & (holding_cost > 0)
        result = np.zeros_like(annual_demand)
        
        # Calculate EOQ only for valid values
        valid_demand = annual_demand[valid_mask]
        valid_holding = holding_cost[valid_mask]
        
        if len(valid_demand) > 0:
            result[valid_mask] = np.sqrt((2 * valid_demand * ordering_cost) / valid_holding)
        
        return pd.Series(result, index=getattr(annual_demand, 'index', None))
    except Exception as e:
        raise Exception(f"Error calculating EOQ: {str(e)}")

def calculate_safety_stock(lead_time_demand, service_level, demand_std):
    """
    Calculate safety stock level
    """
    z_score = norm.ppf(service_level)
    return z_score * demand_std * np.sqrt(lead_time_demand)

def optimize_inventory_levels(inventory_data, sales_history, lead_time=7, service_level=0.95):
    """
    Optimize inventory levels using EOQ and safety stock calculations
    """
    try:
        # Calculate daily demand per product
        daily_demand = sales_history.groupby('product_id')['quantity'].mean()
        annual_demand = daily_demand * 365
        
        # Set cost parameters
        ordering_cost = 50  # Cost per order
        holding_cost_rate = 0.2  # Annual holding cost as percentage of unit cost
        
        # Calculate holding cost per unit
        inventory_with_demand = inventory_data[
            inventory_data['product_id'].isin(annual_demand.index)
        ]
        holding_cost = inventory_with_demand['unit_cost'] * holding_cost_rate
        
        # Ensure annual_demand and holding_cost are aligned
        annual_demand = annual_demand[inventory_with_demand['product_id']]
        
        # Calculate EOQ
        eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
        
        # Calculate demand standard deviation
        demand_std = sales_history.groupby('product_id')['quantity'].std().fillna(0)
        
        # Calculate safety stock
        safety_stock = calculate_safety_stock(lead_time, service_level, demand_std)
        
        # Calculate reorder point
        reorder_point = (daily_demand * lead_time) + safety_stock
        
        # Create recommendations DataFrame
        recommendations = pd.DataFrame({
            'product_id': inventory_with_demand['product_id'],
            'current_quantity': inventory_with_demand['quantity'],
            'eoq': eoq,
            'safety_stock': safety_stock,
            'reorder_point': reorder_point,
            'current_reorder_point': inventory_with_demand['reorder_point']
        })
        
        return recommendations
    except Exception as e:
        raise Exception(f"Error optimizing inventory levels: {str(e)}")

def get_inventory_optimization_insights(db):
    """Get inventory optimization insights using ABC analysis"""
    try:
        # Get inventory data with product details
        query = text("""
            SELECT 
                p.product_id,
                p.name,
                p.category,
                p.unit_cost,
                p.unit_price,
                i.quantity,
                p.reorder_point,
                p.reorder_quantity,
                i.store_id
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
        """)
        
        df = pd.read_sql(query, db.bind)
        
        if df.empty:
            return {
                'inventory_metrics': pd.DataFrame(),
                'abc_analysis': pd.DataFrame(),
                'optimization_results': pd.DataFrame(),
                'recommendations': pd.DataFrame()
            }
        
        # Calculate total value and other metrics
        df['total_value'] = df['unit_cost'] * df['quantity']
        df['potential_revenue'] = df['unit_price'] * df['quantity']
        df['profit_margin'] = df['unit_price'] - df['unit_cost']
        total_value = df['total_value'].sum()
        
        # Perform ABC analysis
        df['cumulative_value'] = df['total_value'].cumsum()
        df['cumulative_percentage'] = (df['cumulative_value'] / total_value * 100).round(2)
        
        # Assign ABC categories
        df['abc_category'] = pd.cut(
            df['cumulative_percentage'],
            bins=[0, 80, 95, 100],
            labels=['A', 'B', 'C']
        ).fillna('C')  # Handle any NaN values
        
        # Calculate inventory metrics by ABC category
        inventory_metrics = df.groupby('abc_category').agg({
            'product_id': 'count',
            'total_value': 'sum',
            'quantity': 'sum',
            'potential_revenue': 'sum'
        }).reset_index()
        
        # Get sales history for optimization
        sales_query = text("""
            SELECT 
                ti.product_id,
                ti.quantity,
                t.transaction_date
            FROM transaction_items ti
            JOIN transactions t ON ti.transaction_id = t.transaction_id
            WHERE t.transaction_date >= NOW() - INTERVAL '1 year'
        """)
        
        sales_history = pd.read_sql(sales_query, db.bind)
        
        if not sales_history.empty:
            # Optimize inventory levels
            optimization_results = optimize_inventory_levels(df, sales_history)
            
            # Generate recommendations
            recommendations = generate_inventory_recommendations(optimization_results)
        else:
            optimization_results = pd.DataFrame()
            recommendations = pd.DataFrame()
        
        return {
            'inventory_metrics': df,
            'abc_analysis': inventory_metrics,
            'optimization_results': optimization_results,
            'recommendations': recommendations
        }
        
    except Exception as e:
        print(f"Error in inventory optimization: {str(e)}")
        return {
            'inventory_metrics': pd.DataFrame(),
            'abc_analysis': pd.DataFrame(),
            'optimization_results': pd.DataFrame(),
            'recommendations': pd.DataFrame()
        }

def generate_inventory_recommendations(optimization_results):
    """Generate inventory recommendations based on optimization results"""
    recommendations = []
    
    for _, row in optimization_results.iterrows():
        if row['current_quantity'] <= row['reorder_point']:
            recommendations.append({
                'product_id': row['product_id'],
                'action': 'Reorder',
                'current_quantity': row['current_quantity'],
                'recommended_quantity': row['eoq'],
                'reorder_point': row['reorder_point']
            })
        elif row['current_quantity'] > row['reorder_point'] * 2:
            recommendations.append({
                'product_id': row['product_id'],
                'action': 'Reduce Stock',
                'current_quantity': row['current_quantity'],
                'recommended_quantity': row['reorder_point'] + row['safety_stock'],
                'reorder_point': row['reorder_point']
            })
    
    return pd.DataFrame(recommendations) 