from pydantic import BaseModel


class Offer(BaseModel):
    seller: str
    price: float

    def __gt__(self, other: "Offer") -> bool:
        return self.price > other.price

    def __lt__(self, other: "Offer") -> bool:
        return self.price < other.price

    def __ge__(self, other: "Offer") -> bool:
        return self.price >= other.price

    def __le__(self, other: "Offer") -> bool:
        return self.price <= other.price
