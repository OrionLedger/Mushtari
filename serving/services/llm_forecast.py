"""
serving/services/llm_forecast.py

LLM-powered demand forecasting service.
Uses Groq (Llama) to generate demand forecasts from historical sales data.
Falls back to ARIMA if the LLM call fails.
"""

import time
from typing import List, Optional, Dict, Any

from repo import get_repository
from infrastructure.llm.client import get_groq_client
from infrastructure.llm.prompts import build_forecast_prompt
from infrastructure.logging.logger import get_logger
from serving.services.forecast_product import (
    forecast_product as arima_forecast_product,
)

logger = get_logger(__name__)

# ── Scope → readable label ────────────────────────────────────────────────
SCOPE_LABEL = {
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "quarter",
    "5years": "year",
    "beginning": "day",
}


def llm_forecast_product(
    product_id: int,
    horizon: int,
    scope: str = "day",
    repo=None,
) -> Dict[str, Any]:
    """
    Generate a demand forecast using an LLM (Groq/Llama).

    Fetches historical sales data, builds a structured prompt with
    statistics and recent trends, sends it to the LLM, and parses the
    JSON response. Falls back to ARIMA if the LLM fails.

    Args:
        product_id: The product ID.
        horizon: Number of periods to forecast at the requested scope.
        scope: Time scope (day, week, month, year, 5years, beginning).
        repo: Optional repository override.

    Returns:
        Dict with forecast results in the same format as forecast_product().
    """
    start_time = time.time()
    import pandas as pd
    import numpy as np

    pg = repo or get_repository("postgres", shared=True)
    rows = pg.get_record(
        "sales",
        filters={"product_id": product_id},
        columns=["ds", "quantity"],
    )

    if not rows:
        return {
            "product_id": product_id,
            "forecast": [],
            "status": "no_data",
            "method": "llm",
        }

    # ── Prepare data ──────────────────────────────────────────────────────
    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["ds"]).dt.floor("D")
    df["quantity"] = df["quantity"].astype(float)

    daily = df.groupby("ds")["quantity"].sum().reset_index().sort_values("ds")
    daily_series = daily.set_index("ds")["quantity"]

    # ── Feature engineering ───────────────────────────────────────────────
    feat_df = daily.copy()
    feat_df["month"] = feat_df["ds"].dt.month
    feat_df["day_of_week"] = feat_df["ds"].dt.dayofweek
    feat_df["prev_day_sales"] = feat_df["quantity"].shift(1)
    feat_df["rollback_7d"] = feat_df["quantity"].rolling(window=7, min_periods=1).sum().shift(1)

    # Historical features (last 60 days, most recent first)
    recent_feat = feat_df.tail(60).iloc[::-1]
    historical_features = []
    for _, row in recent_feat.iterrows():
        historical_features.append({
            "date": row["ds"].isoformat()[:10],
            "quantity": round(float(row["quantity"]), 1),
            "month": int(row["month"]),
            "day_of_week": int(row["day_of_week"]),
            "prev_day_sales": round(float(row["prev_day_sales"]), 1) if pd.notna(row["prev_day_sales"]) else None,
            "rollback_7d": round(float(row["rollback_7d"]), 1) if pd.notna(row["rollback_7d"]) else None,
        })

    # Future features for the next `horizon` periods
    last_date = daily["ds"].max()
    last_row = feat_df.iloc[-1]
    future_features = []
    for i in range(1, horizon + 1):
        future_date = last_date + pd.Timedelta(days=i)
        future_features.append({
            "period": i,
            "date": future_date.isoformat()[:10],
            "month": future_date.month,
            "day_of_week": future_date.dayofweek,
            "prev_day_sales": round(float(last_row["quantity"]), 1) if i == 1 else None,
            "rollback_7d": round(float(last_row["rollback_7d"]) if pd.notna(last_row["rollback_7d"]) else 0.0, 1) if i == 1 else None,
        })
        last_row = {"quantity": None}

    # Statistics
    daily_mean = float(daily_series.mean())
    daily_std = float(daily_series.std())
    weekly_series = daily_series.resample("W").sum()
    weekly_mean = float(weekly_series.mean())

    # Last N daily values (most recent first, max 60)
    last_daily = daily_series.tail(60).tolist()[::-1]

    # Last N weekly sums (most recent first, max 12)
    last_weekly = weekly_series.tail(12).tolist()[::-1]

    # Last week sum
    last_week_sum = float(last_weekly[0]) if last_weekly else 0.0

    # Day-of-week averages
    dow_map = {}
    for day_num in range(7):
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day_num]
        day_data = daily_series[daily_series.index.dayofweek == day_num]
        dow_map[day_name] = float(day_data.mean()) if len(day_data) > 0 else 0.0

    # Product info for extra context
    product_rows = pg.get_record(
        "products",
        filters={"id": product_id},
        columns=["name", "base_price", "current_stock", "status"],
    )
    product_name = "Unknown"
    extra_context = {}
    if product_rows:
        p = product_rows[0]
        product_name = p.get("name", "Unknown")
        extra_context["base_price"] = p.get("base_price", "N/A")
        extra_context["current_stock"] = p.get("current_stock", "N/A")
        extra_context["status"] = p.get("status", "N/A")

    # ── Build prompt ──────────────────────────────────────────────────────
    scope_label = SCOPE_LABEL.get(scope, "day")
    messages = build_forecast_prompt(
        product_id=product_id,
        product_name=product_name,
        horizon=horizon,
        scope=scope_label,
        daily_values=last_daily,
        weekly_sums=last_weekly,
        daily_mean=daily_mean,
        daily_std=daily_std,
        weekly_mean=weekly_mean,
        last_week_sum=last_week_sum,
        day_of_week_avg=dow_map,
        extra_context=extra_context,
        historical_features=historical_features,
        future_features=future_features,
    )

    # ── Call LLM ──────────────────────────────────────────────────────────
    try:
        logger.info(
            "Calling LLM for forecast",
            product_id=product_id,
            horizon=horizon,
            scope=scope,
        )
        client = get_groq_client()
        llm_response = client.chat(messages)

        forecast = _parse_llm_forecast(llm_response, horizon)

        latency = (time.time() - start_time) * 1000
        logger.info(
            "LLM forecast successful",
            product_id=product_id,
            latency_ms=round(latency, 1),
        )

        return {
            "product_id": product_id,
            "horizon": horizon,
            "scope": scope,
            "forecast": forecast,
            "confidence": llm_response.get("confidence", "medium"),
            "reasoning": llm_response.get("reasoning", ""),
            "risk_factors": llm_response.get("risk_factors", []),
            "latency_ms": latency,
            "status": "success",
            "method": "llm",
        }

    except Exception as e:
        logger.warning(
            "LLM forecast failed, falling back to ARIMA",
            product_id=product_id,
            error=str(e),
        )
        # Fallback to ARIMA
        fallback = arima_forecast_product(
            product_id=product_id,
            horizon=horizon,
            scope=scope,
            repo=repo,
        )
        fallback["method"] = "llm_fallback_arima"
        fallback["llm_error"] = str(e)
        return fallback


def _parse_llm_forecast(response: dict, expected_length: int) -> List[float]:
    """
    Parse and validate the forecast array from an LLM response.

    Args:
        response: Parsed JSON dict from the LLM.
        expected_length: Number of forecast values expected.

    Returns:
        List of validated forecast values.

    Raises:
        ValueError: If the forecast is missing, wrong length, or invalid.
    """
    forecast = response.get("forecast")

    if not forecast:
        raise ValueError("LLM response missing 'forecast' field")

    if not isinstance(forecast, list):
        raise ValueError(f"LLM 'forecast' is not a list: {type(forecast)}")

    # Convert to float, clamp negatives
    cleaned = []
    for i, val in enumerate(forecast):
        try:
            fval = float(val)
            cleaned.append(max(0.0, fval))
        except (ValueError, TypeError):
            raise ValueError(f"Forecast value at index {i} is not a number: {val}")

    # Pad or truncate to expected length
    if len(cleaned) < expected_length:
        # Pad with the last value
        pad_val = cleaned[-1] if cleaned else 0.0
        cleaned.extend([pad_val] * (expected_length - len(cleaned)))
    elif len(cleaned) > expected_length:
        cleaned = cleaned[:expected_length]

    return cleaned
