import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sales_trend_chart(data, time_column='transaction_date', value_column='total_amount'):
    """
    Create a sales trend chart with interactive features
    """
    fig = px.line(
        data,
        x=time_column,
        y=value_column,
        title='Sales Trend Over Time',
        labels={
            time_column: 'Date',
            value_column: 'Sales Amount'
        }
    )
    
    # Add range slider
    fig.update_xaxes(rangeslider_visible=True)
    
    # Add hover template
    fig.update_traces(
        hovertemplate="<br>".join([
            "Date: %{x}",
            "Sales: $%{y:,.2f}",
            "<extra></extra>"
        ])
    )
    
    return fig

def create_customer_segmentation_chart(segment_data):
    """Create a pie chart showing customer segment distribution"""
    # Reset index to make segment names a column
    plot_data = segment_data.reset_index()
    
    fig = px.pie(
        plot_data,
        values='count',
        names=plot_data.index,  # Use the index column which contains segment names
        title='Customer Segment Distribution',
        hole=0.4
    )
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_inventory_status_chart(inventory_data):
    """Create an inventory status chart"""
    try:
        # Verify we have the required data
        if not isinstance(inventory_data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
            
        if inventory_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text='No inventory data available',
                xref='paper',
                yref='paper',
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        # Ensure required columns exist
        required_columns = ['category', 'quantity', 'total_value']
        missing_cols = [col for col in required_columns if col not in inventory_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Group by category and calculate metrics
        category_metrics = inventory_data.groupby('category').agg({
            'quantity': 'sum',
            'total_value': 'sum'
        }).reset_index()
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add bars for quantity
        fig.add_trace(
            go.Bar(
                name='Quantity',
                x=category_metrics['category'],
                y=category_metrics['quantity'],
                marker_color='rgb(55, 83, 109)',
                text=category_metrics['quantity'].round(0).astype(int),
                textposition='auto',
                hovertemplate='Category: %{x}<br>Quantity: %{y:,.0f}<extra></extra>'
            )
        )
        
        # Add bars for total value
        fig.add_trace(
            go.Bar(
                name='Total Value ($)',
                x=category_metrics['category'],
                y=category_metrics['total_value'],
                marker_color='rgb(26, 118, 255)',
                text=category_metrics['total_value'].apply(lambda x: f'${x:,.0f}'),
                textposition='auto',
                yaxis='y2',
                hovertemplate='Category: %{x}<br>Total Value: $%{y:,.2f}<extra></extra>'
            )
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Inventory Status by Category',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=16)
            },
            xaxis={
                'title': 'Product Category',
                'title_font': dict(size=14),
                'tickfont': dict(size=12),
                'tickangle': -45,
                'showgrid': True,
                'gridcolor': 'rgba(128, 128, 128, 0.2)',
                'showline': True,
                'linewidth': 1,
                'linecolor': 'gray'
            },
            yaxis={
                'title': 'Quantity',
                'title_font': dict(size=14),
                'tickfont': dict(size=12),
                'showgrid': True,
                'gridcolor': 'rgba(128, 128, 128, 0.2)',
                'zeroline': True,
                'zerolinecolor': 'rgba(128, 128, 128, 0.2)',
                'showline': True,
                'linewidth': 1,
                'linecolor': 'gray'
            },
            yaxis2={
                'title': 'Total Value ($)',
                'title_font': dict(size=14),
                'tickfont': dict(size=12),
                'overlaying': 'y',
                'side': 'right',
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'rgba(128, 128, 128, 0.2)',
                'showline': True,
                'linewidth': 1,
                'linecolor': 'gray'
            },
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': dict(size=12)
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=500,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating inventory chart: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f'Error creating chart: {str(e)}',
            xref='paper',
            yref='paper',
            x=0.5,
            y=0.5,
            showarrow=False
        )
        return fig

def create_product_performance_chart(data, metric='similarity'):
    """
    Create a product performance visualization
    """
    fig = px.bar(
        data,
        x=data.index,
        y=data.values,
        title=f'Product {metric.capitalize()}'
    )
    fig.update_layout(
        xaxis_title='Product ID',
        yaxis_title=metric.capitalize(),
        showlegend=False
    )
    
    return fig

def create_store_performance_map(store_data):
    """
    Create a geographic map of store performance
    """
    fig = px.scatter_geo(
        store_data,
        lat='latitude',
        lon='longitude',
        size='sales',
        color='performance',
        hover_name='store_name',
        title='Store Performance by Location',
        projection='natural earth'
    )
    
    # Update layout
    fig.update_layout(
        geo=dict(
            scope='usa',
            showland=True,
            landcolor='rgb(217, 217, 217)',
            subunitcolor='rgb(255, 255, 255)',
            countrycolor='rgb(255, 255, 255)',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showsubunits=True,
            showcountries=True,
            resolution=50
        )
    )
    
    return fig

def create_association_rules_network(rules_data):
    """
    Create a network visualization of product associations
    """
    # Prepare data for network
    nodes = set()
    edges = []
    
    for _, rule in rules_data.iterrows():
        antecedents = list(rule['antecedents'])
        consequents = list(rule['consequents'])
        
        for ant in antecedents:
            nodes.add(ant)
            for cons in consequents:
                nodes.add(cons)
                edges.append({
                    'from': ant,
                    'to': cons,
                    'value': rule['lift']
                })
    
    # Create network
    fig = go.Figure(data=[
        go.Scatter(
            x=[], y=[],
            mode='markers+text',
            text=list(nodes),
            textposition='middle center',
            marker=dict(
                size=20,
                color='lightblue'
            )
        )
    ])
    
    # Add edges
    for edge in edges:
        fig.add_trace(
            go.Scatter(
                x=[], y=[],
                mode='lines',
                line=dict(
                    width=edge['value'],
                    color='gray'
                ),
                hoverinfo='none'
            )
        )
    
    # Update layout
    fig.update_layout(
        title='Product Association Network',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40)
    )
    
    return fig

def create_forecast_chart(historical_data, forecast_data):
    """
    Create a forecast visualization with confidence intervals
    """
    fig = go.Figure()
    
    # Add historical data
    fig.add_trace(go.Scatter(
        x=historical_data['ds'],
        y=historical_data['y'],
        name='Historical',
        line=dict(color='blue')
    ))
    
    # Add forecast
    fig.add_trace(go.Scatter(
        x=forecast_data['ds'],
        y=forecast_data['yhat'],
        name='Forecast',
        line=dict(color='red')
    ))
    
    # Add confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast_data['ds'].tolist() + forecast_data['ds'].tolist()[::-1],
        y=forecast_data['yhat_upper'].tolist() + forecast_data['yhat_lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(255,0,0,0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))
    
    # Update layout
    fig.update_layout(
        title='Demand Forecast with Confidence Intervals',
        xaxis_title='Date',
        yaxis_title='Demand',
        showlegend=True
    )
    
    return fig

def create_kpi_dashboard(kpi_data):
    """
    Create a KPI dashboard with multiple metrics
    """
    fig = go.Figure()
    
    # Add KPI metrics
    metrics = ['Sales', 'Customers', 'Inventory', 'Profit']
    values = [kpi_data.get(metric.lower(), 0) for metric in metrics]
    changes = [kpi_data.get(f'{metric.lower()}_change', 0) for metric in metrics]
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}]]
    )
    
    # Add indicators
    for i, (metric, value, change) in enumerate(zip(metrics, values, changes)):
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=value,
                delta={'reference': value * (1 - change/100)},
                title={'text': metric},
                number={'prefix': "$" if metric == 'Sales' else ""}
            ),
            row=row, col=col
        )
    
    # Update layout
    fig.update_layout(
        title='Key Performance Indicators',
        showlegend=False,
        grid={'rows': 2, 'columns': 2, 'pattern': "independent"}
    )
    
    return fig 