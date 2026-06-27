"""
serving/services/llm_insight.py

LLM-powered import & ordering insights for a product.

Gathers product details, sales statistics, forecast, and XGBoost
prediction, then calls Groq (Llama) to generate a structured
reorder recommendation with supporting reasoning and risk factors.
"""

import time
from typing import Optional, Dict, Any
import pandas as pd

from repo import get_repository
from infrastructure.llm.client import get_groq_client
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

# ── Fallback lead time (days) ─────────────────────────────────────────────
# Ideally this comes from a `lead_time_days` column in the products table.
DEFAULT_LEAD_TIME_DAYS = 14


# ── System Prompt ─────────────────────────────────────────────────────────

INSIGHT_SYSTEM_PROMPT = """You are a senior supply chain analyst helping a retailer make data-driven import and ordering decisions.

Your goal is to provide actionable, concise recommendations based solely on the data provided. Never fabricate numbers or make assumptions beyond what is given.

RULES:
1. Base reorder urgency on: current stock vs safety stock, daily sales velocity, forecasted demand, and days of cover.
2. Days of cover = current_stock / daily_avg. If daily_avg is 0, days of cover is infinite ("none").
3. Stock-out risk = days until stock reaches zero if current sales continue.
4. If current stock is ABOVE safety stock * 3, the product is overstocked — flag it.
5. If current stock is BELOW safety stock, the product is understocked — recommend immediate reorder.
6. If current stock is at or near zero, recommend URGENT reorder.
7. Consider the sales trend: upward trend means order more, downward trend means be cautious.
8. The forecast values are predicted demand for upcoming periods — use them to size the order.
9. The XGBoost prediction is the next single period — treat it as a near-term signal.
10. Margin = (base_price - unit_cost) / base_price. Higher margin means more room for bulk ordering.
11. Recommend specific order quantities (round numbers) and specific timelines (in days).
12. Be conservative — it is better to recommend a slightly larger order than to risk a stockout.
13. The ENTIRE response must be in **Arabic** (العربية). The `reorder_recommendation`, `key_factors`, and `risk_factors` fields must all be written in clear, simple Arabic that any merchant can understand instantly.
14. Use natural merchant-friendly Arabic — short phrases like "المبيعات مرتفعة هذا الشهر", "المخزون الحالي قليل جداً", "اطلب 80 قطعة خلال 5 أيام" — not technical or academic language.
15. Return ONLY valid JSON matching the specified schema exactly.

Your recommendations directly impact business operations. Accuracy and clarity matter."""


# ── Prompt Builder ─────────────────────────────────────────────────────────

def build_insight_prompt(
    product_id: int,
    product_name: str,
    sku_code: str,
    current_stock: int,
    safety_stock: int,
    base_price: float,
    unit_cost: float,
    status: str,
    daily_avg: float,
    daily_std: float,
    weekly_avg: float,
    monthly_avg: float,
    trend_description: str,
    forecast_values: list,
    xgb_prediction: Optional[float],
    scope: str,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
) -> list:
    """
    Build chat messages for the LLM insight generation call.

    Args:
        product_id: Product ID.
        product_name: Product display name.
        sku_code: SKU / stock-keeping unit code.
        current_stock: Current inventory count.
        safety_stock: Safety stock threshold.
        base_price: Selling price.
        unit_cost: Unit cost (COGS).
        status: Product status (active, inactive, etc.).
        daily_avg: Average daily sales over full history.
        daily_std: Daily sales standard deviation.
        weekly_avg: Average weekly sales.
        monthly_avg: Average monthly sales.
        trend_description: Human-readable trend string.
        forecast_values: Predicted future values (scope units).
        xgb_prediction: XGBoost next-period prediction, or None.
        scope: Time scope of the forecast.
        lead_time_days: Supplier lead time in days.

    Returns:
        List of {"role": "system"|"user", "content": str} messages.
    """
    margin_pct = round((base_price - unit_cost) / base_price * 100, 1) if base_price > 0 else 0.0
    days_of_cover = round(current_stock / daily_avg, 1) if daily_avg > 0 else float("inf")

    # Stock-out risk
    stock_out_in_days = "N/A"
    if daily_avg > 0 and current_stock > 0:
        stock_out_in_days = str(round(current_stock / daily_avg, 1))

    lines = [
        f"PRODUCT: {product_name} (ID: {product_id})",
        f"  SKU: {sku_code}",
        f"  Status: {status}",
        f"  Current stock: {current_stock} units",
        f"  Safety stock: {safety_stock} units",
        f"  Days of cover (at current velocity): {days_of_cover if days_of_cover != float('inf') else 'Infinite (no sales)'}",
        f"  Stock-out in: {stock_out_in_days} days",
        f"  Base price: ${base_price:.2f}",
        f"  Unit cost: ${unit_cost:.2f}",
        f"  Margin: {margin_pct}%",
        f"  Lead time: {lead_time_days} days",
        "",
        "SALES VELOCITY:",
        f"  Daily average: {daily_avg:.1f}  (std dev: ±{daily_std:.1f})",
        f"  Weekly average: {weekly_avg:.1f}",
        f"  Monthly average: {monthly_avg:.1f}",
        f"  Recent trend: {trend_description}",
        "",
    ]

    if forecast_values:
        scope_label = scope if scope != "beginning" else "day"
        forecast_str = ", ".join(f"{v:.1f}" for v in forecast_values)
        lines.append(f"FORECAST (next {len(forecast_values)} {scope_label}(s)):")
        lines.append(f"  [{forecast_str}]")
        lines.append("")

    if xgb_prediction is not None:
        lines.append(f"XGBoost PREDICTION (next {scope}): {xgb_prediction:.1f} units")
        lines.append("")

    lines.append("")
    lines.append("RESPOND WITH JSON IN THIS EXACT FORMAT:")
    lines.append("{")
    lines.append('  "reorder_recommendation": "Short actionable sentence IN ARABIC (e.g. اطلب 80 قطعة خلال 5 أيام)",')
    lines.append('  "order_quantity": <integer>,')
    lines.append('  "reorder_in_days": <integer>,')
    lines.append('  "stock_out_in_days": <integer | null>,')
    lines.append('  "confidence": "high" | "medium" | "low",')
    lines.append('  "key_factors": ["Factor 1", "Factor 2", ...],')
    lines.append('  "risk_factors": ["Risk 1", "Risk 2", ...]')
    lines.append("}")
    lines.append("")
    lines.append("Interpretation guide:")
    lines.append("- `order_quantity`: how many units to order NOW")
    lines.append("- `reorder_in_days`: how many days until the order must be placed (0 = today)")
    lines.append("- `stock_out_in_days`: expected days until stock hits zero if no reorder (null = no risk)")
    lines.append("- `key_factors`: top 2-4 factors in ARABIC, clear for a merchant (e.g. المبيعات مرتفعة, المخزون قليل)")
    lines.append("- `risk_factors`: top 1-3 risks in ARABIC, clear for a merchant (e.g. تأخير في التوريد, زيادة غير متوقعة في الطلب)")

    user_content = "\n".join(lines)

    return [
        {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ── Trend detection (reuses logic from prompts.py) ────────────────────────

def _detect_trend(recent_weeks: list) -> str:
    """Detect trend direction from recent weekly values (most-recent-first)."""
    if len(recent_weeks) < 3:
        return "Insufficient data to determine trend"
    n = len(recent_weeks)
    x_avg = (n - 1) / 2.0
    y_avg = sum(recent_weeks) / n
    num = sum((i - x_avg) * (recent_weeks[i] - y_avg) for i in range(n))
    den = sum((i - x_avg) ** 2 for i in range(n))
    if den == 0:
        return "Flat / no clear trend"
    slope = num / den
    pct_change = (slope * n / y_avg * 100) if y_avg != 0 else 0
    if pct_change > 10:
        return f"Strong upward trend (+{pct_change:.0f}% over recent period)"
    elif pct_change > 3:
        return f"Moderate upward trend (+{pct_change:.0f}%)"
    elif pct_change < -10:
        return f"Strong downward trend ({pct_change:.0f}%)"
    elif pct_change < -3:
        return f"Moderate downward trend ({pct_change:.0f}%)"
    else:
        return "Relatively flat / stable"


# ── Main service function ─────────────────────────────────────────────────

def llm_product_insight(
    product_id: int,
    scope: str = "week",
    horizon: int = 4,
    repo=None,
) -> Dict[str, Any]:
    """
    Generate import/ordering insights for a product using an LLM.

    Args:
        product_id: The product ID.
        scope: Time scope for scale (day, week, month).
        horizon: Number of forecast periods to include.
        repo: Optional repository override.

    Returns:
        Dict with structured insight, or error status.
    """
    start_time = time.time()
    pg = repo or get_repository("postgres", shared=True)
    import numpy as np

    # ── 1. Load product details ──────────────────────────────────────────
    product_rows = pg.get_record(
        "products",
        filters={"id": product_id},
        columns=[
            "id", "name", "sku_code", "base_price", "unit_cost",
            "current_stock", "safety_stock", "status",
        ],
    )
    if not product_rows:
        return {
            "product_id": product_id,
            "status": "error",
            "message": f"Product {product_id} not found",
        }
    prod = product_rows[0]
    p_name = prod.get("name", "Unknown")
    p_sku = prod.get("sku_code", "")
    p_stock = prod.get("current_stock", 0) or 0
    p_safety = prod.get("safety_stock", 0) or 0
    p_price = float(prod.get("base_price", 0) or 0)
    p_cost = float(prod.get("unit_cost", 0) or 0)
    p_status = prod.get("status", "active")

    # ── 2. Load sales data ───────────────────────────────────────────────
    rows = pg.get_record(
        "sales",
        filters={"product_id": product_id},
        columns=["ds", "quantity"],
    )
    if not rows or len(rows) < 14:
        return {
            "product_id": product_id,
            "product_name": p_name,
            "status": "no_data",
            "message": "Insufficient sales data — need at least 14 daily records for meaningful insights.",
        }

    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["ds"]).dt.floor("D")
    df["quantity"] = df["quantity"].astype(float)
    daily = df.groupby("ds")["quantity"].sum().reset_index().sort_values("ds")
    daily_series = daily.set_index("ds")["quantity"]

    daily_avg = float(daily_series.mean())
    daily_std = float(daily_series.std())

    # Weekly sums (drop trailing incomplete week)
    weekly_series = daily_series.resample("W").sum()
    if len(weekly_series) > 0:
        last_label = weekly_series.index[-1]
        week_start = last_label - pd.Timedelta(days=6)
        days_in_last_week = len(daily_series[
            (daily_series.index >= week_start) &
            (daily_series.index <= last_label)
        ])
        if days_in_last_week < 7:
            weekly_series = weekly_series.iloc[:-1]

    weekly_avg = float(weekly_series.mean()) if len(weekly_series) > 0 else 0.0
    recent_weeks = weekly_series.tail(12).tolist()[::-1]
    trend_str = _detect_trend(recent_weeks)

    # Monthly average
    monthly_series = daily_series.resample("ME").sum()
    monthly_avg = float(monthly_series.mean()) if len(monthly_series) > 0 else 0.0

    # ── 3. Get forecast from the LLM forecast service ────────────────────
    from serving.services.llm_forecast import llm_forecast_product

    try:
        forecast_result = llm_forecast_product(
            product_id=product_id,
            horizon=horizon,
            scope=scope,
            repo=repo,
        )
        forecast_values = forecast_result.get("forecast", [])
    except Exception as e:
        logger.warning("Forecast fetch failed for insight", product_id=product_id, error=str(e))
        forecast_values = []

    # ── 4. Get XGBoost prediction ────────────────────────────────────────
    from serving.services.predict_product_demand import predict_product_demand

    xgb_prediction = None
    try:
        xgb_result = predict_product_demand(
            product_id=product_id,
            scope=scope,
        )
        if xgb_result.get("status") == "success":
            xgb_prediction = xgb_result.get("prediction")
    except Exception as e:
        logger.debug("XGBoost not available for insight", product_id=product_id, error=str(e))

    # ── 5. Build prompt and call LLM ─────────────────────────────────────
    messages = build_insight_prompt(
        product_id=product_id,
        product_name=p_name,
        sku_code=p_sku,
        current_stock=p_stock,
        safety_stock=p_safety,
        base_price=p_price,
        unit_cost=p_cost,
        status=p_status,
        daily_avg=daily_avg,
        daily_std=daily_std,
        weekly_avg=weekly_avg,
        monthly_avg=monthly_avg,
        trend_description=trend_str,
        forecast_values=forecast_values,
        xgb_prediction=xgb_prediction,
        scope=scope,
    )

    try:
        client = get_groq_client()
        llm_response = client.chat(messages)

        # Validate required fields
        required = ["reorder_recommendation", "order_quantity", "reorder_in_days", "confidence"]
        for field in required:
            if field not in llm_response:
                raise ValueError(f"LLM response missing required field: {field}")

        # Ensure order_quantity is positive int
        order_qty = max(0, int(llm_response.get("order_quantity", 0)))
        reorder_in = max(0, int(llm_response.get("reorder_in_days", 0)))

        latency = (time.time() - start_time) * 1000

        return {
            "product_id": product_id,
            "product_name": p_name,
            "scope": scope,
            "reorder_recommendation": llm_response.get("reorder_recommendation", ""),
            "order_quantity": order_qty,
            "reorder_in_days": reorder_in,
            "stock_out_in_days": llm_response.get("stock_out_in_days"),
            "confidence": llm_response.get("confidence", "medium"),
            "key_factors": llm_response.get("key_factors", []),
            "risk_factors": llm_response.get("risk_factors", []),
            "latency_ms": round(latency, 1),
            "status": "success",
        }

    except Exception as e:
        logger.error("LLM insight generation failed", product_id=product_id, error=str(e))
        # Fallback: return a simple data-driven insight without LLM
        latency = (time.time() - start_time) * 1000
        return _fallback_insight(
            product_id=product_id,
            product_name=p_name,
            current_stock=p_stock,
            safety_stock=p_safety,
            daily_avg=daily_avg,
            lead_time_days=DEFAULT_LEAD_TIME_DAYS,
            latency_ms=round(latency, 1),
            error=str(e),
        )


def _fallback_insight(
    product_id: int,
    product_name: str,
    current_stock: int,
    safety_stock: int,
    daily_avg: float,
    lead_time_days: int,
    latency_ms: float,
    error: str,
) -> Dict[str, Any]:
    """Generate a simple rule-based insight when the LLM is unavailable."""
    days_of_cover = round(current_stock / daily_avg, 1) if daily_avg > 0 else float("inf")

    if days_of_cover == float("inf"):
        rec = "No sales data — monitor inventory manually."
        order_qty = 0
        reorder_in = 999
        confidence = "low"
        factors = ["No sales history available"]
        risks = ["Cannot determine demand pattern"]
    elif current_stock <= 0:
        rec = f"URGENT: Stock is depleted. Place an emergency order immediately."
        order_qty = max(safety_stock * 2, 50)
        reorder_in = 0
        confidence = "medium"
        factors = ["Current stock is zero"]
        risks = ["Stockout likely causing lost sales"]
    elif days_of_cover <= lead_time_days:
        rec = f"Reorder soon — stock will run out within {days_of_cover} days (lead time: {lead_time_days}d)."
        order_qty = max(int(daily_avg * lead_time_days * 1.5), safety_stock)
        reorder_in = max(0, int(days_of_cover - lead_time_days * 0.7))
        confidence = "medium"
        factors = [f"Days of cover ({days_of_cover}) <= lead time ({lead_time_days}d)"]
        risks = ["Lead time delays could cause stockout"]
    elif current_stock < safety_stock:
        rec = f"Below safety stock ({current_stock} < {safety_stock}). Reorder to restore buffer."
        order_qty = int(safety_stock * 1.5)
        reorder_in = 0
        confidence = "high"
        factors = [f"Stock ({current_stock}) below safety stock ({safety_stock})"]
        risks = ["Unexpected demand spike could cause stockout"]
    else:
        rec = f"Stock level is adequate ({current_stock}, {days_of_cover} days of cover). No urgent reorder needed."
        order_qty = 0
        reorder_in = max(1, int(days_of_cover - lead_time_days))
        confidence = "high"
        factors = [f"Days of cover ({days_of_cover}) exceeds lead time ({lead_time_days}d)"]
        risks = ["Sales velocity increase could reduce days of cover"]

    return {
        "product_id": product_id,
        "product_name": product_name,
        "reorder_recommendation": rec,
        "order_quantity": order_qty,
        "reorder_in_days": reorder_in,
        "stock_out_in_days": int(days_of_cover) if days_of_cover != float("inf") else None,
        "confidence": confidence,
        "key_factors": factors,
        "risk_factors": risks,
        "latency_ms": latency_ms,
        "status": "success",
        "method": "fallback_rule",
        "llm_error": error,
    }
