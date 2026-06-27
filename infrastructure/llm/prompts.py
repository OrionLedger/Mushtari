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
7. Return ONLY valid JSON matching the specified schema exactly.

Your forecast will be compared against traditional ARIMA models. Accuracy matters."""


# ── Prompt Builder ─────────────────────────────────────────────────────────

def build_forecast_prompt(
    product_id: int,
    product_name: str,
    horizon: int,
    scope: str,
    daily_values: List[float],
    weekly_sums: List[float],
    daily_mean: float,
    daily_std: float,
    weekly_mean: float,
    last_week_sum: float,
    day_of_week_avg: Dict[str, float],
    extra_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """
    Build a chat message list (system + user) for LLM demand forecasting.

    Args:
        product_id: Product ID.
        product_name: Product name.
        horizon: Number of periods to forecast.
        scope: Time scope (day, week, month, year, 5years).
        daily_values: Last N daily sales values (most recent first).
        weekly_sums: Last N weekly sums (most recent first).
        daily_mean: Average daily sales over full history.
        daily_std: Standard deviation of daily sales.
        weekly_mean: Average weekly sum over full history.
        last_week_sum: Sum of the most recent (possibly partial) week.
        day_of_week_avg: Dict mapping day name to average sales.
        extra_context: Optional extra info (promotions, stock level, etc.).

    Returns:
        List of {"role": "system"|"user", "content": str} messages.
    """
    # Determine trend direction from recent weeks
    recent_weeks = weekly_sums[-6:] if len(weekly_sums) >= 6 else weekly_sums
    trend = _detect_trend(recent_weeks)

    # Build the user prompt
    lines = [f"Provide a {scope}ly demand forecast for the following product."]
    lines.append("")
    lines.append(f"PRODUCT: {product_name} (ID: {product_id})")
    lines.append(f"FORECAST HORIZON: {horizon} {scope}(s)")
    lines.append("")
    lines.append("HISTORICAL STATISTICS:")
    lines.append(f"  Daily average: {daily_mean:.1f}")
    lines.append(f"  Daily std dev: {daily_std:.1f}")
    lines.append(f"  Weekly average: {weekly_mean:.1f}")
    lines.append(f"  Number of data days: {len(daily_values)}")
    lines.append("")

    if daily_values:
        lines.append(f"LAST {len(daily_values)} DAILY VALUES (most recent first):")
        lines.append(f"  {_format_list(daily_values)}")
        lines.append("")

    if weekly_sums:
        lines.append(f"LAST {len(weekly_sums)} WEEKLY SUMS (most recent first):")
        lines.append(f"  {_format_list(weekly_sums)}")
        lines.append("")

    if day_of_week_avg:
        lines.append("DAY-OF-WEEK AVERAGES:")
        for day, avg in day_of_week_avg.items():
            lines.append(f"  {day}: {avg:.1f}")
        lines.append("")

    lines.append(f"RECENT TREND: {trend}")
    lines.append(f"LAST WEEK SUM: {last_week_sum:.1f}")
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

def _detect_trend(recent_weeks: List[float]) -> str:
    """Detect trend direction from recent weekly values."""
    if len(recent_weeks) < 3:
        return "Insufficient data to determine trend"

    # Simple linear slope approximation
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
        return f"Strong downward trend ({pct_change:.0f}% over recent period)"
    elif pct_change < -3:
        return f"Moderate downward trend ({pct_change:.0f}%)"
    else:
        return "Relatively flat / stable"


def _format_list(values: List[float], precision: int = 1) -> str:
    """Format a list of numbers as a compact string."""
    items = [f"{v:.{precision}f}" for v in values]
    return "[" + ", ".join(items) + "]"
