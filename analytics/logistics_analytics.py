"""
logistics_analytics.py
-----------------------
Generates shipping and logistics metrics and visualisations.

Functions
---------
- avg_shipping_time_by_country(df)  → Choropleth map: Avg shipping days per country
- shipping_mode_distribution(df)    → Donut chart: Orders by shipping mode
- delivery_time_trend(df)           → Line chart: Monthly average shipping time
- get_logistics_kpis(df)            → Dict of scalar KPI values
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ── Colour palette ──────────────────────────────────────────────────────────
PALETTE = px.colors.qualitative.Safe


def avg_shipping_time_by_country(df: pd.DataFrame) -> go.Figure:
    """
    Choropleth world map showing the average number of shipping days per country.

    Parameters
    ----------
    df : pd.DataFrame  Must contain 'Country' and 'Shipping Days' columns.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    country_col = "Country/Region" if "Country/Region" in df.columns else "Country"

    if country_col not in df.columns or "Shipping Days" not in df.columns:
        # Fallback: return an empty figure with a message
        fig = go.Figure()
        fig.update_layout(title="⚠️ Country or Shipping Days data not available")
        return fig

    ship = (
        df.groupby(country_col)["Shipping Days"]
        .mean()
        .reset_index()
        .rename(columns={country_col: "Country", "Shipping Days": "Avg Shipping Days"})
    )
    ship["Avg Shipping Days"] = ship["Avg Shipping Days"].round(1)

    fig = px.choropleth(
        ship,
        locations="Country",
        locationmode="country names",
        color="Avg Shipping Days",
        title="🌍 Average Shipping Time by Country (Days)",
        color_continuous_scale="YlOrRd",
        labels={"Avg Shipping Days": "Avg Days"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(showframe=False, showcoastlines=True),
        font=dict(size=12),
        margin=dict(l=0, r=0, t=60, b=0),
        coloraxis_colorbar=dict(title="Days"),
    )
    return fig


def shipping_mode_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing the split of orders across different shipping modes.
    """
    mode_col = "Ship Mode"
    if mode_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="⚠️ Ship Mode data not available")
        return fig

    mode = df[mode_col].value_counts().reset_index()
    mode.columns = ["Ship Mode", "Order Count"]

    fig = px.pie(
        mode,
        names="Ship Mode",
        values="Order Count",
        title="🚚 Shipping Mode Usage Distribution",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def delivery_time_trend(df: pd.DataFrame) -> go.Figure:
    """
    Line chart of monthly average shipping days over time,
    helping to spot improving or worsening delivery performance.
    """
    if "Shipping Days" not in df.columns or "Order Date" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="⚠️ Shipping Days or Order Date data not available")
        return fig

    trend = (
        df.assign(Month=df["Order Date"].dt.to_period("M").astype(str))
        .groupby("Month")["Shipping Days"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="Month",
        y="Shipping Days",
        title="📈 Delivery Time Trend (Monthly Avg)",
        labels={"Month": "Month", "Shipping Days": "Avg Shipping Days"},
        markers=True,
        line_shape="spline",
        color_discrete_sequence=["#4361EE"],
    )
    fig.add_hline(
        y=trend["Shipping Days"].mean(),
        line_dash="dash",
        line_color="orange",
        annotation_text="Overall Avg",
        annotation_position="bottom right",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        margin=dict(l=10, r=10, t=60, b=10),
        xaxis_tickangle=-45,
    )
    return fig


def get_logistics_kpis(df: pd.DataFrame) -> dict:
    """
    Return scalar logistics KPIs for the dashboard metrics row.

    Keys: avg_shipping_days, max_shipping_days, most_used_mode,
          countries_served, pct_late (orders > 5 days)
    """
    country_col = "Country/Region" if "Country/Region" in df.columns else "Country"
    avg_days = df["Shipping Days"].mean() if "Shipping Days" in df.columns else 0
    max_days = df["Shipping Days"].max() if "Shipping Days" in df.columns else 0
    mode_col = "Ship Mode"
    most_used = df[mode_col].mode()[0] if mode_col in df.columns else "N/A"
    countries = df[country_col].nunique() if country_col in df.columns else 0
    if "Shipping Days" in df.columns:
        pct_late = (df["Shipping Days"] > 5).mean() * 100
    else:
        pct_late = 0

    return {
        "avg_shipping_days": round(avg_days, 1),
        "max_shipping_days": int(max_days),
        "most_used_mode": most_used,
        "countries_served": countries,
        "pct_late": round(pct_late, 1),
    }
