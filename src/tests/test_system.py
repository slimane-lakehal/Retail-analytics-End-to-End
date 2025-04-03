import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from src.database.db_connection import get_db, init_db
from src.database.sample_data import generate_sample_data
from src.database.data_pipeline import DataPipeline
from src.analysis.customer_segmentation import get_customer_segmentation_insights
from src.analysis.demand_forecasting import get_demand_forecast
from src.analysis.inventory_optimization import get_inventory_optimization_insights
from src.analysis.product_recommendations import get_comprehensive_recommendations
from src.database.init_db import Base
from sqlalchemy import create_engine

def test_database_initialization():
    """Test database initialization and sample data generation"""
    print("\nTesting database initialization...")
    db = next(get_db())
    try:
        print("Initializing database...")
        # Drop all tables and recreate schema
        Base.metadata.drop_all(db.get_bind())
        Base.metadata.create_all(db.get_bind())
        print("Database tables created successfully")

        print("Generating sample data...")
        # Generate sample data
        result = generate_sample_data(db)
        db.commit()

        # Verify data was generated
        assert result['stores'] > 0, "No stores were generated"
        assert result['staff'] > 0, "No staff members were generated"
        assert result['products'] > 0, "No products were generated"
        assert result['customers'] > 0, "No customers were generated"
        assert result['transactions'] > 0, "No transactions were generated"

        print("Sample data verified successfully")
        return result
    except Exception as e:
        print(f"Error in database initialization test: {str(e)}")
        if db:
            db.rollback()
        raise e
    finally:
        print("Closing database connection...")
        if db:
            db.close()

def test_data_pipeline():
    """Test the ETL pipeline"""
    print("\nTesting data pipeline...")
    db = next(get_db())
    try:
        print("Creating DataPipeline instance...")
        pipeline = DataPipeline(db)
        
        print("Running pipeline...")
        result = pipeline.run_pipeline()
        
        print("Verifying pipeline results...")
        # Verify pipeline results
        assert 'transaction_data' in result, "Missing transaction_data in result"
        assert 'inventory_data' in result, "Missing inventory_data in result"
        assert 'product_data' in result, "Missing product_data in result"
        assert 'customer_data' in result, "Missing customer_data in result"
        
        # Check data types and content
        assert isinstance(result['transaction_data'], pd.DataFrame), "transaction_data is not a DataFrame"
        assert isinstance(result['inventory_data'], pd.DataFrame), "inventory_data is not a DataFrame"
        assert isinstance(result['product_data'], pd.DataFrame), "product_data is not a DataFrame"
        assert isinstance(result['customer_data'], pd.DataFrame), "customer_data is not a DataFrame"
        
        # Verify data content
        assert not result['transaction_data'].empty, "transaction_data is empty"
        assert not result['inventory_data'].empty, "inventory_data is empty"
        assert not result['product_data'].empty, "product_data is empty"
        assert not result['customer_data'].empty, "customer_data is empty"
        
        print("Data pipeline test completed successfully")
        
    except Exception as e:
        print(f"Error in data pipeline test: {str(e)}")
        raise
    finally:
        print("Closing database connection...")
        db.close()

def test_customer_segmentation():
    """Test customer segmentation analysis"""
    db = next(get_db())
    try:
        result = get_customer_segmentation_insights(db)

        # Verify result structure
        assert 'rfm_data' in result, "RFM data not found in result"
        assert 'segment_analysis' in result, "Segment analysis not found in result"
        assert 'cluster_stats' in result, "Cluster statistics not found in result"

        # Verify data content
        assert not result['rfm_data'].empty, "RFM data is empty"
        assert not result['segment_analysis'].empty, "Segment analysis is empty"
        assert not result['cluster_stats'].empty, "Cluster statistics is empty"

        print("Customer segmentation test passed successfully")
    except Exception as e:
        print(f"Error in customer segmentation test: {str(e)}")
        raise e
    finally:
        db.close()

def test_demand_forecasting():
    """Test demand forecasting"""
    db = next(get_db())
    try:
        # Test with a specific product
        result = get_demand_forecast(db, product_id=1)
        
        # Verify result structure
        assert 'forecast' in result
        assert 'accuracy' in result
        
        # Check forecast data
        assert not result['forecast'].empty
        assert all(col in result['forecast'].columns for col in ['ds', 'yhat', 'yhat_lower', 'yhat_upper'])
        
        # Check accuracy metrics
        assert all(metric in result['accuracy'] for metric in ['mae', 'mape', 'rmse'])
        
    finally:
        db.close()

def test_inventory_optimization():
    """Test inventory optimization"""
    db = next(get_db())
    try:
        result = get_inventory_optimization_insights(db)
        
        # Verify result structure
        assert 'inventory_metrics' in result
        assert 'abc_analysis' in result
        assert 'optimization_results' in result
        assert 'recommendations' in result
        
        # Check data content
        assert not result['inventory_metrics'].empty
        assert not result['abc_analysis'].empty
        
    finally:
        db.close()

def test_product_recommendations():
    """Test product recommendations"""
    db = next(get_db())
    try:
        result = get_comprehensive_recommendations(db, product_id=1)

        # Verify result structure
        assert 'association_rules' in result, "Association rules not found in result"
        assert 'category_analysis' in result, "Category analysis not found in result"
        assert 'similarity_matrix' in result, "Similarity matrix not found in result"

        # Verify data content
        assert not result['association_rules'].empty, "Association rules data is empty"
        assert not result['category_analysis'].empty, "Category analysis data is empty"
        assert not result['similarity_matrix'].empty, "Similarity matrix data is empty"

        print("Product recommendations test passed successfully")
    except Exception as e:
        print(f"Error in product recommendations test: {str(e)}")
        raise e
    finally:
        db.close()

def setup_database():
    """Set up the database for testing"""
    print("Initializing database...")
    try:
        from src.database.init_db import init_database
        success = init_database()
        if success:
            print("Database initialized successfully")
        else:
            print("Failed to initialize database")
            raise Exception("Database initialization failed")
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise

def main():
    """Run all tests"""
    print("\nSetting up database...")
    setup_database()
    
    print("\nRunning tests...")
    test_database_initialization()
    test_data_pipeline()
    test_customer_segmentation()
    test_demand_forecasting()
    test_inventory_optimization()
    test_product_recommendations()
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"]) 