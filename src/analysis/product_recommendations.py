import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from ..database.models import Transaction, TransactionItem, Product
from ..database.db_connection import get_db
from datetime import datetime, timedelta
from sqlalchemy import text

def prepare_transaction_data(db: Session, days_back=90):
    """
    Prepare transaction data for analysis
    """
    # Get cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Query transactions
    transactions = db.query(
        Transaction.transaction_id,
        TransactionItem.product_id,
        Product.name,
        Product.category
    ).join(
        TransactionItem,
        Transaction.transaction_id == TransactionItem.transaction_id
    ).join(
        Product,
        TransactionItem.product_id == Product.product_id
    ).filter(
        Transaction.transaction_date >= cutoff_date
    ).all()
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions, columns=[
        'transaction_id', 'product_id', 'product_name', 'category'
    ])
    
    return df

def generate_association_rules(transaction_data, min_support=0.01, min_confidence=0.5):
    """
    Generate association rules using Apriori algorithm
    """
    # Create transaction matrix
    transaction_matrix = pd.crosstab(
        transaction_data['transaction_id'],
        transaction_data['product_name']
    )
    
    # Convert to binary values (0/1)
    transaction_matrix = (transaction_matrix > 0).astype(int)
    
    # Generate frequent itemsets
    frequent_itemsets = apriori(
        transaction_matrix,
        min_support=min_support,
        use_colnames=True
    )
    
    # Generate association rules
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence
    )
    
    return rules

def create_product_similarity_matrix(transaction_data):
    """
    Create product similarity matrix using collaborative filtering
    """
    # Create user-item matrix
    user_item_matrix = pd.crosstab(
        transaction_data['transaction_id'],
        transaction_data['product_id']
    )
    
    # Calculate cosine similarity
    similarity_matrix = cosine_similarity(user_item_matrix.T)
    similarity_df = pd.DataFrame(
        similarity_matrix,
        index=user_item_matrix.columns,
        columns=user_item_matrix.columns
    )
    
    return similarity_df

def get_product_recommendations(product_id, similarity_matrix, n_recommendations=5):
    """
    Get product recommendations based on similarity
    """
    # Get similarity scores for the product
    product_similarities = similarity_matrix[product_id]
    
    # Sort by similarity and get top recommendations
    recommendations = product_similarities.sort_values(ascending=False)[1:n_recommendations+1]
    
    return recommendations

def analyze_product_categories(transaction_data):
    """
    Analyze product categories and their relationships
    """
    # Calculate category co-occurrence
    category_matrix = pd.crosstab(
        transaction_data['transaction_id'],
        transaction_data['category']
    )
    
    # Calculate category correlations
    category_correlations = category_matrix.corr()
    
    return category_correlations

def get_comprehensive_recommendations(db, product_id):
    """Get comprehensive product recommendations"""
    try:
        # Get product details
        product_query = text("""
            SELECT 
                p.product_id,
                p.name as product_name,
                p.category
            FROM products p
            WHERE p.product_id = :product_id
        """)
        
        product_details = pd.read_sql(product_query, db.bind, params={'product_id': product_id})
        
        if product_details.empty:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Get co-purchase patterns
        co_purchase_query = text("""
            WITH product_purchases AS (
                SELECT 
                    ti.product_id,
                    t.transaction_id,
                    p.name as product_name,
                    p.category,
                    ti.quantity
                FROM transaction_items ti
                JOIN transactions t ON ti.transaction_id = t.transaction_id
                JOIN products p ON ti.product_id = p.product_id
                WHERE t.transaction_date >= NOW() - INTERVAL '90 days'
            )
            SELECT 
                p1.product_id,
                p1.product_name,
                p1.category,
                p2.product_id as related_product_id,
                p2.product_name as related_product_name,
                p2.category as related_category,
                COUNT(DISTINCT p1.transaction_id) as co_purchase_count
            FROM product_purchases p1
            JOIN product_purchases p2 ON p1.transaction_id = p2.transaction_id
            WHERE p1.product_id = :product_id
                AND p1.product_id != p2.product_id
            GROUP BY p1.product_id, p1.product_name, p1.category,
                     p2.product_id, p2.product_name, p2.category
            ORDER BY co_purchase_count DESC
            LIMIT 5
        """)
        
        frequently_bought = pd.read_sql(co_purchase_query, db.bind, params={'product_id': product_id})
        
        # Get product similarity based on purchase patterns
        similarity_query = text("""
            WITH customer_product_matrix AS (
                SELECT 
                    t.customer_id,
                    ti.product_id,
                    p.name as product_name,
                    p.category,
                    SUM(ti.quantity) as quantity
                FROM transaction_items ti
                JOIN transactions t ON ti.transaction_id = t.transaction_id
                JOIN products p ON ti.product_id = p.product_id
                GROUP BY t.customer_id, ti.product_id, p.name, p.category
            )
            SELECT 
                m1.product_id,
                m1.product_name,
                m1.category,
                m2.product_id as similar_product_id,
                m2.product_name as similar_product_name,
                m2.category as similar_category,
                COUNT(DISTINCT m1.customer_id) as common_customers
            FROM customer_product_matrix m1
            JOIN customer_product_matrix m2 ON m1.customer_id = m2.customer_id
            WHERE m1.product_id = :product_id
                AND m1.product_id != m2.product_id
            GROUP BY m1.product_id, m1.product_name, m1.category,
                     m2.product_id, m2.product_name, m2.category
            ORDER BY common_customers DESC
            LIMIT 10
        """)
        
        similar_products = pd.read_sql(similarity_query, db.bind, params={'product_id': product_id})
        
        # Get category analysis
        category_query = text("""
            SELECT 
                p.category,
                COUNT(DISTINCT t.transaction_id) as transaction_count,
                SUM(ti.quantity) as total_quantity,
                SUM(ti.quantity * ti.unit_price) as total_revenue,
                COUNT(DISTINCT p.product_id) as product_count
            FROM products p
            JOIN transaction_items ti ON p.product_id = ti.product_id
            JOIN transactions t ON ti.transaction_id = t.transaction_id
            WHERE t.transaction_date >= NOW() - INTERVAL '90 days'
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """)
        
        category_analysis = pd.read_sql(category_query, db.bind)
        
        return {
            'similar_products': similar_products,
            'frequently_bought_together': frequently_bought,
            'category_analysis': category_analysis
        }
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return {
            'similar_products': pd.DataFrame(),
            'frequently_bought_together': pd.DataFrame(),
            'category_analysis': pd.DataFrame()
        }

def generate_recommendation_insights(recommendation_results):
    """
    Generate insights from recommendation results
    """
    insights = []
    
    # Analyze association rules
    strong_rules = recommendation_results['association_rules'][
        (recommendation_results['association_rules']['lift'] > 2) &
        (recommendation_results['association_rules']['confidence'] > 0.7)
    ]
    
    if len(strong_rules) > 0:
        insights.append(
            f"Found {len(strong_rules)} strong product associations for cross-selling"
        )
    
    # Analyze category relationships
    category_correlations = recommendation_results['category_analysis']
    strong_category_pairs = category_correlations[
        category_correlations > 0.5
    ].stack().reset_index()
    
    if len(strong_category_pairs) > 0:
        insights.append(
            f"Identified {len(strong_category_pairs)} strong category relationships"
        )
    
    return insights

def get_recommendation_strategies(recommendation_results):
    """
    Generate recommendation strategies based on analysis
    """
    strategies = []
    
    # Cross-selling opportunities
    strong_rules = recommendation_results['association_rules'][
        recommendation_results['association_rules']['lift'] > 2
    ]
    if len(strong_rules) > 0:
        strategies.append({
            'type': 'Cross-selling',
            'description': 'Bundle frequently co-purchased products',
            'products': strong_rules[['antecedents', 'consequents']].head(5)
        })
    
    # Category-based recommendations
    category_correlations = recommendation_results['category_analysis']
    strong_categories = category_correlations[
        category_correlations > 0.5
    ].stack().reset_index()
    
    if len(strong_categories) > 0:
        strategies.append({
            'type': 'Category-based',
            'description': 'Promote complementary categories together',
            'categories': strong_categories.head(5)
        })
    
    return strategies 