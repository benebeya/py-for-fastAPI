"""Routing layer. Uses RELATIVE imports to show the other style.

  .        = this package (shop.routers)
  ..       = parent package (shop)
  ..models = shop.models

Relative imports are shorter and survive a package rename, but they only work
INSIDE a package -- you cannot run this file directly as a script.
"""

from ..models import Product
from ..services.catalog import get_product, list_products


def index() -> list[str]:
    return [p.name for p in list_products()]


def detail(name: str) -> Product | None:
    return get_product(name)


print("     [shop/routers/products.py executed]")
