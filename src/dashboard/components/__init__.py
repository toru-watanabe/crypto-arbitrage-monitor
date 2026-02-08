"""Dashboard components package initialization."""

from src.dashboard.components.graphs import (
    create_price_comparison_chart,
    create_spread_heatmap,
    create_profit_scatter,
    create_price_history_chart,
    create_opportunity_timeline,
)

__all__ = [
    "create_price_comparison_chart",
    "create_spread_heatmap",
    "create_profit_scatter",
    "create_price_history_chart",
    "create_opportunity_timeline",
]
