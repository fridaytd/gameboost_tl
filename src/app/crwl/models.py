from pydantic import BaseModel


class Offer(BaseModel):
    seller: str
    price: float
    title: str
    id: int | str | None = None

    def __gt__(self, other: "Offer") -> bool:
        return self.price > other.price

    def __lt__(self, other: "Offer") -> bool:
        return self.price < other.price

    def __ge__(self, other: "Offer") -> bool:
        return self.price >= other.price

    def __le__(self, other: "Offer") -> bool:
        return self.price <= other.price


class ExchangeRate(BaseModel):
    usd_to_eur: float
    eur_to_usd: float
