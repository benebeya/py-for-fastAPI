from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Product(BaseModel):
    units: str
    qty: int

catalog = {
    "tomatoes": Product(units="boxes", qty=1000),
    "wine": Product(units="bottles", qty=500)
}

app = FastAPI(title="New Jersey API Server")

@app.get("/warehouse/{product}")
async def load_truck(product, order_qty):
    """Load product onto truck and update inventory."""
    available = catalog[product].qty

    if int(order_qty) > int(available):
        raise HTTPException(
            status_code=400,
            detail=f"Only {available} units available."
        )

    catalog[product].qty -= int(order_qty)

    return {
        "product": product,
        "order_qty": order_qty,
        "units": catalog[product].units,
        "remaining_qty": catalog[product].qty
    }