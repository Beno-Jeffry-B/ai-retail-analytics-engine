"""
insight_engine.py
-----------------
AI Insight Generator — aggregates KPIs, detects anomalies, and calls an LLM
(Groq) to return concise business insights.

The module works in three stages:
  1. aggregate_kpis(df)    → Compute a summary dict of KPIs
  2. detect_anomalies(df)  → Flag simple statistical anomalies
  3. generate_insights(df) → Build an LLM prompt and return the response text

If the GROQ_API_KEY is not set or the call fails, a graceful fallback message
is returned so the dashboard never crashes.
"""

import os
import pandas as pd
from dotenv import load_dotenv

# Load .env so GROQ_API_KEY is available when running locally
load_dotenv()


# ── KPI Aggregation ──────────────────────────────────────────────────────────

def aggregate_kpis(df: pd.DataFrame) -> dict:
    """
    Compute a comprehensive set of business KPIs from the dataset.

    Returns
    -------
    dict with keys:
        total_sales, total_profit, profit_margin_pct,
        total_orders, total_customers, avg_shipping_days,
        top_category, top_segment, top_country,
        yoy_sales_growth_pct (Year-over-Year growth, latest vs previous year)
    """
    total_sales   = df["Sales"].sum()
    total_profit  = df["Profit"].sum()
    total_orders  = df["Order ID"].nunique()
    total_cust    = df["Customer Name"].nunique()
    profit_margin = (total_profit / total_sales * 100) if total_sales else 0

    avg_ship = (
        df["Shipping Days"].mean()
        if "Shipping Days" in df.columns
        else None
    )

    country_col = "Country/Region" if "Country/Region" in df.columns else "Country"
    top_cat     = df.groupby("Category")["Sales"].sum().idxmax()
    top_seg     = df.groupby("Segment")["Sales"].sum().idxmax()
    top_country = (
        df.groupby(country_col)["Sales"].sum().idxmax()
        if country_col in df.columns else "N/A"
    )

    # Year-over-Year sales growth
    yoy_growth = None
    if "Order Date" in df.columns:
        df = df.copy()
        df["Year"] = df["Order Date"].dt.year
        yearly = df.groupby("Year")["Sales"].sum().sort_index()
        if len(yearly) >= 2:
            prev, curr = yearly.iloc[-2], yearly.iloc[-1]
            yoy_growth = ((curr - prev) / prev * 100) if prev else None

    return {
        "total_sales":          round(total_sales, 2),
        "total_profit":         round(total_profit, 2),
        "profit_margin_pct":    round(profit_margin, 2),
        "total_orders":         total_orders,
        "total_customers":      total_cust,
        "avg_shipping_days":    round(avg_ship, 1) if avg_ship is not None else "N/A",
        "top_category":         top_cat,
        "top_segment":          top_seg,
        "top_country":          top_country,
        "yoy_sales_growth_pct": round(yoy_growth, 2) if yoy_growth is not None else "N/A",
    }


# ── Anomaly Detection ────────────────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame) -> list[str]:
    """
    Detect simple rule-based anomalies in the dataset.

    Checks
    ------
    - Sales drop: Latest month sales < 70 % of the 3-month rolling average
    - Profit drop: Any category with negative total profit
    - Delivery delay: Average shipping days > 5

    Returns
    -------
    list[str]  Human-readable anomaly descriptions (empty list = none found)
    """
    anomalies = []

    # 1. Monthly sales drop
    if "Order Date" in df.columns:
        monthly = (
            df.assign(Month=df["Order Date"].dt.to_period("M"))
            .groupby("Month")["Sales"]
            .sum()
            .sort_index()
        )
        if len(monthly) >= 4:
            rolling_avg = monthly.iloc[-4:-1].mean()
            last_month  = monthly.iloc[-1]
            if rolling_avg > 0 and last_month < 0.70 * rolling_avg:
                drop_pct = ((rolling_avg - last_month) / rolling_avg) * 100
                anomalies.append(
                    f"⚠️  Sales Drop: Last month's sales dropped {drop_pct:.1f}% "
                    f"below the 3-month average."
                )

    # 2. Category-level profit drop (any negative profit category)
    neg_profit_cats = (
        df.groupby("Category")["Profit"]
        .sum()
        .pipe(lambda s: s[s < 0])
        .index.tolist()
    )
    if neg_profit_cats:
        anomalies.append(
            f"⚠️  Profit Drop: Negative profit detected in categories: "
            + ", ".join(neg_profit_cats)
        )

    # 3. Delivery delays
    if "Shipping Days" in df.columns:
        avg_days = df["Shipping Days"].mean()
        if avg_days > 5:
            anomalies.append(
                f"⚠️  Delivery Delay: Average shipping time is {avg_days:.1f} days "
                f"(threshold: 5 days)."
            )

    return anomalies


# ── LLM Insight Generation ───────────────────────────────────────────────────

def generate_insights(df: pd.DataFrame) -> str:
    """
    Generate AI-powered business insights by:
      1. Aggregating KPIs
      2. Detecting anomalies
      3. Building a structured prompt
      4. Calling the Groq LLM (llama3-8b-8192)

    Returns
    -------
    str  Insight text from the LLM, or a fallback message if the call fails.
    """
    kpis      = aggregate_kpis(df)
    anomalies = detect_anomalies(df)

    # ── Build the prompt ────────────────────────────────────────────────────
    anomaly_text = (
        "\n".join(anomalies) if anomalies else "No significant anomalies detected."
    )

    prompt = f"""You are an expert retail business analyst. Based on the following KPI summary and anomaly report for a global superstore, provide a structured analysis.

=== KPI SUMMARY ===
- Total Sales          : ${kpis['total_sales']:,.2f}
- Total Profit         : ${kpis['total_profit']:,.2f}
- Profit Margin        : {kpis['profit_margin_pct']}%
- Total Orders         : {kpis['total_orders']:,}
- Total Customers      : {kpis['total_customers']:,}
- Avg Shipping Days    : {kpis['avg_shipping_days']}
- Top Category (Sales) : {kpis['top_category']}
- Top Segment          : {kpis['top_segment']}
- Top Country          : {kpis['top_country']}
- YoY Sales Growth     : {kpis['yoy_sales_growth_pct']}%

=== ANOMALIES DETECTED ===
{anomaly_text}

Please return the response ONLY in valid Markdown.

Use the exact structure below:

## 🔎 Key Business Insights

- **Insight Title**  
  Short explanation (1 line)

- **Insight Title**  
  Short explanation

## ⚠️ Possible Root Causes

- **Cause**  
  Short explanation

- **Cause**  
  Short explanation

## 🚀 Recommended Actions

- **Action**  
  Short explanation

- **Action**  
  Short explanation

Rules:
- Maximum 5 bullet points per section
- Put the key phrase in **bold**
- Add a new line after every bullet
- Do not put all bullets on one line
"""

    # ── Call Groq API ───────────────────────────────────────────────────────
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return (
            "**AI Insights unavailable** — `GROQ_API_KEY` is not set in your "
            "environment.\n\n"
            "To enable AI insights:\n"
            "1. Create a `.env` file in the project root.\n"
            "2. Add: `GROQ_API_KEY=your_key_here`\n"
            "3. Restart the Streamlit app.\n\n"
            f"---\n**KPI Summary (local)**\n\n"
            f"- Total Sales: ${kpis['total_sales']:,.2f}\n"
            f"- Total Profit: ${kpis['total_profit']:,.2f}\n"
            f"- Profit Margin: {kpis['profit_margin_pct']}%\n"
            f"- Total Orders: {kpis['total_orders']:,}\n"
            f"- Top Category: {kpis['top_category']}\n\n"
            f"**Anomalies**\n\n{anomaly_text}"
        )

    try:
        from groq import Groq  # type: ignore

        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior retail business analyst who provides "
                        "clear, structured, and actionable insights."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as exc:  # noqa: BLE001
        return (
            f"⚠️ **LLM call failed**: {exc}\n\n"
            f"**KPI Summary**\n\n"
            f"- Total Sales: ${kpis['total_sales']:,.2f}\n"
            f"- Total Profit: ${kpis['total_profit']:,.2f}\n"
            f"- Profit Margin: {kpis['profit_margin_pct']}%\n\n"
            f"**Anomalies**\n\n{anomaly_text}"
        )
