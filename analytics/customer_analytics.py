"""
customer_analytics.py
---------------------
Generates customer-centric metrics and Plotly visualisations.

Functions
---------
- top_customers_by_revenue(df)  → Bar chart: Top 10 customers by total sales
- revenue_by_segment(df)        → Pie chart: Revenue split by customer segment
- orders_per_customer(df)       → Histogram: Distribution of orders per customer
- get_customer_kpis(df)         → Dict of scalar KPI values for the dashboard
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ── Colour palette ──────────────────────────────────────────────────────────
PALETTE = px.colors.qualitative.Bold


def top_customers_by_revenue(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing the top 10 customers ranked by total revenue (Sales).

    Parameters
    ----------
    df : pd.DataFrame
        The full superstore DataFrame from load_data().

    Returns
    -------
    plotly.graph_objects.Figure
    """
    top10 = (
        df.groupby("Customer Name")["Sales"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("Sales", ascending=True)           # ascending for horizontal bar
    )

    fig = px.bar(
        top10,
        x="Sales",
        y="Customer Name",
        orientation="h",
        title="🏆 Top 10 Customers by Revenue",
        labels={"Sales": "Total Revenue ($)", "Customer Name": ""},
        color="Sales",
        color_continuous_scale="Blues",
        text_auto=".2s",
    )
    fig.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def revenue_by_segment(df: pd.DataFrame) -> go.Figure:
    """
    Donut / Pie chart showing revenue contribution by customer segment
    (Consumer, Corporate, Home Office).
    """
    seg = (
        df.groupby("Segment")["Sales"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        seg,
        names="Segment",
        values="Sales",
        title="📊 Revenue by Customer Segment",
        color_discrete_sequence=PALETTE,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def orders_per_customer(df: pd.DataFrame) -> go.Figure:
    """
    Histogram showing how many unique orders each customer placed.
    """
    opc = (
        df.groupby("Customer Name")["Order ID"]
        .nunique()
        .reset_index()
        .rename(columns={"Order ID": "Order Count"})
    )

    fig = px.histogram(
        opc,
        x="Order Count",
        nbins=30,
        title="📦 Distribution of Orders per Customer",
        labels={"Order Count": "Number of Orders", "count": "Customers"},
        color_discrete_sequence=["#4361EE"],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=50, b=10),
        bargap=0.1,
    )
    return fig


def get_customer_kpis(df: pd.DataFrame) -> dict:
    """
    Return a dictionary of scalar KPIs for the Customer Analytics section.

    Keys: total_customers, total_revenue, avg_order_value, top_customer
    """
    return {
        "total_customers": df["Customer Name"].nunique(),
        "total_revenue": df["Sales"].sum(),
        "avg_order_value": df.groupby("Order ID")["Sales"].sum().mean(),
        "top_customer": df.groupby("Customer Name")["Sales"].sum().idxmax(),
    }
