import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.db_connection import get_db, init_db, engine, Base
from src.database.sample_data import generate_sample_data
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
from sqlalchemy.orm import sessionmaker

def setup_database():
    """Initialize database and generate sample data"""
    print("Setting up database...")
    db = None
    try:
        # Drop all tables and recreate schema
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("Database tables created successfully")

        # Get database session
        db = next(get_db())
        
        print("Starting sample data generation...")
        result = generate_sample_data(db)
        db.commit()
        print("Sample data generated successfully")
        print(f"Generated sample data:")
        print(f"- {result['stores']} stores")
        print(f"- {result['staff']} staff members")
        print(f"- {result['products']} products")
        print(f"- {result['customers']} customers")
        print(f"- {result['transactions']} transactions")
        return result
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        if db:
            db.rollback()
        raise e
    finally:
        if db:
            db.close()

def run_analysis():
    """Run all analysis modules and generate visualizations"""
    print("\nRunning analysis...")
    
    # Run data pipeline
    print("Running data pipeline...")
    db = next(get_db())
    try:
        pipeline = DataPipeline(db)
        pipeline_result = pipeline.run_pipeline()
        
        # Customer Segmentation
        print("Running customer segmentation...")
        segmentation_result = get_customer_segmentation_insights(db)
        fig_segmentation = create_customer_segmentation_chart(segmentation_result['segment_analysis'])
        fig_segmentation.write_html("output/customer_segmentation.html")
        
        # Demand Forecasting
        print("Running demand forecasting...")
        forecast_result = get_demand_forecast(db, product_id=1)
        fig_forecast = create_sales_trend_chart(
            forecast_result['forecast'],
            time_column='ds',
            value_column='yhat'
        )
        fig_forecast.write_html("output/demand_forecast.html")
        
        # Inventory Optimization
        print("Running inventory optimization...")
        inventory_result = get_inventory_optimization_insights(db)
        fig_inventory = create_inventory_status_chart(inventory_result['inventory_metrics'])
        fig_inventory.write_html("output/inventory_status.html")
        
        # Product Recommendations
        print("Running product recommendations...")
        recommendations_result = get_comprehensive_recommendations(db, product_id=1)
        fig_products = create_product_performance_chart(
            recommendations_result['similarity_matrix'].head(10),
            metric='similarity'
        )
        fig_products.write_html("output/product_recommendations.html")
        
        print("\nAnalysis completed successfully!")
        print("Visualizations saved to the 'output' directory")
        
    finally:
        db.close()

def main():
    """Main function to run tests and analysis"""
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Setup database
    setup_database()
    
    # Run tests
    print("\nRunning tests...")
    test_result = pytest.main(["-v", "src/tests/test_system.py"])
    
    if test_result == 0:
        print("\nAll tests passed successfully!")
        # Run analysis if tests pass
        run_analysis()
    else:
        print("\nTests failed. Please fix the issues before running analysis.")

if __name__ == "__main__":
    main() 