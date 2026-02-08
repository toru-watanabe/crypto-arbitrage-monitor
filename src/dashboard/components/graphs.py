"""Graph components for the dashboard."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List
from src.models import PriceData, ArbitrageOpportunity


def create_price_comparison_chart(prices_df: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Create a bar chart comparing prices across exchanges for a symbol.
    
    Args:
        prices_df: DataFrame with columns [exchange, symbol, price]
        symbol: Symbol to display
    
    Returns:
        Plotly Figure object
    """
    symbol_data = prices_df[prices_df['symbol'] == symbol]
    
    if symbol_data.empty:
        return go.Figure().add_annotation(
            text=f"No data for {symbol}",
            showarrow=False,
            font=dict(size=20)
        )
    
    fig = go.Figure(data=[
        go.Bar(
            x=symbol_data['exchange'],
            y=symbol_data['price'],
            text=symbol_data['price'].apply(lambda x: f'${x:,.2f}'),
            textposition='outside',
            marker=dict(
                color=symbol_data['price'],
                colorscale='Viridis',
                showscale=False
            )
        )
    ])
    
    fig.update_layout(
        title=f'{symbol} Price Comparison',
        xaxis_title='Exchange',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        height=400,
    )
    
    return fig


def create_spread_heatmap(opportunities: List[ArbitrageOpportunity]) -> go.Figure:
    """
    Create a heatmap showing price spreads between exchanges.
    
    Args:
        opportunities: List of ArbitrageOpportunity objects
    
    Returns:
        Plotly Figure object
    """
    if not opportunities:
        return go.Figure().add_annotation(
            text="No arbitrage opportunities",
            showarrow=False,
            font=dict(size=20)
        )
    
    # Create matrix of spreads
    df = pd.DataFrame([
        {
            'Symbol': opp.symbol,
            'Route': f"{opp.buy_exchange} → {opp.sell_exchange}",
            'Profit %': opp.estimated_profit_pct
        }
        for opp in opportunities
    ])
    
    # Pivot for heatmap
    pivot = df.pivot_table(
        values='Profit %',
        index='Symbol',
        columns='Route',
        aggfunc='max',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        text=pivot.values,
        texttemplate='%{text:.2f}%',
        textfont={"size": 10},
        colorbar=dict(title="Profit %")
    ))
    
    fig.update_layout(
        title='Arbitrage Profit Heatmap',
        template='plotly_dark',
        height=500,
        xaxis_title='Trading Route',
        yaxis_title='Symbol'
    )
    
    return fig


def create_profit_scatter(opportunities: List[ArbitrageOpportunity]) -> go.Figure:
    """
    Create scatter plot of arbitrage opportunities.
    
    Args:
        opportunities: List of ArbitrageOpportunity objects
    
    Returns:
        Plotly Figure object
    """
    if not opportunities:
        return go.Figure().add_annotation(
            text="No opportunities to display",
            showarrow=False,
            font=dict(size=20)
        )
    
    df = pd.DataFrame([
        {
            'Symbol': opp.symbol,
            'Price Diff %': opp.price_diff_pct,
            'Est. Profit %': opp.estimated_profit_pct,
            'Route': f"{opp.buy_exchange} → {opp.sell_exchange}",
            'Buy Price': opp.buy_price,
            'Sell Price': opp.sell_price
        }
        for opp in opportunities
    ])
    
    fig = px.scatter(
        df,
        x='Price Diff %',
        y='Est. Profit %',
        size='Buy Price',
        color='Symbol',
        hover_data=['Route', 'Buy Price', 'Sell Price'],
        title='Arbitrage Opportunities Scatter Plot'
    )
    
    # Add threshold line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text="Break-even"
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=500,
    )
    
    return fig


def create_price_history_chart(history_df: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Create time series chart of price history.
    
    Args:
        history_df: DataFrame with columns [exchange, symbol, price, timestamp]
        symbol: Symbol to display
    
    Returns:
        Plotly Figure object
    """
    symbol_data = history_df[history_df['symbol'] == symbol]
    
    if symbol_data.empty:
        return go.Figure().add_annotation(
            text=f"No historical data for {symbol}",
            showarrow=False,
            font=dict(size=20)
        )
    
    fig = go.Figure()
    
    for exchange in symbol_data['exchange'].unique():
        exchange_data = symbol_data[symbol_data['exchange'] == exchange]
        fig.add_trace(go.Scatter(
            x=exchange_data['timestamp'],
            y=exchange_data['price'],
            mode='lines+markers',
            name=exchange.upper(),
            line=dict(width=2),
        ))
    
    fig.update_layout(
        title=f'{symbol} Price History',
        xaxis_title='Time',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_opportunity_timeline(opportunities: List[ArbitrageOpportunity]) -> go.Figure:
    """
    Create timeline of arbitrage opportunities.
    
    Args:
        opportunities: List of ArbitrageOpportunity objects
    
    Returns:
        Plotly Figure object
    """
    if not opportunities:
        return go.Figure().add_annotation(
            text="No opportunities",
            showarrow=False,
            font=dict(size=20)
        )
    
    df = pd.DataFrame([
        {
            'Timestamp': opp.timestamp,
            'Symbol': opp.symbol,
            'Profit %': opp.estimated_profit_pct,
            'Route': f"{opp.buy_exchange} → {opp.sell_exchange}"
        }
        for opp in opportunities
    ])
    
    fig = px.scatter(
        df,
        x='Timestamp',
        y='Profit %',
        color='Symbol',
        size='Profit %',
        hover_data=['Route'],
        title='Arbitrage Opportunities Over Time'
    )
    
    fig.update_layout(
        template='plotly_dark',
        height=400,
    )
    
    return fig
