import os
import sys
from dotenv import load_dotenv
from sqlalchemy.sql import text

# Load environment variables
load_dotenv()

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set database URL explicitly
os.environ['DATABASE_URL'] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

from src.database.db_connection import get_db, SessionLocal, init_db
from src.database.data_pipeline import DataPipeline
from src.analysis.customer_segmentation import get_customer_segmentation_insights
from src.analysis.demand_forecasting import get_demand_forecast
from src.analysis.inventory_optimization import get_inventory_optimization_insights
from src.analysis.product_recommendations import get_comprehensive_recommendations
from src.visualization.charts import (
    create_sales_trend_chart,
    create_customer_segmentation_chart,
    create_inventory_status_chart,
    create_product_performance_chart
)

def get_products(db):
    """Get list of products from database"""
    query = text("""
        SELECT product_id, name, category
        FROM products
        ORDER BY name
    """)
    return pd.read_sql(query, db.bind)

def display_demand_forecasting():
    st.header("Demand Forecasting")
    
    if not st.session_state.data_loaded:
        st.info("Please load the data using the button in the sidebar.")
        return
        
    # Get list of products
    db = SessionLocal()
    try:
        products = get_products(db)
        if products.empty:
            st.warning("No products found in the database.")
            return
        
        # Product selection
        selected_product = st.selectbox(
            "Select a product:",
            options=products['product_id'].tolist(),
            format_func=lambda x: products[products['product_id'] == x]['name'].iloc[0]
        )
        
        # Forecast periods selection
        forecast_periods = st.slider(
            "Forecast periods (days):",
            min_value=7,
            max_value=90,
            value=30,
            step=7
        )
        
        if st.button("Generate Forecast"):
            with st.spinner("Generating forecast..."):
                forecast_result = get_demand_forecast(db, selected_product, forecast_periods)
                
                if 'error' in forecast_result:
                    st.error(forecast_result['error'])
                    return
                
                forecast_df = forecast_result['forecast']
                accuracy = forecast_result['accuracy']
                seasonality = forecast_result['seasonality']
                
                if not forecast_df.empty:
                    # Create forecast plot
                    fig = go.Figure()
                    
                    # Add historical data
                    historical_mask = forecast_df['ds'] <= pd.Timestamp.now()
                    fig.add_trace(go.Scatter(
                        x=forecast_df.loc[historical_mask, 'ds'],
                        y=forecast_df.loc[historical_mask, 'yhat'],
                        name='Historical',
                        line=dict(color='blue')
                    ))
                    
                    # Add forecast
                    forecast_mask = forecast_df['ds'] > pd.Timestamp.now()
                    fig.add_trace(go.Scatter(
                        x=forecast_df.loc[forecast_mask, 'ds'],
                        y=forecast_df.loc[forecast_mask, 'yhat'],
                        name='Forecast',
                        line=dict(color='red', dash='dash')
                    ))
                    
                    # Add confidence interval
                    fig.add_trace(go.Scatter(
                        x=forecast_df.loc[forecast_mask, 'ds'],
                        y=forecast_df.loc[forecast_mask, 'yhat_upper'],
                        fill=None,
                        mode='lines',
                        line_color='rgba(255,0,0,0)',
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=forecast_df.loc[forecast_mask, 'ds'],
                        y=forecast_df.loc[forecast_mask, 'yhat_lower'],
                        fill='tonexty',
                        mode='lines',
                        line_color='rgba(255,0,0,0)',
                        name='95% Confidence Interval',
                        fillcolor='rgba(255,0,0,0.2)'
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title=f"Demand Forecast for {products[products['product_id'] == selected_product]['name'].iloc[0]}",
                        xaxis_title="Date",
                        yaxis_title="Quantity",
                        hovermode='x unified',
                        font=dict(size=12),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display accuracy metrics
                    if accuracy['mae'] is not None:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("MAE", f"{accuracy['mae']:.2f}")
                        with col2:
                            st.metric("MAPE", f"{accuracy['mape']:.2%}")
                        with col3:
                            st.metric("RMSE", f"{accuracy['rmse']:.2f}")
                        with col4:
                            st.metric("R²", f"{accuracy['r2']:.3f}")
                    
                    # Display seasonal patterns
                    if seasonality:
                        st.subheader("Seasonal Patterns")
                        
                        tab1, tab2, tab3 = st.tabs(["Weekly", "Monthly", "Yearly"])
                        
                        with tab1:
                            if seasonality['weekly']:
                                weekly_df = pd.DataFrame(seasonality['weekly'])
                                fig_weekly = px.bar(
                                    weekly_df,
                                    x='day',
                                    y='weekly',
                                    title='Weekly Seasonality Pattern',
                                    labels={
                                        'day': 'Day of Week',
                                        'weekly': 'Seasonal Effect'
                                    }
                                )
                                fig_weekly.update_layout(
                                    xaxis_title="Day of Week",
                                    yaxis_title="Seasonal Effect",
                                    font=dict(size=12)
                                )
                                st.plotly_chart(fig_weekly, use_container_width=True)
                        
                        with tab2:
                            if seasonality['monthly']:
                                monthly_df = pd.DataFrame(seasonality['monthly'])
                                fig_monthly = px.line(
                                    monthly_df,
                                    x='day_of_month',
                                    y='monthly',
                                    title='Monthly Seasonality Pattern',
                                    labels={
                                        'day_of_month': 'Day of Month',
                                        'monthly': 'Seasonal Effect'
                                    }
                                )
                                fig_monthly.update_layout(
                                    xaxis_title="Day of Month",
                                    yaxis_title="Seasonal Effect",
                                    font=dict(size=12)
                                )
                                st.plotly_chart(fig_monthly, use_container_width=True)
                        
                        with tab3:
                            if seasonality['yearly']:
                                yearly_df = pd.DataFrame(seasonality['yearly'])
                                fig_yearly = px.line(
                                    yearly_df,
                                    x='month',
                                    y='yearly',
                                    title='Yearly Seasonality Pattern',
                                    labels={
                                        'month': 'Month',
                                        'yearly': 'Seasonal Effect'
                                    }
                                )
                                fig_yearly.update_layout(
                                    xaxis_title="Month",
                                    yaxis_title="Seasonal Effect",
                                    font=dict(size=12)
                                )
                                fig_yearly.update_xaxes(
                                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                                    tickvals=list(range(1, 13))
                                )
                                st.plotly_chart(fig_yearly, use_container_width=True)
                else:
                    st.warning("Not enough data to generate forecast.")
    except Exception as e:
        st.error(f"Error in demand forecasting: {str(e)}")
    finally:
        db.close()

# Page configuration
st.set_page_config(
    page_title="Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Retail Analytics Dashboard")
st.markdown("""
This dashboard provides comprehensive retail analytics including:
- Customer Segmentation
- Demand Forecasting
- Inventory Optimization
- Product Recommendations
""")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a Page",
    ["Overview", "Customer Segmentation", "Demand Forecasting", 
     "Inventory Optimization", "Product Recommendations"]
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.db_initialized = False

def initialize_database():
    """Initialize the database schema"""
    try:
        init_db()
        st.session_state.db_initialized = True
        return True
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        return False

def load_data():
    """Load all necessary data"""
    if not st.session_state.db_initialized:
        if not initialize_database():
            return False
    
    with st.spinner("Loading data..."):
        db = SessionLocal()
        try:
            # Check if we have data in the database
            result = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
            
            # If no data exists, generate sample data
            if result == 0:
                st.info("No data found in database. Generating sample data...")
                from src.database.sample_data import generate_sample_data
                generate_sample_data(db)
                st.success("Sample data generated successfully!")
            
            # Load data through pipeline
            pipeline = DataPipeline(db)
            data = pipeline.run_pipeline()
            st.session_state.data = data
            st.session_state.data_loaded = True
            return True
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
        finally:
            db.close()

# Load data button
if not st.session_state.data_loaded:
    if st.sidebar.button("Load Data"):
        load_data()

# Overview Page
if page == "Overview":
    if st.session_state.data_loaded:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Sales Trends")
            fig_sales = create_sales_trend_chart(
                st.session_state.data['transaction_data'],
                time_column='transaction_date',
                value_column='total_amount'
            )
            st.plotly_chart(fig_sales, use_container_width=True)
        
        with col2:
            st.subheader("Inventory Status")
            fig_inventory = create_inventory_status_chart(
                st.session_state.data['inventory_data']
            )
            st.plotly_chart(fig_inventory, use_container_width=True)
    else:
        st.info("Please load the data using the button in the sidebar.")

# Customer Segmentation Page
elif page == "Customer Segmentation":
    st.header("Customer Segmentation")
    
    if st.session_state.data_loaded:
        with st.spinner("Analyzing customer segments..."):
            db = SessionLocal()
            try:
                segmentation_result = get_customer_segmentation_insights(db)
                
                if not segmentation_result['segment_analysis'].empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Customer Segments Distribution")
                        fig_segments = create_customer_segmentation_chart(
                            segmentation_result['segment_analysis']
                        )
                        st.plotly_chart(fig_segments, use_container_width=True)
                    
                    with col2:
                        st.subheader("Segment Characteristics")
                        if not segmentation_result['cluster_stats'].empty:
                            cluster_stats = segmentation_result['cluster_stats'].copy()
                            # Format monetary values
                            for col in cluster_stats.columns:
                                if 'monetary' in col:
                                    cluster_stats[col] = cluster_stats[col].apply(lambda x: f"${x:,.2f}")
                            st.dataframe(cluster_stats, use_container_width=True)
                        else:
                            st.info("No segment characteristics data available.")
                    
                    # Display segment analysis
                    st.subheader("Segment Analysis")
                    segment_stats = segmentation_result['segment_analysis'].copy()
                    # Format monetary and percentage columns
                    segment_stats['avg_monetary'] = segment_stats['avg_monetary'].apply(lambda x: f"${x:,.2f}")
                    segment_stats['total_monetary'] = segment_stats['total_monetary'].apply(lambda x: f"${x:,.2f}")
                    segment_stats['percentage'] = segment_stats['percentage'].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(segment_stats, use_container_width=True)
                    
                    # Display customer details
                    st.subheader("Customer Details")
                    if not segmentation_result['rfm_data'].empty:
                        rfm_data = segmentation_result['rfm_data'].copy()
                        # Format monetary values
                        rfm_data['monetary'] = rfm_data['monetary'].apply(lambda x: f"${x:,.2f}")
                        st.dataframe(rfm_data, use_container_width=True)
                    else:
                        st.info("No customer details available.")
                else:
                    st.warning("No customer data available for segmentation.")
            except Exception as e:
                st.error(f"Error analyzing customer segments: {str(e)}")
            finally:
                db.close()
    else:
        st.info("Please load the data using the button in the sidebar.")

# Demand Forecasting Page
elif page == "Demand Forecasting":
    display_demand_forecasting()

# Inventory Optimization Page
elif page == "Inventory Optimization":
    st.header("Inventory Optimization")
    
    if st.session_state.data_loaded:
        with st.spinner("Analyzing inventory..."):
            db = SessionLocal()
            try:
                inventory_result = get_inventory_optimization_insights(db)
                
                if not inventory_result['inventory_metrics'].empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Current Inventory Status")
                        fig_inventory = create_inventory_status_chart(
                            inventory_result['inventory_metrics']
                        )
                        st.plotly_chart(fig_inventory, use_container_width=True)
                    
                    with col2:
                        st.subheader("ABC Analysis")
                        abc_df = inventory_result['abc_analysis'].copy()
                        # Format currency columns
                        abc_df['total_value'] = abc_df['total_value'].apply(lambda x: f"${x:,.2f}")
                        abc_df['potential_revenue'] = abc_df['potential_revenue'].apply(lambda x: f"${x:,.2f}")
                        st.dataframe(abc_df)
                    
                    st.subheader("Optimization Recommendations")
                    if not inventory_result['optimization_results'].empty:
                        opt_df = inventory_result['optimization_results'].copy()
                        # Round numeric columns
                        numeric_cols = ['eoq', 'safety_stock', 'reorder_point']
                        opt_df[numeric_cols] = opt_df[numeric_cols].round(0)
                        st.dataframe(opt_df)
                    else:
                        st.info("No optimization recommendations available. This could be due to insufficient sales history.")
                    
                    # Add summary metrics
                    st.subheader("Inventory Summary")
                    metrics_df = inventory_result['inventory_metrics']
                    col1, col2, col3 = st.columns(3)
                    
                    total_value = metrics_df['total_value'].sum()
                    low_stock_count = len(metrics_df[metrics_df['quantity'] <= metrics_df['reorder_point']])
                    avg_stock = metrics_df['quantity'].mean()
                    
                    col1.metric(
                        "Total Inventory Value",
                        f"${total_value:,.2f}"
                    )
                    col2.metric(
                        "Low Stock Items",
                        f"{low_stock_count}"
                    )
                    col3.metric(
                        "Average Stock Level",
                        f"{avg_stock:.1f}"
                    )
                else:
                    st.warning("No inventory data available. Please check your database connection and data.")
            except Exception as e:
                st.error(f"Error analyzing inventory: {str(e)}")
            finally:
                db.close()
    else:
        st.info("Please load the data using the button in the sidebar.")

# Product Recommendations Page
elif page == "Product Recommendations":
    st.header("Product Recommendations")
    
    if st.session_state.data_loaded:
        # Product selection
        products = st.session_state.data['product_data']
        product_options = [
            {'label': f"{row['name']} ({row['category']})", 'value': row['product_id']}
            for _, row in products.iterrows()
        ]
        
        selected_product = st.selectbox(
            "Select Product",
            options=[opt['value'] for opt in product_options],
            format_func=lambda x: next(
                opt['label'] for opt in product_options if opt['value'] == x
            )
        )
        
        if selected_product:
            with st.spinner("Generating recommendations..."):
                db = SessionLocal()
                try:
                    recommendations = get_comprehensive_recommendations(db, product_id=selected_product)
                    
                    if not recommendations['similar_products'].empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Similar Products")
                            similar_df = recommendations['similar_products'].copy()
                            similar_df = similar_df[[
                                'similar_product_name', 'similar_category', 'common_customers'
                            ]].rename(columns={
                                'similar_product_name': 'Product Name',
                                'similar_category': 'Category',
                                'common_customers': 'Common Customers'
                            })
                            st.dataframe(similar_df, use_container_width=True)
                        
                        with col2:
                            st.subheader("Frequently Bought Together")
                            freq_df = recommendations['frequently_bought_together'].copy()
                            freq_df = freq_df[[
                                'related_product_name', 'related_category', 'co_purchase_count'
                            ]].rename(columns={
                                'related_product_name': 'Product Name',
                                'related_category': 'Category',
                                'co_purchase_count': 'Co-purchase Count'
                            })
                            st.dataframe(freq_df, use_container_width=True)
                        
                        # Category Analysis
                        st.subheader("Category Performance")
                        cat_df = recommendations['category_analysis'].copy()
                        cat_df['avg_revenue_per_transaction'] = cat_df['total_revenue'] / cat_df['transaction_count']
                        
                        # Format monetary values
                        cat_df['total_revenue'] = cat_df['total_revenue'].apply(lambda x: f"${x:,.2f}")
                        cat_df['avg_revenue_per_transaction'] = cat_df['avg_revenue_per_transaction'].apply(lambda x: f"${x:,.2f}")
                        
                        # Rename columns for better display
                        cat_df = cat_df.rename(columns={
                            'category': 'Category',
                            'transaction_count': 'Total Transactions',
                            'total_quantity': 'Total Units Sold',
                            'total_revenue': 'Total Revenue',
                            'product_count': 'Number of Products',
                            'avg_revenue_per_transaction': 'Avg Revenue per Transaction'
                        })
                        
                        st.dataframe(cat_df, use_container_width=True)
                        
                        # Product Similarity Visualization
                        st.subheader("Product Similarity Network")
                        fig = px.scatter(
                            similar_df,
                            x='Common Customers',
                            y='Category',
                            size='Common Customers',
                            color='Category',
                            hover_data=['Product Name'],
                            title=f"Product Similarity Network for {products[products['product_id'] == selected_product]['name'].iloc[0]}"
                        )
                        fig.update_layout(
                            xaxis_title="Number of Common Customers",
                            yaxis_title="Product Category",
                            showlegend=True
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.warning("No recommendations available for this product.")
                except Exception as e:
                    st.error(f"Error generating recommendations: {str(e)}")
                finally:
                    db.close()
    else:
        st.info("Please load the data using the button in the sidebar.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Your Team") 