from datetime import datetime
import os
import random
from app.models.crwl_models import Offer
from app.models.gsheet_models import Product
from app.crwl import currencies_extract
from app.models.process_models import CurrencyProcessResult
from app.utils.logger import logger
from app.gameboost_client import GameboostClient
from app.decorators import retry_on_fail


def is_change_price(
    crwl_offers: list[Offer],
) -> bool:
    # If our name in crawled offer do not need to change price
    if os.environ["MY_SELLER_NAME"] in [offer.seller for offer in crwl_offers]:
        logger.info(
            f"No need to change price because {os.environ["MY_SELLER_NAME"]} has existed in product compare already"
        )
        return False

    return True


def filter_crwl_offer(
    product: Product,
    crwl_offers: list[Offer],
) -> list[Offer]:
    result_offers: list[Offer] = []
    blacklist = product.blacklits()
    for offer in crwl_offers:
        if offer.seller not in blacklist:
            result_offers.append(offer)

    return result_offers


def calculate_price_change(
    product: Product,
    crwl_offers: list[Offer],
) -> CurrencyProcessResult:
    filtered_crwl_offers = filter_crwl_offer(product, crwl_offers)
    sorted_filtered_crwl_offers = sorted(filtered_crwl_offers)
    min_price_crwl_offer = sorted_filtered_crwl_offers[0]
    compare_price = min_price_crwl_offer.price

    min_price = product.min_price()
    max_price = product.max_price()

    final_price = None

    if compare_price < min_price:
        final_price = min_price

    elif compare_price > max_price:
        final_price = max_price

    else:
        final_price = round(
            compare_price
            - random.uniform(product.DONGIAGIAM_MIN, product.DONGIAGIAM_MAX),
            product.DONGIA_LAMTRON,
        )

    return CurrencyProcessResult(
        final_price=final_price,
        min_price=min_price,
        max_price=max_price,
        compare_price=compare_price,
        seller=min_price_crwl_offer.seller,
        top_seller=sorted_filtered_crwl_offers[:2],
    )


@retry_on_fail()
def currency_price_update(
    product: Product,
    currency_price_change_result: CurrencyProcessResult,
):
    client = GameboostClient()
    onl_offer = client.get_currency_offer(product.Product_link)

    payload = {
        "description": onl_offer["attributes"]["description"],
        "price": currency_price_change_result.final_price,
        "game": onl_offer["attributes"]["game_slug"],
        "stock": onl_offer["attributes"]["stock"],
        "min_quantity": onl_offer["attributes"]["min_quantity"],
        "delivery_time": onl_offer["attributes"]["delivery_time"],
    }
    client.update_currency_offer(product.Product_link, payload)


def last_update_message(
    now: datetime,
) -> str:
    formatted_date = now.strftime("%-m/%-d/%Y %H:%M:%S")
    return formatted_date


def note_message(
    now: datetime, currency_price_change_result: CurrencyProcessResult
) -> str:
    message = f"""{last_update_message(now)}:Giá đã cập nhật thành công; Price = {currency_price_change_result.final_price}; Pricemin = {currency_price_change_result.min_price}, Pricemax = {currency_price_change_result.max_price}, GiaSosanh = {currency_price_change_result.compare_price} - Seller: {currency_price_change_result.seller}"""

    return message


def currency_process(
    sb,
    product: Product,
) -> CurrencyProcessResult | None:
    logger.info("Currency Proccess")
    logger.info(f"Crawling at: {product.Product_compare}")
    url_product_compare = product.Product_compare.replace(
        "https://gameboost", "https://api.gameboost"
    )
    crwl_offers = currencies_extract(sb, url_product_compare)
    if not is_change_price(crwl_offers):
        logger.info("Sheet updating")
        now = datetime.now()
        product.Last_update = last_update_message(now)
        product.update()

        return None

    logger.info(f"Caculating price change for {product.Product_name}")
    currency_price_change_result = calculate_price_change(product, crwl_offers)

    logger.info(f"Price updating for {product.Product_name}")
    currency_price_update(product, currency_price_change_result)

    logger.info("Sheet updating")
    now = datetime.now()
    product.Last_update = last_update_message(now)
    product.Note = note_message(now, currency_price_change_result)
    product.update()
    return currency_price_change_result


@retry_on_fail()
def run(
    sb,
    product: Product,
):
    logger.info(f"{product.Product_name} is besing processed")
    if product.Category.lower() == "currencies":
        return currency_process(sb, product)
    elif product.Category.lower() == "items":
        # TODO
        pass
    elif product.Category.lower() == "accounts":
        # TODO
        pass
