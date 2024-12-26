from pydantic import BaseModel


class CurrencyProcessResult(BaseModel):
    final_price: float
    stock: int
    min_price: float
    max_price: float | None
    compare_price: float
    seller: str
