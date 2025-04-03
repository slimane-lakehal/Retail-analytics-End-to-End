# Retail Analytics End-to-End Solution

A comprehensive retail analytics solution that provides insights into customer behavior, inventory management, demand forecasting, and product recommendations.

## Features

- **Customer Segmentation**: RFM analysis and customer clustering
- **Demand Forecasting**: Time series forecasting using Prophet
- **Inventory Optimization**: ABC analysis and inventory level optimization
- **Product Recommendations**: Association rules and collaborative filtering
- **Interactive Dashboard**: Streamlit-based visualization interface
- **Realistic Sample Data**: Seasonally-aware transaction patterns with product bundling

## Project Structure

```
retail-analytics/
├── data/                      # Data storage directory
│   ├── raw/                   # Raw data files
│   ├── processed/             # Processed data files
│   └── models/                # Trained models
├── src/
│   ├── database/             # Database related code
│   │   ├── db_connection.py  # Database connection handling
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schema.sql        # Database schema
│   │   ├── data_pipeline.py  # ETL processes
│   │   └── sample_data.py    # Sample data generation with realistic patterns
│   ├── analysis/             # Analysis modules
│   │   ├── customer_segmentation.py
│   │   ├── demand_forecasting.py
│   │   ├── inventory_optimization.py
│   │   └── product_recommendations.py
│   ├── visualization/        # Visualization components
│   │   └── charts.py        # Plotly chart functions
│   ├── tests/               # Test files
│   │   └── test_system.py   # System tests
│   ├── app.py               # Streamlit dashboard
│   └── run_tests.py         # Test runner
├── docker-compose.yml       # Docker configuration
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## Prerequisites

- Python 3.8+
- Docker Desktop
- PostgreSQL 17 (via Docker)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd retail-analytics
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start PostgreSQL using Docker:
```bash
docker-compose up -d
```

6. Initialize the database:
```bash
python src/run_tests.py
```

## Running the Application

1. Start the Streamlit dashboard:
```bash
streamlit run src/app.py
```

2. Access the dashboard at http://localhost:8501

## Testing

Run the test suite:
```bash
python src/run_tests.py
```

## Features in Detail

### Sample Data Generation
- Realistic transaction patterns
- Seasonal variations by product category
- Product bundling and related items
- Dynamic pricing with seasonal discounts
- Category-specific quantity patterns
- Holiday season adjustments

### Customer Segmentation
- RFM (Recency, Frequency, Monetary) analysis
- K-means clustering for customer segments
- Segment characteristics analysis
- Customer lifetime value calculation

### Demand Forecasting
- Time series forecasting using Prophet
- Seasonal pattern analysis
- Forecast accuracy metrics
- Confidence intervals

### Inventory Optimization
- ABC analysis
- Economic Order Quantity (EOQ) calculation
- Safety stock optimization
- Reorder point determination

### Product Recommendations
- Association rules mining
- Collaborative filtering
- Category analysis
- Cross-selling opportunities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Streamlit
- Powered by PostgreSQL
- Data analysis with pandas and numpy
- Visualizations with Plotly
- Machine learning with scikit-learn and Prophet 