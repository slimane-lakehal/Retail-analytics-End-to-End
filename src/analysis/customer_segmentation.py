import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.models import Customer, Transaction, TransactionItem
from ..database.db_connection import get_db
from sqlalchemy.sql import text

def calculate_rfm_metrics(db: Session, days_back=365):
    """
    Calculate RFM (Recency, Frequency, Monetary) metrics for each customer
    """
    try:
        # Get cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Query transactions with direct SQL for better performance
        query = """
            SELECT 
                t.customer_id,
                MAX(t.transaction_date) as last_purchase,
                COUNT(DISTINCT t.transaction_id) as frequency,
                SUM(t.total_amount) as monetary
            FROM transactions t
            WHERE t.transaction_date >= :cutoff_date
                AND t.customer_id IS NOT NULL
            GROUP BY t.customer_id
        """
        
        # Execute query
        result = db.execute(text(query), {'cutoff_date': cutoff_date})
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall(), columns=['customer_id', 'last_purchase', 'frequency', 'monetary'])
        
        # Calculate recency
        df['last_purchase'] = pd.to_datetime(df['last_purchase'])
        df['recency'] = (datetime.now() - df['last_purchase']).dt.days
        
        # Drop last_purchase column as it's no longer needed
        df = df.drop('last_purchase', axis=1)
        
        return df
    except Exception as e:
        raise Exception(f"Error calculating RFM metrics: {str(e)}")

def segment_customers(rfm_data):
    """
    Segment customers using RFM scores
    """
    try:
        # Create R, F, and M quartiles
        r_labels = range(4, 0, -1)  # 4 is best, 1 is worst
        f_labels = range(1, 5)      # 1 is worst, 4 is best
        m_labels = range(1, 5)      # 1 is worst, 4 is best
        
        r_quartiles = pd.qcut(rfm_data['recency'], q=4, labels=r_labels)
        f_quartiles = pd.qcut(rfm_data['frequency'], q=4, labels=f_labels)
        m_quartiles = pd.qcut(rfm_data['monetary'], q=4, labels=m_labels)
        
        # Create RFM segmentation
        rfm_data['r_score'] = r_quartiles
        rfm_data['f_score'] = f_quartiles
        rfm_data['m_score'] = m_quartiles
        
        # Calculate RFM Score
        rfm_data['rfm_score'] = (
            rfm_data['r_score'].astype(str) +
            rfm_data['f_score'].astype(str) +
            rfm_data['m_score'].astype(str)
        )
        
        # Segment customers
        def segment_label(row):
            if row['rfm_score'] in ['444', '434', '443', '433']:
                return 'Best Customers'
            elif row['r_score'] == 4:
                return 'Lost Customers'
            elif row['f_score'] == 4 and row['m_score'] == 4:
                return 'Loyal Customers'
            elif row['m_score'] == 4:
                return 'Big Spenders'
            elif row['f_score'] == 4:
                return 'Regular Customers'
            else:
                return 'Average Customers'
        
        rfm_data['segment'] = rfm_data.apply(segment_label, axis=1)
        
        # Calculate segment statistics
        segment_stats = rfm_data.groupby('segment').agg({
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean',
            'customer_id': 'count'
        }).round(2)
        
        segment_stats.columns = ['Avg Recency (days)', 'Avg Frequency', 'Avg Monetary', 'Count']
        segment_stats['Percentage'] = (segment_stats['Count'] / len(rfm_data) * 100).round(2)
        
        return rfm_data, segment_stats
    except Exception as e:
        raise Exception(f"Error segmenting customers: {str(e)}")

def analyze_customer_segments(rfm_data):
    """
    Analyze customer segments and provide insights
    """
    try:
        segment_analysis = rfm_data.groupby('segment').agg({
            'recency': ['mean', 'min', 'max'],
            'frequency': ['mean', 'min', 'max'],
            'monetary': ['mean', 'min', 'max'],
            'customer_id': 'count'
        })
        
        # Flatten column names
        segment_analysis.columns = [
            f"{col[0]}_{col[1]}" for col in segment_analysis.columns
        ]
        
        # Calculate percentage of total customers
        total_customers = len(rfm_data)
        segment_analysis['percentage'] = (
            segment_analysis['customer_id_count'] / total_customers * 100
        ).round(2)
        
        return segment_analysis
    except Exception as e:
        raise Exception(f"Error analyzing customer segments: {str(e)}")

def get_customer_segmentation_insights(db):
    """Get customer segmentation insights using RFM analysis"""
    try:
        # Get transaction data
        query = text("""
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                COUNT(t.transaction_id) as frequency,
                COALESCE(SUM(t.total_amount), 0) as monetary,
                MAX(t.transaction_date) as last_purchase
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
        """)
        
        df = pd.read_sql(query, db.bind)
        
        if df.empty:
            return {
                'rfm_data': pd.DataFrame(),
                'segment_analysis': pd.DataFrame(),
                'segment_stats': pd.DataFrame(),
                'cluster_stats': pd.DataFrame()
            }
        
        # Calculate RFM metrics
        now = pd.Timestamp.now(tz=None)  # Use timezone-naive timestamp
        df['last_purchase'] = pd.to_datetime(df['last_purchase']).dt.tz_localize(None)  # Remove timezone
        df['recency'] = (now - df['last_purchase']).dt.days
        df['frequency'] = df['frequency'].fillna(0)
        df['monetary'] = df['monetary'].fillna(0)
        
        # Handle customers with no purchases
        df['recency'] = df['recency'].fillna(365)  # Assume 1 year for new customers
        
        # Calculate RFM scores
        r_labels = range(4, 0, -1)
        f_labels = range(1, 5)
        m_labels = range(1, 5)
        
        # Handle case when there's only one unique value
        if len(df['recency'].unique()) < 4:
            r_quartiles = pd.Series([2] * len(df), index=df.index)  # Assign middle value
        else:
            r_quartiles = pd.qcut(df['recency'], q=4, labels=r_labels)
            
        if len(df['frequency'].unique()) < 4:
            f_quartiles = pd.Series([2] * len(df), index=df.index)
        else:
            f_quartiles = pd.qcut(df['frequency'], q=4, labels=f_labels)
            
        if len(df['monetary'].unique()) < 4:
            m_quartiles = pd.Series([2] * len(df), index=df.index)
        else:
            m_quartiles = pd.qcut(df['monetary'], q=4, labels=m_labels)
        
        df['R'] = r_quartiles
        df['F'] = f_quartiles
        df['M'] = m_quartiles
        
        # Calculate RFM Score
        df['RFM_Score'] = df['R'].astype(str) + df['F'].astype(str) + df['M'].astype(str)
        
        # Segment customers
        df['Segment'] = df.apply(segment_customers, axis=1)
        
        # Calculate segment statistics
        segment_stats = df.groupby('Segment').agg({
            'customer_id': 'count',
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': ['mean', 'sum']
        }).round(2)
        
        # Flatten column names
        segment_stats.columns = [
            'count', 'avg_recency', 'avg_frequency',
            'avg_monetary', 'total_monetary'
        ]
        
        # Calculate segment percentages
        total_customers = len(df)
        segment_stats['percentage'] = (segment_stats['count'] / total_customers * 100).round(2)
        
        # Calculate cluster statistics
        cluster_stats = df.groupby('Segment').agg({
            'recency': ['mean', 'min', 'max'],
            'frequency': ['mean', 'min', 'max'],
            'monetary': ['mean', 'min', 'max']
        }).round(2)
        
        # Flatten cluster_stats column names
        cluster_stats.columns = [
            f"{col[0]}_{col[1]}" for col in cluster_stats.columns
        ]
        
        return {
            'rfm_data': df,
            'segment_analysis': segment_stats,
            'segment_stats': segment_stats,  # Add this for backward compatibility
            'cluster_stats': cluster_stats
        }
        
    except Exception as e:
        print(f"Error in customer segmentation: {str(e)}")
        return {
            'rfm_data': pd.DataFrame(),
            'segment_analysis': pd.DataFrame(),
            'segment_stats': pd.DataFrame(),
            'cluster_stats': pd.DataFrame()
        }

def segment_customers(row):
    """Segment customers based on RFM scores"""
    if row['R'] == 4 and row['F'] == 4 and row['M'] == 4:
        return 'Best Customers'
    elif row['F'] == 4 and row['M'] == 4:
        return 'Loyal Customers'
    elif row['M'] == 4:
        return 'Big Spenders'
    elif row['R'] == 1:
        return 'Lost Customers'
    elif row['R'] == 4:
        return 'Recent Customers'
    else:
        return 'Average Customers'

def get_segment_characteristics(df):
    """Get detailed characteristics for each segment"""
    return df.groupby('Segment').agg({
        'recency': ['mean', 'min', 'max'],
        'frequency': ['mean', 'min', 'max'],
        'monetary': ['mean', 'min', 'max']
    }).round(2)

def get_segment_recommendations(segment_analysis):
    """
    Generate recommendations for each customer segment
    """
    recommendations = {
        'Lost Customers': [
            'Re-engagement campaigns',
            'Special win-back offers',
            'Personalized communication'
        ],
        'At Risk Customers': [
            'Loyalty program incentives',
            'Targeted promotions',
            'Customer feedback surveys'
        ],
        'Regular Customers': [
            'Cross-selling opportunities',
            'Upselling campaigns',
            'Referral program'
        ],
        'Loyal Customers': [
            'VIP treatment',
            'Exclusive offers',
            'Early access to new products'
        ],
        'Champions': [
            'Brand ambassador program',
            'Premium loyalty rewards',
            'Co-creation opportunities'
        ]
    }
    
    return recommendations 