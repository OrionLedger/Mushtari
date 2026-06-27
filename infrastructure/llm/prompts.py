"""
infrastructure/llm/prompts.py

Prompt templates for LLM-based demand forecasting.
Builds structured prompts from historical sales data and product context.
"""

import json
from typing import List, Dict, Any, Optional


# ── System Prompt ──────────────────────────────────────────────────────────

FORECAST_SYSTEM_PROMPT = """You are a senior demand forecasting analyst for a retail business. Your expertise is in analyzing historical sales data and generating accurate, realistic demand forecasts.

RULES:
1. Analyze the data carefully — look for trends, seasonality, and recent patterns.
2. If the data shows a clear trend (upward or downward), continue that trend in the forecast.
3. If the data is stable with no clear trend, forecast near the historical average.
4. Do NOT converge to the mean too quickly — the first few forecast periods should follow the most recent observed values.
5. Forecast values must be positive numbers (no negatives or zeros unless the data supports it).
6. Be realistic — don't extrapolate extreme values beyond what the data supports.
7. Use the HISTORICAL DATA WITH FEATURES table. Features are computed at the forecast scope (day/week/month/year). Look for seasonal patterns in month, day-of-week, week-of-year, or quarter depending on the scope.
8. The prev_period_sales and rollback_N columns show the previous period's sales and trailing N-period sum. Only period 1 of the forecast has known values for these — for later periods they depend on the forecast itself. Use the calendar-based features (month, day-of-week, etc.) instead.
9. Return ONLY valid JSON matching the specified schema exactly.

Your forecast will be compared against traditional ARIMA models. Accuracy matters."""


# ── Prompt Builder ─────────────────────────────────────────────────────────

def build_forecast_prompt(
    product_id: int,
    product_name: str,
    horizon: int,
    scope: str,
    scope_values: List[float],
    scope_mean: float,
    scope_std: float,
    scope_count: int,
    scope_trend_values: List[float],
    scope_last_value: float,
    day_of_week_avg: Optional[Dict[str, float]] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    historical_features: Optional[List[Dict]] = None,
    future_features: Optional[List[Dict]] = None,
) -> List[Dict[str, str]]:
    """
    Build a chat message list (system + user) for LLM demand forecasting.

    Args:
        product_id: Product ID.
        product_name: Product name.
        horizon: Number of periods to forecast.
        scope: Time scope label (day, week, month, year).
        scope_values: Last N scope-period sales values (most recent first).
        scope_mean: Average sales per scope period.
        scope_std: Standard deviation of per-period sales.
        scope_count: Number of scope periods in history.
        scope_trend_values: Last N scope values for trend detection.
        scope_last_value: Most recent scope period's sales.
        day_of_week_avg: Dict mapping day name to average sales (day scope only).
        extra_context: Optional extra info (promotions, stock level, etc.).
        historical_features: Per-period feature dicts (most recent first).
        future_features: Per-period feature dicts for forecast periods.

    Returns:
        List of {"role": "system"|"user", "content": str} messages.
    """
    scope_cap = scope.capitalize()  # "Day", "Week", "Month", "Year"

    # Determine trend direction from scope-aggregated values
    recent = scope_trend_values[-6:] if len(scope_trend_values) >= 6 else scope_trend_values
    trend = _detect_trend(recent) if len(recent) >= 3 else "Insufficient data to determine trend"

    # Build the user prompt
    lines = [f"Provide a {scope}ly demand forecast for the following product."]
    lines.append("")
    lines.append(f"PRODUCT: {product_name} (ID: {product_id})")
    lines.append(f"FORECAST HORIZON: {horizon} {scope}(s)")
    lines.append("")
    lines.append("HISTORICAL STATISTICS:")
    lines.append(f"  {scope_cap} average: {scope_mean:.1f}")
    lines.append(f"  {scope_cap} std dev: {scope_std:.1f}")
    lines.append(f"  Number of {scope} periods: {scope_count}")
    lines.append("")

    if scope_values:
        lines.append(f"LAST {len(scope_values)} {scope_cap.upper()} VALUES (most recent first):")
        lines.append(f"  {_format_list(scope_values)}")
        lines.append("")

    if day_of_week_avg and scope == "day":
        lines.append("DAY-OF-WEEK AVERAGES:")
        for day, avg in day_of_week_avg.items():
            lines.append(f"  {day}: {avg:.1f}")
        lines.append("")

    # ── Feature table ─────────────────────────────────────────────────────
    # Build headers dynamically from the first feature dict's keys
    hist_key_order = ["date", "quantity", "month", "day_of_week", "week_of_year",
                      "week_of_month", "quarter", "prev_period_sales", "rollback_N"]
    future_key_order = ["period", "date", "month", "day_of_week", "week_of_year",
                        "week_of_month", "quarter", "prev_period_sales", "rollback_N"]

    def _fmt_val(val, width):
        if val is None:
            return "-".center(width)
        if isinstance(val, float):
            return f"{val:>{width}.1f}"
        return f"{str(val):>{width}s}"

    if historical_features:
        # Determine which columns are present
        sample_keys = set(historical_features[0].keys()) if historical_features else set()
        cols = [k for k in hist_key_order if k in sample_keys]
        lines.append(f"HISTORICAL {scope_cap.upper()} DATA WITH FEATURES (most recent first):")
        header = "  " + " | ".join(k.replace("_", " ").title().ljust(10) for k in cols)
        lines.append(header)
        lines.append("  " + "-" * len(header))
        for f in historical_features:
            row_str = "  " + " | ".join(str(f.get(k, "-")).rjust(10) if f.get(k) is not None else "-".rjust(10) for k in cols)
            lines.append(row_str)
        lines.append("")

    if future_features:
        sample_keys = set(future_features[0].keys()) if future_features else set()
        cols = [k for k in future_key_order if k in sample_keys]
        lines.append(f"FEATURES FOR FORECAST {scope_cap.upper()} PERIODS:")
        note = "(month/dow/week_of_year/quarter are known from calendar; prev_period_sales and rollback_N known only for period 1)"
        lines.append("  " + note)
        header = "  " + " | ".join(k.replace("_", " ").title().ljust(10) for k in cols)
        lines.append(header)
        lines.append("  " + "-" * len(header))
        for f in future_features:
            row_str = "  " + " | ".join(str(f.get(k, "-")).rjust(10) if f.get(k) is not None else "-".rjust(10) for k in cols)
            lines.append(row_str)
        lines.append("")

    lines.append(f"RECENT TREND: {trend}")
    lines.append(f"LAST {scope_cap.upper()} VALUE: {scope_last_value:.1f}")
    lines.append("")

    if extra_context:
        lines.append("ADDITIONAL CONTEXT:")
        for key, value in extra_context.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    # Output format specification
    lines.append("Respond with JSON in the following format EXACTLY:")
    lines.append("{")
    lines.append(f'  "forecast": [<float>, <float>, ...],')
    lines.append('  "confidence": "high" | "medium" | "low",')
    lines.append('  "reasoning": "Brief explanation of the key patterns and logic used",')
    lines.append('  "risk_factors": ["Risk factor 1", "Risk factor 2", ...]')
    lines.append("}")
    lines.append("")
    lines.append(
        f"The forecast array must contain exactly {horizon} numbers "
        f"representing {scope}ly demand predictions."
    )

    user_content = "\n".join(lines)

    return [
        {"role": "system", "content": FORECAST_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ── Helpers ────────────────────────────────────────────────────────────────

def _detect_trend(recent_values: List[float]) -> str:
    """Detect trend direction from recent aggregated values."""
    if len(recent_values) < 3:
        return "Insufficient data to determine trend"

    # Simple linear slope approximation
    n = len(recent_values)
    x_avg = (n - 1) / 2.0
    y_avg = sum(recent_values) / n

    num = sum((i - x_avg) * (recent_values[i] - y_avg) for i in range(n))
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
        return f"Strong downward trend ({pct_change:.0f}% over recent period)"
    elif pct_change < -3:
        return f"Moderate downward trend ({pct_change:.0f}%)"
    else:
        return "Relatively flat / stable"


def _format_list(values: List[float], precision: int = 1) -> str:
    """Format a list of numbers as a compact string."""
    items = [f"{v:.{precision}f}" for v in values]
    return "[" + ", ".join(items) + "]"
