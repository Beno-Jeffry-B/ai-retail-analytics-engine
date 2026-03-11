"""
product_analytics.py
--------------------
Generates product and category-level metrics and visualisations.

Functions
---------
- sales_by_category(df)          → Bar chart: Total sales per category
- profit_by_category(df)         → Bar chart: Total profit per category
- top_profitable_products(df)    → Horizontal bar: Top 10 most profitable products
- get_product_kpis(df)           → Dict of scalar KPI values
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ── Colour palette ──────────────────────────────────────────────────────────
PALETTE = px.colors.qualitative.Vivid


def sales_by_category(df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart showing total Sales broken down by Category and Sub-Category.
    Falls back to Category-only if Sub-Category column is absent.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if "Sub-Category" in df.columns:
        cat = (
            df.groupby(["Category", "Sub-Category"])["Sales"]
            .sum()
            .reset_index()
        )
        fig = px.bar(
            cat,
            x="Sub-Category",
            y="Sales",
            color="Category",
            title="🛒 Sales by Category & Sub-Category",
            labels={"Sales": "Total Sales ($)"},
            color_discrete_sequence=PALETTE,
            barmode="group",
            text_auto=".2s",
        )
    else:
        cat = df.groupby("Category")["Sales"].sum().reset_index()
        fig = px.bar(
            cat,
            x="Category",
            y="Sales",
            title="🛒 Sales by Category",
            labels={"Sales": "Total Sales ($)"},
            color="Category",
            color_discrete_sequence=PALETTE,
            text_auto=".2s",
        )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=60, b=10),
        xaxis_tickangle=-30,
    )
    return fig


def profit_by_category(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing total Profit by Category, colour-coded green/red by sign.
    """
    cat = (
        df.groupby("Category")["Profit"]
        .sum()
        .reset_index()
        .sort_values("Profit", ascending=False)
    )
    cat["Color"] = cat["Profit"].apply(lambda x: "#2DC653" if x >= 0 else "#E5383B")

    fig = go.Figure(
        go.Bar(
            x=cat["Category"],
            y=cat["Profit"],
            marker_color=cat["Color"],
            text=cat["Profit"].apply(lambda x: f"${x:,.0f}"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="💰 Profit by Category",
        xaxis_title="Category",
        yaxis_title="Total Profit ($)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def top_profitable_products(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """
    Horizontal bar chart of the top-N most profitable products.

    Parameters
    ----------
    df : pd.DataFrame
    n  : int  Number of products to show (default 10)
    """
    top = (
        df.groupby("Product Name")["Profit"]
        .sum()
        .nlargest(n)
        .reset_index()
        .sort_values("Profit", ascending=True)
    )

    fig = px.bar(
        top,
        x="Profit",
        y="Product Name",
        orientation="h",
        title=f"🥇 Top {n} Most Profitable Products",
        labels={"Profit": "Total Profit ($)", "Product Name": ""},
        color="Profit",
        color_continuous_scale="Greens",
        text_auto=".2s",
    )
    fig.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def get_product_kpis(df: pd.DataFrame) -> dict:
    """
    Return scalar product KPIs for the dashboard metrics row.

    Keys: total_products, best_category_sales, best_category_profit,
          total_profit, profit_margin_pct
    """
    best_cat_sales = df.groupby("Category")["Sales"].sum().idxmax()
    best_cat_profit = df.groupby("Category")["Profit"].sum().idxmax()
    total_profit = df["Profit"].sum()
    total_sales = df["Sales"].sum()

    return {
        "total_products": df["Product Name"].nunique(),
        "best_category_sales": best_cat_sales,
        "best_category_profit": best_cat_profit,
        "total_profit": total_profit,
        "profit_margin_pct": (total_profit / total_sales * 100) if total_sales else 0,
    }
