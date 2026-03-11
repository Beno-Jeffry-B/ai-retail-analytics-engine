"""
app.py
------
AI Autonomous Retail Analytics Engine — Main Streamlit Dashboard

Run with:
    streamlit run app.py

Sections (sidebar navigation):
  📊 Customer Analytics
  🛒 Product Analytics
  🚚 Logistics Analytics
  🤖 AI Insights
"""

import streamlit as st
import pandas as pd

# ── Internal modules ─────────────────────────────────────────────────────────
from utils.data_loader import load_data, get_date_range
from analytics import customer_analytics as ca
from analytics import product_analytics  as pa
from analytics import logistics_analytics as la
from analytics import insight_engine      as ie


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Retail Analytics Engine",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS (dark, premium feel) ──────────────────────────────────────────
st.markdown(
    """
    <style>
        /* ── Global ── */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(160deg, #0f0c29, #302b63, #24243e);
        }
        [data-testid="stSidebar"] * { color: #e0e0e0 !important; }

        /* ── Metric cards ── */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 16px 20px;
            border: 1px solid #2d2d5a;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        [data-testid="stMetricLabel"]  { color: #9b9bbf !important; font-size: 0.82rem !important; }
        [data-testid="stMetricValue"]  { color: #ffffff !important; font-size: 1.6rem !important; font-weight: 700 !important; }
        [data-testid="stMetricDelta"]  { font-size: 0.85rem !important; }

        /* ── Section headers ── */
        .section-header {
            font-size: 1.6rem;
            font-weight: 700;
            color: #7f7fd5;
            margin-bottom: 0.5rem;
        }
        .section-sub {
            font-size: 0.9rem;
            color: #9b9bbf;
            margin-top: -0.4rem;
            margin-bottom: 1.2rem;
        }

        /* ── AI insight box ── */
        .insight-box {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 100%);
            border-left: 4px solid #7f7fd5;
            border-radius: 12px;
            padding: 24px 28px;
            color: #e0e0e0;
            line-height: 1.75;
            box-shadow: 0 8px 32px rgba(127,127,213,0.15);
        }

        /* ── Hint text ── */
        .hint { font-size: 0.8rem; color: #6b6b8a; margin-top: 0.3rem; }

        /* ── Anomaly badge ── */
        .anomaly-badge {
            background: rgba(229,56,59,0.15);
            border: 1px solid #e5383b;
            border-radius: 8px;
            padding: 8px 14px;
            margin-bottom: 6px;
            color: #ff6b6b;
        }

        /* ── Plotly chart container ── */
        .element-container iframe { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loading (cached) ──────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def get_data() -> pd.DataFrame:
    return load_data()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='text-align:center;margin-bottom:4px;'>🛍️ Retail AI</h2>"
        "<p style='text-align:center;font-size:0.8rem;color:#9b9bbf;margin-top:0;'>"
        "Autonomous Analytics Engine</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    PAGES = {
        "📊 Customer Analytics":  "customer",
        "🛒 Product Analytics":   "product",
        "🚚 Logistics Analytics": "logistics",
        "🤖 AI Insights":         "ai",
    }
    page_label = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
    page = PAGES[page_label]

    st.divider()

    # Load data — show error banner in sidebar if file is missing
    try:
        df = get_data()
        min_d, max_d = get_date_range(df)
        st.success(f"✅ {len(df):,} records loaded")
        st.caption(f"📅 {min_d.strftime('%b %Y')} → {max_d.strftime('%b %Y')}")
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    # ── Date range filter ──────────────────────────────────────────────────
    st.markdown("**Filter by Year**")
    years = sorted(df["Order Date"].dt.year.dropna().unique().astype(int))
    selected_years = st.multiselect("Year", years, default=years)
    if selected_years:
        df = df[df["Order Date"].dt.year.isin(selected_years)]

    st.markdown('<p class="hint">Data: Global Superstore</p>', unsafe_allow_html=True)


# ── Helper: section header ────────────────────────────────────────────────────
def section_header(title: str, subtitle: str = ""):
    st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="section-sub">{subtitle}</p>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Customer Analytics
# ═══════════════════════════════════════════════════════════════════════════════
if page == "customer":
    section_header(
        "📊 Customer Analytics",
        "Revenue breakdown and customer ordering behaviour"
    )

    kpis = ca.get_customer_kpis(df)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Customers",    f"{kpis['total_customers']:,}")
    c2.metric("Total Revenue",      f"${kpis['total_revenue']:,.0f}")
    c3.metric("Avg Order Value",    f"${kpis['avg_order_value']:,.0f}")
    c4.metric("Top Customer",       kpis["top_customer"])

    st.divider()

    # Charts
    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.plotly_chart(ca.top_customers_by_revenue(df), use_container_width=True)
    with col2:
        st.plotly_chart(ca.revenue_by_segment(df),       use_container_width=True)

    st.plotly_chart(ca.orders_per_customer(df), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Product Analytics
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "product":
    section_header(
        "🛒 Product Analytics",
        "Category performance and most profitable products"
    )

    kpis = pa.get_product_kpis(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Products",         f"{kpis['total_products']:,}")
    c2.metric("Total Profit",           f"${kpis['total_profit']:,.0f}")
    c3.metric("Profit Margin",          f"{kpis['profit_margin_pct']:.1f}%")
    c4.metric("Best Category (Sales)",  kpis["best_category_sales"])
    c5.metric("Best Category (Profit)", kpis["best_category_profit"])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(pa.sales_by_category(df),  use_container_width=True)
    with col2:
        st.plotly_chart(pa.profit_by_category(df), use_container_width=True)

    st.plotly_chart(pa.top_profitable_products(df), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Logistics Analytics
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "logistics":
    section_header(
        "🚚 Logistics Analytics",
        "Shipping performance, mode usage and delivery trends"
    )

    kpis = la.get_logistics_kpis(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Avg Shipping Days",   f"{kpis['avg_shipping_days']} days")
    c2.metric("Max Shipping Days",   f"{kpis['max_shipping_days']} days")
    c3.metric("Most Used Mode",      kpis["most_used_mode"])
    c4.metric("Countries Served",    f"{kpis['countries_served']}")
    c5.metric("% Late Deliveries",   f"{kpis['pct_late']}%")

    st.divider()

    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.plotly_chart(la.avg_shipping_time_by_country(df), use_container_width=True)
    with col2:
        st.plotly_chart(la.shipping_mode_distribution(df),   use_container_width=True)

    st.plotly_chart(la.delivery_time_trend(df), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AI Insights
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "ai":
    section_header(
        "🤖 AI Insights",
        "LLM-powered analysis: key insights, root causes, and recommended actions"
    )

    # ── KPI summary strip ──────────────────────────────────────────────────
    kpis = ie.aggregate_kpis(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales",    f"${kpis['total_sales']:,.0f}")
    c2.metric("Total Profit",   f"${kpis['total_profit']:,.0f}")
    c3.metric("Profit Margin",  f"{kpis['profit_margin_pct']}%")
    c4.metric("YoY Growth",     f"{kpis['yoy_sales_growth_pct']}%")

    st.divider()

    # ── Anomaly panel ──────────────────────────────────────────────────────
    anomalies = ie.detect_anomalies(df)
    if anomalies:
        st.markdown("#### ⚡ Detected Anomalies")
        for a in anomalies:
            st.markdown(f'<div class="anomaly-badge">{a}</div>', unsafe_allow_html=True)
        st.divider()
    else:
        st.success("✅ No significant anomalies detected in the current date range.")

    # ── Generate Insights button ───────────────────────────────────────────
    st.markdown(
        "Click the button below to send the KPI summary to the AI model and "
        "receive a structured business analysis."
    )

    if st.button("🚀 Generate AI Insights", type="primary", use_container_width=True):
        with st.spinner("Analysing data and consulting the AI model…"):
            insight_text = ie.generate_insights(df)

        st.markdown("#### 💡 AI Business Analysis")
        st.markdown(
            f'<div class="insight-box">{insight_text}</div>',
            unsafe_allow_html=True,
        )
        # Also render as native markdown for copy-friendly output
        with st.expander("📋 Plain text (copy-friendly)"):
            st.markdown(insight_text)
