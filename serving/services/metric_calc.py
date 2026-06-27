from typing import List, Dict, Any, Optional
from repo import get_repository
import pandas as pd
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

SALES_TABLE = "sales"


class MetricCalc:
    """
    Business Intelligence Service that reads from the configured repository
    (PostgreSQL or SQLite) for a unified view of sales and product data.
    """

    @staticmethod
    def _get_repo():
        """Return the configured repository (routes to SQLite in local mode)."""
        return get_repository("postgres", shared=True)

    @classmethod
    def get_business_kpis(cls) -> Dict[str, Any]:
        """
        Calculates high-level KPIs from sales and product data.
        """
        repo = cls._get_repo()

        # 1. Fetch sales volume
        rows = repo.get_record(SALES_TABLE, columns=["product_id", "quantity", "price_at_sale", "ds"])
        if not rows:
            return {"total_volume": 0, "revenue": "$0", "growth": "0%", "conversion": "N/A", "margin": "0%"}

        df = pd.DataFrame(rows)
        df['revenue'] = df['quantity'].apply(float) * df['price_at_sale'].apply(float)

        # 2. Extract Product Costs
        products = repo.get_record("products", columns=["id", "unit_cost"])
        cost_map = {p['id']: float(p['unit_cost']) for p in products}

        df['unit_cost'] = df['product_id'].map(cost_map).fillna(0.0)
        df['total_cost'] = df['quantity'].apply(float) * df['unit_cost']

        total_revenue = float(df['revenue'].sum())
        total_cost = float(df['total_cost'].sum())
        total_volume = int(df['quantity'].sum())

        margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0.0

        # 3. Growth Calculation
        df = df.sort_values('ds')
        midpoint = len(df) // 2
        recent_rev = float(df.iloc[midpoint:]['revenue'].sum()) if midpoint > 0 else total_revenue
        prev_rev = float(df.iloc[:midpoint]['revenue'].sum()) if midpoint > 0 else total_revenue
        rev_change = ((recent_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0

        return {
            "total_volume": total_volume,
            "revenue": f"${total_revenue:,.0f}",
            "growth": f"{rev_change:.1f}%",
            "conversion": "Pending",
            "margin": f"{margin:.1f}%",
            "revenue_change": f"{'+' if rev_change >= 0 else ''}{rev_change:.2f}%",
            "growth_change": "Steady" if abs(rev_change) < 10 else "High Velocity",
        }

    @classmethod
    def get_revenue_breakdown(cls, category: str = "product") -> List[Dict[str, Any]]:
        """
        Calculates real revenue per product using price_at_sale.
        """
        repo = cls._get_repo()

        rows = repo.get_record(SALES_TABLE, columns=["product_id", "quantity", "price_at_sale"])
        if not rows:
            return []

        df = pd.DataFrame(rows)
        df['rev_contribution'] = df['quantity'].apply(float) * df['price_at_sale'].apply(float)

        grouped = df.groupby('product_id')['rev_contribution'].sum().reset_index()

        product_metadata = repo.get_record("products", columns=["id", "name"])
        name_map = {row['id']: row['name'] for row in product_metadata}

        result = []
        for _, row in grouped.iterrows():
            product_id = int(row['product_id'])
            name = name_map.get(product_id, f"SKU #{product_id}")
            result.append({
                "name": name,
                "value": int(row['rev_contribution'])
            })

        return sorted(result, key=lambda x: x['value'], reverse=True)[:5]

    @classmethod
    def get_demand_trends(cls, scope: str = "week") -> List[Dict[str, Any]]:
        """
        Aggregates sales records into time-buckets for charting.
        """
        repo = cls._get_repo()

        rows = repo.get_record(SALES_TABLE, columns=["ds", "quantity"])
        if not rows:
            return []

        df = pd.DataFrame(rows)
        df['ds'] = pd.to_datetime(df['ds'])
        df['sales'] = df['quantity'].apply(float)

        freq_map = {"day": "D", "week": "W", "month": "M", "year": "Q"}
        freq = freq_map.get(scope, "W")

        resampled = df.resample(freq, on='ds')['sales'].sum().reset_index()

        result = []
        for _, row in resampled.iterrows():
            date_str = row['ds'].strftime("%Y-%m-%d") if freq == 'D' else row['ds'].strftime("%b %d")
            result.append({
                "name": date_str,
                "sales": int(row['sales']),
                "forecast": int(row['sales'] * 1.1)
            })

        return result

    @classmethod
    def get_user_stats(cls, category: str = "device") -> List[Dict[str, Any]]:
        """Mock user acquisition stats."""
        if category == "device":
            return [
                {"name": "Mobile", "value": 65, "color": "var(--accent-color)"},
                {"name": "Desktop", "value": 25, "color": "#a855f7"},
                {"name": "Tablet", "value": 10, "color": "#3b82f6"}
            ]
        else:
            return [
                {"name": "Direct", "value": 40, "color": "var(--accent-color)"},
                {"name": "Organic", "value": 35, "color": "#a855f7"},
                {"name": "Social", "value": 25, "color": "#f59e0b"}
            ]

    @classmethod
    def get_inventory_status(cls, query: str = "") -> List[Dict[str, Any]]:
        """
        Combines product metadata with stock velocity calculated from sales data.
        """
        repo = cls._get_repo()

        try:
            products_raw = repo.get_record("products", columns=[
                "id", "name", "category_id", "status", "current_stock", "safety_stock"
            ])
            categories = {row['id']: row['name'] for row in repo.get_record("categories")}
        except Exception as e:
            logger.error(f"Products fetch failed in inventory status: {e}")
            products_raw = []
            categories = {}

        try:
            sales_rows = repo.get_record(SALES_TABLE, columns=["product_id", "quantity"])
            sales_df = pd.DataFrame(sales_rows)
            velocity_map = {}
            all_sold_product_ids = set()
            if not sales_df.empty:
                velocity_map = sales_df.groupby('product_id')['quantity'].mean().to_dict()
                all_sold_product_ids = set(velocity_map.keys())
        except Exception as e:
            logger.error(f"Sales fetch failed in inventory status: {e}")
            velocity_map = {}
            all_sold_product_ids = set()

        postgres_map = {p['id']: p for p in products_raw}
        all_product_ids = set(postgres_map.keys()) | all_sold_product_ids

        inventory = []
        for pid in all_product_ids:
            prod = postgres_map.get(pid, {
                "id": pid,
                "name": f"Unknown SKU #{pid}",
                "category_id": None,
                "current_stock": 0,
                "safety_stock": 0
            })

            if query.lower() and query.lower() not in prod['name'].lower():
                continue

            velocity = float(velocity_map.get(pid, 0.0))
            stock = int(prod.get('current_stock', 0))
            safety = int(prod.get('safety_stock', 10))

            risk_level = "High" if stock <= safety else "Low"
            if stock > safety and velocity > 15.0:
                risk_level = "Monitor"

            inventory.append({
                "id": pid,
                "name": prod['name'],
                "category": categories.get(prod['category_id'], "Uncategorized"),
                "stock": stock,
                "velocity": round(velocity, 2),
                "risk": risk_level
            })

        return sorted(inventory, key=lambda x: x['id'])
