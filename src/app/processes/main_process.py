from app.sheet.models import RowModel
from app.shared.enums import OfferType
from app import logger

from .currency import currency_process
from .item import item_process
from .account import account_process


def process(
    sb,
    run_row: RowModel,
) -> None:
    """Process a single row from the spreadsheet."""
    logger.info(f"{run_row.Product_name} is being processed")
    logger.info(f'Category: {run_row.Category}')
    if run_row.Category == OfferType.Currency.value:
        return currency_process(sb, run_row)
    elif run_row.Category == OfferType.Item.value:
        return item_process(sb, run_row)
    elif run_row.Category == OfferType.Account.value:
        return account_process(sb, run_row)
