"""The `shop` package.

__init__.py does two jobs:
  1. marks this directory as a package (optional since 3.3, but ALWAYS do it)
  2. runs when the package is first imported -- so it defines the public API

Keep it thin. Heavy work here slows every import and invites circular imports.
"""

__version__ = "0.1.0"

# Re-export so callers can write `from shop import Product`
# instead of `from shop.models import Product`.
from shop.models import Product

__all__ = ["Product", "__version__"]

print("     [shop/__init__.py executed]")
