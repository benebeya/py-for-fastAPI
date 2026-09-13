"""Data shapes. Imports only stdlib + config -- never services or routers."""

from dataclasses import dataclass


@dataclass
class Product:
    name: str
    qty: int


print("     [shop/models.py executed]")
