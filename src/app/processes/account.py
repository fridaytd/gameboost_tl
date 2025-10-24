import logging

from datetime import datetime

from app.sheet.models import RowModel

# from app.shared.decorators import retry_on_fail
from app.gameboost.api import gameboost_api_client
from app.shared.utils import formated_datetime
from app.crwl.crwl import accounts_extract

# from app.shared.decorators import retry_on_fail
from app import config

from .shared import (
    filter_valid_offers,
    find_lower_price_offers,
    find_offer_min_price,
    calculate_price_change,
)

logger = logging.getLogger(__name__)


def update_multiple_accounts(
    account_offer_ids: list[str],
    prices: float,
) -> None:
    for account_offer_id in account_offer_ids:
        try:
            res = gameboost_api_client.update_account_offer(
                account_offer_id=account_offer_id,
                price=prices,
            )
            logger.info(
                f"Updated account offer {account_offer_id} with price {prices}\n Update response: {res}"
            )
        except Exception as e:
            logger.exception(f"Error updating account offer {account_offer_id}: {e}")


def account_process(sb, run_row: RowModel):
    # If not compare product, update by min price and return

    account_offer_ids = [id.strip() for id in run_row.Product_link.split(";")]

    if run_row.Check_product_compare != "1":
        logger.info(
            f"{run_row.Product_name} is skipped due to Check_product_compare != 1"
        )
        min_price = run_row.min_price()
        max_price = run_row.max_price()

        update_multiple_accounts(
            account_offer_ids=account_offer_ids,
            prices=min_price,
        )

        now = datetime.now()

        run_row.Note = f"{formated_datetime(now)}: Không so sánh, Cập nhật theo giá min. PRICE={min_price}, Pricemin={run_row.min_price()}, Pricemax={max_price}"
        run_row.Last_update = formated_datetime(now)
        run_row.update()
        return
    # Try to crawl compare product
    try:
        logger.info(f"Crawling at: {run_row.Product_compare}")
        crwl_offers = accounts_extract(sb, run_row.Product_compare)

    except Exception as e:
        # If crawl error, update by min price and return
        logger.exception(f"Error crawling {run_row.Product_name}: {e}")

        min_price = run_row.min_price()
        max_price = run_row.max_price()

        update_multiple_accounts(
            account_offer_ids=account_offer_ids,
            prices=min_price,
        )

        now = datetime.now()

        run_row.Note = f"{formated_datetime(now)}: Không thể quét giá: {e}, Cập nhật theo giá min. PRICE={min_price}, Pricemin={run_row.min_price()}, Pricemax={max_price}"
        run_row.Last_update = formated_datetime(now)
        run_row.update()

        return

    min_price = run_row.min_price()
    max_price = run_row.max_price()
    blacklist = run_row.blacklist()
    # my_currency_offer = gameboost_api_client.get_currency_offer(run_row.Product_link)

    valid_offers = filter_valid_offers(
        crwl_offers,
        min_price=min_price,
        max_price=max_price,
        blacklist=blacklist,
        include_keywords=run_row.include_keywords(),
        exclude_keywords=run_row.exclude_keywords(),
    )

    offer_min_price = find_offer_min_price(valid_offers)

    logger.info(f"Crawled offers: {[offer.model_dump() for offer in crwl_offers]}")

    if len(valid_offers) == 0 or offer_min_price is None:
        # No valid offers, update to min price
        update_multiple_accounts(
            account_offer_ids=account_offer_ids,
            prices=min_price,
        )

        now = datetime.now()

        lower_price_offers = find_lower_price_offers(crwl_offers, min_price)
        run_row.Note = f"{formated_datetime(now)}: Không có sản phẩm hợp lệ so sánh, Giá đã cập nhật thành công; Price = {min_price:f}; Pricemin = {min_price:f}, Pricemax = {max_price:f}\nSeller có giá thấp hơn: {', '.join([f'{offer.seller} - {offer.price}' for offer in lower_price_offers if offer.seller != config.MY_SELLER_NAME])}"
        run_row.Last_update = formated_datetime(now)
        run_row.update()
        return

    # Calculate new price
    new_price = calculate_price_change(
        run_row,
        offer_min_price.price,
        min_price,
    )

    # Update price if changed
    update_multiple_accounts(
        account_offer_ids=account_offer_ids,
        prices=new_price,
    )

    now = datetime.now()
    lower_price_offers = find_lower_price_offers(crwl_offers, new_price)
    run_row.Note = f"""{formated_datetime(now)}:Giá đã cập nhật thành công; Price = {new_price:f}; Pricemin = {min_price:f}, Pricemax = {max_price:f}, GiaSosanh = {offer_min_price.price:f} - Seller: {offer_min_price.seller}
Seller có giá thấp hơn: {", ".join([f"{offer.seller} - {offer.price:f}" for offer in lower_price_offers if offer.seller != config.MY_SELLER_NAME])}
"""
    run_row.Last_update = formated_datetime(now)
    run_row.update()

    return
