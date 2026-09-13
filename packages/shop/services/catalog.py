"""Business logic. Uses ABSOLUTE imports -- unambiguous, and the style most
FastAPI projects standardise on."""

from shop.config import settings
from shop.models import Product

_CATALOG: dict[str, Product] = {
    "wine": Product("wine", 500),
    "tomatoes": Product("tomatoes", 1000),
}


def list_products() -> list[Product]:
    return list(_CATALOG.values())


def get_product(name: str) -> Product | None:
    return _CATALOG.get(name)


def app_name() -> str:
    return settings.app_name


print("     [shop/services/catalog.py executed]")
