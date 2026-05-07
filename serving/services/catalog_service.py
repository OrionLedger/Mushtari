from typing import List, Dict, Any, Optional
from repo import get_repository
from etl.config.settings import get_settings

class CatalogService:
    """
    Manages the product and metadata catalog in the relational (Postgres) database.
    This service enriches raw IDs with human-readable descriptions and categories.
    """

    @staticmethod
    def _get_repo():
        settings = get_settings().extract.postgres
        return get_repository(
            "postgres",
            user=settings.user,
            password=settings.password,
            host=settings.host,
            port=settings.port,
            dbname=settings.dbname
        )

    @classmethod
    def get_products(cls, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all active SKUs. Optionally filtered by category.
        """
        repo = cls._get_repo()
        filters = {"status": "active"}
        if category_id:
            filters["category_id"] = category_id
        
        return repo.get_record("products", filters=filters)

    @classmethod
    def get_categories(cls) -> List[Dict[str, Any]]:
        """
        Retrieves the full product category hierarchy.
        """
        repo = cls._get_repo()
        return repo.get_record("categories")

    @classmethod
    def update_product_metadata(cls, product_id: int, updates: Dict[str, Any]) -> bool:
        """
        Updates descriptive metadata for a specific SKU.
        """
        repo = cls._get_repo()
        return repo.update_record("products", product_id, updates)

    @classmethod
    def register_new_sku(cls, sku_data: Dict[str, Any]) -> bool:
        """
        Registers a new product in the relational catalog.
        """
        repo = cls._get_repo()
        return repo.add_record("products", sku_data)
