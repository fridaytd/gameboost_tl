import random
from pydantic import BaseModel
from app.crwl.models import Offer
from app.sheet.models import RowModel


class CurrencyProcessResult(BaseModel):
    final_price: float
    stock: int
    min_price: float
    max_price: float | None
    compare_price: float
    seller: str


def filter_valid_offers(
    crwl_offers: list[Offer],
    min_price: float,
    max_price: float | None,
    blacklist: list[str],
    include_keywords: list[str] | None,
    exclude_keywords: list[str] | None,
) -> list[Offer]:
    valid_offers: list[Offer] = []

    for crwl_offer in crwl_offers:
        # Check blacklist
        if crwl_offer.seller in blacklist:
            continue

        # Check include keywords
        if include_keywords:
            if not any(
                keyword.lower() in crwl_offer.title.lower()
                for keyword in include_keywords
            ):
                continue

        # Check exclude keywords
        if exclude_keywords:
            if any(
                keyword.lower() in crwl_offer.title.lower()
                for keyword in exclude_keywords
            ):
                continue

        # Check price range
        if (
            max_price is not None and not (min_price <= crwl_offer.price <= max_price)
        ) or (max_price is None and crwl_offer.price < min_price):
            continue

        valid_offers.append(crwl_offer)

    return valid_offers


def find_offer_min_price(
    crwl_offers: list[Offer],
) -> Offer | None:
    offer_min_price = None
    for crwl_offer in crwl_offers:
        if offer_min_price is None:
            offer_min_price = crwl_offer
        elif crwl_offer.price < offer_min_price.price:
            offer_min_price = crwl_offer

    return offer_min_price


def find_lower_price_offers(
    offers: list[Offer],
    compare_price: float,
) -> list[Offer]:
    lower_price_offer: list[Offer] = []

    for offer in offers:
        if offer.price < compare_price:
            lower_price_offer.append(offer)

    return lower_price_offer


def calculate_price_change(
    run_row: RowModel,
    compare_price: float,
    min_price: float,
) -> float:
    min_final_price = (
        min_price
        if compare_price - run_row.DONGIAGIAM_MAX < min_price
        else compare_price - run_row.DONGIAGIAM_MAX
    )

    max_final_price = (
        min_price
        if compare_price - run_row.DONGIAGIAM_MIN <= min_price
        else compare_price - run_row.DONGIAGIAM_MIN
    )

    return round(
        random.uniform(min_final_price, max_final_price), run_row.DONGIA_LAMTRON
    )
