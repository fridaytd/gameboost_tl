from pydantic import BaseModel
from typing import TypeVar, Generic
from typing import List

T = TypeVar("T", bound=BaseModel)


class OfferResponse(BaseModel, Generic[T]):
    data: T


class Game(BaseModel):
    id: int
    name: str
    slug: str


class CurrencyUnit(BaseModel):
    slug: str
    currency_name: str
    name: str
    symbol: str
    multiplier: int


class DeliveryTime(BaseModel):
    duration: int
    unit: str
    format: str
    # format_long: dict
    seconds: int


class Price(BaseModel):
    format: str
    format_readable: str
    amount: float
    currency: str


class CurrencyOffer(BaseModel):
    id: int
    uuid: str
    game: Game
    currency_unit: CurrencyUnit
    title: str
    description: str
    parameters: dict
    base_currency: str
    status: str
    # delivery_time: DeliveryTime
    # delivery_instructions: str
    stock: int
    min_quantity: int
    price_eur: Price
    price_usd: Price
    views: int
    icon_url: str
    created_at: int
    updated_at: int
    # listed_at: int


# class CurrencyOfferResponse(OfferResponse[CurrencyOffer]):
#     pass


class Credentials(BaseModel):
    login: str
    password: str
    email_login: str
    email_password: str
    email_provider: str


class Currency(BaseModel):
    symbol: str
    code: str


class CurrencyPrice(BaseModel):
    format: str
    value: float
    amount: float
    currency: Currency


class AccountOffer(BaseModel):
    id: int
    game: Game
    account_order_ids: List[int]
    title: str
    slug: str
    description: str
    parameters: dict
    dump: str
    status: str
    # delivery_time: DeliveryTime
    # is_manual_delivery: bool
    # credentials: Credentials
    delivery_instructions: str
    price: CurrencyPrice
    price_usd: CurrencyPrice
    views: int
    # image_urls: List[str]
    created_at: int
    updated_at: int
    # listed_at: int


class ItemOffer(BaseModel):
    id: int
    game: Game
    title: str
    slug: str
    description: str
    # parameters: dict
    status: str
    # delivery_time: DeliveryTime
    delivery_instructions: str
    stock: int
    min_quantity: int
    price_eur: CurrencyPrice
    price_usd: CurrencyPrice
    views: int
    image_urls: List[str]
    created_at: int
    updated_at: int
    # listed_at: int
