"""In-memory holder for whichever product catalog is currently indexed.

Populated at startup from data/products.json, and replaced wholesale by
POST /index (see main.py). Other modules read the current catalog through
this module rather than re-reading data_loader's file-based default, so a
freshly uploaded dataset is reflected everywhere immediately.
"""

from __future__ import annotations

from app.models import Product

_current_products: list[Product] = []
_current_products_by_id: dict[int, Product] = {}
_current_categories: set[str] = set()


def set_current_products(products: list[Product]) -> None:
    """Replace the active catalog and refresh its derived lookup structures."""
    global _current_products, _current_products_by_id, _current_categories
    _current_products = products
    _current_products_by_id = {product.id: product for product in products}
    _current_categories = {product.category for product in products}


def get_current_products() -> list[Product]:
    return _current_products


def get_known_categories() -> set[str]:
    return _current_categories


def get_products_by_id() -> dict[int, Product]:
    """Return the active catalog's ID lookup built during catalog replacement."""
    return _current_products_by_id
