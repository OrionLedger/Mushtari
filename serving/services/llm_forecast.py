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

# ── Scope mappings ───────────────────────────────────────────────────────
SCOPE_LABEL = {
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "year",
    "5years": "year",
    "beginning": "day",
}

SCOPE_RULE = {
    "day": "D",
    "week": "W",
    "month": "ME",
    "year": "YE",
    "5years": "YE",
    "beginning": "D",
}

SCOPE_MAX_VALUES = {
    "day": 60,
    "week": 26,
    "month": 24,
    "year": 10,
}

# Each scope defines which features to compute.
# Tuple: (column_name, extractor_callable, is_known_for_future)
SCOPE_FEATURES = {
    "day": [
        ("month", lambda r: r["ds"].month, True),
        ("day_of_week", lambda r: r["ds"].dayofweek, True),
        ("prev_period_sales", None, False),
        ("rollback_N", None, False),
    ],
    "week": [
        ("month", lambda r: r["ds"].month, True),
        ("week_of_year", lambda r: r["ds"].isocalendar().week, True),
        ("week_of_month", lambda r: (r["ds"].day - 1) // 7 + 1, True),
        ("prev_period_sales", None, False),
        ("rollback_N", None, False),
    ],
    "month": [
        ("month", lambda r: r["ds"].month, True),
        ("quarter", lambda r: r["ds"].quarter, True),
        ("prev_period_sales", None, False),
        ("rollback_N", None, False),
    ],
    "year": [
        ("prev_period_sales", None, False),
    ],
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

    # ── Resample to scope ─────────────────────────────────────────────────
    rule = SCOPE_RULE.get(scope, "D")
    scope_series = daily_series.resample(rule).sum()
    scope_count = len(scope_series)
    scope_mean = float(scope_series.mean())
    scope_std = float(scope_series.std())

    # Last N scope values (most recent first)
    max_n = SCOPE_MAX_VALUES.get(scope, 60)
    scope_values = scope_series.tail(max_n).tolist()[::-1]
    scope_last_value = float(scope_series.iloc[-1]) if len(scope_series) > 0 else 0.0

    # ── Trend on scope-aggregated data ────────────────────────────────────
    scope_trend_values = scope_series.tail(12).tolist()[::-1]

    # ── Day-of-week averages (only for day scope) ─────────────────────────
    dow_map = {}
    if scope == "day":
        for day_num in range(7):
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day_num]
            day_data = daily_series[daily_series.index.dayofweek == day_num]
            dow_map[day_name] = float(day_data.mean()) if len(day_data) > 0 else 0.0

    # ── Feature engineering on scope-aggregated data ──────────────────────
    scope_feat_df = scope_series.reset_index(name="quantity")
    scope_feat_df.columns = ["ds", "quantity"]

    # Add feature columns based on scope
    for col_name, extractor, _ in SCOPE_FEATURES.get(scope, SCOPE_FEATURES["day"]):
        if extractor is not None:
            scope_feat_df[col_name] = scope_feat_df.apply(extractor, axis=1)

    # Add rolling/lag features
    scope_feat_df["prev_period_sales"] = scope_feat_df["quantity"].shift(1)
    if scope == "day":
        scope_feat_df["rollback_N"] = scope_feat_df["quantity"].rolling(7).sum().shift(1)
    elif scope == "week":
        scope_feat_df["rollback_N"] = scope_feat_df["quantity"].rolling(4).sum().shift(1)
    elif scope == "month":
        scope_feat_df["rollback_N"] = scope_feat_df["quantity"].rolling(3).sum().shift(1)

    # Historical features (most recent first)
    recent_feat = scope_feat_df.tail(max_n).iloc[::-1]
    feature_cols = [col for col, _, _ in SCOPE_FEATURES.get(scope, SCOPE_FEATURES["day"])]

    def _build_hist_dict(row):
        feat = {"date": row["ds"].isoformat()[:10], "quantity": round(float(row["quantity"]), 1)}
        for col in feature_cols:
            if col in row.index:
                val = row[col]
                if pd.notna(val):
                    try:
                        feat[col] = round(float(val), 1) if col in ("prev_period_sales", "rollback_N") else int(val)
                    except (ValueError, TypeError):
                        feat[col] = None
                else:
                    feat[col] = None
        return feat

    historical_features = [_build_hist_dict(row) for _, row in recent_feat.iterrows()]

    # Future features
    last_date = scope_feat_df["ds"].max()
    last_historical = scope_feat_df.iloc[-1]
    last_quantity = float(last_historical["quantity"])
    last_rollback = float(last_historical.get("rollback_N", 0.0)) if pd.notna(last_historical.get("rollback_N", None)) else None
    import datetime as _dt_mod

    future_features = []
    for i in range(1, horizon + 1):
        if scope == "day":
            future_date = last_date + pd.Timedelta(days=i)
        elif scope == "week":
            future_date = last_date + pd.Timedelta(weeks=i)
        elif scope == "month":
            m = last_date.month - 1 + i
            y = last_date.year + m // 12
            m = m % 12 + 1
            d = min(last_date.day, [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30,
                                    31, 31, 30, 31, 30, 31][m - 1])
            future_date = pd.Timestamp(_dt_mod.date(y, m, d))
        else:
            future_date = pd.Timestamp(year=last_date.year + i, month=1, day=1)

        feat = {"period": i, "date": future_date.isoformat()[:10]}
        for col, extractor, is_known in SCOPE_FEATURES.get(scope, SCOPE_FEATURES["day"]):
            if extractor is not None and is_known:
                feat[col] = int(extractor(future_date))
            elif col == "prev_period_sales":
                feat[col] = round(last_quantity, 1) if i == 1 else None
            elif col == "rollback_N":
                feat[col] = round(last_rollback, 1) if i == 1 and last_rollback is not None else None
            else:
                feat[col] = None
        future_features.append(feat)

    # ── Product info for extra context ────────────────────────────────────
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
        scope_values=scope_values,
        scope_mean=scope_mean,
        scope_std=scope_std,
        scope_count=scope_count,
        scope_trend_values=scope_trend_values,
        scope_last_value=scope_last_value,
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
