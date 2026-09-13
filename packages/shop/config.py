"""Settings live at the top of the dependency graph: config imports NOTHING
from the rest of the package. That is what keeps it circular-import-proof."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "shop"
    debug: bool = False


settings = Settings()

print("     [shop/config.py executed]")
