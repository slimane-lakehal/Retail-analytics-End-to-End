import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.models import Transaction, TransactionItem, Product
from ..database.db_connection import get_db
from sqlalchemy.sql import text
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score

def prepare_time_series_data(db: Session, product_id=None, days_back=365):
    """
    Prepare time series data for forecasting
    """
    # Get cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        # Query transactions with direct SQL for better performance
        query = """
            SELECT 
                DATE(t.transaction_date) as date,
                COALESCE(SUM(ti.quantity), 0) as total_quantity,
                ti.product_id
            FROM transactions t
            JOIN transaction_items ti ON t.transaction_id = ti.transaction_id
            WHERE t.transaction_date >= :cutoff_date
            GROUP BY DATE(t.transaction_date), ti.product_id
        """
        
        if product_id:
            query += " HAVING ti.product_id = :product_id"
        
        # Execute query
        result = db.execute(text(query), {
            'cutoff_date': cutoff_date,
            'product_id': product_id
        })
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall(), columns=['ds', 'y', 'product_id'])
        
        # Fill in missing dates with zeros
        if not df.empty:
            date_range = pd.date_range(start=cutoff_date, end=datetime.now(), freq='D')
            if product_id:
                template = pd.DataFrame({'ds': date_range})
                template['product_id'] = product_id
                df = template.merge(df, on=['ds', 'product_id'], how='left')
            else:
                product_ids = df['product_id'].unique()
                template = pd.DataFrame([(d, p) for d in date_range for p in product_ids],
                                     columns=['ds', 'product_id'])
                df = template.merge(df, on=['ds', 'product_id'], how='left')
            
            df['y'] = df['y'].fillna(0)
        
        return df
    except Exception as e:
        raise Exception(f"Error preparing time series data: {str(e)}")

def forecast_demand(daily_sales, forecast_periods=30, product_id=None):
    """
    Forecast demand using Prophet
    """
    try:
        # Prepare data for Prophet
        if product_id:
            prophet_data = daily_sales[daily_sales['product_id'] == product_id].copy()
        else:
            prophet_data = daily_sales.copy()
        
        # Ensure we have enough data
        if len(prophet_data) < 2:
            raise ValueError("Insufficient data for forecasting. Need at least 2 data points.")
        
        # Check if we have any non-zero values
        if prophet_data['y'].sum() == 0:
            raise ValueError("No sales data available for forecasting.")
        
        # Initialize and fit Prophet model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )
        
        model.fit(prophet_data)
        
        # Create future dates for forecasting
        future_dates = model.make_future_dataframe(periods=forecast_periods)
        
        # Make predictions
        forecast = model.predict(future_dates)
        
        return model, forecast
    except Exception as e:
        raise Exception(f"Error in demand forecasting: {str(e)}")

def analyze_forecast_accuracy(model, forecast, actual_data):
    """
    Analyze forecast accuracy
    """
    # Merge forecast with actual data
    comparison = pd.merge(
        forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
        actual_data,
        on='ds',
        how='left'
    )
    
    # Calculate error metrics
    comparison['error'] = comparison['y'] - comparison['yhat']
    comparison['absolute_error'] = abs(comparison['error'])
    comparison['percentage_error'] = (comparison['error'] / comparison['y']) * 100
    
    # Calculate metrics
    mae = comparison['absolute_error'].mean()
    mape = comparison['percentage_error'].abs().mean()
    rmse = np.sqrt((comparison['error'] ** 2).mean())
    
    return {
        'mae': mae,
        'mape': mape,
        'rmse': rmse,
        'comparison': comparison
    }

def get_seasonal_patterns(model):
    """Extract seasonal patterns from the Prophet model"""
    try:
        # Get yearly seasonality
        yearly = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', end='2023-12-31', freq='D'),
            'seasonal': 'yearly'
        })
        yearly_pattern = model.predict(yearly)[['ds', 'yearly']]
        yearly_pattern['month'] = yearly_pattern['ds'].dt.month
        yearly_avg = yearly_pattern.groupby('month')['yearly'].mean().reset_index()
        
        # Get weekly seasonality
        weekly = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', end='2023-01-07', freq='D'),
            'seasonal': 'weekly'
        })
        weekly_pattern = model.predict(weekly)[['ds', 'weekly']]
        weekly_pattern['day'] = weekly_pattern['ds'].dt.day_name()
        weekly_avg = weekly_pattern[['day', 'weekly']]
        
        # Get monthly seasonality if it exists
        if 'monthly' in model.seasonalities:
            monthly = pd.DataFrame({
                'ds': pd.date_range(start='2023-01-01', end='2023-01-31', freq='D'),
                'seasonal': 'monthly'
            })
            monthly_pattern = model.predict(monthly)[['ds', 'monthly']]
            monthly_pattern['day_of_month'] = monthly_pattern['ds'].dt.day
            monthly_avg = monthly_pattern[['day_of_month', 'monthly']]
        else:
            monthly_avg = pd.DataFrame()
        
        return {
            'yearly': yearly_avg.to_dict('records'),
            'weekly': weekly_avg.to_dict('records'),
            'monthly': monthly_avg.to_dict('records') if not monthly_avg.empty else None
        }
        
    except Exception as e:
        print(f"Error extracting seasonal patterns: {str(e)}")
        return {
            'yearly': None,
            'weekly': None,
            'monthly': None
        }

def get_demand_forecast(db, product_id, forecast_periods=30):
    """Get demand forecast for a specific product"""
    try:
        # Get historical sales data with daily aggregation using a more robust query
        query = text("""
            WITH date_range AS (
                SELECT generate_series(
                    COALESCE((SELECT MIN(transaction_date)::date FROM transactions), CURRENT_DATE - INTERVAL '365 days'),
                    CURRENT_DATE,
                    '1 day'::interval
                )::date AS date
            ),
            daily_sales AS (
                SELECT 
                    dr.date,
                    COALESCE(SUM(ti.quantity), 0) as quantity
                FROM date_range dr
                LEFT JOIN transactions t ON dr.date = DATE(t.transaction_date)
                LEFT JOIN transaction_items ti ON t.transaction_id = ti.transaction_id 
                    AND ti.product_id = :product_id
                GROUP BY dr.date
                ORDER BY dr.date
            )
            SELECT 
                date,
                quantity
            FROM daily_sales
            ORDER BY date
        """)
        
        df = pd.read_sql(query, db.bind, params={'product_id': product_id})
        
        if df.empty:
            return {
                'forecast': pd.DataFrame(),
                'accuracy': {'mae': None, 'mape': None, 'rmse': None, 'r2': None},
                'error': 'No historical data available for this product'
            }
        
        # Ensure date column is properly formatted
        df['ds'] = pd.to_datetime(df['date']).dt.tz_localize(None)  # Remove timezone
        df['y'] = df['quantity']
        
        # Drop the original columns and any rows with NaN
        df = df[['ds', 'y']].dropna()
        
        if len(df) < 7:  # Require at least a week of data
            return {
                'forecast': pd.DataFrame(),
                'accuracy': {'mae': None, 'mape': None, 'rmse': None, 'r2': None},
                'error': 'Insufficient data for forecasting. Need at least 7 days of data.'
            }
        
        # Handle zero values for MAPE calculation
        min_non_zero = df['y'][df['y'] > 0].min() if any(df['y'] > 0) else 1
        df['y'] = df['y'].replace(0, min_non_zero * 0.1)
        
        # Handle outliers using IQR method
        Q1 = df['y'].quantile(0.25)
        Q3 = df['y'].quantile(0.75)
        IQR = Q3 - Q1
        df['y'] = df['y'].clip(lower=Q1 - 1.5*IQR, upper=Q3 + 1.5*IQR)
        
        # Split data into train and test sets
        train_size = int(len(df) * 0.8)
        if train_size < 14:  # Ensure we have at least 14 days of training data
            train_size = len(df) - 7 if len(df) > 7 else len(df)  # Leave 7 days for testing if possible
        
        train = df[:train_size]
        test = df[train_size:] if train_size < len(df) else pd.DataFrame()
        
        # Initialize and fit Prophet model with custom parameters
        model = Prophet(
            yearly_seasonality=len(train) >= 365,  # Only use yearly seasonality if we have enough data
            weekly_seasonality=len(train) >= 14,   # Only use weekly seasonality if we have enough data
            daily_seasonality=False,  # Disable daily seasonality to prevent overfitting
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            holidays_prior_scale=10.0,
            interval_width=0.95
        )
        
        # Add country-specific holidays if we have enough data
        if len(train) >= 90:  # Only add holidays if we have at least 3 months of data
            model.add_country_holidays(country_name='US')
        
        # Add custom monthly seasonality if we have enough data
        if len(train) >= 60:  # Only add monthly seasonality if we have at least 2 months of data
            model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
            )
        
        # Fit the model
        model.fit(train)
        
        # Make future dataframe
        future = model.make_future_dataframe(
            periods=forecast_periods,
            freq='D',
            include_history=True
        )
        
        # Make predictions
        forecast = model.predict(future)
        
        # Calculate accuracy metrics on test set
        if not test.empty and len(test) >= 3:  # Only calculate metrics if we have enough test data
            test_forecast = model.predict(test[['ds']])
            
            # Calculate metrics
            mae = mean_absolute_error(test['y'], test_forecast['yhat'])
            
            # Calculate MAPE avoiding division by zero
            mape = np.mean(np.abs((test['y'] - test_forecast['yhat']) / test['y'])) * 100
            
            rmse = np.sqrt(mean_squared_error(test['y'], test_forecast['yhat']))
            
            # Calculate R² score
            r2 = r2_score(test['y'], test_forecast['yhat'])
        else:
            mae = mape = rmse = r2 = None
        
        # Get seasonal patterns
        seasonal_patterns = get_seasonal_patterns(model)
        
        # Select relevant columns for the forecast
        forecast_output = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']]
        
        return {
            'forecast': forecast_output,
            'accuracy': {
                'mae': mae,
                'mape': mape,
                'rmse': rmse,
                'r2': r2
            },
            'seasonality': seasonal_patterns
        }
        
    except Exception as e:
        print(f"Error generating forecast: {str(e)}")
        return {
            'forecast': pd.DataFrame(),
            'accuracy': {'mae': None, 'mape': None, 'rmse': None, 'r2': None},
            'error': str(e)
        }

def generate_forecast_recommendations(forecast_results):
    """
    Generate recommendations based on forecast results
    """
    recommendations = []
    
    # Analyze trend
    last_date = forecast_results['forecast']['ds'].max()
    last_forecast = forecast_results['forecast'].loc[
        forecast_results['forecast']['ds'] == last_date
    ]
    
    # Check for significant changes
    if last_forecast['trend'].values[0] > 1.1:  # 10% increase
        recommendations.append("Consider increasing inventory levels")
    elif last_forecast['trend'].values[0] < 0.9:  # 10% decrease
        recommendations.append("Consider reducing inventory levels")
    
    # Check for seasonality
    weekly_seasonality = forecast_results['seasonality']['weekly']
    if weekly_seasonality['weekly'].std() > 0.5:  # Significant weekly variation
        recommendations.append("Implement dynamic pricing based on weekly patterns")
    
    # Check forecast accuracy
    if forecast_results['accuracy']['mape'] > 20:  # High error rate
        recommendations.append("Review and adjust forecasting model parameters")
    
    return recommendations 