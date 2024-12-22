from pydantic import BaseModel


class CurrencyProcessResult(BaseModel):
    final_price: float
    min_price: float
    max_price: float
    compare_price: float
    seller: str
    top_seller: list
