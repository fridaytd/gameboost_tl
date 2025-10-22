import json
from bs4 import BeautifulSoup
import random

from .exceptions import CrwlError
from .models import Offer

from app.shared.decorators import retry_on_fail


def get_soup(
    sb,
    url: str,
) -> BeautifulSoup:
    sb.get(url)
    # sb.cdp.sleep(random.uniform(0.5, 0.9))
    soup = BeautifulSoup(sb.cdp.get_page_source(), "html.parser")
    sb.cdp.sleep(random.uniform(0.3, 0.7))
    return soup


@retry_on_fail()
def currencies_extract(
    sb,
    url: str,
) -> list[Offer]:
    soup = get_soup(sb, url)
    app_tag = soup.select_one("#app")
    if not app_tag:
        raise CrwlError("App tag not found!!!")

    page_data = app_tag.attrs.get("data-page", None)
    if not page_data:
        raise CrwlError("Page data not found!!!")
    page_data = json.loads(page_data)  # type: ignore
    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_currencies_dict: list[dict] = []
    if "currency_offer" in model:
        list_currencies_dict.append(model["currency_offer"])

    if "currencies" in model and "data" in model["currencies"]:
        list_currencies_dict.extend(model["currencies"]["data"])

    return [
        Offer(
            seller=currency["seller"]["username"],
            price=currency["price"]["amount"],
            title=currency["title"],
            id=currency.get("id", None),
        )
        for currency in list_currencies_dict
    ]


def items_extract(
    sb,
    url: str,
) -> list[Offer]:
    soup = get_soup(sb, url)
    app_tag = soup.select_one("#app")
    if not app_tag:
        raise CrwlError("App tag not found!!!")

    page_data = app_tag.attrs.get("data-page", None)
    if not page_data:
        raise CrwlError("Page data not found!!!")
    page_data = json.loads(page_data)  # type: ignore
    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_items_dict = []

    if "items" in model and "data" in model["items"]:
        list_items_dict.extend(model["items"]["data"])

    return [
        Offer(
            seller=item["seller"]["username"],
            price=item["price"]["value"],
            title=item["title"],
            id=item.get("id", None),
        )
        for item in list_items_dict
    ]


def accounts_extract(
    sb,
    url: str,
) -> list[Offer]:
    soup = get_soup(sb, url)
    app_tag = soup.select_one("#app")
    if not app_tag:
        raise CrwlError("App tag not found!!!")

    page_data = app_tag.attrs.get("data-page", None)
    if not page_data:
        raise CrwlError("Page data not found!!!")
    page_data = json.loads(page_data)  # type: ignore
    props = page_data.get("props", None)
    if not props:
        raise CrwlError("Props not found!!!")

    model = props.get("model", None)
    if not model:
        raise CrwlError("Model not found!!!")

    list_accounts_dict = []

    if "accounts" in model and "data" in model["accounts"]:
        list_accounts_dict.extend(model["accounts"]["data"])

    return [
        Offer(
            seller=item["seller"]["username"],
            price=item["price"]["value"],
            title=item["title"],
            id=item.get("id", None),
        )
        for item in list_accounts_dict
    ]
