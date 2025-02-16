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


def find_offer_min_price(
    crwl_offers: list[Offer],
    blacklist: list[str],
    product_min_price: float,
    product_max_price: float | None,
) -> tuple[Offer | None, Offer | None]:
    my_seller_offer = None
    other_offer_min_price = None
    for crwl_offer in crwl_offers:
        # If current crawled offer is our
        if crwl_offer.seller == os.environ["MY_SELLER_NAME"]:
            my_seller_offer = crwl_offer

        # If current crawled offer is not our and not in blacklist
        elif crwl_offer.seller not in blacklist:
            # If it has product max price --->  product min price <= current crawled offer's price <= product max price
            # If it hasn't product max price ---> product min price <= current crawled offer's price
            if (
                product_max_price is not None
                and product_min_price <= crwl_offer.price <= product_max_price
            ) or (product_max_price is None and product_min_price <= crwl_offer.price):
                if other_offer_min_price is None:
                    other_offer_min_price = crwl_offer
                elif crwl_offer.price < other_offer_min_price.price:
                    other_offer_min_price = crwl_offer

    return my_seller_offer, other_offer_min_price


def calculate_price_change(
    product: Product,
    other_offer_min_price: Offer | None,
    product_min_price: float,
    product_max_price: float | None,
) -> CurrencyProcessResult:
    final_price = None

    # If it has no other valid offer
    if other_offer_min_price is None:
        # Set price to max price if it has product max price
        if product_max_price is not None:
            final_price = product_max_price
        # If it has no product max price, set by product min price
        else:
            final_price = product_min_price

        return CurrencyProcessResult(
            final_price=round(final_price, product.DONGIA_LAMTRON),
            stock=product.stock(),
            min_price=product_min_price,
            max_price=product_max_price,
            compare_price=0,
            seller="",
        )

    else:
        compare_price = other_offer_min_price.price

        if compare_price <= product_min_price:
            final_price = product_min_price

        elif product_max_price is not None and compare_price >= product_max_price:
            final_price = product_max_price

        else:
            final_price = round(
                compare_price
                - random.uniform(product.DONGIAGIAM_MIN, product.DONGIAGIAM_MAX),
                product.DONGIA_LAMTRON,
            )

        return CurrencyProcessResult(
            final_price=round(final_price, product.DONGIA_LAMTRON),
            stock=product.stock(),
            min_price=product_min_price,
            max_price=product_max_price,
            compare_price=compare_price,
            seller=other_offer_min_price.seller,
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
        "stock": currency_price_change_result.stock,
        "min_quantity": onl_offer["attributes"]["min_quantity"],
        "delivery_time": onl_offer["attributes"]["delivery_time"],
    }
    if onl_offer["attributes"].get("data", None) is not None:
        payload.update(
            {
                "currency_data": onl_offer["attributes"]["data"],
            }
        )

    client.update_currency_offer(product.Product_link, payload)


def last_update_message(
    now: datetime,
) -> str:
    formatted_date = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted_date


def note_message(
    now: datetime, currency_price_change_result: CurrencyProcessResult
) -> str:
    message = f"""{last_update_message(now)}:Giá đã cập nhật thành công; Price = {currency_price_change_result.final_price}; Stock = {currency_price_change_result.stock}; Pricemin = {currency_price_change_result.min_price}, Pricemax = {currency_price_change_result.max_price}, GiaSosanh = {currency_price_change_result.compare_price} - Seller: {currency_price_change_result.seller}"""

    return message


def currency_process(
    sb,
    product: Product,
) -> CurrencyProcessResult | None:
    logger.info("Currency Proccess")
    logger.info(f"Crawling at: {product.Product_compare}")
    # url_product_compare = product.Product_compare.replace(
    #     "https://gameboost", "https://api.gameboost"
    # )
    url_product_compare = product.Product_compare
    crwl_offers = currencies_extract(sb, url_product_compare)
    blacklist = product.blacklits()

    product_min_price = product.min_price()
    product_max_price = product.max_price()

    my_seller_offer, other_offer_min_price = find_offer_min_price(
        crwl_offers, blacklist, product_min_price, product_max_price
    )
    now = datetime.now()

    # If have no valid other crawled, update product price to product max price if existing or product min price if no
    if other_offer_min_price is None:
        logger.info(f"Calculating price change for {product.Product_name}")
        currency_price_change_result = calculate_price_change(
            product, other_offer_min_price, product_min_price, product_max_price
        )
        logger.info(f"Price updating for {product.Product_name}")
        currency_price_update(product, currency_price_change_result)

        note_message_var = f"""{last_update_message(now)}: Không có sản phẩm hợp lệ so sánh, Giá đã cập nhật thành công; Price = {currency_price_change_result.final_price}; Stock = {currency_price_change_result.stock}; Pricemin = {currency_price_change_result.min_price}, Pricemax = {currency_price_change_result.max_price}"""

        logger.info("Sheet updating")
        product.Last_update = last_update_message(now)
        product.Note = note_message_var
        product.update()
        return currency_price_change_result

    # If it contains valid other crawled offer, perform price compare and update
    else:
        if (
            my_seller_offer is not None
            and my_seller_offer.price < other_offer_min_price.price
            and my_seller_offer.price
            >= other_offer_min_price.price - product.DONGIAGIAM_MAX
        ):
            note_message_var = f"{last_update_message(now)}: Không cần cập nhật giá vì {os.environ['MY_SELLER_NAME']} Đã có giá nhỏ nhất: Price = {my_seller_offer.price}; Stock = {product.stock()}; Pricemin = {product_min_price}, Pricemax = {product_max_price}, GiaSosanh = {other_offer_min_price.price} - Seller: {other_offer_min_price.seller}"
            logger.info(note_message_var)
            product.Last_update = last_update_message(now)
            product.Note = note_message_var
            logger.info("Sheet updating")
            product.update()
        else:
            logger.info(f"Caculating price change for {product.Product_name}")
            currency_price_change_result = calculate_price_change(
                product, other_offer_min_price, product_min_price, product_max_price
            )

            logger.info(f"Price updating for {product.Product_name}")
            currency_price_update(product, currency_price_change_result)

            logger.info("Sheet updating")
            product.Last_update = last_update_message(now)
            product.Note = note_message(now, currency_price_change_result)
            product.update()
            return currency_price_change_result


@retry_on_fail(max_retries=2)
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
