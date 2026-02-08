"""Plotly Dash application for arbitrage monitoring dashboard."""

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta

from src.config import settings
from src.storage import RedisClient, TimescaleClient
from src.processors import ArbitrageCalculator
from src.models import ArbitrageOpportunity
from src.dashboard.components import (
    create_price_comparison_chart,
    create_spread_heatmap,
    create_profit_scatter,
    create_price_history_chart,
)


# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="Crypto Arbitrage Monitor"
)

# Initialize clients
redis_client = RedisClient()
timescale_client = TimescaleClient()
calculator = ArbitrageCalculator()

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Crypto Arbitrage Monitor", className="text-center mb-4 mt-4"),
            html.P(
                f"Real-time monitoring of {', '.join(settings.coin_list)} across Bybit, Binance, and KuCoin",
                className="text-center text-muted mb-4"
            ),
        ])
    ]),
    
    # Stats cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-opportunities", children="0", className="text-success"),
                    html.P("Opportunities Found", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="best-profit", children="0%", className="text-warning"),
                    html.P("Best Profit", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="active-pairs", children="0", className="text-info"),
                    html.P("Active Pairs", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="last-update", children="--:--:--", className="text-light"),
                    html.P("Last Update", className="text-muted mb-0")
                ])
            ])
        ], width=3),
    ], className="mb-4"),
    
    # Real-time Price Monitor
    dbc.Row([
        dbc.Col([
            html.H3("Real-Time Price Monitor (USDT Pairs)", className="mb-3"),
            dash_table.DataTable(
                id='price-monitor-table',
                columns=[
                    {"name": "Coin", "id": "coin"},
                    {"name": "Bybit", "id": "bybit"},
                    {"name": "Binance", "id": "binance"},
                    {"name": "KuCoin", "id": "kucoin"},
                    {"name": "Min Price", "id": "min_price"},
                    {"name": "Max Price", "id": "max_price"},
                    {"name": "Spread %", "id": "spread"},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'backgroundColor': '#1e1e1e',
                    'color': 'white',
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'padding': '10px'
                },
                style_header={
                    'backgroundColor': '#2d2d2d',
                    'fontWeight': 'bold',
                    'fontSize': '15px'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'coin'},
                        'fontWeight': 'bold',
                        'fontSize': '16px'
                    },
                    {
                        'if': {'filter_query': '{spread} > 0.5'},
                        'backgroundColor': '#1a472a',
                    },
                ],
                data=[]
            )
        ])
    ], className="mb-4"),
    
    # Opportunities table
    dbc.Row([
        dbc.Col([
            html.H3("Current Arbitrage Opportunities", className="mb-3"),
            dash_table.DataTable(
                id='opportunities-table',
                columns=[
                    {"name": "Symbol", "id": "symbol"},
                    {"name": "Buy From", "id": "buy_exchange"},
                    {"name": "Buy Price", "id": "buy_price"},
                    {"name": "Sell To", "id": "sell_exchange"},
                    {"name": "Sell Price", "id": "sell_price"},
                    {"name": "Price Diff %", "id": "price_diff_pct"},
                    {"name": "Est. Profit %", "id": "profit_pct"},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'backgroundColor': '#1e1e1e',
                    'color': 'white',
                    'textAlign': 'center'
                },
                style_header={
                    'backgroundColor': '#2d2d2d',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{profit_pct} > 1.0'},
                        'backgroundColor': '#1a472a',
                        'color': '#4ade80'
                    },
                    {
                        'if': {'filter_query': '{profit_pct} > 0 && {profit_pct} <= 1.0'},
                        'backgroundColor': '#3f3f1a',
                        'color': '#fbbf24'
                    },
                ],
                data=[]
            )
        ])
    ], className="mb-4"),
    
    # Visualizations
    dbc.Row([
        dbc.Col([
            html.H3("Price Comparison", className="mb-3"),
            dcc.Dropdown(
                id='coin-selector',
                options=[{'label': coin, 'value': f'{coin}USDT'} for coin in settings.coin_list],
                value='BTCUSDT',
                className="mb-3",
                style={'color': 'black'}
            ),
            dcc.Graph(id='price-comparison-chart')
        ], width=6),
        dbc.Col([
            html.H3("Arbitrage Heatmap", className="mb-3"),
            dcc.Graph(id='spread-heatmap')
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.H3("Profit Scatter", className="mb-3"),
            dcc.Graph(id='profit-scatter')
        ], width=6),
        dbc.Col([
            html.H3("Price History (24h)", className="mb-3"),
            dcc.Graph(id='price-history-chart')
        ], width=6),
    ], className="mb-4"),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # 10 seconds
        n_intervals=0
    ),
    
    # Footer
    html.Hr(),
    html.P(
        f"Monitoring interval: {settings.SCRAPE_INTERVAL}s | "
        f"Min profit threshold: {settings.MIN_PROFIT_THRESHOLD}%",
        className="text-center text-muted mb-4"
    ),
], fluid=True)


@app.callback(
    [
        Output('total-opportunities', 'children'),
        Output('best-profit', 'children'),
        Output('active-pairs', 'children'),
        Output('last-update', 'children'),
        Output('price-monitor-table', 'data'),
        Output('opportunities-table', 'data'),
        Output('price-comparison-chart', 'figure'),
        Output('spread-heatmap', 'figure'),
        Output('profit-scatter', 'figure'),
        Output('price-history-chart', 'figure'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('coin-selector', 'value'),
    ]
)
def update_dashboard(n, selected_coin):
    """Update all dashboard components."""
    
    # Get current prices from Redis
    all_prices = redis_client.get_all_latest_prices()
    
    # Calculate opportunities
    opportunities = calculator.calculate_opportunities(all_prices)
    profitable = calculator.filter_profitable(opportunities)
    
    # Update stats
    total_opps = len(profitable)
    best_profit = f"{max([o.estimated_profit_pct for o in profitable], default=0):.2f}%"
    active_pairs = len(all_prices)
    last_update = datetime.utcnow().strftime("%H:%M:%S UTC")
    
    # Prepare table data
    table_data = [
        {
            'symbol': opp.symbol,
            'buy_exchange': opp.buy_exchange.upper(),
            'buy_price': f"${opp.buy_price:,.2f}",
            'sell_exchange': opp.sell_exchange.upper(),
            'sell_price': f"${opp.sell_price:,.2f}",
            'price_diff_pct': f"{opp.price_diff_pct:.2f}%",
            'profit_pct': round(opp.estimated_profit_pct, 2),
        }
        for opp in profitable[:20]  # Top 20
    ]
    
    # Prepare price data
    prices_df = pd.DataFrame([
        {
            'exchange': p.exchange,
            'symbol': p.symbol,
            'price': p.price,
            'timestamp': p.timestamp
        }
        for p in all_prices
    ])
    
    # Prepare real-time price monitor data
    price_monitor_data = []
    for coin in settings.coin_list:
        symbol = f"{coin}USDT"
        coin_prices = [p for p in all_prices if p.symbol == symbol]
        
        row = {'coin': coin}
        prices = []
        
        for exchange in ['bybit', 'binance', 'kucoin']:
            price_obj = next((p for p in coin_prices if p.exchange == exchange), None)
            if price_obj:
                # Use 4 decimal places for prices under $1 (e.g., TRX, DOGE)
                fmt = ",.4f" if price_obj.price < 1.0 else ",.2f"
                row[exchange] = f"${price_obj.price:{fmt}}"
                prices.append(price_obj.price)
            else:
                row[exchange] = "-"
        
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            spread = ((max_price - min_price) / min_price) * 100
            
            # Format min/max with same logic
            min_fmt = ",.4f" if min_price < 1.0 else ",.2f"
            max_fmt = ",.4f" if max_price < 1.0 else ",.2f"
            
            row['min_price'] = f"${min_price:{min_fmt}}"
            row['max_price'] = f"${max_price:{max_fmt}}"
            row['spread'] = f"{spread:.2f}%"
        else:
            row['min_price'] = "-"
            row['max_price'] = "-"
            row['spread'] = "-"
            
        price_monitor_data.append(row)

    # Create charts
    price_chart = create_price_comparison_chart(prices_df, selected_coin)
    heatmap = create_spread_heatmap(profitable)
    scatter = create_profit_scatter(profitable)
    
    # Get historical data for selected coin
    try:
        history = timescale_client.get_price_history(
            symbol=selected_coin,
            start_time=datetime.utcnow() - timedelta(hours=24),
            limit=500
        )
        history_df = pd.DataFrame(history)
        history_chart = create_price_history_chart(history_df, selected_coin)
    except Exception as e:
        print(f"Error loading history: {e}")
        history_chart = create_price_history_chart(pd.DataFrame(), selected_coin)
    
    return (
        total_opps,
        best_profit,
        active_pairs,
        last_update,
        price_monitor_data,
        table_data,
        price_chart,
        heatmap,
        scatter,
        history_chart
    )


if __name__ == '__main__':
    print("🚀 Starting Crypto Arbitrage Monitor Dashboard...")
    print(f"📊 Dashboard URL: http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}")
    print(f"🔄 Auto-refresh: Every 10 seconds")
    print(f"💰 Monitoring: {', '.join(settings.coin_list)}")
    
    app.run_server(
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        debug=settings.DASHBOARD_DEBUG
    )
